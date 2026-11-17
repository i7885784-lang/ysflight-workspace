from pathlib import Path
import sys,numpy as np,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));import dnm
from mesh import pack_dnm
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--report',type=Path,required=True);cli=parser.parse_args();src=cli.baseline;assert hashlib.sha256(src.read_bytes()).hexdigest()=='ab047aeb24a384a8d2010058182191bfbf015e08a4470ac28fc42c9e6351e6b6';packs,nodes=dnm.read(src);ls=packs['SourceAirframe.srf'];old=list(ls);m=dnm.mesh(ls);v=np.array(m.v);keys=set();maps={}
for fi,(ids,c,b) in enumerate(m.f):
 q=v[ids];nn=np.cross(q[1]-q[0],q[2]-q[0]);nn/=max(np.linalg.norm(nn),1e-15)
 if not(-1.6<q[:,0].min() and q[:,0].max()<-.74 and q[:,1].max()<-1.0 and .240<q[:,2].max()<.246 and q[:,2].min()<.06 and nn[1]<-.6):continue
 replacements={}
 for vi in ids:
  q0=v[vi]
  if not(.240<q0[2]<.246):continue
  cand=np.flatnonzero((abs(v[:,0]-q0[0])<.012)&(abs(v[:,2]-q0[2])<.001)&(v[:,1]<q0[1]-.025)&(v[:,1]>q0[1]-.065))
  if len(cand):replacements[vi]=int(cand[np.argmin(np.linalg.norm(v[cand]-q0,axis=1))])
 if replacements:
  key=tuple(sorted(map(tuple,np.round(q,6))));keys.add(key);maps[key]=replacements
k=ls.index('F');fi=0;affected=[]
while k<len(ls) and ls[k]=='F':
 end=ls.index('E',k);ids=m.f[fi][0];key=tuple(sorted(map(tuple,np.round(v[ids],6))))
 if key in keys:
  mapping=maps[key];new=[]
  for vi in ids:
   # Match reverse-side records geometrically as well.
   match=next((dst for source,dst in mapping.items() if np.linalg.norm(v[vi]-v[source])<.00001),vi);new.append(match)
  q=v[new];normal=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);assert np.linalg.norm(normal)>1e-10;normal/=np.linalg.norm(normal)
  for j in range(k,end):
   if ls[j].startswith('V '):ls[j]='V '+' '.join(map(str,new))
   elif ls[j].startswith('N '):ls[j]='N '+' '.join('%.6f'%x for x in np.r_[q.mean(0),normal])
  affected.append(fi)
 fi+=1;k=end+1
assert affected;packs['SourceAirframe.srf']=ls;data=pack_dnm(list(packs.items()),sum(nodes,[])).encode();cli.output.write_bytes(data);patch={str(i):{'old':a,'new':b} for i,(a,b) in enumerate(zip(old,ls)) if a!=b};cli.output.with_suffix('.reverse.json').write_text(json.dumps(patch));report=dict(affected_faces=affected,vertices_unchanged=True,colors_unchanged=True,sha256=hashlib.sha256(data).hexdigest());cli.report.write_text(json.dumps(report,indent=2));print(report)
