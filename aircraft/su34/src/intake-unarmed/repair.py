"""Repair inward ceiling material coverage and remove confirmed detachable Su34 weapon racks."""
from pathlib import Path
import argparse,sys,json,hashlib,numpy as np
pa=argparse.ArgumentParser();pa.add_argument('--baseline',type=Path,required=True);pa.add_argument('--output',type=Path,required=True);pa.add_argument('--report',type=Path,required=True);pa.add_argument('--helpers',type=Path);pa.add_argument('--dat-baseline',type=Path);pa.add_argument('--dat-output',type=Path);a=pa.parse_args()
for p in [a.helpers,Path(__file__).resolve().parent.parent/'intake-front',Path(__file__).resolve().parent.parent/'su34-intake-front']:
 if p:sys.path.insert(0,str(p))
import dnm
from mesh import pack_dnm
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()=='4aaaedfe34aee1247861eec4d2547642acba1b4aa36b17ccc3d8fbef36909eb9'
p,n=dnm.read(a.baseline);ls=p['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);_,ix=np.unique(np.round(v,4),axis=0,return_inverse=True);parent=list(range(int(ix.max())+1))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for ids,c,b in m.f:
 rr=root(int(ix[ids[0]]))
 for vi in ids:parent[root(int(ix[vi]))]=rr
components={}
for i,(ids,c,b) in enumerate(m.f):components.setdefault(root(int(ix[ids[0]])),[]).append(i)
remove=set();racks=[]
for faces in components.values():
 q=np.concatenate([v[m.f[i][0]] for i in faces]);lo=q.min(0);hi=q.max(0);cx=(lo[0]+hi[0])/2
 wing=(3.3<abs(cx)<6.3 and hi[0]-lo[0]<.20 and lo[1]>-.50 and hi[1]<.05 and lo[2]>-5.5 and hi[2]<-.9)
 center=(lo[0]>-.08 and hi[0]<.12 and lo[1]<-.5 and hi[1]<-.38 and lo[2]>-5.7 and hi[2]<-3.9)
 if wing or center:remove.update(faces);racks.append(dict(faces=faces,bounds=[lo.tolist(),hi.tolist()],kind='wing rack part' if wing else 'centreline rack'))
assert len(racks)==19 and len(remove)==568
# Donor tip rails are fused into SourceAirframe. Their existing inner joins are
# measured separately because the donor is not exactly mirrored about X=0.
from collections import Counter
from shapely.geometry import Polygon
from shapely.ops import triangulate
cap_specs=[];tip_removed=[]
for sg,limit in [(1,7.1679),(-1,7.1344)]:
 tip={i for i,(ids,c,b) in enumerate(m.f) if (v[ids,0]*sg).min()>limit};assert len(tip)==144
 remove.update(tip);tip_removed.extend(sorted(tip));edges=Counter();edge_colors={}
 for i,(ids,c,b) in enumerate(m.f):
  if i in remove:continue
  q=v[ids]
  for aa,bb in zip(q,np.roll(q,-1,axis=0)):
   if min(aa[0]*sg,bb[0]*sg)<limit:continue
   key=tuple(sorted(map(tuple,np.round([aa,bb],6))));edges[key]+=1;edge_colors[key]=c
 boundary=[edge for edge,count in edges.items() if count==2];assert len(boundary)==11
 adj={}
 for aa,bb in boundary:adj.setdefault(aa,[]).append(bb);adj.setdefault(bb,[]).append(aa)
 assert all(len(row)==2 for row in adj.values());start=min(adj);loop=[start];previous=None;current=start
 while True:
  nxt=next(q for q in adj[current] if q!=previous)
  if nxt==start:break
  assert nxt not in loop;loop.append(nxt);previous,current=current,nxt
 assert len(loop)==11;poly=Polygon([(q[1],q[2]) for q in loop]);assert poly.is_valid
 by_yz={(q[1],q[2]):q for q in loop};tris=[t for t in triangulate(poly) if poly.covers(t)];assert len(tris)==9
 assert abs(sum(t.area for t in tris)-poly.area)<1e-10
 for tri in tris:
  q=np.array([by_yz[tuple(q)] for q in list(tri.exterior.coords)[:3]])
  if np.cross(q[1]-q[0],q[2]-q[0])[0]*sg<0:q=q[::-1]
  edge=min(boundary,key=lambda e:np.linalg.norm((np.array(e[0])+e[1])*.5-q.mean(0)));cap_specs.append((q,edge_colors[edge]))
assert len(remove)==856
# Confirmed by actual per-face ID frames and864 radial first-wall hits. These ten
# inward ceiling faces were excluded by the older shader's upper Y-bound.
ceiling={2239,2240,2245,2915,2916,2921,4254,4255,4269,4270}
assert not ceiling&remove
first=ls.index('F');blocks=[];k=first
while k<len(ls) and ls[k]=='F':j=ls.index('E',k)+1;blocks.append(ls[k:j]);k=j
verts=list(m.v);out=[];changed=[]
def clip(poly,z,above):
 result=[]
 for p0,p1 in zip(poly,poly[1:]+poly[:1]):
  d0=p0[2]-z;d1=p1[2]-z;inside=d0>=0 if above else d0<=0;other=d1>=0 if above else d1<=0
  if inside:result.append(p0)
  if inside!=other:result.append(p0+(p1-p0)*d0/(d0-d1))
 clean=[]
 for q in result:
  if not clean or np.linalg.norm(q-clean[-1])>1e-8:clean.append(q)
 if len(clean)>1 and np.linalg.norm(clean[0]-clean[-1])<1e-8:clean.pop()
 return clean

def shade(z):
 u=float(np.clip((z+3.35)/5.2,0,1));s=u*u*(3-2*u)
 return tuple(round(x+(y-x)*s) for x,y in zip((9,12,14),(70,85,94)))
for i,(ids,c,b) in enumerate(m.f):
 block=blocks[i]
 if i in remove:continue
 if i not in ceiling:out+=block;continue
 q=v[ids];normal=np.cross(q[1]-q[0],q[2]-q[0]);normal/=np.linalg.norm(normal);origin=q.mean(0);origin[1]=-.62;assert normal@(origin-q.mean(0))>.25
 changed.append(i)
 for j in range(1,len(q)-1):
  tri=list(q[[0,j,j+1]]);lo=min(p[2] for p in tri);hi=max(p[2] for p in tri);cuts=[lo]+[z for z in [-3.35,-2.2,-1,.3,1.85] if lo+1e-7<z<hi-1e-7]+[hi]
  for aa,bb in zip(cuts,cuts[1:]):
   poly=clip(clip(tri,aa,True),bb,False)
   if len(poly)<3:continue
   poly=np.round(poly,6);assert np.linalg.norm(np.cross(poly[1]-poly[0],poly[2]-poly[0]))>1e-10;col=shade(float(poly[:,2].mean())) if bb>-3.35+1e-7 else c;vi=list(range(len(verts),len(verts)+len(poly)));verts.extend(map(tuple,poly))
   out+=['V '+' '.join(map(str,vi)) if line.startswith('V ') else 'C '+' '.join(map(str,col)) if line.startswith('C ') else line for line in block]
# Close only the exposed wing end loops, using existing boundary vertices.
vertex_ids={tuple(q):i for i,q in enumerate(v)};cap_face_count=0;cap_area=0.
for q,c in cap_specs:
 cap_area+=np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))
 for poly in [q,q[::-1]]:
  ids=[vertex_ids[tuple(qq)] for qq in poly];nn=np.cross(poly[1]-poly[0],poly[2]-poly[0]);nn/=np.linalg.norm(nn)
  out+=['F','C '+' '.join(map(str,c)),'N '+' '.join('%.6f'%x for x in nn),'V '+' '.join(map(str,ids)),'E'];cap_face_count+=1
