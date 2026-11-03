"""Paper-diorama kit for Blender (run inside Blender, headless): scene shots for the edit engine.

A lit black stage with paper, card and acetate props, a camera with depth of field, and every
animated value written as a function of time (seconds), so scenes key straight to word times.
Render with:  Blender -b --factory-startup -P scene.py -- --times scene.json --out DIR [--res 1080x1920]
              [--fps 23.976] [--samples 32] [--stills 0.5,2.0 --scale 50]
then encode the frames with render_scene.sh (ProRes at the plan's frame rate) and use the clip as
`shot: scene` in the plan. Colours: paper, grey card, black card, one vermilion accent.
"""
import argparse, json, math, sys
import bpy
from mathutils import Vector

VERMILION = (226 / 255, 69 / 255, 43 / 255)
SUP = "/System/Library/Fonts/Supplemental/"


def lin(c):  # sRGB -> linear (Blender colour inputs are linear)
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ---------------------------------------------------------------- time
def c01(x): return max(0.0, min(1.0, x))
def lerp(a, b, u): return a + (b - a) * u
def seg(t, a, b): return c01((t - a) / (b - a)) if b > a else float(t >= b)
def io2(x): x = c01(x); return 2 * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 2 / 2
def io3(x): x = c01(x); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def o3(x): return 1 - (1 - c01(x)) ** 3
def oback(x, s=1.4): x = c01(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def vlerp(a, b, u): return Vector(a).lerp(Vector(b), u)


def pop(t, t0, d=0.22):
    """Stop-motion arrival: 0 -> 1.12 -> 1 on twos (each value held for two frames at 24 fps)."""
    k = math.floor((t - t0) * 12) / 12 + 1e-6
    if t < t0:
        return 0.0
    return oback(k / d, 2.2) if k < d else 1.0


# ---------------------------------------------------------------- setup
def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--times"); ap.add_argument("--out", required=True)
    ap.add_argument("--res", default="1080x1920"); ap.add_argument("--fps", type=float, default=23.976)
    ap.add_argument("--samples", type=int, default=32); ap.add_argument("--stills", default="")
    ap.add_argument("--scale", type=int, default=100)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    a.T = json.load(open(a.times)) if a.times else {}
    return a


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def setattr_any(obj, names, value):
    for n in names:
        if hasattr(obj, n):
            try:
                setattr(obj, n, value); return True
            except (TypeError, AttributeError, ValueError):
                pass
    return False


def setup(a, dur):
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    w, h = (int(x) for x in a.res.split("x"))
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, a.scale
    if abs(a.fps - 23.976) < 0.01:
        sc.render.fps, sc.render.fps_base = 24, 1.001
    else:
        sc.render.fps, sc.render.fps_base = int(round(a.fps)), 1.0
    sc.frame_start, sc.frame_end = 1, int(math.ceil(dur * a.fps)) + 1
    ee = sc.eevee
    setattr_any(ee, ["taa_render_samples"], a.samples)
    setattr_any(ee, ["use_raytracing"], True)
    setattr_any(ee, ["use_shadows"], True)
    setattr_any(ee, ["use_gtao"], True)
    setattr_any(ee, ["shadow_ray_count"], 2); setattr_any(ee, ["shadow_step_count"], 8)
    setattr_any(sc.render, ["use_motion_blur"], True) or setattr_any(ee, ["use_motion_blur"], True)
    setattr_any(sc.render, ["motion_blur_shutter"], 0.5) or setattr_any(ee, ["motion_blur_shutter"], 0.5)
    setattr_any(sc.view_settings, ["view_transform"], "AgX") or setattr_any(sc.view_settings, ["view_transform"], "Filmic")
    for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):  # highlights roll off instead of clipping
        if setattr_any(sc.view_settings, ["look"], look):
            break
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGB"
    sc.render.filepath = a.out.rstrip("/") + "/f_"
    world = bpy.data.worlds.new("dark"); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.004, 0.004, 0.005, 1); bg.inputs["Strength"].default_value = 1.0
    return sc


