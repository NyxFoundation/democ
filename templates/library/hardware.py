"""Hardware motion studies, with optional imported product models and studio HDRIs.
blender -b -t 8 -P templates/library/hardware.py -- --preset port-orbit --out out/library/port-orbit
"""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Euler
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))

p=argparse.ArgumentParser()
p.add_argument('--preset',required=True,choices=['port-orbit','rim-reveal','macro-controls','drone-orbit','humanoid-articulation','orbital-earth','terrain-flyover','asset-inspect'])
p.add_argument('--out',required=True)
p.add_argument('--duration',type=float,default=6)
p.add_argument('--fps',type=int,default=25)
p.add_argument('--width',type=int,default=960)
p.add_argument('--height',type=int,default=600)
p.add_argument('--samples',type=int,default=12)
p.add_argument('--config')
p.add_argument('--engine',choices=['eevee','cycles'],default='cycles')
p.add_argument('--frames',help='Render only comma-separated review frames')
p.add_argument('--no-render',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
config=json.loads(Path(a.config).read_text()) if a.config else {}
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
last=max(2,round(a.duration*a.fps));bpy.ops.wm.read_factory_settings(use_empty=True)
motion_last=max(2,round(float(config.get('motion_duration',a.duration))*a.fps))
s=bpy.context.scene
if a.engine=='cycles':
 s.render.engine='CYCLES';s.cycles.samples=a.samples;s.cycles.use_denoising=True
 s.render.use_persistent_data=True
 s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.035
 s.cycles.adaptive_min_samples=8;s.cycles.max_bounces=6
else:
 s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=a.samples
s.render.resolution_x=a.width;s.render.resolution_y=a.height;s.render.resolution_percentage=100
s.render.fps=a.fps;s.frame_start=1;s.frame_end=last
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB'
s.render.use_motion_blur=True;s.render.motion_blur_shutter=.18
s.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Studio void');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.003,.004,.007,1);bg.inputs['Strength'].default_value=.25;s.world=world
if config.get('hdri_path'):
 nodes=world.node_tree.nodes;links=world.node_tree.links
 tex=nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(config['hdri_path'])
 coords=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeMapping')
 mapping.inputs['Rotation'].default_value[2]=math.radians(config.get('hdri_rotation',35))
 links.new(coords.outputs['Generated'],mapping.inputs['Vector'])
 links.new(mapping.outputs['Vector'],tex.inputs['Vector']);links.new(tex.outputs['Color'],bg.inputs['Color'])
 bg.inputs['Strength'].default_value=config.get('hdri_strength',.38)
 dark=nodes.new('ShaderNodeBackground');dark.inputs['Color'].default_value=(0,0,0,1)
 ray=nodes.new('ShaderNodeLightPath');mix=nodes.new('ShaderNodeMixShader')
 links.new(ray.outputs['Is Camera Ray'],mix.inputs[0]);links.new(bg.outputs[0],mix.inputs[1]);links.new(dark.outputs[0],mix.inputs[2])
 output=next(n for n in nodes if n.type=='OUTPUT_WORLD');links.new(mix.outputs[0],output.inputs['Surface'])
 if a.engine=='eevee':
  # EEVEE probes need the actual environment, not a camera-ray world mix.
  links.new(bg.outputs[0],output.inputs['Surface']);s.render.film_transparent=True
  s.render.image_settings.color_mode='RGBA'


def import_product(path,width=5.6):
 """Keep the source geometry, UVs, normal maps and material assignments intact."""
 before=set(s.objects);previous_images=set(bpy.data.images);path=Path(path).resolve()
 if path.suffix.lower() in ['.usd','.usdz','.usdc','.usda']:
  bpy.ops.wm.usd_import(filepath=str(path),import_materials=True,import_textures_mode='IMPORT_PACK')
 elif path.suffix.lower() in ['.gltf','.glb']:
  bpy.ops.import_scene.gltf(filepath=str(path))
 elif path.suffix.lower()=='.blend':
  with bpy.data.libraries.load(str(path),link=False) as (source,target):target.objects=source.objects
  for ob in target.objects:
   if ob is not None and ob.name not in s.objects:s.collection.objects.link(ob)
 else:raise ValueError('Supported models: USDZ, USD, GLB, glTF, blend')
 imported=set(s.objects)-before
 if config.get('model_roots'):
  selected=[ob for ob in imported if ob.name in config['model_roots']]
  if len(selected)!=len(config['model_roots']):raise ValueError('Source model roots changed')
  keep=set(selected)
  for ob in selected:
   keep.update(ob.children_recursive)
   while ob.parent in imported:ob=ob.parent;keep.add(ob)
  for ob in imported-keep:bpy.data.objects.remove(ob,do_unlink=True)
  imported=keep
 for ob in list(imported):
  if ob.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(ob,do_unlink=True);imported.remove(ob)
 for image in set(bpy.data.images)-previous_images:
  if image.source!='FILE' or image.packed_file:continue
  if not Path(bpy.path.abspath(image.filepath)).is_file():
   candidates=[path.parent/image.filepath.removeprefix('//'),path.parent/'textures'/Path(image.filepath).name]
   resolved=next((p for p in candidates if p.is_file()),None)
   if resolved is None:raise FileNotFoundError(f'Missing texture for {path.name}: {image.filepath}')
   image.filepath=str(resolved);image.reload()
 bpy.context.view_layer.update()
 meshes=[ob for ob in imported if ob.type=='MESH' and not ob.hide_render]
 if not meshes:raise ValueError('The imported model contains no meshes')
 rotation=Euler(tuple(math.radians(v) for v in config.get('model_rotation',[0,0,0]))).to_matrix().to_4x4()
 points=[rotation@ob.matrix_world@Vector(p) for ob in meshes for p in ob.bound_box]
 lo=Vector([min(p[i] for p in points) for i in range(3)]);hi=Vector([max(p[i] for p in points) for i in range(3)])
 factor=width/(hi.x-lo.x);offset=Vector((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
 bpy.ops.object.empty_add();root=bpy.context.object;root.name='Imported product'
 for ob in imported:
  if ob.parent not in imported:
   matrix=ob.matrix_world.copy();ob.parent=root;ob.matrix_world=matrix
 root.matrix_world=Matrix.Scale(factor,4)@Matrix.Translation(offset)@rotation
 bpy.context.view_layer.update()
 return (hi.z-lo.z)*factor


def key(obj,prop,value,t):
 setattr(obj,prop,value);obj.keyframe_insert(prop,frame=1+round(t*(motion_last-1)))


def material(name,color,metal=0,rough=.3,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 node=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 node.inputs['Base Color'].default_value=(*color,1);node.inputs['Metallic'].default_value=metal;node.inputs['Roughness'].default_value=rough
 node.inputs['Emission Color'].default_value=(*color,1);node.inputs['Emission Strength'].default_value=emit
 return m


silver=material('Satin alloy',(.57,.61,.67),.8,.24)
black=material('Soft black',(.008,.011,.017),.25,.31)
ceramic=material('Warm ceramic',(.78,.78,.75),.06,.23)
led=material('Quiet mint status',(.12,.85,.55),.05,.25,3)


def box(name,loc,dims,mat,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 b=o.modifiers.new('Soft machined edges','BEVEL');b.width=bevel;b.segments=5
 o.modifiers.new('Surface normals','WEIGHTED_NORMAL');o.data.materials.append(mat)
 return o


def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
 for face in o.data.polygons:face.use_smooth=True
 return o


def cylinder(name,loc,radius,depth,mat):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=loc)
 o=bpy.context.object;o.name=name;o.data.materials.append(mat)
 bevel=o.modifiers.new('Edge radius','BEVEL');bevel.width=.035;bevel.segments=3
 o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return o


def light(name,pos,power,size,color=(1,1,1),target=(0,0,0),shape='DISK'):
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name=name
 o.data.energy=power;o.data.color=color;o.data.shape=shape;o.data.size=size
 if shape=='RECTANGLE':o.data.size_y=size*.2
 o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 return o


bpy.ops.object.empty_add(location=(0,0,.4));look=bpy.context.object;look.name='Camera target'
bpy.ops.object.camera_add(location=(7,-10,8));cam=bpy.context.object;cam.name='Product camera'
cam.data.lens=60;cam.data.clip_start=.05;cam.data.clip_end=200
track=cam.constraints.new('TRACK_TO');track.target=look;track.track_axis='TRACK_NEGATIVE_Z';track.up_axis='UP_Y'
cam.data.dof.use_dof=True;cam.data.dof.focus_object=look;cam.data.dof.aperture_fstop=7;s.camera=cam


def camera(t,pos,target,fstop=7):
 key(cam,'location',pos,t);key(look,'location',target,t)
 cam.data.dof.aperture_fstop=fstop;cam.data.dof.keyframe_insert('aperture_fstop',frame=1+round(t*(motion_last-1)))

rig=SimpleNamespace(scene=s,cam=cam,target=look,config=config,frames=last,fps=a.fps,duration=a.duration,
 key=key,light=light,shot=camera,material=material,box=box,sphere=sphere,import_product=import_product)


if a.preset=='asset-inspect':
 h=import_product(config['model_path'],5.6)
 meshes=[ob for ob in s.objects if ob.type=='MESH' and not ob.hide_render]
 points=[ob.matrix_world@Vector(p) for ob in meshes for p in ob.bound_box]
 width=max(p.x for p in points)-min(p.x for p in points)
 depth=max(p.y for p in points)-min(p.y for p in points)
 largest=max(width,depth,h);target=tuple(config.get('inspection_target',(0,0,h*.46)))
 # A neutral studio inspection makes missing maps, faceted silhouettes and
 # oversimplified controls visible before a model reaches a production shot.
 floor=material('Neutral studio sweep',(.09,.095,.10),0,.72)
 box('Studio sweep',(0,0,-.09),(200,200,.16),floor,.01)
 light('Large window',(-6,-5,10),1600,8,target=target,shape='RECTANGLE')
 light('White bounce',(7,-2,6),350,9,target=target)
 light('Strip reflection',(1,6,8),900,5,target=target,shape='RECTANGLE')
 distance=largest*float(config.get('inspection_camera_scale',3.25))
 camera(0,(distance*.58,-distance*.8,h*.46+distance*.45),target,11)
 cam.data.lens=75
 report={'model':config['model_path'],'meshes':len(meshes),'triangles':sum(sum(max(0,len(p.vertices)-2) for p in ob.data.polygons) for ob in meshes),
         'materials':len({m for ob in meshes for m in ob.data.materials if m}),
         'images':len(bpy.data.images),'dimensions':[width,depth,h]}
 (out.parent/'inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))

elif a.preset=='port-orbit':
 w=float(config.get('body_width',5.6));d=float(config.get('body_depth',4.8));h=float(config.get('body_height',1.4))
 if config.get('model_path'):
  h=import_product(config['model_path'],w)
 else:
  box('Compact enclosure',(0,0,.15+h/2),(w,d,h),silver,.34)
  box('Dark floating base',(0,0,.06),(w-.65,d-.65,.24),black,.16)
  for j,x in enumerate((-.55,.35)):
   box('Front port %d'%j,(x,-d/2-.005,.69),(.33,.045,.17),black,.075)
  sphere('Front status',(1.3,-d/2-.022,.66),(.035,.012,.035),led)
  for j,(x,width,height) in enumerate([(-1.8,.47,.31),(-.92,.48,.30),(.0,.63,.21),(1.0,.29,.18),(1.65,.29,.18)]):
   box('Rear port opening %d'%j,(x,d/2+.028,.77),(width,.025,height),black,.04)
 light('Key softbox',(-5,-4,10),900,8,target=(0,0,h/2),shape='RECTANGLE')
 light('Top fill',(3,-2,12),240,10,target=(0,0,h/2))
 light('Back edge',(2,6,7),500,6,target=(0,0,h/2),shape='RECTANGLE')
 # Sample the orbit on a sphere: interpolating front/rear Cartesian endpoints
 # would send the camera through the enclosure halfway through the turn.
 def eased(value):
  q=max(0,min(1,value));return q*q*(3-2*q)
 for frame in range(last):
  t=frame/(last-1)
  az=math.radians(-90+180*eased((t-.56)/.38))
  el=math.radians(77-65*eased(t/.29));r=float(config.get('camera_radius',18.5))
  camera(t,(r*math.cos(el)*math.cos(az),r*math.cos(el)*math.sin(az),h/2+r*math.sin(el)),(0,0,h/2),10)

elif a.preset=='rim-reveal':
 from quality_scenes import rim_reveal
 rim_reveal(rig)

elif a.preset=='macro-controls':
 if config.get('model_path'):
  import_product(config['model_path'],5.6)
  # Preserve the downloaded controls, lettering, speaker mesh and wear maps.
  # The camera follows the actual front panel rather than a generated knob grid.
  rake=light('Moving strip',(-4,-4,5),650,5,shape='RECTANGLE',target=(0,-.5,1.4))
  light('Gentle fill',(3,-4,4),160,7,target=(0,-.5,1.4))
  light('Top separation',(2,3,6),500,5,target=(0,0,1.5),shape='RECTANGLE')
  key(rake,'location',(-4,-4,5),0);key(rake,'location',(3,-3,5),1)
  cam.data.lens=75
  camera(0,(-2.5,-6.7,3.0),(-.65,-.55,1.25),8)
  camera(1,(1.5,-6.7,2.8),(.65,-.55,1.25),8)
 else:
  raise ValueError('macro-controls requires a textured model_path; choose a reviewed source asset')

elif a.preset=='drone-orbit':
 from quality_scenes import drone_orbit
 drone_orbit(rig)

elif a.preset=='humanoid-articulation':
 from quality_scenes import humanoid_articulation
 humanoid_articulation(rig)

elif a.preset=='orbital-earth':
 from quality_scenes import orbital_earth
 orbital_earth(rig)

elif a.preset=='terrain-flyover':
 from quality_scenes import terrain_flyover
 terrain_flyover(rig)

for ob in list(s.objects)+list(bpy.data.lights):
 if ob.animation_data and ob.animation_data.action:
  for layer in ob.animation_data.action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for point in fc.keyframe_points:
       if fc.data_path=='hide_render':point.interpolation='CONSTANT'
       else:point.handle_left_type='AUTO_CLAMPED';point.handle_right_type='AUTO_CLAMPED'
# USD/glTF importers may adopt the source stage's frame range. The study owns it.
s.frame_start=1;s.frame_end=last;s.render.fps=a.fps
if config.get('asset_sources'):
 text=bpy.data.texts.new('ASSET_SOURCES.json');text.write(json.dumps(config['asset_sources'],ensure_ascii=False,indent=2))
 s['asset_sources']=json.dumps(config['asset_sources'],ensure_ascii=False)
if config.get('model_path'):
 license_path=Path(config['model_path']).parent/'LICENSE'
 if license_path.exists():bpy.data.texts.new('THIRD_PARTY_LICENSE.txt').write(license_path.read_text())
s.frame_set(1);s.render.filepath=str(out/'f');bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out.parent/(a.preset+'.blend')))
if not a.no_render:
 if a.frames:
  for f in map(int,a.frames.split(',')):
   s.frame_set(f);s.render.filepath=str(out/('review-%04d.png'%f));bpy.ops.render.render(write_still=True)
 else:bpy.ops.render.render(animation=True)
