"""Lossless topology/UV bridge for the isolated OBJ renderer test."""
from pathlib import Path
import numpy as np,struct,json,collections,hashlib,shutil
from PIL import Image
r=Path(__file__).resolve().parent;root=r/'model';out=r/'payload';out.mkdir(exist_ok=True)
materials={};current=None
for line in (root/'Su-34.mtl').read_text().splitlines():
 s=line.split()
 if not s:continue
 if s[0]=='newmtl':current={'name':s[1],'Kd':[1.,1.,1.],'d':1.};materials[s[1]]=current
 elif s[0]=='Kd':current['Kd']=list(map(float,s[1:4]))
 elif s[0]=='d':current['d']=float(s[1])
 elif s[0].startswith('map_'):current[s[0]]=' '.join(s[1:])
vertices=[];uvs=[];faces=[];face_uvs=[];groups=[];names=[];material='';objects=[];object_name=''
for line in (root/'Su-34.obj').open():
 s=line.split()
 if not s:continue
 if s[0]=='v':vertices.append(tuple(map(float,s[1:4])))
 elif s[0]=='vt':uvs.append(tuple(map(float,s[1:3])))
 elif s[0]=='usemtl':material=s[1]
 elif s[0]=='o':object_name=s[1]
 elif s[0]=='f':
  assert len(s)==4,'No implicit retriangulation allowed'
  fields=[q.split('/') for q in s[1:]];faces.append([int(q[0])-1 for q in fields]);face_uvs.append([int(q[1])-1 for q in fields]);groups.append(material);objects.append(object_name)
v=np.array(vertices,dtype=np.float64);uv=np.array(uvs,dtype=np.float64);f=np.array(faces,dtype=np.int32);ft=np.array(face_uvs,dtype=np.int32)
assert np.array_equal(f,ft),'Separate UV-index support required'
# Reconstruct smooth normals ONLY over vertices shared in the original OBJ.
# Exported vertex splits remain split; no welding, decimation or shape edits.
cross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);normals=np.zeros_like(v)
for k in range(3):np.add.at(normals,f[:,k],cross)
length=np.linalg.norm(normals,axis=1);valid=length>1e-15;normals[valid]/=length[valid,None];normals[~valid]=(0,1,0)
packed=np.c_[v,normals,uv].astype('<f4');rows=[];indices=[];cursor=0;converted={}
for name,mat in materials.items():
 sel=np.array([q==name for q in groups]);ids=f[sel].reshape(-1).astype('<u4');indices.append(ids);paths=[]
 for kind in ['map_Kd','map_normal','map_Ks','map_ao','map_d']:
  path=mat.get(kind)
  if not path:paths.append('-');continue
  source=root/path
  # The outermost Sketchfab archive carries the author's replacement livery.
  if kind=='map_Kd' and source.stem=='su_34_c':source=r/'unpacked/textures/su_34.png'
  dest=source.stem+'_'+kind+'.png';im=Image.open(source).convert('RGBA');im.save(out/dest)
  converted[dest]={'source':str(source.relative_to(r)),'size':list(im.size),'pixels_sha256':hashlib.sha256(im.tobytes()).hexdigest()};paths.append(dest)
 rows.append([len(ids),cursor,mat['d'],*mat['Kd'],*paths]);cursor+=len(ids)
with (out/'aircraft.mesh').open('wb') as stream:
 stream.write(b'YSOBJ001');stream.write(struct.pack('<II',len(v),cursor));stream.write(packed.tobytes());stream.write(np.concatenate(indices).tobytes())
(out/'aircraft.materials').write_text(str(len(rows))+'\n'+'\n'.join(' '.join(map(str,row)) for row in rows)+'\n')
assert cursor==579601*3
report={'vertices':len(v),'triangles':len(f),'objects':len(set(objects)),'uv_corners_exact':True,'indices_unchanged_except_material_batch_order':True,'position_max_float32_error_m':float(abs(packed[:,:3]-v).max()),'uv_max_float32_error':float(abs(packed[:,6:]-uv).max()),'normal_policy':'OBJ has no normals; area weighted normals over existing source vertex indices only','textures':converted,'materials':materials,'static_pose_only':True}
(r/'export-check.json').write_text(json.dumps(report,indent=2));print('Exported',len(f),'triangles,',len(v),'vertices,',len(rows),'materials; NO decimation')
