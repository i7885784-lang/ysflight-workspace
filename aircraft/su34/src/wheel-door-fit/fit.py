"""Trim only the two main wheel-door overhangs and their static surround."""
from pathlib import Path
import argparse,hashlib,json,collections,numpy as np
from shapely.geometry import Polygon,box
from shapely import union_all,constrained_delaunay_triangles
import dnm
from mesh import pack_dnm,Mesh
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--output',required=True);ap.add_argument('--report',required=True);a=ap.parse_args();src=Path(a.baseline);assert hashlib.sha256(src.read_bytes()).hexdigest()=='e60bef484705795468dc12666ab23f0d99d7478f3003a4029704236e03a31398'
p,ns=dnm.read(src);nodes={dnm.name(n):n for n in ns};ref='\n'.join(p[dnm.fil(nodes['SourceAirframe'])]).encode();body=dnm.mesh(ref.decode().splitlines());v=np.array(body.v);tri=np.array([[ids[0],ids[j],ids[j+1]] for ids,c,b in body.f for j in range(1,len(ids)-1)]);t=v[tri];aa=t[:,0];ab=t[:,1]-aa;ac=t[:,2]-aa;det=ab[:,0]*ac[:,2]-ab[:,2]*ac[:,0];ok=np.abs(det)>1e-12;t,aa,ab,ac,det=[q[ok] for q in [t,aa,ab,ac,det]]
raw_footprint=union_all([Polygon(q[:,[0,2]]) for q in t]);footprint=raw_footprint;mask=footprint.buffer(-.008,join_style='mitre');report={}
def components(poly):return poly.geoms if hasattr(poly,'geoms') else [poly]
def floor(z):return -.245+.095*np.clip((-z-.8)/.8,0,1)
def top(xz):
 dx,dz=(xz-aa[:,[0,2]]).T;u=(dx*ac[:,2]-dz*ac[:,0])/det;w=(ab[:,0]*dz-ab[:,2]*dx)/det;hit=(u>=-1e-6)&(w>=-1e-6)&(u+w<=1.000001);assert hit.any(),xz
 return float(np.max(aa[hit,1]+u[hit]*ab[hit,1]+w[hit]*ac[hit,1]))-.003
for name in ['OriginalSideDoorLWheel','OriginalSideDoorRWheel']:
 old=dnm.mesh(p[dnm.fil(nodes[name])]);m=Mesh();edges=collections.Counter();directed={};before=[];after=[]
 for ids,c,bright in old.f:
  if c!=(138,169,181):continue
  q=np.array(old.v)[ids];poly=Polygon(q[:,[0,2]]);before.append(poly)
  origin=q[0];u=q[1]-origin;w=q[2]-origin;den=u[0]*w[2]-u[2]*w[0];assert abs(den)>1e-12
  for clipped in components(poly.intersection(mask)):
   if clipped.area<1e-10:continue
   assert not clipped.interiors,'Unexpected hole in door polygon'
   for piece in constrained_delaunay_triangles(clipped).geoms:
    xz=np.array(piece.exterior.coords)[:-1];d=xz-origin[[0,2]];uu=(d[:,0]*w[2]-d[:,1]*w[0])/den;ww=(u[0]*d[:,1]-u[2]*d[:,0])/den;lower=np.round(np.c_[xz[:,0],origin[1]+uu*u[1]+ww*w[1],xz[:,1]],6)
    if np.linalg.norm(np.cross(lower[1]-lower[0],lower[2]-lower[0]))<1e-12:continue
    if np.cross(lower[1]-lower[0],lower[2]-lower[0])[1]*np.cross(u,w)[1]<0:lower=lower[::-1]
    upper=np.round(lower+[0,.012,0],6);m.face(lower,(138,169,181));m.face(upper[::-1],(120,145,160));after.append(piece)
    pts=[tuple(x) for x in lower]
    for x,z in zip(pts,pts[1:]+pts[:1]):
     key=tuple(sorted([x,z]));edges[key]+=1;directed[key]=(x,z)
 for key,count in edges.items():
  if count!=1:continue
  x,z=map(np.array,directed[key]);m.face(np.round([x,z,z+[0,.012,0],x+[0,.012,0]],6),(116,141,154))
 p[dnm.fil(nodes[name])]=m.srf();report[name]=dict(before_area_m2=union_all(before).area,after_area_m2=union_all(after).area,hinge_and_animation_exact=True)
