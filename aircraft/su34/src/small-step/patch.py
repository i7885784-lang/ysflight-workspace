from pathlib import Path
import sys,json,hashlib,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));import dnm
from mesh import pack_dnm
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);cli=parser.parse_args();src=cli.baseline;data=src.read_bytes();assert hashlib.sha256(data).hexdigest()=='ab047aeb24a384a8d2010058182191bfbf015e08a4470ac28fc42c9e6351e6b6';packs,nodes=dnm.read(src);ls=packs['SourceAirframe.srf'];old=list(ls);m=dnm.mesh(ls);v=np.array(m.v);moved=[]
# Only the highlighted right-side lower corner ring; max6mm up and10mm aft.
for i,q in enumerate(v.copy()):
 if -1.43<q[0]<-.78 and -1.235<q[1]<-1.16 and .242<q[2]<.246:
  weight=float(np.clip((-1.16-q[1])/.045,0,1));v[i,1]=round(q[1]+.010*weight,6);v[i,2]=round(q[2],6);ls[i+1]='V %.6f %.6f %.6f'%tuple(v[i]);moved.append(i)
assert moved;changed=set(moved);k=ls.index('F');fi=0
while k<len(ls) and ls[k]=='F':
 end=ls.index('E',k);ids=m.f[fi][0]
 if changed&set(ids):
  q=v[ids];nn=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);assert np.linalg.norm(nn)>1e-12;nn/=np.linalg.norm(nn)
  for j in range(k,end):
   if ls[j].startswith('N '):ls[j]='N '+' '.join('%.6f'%x for x in np.r_[q.mean(0),nn])
 k=end+1;fi+=1
patch={str(i):{'old':a,'new':b} for i,(a,b) in enumerate(zip(old,ls)) if a!=b};packs['SourceAirframe.srf']=ls;out=pack_dnm(list(packs.items()),sum(nodes,[])).encode();cli.output.write_bytes(out);cli.output.with_suffix('.reverse.json').write_text(json.dumps(patch));report=dict(moved_vertices=len(moved),unique_points=len(np.unique(np.array(m.v)[moved],axis=0)),max_up_m=.010,max_aft_m=0,sha256=hashlib.sha256(out).hexdigest());cli.report.write_text(json.dumps(report,indent=2));print(report)
