"""Hardware motion studies, with optional imported product models and studio HDRIs.
blender -b -t 8 -P templates/library/hardware.py -- --preset port-orbit --out out/library/port-orbit
"""
import argparse,json,math,sys,xml.etree.ElementTree as ET
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion

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
 for i,x in enumerate((-1.55,1.55)):
  bpy.ops.object.empty_add(location=(x,0,.2));root=bpy.context.object;root.name='Sensor module %d'%i
  pieces=[sphere('Ceramic sensor shell',(0,0,.35),(.79,.60,.74),ceramic),
          box('Sensor stem',(.23,0,-.7),(.48,.45,1.35),ceramic,.22),
          sphere('Acoustic aperture',(0,-.575,.44),(.32,.035,.34),black),
          sphere('Inner diaphragm',(0,-.61,.44),(.19,.022,.20),silver)]
  for piece in pieces:piece.parent=root
  for t,rz,ry in [(0,(-12 if i==0 else 14),(-20 if i==0 else 25)),(.65,(-5 if i==0 else 8),(15 if i==0 else -12)),(1,5,20 if i==0 else -5)]:
   key(root,'rotation_euler',(math.radians(-10),math.radians(ry),math.radians(rz)),t)
 rim1=light('Left outline',(-4,3,4),900,5,(.75,.83,1))
 rim2=light('Right outline',(5,3,1),850,4)
 fill=light('Material reveal',(-2,-5,5),0,6,(1,.98,.92))
 for t,power in [(0,0),(.17,0),(.55,1000),(.78,1450),(1,1450)]:key(fill.data,'energy',power,t)
 camera(0,(0,-13,3),(0,0,0),9);camera(1,(2,-12.5,3.4),(0,0,0),9)

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
 import_product(config['model_path'],5.7)
 root=s.objects['Imported product'];root.location.z=.45
 # The source model already has UVs, metallic/roughness maps and real propellers.
 for ob in s.objects:
  if 'PropClockwise' in ob.name or 'PropCounterClockwise' in ob.name:
   key(ob,'rotation_euler',ob.rotation_euler.copy(),0)
   rotation=ob.rotation_euler.copy();rotation.y+=math.tau*18*(1 if 'Counter' in ob.name else -1)
   key(ob,'rotation_euler',rotation,1)
 for t,z in [(0,.45),(.35,.55),(.75,.47),(1,.52)]:key(root,'location',(0,0,z),t)
 light('Overhead strip',(-4,-4,9),1100,8,shape='RECTANGLE')
 light('Camera fill',(4,-4,5),450,6);light('Rear separation',(2,6,7),900,7)
 for i in range(last):
  t=i/(last-1);angle=math.radians(-112+76*t)
  camera(t,(12.5*math.cos(angle),12.5*math.sin(angle),7.2-1.2*t),(0,0,1),9)

