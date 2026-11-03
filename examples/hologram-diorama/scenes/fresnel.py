"""Scene 2: "well, behind me hung up is one of the Fresnel type lens things" (a lit paper diorama).
The lens drops into its clips on "hung", its grooves light on "Fresnel", his paper figure steps behind
it and its magnified hologram appears on "lens". Times: fresnel.json."""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "diorama"))   # this skill's kit
import kit as K
from mathutils import Vector

a = K.args(); T = a.T; K.reset(); sc = K.setup(a, T["dur"])
K.stage(floor=(0.018, 0.018, 0.02))

black = K.mat("black_card", (0.03, 0.03, 0.032), rough=0.6, spec=0.3, grain=0.008)
grey = K.mat("grey_card", (0.26, 0.26, 0.255), rough=0.88, spec=0.2, grain=0.012)
wire_m = K.mat("wire", (0.5, 0.5, 0.52), rough=0.35, spec=0.8)
mote = K.mat("mote", (1, 0.95, 0.85), emit=(1.0, 0.93, 0.8), strength=1.5)
def hologram(name, col):
    """Translucent, emissive and scanlined: one value node drives its presence (0-1)."""
    m = K.mat(name, col, rough=0.5, alpha=0.0, emit=col, strength=0.0)
    nt = m.node_tree; b = K._bsdf(m); N = nt.nodes.new; L = nt.links.new
    tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
    mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 900.0; L(sep.outputs["Z"], mul.inputs[0])
    sn = N("ShaderNodeMath"); sn.operation = "SINE"; L(mul.outputs[0], sn.inputs[0])
    scan = N("ShaderNodeMapRange"); scan.inputs["From Min"].default_value = -1; scan.inputs["To Min"].default_value = 0.45; L(sn.outputs[0], scan.inputs["Value"])
    amt = N("ShaderNodeValue"); amt.outputs[0].default_value = 0.0
    al = N("ShaderNodeMath"); al.operation = "MULTIPLY"; L(scan.outputs["Result"], al.inputs[0]); L(amt.outputs[0], al.inputs[1])
    L(al.outputs[0], b.inputs["Alpha"])
    em = N("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 4.0; L(al.outputs[0], em.inputs[0])
    L(em.outputs[0], b.inputs["Emission Strength"])
    return m, amt.outputs[0]
ghost_c, amt_c = hologram("ghost", (0.62, 0.9, 1.0))
ghost_r, amt_r = hologram("ghost_red", K.VERMILION)
fres, wave, glow = K.rings("fresnel", spacing=0.016, base_alpha=0.14, line_alpha=0.45)

LX, LY, LZ = 0.0, 0.26, 0.70           # the lens centre (it hangs 0.46 x 0.60)
lens = K.empty("lens", (LX, LY, LZ))
K.box("lens_sheet", (0.46, 0.0015, 0.60), (LX, LY, LZ), m=fres, bevel=0, parent=lens)
K.cyl("wire", 0.0016, 1.3, (0, LY, 1.02), (0, math.pi / 2, 0), m=wire_m, verts=12)
for sx in (-0.17, 0.17):
    K.box(f"clip_{sx}", (0.045, 0.024, 0.032), (sx, LY, 1.0), m=black)
    K.box(f"clip_h_{sx}", (0.004, 0.03, 0.03), (sx, LY, 1.03), (math.radians(30), 0, 0), m=wire_m, bevel=0)

def figure(name, scale, m, loc, legs=True):
    """His paper cutout: cap, head, shoulders, body (a flat black card standing up)."""
    root = K.empty(name, loc); s = scale; x, y, z = loc
    K.cyl(name + "_head", 0.055 * s, 0.004, (x, y, z + 0.40 * s), (math.pi / 2, 0, 0), m=m, verts=40, parent=root)
    K.box(name + "_cap", (0.12 * s, 0.004, 0.035 * s), (x, y, z + 0.445 * s), m=m, bevel=0.003, parent=root)
    K.box(name + "_brim", (0.08 * s, 0.004, 0.012 * s), (x + 0.07 * s, y, z + 0.432 * s), m=m, bevel=0.002, parent=root)
    K.box(name + "_neck", (0.04 * s, 0.004, 0.05 * s), (x, y, z + 0.33 * s), m=m, bevel=0, parent=root)
    K.box(name + "_body", (0.20 * s, 0.004, 0.26 * s), (x, y, z + 0.18 * s), m=m, bevel=0.02 * s, parent=root)
    if legs:
        K.box(name + "_legs", (0.14 * s, 0.004, 0.08 * s), (x, y, z + 0.04 * s), m=m, bevel=0.005, parent=root)
    return root

FIG0 = Vector((-0.13, -0.06, 0.0))
fig = figure("fig", 1.0, black, tuple(FIG0))
GH = Vector((0.0, LY - 0.006, 0.34))   # a magnified bust that sits inside the lens
ghost = figure("ghost", 1.25, ghost_c, tuple(GH), legs=False)
ghost_r_ = figure("ghost_red", 1.25, ghost_r, (GH.x + 0.01, GH.y + 0.002, GH.z), legs=False)

dust = K.dust(220, (0.0, 0.1, 0.8), (1.3, 1.2, 1.4), mote, seed=23)
K.light("SPOT", "beam", (0.0, -0.25, 2.6), (0, 0.1, 0.5), 520, color=(1.0, 0.94, 0.85), size=0.06, spot_deg=40, blend=0.6)
K.light("AREA", "behind", (0.15, 1.25, 0.95), (0, 0.2, 0.6), 160, color=(0.7, 0.85, 1.0), size=0.7)
K.light("AREA", "fill", (-1.2, -1.4, 0.6), (0, 0.1, 0.5), 15, color=(1, 1, 1), size=1.2)
cam = K.camera(lens=35, fstop=2.4)

def frame(t):
    # the lens drops into its clips on "hung", then swings and settles
    u = K.oback(K.seg(t, T["hung"] - 0.05, T["hung"] + 0.3), 1.6)
    swing = math.radians(5) * math.exp(-2.2 * max(0.0, t - T["hung"] - 0.25)) * math.sin(7 * (t - T["hung"])) * (t > T["hung"] + 0.25)
    lens.location = (LX, LY, LZ + 0.9 * (1 - u)); lens.rotation_euler = (swing, 0, 0)
    # the rings light outward on "Fresnel"
    wave.default_value = -0.1 + 0.48 * K.seg(t, T["fresnel"] - 0.05, T["fresnel"] + 0.75)
    glow.default_value = 6.0 * K.seg(t, T["fresnel"] - 0.1, T["fresnel"] + 0.05)
    # he steps behind it on twos (three steps), then his hologram swells into the lens on "lens"
    st = math.floor(K.seg(t, T["fresnel"] + 0.35, T["lens"] - 0.05) * 3) / 3
    fig.location = FIG0 + Vector((0.13 * st, 0.48 * st, 0.0))
    g = K.seg(t, T["lens"] - 0.05, T["lens"] + 0.25) * (0.82 + 0.18 * math.sin(t * 43) * math.sin(t * 7.3))
    gs = K.lerp(0.85, 1.0, K.o3(K.seg(t, T["lens"] - 0.05, T["lens"] + 0.35)))
    for o, amt, al in ((ghost, amt_c, 0.34), (ghost_r_, amt_r, 0.16)):
        o.scale = (gs, gs, gs); amt.default_value = al * g
    dust.location = (0.02 * math.sin(t * 0.6), 0.0, 0.025 * t)
    p = K.io2(K.seg(t, 0, T["dur"]))
    loc = K.vlerp((-0.30, -1.35, 0.56), (-0.16, -1.08, 0.62), p)
    tgt = K.vlerp((-0.02, 0.15, 0.58), (0.0, 0.22, 0.66), p)
    K.aim(cam, loc, tgt, focus=K.vlerp((-0.13, -0.06, 0.4), (LX, LY, LZ), K.io2(K.seg(t, T["hung"], T["fresnel"]))))

K.animate(frame); frame(0.0)
K.render(a, sc)
