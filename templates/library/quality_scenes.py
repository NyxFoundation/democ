"""Source geometry and photographed data for the six quality-review studies."""
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion


def shader(material):
    return next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def sun(r, direction, energy=3, angle=.1):
    bpy.ops.object.light_add(type='SUN', location=direction)
    ob = bpy.context.object
    ob.name = 'Directional sunlight'
    ob.data.energy = energy
    ob.data.angle = angle
    ob.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
    return ob


def world(r, strength=.3, visible=False):
    tree = r.scene.world.node_tree
    bg = next(n for n in tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Strength'].default_value = strength
    coords = next((n for n in tree.nodes if n.type == 'TEX_COORD'), None)
    mapping = next((n for n in tree.nodes if n.type == 'MAPPING'), None)
    if coords and mapping:
        tree.links.new(coords.outputs['Normal'], mapping.inputs['Vector'])
    if visible:
        output = next(n for n in tree.nodes if n.type == 'OUTPUT_WORLD')
        tree.links.new(bg.outputs[0], output.inputs['Surface'])
        r.scene.render.film_transparent = False
    return bg


def bounds(objects):
    points = [ob.matrix_world @ Vector(p) for ob in objects if ob.type == 'MESH' for p in ob.bound_box]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    return low, high


def rim_reveal(r):
    r.import_product(r.config['model_path'], 5.6)
    # These are the two complete earbud roots from Apple's source USDZ.
    # The charging case is excluded before normalization, never approximated.
    for index, name in enumerate(r.config['model_roots']):
        group = r.scene.objects[name]
        low, high = bounds(group.children_recursive)
        center = (low + high) / 2
        matrix = group.matrix_world.copy()
        bpy.ops.object.empty_add(location=center)
        pivot = bpy.context.object
        pivot.name = ['Left earbud staging', 'Right earbud staging'][index]
        group.parent = pivot
        group.matrix_world = matrix
        pivot.location = (-1.45, 0, 1.05) if index == 0 else (1.35, .3, -.85)
        for t, tilt in [(0, -22), (.55, -27), (1, -31)]:
            r.key(pivot, 'rotation_euler', (0, math.radians(tilt), math.radians(-8 if index == 0 else 8)), t)
    bg = world(r, 0)
    for t, power in [(0, 0), (.18, 0), (.64, .12), (1, .2)]:
        bg.inputs['Strength'].default_value = power
        bg.inputs['Strength'].keyframe_insert('default_value', frame=1+round(t*(r.frames-1)))
    r.light('Narrow left contour', (-5, 4, 5), 650, 5, target=(0, 0, 0), shape='RECTANGLE')
    r.light('Narrow right contour', (5, 4, 2), 580, 4, target=(0, 0, 0), shape='RECTANGLE')
    fill = r.light('Front porcelain reveal', (-2, -6, 5), 0, 7, target=(0, 0, .1), shape='RECTANGLE')
    for t, power in [(0, 0), (.15, 0), (.6, 850), (.9, 1350), (1, 1350)]:
        r.key(fill.data, 'energy', power, t)
    r.cam.data.lens = 72
    r.shot(0, (0, -19.8, 2.0), (0, 0, .15), 11)
    r.shot(1, (.45, -19.2, 2.1), (0, 0, .15), 11)


def drone_orbit(r):
    height = r.import_product(r.config['model_path'], 5.8)
    # Textures, separate lenses, screws, propellers and motor housings belong
    # to the acquired Mavic 3 Cine model and retain their original assignments.
    world(r, .42)
    floor = r.material('Dark studio sweep', (.025, .029, .034), .05, .54)
    r.box('Studio sweep', (0, 0, -.065), (200, 200, .1), floor, .005)
    r.light('Overhead silk', (-3, -4, 8), 950, 7, target=(0, 0, height/2), shape='RECTANGLE')
    r.light('Side reflection', (5, 3, 5), 750, 5, target=(0, 0, height/2), shape='RECTANGLE')
    r.light('Lens catchlight', (-1, -7, 2), 130, 4, target=(0, 0, height/2))
    r.cam.data.lens = 65
    for frame in range(r.frames):
        t = frame/(r.frames-1)
        q = t*t*(3-2*t)
        angle = math.radians(-34-44*q)
        distance = 11.5+2.2*q
        r.shot(t, (distance*math.cos(angle), distance*math.sin(angle), 3.0+1.4*q),
               (.2, 0, height*.48), 10)


def humanoid_articulation(r):
    source = Path(r.config['model_path'])
    tree = ET.parse(source).getroot()
    shell = r.material('G1 off-white polymer', (.66, .68, .70), .08, .26)
    dark = r.material('G1 dark housings', (.018, .021, .024), .12, .35)
    visor = r.material('G1 optical visor', (.006, .009, .012), .12, .13)
    shader(visor).inputs['Coat Weight'].default_value = .35
    rubber = r.material('G1 elastomer', (.012, .013, .015), 0, .57)
    nodes, rotors, axes = {}, {}, {}
    for link in tree.findall('link'):
        bpy.ops.object.empty_add()
        node = bpy.context.object
        node.name = link.get('name')
        nodes[node.name] = node
        for visual in link.findall('visual'):
            mesh = visual.find('geometry/mesh')
            if mesh is None:
                continue
            before = set(r.scene.objects)
            bpy.ops.wm.stl_import(filepath=str(source.parent/'meshes'/Path(mesh.get('filename')).name))
            origin = visual.find('origin')
            xyz = list(map(float, origin.get('xyz', '0 0 0').split())) if origin is not None else [0]*3
            angles = list(map(float, origin.get('rpy', '0 0 0').split())) if origin is not None else [0]*3
            material = visual.find('material')
            material_name = material.get('name') if material is not None else 'white'
            # Read URDF material names. Joint-name heuristics colored the old
            # face white and the complete thighs black, unlike the real G1.
            mat = shell if material_name == 'white' else dark
            if node.name == 'head_link': mat = visor
            if 'hand' in node.name or 'ankle_roll' in node.name: mat = rubber
            for ob in set(r.scene.objects)-before:
                ob.parent = node
                ob.location, ob.rotation_euler = xyz, angles
                ob.data.materials.append(mat)
                for face in ob.data.polygons: face.use_smooth = True
                if hasattr(ob.data, 'set_sharp_from_angle'): ob.data.set_sharp_from_angle(angle=.58)
    for joint in tree.findall('joint'):
        parent = nodes[joint.find('parent').get('link')]
        child = nodes[joint.find('child').get('link')]
        bpy.ops.object.empty_add()
        origin = bpy.context.object
        origin.name = joint.get('name')
        origin.parent = parent
        transform = joint.find('origin')
        if transform is not None:
            origin.location = list(map(float, transform.get('xyz', '0 0 0').split()))
            origin.rotation_euler = list(map(float, transform.get('rpy', '0 0 0').split()))
        bpy.ops.object.empty_add()
        rotor = bpy.context.object
        rotor.name = joint.get('name')+' motion'
        rotor.parent = origin
        rotor.rotation_mode = 'QUATERNION'
        child.parent = rotor
        rotors[joint.get('name')] = rotor
        axis = joint.find('axis')
        axes[joint.get('name')] = Vector(list(map(float, axis.get('xyz', '0 0 1').split()))) if axis is not None else Vector((0, 0, 1))
    roots = [ob for ob in nodes.values() if ob.parent is None]
    bpy.ops.object.empty_add()
    root = bpy.context.object
    root.name = 'G1 walking assembly'
    for ob in roots: ob.parent = root
    bpy.context.view_layer.update()
    # Solve the sagittal two-link chain from the actual imported joint centers.
    legs = {}
    for side in ['left', 'right']:
        hip = rotors[side+'_hip_pitch_joint'].parent.matrix_world.translation.copy()
        knee = rotors[side+'_knee_joint'].parent.matrix_world.translation.copy()
        ankle = rotors[side+'_ankle_pitch_joint'].parent.matrix_world.translation.copy()
        v1, v2 = knee-hip, ankle-knee
        legs[side] = (hip, ankle, math.hypot(v1.x, v1.z), math.hypot(v2.x, v2.z),
                      math.atan2(v1.x, -v1.z), math.atan2(v2.x, -v2.z))
    scale = 3.1
    low, high = bounds([o for o in r.scene.objects if o.type == 'MESH'])
    base = -low.z*scale
    root.scale = (scale,)*3
    root.rotation_euler.z = -math.pi/2
    stride, period, stance = .22, 1.25, .65
    speed = stride/(period*stance)
    for frame in range(r.frames):
        t = frame/(r.frames-1)
        seconds = t*r.duration
        bob = .006*math.cos(seconds/period*4*math.pi)
        r.key(root, 'location', (0, -speed*seconds*scale, base-.027*scale+bob*scale), t)
        for side, offset in [('left', 0), ('right', .5)]:
            phase = (seconds/period+offset) % 1
            if phase < stance:
                forward = stride*(.5-phase/stance)
                lift = 0
            else:
                u = (phase-stance)/(1-stance)
                forward = stride*(-.5+u*u*(3-2*u))
                lift = .055*math.sin(math.pi*u)
            hip, ankle, l1, l2, rest1, rest2 = legs[side]
            dx = ankle.x+forward-hip.x
            dz = ankle.z+.027-bob+lift-hip.z
            distance = min(l1+l2-.0001, math.hypot(dx, dz))
            beta = math.acos(max(-1, min(1, (l1*l1+distance*distance-l2*l2)/(2*l1*distance))))
            bend = math.acos(max(-1, min(1, (distance*distance-l1*l1-l2*l2)/(2*l1*l2))))
            thigh = math.atan2(dx, -dz)+beta
            hip_angle = rest1-thigh
            knee_angle = rest2-hip_angle-(thigh-bend)
            ankle_angle = -hip_angle-knee_angle-.1749
            for joint, angle in [('hip_pitch', hip_angle), ('knee', knee_angle), ('ankle_pitch', ankle_angle),
                                 ('shoulder_pitch', .30*math.sin(2*math.pi*phase)), ('elbow', .33+.08*math.sin(2*math.pi*phase))]:
                name = side+'_'+joint+'_joint'
                if name in rotors: r.key(rotors[name], 'rotation_quaternion', Quaternion(axes[name], angle), t)
        r.shot(t, (7.6, -13.8-speed*seconds*scale, 4.0), (0, -speed*seconds*scale, 2.05), 11)
    pavement = r.material('Courtyard concrete paving', (.25, .26, .27), 0, .85)
    nt = pavement.node_tree
    pos = nt.nodes.new('ShaderNodeNewGeometry')
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.inputs['Color1'].default_value = (.27, .28, .29, 1)
    brick.inputs['Color2'].default_value = (.22, .235, .25, 1)
    brick.inputs['Mortar'].default_value = (.11, .12, .13, 1)
    brick.inputs['Scale'].default_value = .5
    brick.inputs['Mortar Size'].default_value = .006
    brick.inputs['Brick Width'].default_value = .8
    brick.inputs['Row Height'].default_value = .8
    nt.links.new(pos.outputs['Position'], brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'], shader(pavement).inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.008
    nt.links.new(brick.outputs['Fac'], bump.inputs['Height']);nt.links.new(bump.outputs[0], shader(pavement).inputs['Normal'])
    r.box('Outdoor paving', (0, 0, -.06), (200, 200, .1), pavement, .005)
    world(r, .65, True)
    sun(r, (-6, -4, 10), 2.5, .07)
    r.cam.data.lens = 60
    r.cam.data.dof.use_dof = False


def orbital_earth(r):
    r.scene.view_settings.view_transform = 'Standard'
    r.scene.render.film_transparent = False
    world(r, .012)
    surface = r.material('NASA Blue Marble reflectance', (.3, .4, .5), 0, 1)
    shader(surface).inputs['Specular IOR Level'].default_value = .05
    image = surface.node_tree.nodes.new('ShaderNodeTexImage')
    image.image = bpy.data.images.load(r.config['texture_path'])
    # A near-full-phase disk needs broad, smooth limb shading. Computing the
    # illumination in the surface shader avoids EEVEE shadow-map acne between
    # concentric planet/cloud shells (a dark meridian in the earlier render).
    nt = surface.node_tree
    geometry = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    dot.inputs[1].default_value=Vector((-.16,-.98,.1)).normalized()
    nt.links.new(geometry.outputs['Normal'],dot.inputs[0])
    ramp=nt.nodes.new('ShaderNodeMapRange');ramp.clamp=True
    ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
    ramp.inputs['To Min'].default_value=.12;ramp.inputs['To Max'].default_value=.86
    nt.links.new(dot.outputs['Value'],ramp.inputs['Value'])
    multiply=nt.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    nt.links.new(image.outputs['Color'],multiply.inputs[1]);nt.links.new(ramp.outputs[0],multiply.inputs[2])
    emission=nt.nodes.new('ShaderNodeEmission');nt.links.new(multiply.outputs[0],emission.inputs[0])
    nt.links.new(emission.outputs[0],next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=192, ring_count=96, radius=3)
    earth = bpy.context.object;earth.name='NASA Earth surface';earth.data.materials.append(surface)
    for p in earth.data.polygons:p.use_smooth=True
    clouds = r.material('NASA observed clouds', (.94, .96, 1), 0, 1)
    nt = clouds.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(r.config['clouds_path'])
    transparent=nt.nodes.new('ShaderNodeBsdfTransparent');emission=nt.nodes.new('ShaderNodeEmission')
    emission.inputs[0].default_value=(.87,.91,.96,1);emission.inputs[1].default_value=.82
    mix=nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tex.outputs['Color'],mix.inputs[0]);nt.links.new(transparent.outputs[0],mix.inputs[1]);nt.links.new(emission.outputs[0],mix.inputs[2])
    nt.links.new(mix.outputs[0],next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
    if hasattr(clouds, 'surface_render_method'):clouds.surface_render_method='BLENDED'
    clouds.use_backface_culling = True
    bpy.ops.mesh.primitive_uv_sphere_add(segments=192,ring_count=96,radius=3.009)
    shell=bpy.context.object;shell.name='Separate observed cloud layer';shell.data.materials.append(clouds)
    for p in shell.data.polygons:p.use_smooth=True
    atmo=bpy.data.materials.new('Soft Rayleigh limb');atmo.use_nodes=True
    nodes=atmo.node_tree.nodes;nodes.clear();links=atmo.node_tree.links
    output=nodes.new('ShaderNodeOutputMaterial');transparent=nodes.new('ShaderNodeBsdfTransparent')
    emission=nodes.new('ShaderNodeEmission');emission.inputs[0].default_value=(.06,.27,.65,1);emission.inputs[1].default_value=.3
    facing=nodes.new('ShaderNodeLayerWeight');power=nodes.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=5
    mix=nodes.new('ShaderNodeMixShader');links.new(facing.outputs['Facing'],power.inputs[0]);links.new(power.outputs[0],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs[0])
    if hasattr(atmo,'surface_render_method'):atmo.surface_render_method='BLENDED'
    atmo.use_backface_culling=True
    bpy.ops.mesh.primitive_uv_sphere_add(segments=192,ring_count=96,radius=3.035)
    atmosphere=bpy.context.object;atmosphere.name='Atmosphere volume silhouette';atmosphere.data.materials.append(atmo)
    for p in atmosphere.data.polygons:p.use_smooth=True
    for ob in [earth,shell]:
        r.key(ob,'rotation_euler',(0,0,math.radians(-3)),0)
        r.key(ob,'rotation_euler',(0,0,math.radians(18 if ob==earth else 19)),1)
    sun(r, (-2, -12, 2), 3.4, .0093)
    r.cam.data.type='ORTHO';r.cam.data.ortho_scale=11.3;r.cam.data.dof.use_dof=False
    r.shot(0,(0,-20,1.4),(0,0,0),16);r.shot(1,(0,-20,1.4),(0,0,0),16)


def terrain_flyover(r):
    heightmap=bpy.data.images.load(r.config['terrain_path']);heightmap.colorspace_settings.name='Non-Color'
    width,height=heightmap.size;pixels=list(heightmap.pixels)
    resolution=512;vertices=[];faces=[];uvs=[];span=18
    meters_per_unit=float(r.config['terrain_meters_per_unit'])
    for y in range(resolution):
        for x in range(resolution):
            px=round(x/(resolution-1)*(width-1));py=round(y/(resolution-1)*(height-1));i=(py*width+px)*4
            red,green,blue=[round(v*255) for v in pixels[i:i+3]]
            elevation=max(0,red*256+green+blue/256-32768)
            vertices.append(((x/(resolution-1)-.5)*span,(y/(resolution-1)-.5)*span,elevation/meters_per_unit*1.65))
            uvs.append((x/(resolution-1),y/(resolution-1)))
    for y in range(resolution-1):
        for x in range(resolution-1):
            i=y*resolution+x;faces.append((i,i+1,i+1+resolution,i+resolution))
    mesh=bpy.data.meshes.new('Sete Cidades measured elevation');mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new('São Miguel satellite terrain',mesh);r.scene.collection.objects.link(ob)
    layer=mesh.uv_layers.new(name='Mercator satellite registration')
    for polygon in mesh.polygons:
        polygon.use_smooth=True
        for loop in polygon.loop_indices:layer.data[loop].uv=uvs[mesh.loops[loop].vertex_index]
    mat=r.material('Copernicus Sentinel 2016 imagery',(.3,.4,.3),0,1);ob.data.materials.append(mat)
    shader(mat).inputs['Specular IOR Level'].default_value=0
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(r.config['texture_path'])
    mat.node_tree.links.new(tex.outputs['Color'],shader(mat).inputs['Base Color'])
    # The satellite mosaic already contains illumination. Retain its colour
    # with fill emission rather than shading the photographed slopes twice.
    mat.node_tree.links.new(tex.outputs['Color'],shader(mat).inputs['Emission Color']);shader(mat).inputs['Emission Strength'].default_value=.55
    r.scene.view_settings.exposure=.35
    bg=world(r,.45);bg.inputs['Color'].default_value=(.4,.5,.65,1)
    r.scene.render.film_transparent=False
    sun(r,(-8,-6,12),2.4,.09)
    r.cam.data.lens=43;r.cam.data.dof.use_dof=False
    # Keep the mosaic's outer edge beyond the view, including the wide end.
    r.shot(0,(6,-9,8.8),(3,-1.1,.3),16)
    r.shot(1,(5,-6,6.5),(3,.2,.3),16)
