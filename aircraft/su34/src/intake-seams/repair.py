from pathlib import Path
import sys,numpy as np,json,hashlib,argparse
p=argparse.ArgumentParser(description="Local Su34 lower rim connectivity and upper bevel shade boundary repair")
p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--helpers',type=Path)
a=p.parse_args()
for helper in [a.helpers,Path(__file__).resolve().parent.parent/'intake-front',Path(__file__).resolve().parent.parent/'su34-intake-front']:
 if helper:sys.path.insert(0,str(helper))
import dnm
from mesh import pack_dnm
src=a.baseline
assert hashlib.sha256(src.read_bytes()).hexdigest()=='b6470cf3dcea7a07eac5df5ed17818268232a9fce170ac037b2e795e643c7365'
packs,nodes=dnm.read(src);ls=packs['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);keys={};first=ls.index('F');blocks=[];i=first
while i<len(ls) and ls[i]=='F':j=ls.index('E',i)+1;blocks.append(ls[i:j]);i=j
suffix=ls[i:]
for fi,(ids,c,b) in enumerate(m.f):
 q=v[ids];nn=np.cross(q[1]-q[0],q[2]-q[0]);nn/=max(np.linalg.norm(nn),1e-15)
 if not(.65<q[:,0].min() and q[:,0].max()<1.75 and q[:,1].max()<-1.0 and .240<q[:,2].max()<.246 and .04<q[:,2].min()<.06 and max(c)>110 and nn[1]<-.6):continue
 mapping={}
 for vi in ids:
  q0=v[vi]
  if not(.240<q0[2]<.246):continue
  cand=np.flatnonzero((abs(v[:,0]-q0[0])<.012)&(abs(v[:,2]-q0[2])<.001)&(v[:,1]<q0[1]-.025)&(v[:,1]>q0[1]-.065))
  if len(cand):mapping[vi]=int(cand[np.argmin(np.linalg.norm(v[cand]-q0,axis=1))])
 if mapping:keys[tuple(sorted(map(tuple,np.round(q,6))))]=mapping
# Only exterior floor faces are rerouted; inner channel floor is protected.
bottom=[];rim=[];newverts=list(m.v);out=[]
# Match the original outside material of the exact reverse face.
reverse={}
for ids,c,b in m.f:reverse.setdefault(tuple(sorted(map(tuple,np.round(v[ids],6)))),[]).append(c)
def clip(poly,above):
 result=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  aa=a[1]>=-.28 if above else a[1]<=-.28;bb=b[1]>=-.28 if above else b[1]<=-.28
  if aa:result.append(a)
  if aa!=bb:result.append(a+(b-a)*(-.28-a[1])/(b[1]-a[1]))
 return result
# The front bevel uses the existing outside material. Darkening starts behind its edge.
for fi,(ids,c,bright) in enumerate(m.f):
 block=blocks[fi];key=tuple(sorted(map(tuple,np.round(v[ids],6))))
 if key in keys:
  mapping=keys[key];ids=[next((dst for source,dst in mapping.items() if np.linalg.norm(v[vi]-v[source])<.00001),vi) for vi in ids];ids=[vi for j,vi in enumerate(ids) if j==0 or vi!=ids[j-1]];ids=ids[:-1] if ids[0]==ids[-1] else ids;q=v[ids];nn=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);nn/=np.linalg.norm(nn);block=['V '+' '.join(map(str,ids)) if l.startswith('V ') else 'N '+' '.join('%.6f'%x for x in np.r_[q.mean(0),nn]) if l.startswith('N ') else l for l in block];bottom.append(fi)
 q=v[ids];sg=1 if q[:,0].mean()>0 else -1
 shade=max(c)<100
 selected=shade and (q[:,0]*sg).min()>.65 and (q[:,0]*sg).max()<1.7 and q[:,1].min()>-.301 and q[:,1].max()>-.28 and q[:,1].max()<-.05 and q[:,2].min()>1.20 and q[:,2].max()<1.87
 if not selected:out+=block;continue
 exterior=next((cc for cc in reverse[key] if max(cc)>110),(55,109,137));rim.append(fi)
 for j in range(1,len(q)-1):
  tri=list(q[[0,j,j+1]])
  for above in [False,True]:
   poly=clip(tri,above)
   if len(poly)<3:continue
   poly=np.round(poly,6)
   if np.linalg.norm(np.sum(np.cross(poly,np.roll(poly,-1,axis=0)),axis=0))<1e-11:continue
   ix=list(range(len(newverts),len(newverts)+len(poly)));newverts.extend(map(tuple,poly));color=exterior if above else c
   out+=['V '+' '.join(map(str,ix)) if l.startswith('V ') else 'C '+' '.join(map(str,color)) if l.startswith('C ') else l for l in block]
packs['SourceAirframe.srf']=ls[:first]+['V %.6f %.6f %.6f'%q for q in newverts[len(v):]]+out+suffix;data=pack_dnm(list(packs.items()),sum(nodes,[])).encode();a.output.write_bytes(data);report=dict(bottom_faces=bottom,rim_faces=rim,original_vertices_unchanged=True,sha256=hashlib.sha256(data).hexdigest());a.report.write_text(json.dumps(report,indent=2));assert len(bottom)==24 and rim;assert packs.keys()==dnm.read(src)[0].keys();print(report)
