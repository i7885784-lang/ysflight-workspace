from pathlib import Path
import sys,json,hashlib,numpy as np
from shapely.geometry import LineString,Point
from shapely.ops import unary_union,polygonize
from shapely import constrained_delaunay_triangles
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));import dnm
from mesh import Mesh,pack_dnm
import argparse
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);cli=p.parse_args();src=cli.baseline;assert hashlib.sha256(src.read_bytes()).hexdigest()=='d35380cca144ac34c8e31d704501666a14831c8e2008a93296654984b639b970';packs,nodes=dnm.read(src);lines=packs['SourceAirframe.srf'];m=dnm.mesh(lines);v=np.array(m.v);rib_indices=list(range(5068,5076))+list(range(5265,5273));rib_keys={tuple(sorted(tuple(q) for q in v[m.f[i][0]])) for i in rib_indices};remove={i for i,(ids,c,b) in enumerate(m.f) if tuple(sorted(tuple(q) for q in v[ids])) in rib_keys};assert len(remove)==32
first=lines.index('F');blocks=[];i=first
while i<len(lines) and lines[i]=='F':
 j=lines.index('E',i)+1;blocks.append(lines[i:j]);i=j
suffix=lines[i:];tris=np.array([v[[ids[0],ids[j],ids[j+1]]] for i,(ids,c,b) in enumerate(m.f) if i not in remove for j in range(1,len(ids)-1)]);zmin=tris[:,:,2].min(1);zmax=tris[:,:,2].max(1);selected=[]
def shade(z):
 u=float(np.clip((z+2.35)/4.2,0,1));s=u*u*(3-2*u);return tuple(int(round(a+(b-a)*s)) for a,b in zip((18,22,25),(48,59,65)))
for i,(ids,c,b) in enumerate(m.f):
 if i in remove:continue
 q=v[ids];sg=1 if q[:,0].mean()>0 else -1
 if (q[:,0]*sg).min()<.45 or (q[:,0]*sg).max()>1.85 or q[:,1].min()<-1.5 or q[:,1].max()>-.10 or q[:,2].min()<-4.2 or q[:,2].max()>2:continue
 target=q[:3].mean(0);z=target[2];cx=np.interp(z,[-3.49,-2.4,-1.3,-.35],[1.16,1.06,.99,1.035])+(0.03355 if sg>0 else 0);cy=np.interp(z,[-3.49,-2.4,-1.3,-.35],[-.6,-.61,-.655,-.655]);origin=np.array([sg*cx,cy,z]);delta=target-origin;dist=np.linalg.norm(delta);normal=np.cross(q[1]-q[0],q[2]-q[0]);normal/=max(np.linalg.norm(normal),1e-30)
 if dist<.08 or dist>.8 or normal@(-delta)<=.0001:continue
 direction=delta/dist;t=tris[(zmin<=z+1e-7)&(zmax>=z-1e-7)];e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-12;inv=np.divide(1.,det,out=np.zeros_like(det),where=valid);s=origin-t[:,0];u=inv*np.einsum('ij,ij->i',s,h);qq=np.cross(s,e1);w=inv*np.einsum('j,ij->i',direction,qq);tt=inv*np.einsum('ij,ij->i',e2,qq);hit=valid&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1.0000001)&(tt>1e-6)
 if hit.any() and abs(float(tt[hit].min())-dist)<1e-4:
  col=shade(q[:,2].mean());blocks[i]=['C '+' '.join(map(str,col)) if l.startswith('C ') else l for l in blocks[i]];selected.append(i)
packs['SourceAirframe.srf']=lines[:first]+sum([b for i,b in enumerate(blocks) if i not in remove],[])+suffix
# Close the real source channel section. Remove the intersecting artificial inner liner.
z=-3.35;crossings={};segments=[]
for tri in tris[(zmin<z)&(zmax>z)]:
 pp=[]
 for a,b in zip(tri,np.roll(tri,-1,axis=0)):
  if (a[2]-z)*(b[2]-z)<0:
   edge=tuple(sorted([tuple(a),tuple(b)]))
   if edge not in crossings:
    a,b=map(np.array,edge);crossings[edge]=np.round((a+(b-a)*(z-a[2])/(b[2]-a[2]))[:2],6)
   pp.append(crossings[edge])
 if len(pp)==2 and np.linalg.norm(pp[0]-pp[1])>1e-9:segments.append(LineString(pp))
cells=list(polygonize(unary_union(segments)));report={'removed_rib_faces':sorted(remove),'selected_inner_faces':selected,'rear_z_m':z,'channels':{}}
for node in nodes:
 name=dnm.name(node)
 if name not in ['InsideIntakeL','InsideIntakeR']:continue
 sg=1 if name.endswith('L') else -1;seed=Point(sg*(1.16+(0.03355 if sg>0 else 0)),-.6);air=[p for p in cells if p.covers(seed)];assert air,(name,'air section missing');poly=min(air,key=lambda p:p.area).buffer(-.0005,join_style=2).simplify(.00001,preserve_topology=True);assert poly.geom_type=='Polygon' and poly.covers(seed) and .1<poly.area<1.5;cap=Mesh()
 for t in constrained_delaunay_triangles(poly).geoms:
  xy=np.array(t.exterior.coords)[:-1];q=np.round(np.c_[xy,np.full(3,z)],6);cap.face(q,(18,22,25));cap.face(q[::-1],(18,22,25))
 packs[dnm.fil(node)]=cap.srf();report['channels'][name]={'area_m2':poly.area,'bounds':list(poly.bounds),'cap_faces':len(cap.f),'removed_intersecting_liner_faces':240}
out=cli.output;out.write_bytes(pack_dnm(list(packs.items()),sum(nodes,[])).encode());report['model_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();cli.report.write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['selected_inner_faces','removed_rib_faces']})
