from pathlib import Path
import sys,json,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'intake-front'));sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'su34-intake-front'));import dnm
from mesh import pack_dnm
import argparse
p0=argparse.ArgumentParser();p0.add_argument('--baseline',type=Path,required=True);p0.add_argument('--output',type=Path,required=True);cli=p0.parse_args();p,n=dnm.read(cli.baseline);sel=set([205, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 2087, 2088, 2089, 2090, 2091, 2092, 2093, 2094, 2095, 2096, 2097, 2098, 2099, 2100, 2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108, 2109, 2110, 2111, 2112, 2113, 2114, 2115, 2116, 2117, 2144, 2145, 2146, 2147, 2152, 2153, 2154, 2155, 2156, 2157, 2158, 2159, 2160, 2161, 2162, 2163, 2164, 2165, 2166, 2177, 2178, 2179, 2182, 2184, 2185, 2186, 2187, 2188, 2189, 2190, 2191, 2192, 2193, 2373, 2374, 2375, 2376, 2377, 2749, 2750, 2751, 2752, 2753, 2754, 2755, 2756, 2757, 2758, 2759, 2760, 2761, 2762, 2763, 2764, 2780, 2783, 2799, 2800, 2801, 2802, 2803, 2804, 2805, 2806, 2807, 2808, 2809, 2810, 2813, 2814, 2815, 2816, 2817, 2818, 2819, 2820, 2821, 2822, 2823, 2824, 2825, 2826, 2827, 2828, 2829, 2830, 2831, 2832, 2833, 2834, 2955, 3264, 3265, 3266, 3267, 3268, 3269, 3270, 3271, 3272, 3273, 3274, 3275, 3276, 3277, 3288, 3289, 3290, 3291, 3292, 3293, 3294, 3295, 3296, 3297, 3298, 3299, 3300, 3301, 3302, 3303, 3304, 3305, 3306, 3307, 3308, 3309, 3310, 3364, 3365, 3366, 3367, 3368, 3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377, 3378, 3379, 3380, 3381, 3382, 3383, 3384, 3385, 3386, 3387, 3451, 3452, 3453, 3454, 3455, 3456, 3457, 3458, 3459, 3460, 3461, 3462, 3463, 3938, 3939, 3940, 3954, 3955, 3956, 3958, 3986, 3987, 3988, 3991, 3992, 3993, 3994, 3995, 3996, 3997, 4000, 4687, 4689, 10305, 10307, 10313]);ls=p['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);first=ls.index('F');blocks=[];k=first
while k<len(ls) and ls[k]=='F':j=ls.index('E',k)+1;blocks.append(ls[k:j]);k=j
verts=list(m.v);out=[]
def clip(poly,z,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  aa=a[2]>=z if above else a[2]<=z;bb=b[2]>=z if above else b[2]<=z
  if aa:out.append(a)
  if aa!=bb:out.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
 return out
for i,(ids,c,b) in enumerate(m.f):
 block=blocks[i]
 if i not in sel:out+=block;continue
 for j in range(1,len(ids)-1):
  tri=v[[ids[0],ids[j],ids[j+1]]];lo,hi=tri[:,2].min(),tri[:,2].max();cuts=[lo]+[z for z in [-3.35,-2.2,-1.0,.3,1.85] if lo+1e-6<z<hi-1e-6]+[hi]
  pieces=[list(tri)] if hi-lo<1e-8 else [clip(clip(list(tri),a,True),b,False) for a,b in zip(cuts,cuts[1:])]
  for q in pieces:
   if len(q)<3:continue
   q=np.round(q,6)
   if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-11:continue
   z=q[:,2].mean();u=float(np.clip((z+3.35)/5.2,0,1));s=u*u*(3-2*u);col=tuple(round(a+(b-a)*s) for a,b in zip((9,12,14),(70,85,94)));ix=list(range(len(verts),len(verts)+len(q)));verts.extend(map(tuple,q));out+=['V '+' '.join(map(str,ix)) if l.startswith('V ') else 'C '+' '.join(map(str,col)) if l.startswith('C ') else l for l in block]
p['SourceAirframe.srf']=['SURF']+['V %.6f %.6f %.6f'%v for v in verts]+out+ls[k:]
(cli.output).write_bytes(pack_dnm(list(p.items()),sum(n,[])).encode())
# Correct the two confirmed lower-skin peaks and their mirrored counterparts.
p,n=dnm.read(cli.output);ls=p['SourceAirframe.srf'];m=dnm.mesh(ls);vv=np.array(m.v);changed=set()
for old,new_y in [((1.441706,-1.222474,-2.805364),-1.1868),((1.458259,-1.211039,-2.976760),-1.1864),((-1.408188,-1.222306,-2.805222),-1.186632),((-1.424762,-1.210860,-2.976615),-1.186221)]:
 ids=np.flatnonzero(np.linalg.norm(vv-np.array(old),axis=1)<.000012);assert len(ids)>0;vv[ids,1]=new_y;changed.update(map(int,ids))
for i in changed:ls[i+1]='V %.6f %.6f %.6f'%tuple(vv[i])
k=ls.index('F');face_i=0
while k<len(ls) and ls[k]=='F':
 end=ls.index('E',k);ids=m.f[face_i][0]
 if set(ids)&changed:
  q=vv[ids];normal=np.cross(q[1]-q[0],q[2]-q[0]);normal/=np.linalg.norm(normal);center=q.mean(0)
  for j in range(k,end):
   if ls[j].startswith('N '):ls[j]='N '+' '.join('%.6f'%x for x in np.r_[center,normal])
 face_i+=1;k=end+1
p['SourceAirframe.srf']=ls;(cli.output).write_bytes(pack_dnm(list(p.items()),sum(n,[])).encode())
# Authorized cosmetic closure of the external upper attachment gap.
p,n=dnm.read(cli.output);ls=p['SourceAirframe.srf'];m=dnm.mesh(ls);v=np.array(m.v);tri=np.array([v[[ids[0],ids[j],ids[j+1]]] for ids,c,b in m.f for j in range(1,len(ids)-1)]);patch=None
from mesh import Mesh
patch=Mesh()
def upper_y(x,z):
 aa=tri[:,0][:,[0,2]];e1=tri[:,1][:,[0,2]]-aa;e2=tri[:,2][:,[0,2]]-aa;d=np.array([x,z])-aa;det=e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0];ok=abs(det)>1e-12;u=np.divide(d[:,0]*e2[:,1]-d[:,1]*e2[:,0],det,out=np.zeros_like(det),where=ok);w=np.divide(e1[:,0]*d[:,1]-e1[:,1]*d[:,0],det,out=np.zeros_like(det),where=ok);yy=tri[:,0,1]+u*(tri[:,1,1]-tri[:,0,1])+w*(tri[:,2,1]-tri[:,0,1]);hits=yy[ok&(u>=0)&(w>=0)&(u+w<=1)&(yy<-.01)&(yy>-.215)];assert len(hits)>0;return float(max(hits))+.0003
for sg in [1,-1]:
 a=np.array([.694603,-.28,1.768196]);b=np.array([1.473162,-.28,1.658129])
 if sg<0:
  for q in [a,b]:
   target=q.copy();target[0]=-target[0]+.03355;q[:]=v[np.argmin(np.linalg.norm(v-target,axis=1))]
 bottom=[a+(b-a)*t for t in np.linspace(0,1,9)];top=[np.array([q[0],upper_y(q[0],q[2]),q[2]]) for q in bottom]
 for i in range(8):
  for q in [[bottom[i],bottom[i+1],top[i+1]],[bottom[i],top[i+1],top[i]]]:
   if np.cross(np.array(q[1])-q[0],np.array(q[2])-q[0])[2]<0:q=q[::-1]
   patch.face(q,(103,153,174));patch.face(q[::-1],(42,51,57))
# Append physical seam joins to the existing SourceAirframe, retaining old records.
offset=len(m.v);patch.f=[([i+offset for i in ids],c,b) for ids,c,b in patch.f];patch.v=list(m.v)+patch.v;extra=patch.srf();f=extra.index('F');first=ls.index('F');p['SourceAirframe.srf']=ls[:first]+extra[1+offset:f]+ls[first:-1]+extra[f:];(cli.output).write_bytes(pack_dnm(list(p.items()),sum(n,[])).encode())
