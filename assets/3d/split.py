"""書き出した UI レイヤーを 3D 空間の板として並べ、カメラを動かす。

UI はモデリングしない。平面の絵として書き出して、奥行きのある空間にカードとして
置く。これで HTML が原理的に出せないもの——被写界深度・モーションブラー・実光源の
反射・正確なフレーム——が付く。文言を直したらレイヤーを撮り直すだけで、
.blend 側のアニメーションはそのまま生きる。

  blender -b -P assets/3d/split.py -- --layers out/layers/split \
      --out out/3d/split --blend out/3d/split.blend [--frame 60] [--no-render]

.blend は開く Blender と同じ版で書く。新しい版で書いたものを古い版で開くと
「expect loss of data」の警告が出る。

画面座標はそのまま持ち込む。1600x1000 px の画面を 1.6 x 1.0 の板として扱い、
カメラをちょうどその幅が収まる距離に置く。あとはその基準からずらしていく。
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

PX = 100.0           # 1 Blender 単位 = 100 px。画面 1600x1000 が 16x10 単位
                     # 現実寸法に近づけないと、物理カメラの被写界深度が破綻する
FPS = 25
LAST = 125           # 5 秒


def arg(name, default=None):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return argv[argv.index(name) + 1] if name in argv else default


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def node(tree, idname):
    """ノードは名前で引かない。Blender の UI 言語が日本語だと
    「プリンシプルBSDF」になっていて KeyError になる。ソケット名は翻訳されない。"""
    for n in tree.nodes:
        if n.bl_idname == idname:
            return n
    raise SystemExit(f"{idname} が見つからない")


def card(name, png, x, y, z, w, h):
    """絵を 1 枚、板にして置く。z は上方向、y が奥行き。"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, z))
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (math.radians(90), 0, 0)   # カメラ（-y 側）を向かせる
    ob.scale = (w, h, 1.0)                         # 回したあとの高さは local Y

    img = bpy.data.images.load(os.path.abspath(png))
    img.alpha_mode = "STRAIGHT"
    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = node(nt, "ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    tex.location = (-400, 0)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    # UI は自分の明るさで読ませる。光源は縁とわずかな艶にだけ効かせる
    if "Emission Color" in bsdf.inputs:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Metallic"].default_value = 0.0

    # 透過の指定は 4.2 で名前が変わった。あるほうを使う
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, val)
            except TypeError:
                pass
    mat.use_backface_culling = False
    ob.data.materials.append(mat)
    return ob


def place(layers_dir):
    """layers.json の画面座標を、そのまま 3D の位置に移す。"""
    meta = json.load(open(os.path.join(layers_dir, "layers.json")))
    sw, sh = meta["stage"]
    out = {}
    for L in meta["layers"]:
        x = (L["x"] + L["w"] / 2 - sw / 2) / PX
        z = -(L["y"] + L["h"] / 2 - sh / 2) / PX
        out[L["name"]] = dict(
            png=os.path.join(layers_dir, L["file"]),
            x=x, z=z, w=L["w"] / PX, h=L["h"] / PX)
    return out


def fcurves(ob):
    """4.4 で Action が slot 制になり action.fcurves が無くなった。両方を見る。"""
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in getattr(layer, "strips", []):
            try:
                cb = strip.channelbag(ad.action_slot)
            except Exception:
                cb = None
            if cb:
                out.extend(cb.fcurves)
    return out


def key(ob, path, frames, interp="BEZIER"):
    """(フレーム, 値) の並びでキーを打つ。"""
    for f, v in frames:
        setattr(ob, path, v)
        ob.keyframe_insert(path, frame=f)
    for fc in fcurves(ob):
        if fc.data_path != path:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if interp == "BEZIER":
                kp.easing = "EASE_IN_OUT"