elif a.preset=='humanoid-articulation':
 source=Path(config['model_path']);tree=ET.parse(source).getroot()
 shell=material('Pearl alloy shell',(.53,.55,.57),.55,.29)
 jointmat=material('Graphite joint housings',(.018,.023,.028),.28,.34)
 rubber=material('Elastomer hands',(.012,.015,.018),0,.55)
 nodes={};rotors={};rest={};axes={}
 for link in tree.findall('link'):
  bpy.ops.object.empty_add();node=bpy.context.object;node.name=link.get('name');nodes[node.name]=node
  for visual in link.findall('visual'):
   mesh=visual.find('geometry/mesh')
   if mesh is None:continue
   path=source.parent/'meshes'/mesh.get('filename').split('/')[-1]
   before=set(s.objects);bpy.ops.wm.stl_import(filepath=str(path))
   origin=visual.find('origin');xyz=[0,0,0];rpy=[0,0,0]
   if origin is not None:
    xyz=list(map(float,origin.get('xyz','0 0 0').split()));rpy=list(map(float,origin.get('rpy','0 0 0').split()))
   for ob in set(s.objects)-before:
    ob.parent=node;ob.location=xyz;ob.rotation_euler=rpy
    ob.data.materials.append(rubber if 'hand' in node.name else jointmat if any(x in node.name for x in ['pitch','roll','yaw','support','contour']) else shell)
    for face in ob.data.polygons:face.use_smooth=True
    if hasattr(ob.data,'set_sharp_from_angle'):ob.data.set_sharp_from_angle(angle=.7)
 for joint in tree.findall('joint'):
  parent=nodes[joint.find('parent').get('link')];child=nodes[joint.find('child').get('link')]
  bpy.ops.object.empty_add();origin=bpy.context.object;origin.name=joint.get('name');origin.parent=parent
  frame=joint.find('origin')
  if frame is not None:
   origin.location=list(map(float,frame.get('xyz','0 0 0').split()))
   origin.rotation_euler=list(map(float,frame.get('rpy','0 0 0').split()))
  bpy.ops.object.empty_add();rotor=bpy.context.object;rotor.name=joint.get('name')+' motion';rotor.parent=origin
  rotor.rotation_mode='QUATERNION';child.parent=rotor;rotors[joint.get('name')]=rotor
  axis=joint.find('axis');axes[joint.get('name')]=Vector(list(map(float,axis.get('xyz','0 0 1').split()))) if axis is not None else Vector((0,0,1))
 roots=[ob for ob in nodes.values() if ob.parent is None]
 bpy.ops.object.empty_add();root=bpy.context.object;root.name='G1 assembly'
 for ob in roots:ob.parent=root
 root.scale=(3.1,)*3;root.rotation_euler.z=-math.pi/2
 bpy.context.view_layer.update()
 low=min((ob.matrix_world@Vector(p)).z for ob in s.objects if ob.type=='MESH' for p in ob.bound_box);root.location.z=-low
 # A slow, readable articulation study. This is not a locomotion controller.
 for name,rotor in rotors.items():
  if 'shoulder_pitch' in name:values=[(0,0),(.35,-.65),(.65,-.9),(1,-.15)]
  elif 'elbow' in name:values=[(0,.15),(.35,.9),(.65,1.2),(1,.2)]
  elif 'shoulder_roll' in name:values=[(0,.12 if 'left' in name else -.12),(1,.12 if 'left' in name else -.12)]
  else:continue
  for t,angle in values:key(rotor,'rotation_quaternion',Quaternion(axes[name],angle),t)
 box('Studio floor',(0,0,-.045),(200,200,.08),material('Warm studio gray',(.13,.14,.15),0,.6),.005)
 light('Soft daylight',(-5,-4,9),1700,8);light('Rim strip',(4,5,7),1300,6,shape='RECTANGLE')
 for i in range(last):
  t=i/(last-1);angle=math.radians(-105+30*t)
  camera(t,(13*math.cos(angle),13*math.sin(angle),3.8),(0,0,2.05),8)

