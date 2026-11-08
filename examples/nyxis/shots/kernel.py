"""Cinematic proof dependency tree: grow, orbit, inspect, converge, certify.
Blender 5.0+, 18 s / 450 frames / 25 fps. A spherical dependency volume with transient node inspections.
The topology and moving checks illustrate dependencies; they are not a kernel trace.
References and creative decisions are documented in ../notes.md.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

parser = argparse.ArgumentParser()
parser.add_argument("--layers", required=True)
parser.add_argument("--out", default="out/nyxis/build/3d/kernel")
parser.add_argument("--blend")
parser.add_argument("--no-render", action="store_true")
parser.add_argument("--frames", help="Comma separated review frames")
parser.add_argument("--samples", type=int, default=12)
parser.add_argument("--resolution", type=int, default=100)
parser.add_argument("--start-frame", type=int, default=1)
parser.add_argument("--end-frame", type=int, default=450)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
parts = Path(args.layers).resolve()
output = Path(args.out).resolve()
output.mkdir(parents=True, exist_ok=True)

# Work at a physical scale where focus pulls produce useful depth of field.
S = 0.15
FPS = 25
LAST = 450


def F(frame):
    """Design timing uses 600 ticks; render directly at 25 fps for 18 seconds."""
    return max(1, round(frame * LAST / 600))
rng = random.Random(37)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = args.samples
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.resolution_percentage = args.resolution
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = LAST
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.film_transparent = False
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.18
scene.eevee.motion_blur_steps = 2
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("Deep navy void")
world.use_nodes = True
world.node_tree.nodes.clear()
background = world.node_tree.nodes.new("ShaderNodeBackground")
background.inputs["Color"].default_value = (0.001, 0.0025, 0.006, 1)
background.inputs["Strength"].default_value = 0.18
world_out = world.node_tree.nodes.new("ShaderNodeOutputWorld")
world.node_tree.links.new(background.outputs[0], world_out.inputs[0])
scene.world = world


def scaled(p):
    return Vector(p) * S


def key(obj, prop, value, frame):
    setattr(obj, prop, value)
    obj.keyframe_insert(prop, frame=F(frame))


def socket_key(socket, value, frame):
    socket.default_value = value
    socket.keyframe_insert("default_value", frame=F(frame))


def reveal(obj, frame):
    key(obj, "hide_render", True, 1)
    key(obj, "hide_render", True, max(1, frame - 1))
    key(obj, "hide_render", False, frame)


def emission(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1)
    emit.inputs["Strength"].default_value = strength
    mat.node_tree.links.new(emit.outputs[0], out.inputs[0])
    return mat, emit


def physical(name, color, metallic=0.7, roughness=0.24):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    p = mat.node_tree.nodes.get("Principled BSDF")
    if p is None:
        mat.node_tree.nodes.clear()
        p = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(p.outputs[0], out.inputs[0])
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    return mat


def alpha_gate(mat, shader_output):
    nodes = mat.node_tree.nodes
    out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mat.node_tree.links.new(transparent.outputs[0], mix.inputs[1])
    mat.node_tree.links.new(shader_output, mix.inputs[2])
    mat.node_tree.links.new(mix.outputs[0], out.inputs[0])
    return mix.inputs[0]


# One material, independently animated object colors: no hundreds of shader variants.
node_material = physical("Constellation points", (0.025, 0.08, 0.16), 0.08, 0.42)
principled = next(n for n in node_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
object_info = node_material.node_tree.nodes.new("ShaderNodeObjectInfo")
node_material.node_tree.links.new(object_info.outputs["Color"], principled.inputs["Base Color"])
node_material.node_tree.links.new(object_info.outputs["Color"], principled.inputs["Emission Color"])
principled.inputs["Emission Strength"].default_value = 1.8
wire, _ = emission("Unverified cool blue filaments", (0.016, 0.082, 0.18), 1.15)
verified, _ = emission("Verified warm gold filaments", (0.85, 0.36, 0.065), 1.65)
pulse, _ = emission("Moving ivory kernel checks", (1.0, 0.83, 0.50), 7)
rim, _ = emission("Transient inspection halos", (1.0, 0.53, 0.14), 2.2)
dim_star, _ = emission("Distant dust", (0.08, 0.19, 0.29), 0.6)
white, _ = emission("Verified judgment", (1.0, 0.71, 0.30), 1.5)


def depth_falloff(material, strength, base):
    """Near-side filaments shine; the far hemisphere remains a softer layer."""
    nodes=material.node_tree.nodes;links=material.node_tree.links
    camera_depth=nodes.new("ShaderNodeCameraData")
    remap=nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value=8.8
    remap.inputs["From Max"].default_value=14.6
    remap.inputs["To Min"].default_value=base*1.45
    remap.inputs["To Max"].default_value=base*.18
    links.new(camera_depth.outputs["View Z Depth"],remap.inputs["Value"])
    links.new(remap.outputs["Result"],strength)


depth_falloff(node_material,principled.inputs["Emission Strength"],1.8)
for material,base in [(wire,1.15),(verified,1.65)]:
    shader=next(n for n in material.node_tree.nodes if n.type=="EMISSION")
    depth_falloff(material,shader.inputs["Strength"],base)

bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1)
node_mesh = bpy.context.object.data
node_mesh.name = "Perfectly smooth proof sphere"
for polygon in node_mesh.polygons:
    polygon.use_smooth = True
bpy.data.objects.remove(bpy.context.object, do_unlink=True)
node_mesh.materials.append(node_material)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1)
pulse_mesh = bpy.context.object.data
pulse_mesh.name = "Smooth photon"
for polygon in pulse_mesh.polygons:
    polygon.use_smooth = True
bpy.data.objects.remove(bpy.context.object, do_unlink=True)
pulse_mesh.materials.append(pulse)


def sphere(name, point, radius, mesh=node_mesh):
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.location = scaled(point)
    obj.scale = (radius * S,) * 3
    return obj


def path(name, points, material, width):
    """One exact cubic, with matching tangents at each fork; never a polyline."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 48
    curve.bevel_depth = width * S
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(1)
    a, c1, c2, b = [scaled(p) for p in points]
    left, right = spline.bezier_points
    for p in (left, right):
        p.handle_left_type = "FREE"
        p.handle_right_type = "FREE"
    left.co = a; left.handle_right = c1; left.handle_left = 2*a-c1
    right.co = b; right.handle_left = c2; right.handle_right = 2*b-c2
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    curve.materials.append(material)
    return obj


