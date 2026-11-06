"""Blender を headless で回して素材を 1 本焼く雛形。

  blender --background --python assets/3d/wordmark.py -- --out out/3d/wordmark.mp4

GUI で作った .blend を置いて差し替えてもよいが、スクリプトで組んでおくと
色や尺を直したときに同じ絵が出る。タイムライン側が素材の尺を前提にするので、
作り直すたびに違う長さが出てくるのが一番困る。
"""
import math
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = "out/3d/wordmark.mp4"
if "--out" in argv:
    out = argv[argv.index("--out") + 1]
out = os.path.abspath(out)
os.makedirs(os.path.dirname(out), exist_ok=True)

SECONDS = 3.0
FPS = 25

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = int(SECONDS * FPS)

# EEVEE の識別子は 4.2 で改名された。ある方を使う
engines = {e.identifier for e in
           bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
scene.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines
                       else "BLENDER_EEVEE")

# 文字を押し出す
bpy.ops.object.text_add()
txt = bpy.context.object
txt.data.body = "NYXIS"
txt.data.extrude = 0.10
txt.data.bevel_depth = 0.006
txt.data.align_x = "CENTER"
txt.data.align_y = "CENTER"
txt.rotation_euler = (math.radians(90), 0, 0)

mat = bpy.data.materials.new("wordmark")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.86, 0.90, 1.0, 1)
bsdf.inputs["Metallic"].default_value = 0.85
bsdf.inputs["Roughness"].default_value = 0.22
txt.data.materials.append(mat)

# 回す。最初と最後だけキーを打てば線形に回る
txt.keyframe_insert("rotation_euler", frame=scene.frame_start)
txt.rotation_euler = (math.radians(90), 0, math.radians(360))
txt.keyframe_insert("rotation_euler", frame=scene.frame_end)
for fc in txt.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

bpy.ops.object.light_add(type="AREA", location=(2.5, -3.5, 3))
bpy.context.object.data.energy = 900
bpy.ops.object.light_add(type="AREA", location=(-3, -2, -1))
bpy.context.object.data.energy = 300

bpy.ops.object.camera_add(location=(0, -5.2, 0), rotation=(math.radians(90), 0, 0))
scene.camera = bpy.context.object
scene.world = bpy.data.worlds.new("world")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.03, 0.05, 1)

scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.use_file_extension = False
scene.render.filepath = out
bpy.ops.render.render(animation=True)

# Blender は動画の書き出し先にフレーム範囲を足すことがある。足されたら戻す
if not os.path.exists(out):
    base, ext = os.path.splitext(out)
    import glob
    hits = glob.glob(base + "*" + ext) or glob.glob(base + "*")
    if hits:
        os.replace(hits[0], out)
print("wrote", out)