# Rebuild only the wheel-side portion of the static surround. Rear strut bays stay original.
parts=[]
for name,n in nodes.items():
 if not name.startswith('OriginalSideDoor'):continue
 old=dnm.mesh(p[dnm.fil(n)])
 for ids,c,b in old.f:
  poly=Polygon(np.array(old.v)[ids][:,[0,2]])
  if poly.area>1e-12:parts.append(poly)
opening=union_all(parts).buffer(.005,join_style='mitre');affected=box(-10,-1.45,10,10)
def keep_rear(old):
 m=Mesh()
 for ids,c,b in old.f:
  pts=[np.array(old.v[i]) for i in ids];out=[]
  for x,z in zip(pts,pts[1:]+pts[:1]):
   inside=x[2]<=-1.45;next_inside=z[2]<=-1.45
   if inside:out.append(x)
   if inside!=next_inside:out.append(x+(z-x)*((-1.45-x[2])/(z[2]-x[2])))
  if len(out)>=3:m.face(np.round(out,6),c,b)
 return m
wallname='ConformalWingRootBaySides';wall=keep_rear(dnm.mesh(p[dnm.fil(nodes[wallname])]))
for poly in components(opening):
 for ring in [poly.exterior,*poly.interiors]:
  coords=np.array(ring.coords)
  for start,end in zip(coords[:-1],coords[1:]):
   if max(start[1],end[1])<=-1.45:continue
   if start[1]<-1.45:start=start+(end-start)*((-1.45-start[1])/(end[1]-start[1]))
   if end[1]<-1.45:end=end+(start-end)*((-1.45-end[1])/(start[1]-end[1]))
   points=np.linspace(start,end,max(2,int(np.linalg.norm(end-start)/.035)+1))
   for x,z in zip(points[:-1],points[1:]):
    q=np.round([(x[0],floor(x[1]),x[1]),(z[0],floor(z[1]),z[1]),(z[0],max(floor(z[1])+.001,top(z)),z[1]),(x[0],max(floor(x[1])+.001,top(x)),x[1])],6);wall.face(q,(128,157,175));wall.face(q[::-1],(128,157,175))
p[dnm.fil(nodes[wallname])]=wall.srf();sealname='MainBaySeals';seal=keep_rear(dnm.mesh(p[dnm.fil(nodes[sealname])]))
region=opening.buffer(.016,join_style='mitre').difference(opening).intersection(affected).intersection(footprint.buffer(-.001,join_style='mitre'))
for poly in components(region):
 for tri in constrained_delaunay_triangles(poly).geoms:
  q=np.array(tri.exterior.coords)[:-1];q=np.round(np.c_[q[:,0],floor(q[:,1])+.016,q[:,1]],6);seal.face(q,(92,117,132));seal.face(q[::-1],(92,117,132))
p[dnm.fil(nodes[sealname])]=seal.srf()
# Fit the existing stepped overlap seat as well; its 45mm outer border was exposed.
seatname='InternalSeamSeatMain';seat=keep_rear(dnm.mesh(p[dnm.fil(nodes[seatname])]))
foot=opening.buffer(-.005,join_style='mitre')
region=foot.buffer(.045,join_style='mitre').difference(foot.buffer(-.010,join_style='mitre')).intersection(affected).intersection(footprint.buffer(-.003,join_style='mitre'))
for poly in components(region):
 for tr in constrained_delaunay_triangles(poly).geoms:
  xz=np.array(tr.exterior.coords)[:-1];cap=np.array([top(q) for q in xz]);low=np.minimum(floor(xz[:,1])+.010,cap-.001);high=np.minimum(low+.18,cap);q=np.round(np.c_[xz[:,0],low,xz[:,1]],6);r=np.round(np.c_[xz[:,0],high,xz[:,1]],6)
  for f in [q,q[::-1],r,r[::-1]]:seat.face(f,(112,139,153))
  for i,j in [(0,1),(1,2),(2,0)]:
   f=[q[i],q[j],r[j],r[i]];seat.face(f,(112,139,153));seat.face(f[::-1],(112,139,153))
p[dnm.fil(nodes[seatname])]=seat.srf()
data=pack_dnm(list(p.items()),sum(ns,[])).encode();Path(a.output).write_bytes(data);report.update(model_sha256=hashlib.sha256(data).hexdigest(),reference_sha256=hashlib.sha256(ref).hexdigest(),changed_meshes=['OriginalSideDoorLWheel','OriginalSideDoorRWheel',wallname,sealname,seatname],door_inset_mm=8,all_nodes_exact=True);Path(a.report).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
