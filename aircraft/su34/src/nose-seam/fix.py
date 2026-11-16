from pathlib import Path
import sys,json,hashlib,numpy as np
from scipy.spatial.transform import Rotation
import dnm
import argparse
from mesh import pack_dnm
args=argparse.ArgumentParser();args.add_argument('--baseline',required=True);args.add_argument('--output',required=True);args.add_argument('--report',required=True);a=args.parse_args();src=Path(a.baseline);dest=Path(a.output);data=src.read_bytes();assert hashlib.sha256(data).hexdigest()=='dadaddbd32530a68b9ef80413fc37741df073df3eacaca23c580951198fdfce9'
p,ns=dnm.read(src);assert pack_dnm(list(p.items()),sum(ns,[])).encode()==data
report={}
for n in ns:
 name=dnm.name(n)
 if not name.startswith('FlushDoorN'):continue
 m=dnm.mesh(p[dnm.fil(n)]);v=np.array(m.v);st=np.array([x for x in n if x.startswith('STA ')][-1].split()[1:],float);h,pitch,b=st[3:6]*np.pi/32768;R=Rotation.from_euler('YXZ',[-h,-pitch,b]).as_matrix();axis=Rotation.from_matrix(R).as_rotvec();axis/=np.linalg.norm(axis);origin=np.linalg.lstsq(np.eye(3)-R,st[:3],rcond=1e-4)[0]
 edge=np.abs(np.abs(v[:,0])-.46)<1e-6;zkeys=np.unique(v[edge,2]);centers=np.array([(v[edge & (np.abs(v[:,2]-z)<1e-7),1].min()+v[edge & (np.abs(v[:,2]-z)<1e-7),1].max())/2 for z in zkeys])
 center=np.interp(v[:,2],zkeys,centers);tip=origin[None,:]+((v[:,2]-origin[2])/axis[2])[:,None]*axis[None,:];u=np.clip((np.abs(v[:,0])-.40)/.06,0,1);w=u*u*(3-2*u)
 before=np.linalg.norm(np.cross(v[edge]-origin,axis),axis=1)
 v[:,0]+=w*(tip[:,0]-np.sign(v[:,0])*.46)
 after=np.linalg.norm(np.cross(v[edge]-origin,axis),axis=1)
 m.v=[tuple(x) for x in v];p[dnm.fil(n)]=m.srf();report[name]=dict(changed_vertices=int(np.count_nonzero(w)),max_hinge_distance_before_mm=float(before.max()*1000),max_hinge_distance_after_mm=float(after.max()*1000),faces=len(m.f),animation_unchanged=True)
dest.parent.mkdir(parents=True,exist_ok=True);dnm.write(dest,p,ns)
Path(a.report).write_text(json.dumps(report,indent=2))
print(hashlib.sha256(dest.read_bytes()).hexdigest())