# ---------------------------------------------------------------- materials
def _bsdf(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _set(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def mat(name, color=(0.85, 0.84, 0.8), rough=0.8, alpha=1.0, emit=None, strength=0.0, spec=0.3, grain=0.0, srgb=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = _bsdf(m)
    col = lin(color) if srgb else color
    _set(b, "Base Color", (*col, 1)); _set(b, "Roughness", rough)
    _set(b, "Specular IOR Level", spec); _set(b, "Alpha", alpha)
    if emit is not None:
        _set(b, "Emission Color", (*(lin(emit) if srgb else emit), 1)); _set(b, "Emission Strength", strength)
    if alpha < 1:
        setattr_any(m, ["surface_render_method"], "BLENDED") or setattr_any(m, ["blend_method"], "BLEND")
    if grain:  # paper tooth: a fine noise bump
        nt = m.node_tree; n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 420
        n.inputs["Detail"].default_value = 6.0
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = grain
        nt.links.new(n.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def rings(name, spacing=0.012, base_alpha=0.16, line_alpha=0.55, glow=(1.0, 0.93, 0.8)):
    """Acetate printed with concentric grooves (a Fresnel lens). Returns (material, wave value node,
    glow value node): wave is the radius (m) of a travelling bright ring; glow scales the emission."""
    m = mat(name, (0.92, 0.94, 0.97), rough=0.12, alpha=base_alpha, spec=0.8)
    nt = m.node_tree; b = _bsdf(m); N = nt.nodes.new; L = nt.links.new
    tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
    comb = N("ShaderNodeCombineXYZ"); L(sep.outputs["X"], comb.inputs["X"]); L(sep.outputs["Z"], comb.inputs["Z"])
    r = N("ShaderNodeVectorMath"); r.operation = "LENGTH"; L(comb.outputs[0], r.inputs[0])

    def math_(op, a=None, b_=None, va=None, vb=None):
        n = N("ShaderNodeMath"); n.operation = op
        if a is not None: L(a, n.inputs[0])
        if va is not None: n.inputs[0].default_value = va
        if b_ is not None: L(b_, n.inputs[1])
        if vb is not None: n.inputs[1].default_value = vb
        return n.outputs[0]
    fr = math_("FRACT", math_("MULTIPLY", r.outputs["Value"], vb=1 / spacing))
    line = math_("LESS_THAN", fr, vb=0.14)                       # the groove line
    wave = N("ShaderNodeValue"); wave.outputs[0].default_value = -1.0
    band = math_("MAXIMUM", math_("SUBTRACT", None, math_("DIVIDE", math_("ABSOLUTE", math_("SUBTRACT", r.outputs["Value"], wave.outputs[0])), vb=0.05), va=1.0), vb=0.0)
    glow_v = N("ShaderNodeValue"); glow_v.outputs[0].default_value = 0.0
    em = math_("MULTIPLY", math_("ADD", math_("MULTIPLY", line, band), math_("MULTIPLY", line, vb=0.08)), glow_v.outputs[0])
    L(em, b.inputs["Emission Strength"]); _set(b, "Emission Color", (*lin(glow), 1))
    L(math_("ADD", math_("MULTIPLY", line, vb=line_alpha - base_alpha), vb=base_alpha), b.inputs["Alpha"])
    return m, wave.outputs[0], glow_v.outputs[0]


# ---------------------------------------------------------------- objects
def _active():
    return bpy.context.view_layer.objects.active


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), m=None, bevel=0.0015, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = _active(); o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("bevel", "BEVEL"); mod.width = bevel; mod.segments = 2
    if m:
        o.data.materials.append(m)
    if parent:
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def cyl(name, r, depth, loc=(0, 0, 0), rot=(0, 0, 0), m=None, verts=32, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = _active(); o.name = name
    if m:
        o.data.materials.append(m)
    if parent:
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); o.location = loc; bpy.context.scene.collection.objects.link(o)
    return o


def text(name, body, size, loc, m, font="Courier New Bold.ttf", rot=(math.pi / 2, 0, 0), extrude=0.0006, parent=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.font = bpy.data.fonts.load(SUP + font)
    o = bpy.data.objects.new(name, cu); o.location = loc; o.rotation_euler = rot
    o.data.materials.append(m); bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def tag(name, label, loc, paper, ink, string, parent=None, w=0.11, h=0.036, size=0.017):
    """A paper luggage tag on a short string, facing the camera (-y)."""
    root = empty(name, loc)
    if parent:
        root.parent = parent; root.matrix_parent_inverse = parent.matrix_world.inverted()
    box(name + "_card", (w, 0.0012, h), (loc[0], loc[1], loc[2]), m=paper, bevel=0.0006, parent=root)
    text(name + "_txt", label, size, (loc[0] + 0.004, loc[1] - 0.0012, loc[2] - 0.001), ink, parent=root)
    cyl(name + "_hole", 0.0035, 0.002, (loc[0] - w / 2 + 0.008, loc[1] - 0.0007, loc[2]), (math.pi / 2, 0, 0), m=ink, parent=root)
    cyl(name + "_str", 0.0007, 0.07, (loc[0] - w / 2 - 0.022, loc[1], loc[2] + 0.02), (0, math.radians(55), 0), m=string, verts=8, parent=root)
    return root


def stage(floor=(0.035, 0.035, 0.038), wall=False, grain=0.004):
    """A black stage: a near-black card floor (and optionally a far wall); beyond it, the void."""
    m = mat("stage", floor, rough=0.75, spec=0.15, grain=grain)
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 1.5, 0)); f = _active(); f.name = "floor"; f.data.materials.append(m)
    if wall:
        bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 3.2, 3.5), rotation=(math.pi / 2, 0, 0))
        w = _active(); w.name = "wall"; w.data.materials.append(m)
    return m


