from pathlib import Path
import sys,json,hashlib,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));import dnm
from mesh import pack_dnm
import argparse
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();src=a.baseline;assert hashlib.sha256(src.read_bytes()).hexdigest()=='f12b117afa8f892c9e7213a296124db889123d54e8ff869a381feded903d4749';packs,nodes=dnm.read(src);lookup={dnm.name(n):n for n in nodes};key=dnm.fil(lookup['SourceAirframe']);m=dnm.mesh(packs[key]);v=np.array(m.v);tris=np.array([v[[ids[0],ids[j],ids[j+1]]] for ids,c,b in m.f for j in range(1,len(ids)-1)]);zmin=tris[:,:,2].min(1);zmax=tris[:,:,2].max(1)
norm=[];pair={}
for i,(ids,c,b) in enumerate(m.f):
 q=v[ids];n=np.cross(q[1]-q[0],q[2]-q[0]);n/=max(np.linalg.norm(n),1e-30);norm.append(n);g=tuple(sorted(tuple(x) for x in q));pair.setdefault(g,[]).append(i)
norm=np.array(norm);selected=[];kept_opposites=[]
for i,(ids,c,b) in enumerate(m.f):
 q=v[ids];sg=1 if q[:,0].mean()>0 else -1
 if (q[:,0]*sg).min()<.45 or (q[:,0]*sg).max()>1.85 or q[:,1].min()< -1.5 or q[:,1].max()>-.10 or q[:,2].min()< -4.2 or q[:,2].max()>2.0:continue
 target=q[:3].mean(0);z=target[2];cx=np.interp(z,[-3.49,-2.4,-1.3,-.35],[1.16,1.06,.99,1.035])+(0.03355 if sg>0 else 0);cy=np.interp(z,[-3.49,-2.4,-1.3,-.35],[-.60,-.61,-.655,-.655]);origin=np.array([sg*cx,cy,z]);delta=target-origin;distance=np.linalg.norm(delta)
 if distance<.08 or distance>.8 or norm[i]@(-delta)<=.0001:continue
 opposite=[j for j in pair[tuple(sorted(tuple(x) for x in q))] if norm[i]@norm[j]<-.99]
 direction=delta/distance;t=tris[(zmin<=z+1e-7)&(zmax>=z-1e-7)];e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0];h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-12;inv=np.divide(1.,det,out=np.zeros_like(det),where=valid);s=origin-t[:,0];u=inv*np.einsum('ij,ij->i',s,h);qq=np.cross(s,e1);ww=inv*np.einsum('j,ij->i',direction,qq);tt=inv*np.einsum('ij,ij->i',e2,qq);hit=valid&(u>=-1e-7)&(ww>=-1e-7)&(u+ww<=1.0000001)&(tt>1e-6)
 if not hit.any() or abs(float(tt[hit].min())-distance)>1e-4:continue
 selected.append(i);kept_opposites.extend(opposite)
assert selected and not set(selected)&set(kept_opposites)
def shade(z):
 u=float(np.clip((z+2.35)/(1.85+2.35),0,1));s=u*u*(3-2*u)
 return tuple(int(round(a+(b-a)*s)) for a,b in zip((18,22,25),(48,59,65)))
def recolor(lines,colors):
 out=list(lines);i=0
 for k,line in enumerate(out):
  if line.startswith('C '):
   if i in colors:out[k]='C '+' '.join(map(str,colors[i]))
   i+=1
 return out
packs[key]=recolor(packs[key],{i:shade(v[m.f[i][0],2].mean()) for i in selected})
for name in ['InsideIntakeL','InsideIntakeR']:
 k=dnm.fil(lookup[name]);liner=dnm.mesh(packs[k]);vv=np.array(liner.v);packs[k]=recolor(packs[k],{i:shade(vv[ids,2].mean()) for i,(ids,c,b) in enumerate(liner.f)})
out=a.output;out.write_bytes(pack_dnm(list(packs.items()),sum(nodes,[])).encode());report={'selected_inward_faces':selected,'unchanged_opposite_faces':sorted(set(kept_opposites)),'count':len(selected),'bounds':np.concatenate([v[m.f[i][0]] for i in selected]).min(0).tolist()+np.concatenate([v[m.f[i][0]] for i in selected]).max(0).tolist(),'model_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};a.report.write_text(json.dumps(report,indent=2));print({k:x for k,x in report.items() if k not in ['selected_inward_faces','unchanged_opposite_faces']})