def tangent(point, fallback):
    radial=point-root_point
    return radial.normalized() if radial.length>1e-6 else fallback.normalized()


def bezier_points(a, b):
    a,b=Vector(a),Vector(b)
    reach=(b-a).length*.32
    return [a,a+tangent(a,b-a)*reach,b-tangent(b,b-a)*reach,b]


def ring_curve(name, material):
    """A circular halo facing the camera, only visible during an inspection."""
    bpy.ops.curve.primitive_bezier_circle_add(radius=S)
    obj = bpy.context.object; obj.name = name
    obj.data.resolution_u = 48
    obj.data.bevel_depth = 0.014 * S
    obj.data.bevel_resolution = 3
    obj.data.materials.append(material)
    return obj


# Uniform directions on the outer sphere; recursively balanced geodesic
# clusters keep every parent's dependencies together in the same solid angle.
root_point=Vector((0,0,0))
outer=[]
golden=math.pi*(3-math.sqrt(5))
for i in range(216):
    z=1-2*(i+.5)/216
    r=math.sqrt(1-z*z);theta=i*golden
    outer.append(Vector((r*math.cos(theta),r*math.sin(theta),z)))


def balanced_groups(points,count,seeds=None):
    center=sum(points,Vector()).normalized()
    if seeds is None:
        seeds=[min(points,key=lambda p:p.dot(center))]
        while len(seeds)<count:
            seeds.append(min(points,key=lambda p:max(p.dot(s) for s in seeds)))
    capacity=len(points)//count
    groups=[[] for _ in range(count)]
    def confidence(p):
        scores=sorted((p.dot(seed) for seed in seeds),reverse=True)
        return scores[0]-scores[1]
    for point in sorted(points,key=confidence,reverse=True):
        slot=max((j for j in range(count) if len(groups[j])<capacity),
                 key=lambda j:point.dot(seeds[j]))
        groups[slot].append(point)
    return groups


seeds=[Vector(p).normalized() for p in [(1,-1,1),(-1,-1,-1),(1,1,-1),(-1,1,1)]]
group_levels=[balanced_groups(outer,4,seeds)]
for splits in [3,3,3,2]:
    group_levels.append([child for group in group_levels[-1]
                         for child in balanced_groups(group,splits)])
