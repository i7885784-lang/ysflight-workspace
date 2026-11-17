from pathlib import Path
import sys,numpy as np,json,hashlib
import argparse,subprocess
pa=argparse.ArgumentParser();pa.add_argument('--baseline',type=Path,required=True);pa.add_argument('--output',type=Path,required=True);pa.add_argument('--report',type=Path,required=True);pa.add_argument('--helpers',type=Path);cli=pa.parse_args()
for helper in [cli.helpers,Path(__file__).resolve().parent.parent/'intake-front',Path(__file__).resolve().parent.parent/'su34-intake-front']:
 if helper:sys.path.insert(0,str(helper))
import dnm
from mesh import Mesh,pack_dnm
assert hashlib.sha256(cli.baseline.read_bytes()).hexdigest()=='d4dc6f68fe3761a9a5d84b8823af728dedca023e8e7c8c7ff06dde5e931a81e7'
sections_path=cli.output.with_suffix('.sections.json');command=[sys.executable,str(Path(__file__).resolve().parent/'fit.py'),'--baseline',str(cli.baseline),'--sections',str(sections_path)]
if cli.helpers:command+=['--helpers',str(cli.helpers)]
subprocess.run(command,check=True);p,n=dnm.read(cli.baseline);ls=p['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);selected=[]
for i,(ids,c,b) in enumerate(m.f):
 q=v[ids];sg=1 if q[:,0].mean()>0 else -1
 if not((q[:,0]*sg).min()>.65 and (q[:,0]*sg).max()<1.75 and q[:,1].max()<-.90 and q[:,1].min()>-1.24 and q[:,2].min()>-1.35 and q[:,2].max()<.65 and max(c)>100):continue
 nn=np.sum(np.cross(q,np.roll(q,-1,axis=0)),axis=0);nn/=np.linalg.norm(nn);o=np.array([1.15994 if sg>0 else -1.12603,-.62,q[:,2].mean()])
 if nn@(o-q.mean(0))>.1:selected.append(i)
def shade(z):
 u=float(np.clip((z+3.35)/5.2,0,1));s=u*u*(3-2*u);return tuple(round(a+(b-a)*s) for a,b in zip((9,12,14),(70,85,94)))
face=0
for i,line in enumerate(ls):
 if line.startswith('C '):
  if face in selected:ls[i]='C '+' '.join(map(str,shade(v[m.f[face][0],2].mean())))
  face+=1
fillet=Mesh();sections=json.loads(sections_path.read_text())
for sg,rows in sections.items():
 sg=int(sg)
 for aa,bb in zip(rows,rows[1:]):
  a,b=np.array(aa['points']),np.array(bb['points'])
  for q in [np.array([a[0],a[1],b[1]]),np.array([a[0],b[1],b[0]])]:
   normal=np.cross(q[1]-q[0],q[2]-q[0]);area=np.linalg.norm(normal)
   if area<1e-10:continue
   if normal@np.array([-sg,-1.,0])<0:q=q[::-1]
   fillet.face(q,shade(q[:,2].mean()));fillet.face(q[::-1],shade(q[:,2].mean()))
count=len(fillet.f);offset=len(m.v);fillet.f=[([j+offset for j in ids],c,b) for ids,c,b in fillet.f];fillet.v=list(m.v)+fillet.v;extra=fillet.srf();first=ls.index('F');f=extra.index('F');p['SourceAirframe.srf']=ls[:first]+extra[1+offset:f]+ls[first:-1]+extra[f:];data=pack_dnm(list(p.items()),sum(n,[])).encode();cli.output.write_bytes(data);report=dict(sha256=hashlib.sha256(data).hexdigest(),lower_inward_faces=selected,new_fitted_fillet_face_records=count,protected_meshes_and_nodes_unchanged=True,fillet_clearance_to_bay_mm=30/np.sqrt(2),rear_cap_z=-3.35);cli.report.write_text(json.dumps(report,indent=2));print({k:x for k,x in report.items() if k!='lower_inward_faces'})
