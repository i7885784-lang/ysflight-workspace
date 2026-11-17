from pathlib import Path
import sys,json,hashlib,numpy as np
from shapely.geometry import LineString
from shapely import constrained_delaunay_triangles
from shapely.ops import unary_union,polygonize
import dnm
from mesh import Mesh,pack_dnm
def generate(source,out,report_path,z=-1.4):
 raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()=='5ffbd1cedb9b82c81f048319bf4d4e96fb1b85f560ee4ce64bdc68e7d54fd263';base,nodes=dnm.read(source);body_node=next(n for n in nodes if dnm.name(n)=='SourceAirframe');body=dnm.mesh(base[dnm.fil(body_node)]);body_v=np.array(body.v);body_tri=np.array([body_v[[ids[0],ids[j],ids[j+1]]] for ids,c,b in body.f for j in range(1,len(ids)-1)])
 packs=dict(base);report={}
 for node in nodes:
  name=dnm.name(node)
  if name not in ['InsideIntakeL','InsideIntakeR']:continue
  key=dnm.fil(node);lines=packs[key];old=dnm.mesh(lines);faces=old.f[:-48];count=max(i for ids,c,b in faces for i in ids)+1;v=np.array(old.v);rear=float(v[:,2].min());assert all(np.allclose(v[ids,2],rear) for ids,c,b in old.f[-48:]);segments=[];crossings={}
  # Use only inward-facing wall quads, matching the visible side of the original liner.
  for ids,c,b in (faces[:len(faces)//2] if name.endswith('L') else faces[len(faces)//2:]):
   q=v[ids]
   for j in range(1,len(q)-1):
    t=q[[0,j,j+1]];points=[]
    for a,b in zip(t,np.roll(t,-1,axis=0)):
     if (a[2]-z)*(b[2]-z)<0:
      edge=tuple(sorted([tuple(a),tuple(b)]))
      if edge not in crossings:
       aa,bb=map(np.array,edge);crossings[edge]=np.round((aa+(bb-aa)*(z-aa[2])/(bb[2]-aa[2]))[:2],6)
      points.append(crossings[edge])
    if len(points)==2 and np.linalg.norm(points[0]-points[1])>1e-9:segments.append(LineString(np.round(points,6)))
  
  polys=list(polygonize(unary_union(segments)));assert len(polys)==1,(name,z,len(polys));liner_poly=polys[0];seed=liner_poly.centroid;body_lines=[];cache={};xmin,ymin,xmax,ymax=liner_poly.bounds
  candidates=body_tri[(body_tri[:,:,2].min(1)<z)&(body_tri[:,:,2].max(1)>z)&(body_tri[:,:,0].max(1)>=xmin)&(body_tri[:,:,0].min(1)<=xmax)&(body_tri[:,:,1].max(1)>=ymin)&(body_tri[:,:,1].min(1)<=ymax)]
  for triangle in candidates:
   pp=[]
   for aa,bb in zip(triangle,np.roll(triangle,-1,axis=0)):
    if (aa[2]-z)*(bb[2]-z)<0:
     edge=tuple(sorted([tuple(aa),tuple(bb)]))
     if edge not in cache:
      aa,bb=map(np.array,edge);cache[edge]=np.round((aa+(bb-aa)*(z-aa[2])/(bb[2]-aa[2]))[:2],6)
     pp.append(cache[edge])
   if len(pp)==2 and np.linalg.norm(pp[0]-pp[1])>1e-9:body_lines.append(LineString(pp))
  cells=list(polygonize(unary_union([liner_poly.boundary,*body_lines])));air=[cell for cell in cells if cell.covers(seed) and liner_poly.covers(cell.representative_point())];assert air,(name,z,'air cell missing');poly=min(air,key=lambda q:q.area).buffer(-.001,join_style=2).simplify(.00001,preserve_topology=True);assert poly.geom_type=='Polygon' and not poly.is_empty and poly.covers(seed);ring=np.array(poly.exterior.coords)[:-1];cap=Mesh()
  for triangle in constrained_delaunay_triangles(poly).geoms:
   xy=np.array(triangle.exterior.coords)[:-1];q=np.round(np.c_[xy,np.full(3,z)],6);assert np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))>1e-12;cap.face(q,(18,22,25));cap.face(q[::-1],(18,22,25))
  i=lines.index('F');end=i
  for _ in faces:end=lines.index('E',end)+1
  cap.f=[([x+count for x in ids],c,b) for ids,c,b in cap.f];cap.v=[tuple(q) for q in v[:count]]+cap.v;extra=cap.srf();first=extra.index('F');packs[key]=lines[:1+count]+extra[1+count:first]+lines[i:end]+extra[first:];report[name]={'old_rear_z':rear,'new_rear_z':z,'depth_from_liner_start_m':-.35-z,'ring_points':len(ring),'cap_faces':len(cap.f)}
 data=pack_dnm(list(packs.items()),sum(nodes,[])).encode();out.write_bytes(data);report['model_sha256']=hashlib.sha256(data).hexdigest();report_path.write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--report',required=True,type=Path);a=p.parse_args();print(json.dumps(generate(a.baseline,a.output,a.report),indent=2))