levels=[[root_point]]
radii=[3.4,6.1,9.1,11.7,14.2]
for groups,radius in zip(group_levels,radii):
    levels.append([(sum(group,Vector())/len(group)).normalized()*radius for group in groups])

# Verify leaves first, then allow a parent check only after every child arrives.
check_times = {}
for depth in range(5, 0, -1):
    for i in range(len(levels[depth])):
        if depth == 5:
            check_times[depth, i] = 278 + (i * 7 % 25)
        else:
            child_count = len(levels[depth + 1])
            children = [j for j in range(child_count)
                        if j * len(levels[depth]) // child_count == i]
            check_times[depth, i] = max(check_times[depth + 1, j] + 24 for j in children) + 8

node_objects = {}
for depth in range(1, 6):
    row, previous = levels[depth], levels[depth - 1]
    for i, point in enumerate(row):
        parent = previous[i * len(previous) // len(row)]
        grow_start = 12 + depth * 12 + (i * 3 % 7)
        grow_end = grow_start + 18
        check = check_times[depth, i]
        radius = 0.105 if depth == 1 else 0.078 if depth < 4 else 0.058
        node = sphere("Term %d.%03d" % (depth, i), point, radius)
        node_objects[depth,i] = node
        reveal(node, grow_end - 3)
        for f, size in [(grow_end-3, 0.04), (grow_end+7, 1.08), (grow_end+15, 1),
                        (check-1, 1), (check+5, 1.16), (check+15, 1)]:
            key(node, "scale", (radius*S*size,)*3, f)
        for f, color in [(1, (0.025,0.10,0.25,1)), (check-1,(0.025,0.10,0.25,1)),
                         (check+2,(1.0,0.90,0.68,1)), (check+14,(1.0,0.43,0.075,1))]:
            key(node, "color", color, f)

        points = bezier_points(parent, point)
        width = 0.015 if depth == 1 else 0.012 if depth < 4 else 0.008
        edge = path("Dependency %d.%03d" % (depth,i), points, wire, width)
        edge.data.bevel_factor_end = 0
        edge.data.keyframe_insert("bevel_factor_end", frame=F(grow_start))
        edge.data.bevel_factor_end = 1
        edge.data.keyframe_insert("bevel_factor_end", frame=F(grow_end))

        done = path("Checked %d.%03d" % (depth,i), points, verified, width*0.87)
        reveal(done, check+24)
        key(edge,"hide_render",False,1)
        key(edge,"hide_render",False,check+23)
        key(edge,"hide_render",True,check+24)

        # A luminous segment and a bright head travel through the curved dependency.
        trail = path("Check trail %d.%03d" % (depth,i), points, pulse, width*1.55)
        reveal(trail, check+1)
        key(trail, "hide_render", False, check+23)
        key(trail, "hide_render", True, check+25)
        for f, a, b in [(check+1,0.90,1), (check+6,0.62,0.88),
                         (check+16,0.18,0.44), (check+24,0,0.03)]:
            trail.data.bevel_factor_start=a;trail.data.keyframe_insert("bevel_factor_start", frame=F(f))
            trail.data.bevel_factor_end=b;trail.data.keyframe_insert("bevel_factor_end", frame=F(f))
        photon = sphere("Check photon %d.%03d"%(depth,i), point, radius*0.46, pulse_mesh)
        reveal(photon, check+1)
        key(photon,"hide_render",False,check+23)
        key(photon,"hide_render",True,check+25)
        photon.location = (0, 0, 0)
        travel = photon.constraints.new("FOLLOW_PATH")
        travel.target = edge
        travel.use_fixed_location = True
        travel.offset_factor = 1
        travel.keyframe_insert("offset_factor", frame=F(check+1))
        travel.offset_factor = 0
        travel.keyframe_insert("offset_factor", frame=F(check+24))

# Sparse floating dust gives the camera move parallax without a floor grid.
for i in range(125):
    point=(rng.uniform(-25,25),rng.uniform(-30,30),rng.uniform(-22,22))
    star=sphere("Atmosphere %03d"%i,point,rng.uniform(0.015,0.035))
    star.data = node_mesh.copy()
    star.data.materials.clear()
    star.data.materials.append(dim_star)

# The main theorem is exactly the same kind of sphere as its dependencies.
# Labels are momentary annotations, never physical cards or panels.
meta = json.loads((parts/"layers.json").read_text())
layers = {item["name"]:item for item in meta["layers"]}
root_radius=0.16
root = sphere("authorization_safety", root_point, root_radius)
node_objects[0,0] = root
for frame, color in [(1,(0.025,0.10,0.25,1)), (453,(0.025,0.10,0.25,1)),
                     (461,(1.0,0.92,0.74,1)), (479,(1.0,0.43,0.075,1)),
                     (600,(1.0,0.43,0.075,1))]:
    key(root,"color",color,frame)
for frame, size in [(1,0.90),(40,1),(450,1),(465,1.12),(490,1),(600,1)]:
    key(root,"scale",(root_radius*S*size,)*3,frame)

# Broad reflections make the smooth spheres read as round volumes.
for name,position,energy,size,color in [
    ("Soft cyan key",(-10,-10,13),110,5,(.35,.75,1)),
    ("White edge light",(12,7,12),170,4,(.75,.88,1)),
    ("Warm rim",(-9,19,4),70,3,(1,.6,.25)),
]:
    bpy.ops.object.light_add(type="AREA",location=scaled(position))
    light=bpy.context.object;light.name=name
    light.data.energy=energy;light.data.shape="DISK";light.data.size=size*S
    light.data.color=color
    light.rotation_euler=(scaled(root_point)-light.location).to_track_quat("-Z","Y").to_euler()

bpy.ops.object.empty_add(location=scaled((0,8,3.4)))
look=bpy.context.object;look.name="Camera look target"
bpy.ops.object.empty_add(location=scaled(root_point))
focus=bpy.context.object;focus.name="Rack focus"
bpy.ops.object.camera_add(location=scaled((1,-21,8.5)))
camera=bpy.context.object;camera.name="Cinematic proof camera"
camera.data.lens=40
camera.data.clip_start=.015;camera.data.clip_end=100
camera.data.dof.use_dof=True;camera.data.dof.focus_object=focus
camera.data.dof.aperture_blades=7
track=camera.constraints.new("TRACK_TO");track.target=look
track.track_axis="TRACK_NEGATIVE_Z";track.up_axis="UP_Y"
scene.camera=camera
lemma_point=levels[1][0]
struct_point=levels[2][1]
# Keep the complete sphere visible. A continuous orbit, rather than macro
# pushes into individual balls, reveals the volume of the dependencies.
camera_moves=[]
for f,azimuth,elevation,radius in [
    (1,-100,18,77),(80,-94,17,78),(145,-81,19,78),
    (195,-70,20,77),(265,-58,19,75),(310,-48,17,75),
    (365,-36,15,76),(440,-20,14,78),(510,-8,16,78),(600,6,18,79),
]:
    az=math.radians(azimuth);el=math.radians(elevation)
    position=Vector((radius*math.cos(el)*math.cos(az),
                     radius*math.cos(el)*math.sin(az),radius*math.sin(el)))
    right=Vector((-position.y,position.x,0)).normalized()
    camera_moves.append((f,position,right*9,root_point,12))
for f,position,target,focus_point,fstop in camera_moves:
    key(camera,"location",scaled(position),f)
    key(look,"location",scaled(target),f)
    key(focus,"location",scaled(focus_point),f)
    camera.data.dof.aperture_fstop=fstop
    camera.data.dof.keyframe_insert("aperture_fstop",frame=F(f))

# A single selected node gets a circular halo and a delicate tether to its
# temporary text. This is baked into the blend; no live handler is required.
inspections = [
    (0, (0,0), 12, 88, 0.55),
    (1, (1,0), 200, 276, 0.38),
    (2, (2,1), 310, 385, 0.35),
    (3, (0,0), 492, 578, 0.55),
]
for number, node_id, start, end, radius in inspections:
    selected = node_objects[node_id]
    material, shader = emission("Inspection %d gold" % number, (1,0.63,0.23), 1.8)
    gate = alpha_gate(material, shader.outputs[0])
    for f, value in [(1,0),(start,0),(start+6,1),(end-6,1),(end,0),(600,0)]:
        socket_key(gate,value,f)
    halo = ring_curve("Inspection %d focus halo" % number, material)
    halo.location = selected.location
    halo.scale = (radius,)*3
    reveal(halo,start)
    key(halo,"hide_render",False,end-1)
    key(halo,"hide_render",True,end)
    tether = path("Inspection %d tether" % number,
                  [(0,0,0)]*4,material,0.010)
    tether.parent = camera
    reveal(tether,start)
    key(tether,"hide_render",False,end-1)
    key(tether,"hide_render",True,end)
    for f in range(start, end+1, 2):
        scene.frame_set(F(f))
        deps = bpy.context.evaluated_depsgraph_get()
        cam = camera.evaluated_get(deps)
        halo.rotation_euler = cam.matrix_world.to_quaternion().to_euler()
        halo.keyframe_insert("rotation_euler",frame=F(f))
        projected = world_to_camera_view(scene,cam,selected.location)
        distance = (cam.matrix_world.translation-selected.location).length
        width = 2*distance*math.tan(camera.data.angle_x/2)
        height = width*1000/1600
        def image_point(x,y):
            return Vector(((x/1600-.5)*width,(.5-y/1000)*height,-distance))
        # Terminate before the left edge of the text, clear of its glyphs.
        ax=projected.x*1600+24
        ay=(1-projected.y)*1000
        a=image_point(ax,ay); b=image_point(975,330)
        c1=image_point(ax+(975-ax)*.45,ay)
        c2=image_point(975-(975-ax)*.30,330)
        left,right=tether.data.splines[0].bezier_points
        for p,co,lh,rh in [(left,a,2*a-c1,c1),(right,b,c2,2*b-c2)]:
            p.co=co;p.handle_left=lh;p.handle_right=rh
            for prop in ("co","handle_left","handle_right"):
                p.keyframe_insert(prop,frame=F(f))
    if node_id!=(0,0):
        for f,color in [(start-1,(0.025,0.10,0.25,1)),
                        (start+6,(1.0,0.76,0.32,1)),
                        (end-6,(1.0,0.76,0.32,1)),
                        (end+1,(0.025,0.10,0.25,1))]:
            key(selected,"color",color,f)

# Composite typography AFTER lens effects and glow so it stays perfectly sharp.
compositor=bpy.data.node_groups.new("Proof cinema composite","CompositorNodeTree")
scene.compositing_node_group=compositor
compositor.interface.new_socket(name="Image",in_out="OUTPUT",socket_type="NodeSocketColor")
render=compositor.nodes.new("CompositorNodeRLayers")
glow=compositor.nodes.new("CompositorNodeGlare")
glow.inputs["Type"].default_value="Fog Glow"
glow.inputs["Quality"].default_value="Medium"
glow.inputs["Threshold"].default_value=1.35
glow.inputs["Strength"].default_value=.40
glow.inputs["Size"].default_value=.22
compositor.links.new(render.outputs["Image"],glow.inputs["Image"])
latest=glow.outputs["Image"]


def full_frame_image(name):
    """Place exported HTML pixels at their original positions on a transparent canvas."""
    layer=layers[name]
    source=bpy.data.images.load(str(parts/layer["file"]),check_existing=False)
    w,h=round(layer["w"]),round(layer["h"])
    source.scale(w,h)
    data=np.empty(w*h*4,dtype=np.float32)
    source.pixels.foreach_get(data)
    canvas=np.zeros((1000,1600,4),dtype=np.float32)
    x,y=round(layer["x"]),1000-round(layer["y"])-h
    canvas[y:y+h,x:x+w,:]=data.reshape(h,w,4)
    image=bpy.data.images.new("Overlay "+name,width=1600,height=1000,alpha=True)
    image.colorspace_settings.name=source.colorspace_settings.name
    image.pixels.foreach_set(canvas.ravel())
    image.pack()
    bpy.data.images.remove(source)
    return image


def shade_image(name, inspection=False):
    """Soft cinematic light falloff, with no rectangular panel behind text."""
    y,x=np.mgrid[0:1000,0:1600]
    y=999-y
    if inspection:
        alpha=.94*np.exp(-(((x-1265)/295)**4+((y-385)/180)**4)*.8)
    else:
        alpha=np.maximum(.68*np.exp(-((y-105)/105)**4),
                         .65*np.exp(-((y-880)/95)**4))
    pixels=np.zeros((1000,1600,4),dtype=np.float32)
    pixels[:,:,:3]=(.003,.005,.01)
    pixels[:,:,3]=alpha
    image=bpy.data.images.new(name,width=1600,height=1000,alpha=True)
    image.pixels.foreach_set(pixels.ravel());image.pack()
    return image


def composite_image(image, background):
    node=compositor.nodes.new("CompositorNodeImage");node.image=image
    scale=compositor.nodes.new("CompositorNodeScale")
    scale.inputs["X"].default_value=args.resolution/100
    scale.inputs["Y"].default_value=args.resolution/100
    compositor.links.new(node.outputs["Image"],scale.inputs["Image"])
    over=compositor.nodes.new("CompositorNodeAlphaOver")
    compositor.links.new(background,over.inputs["Background"])
    compositor.links.new(scale.outputs["Image"],over.inputs["Foreground"])
    return over


latest=composite_image(shade_image("Typography falloff"),latest).outputs[0]

caption_names=sorted((name for name in layers if name.startswith("caption")),
                     key=lambda name:int(name.removeprefix("caption")))
caption_cuts=([1,200,305,475,600] if len(caption_names)==4 else
              [1,100,220,310,475,600] if len(caption_names)==5 else
              [round(1+599*j/len(caption_names)) for j in range(len(caption_names)+1)])
for i,name in enumerate(["header"]+caption_names):
    image_node=compositor.nodes.new("CompositorNodeImage")
    image_node.image=full_frame_image(name)
    over=compositor.nodes.new("CompositorNodeAlphaOver")
    compositor.links.new(latest,over.inputs["Background"])
    scale=compositor.nodes.new("CompositorNodeScale")
    scale.inputs["X"].default_value=args.resolution/100
    scale.inputs["Y"].default_value=args.resolution/100
    compositor.links.new(image_node.outputs["Image"],scale.inputs["Image"])
    compositor.links.new(scale.outputs["Image"],over.inputs["Foreground"])
    if name!="header":
        j=i-1
        start=caption_cuts[j];end=caption_cuts[j+1]-1 if j<len(caption_names)-1 else 600
        for f,value in [(1,0),(start,0),(start+6,1),(end-6,1),(end,0)]:
            socket_key(over.inputs["Factor"],value,f)
        if j==len(caption_names)-1:socket_key(over.inputs["Factor"],1,600)
    latest=over.outputs[0]
# The text is sharp screen-space typography; only its selected sphere and
# tether belong to the 3D scene. No card background and no persistent labels.
for number, node_id, start, end, radius in inspections:
    image_node=compositor.nodes.new("CompositorNodeImage")
    shade=composite_image(shade_image("Inspection falloff %d"%number,True),latest)
    for f,value in [(1,0),(start,0),(start+6,1),(end-6,1),(end,0),(600,0)]:
        socket_key(shade.inputs["Factor"],value,f)
    latest=shade.outputs[0]
    image_node.image=full_frame_image("inspect%d"%number)
    scale=compositor.nodes.new("CompositorNodeScale")
    scale.inputs["X"].default_value=args.resolution/100
    scale.inputs["Y"].default_value=args.resolution/100
    compositor.links.new(image_node.outputs["Image"],scale.inputs["Image"])
    over=compositor.nodes.new("CompositorNodeAlphaOver")
    compositor.links.new(latest,over.inputs["Background"])
    compositor.links.new(scale.outputs["Image"],over.inputs["Foreground"])
    for f,value in [(1,0),(start,0),(start+6,1),(end-6,1),(end,0),(600,0)]:
        socket_key(over.inputs["Factor"],value,f)
    latest=over.outputs[0]

group_output=compositor.nodes.new("NodeGroupOutput")
compositor.links.new(latest,group_output.inputs["Image"])

# Continuous camera arcs, linear check travel, and constant visibility switches.
for obj in scene.objects:
    if obj.animation_data and obj.animation_data.action:
        for layer in obj.animation_data.action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for point in fc.keyframe_points:
                            if fc.data_path=="hide_render":
                                point.interpolation="CONSTANT"
                            elif obj.name.startswith("Check photon"):
                                point.interpolation="LINEAR"
                            else:
                                point.handle_left_type="AUTO_CLAMPED"
                                point.handle_right_type="AUTO_CLAMPED"

scene.frame_set(1)
scene.render.filepath=str(output/"f")
if args.blend:
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.blend).resolve()))
if not args.no_render:
    if args.frames:
        for frame in map(int,args.frames.split(",")):
            scene.frame_set(frame);scene.render.filepath=str(output/("t%04d.png"%frame))
            bpy.ops.render.render(write_still=True)
    elif args.start_frame != 1 or args.end_frame != LAST:
        # Keep the timeline origin stable when rendering a patch.
        for frame in range(args.start_frame, args.end_frame + 1):
            scene.frame_set(frame)
            scene.render.filepath=str(output/("f%04d.png"%frame))
            bpy.ops.render.render(write_still=True)
    else:
        scene.render.filepath=str(output/"f")
        bpy.ops.render.render(animation=True)
