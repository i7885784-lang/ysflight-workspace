from pathlib import Path
import sys,json,hashlib,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));import dnm
from mesh import pack_dnm
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);cli=parser.parse_args();src=cli.baseline;raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()=='37240eded3ba637b8e0f7b3f3b89444ae8a8ccf9f15dc2f5d299735384d352b0';p,n=dnm.read(src);ls=p['SourceAirframe.srf'];old=list(ls);m=dnm.mesh(ls);v=np.array(m.v);before=v.copy();moved=[]
def smooth(t):t=float(np.clip(t,0,1));return t*t*(3-2*t)
for i,q in enumerate(before):
 x,y,z=q;sg=1 if x>0 else -1;cx=1.15994 if sg>0 else -1.12603
 if not(.60<abs(x)<1.80 and -1.4<y<-.15 and -2.4<z<2.0):continue
 depth=smooth((z+2.4)/2.3);join=smooth((-.15-y)/.13);side=smooth((1.80-abs(x))/.15);w=depth*join*side
 delta=x-cx;newx=cx+delta*(1-.06*w)
 # Slightly stronger chamfer at the lower corners, max another8mm per edge.
 bevel=.008*smooth((-1.02-y)/.22)*smooth((abs(delta)-.28)/.13)*w
 newx-=np.sign(delta)*bevel
 v[i,0]=round(newx,6)
 if v[i,0]!=x:ls[i+1]='V %.6f %.6f %.6f'%tuple(v[i]);moved.append(i)
changed=set(moved);k=ls.index('F');fi=0
while k<len(ls) and ls[k]=='F':
 end=ls.index('E',k);ids=m.f[fi][0]
 if changed&set(ids):
  q=v[ids];nn=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);assert np.linalg.norm(nn)>1e-11;nn/=np.linalg.norm(nn)
  for j in range(k,end):
   if ls[j].startswith('N '):ls[j]='N '+' '.join('%.6f'%x for x in np.r_[q.mean(0),nn])
 k=end+1;fi+=1
p['SourceAirframe.srf']=ls;out=pack_dnm(list(p.items()),sum(n,[])).encode();cli.output.write_bytes(out);patch={str(i):{'old':a,'new':b} for i,(a,b) in enumerate(zip(old,ls)) if a!=b};cli.output.with_suffix('.reverse.json').write_text(json.dumps(patch));report=dict(scale_at_mouth=.94,centres=[1.15994,-1.12603],height_and_z_exact=bool(np.array_equal(before[:,1:],v[:,1:])),corner_extra_max_m=.008,moved_vertices=len(moved),max_x_shift_m=float(abs(v[:,0]-before[:,0]).max()),sha256=hashlib.sha256(out).hexdigest());cli.report.write_text(json.dumps(report,indent=2));print(report)
