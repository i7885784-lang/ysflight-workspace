"""Fit the duct corner below/inboard of the untouched bay wall.
The limit1.07 equals bay X1.52 + lower Y(-.42) minus30mm;
normal clearance is30/sqrt(2)mm. Endpoints follow the existing shell.
"""
from pathlib import Path
import sys,numpy as np,json
import argparse
pa=argparse.ArgumentParser();pa.add_argument('--baseline',type=Path,required=True);pa.add_argument('--sections',type=Path,required=True);pa.add_argument('--helpers',type=Path);cli=pa.parse_args()
for helper in [cli.helpers,Path(__file__).resolve().parent.parent/'intake-front',Path(__file__).resolve().parent.parent/'su34-intake-front']:
 if helper:sys.path.insert(0,str(helper))
import dnm
p,n=dnm.read(cli.baseline);m=dnm.mesh(p['SourceAirframe.srf']);v=np.array(m.v);tri=np.array([v[[ids[0],ids[j],ids[j+1]]] for ids,c,b in m.f for j in range(1,len(ids)-1)]);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-15);zlo=tri[:,:,2].min(1);zhi=tri[:,:,2].max(1)
def section(sg,z):
 cut=1.07;o=np.array([sg*1.15,-.62,z]);nn=np.array([sg,1.,0]);base=o+nn*(cut-nn@o)/2;d=np.array([sg,-1.,0])/np.sqrt(2);ix=np.flatnonzero((zlo<=z+1e-8)&(zhi>=z-1e-8));t=tri[ix];e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);inv=np.divide(1.,det,out=np.zeros_like(det),where=abs(det)>1e-12);s=base-t[:,0];a=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);b=inv*np.einsum('j,ij->i',d,q);dist=inv*np.einsum('ij,ij->i',e2,q);points=base+dist[:,None]*d
 valid=(abs(det)>1e-12)&(a>=-1e-7)&(b>=-1e-7)&(a+b<=1.0000001)&(points[:,0]*sg>1.05)&(points[:,0]*sg<1.8)&(points[:,1]>-.85)&(points[:,1]<.02)&(np.einsum('ij,ij->i',normal[ix],o-points)>1e-6)
 records=sorted([(float(dist[i]),float(normal[ix[i]]@d),points[i]) for i in np.flatnonzero(valid)],key=lambda q:q[0]);hits=[]
 for row in records:
  if not hits or row[0]-hits[-1][0]>1e-5:hits.append(row)
 pairs=[(aa,bb) for aa,bb in zip(hits,hits[1:]) if aa[1]>1e-5 and bb[1]<-1e-5 and bb[0]-aa[0]>1e-7]
 if not pairs:return None
 aa,bb=max(pairs,key=lambda pp:pp[1][0]-pp[0][0]);return [aa[2].tolist(),bb[2].tolist()]
out={}
for sg in [1,-1]:
 rows=[];previous=None
 zs=list(np.linspace(-3.35,-1.47,25))+list(np.linspace(-1.46,-1.25,22))
 for z in zs:
  q=section(sg,float(z))
  if q is None:
   assert previous is not None
   lo=previous;hi=float(z)
   for _ in range(30):
    mid=(lo+hi)/2
    if section(sg,mid) is None:hi=mid
    else:lo=mid
   rows.append(dict(z=lo,points=section(sg,lo)));
   # Taper the strip into its existing side-wall attachment inside the shell.
   tip=section(sg,lo)[1];tip[2]=float(z);rows.append(dict(z=float(z),points=[tip,tip]));break
  rows.append(dict(z=float(z),points=q));previous=float(z)
 assert len(rows)>2
 out[str(sg)]=rows
 print('Fitted side',sg,'sections',len(rows))
cli.sections.write_text(json.dumps(out))