def look(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def light(kind, name, loc, target, energy, color=(1, 0.96, 0.9), size=0.3, spot_deg=55, blend=0.6):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == "AREA":
        ld.size = size
    else:
        setattr_any(ld, ["shadow_soft_size"], size)
    if kind == "SPOT":
        ld.spot_size = math.radians(spot_deg); ld.spot_blend = blend
    o = bpy.data.objects.new(name, ld); o.location = loc; bpy.context.scene.collection.objects.link(o)
    look(o, target)
    return o


def camera(lens=32, fstop=2.8):
    cd = bpy.data.cameras.new("cam"); cd.lens = lens; cd.sensor_fit = "AUTO"
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    o = bpy.data.objects.new("cam", cd); bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    return o


def aim(cam, loc, target, focus=None):
    cam.location = loc; look(cam, target)
    cam.data.dof.focus_distance = (Vector(focus or target) - Vector(loc)).length


# ---------------------------------------------------------------- run
def animate(fn):
    """fn(t) sets every animated value for time t (seconds); it runs for frames and motion-blur subframes."""
    def h(scene, *_):
        fps = scene.render.fps / scene.render.fps_base
        fn((scene.frame_current - 1 + scene.frame_subframe) / fps)
    bpy.app.handlers.frame_change_pre.clear(); bpy.app.handlers.frame_change_pre.append(h)


def render(a, sc):
    fps = sc.render.fps / sc.render.fps_base
    if a.stills:
        for s in a.stills.split(","):
            f = int(round(float(s) * fps)) + 1
            sc.frame_set(f); sc.render.filepath = f"{a.out.rstrip('/')}/still_{float(s):05.2f}.png"
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


# ---------------------------------------------------------------- atmosphere and screens
def haze(density=0.008, anisotropy=0.5):
    """Air you can see light in: a world volume, so a spot from above draws its beam."""
    sc = bpy.context.scene; nt = sc.world.node_tree
    vs = nt.nodes.new("ShaderNodeVolumeScatter")
    vs.inputs["Density"].default_value = density; vs.inputs["Anisotropy"].default_value = anisotropy
    out = next(n for n in nt.nodes if n.type == "OUTPUT_WORLD")
    nt.links.new(vs.outputs["Volume"], out.inputs["Volume"])
    ee = sc.eevee
    setattr_any(ee, ["volumetric_start"], 0.1); setattr_any(ee, ["volumetric_end"], 8.0)
    setattr_any(ee, ["volumetric_tile_size"], "4"); setattr_any(ee, ["volumetric_samples"], 64)
    setattr_any(ee, ["use_volumetric_shadows"], True); setattr_any(ee, ["volumetric_shadow_samples"], 16)
    return vs


def dust(n, center, size, m, seed=7, r=0.0011):
    """A cloud of dust motes (one mesh). Drift it by moving the object."""
    import bmesh, random
    rnd = random.Random(seed); me = bpy.data.meshes.new("dust"); bm = bmesh.new()
    for _ in range(n):
        c = Vector(center) + Vector(((rnd.random() - 0.5) * size[0], (rnd.random() - 0.5) * size[1], (rnd.random() - 0.5) * size[2]))
        rr = r * (0.5 + rnd.random())
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rr, matrix=__import__("mathutils").Matrix.Translation(c))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("dust", me); o.data.materials.append(m); bpy.context.scene.collection.objects.link(o)
    return o


def bars(name):
    """A screen showing SMPTE-style colour bars. Returns (material, offset value node): offset slides the bars (glitch)."""
    m = mat(name, (0.02, 0.022, 0.026), rough=0.3, spec=0.6, emit=(1, 1, 1), strength=0.0)
    nt = m.node_tree; b = _bsdf(m); N = nt.nodes.new; L = nt.links.new
    tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], sep.inputs[0])
    off = N("ShaderNodeValue"); off.outputs[0].default_value = 0.0
    add = N("ShaderNodeMath"); add.operation = "ADD"; L(sep.outputs["X"], add.inputs[0]); L(off.outputs[0], add.inputs[1])
    fr = N("ShaderNodeMath"); fr.operation = "FRACT"; L(add.outputs[0], fr.inputs[0])
    ramp = N("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    cols = [(0.75, 0.75, 0.75), (0.75, 0.75, 0.0), (0.0, 0.75, 0.75), (0.0, 0.75, 0.0), (0.75, 0.0, 0.75), (0.75, 0.0, 0.0), (0.0, 0.0, 0.75)]
    els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = (*lin(cols[0]), 1); els[1].position = 1 / 7; els[1].color = (*lin(cols[1]), 1)
    for k in range(2, 7):
        e = els.new(k / 7); e.color = (*lin(cols[k]), 1)
    L(fr.outputs[0], ramp.inputs["Fac"]); L(ramp.outputs["Color"], b.inputs["Emission Color"])
    return m, off.outputs[0]


def polyline(name, pts, m, depth=0.0016, parent=None):
    """A drawn line (cracks, strokes): animate obj.data.bevel_factor_end from 0 to 1 to draw it."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_factor_end = 0.0
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p_, xyz in zip(sp.points, pts):
        p_.co = (*xyz, 1.0)
    o = bpy.data.objects.new(name, cu); o.data.materials.append(m); bpy.context.scene.collection.objects.link(o)
    if parent:
        o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o