elif a.preset=='orbital-earth':
 earth=material('Earth daylight',(.4,.5,.6),0,.65)
 shader=next(n for n in earth.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 tex=earth.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(config['texture_path'])
 earth.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
 globe=sphere('Earth',(0,0,0),(3.0,)*3,earth)
 # The stock UV sphere is low resolution; add subdivisions for a clean limb.
 sub=globe.modifiers.new('Smooth globe silhouette','SUBSURF');sub.levels=2
 key(globe,'rotation_euler',(0,0,math.radians(-95)),0);key(globe,'rotation_euler',(0,0,math.radians(-65)),1)
 if config.get('clouds_path'):
  # Photographic cloud coverage blended in the surface shader: the same imagery
  # without tracing multiple semitransparent shells through every ocean pixel.
  clouds=earth.node_tree.nodes.new('ShaderNodeTexImage');clouds.image=bpy.data.images.load(config['clouds_path'])
  composite=earth.node_tree.nodes.new('ShaderNodeMixRGB');composite.inputs[2].default_value=(.83,.87,.92,1)
  earth.node_tree.links.new(clouds.outputs['Color'],composite.inputs[0])
  earth.node_tree.links.new(tex.outputs['Color'],composite.inputs[1])
  earth.node_tree.links.new(composite.outputs[0],shader.inputs['Base Color'])
 # A thin geometric limb avoids stochastic transparency noise in EEVEE.
 # This is a visual Earth study rather than atmospheric radiative transfer.
 bpy.ops.curve.primitive_bezier_circle_add(radius=3.014,location=(0,0,0))
 limb=bpy.context.object;limb.name='Thin atmospheric limb';limb.data.bevel_depth=.007;limb.data.bevel_resolution=3
 limb.data.materials.append(material('Atmospheric blue',(.06,.22,.48),0,.5,1.2))
 facing=limb.constraints.new('TRACK_TO');facing.target=cam;facing.track_axis='TRACK_Z';facing.up_axis='UP_Y'
 light('Sun',(-8,-9,9),1800,2)
 for i in range(last):
  t=i/(last-1);camera(t,(.7,-17+1.6*t,4.2-.9*t),(0,0,0),16)

elif a.preset=='terrain-flyover':
 image=bpy.data.images.load(config['terrain_path']);image.colorspace_settings.name='Non-Color';width,height=image.size;pixels=list(image.pixels)
 resolution=128;vertices=[];faces=[];heights=[]
 for y in range(resolution):
  for x in range(resolution):
   px=min(width-1,round(x/(resolution-1)*(width-1)));py=min(height-1,round(y/(resolution-1)*(height-1)))
   i=(py*width+px)*4;r,g,b=[round(v*255) for v in pixels[i:i+3]]
   elevation=r*256+g+b/256-32768;heights.append(elevation)
   vertices.append(((x/(resolution-1)-.5)*12,(y/(resolution-1)-.5)*12,elevation/2300))
 for y in range(resolution-1):
  for x in range(resolution-1):
   i=y*resolution+x;faces.append((i,i+1,i+1+resolution,i+resolution))
 mesh=bpy.data.meshes.new('Terrarium elevation mesh');mesh.from_pydata(vertices,[],faces);mesh.update()
 ob=bpy.data.objects.new('Mount Fuji DEM',mesh);s.collection.objects.link(ob)
 mat=material('Topographic paper',(.32,.39,.31),0,.88);ob.data.materials.append(mat)
 nodes=mat.node_tree.nodes;links=mat.node_tree.links;shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 geometry=nodes.new('ShaderNodeNewGeometry');separate=nodes.new('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Position'],separate.inputs[0])
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.02;ramp.color_ramp.elements[0].color=(.09,.17,.12,1);ramp.color_ramp.elements[1].position=1;ramp.color_ramp.elements[1].color=(.85,.81,.66,1)
 links.new(separate.outputs['Z'],ramp.inputs[0]);links.new(ramp.outputs[0],shader.inputs['Base Color'])
 # Thin elevation contours make the real relief legible without labels.
 frequency=nodes.new('ShaderNodeMath');frequency.operation='MULTIPLY';frequency.inputs[1].default_value=12
 fraction=nodes.new('ShaderNodeMath');fraction.operation='PINGPONG';fraction.inputs[1].default_value=1
 threshold=nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.94
 ink=nodes.new('ShaderNodeMixRGB');ink.inputs[2].default_value=(.025,.05,.038,1)
 links.new(separate.outputs['Z'],frequency.inputs[0]);links.new(frequency.outputs[0],fraction.inputs[0]);links.new(fraction.outputs[0],threshold.inputs[0]);links.new(threshold.outputs[0],ink.inputs[0]);links.new(ramp.outputs[0],ink.inputs[1]);links.new(ink.outputs[0],shader.inputs['Base Color'])
 box('Terrain plinth',(0,0,-.18),(12,12,.35),material('Cut terrain edge',(.055,.08,.065),0,.85),.05)
 box('Studio ground',(0,0,-.39),(200,200,.08),material('Map studio',(.16,.18,.16),0,.9),.01)
 for face in mesh.polygons:face.use_smooth=True
 light('Low afternoon sun',(-8,-10,10),2600,4)
 for i in range(last):
  t=i/(last-1);camera(t,(-18+4*t,-22+4*t,21-2*t),(0,0,.55),11)

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