p['SourceAirframe.srf']=ls[:first]+['V %.6f %.6f %.6f'%q for q in verts[len(v):]]+out+ls[k:]
launcher=next(nd for nd in n if dnm.name(nd)=='OwnTipLaunchers');assert len(dnm.mesh(p[dnm.fil(launcher)]).f)==36;del p[dnm.fil(launcher)];n=[nd for nd in n if dnm.name(nd)!='OwnTipLaunchers'];data=pack_dnm(list(p.items()),sum(n,[])).encode();a.output.write_bytes(data)
report=dict(sha256=hashlib.sha256(data).hexdigest(),source_removed_pylon_face_records=856,tip_rail_removed_face_records=tip_removed,wing_end_cap_face_records=cap_face_count,wing_end_cap_double_sided_area_m2=cap_area,deleted_tip_launcher_face_records=36,removed_components=racks,ceiling_faces=changed,original_vertices_unchanged=True,all_other_meshes_and_animation_records_unchanged=True)
if a.dat_baseline:
 assert a.dat_output
 old=a.dat_baseline.read_text();lines=[];deleted=[]
 for line in old.splitlines():
  key=line.split()[0] if line.strip() else ''
  if key in ['HRDPOINT','LOADWEPN']:deleted.append(line);continue
  if key=='INITIGUN':line='INITIGUN 0 # Unarmed Su34 aerobatic version'
  if key=='MAXNMRKT':line='MAXNMRKT 0 # Unarmed Su34 aerobatic version'
  lines.append(line)
 assert len(deleted)==8;a.dat_output.write_text('\n'.join(lines)+'\n');report['removed_default_weapon_and_station_lines']=deleted;report['dat_sha256']=hashlib.sha256(a.dat_output.read_bytes()).hexdigest()
a.report.write_text(json.dumps(report,indent=2));print({k:x for k,x in report.items() if k not in ['removed_components','removed_default_weapon_and_station_lines','tip_rail_removed_face_records']})
