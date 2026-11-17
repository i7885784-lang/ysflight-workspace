"""Su30-style matte, closed intake depth, fitted to the existing Su34 liner."""
from pathlib import Path
import argparse,hashlib,json,math,numpy as np
import dnm
from mesh import pack_dnm,Mesh
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args();src=Path(a.baseline);assert hashlib.sha256(src.read_bytes()).hexdigest()=='ae7659092f75d61393c72462ffd9b6f716e58a6ae8953cd8d76f16e4a0acbfa4';packs,nodes=dnm.read(src);report={}
for node in nodes:
 name=dnm.name(node)
 if name not in ['InsideIntakeL','InsideIntakeR']:continue
 key=dnm.fil(node);lines=packs[key];old=dnm.mesh(lines);v=np.array(old.v);rear=float(v[:,2].min());front=float(v[:,2].max());end=np.unique(v[np.abs(v[:,2]-rear)<1e-7],axis=0);center=np.mean(end,axis=0);angles=np.arctan2(end[:,1]-center[1],end[:,0]-center[0]);end=end[np.argsort(angles)];assert len(end)==24
 # Keep all original vertices, indices and normal records. Only internal C records change.
 first=lines.index('F');face_lines=list(lines[first:-1]);face_index=0
 for i,line in enumerate(face_lines):
  if not line.startswith('C '):continue
  ids,color,bright=old.f[face_index];z=float(v[ids,2].mean());u=max(0,min(1,(z-rear)/(front-rear)));c=tuple(int(round(x+(y-x)*u**1.5)) for x,y in zip((18,22,25),(48,59,65)))
  if color==(71,79,85):c=tuple(min(255,x+3) for x in c)
  face_lines[i]='C '+' '.join(map(str,c));face_index+=1
 assert face_index==len(old.f)
 cap=Mesh()
 for i in range(len(end)):
  q=np.round([center,end[i],end[(i+1)%len(end)]],6);cap.face(q,(18,22,25));cap.face(q[::-1],(18,22,25))
 offset=len(old.v);cap.f=[([i+offset for i in ids],c,b) for ids,c,b in cap.f];cap.v=list(old.v)+cap.v;extra=cap.srf();end_vertices=extra.index('F');packs[key]=lines[:first]+extra[1+offset:end_vertices]+face_lines+extra[end_vertices:]
 report[name]={'front_z_m':front,'rear_z_m':rear,'existing_liner_geometry_normals_indices_exact':True,'closed_rear_triangles':48,'rear_matte_rgb':[18,22,25],'emissive':False,'original_compressors_unchanged_behind_dark_rear':True}
data=pack_dnm(list(packs.items()),sum(nodes,[])).encode();Path(a.output).write_bytes(data);report['model_sha256']=hashlib.sha256(data).hexdigest();Path(a.report).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