def main():
    layers_dir = os.path.abspath(arg("--layers", "out/layers/split"))
    out = os.path.abspath(arg("--out", "out/3d/split"))
    blend = arg("--blend")
    one = arg("--frame")
    many = arg("--frames")
    no_render = "--no-render" in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    clear()
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, LAST

    engines = {e.identifier for e in
               bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    sc.render.engine = ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines
                        else "BLENDER_EEVEE" if "BLENDER_EEVEE" in engines else "CYCLES")
    if arg("--cycles"):
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 64
    sc.render.use_motion_blur = True            # HTML から出てこないものの一つ
    if hasattr(sc.render, "motion_blur_shutter"):
        sc.render.motion_blur_shutter = 0.3
    ee = getattr(sc, "eevee", None)
    if ee is not None:
        if hasattr(ee, "taa_render_samples"):
            ee.taa_render_samples = 32
        if hasattr(ee, "use_raytracing"):
            ee.use_raytracing = False       # 板しかないので反射の追跡は要らない
        if hasattr(ee, "motion_blur_steps"):
            ee.motion_blur_steps = 4
    print("engine:", sc.render.engine)

    L = place(layers_dir)

    # --- 板を置く。左は手前、右はすこし奥。HTML では同じ平面にいたもの -----
    left = card("left", L["left"]["png"], L["left"]["x"], 0.0, L["left"]["z"],
                L["left"]["w"], L["left"]["h"])
    right = card("right", L["right"]["png"], L["right"]["x"], 2.0, L["right"]["z"],
                 L["right"]["w"], L["right"]["h"])
    band = card("band", L["band"]["png"], 0.0, -2.6, L["band"]["z"],
                L["band"]["w"], L["band"]["h"])
    chip_a = card("chipA", L["chip-from"]["png"], 0, 0, 0,
                  L["chip-from"]["w"], L["chip-from"]["h"])
    chip_b = card("chipB", L["chip-to"]["png"], 0, 0, 0,
                  L["chip-to"]["w"], L["chip-to"]["h"])

    # 板に厚みを与える。縁が光を拾うと、絵ではなく物に見える
    for ob in (left, right, chip_a, chip_b):
        m = ob.modifiers.new("solid", "SOLIDIFY")
        m.thickness = 0.06
        m.offset = 1.0

    # --- 飛行。HTML では平面内しか動けなかったものを、手前へ持ち上げる -----
    src = Vector((L["left"]["x"] + 0.2, -0.1, L["left"]["z"] + 0.2))
    dst = Vector((L["right"]["x"] - 0.3, 1.9, L["right"]["z"] - 0.1))
    mid = (src + dst) / 2 + Vector((0, -3.6, 1.1))       # カメラ側へふくらませる
    F0, F1 = 22, 78
    FM = (F0 + F1) // 2
    for ob in (chip_a, chip_b):
        key(ob, "location", [(F0, src), (FM, mid), (F1, dst)])
        key(ob, "rotation_euler",
            [(F0, (math.radians(90), 0, math.radians(-7))),
             (FM, (math.radians(84), 0, 0)),
             (F1, (math.radians(90), 0, math.radians(4)))])
    # 空中で表記が入れ替わる。Alpha は画像から来ているので板ごと出し入れする
    for ob, frames in ((chip_a, [(F0, 1.0), (FM - 6, 1.0), (FM + 6, 0.0), (F1, 0.0)]),
                       (chip_b, [(F0, 0.0), (FM - 6, 0.0), (FM + 6, 1.0), (F1, 1.0)])):
        key(ob, "hide_render", [(f, v < 0.5) for f, v in frames], interp="CONSTANT")
        key(ob, "scale", [(f, (ob.scale.x, ob.scale.y, 1.0)) for f, _ in frames])

    # 右の板は、箱が着いてから現れる
    key(right, "hide_render", [(1, True), (F1 - 2, True), (F1, False)], interp="CONSTANT")
    key(band, "hide_render", [(1, True), (96, True), (98, False)], interp="CONSTANT")

    # --- 光。板は自分で光るので、これは縁と空気のため -----------------------
    for loc, energy, size, color in (
        ((-11, -9, 8), 2600, 14.0, (0.42, 0.72, 0.95)),
        ((12, -7, -7), 1500, 14.0, (0.75, 0.55, 0.95)),
    ):
        bpy.ops.object.light_add(type="AREA", location=loc)
        lt = bpy.context.object
        lt.data.energy = energy
        lt.data.size = size
        lt.data.color = color

    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    node(world.node_tree, "ShaderNodeBackground").inputs[0].default_value = \
        (0.012, 0.018, 0.035, 1)
    sc.world = world

    # --- カメラ。回転は手で打たない。注視点を置いて追わせる ----------------
    # 寄りと手打ちのパンは必ず喧嘩する。何を見ているかだけ決めれば画は決まる。
    f = 50.0
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    look = bpy.context.object
    look.name = "look"

    cL = Vector((L["left"]["x"], 0.0, L["left"]["z"]))
    cR = Vector((L["right"]["x"], 2.0, L["right"]["z"]))
    end = Vector((L["right"]["x"] - 0.6, 1.2, -2.3))    # 最後は下の一文も入れる
    key(look, "location", [(1, cL), (F0, cL), (FM, mid), (F1, cR), (LAST, end)])

    cam_keys = [
        (1,    Vector((L["left"]["x"] + 0.4, -15.2,  0.6))),
        (F0,   Vector((L["left"]["x"] + 1.0, -15.6,  0.5))),
        (F1,   Vector((L["right"]["x"] - 1.6, -18.6, 0.1))),
        (LAST, Vector((L["right"]["x"] - 1.9, -21.5, -0.5))),
    ]
    bpy.ops.object.camera_add(location=cam_keys[0][1])
    cam = bpy.context.object
    cam.data.lens = f
    sc.camera = cam
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 3.2      # 板が読める範囲で、奥がほどけるところ
    tr = cam.constraints.new("TRACK_TO")
    tr.target = look
    tr.track_axis = "TRACK_NEGATIVE_Z"
    tr.up_axis = "UP_Y"
    key(cam, "location", cam_keys)

    # ピントは注視点に付いていく。そのフレームでのカメラとの距離をそのまま入れる
    look_keys = dict(((1, cL), (F0, cL), (FM, mid), (F1, cR), (LAST, end)))

    def cam_at(fr):
        for a, b in zip(cam_keys, cam_keys[1:]):
            if a[0] <= fr <= b[0]:
                return a[1].lerp(b[1], (fr - a[0]) / max(b[0] - a[0], 1))
        return cam_keys[-1][1]

    d = cam.data.dof
    for fr, target in look_keys.items():
        d.focus_distance = (cam_at(fr) - target).length
        d.keyframe_insert("focus_distance", frame=fr)

    if blend:
        blend = os.path.abspath(blend)
        os.makedirs(os.path.dirname(blend) or ".", exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=blend)      # クリエイタが開くのはこれ
        print("wrote", blend)

    if no_render:
        print("blend だけ書いた")
        return

    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = out + "/f"
    if many:
        for fr in [int(x) for x in many.split(",")]:
            sc.frame_set(fr)
            sc.render.filepath = out + "/t%03d" % fr
            bpy.ops.render.render(write_still=True)
    elif one:
        sc.frame_set(int(one))
        sc.render.filepath = out + "/test"
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
    print("done")


main()
