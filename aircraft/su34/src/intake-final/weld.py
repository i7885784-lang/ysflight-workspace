from pathlib import Path
import sys,numpy as np,json
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'su34-intake-front'));import dnm
from mesh import pack_dnm,Mesh
import argparse,hashlib
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);cli=p.parse_args();assert hashlib.sha256(cli.baseline.read_bytes()).hexdigest()=='dcc4e9869ed091cc70d6a90ec717d4a9467fb1e0ef1086971cf87b554995a5a6';packs,nodes=dnm.read(cli.baseline);ls=packs['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);mask=(np.abs(v[:,0])>.6)&(np.abs(v[:,0])<1.8)&(v[:,1]>-1.3)&(v[:,1]<-.15)&(v[:,2]>-.85)&(v[:,2]<1.9);ix=np.flatnonzero(mask);tree=cKDTree(v[ix]);pairs=tree.query_pairs(.004);parents=list(range(len(ix)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
for a,b in pairs:parents[find(a)]=find(b)
groups={}
for a in range(len(ix)):groups.setdefault(find(a),[]).append(ix[a])
moved=[]
for g in groups.values():
 q=v[g];span=np.linalg.norm(q.max(0)-q.min(0))
 if .0025<span<.0041 and ((.24<q[:,2].mean()<.25 and q[:,1].mean()<-1.1)):
  target=np.round(q.mean(0),6);moved.append({'count':len(g),'span_m':float(span),'center':target.tolist()});v[g]=target
# Preserve all polygon records; only replace confirmed mismatched rim vertices.
ls=list(ls)
for i,p in enumerate(v):ls[1+i]='V %.6f %.6f %.6f'%tuple(p)
packs['SourceAirframe.srf']=ls
out=cli.output;out.write_bytes(pack_dnm(list(packs.items()),sum(nodes,[])).encode());cli.report.write_text(json.dumps(moved,indent=2));print(moved)
