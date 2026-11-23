"""Clean cockpit-display prototype, measured parameters are provisional.
Not a factory CAD replica; front layout based on the supplied photo references.
No source-photo pixels or neural-source geometry reused.
"""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
r=Path('/tmp/su30-panel-repair');bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
def mat(name,color,rough=.5,metal=.0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
frame=mat('Coated charcoal metal',(.020,.023,.026),.48,.15)
body=mat('Rear housing charcoal',(.012,.015,.018),.6,.2)
rubber=mat('Button rubber',(.012,.015,.017),.62)
white=mat('White button marking',(.66,.68,.65),.65)
steel=mat('Fasteners',(.16,.18,.19),.32,.75)
dark=mat('Dark recesses',(.006,.008,.009),.8)
glass=mat('Inactive screen glass',(.001,.003,.005),.19,.12)
parts=[]
root=bpy.data.objects.new('SU30_MFD_Prototype',None);scene.collection.objects.link(root)
root['status']='Test approximation, not factory CAD; mounting dimensions provisional'
root['units']='metres';root['screen_active_width_m']=.127
root['button_count']=24;root['press_direction_local']='-Z';root['press_travel_m']=.0006
def finish(o,name,material,parent=root):
 o.name=name;o.data.materials.append(material);o.parent=parent;parts.append(o)
 for p in o.data.polygons:p.use_smooth=True
 return o
def bevel(o,w,segments=4):
 b=o.modifiers.new('Physical edge radius','BEVEL');b.width=w;b.segments=segments;b.limit_method='ANGLE'
 n=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=50
def box(name,loc,size,material,radius=.001,parent=root):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);finish(o,name,material,parent)
 if radius:bevel(o,radius)
 return o
def rr(w,h,rad,n=12):
 p=[]
 for cx,cy,start in [(w/2-rad,h/2-rad,0),(-w/2+rad,h/2-rad,90),(-w/2+rad,-h/2+rad,180),(w/2-rad,-h/2+rad,270)]:
  for k in range(n):
   a=math.radians(start+90*k/n);p.append((cx+rad*math.cos(a),cy+rad*math.sin(a)))
 return p
def ring(name,outer,inner,zlo,zhi,material):
 n=len(outer);assert n==len(inner)
 v=[(x,y,z) for z,p in [(zhi,outer),(zhi,inner),(zlo,outer),(zlo,inner)] for x,y in p];f=[]
 for i in range(n):
  j=(i+1)%n
  f.extend([(i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),(i,2*n+i,2*n+j,j),(n+j,3*n+j,3*n+i,n+i)])
 m=bpy.data.meshes.new(name);m.from_pydata(v,[],f);m.update();o=bpy.data.objects.new(name,m);scene.collection.objects.link(o)
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free();finish(o,name,material);return o
box('Rear housing',(0,0,-.023),(.162,.162,.044),body,.005)
box('Screen backing',(0,0,-.001),(.136,.136,.004),dark,.003)
bezel=ring('Front bezel',rr(.174,.174,.008),rr(.131,.131,.0035),-.004,.008,frame);bevel(bezel,.0008,3)
box('Screen surface',(0,0,.0021),(.130,.130,.0012),glass,.003)
for sx in (-1,1):
 for sy in (-1,1):
  cx,cy=sx*.067,sy*.093
  outer=[(x+cx,y+cy) for x,y in rr(.026,.026,.007)]
  # True circular through-hole, not a painted black dot.
  inner=[(cx+.0032*math.cos(2*math.pi*k/48),cy+.0032*math.sin(2*math.pi*k/48)) for k in range(48)]
  tab=ring('Mount tab %s %s'%(sx,sy),outer,inner,-.005,-.001,frame);bevel(tab,.0005,3)
  x,y=sx*.079,sy*.079
  bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.0036,depth=.0013,location=(x,y,.0088));finish(bpy.context.object,'Bezel screw %s %s'%(sx,sy),steel)
  box('Screw slot A %s %s'%(sx,sy),(x,y,.00949),(.0048,.00065,.00013),dark,.0002)
  box('Screw slot B %s %s'%(sx,sy),(x,y,.00950),(.00065,.0048,.00013),dark,.0002)
for side in ('TOP','BOTTOM','LEFT','RIGHT'):
 for i in range(6):
  along=(i-2.5)*.019
  x,y=(along,.075) if side=='TOP' else (along,-.075) if side=='BOTTOM' else (-.075,along) if side=='LEFT' else (.075,along)
  key=f'BTN_{side}_{i+1:02d}'
  box(key+'_seal',(x,y,.0085),(.0125,.0125,.001),dark,.0018)
  button=box(key,(x,y,.009),(.0105,.0105,.0022),rubber,.0008)
  button['control_id']=key;button['role']='independent push button';button['travel_m']=.0006
  # Child marking follows the button when it is pressed.
  bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.00105,depth=.00010,location=(0,0,.00116))
  dot=finish(bpy.context.object,key+'_mark',white,button)
  dot.location=(0,0,.00116)
# Apply actual bevel geometry so it survives conversion; smooth normals remain.
for o in parts:
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 o.select_set(False)
for o in [root]+parts:o.select_set(True)
bpy.context.view_layer.objects.active=bezel
out=r/'Su30_MFD_Clean_Test.glb'
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_extras=True,export_normals=True,export_texcoords=True,export_materials='EXPORT')
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=False
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.29,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
def aim(o):o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
for name,pos,energy,size in [('Key',(.2,.3,.4),2.1,.3),('Fill',(-.3,.1,.2),1.2,.3),('Rim',(.1,-.3,.1),1.8,.2)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;aim(o)
bpy.ops.object.camera_add(location=(0,0,.5));cam=bpy.context.object;cam.name='Preview camera';cam.data.type='ORTHO';cam.data.ortho_scale=.265;scene.camera=cam;aim(cam)
scene.render.filepath=str(r/'clean-front.png');bpy.ops.render.render(write_still=True)
cam.location=(.24,-.20,.40);cam.data.ortho_scale=.285;aim(cam)
scene.render.filepath=str(r/'clean-quarter.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(r/'Su30_MFD_Clean_Test.blend'),compress=True)
report={'status':'clean replacement prototype; not a factory dimensional replica','source_geometry_reused':False,'screen_width_m':.127,'bezel_width_m':.174,'housing_depth_m':.044,'separate_buttons':24,'button_control_ids':[o['control_id'] for o in parts if 'control_id' in o],'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts),'mesh_objects':len(parts),'shader':'standard glTF PBR, no emission texture, no baked source-photo reflections','style':'physical edge bevels and smooth normals; no forced faceting or decimation','not_integrated_into_game':True}
(r/'clean-report.json').write_text(json.dumps(report,indent=2));print('CLEAN_REPORT',json.dumps(report),flush=True)
