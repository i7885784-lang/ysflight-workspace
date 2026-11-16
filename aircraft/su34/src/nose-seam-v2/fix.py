from pathlib import Path
import sys,argparse,json,hashlib,collections,numpy as np
from scipy.spatial.transform import Rotation
import dnm
from mesh import pack_dnm
args=argparse.ArgumentParser();args.add_argument('--baseline',required=True);args.add_argument('--output',required=True);args.add_argument('--report',required=True);a=args.parse_args();src=Path(a.baseline);dest=Path(a.output);data=src.read_bytes();assert hashlib.sha256(data).hexdigest()=='dadaddbd32530a68b9ef80413fc37741df073df3eacaca23c580951198fdfce9';p,ns=dnm.read(src);report={}
for n in ns:
 name=dnm.name(n)
 if name not in ['FlushDoorN0','FlushDoorN1']:continue
 m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);st=np.array([s.split()[1:] for s in n if s.startswith('STA ')][-1],float);h,pi,b=st[3:6]*np.pi/32768;R=Rotation.from_euler('YXZ',[-h,-pi,b]).as_matrix();axis=Rotation.from_matrix(R).as_rotvec();axis/=np.linalg.norm(axis);origin=np.linalg.lstsq(np.eye(3)-R,st[:3],rcond=1e-4)[0]
 cap=[];keep=[]
 for ids,c,bright in m.f:
  (cap if np.max(np.abs(np.abs(v[ids,0])-.46))<1e-6 else keep).append((ids,c,bright))
 assert cap;unique={};edge_count=collections.Counter();edge_directed={}
 for ids,c,bright in cap:
  points=[tuple(np.round(v[i],6)) for i in ids];key=tuple(sorted(points))
  if key in unique:continue
  unique[key]=(points,c,bright)
  for q,r in zip(points,points[1:]+points[:1]):
   key=tuple(sorted([q,r]));edge_count[key]+=1;edge_directed[key]=(q,r)
 # Connected hinge return reaches the existing collar with 10mm overlap; skin thickness retained.
 points=np.array(list({q for ps,c,b in unique.values() for q in ps}));zs=np.unique(points[:,2]);mid=np.array([np.mean([points[np.abs(points[:,2]-z)<1e-7,1].min(),points[np.abs(points[:,2]-z)<1e-7,1].max()]) for z in zs])
 def tip(q):
  q=np.array(q);t=origin+axis*((q[2]-origin[2])/axis[2]);t[0]+=np.sign(t[0])*.010;t[1]+=q[1]-np.interp(q[2],zs,mid);return t
 m.f=keep;before=len(m.f)
 for ps,c,bright in unique.values():
  q=[tip(x) for x in ps];m.face(q,c,bright);m.face(q[::-1],c,bright)
 for key,count in edge_count.items():
  if count!=1:continue
  q,r=edge_directed[key];poly=[q,r,tip(r),tip(q)];m.face(poly,(105,129,141));m.face(poly[::-1],(105,129,141))
 p[dnm.fil(n)]=m.srf();report[name]=dict(original_vertices_unchanged=True,original_skin_faces_retained=True,replaced_hinge_cap_faces=len(cap),return_boundary_segments=sum(x==1 for x in edge_count.values()),new_return_faces=len(m.f)-before,animation_exact=True)
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(pack_dnm(list(p.items()),sum(ns,[])).encode());Path(a.report).write_text(json.dumps(report,indent=2));print(hashlib.sha256(dest.read_bytes()).hexdigest())
