from pathlib import Path
import sys,numpy as np,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'su34-intake-front'));import dnm
from mesh import pack_dnm
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);cli=parser.parse_args();src=cli.baseline;assert hashlib.sha256(src.read_bytes()).hexdigest()=='ab047aeb24a384a8d2010058182191bfbf015e08a4470ac28fc42c9e6351e6b6';p,n=dnm.read(src);ls=p['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);old=v.copy();tri=np.array([v[[ids[0],ids[j],ids[j+1]]] for ids,c,b in m.f for j in range(1,len(ids)-1)]);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);norm=np.linalg.norm(normal,axis=1);tri=tri[(normal[:,1]>.65*norm)&(tri[:,:,1].max(1)<-.85)&(tri[:,:,2].max(1)>-.43)&(tri[:,:,2].min(1)<.49)];a=tri[:,0][:,[0,2]];e1=tri[:,1][:,[0,2]]-a;e2=tri[:,2][:,[0,2]]-a;det=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0];ok=abs(det)>1e-12;changes=[]
for i,q in enumerate(old):
 if not(.74<abs(q[0])<1.58 and -1.3<q[1]<-1.0 and -.42<q[2]<.48):continue
 query=q[[0,2]].copy();query[1]-=.003;d=query-a;u=np.divide(d[:,0]*e2[:,1]-d[:,1]*e2[:,0],det,out=np.zeros_like(det),where=ok);w=np.divide(e1[:,0]*d[:,1]-e1[:,1]*d[:,0],det,out=np.zeros_like(det),where=ok);hit=ok&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)
 if not hit.any():continue
 yy=tri[:,0,1]+u*(tri[:,1,1]-tri[:,0,1])+w*(tri[:,2,1]-tri[:,0,1]);target=float(max(yy[hit]));diff=target-q[1]
 if not(.012<diff<.095):continue
 t=float(np.clip((q[2]+.42)/.663,0,1));s=t*t*(3-2*t);v[i,1]=round(q[1]+.8*diff*s,6);changes.append(i)
for i in changes:ls[i+1]='V %.6f %.6f %.6f'%tuple(v[i])
k=ls.index('F');fi=0;changed=set(changes)
while k<len(ls) and ls[k]=='F':
 end=ls.index('E',k);ids=m.f[fi][0]
 if changed&set(ids):
  q=v[ids];norm=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);assert np.linalg.norm(norm)>1e-12;norm/=np.linalg.norm(norm)
  for j in range(k,end):
   if ls[j].startswith('N '):ls[j]='N '+' '.join('%.6f'%x for x in np.r_[q.mean(0),norm])
 k=end+1;fi+=1
p['SourceAirframe.srf']=ls;data=pack_dnm(list(p.items()),sum(n,[])).encode();cli.output.write_bytes(data);report=dict(vertices_moved=len(changes),unique_points=len(np.unique(old[changes],axis=0)),max_shift_m=float(np.max(v[:,1]-old[:,1])),sha256=hashlib.sha256(data).hexdigest());cli.report.write_text(json.dumps(report,indent=2));print(report)
