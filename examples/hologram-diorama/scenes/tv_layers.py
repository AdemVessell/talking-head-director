"""Scene 1: his television, taken apart into its layers (a lit paper diorama). Times: tv_layers.json."""
import math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "diorama"))   # this skill's kit
import kit as K
from mathutils import Vector

a = K.args(); T = a.T; K.reset(); sc = K.setup(a, T["dur"])
K.stage(floor=(0.018, 0.018, 0.02))   # a clean void: the dust carries the air

paper = K.mat("paper", (0.80, 0.79, 0.75), rough=0.9, spec=0.2, grain=0.012)
grey = K.mat("grey_card", (0.26, 0.26, 0.255), rough=0.88, spec=0.2, grain=0.012)
black = K.mat("black_card", (0.035, 0.035, 0.037), rough=0.62, spec=0.3, grain=0.008)
diff = K.mat("diffuser", (0.9, 0.9, 0.89), rough=0.92, alpha=0.42, spec=0.2, grain=0.006)
led = K.mat("led", (1.0, 0.95, 0.85), rough=0.4, emit=(1.0, 0.88, 0.7), strength=0.0)
red = K.mat("vermilion", K.VERMILION, rough=0.7, spec=0.2, grain=0.01)
crack_m = K.mat("crack", K.VERMILION, rough=0.5, emit=K.VERMILION, strength=0.0)
ink = K.mat("ink", (0.05, 0.05, 0.05), rough=0.7)
white_ink = K.mat("white_ink", (0.96, 0.95, 0.9), rough=0.7)
mote = K.mat("mote", (1, 0.95, 0.85), emit=(1.0, 0.93, 0.8), strength=1.5)
screen, bar_off = K.bars("screen")
fres, wave, glow = K.rings("fresnel", spacing=0.02)

Z0 = 0.42
layers = {}
def layer(name, y):
    e = K.empty(name, (0, y, Z0)); layers[name] = e; return e

g = layer("bezel", 0.000)
for nm, sz, lc in [("t", (0.64, 0.014, 0.022), (0, 0.18)), ("b", (0.64, 0.014, 0.022), (0, -0.18)),
                   ("l", (0.022, 0.014, 0.38), (-0.31, 0)), ("r", (0.022, 0.014, 0.38), (0.31, 0))]:
    K.box("bezel_" + nm, sz, (lc[0], 0.0, Z0 + lc[1]), m=black, parent=g)
g = layer("lcd", 0.010); K.box("lcd_panel", (0.60, 0.004, 0.345), (0, 0.010, Z0), m=screen, parent=g)
g = layer("fresnel", 0.016); K.box("fresnel_sheet", (0.60, 0.0015, 0.345), (0, 0.016, Z0), m=fres, bevel=0, parent=g)
g = layer("diffuser", 0.021); K.box("diffuser_sheet", (0.60, 0.0015, 0.345), (0, 0.021, Z0), m=diff, bevel=0, parent=g)
g = layer("backlight", 0.028); K.box("backlight_card", (0.60, 0.006, 0.345), (0, 0.028, Z0), m=paper, parent=g)
for i in range(9):
    for j in range(5):
        K.cyl(f"led_{i}_{j}", 0.009, 0.004, (-0.26 + i * 0.065, 0.0245, Z0 - 0.13 + j * 0.065), (math.pi / 2, 0, 0), m=led, verts=16, parent=g)
g = layer("back", 0.040); K.box("back_panel", (0.64, 0.016, 0.38), (0, 0.040, Z0), m=grey, parent=g)
for k in range(7):
    K.box(f"vent_{k}", (0.012, 0.002, 0.16), (-0.18 + k * 0.06, 0.031, Z0 + 0.06), m=ink, bevel=0, parent=g)
# a folded-card stand: two leaning boards and a foot
K.box("stand_a", (0.16, 0.012, 0.25), (0, 0.10, 0.12), (math.radians(-28), 0, 0), m=grey, parent=g)
K.box("stand_foot", (0.30, 0.20, 0.010), (0, 0.07, 0.005), m=grey, parent=g)

# the break: cracks radiating from an impact point on the screen
cx, cz = 0.07, Z0 + 0.05; rnd = random.Random(3); cracks = []
for k in range(7):
    ang = k * 2 * math.pi / 7 + rnd.uniform(-0.25, 0.25); r = 0.0; pts = [(cx, 0.0062, cz)]
    for s in range(5):
        r += rnd.uniform(0.022, 0.05); a2 = ang + rnd.uniform(-0.35, 0.35)
        pts.append((cx + r * math.cos(a2), 0.0062, cz + r * math.sin(a2)))
    cracks.append(K.polyline(f"crack_{k}", pts, crack_m, 0.0014 if k % 2 else 0.0018, parent=layers["lcd"]))
ring_pts = [(cx + 0.018 * math.cos(u * 2 * math.pi / 12), 0.0062, cz + 0.018 * math.sin(u * 2 * math.pi / 12)) for u in range(13)]
cracks.append(K.polyline("crack_ring", ring_pts, crack_m, 0.0012, parent=layers["lcd"]))

AZ = 30  # final camera heading: tags turn to face it
def tag(name, label, layer_name, m_card, m_text, w):  # hung off the layer's left edge, out in the air
    return K.tag(name, label, (-0.33 - w / 2 - 0.03, -0.002, Z0 + 0.10), m_card, m_text, ink, parent=layers[layer_name], w=w, h=0.07, size=0.04)
tags = {"lcd": tag("tag_lcd", "LCD", "lcd", paper, ink, 0.12), "fresnel": tag("tag_fresnel", "FRESNEL LENS", "fresnel", red, white_ink, 0.36),
        "diffuser": tag("tag_diffuser", "DIFFUSER", "diffuser", paper, ink, 0.25), "backlight": tag("tag_backlight", "BACKLIGHT", "backlight", paper, ink, 0.28)}

dust = K.dust(260, (0.0, -0.25, 0.9), (1.4, 1.2, 1.4), mote, seed=11)
K.light("SPOT", "beam", (0.05, -0.35, 2.6), (0, -0.25, 0.45), 520, color=(1.0, 0.94, 0.85), size=0.06, spot_deg=34, blend=0.55)
K.light("AREA", "rim", (0.9, 0.9, 1.1), (0, -0.2, 0.5), 90, color=(0.72, 0.82, 1.0), size=0.6)
K.light("AREA", "fill", (-1.2, -1.4, 0.6), (0, -0.2, 0.45), 18, color=(1, 1, 1), size=1.2)
cam = K.camera(lens=30, fstop=2.4)

ORDER = ["bezel", "lcd", "fresnel", "diffuser", "backlight"]   # the stack climbs toward us and up into the beam
STEP = {"bezel": 5, "lcd": 4, "fresnel": 3, "diffuser": 2, "backlight": 1}
BASE_Y = {n: layers[n].location.y for n in layers}
t_apart = T.get("apart", T["television"] - 0.62)

def cam_at(t):
    u = K.io2(K.seg(t, T["various"] - 0.2, T["dur"] + 0.3))
    az = math.radians(K.lerp(K.lerp(12, 16, K.seg(t, 0, T["various"])), AZ, u))
    dist = K.lerp(K.lerp(1.12, 1.0, K.io2(K.seg(t, 0, T["various"]))), 2.25, u)
    tgt = K.vlerp((0, 0.0, 0.36), (0.05, -0.26, 0.86), u)   # the screen sits above the caption band
    loc = Vector(tgt) + Vector((-math.sin(az) * dist, -math.cos(az) * dist, K.lerp(0.18, 0.05, u)))
    k = (t - T["broke"]) * 24
    if 0 <= k < 7:
        loc += Vector((0.007 * math.sin(k * 2.7), 0, 0.006 * math.cos(k * 3.1))) * math.exp(-0.4 * k)
    return loc, tgt

def frame(t):
    loose = 0.012 * K.oback(K.seg(t, t_apart, t_apart + 0.3))
    for i, n in enumerate(ORDER):
        t0 = T["various"] + 0.08 * i
        u = K.oback(K.seg(t, t0, t0 + 0.8), 1.0)
        k = STEP[n]
        bob = 0.006 * math.sin(1.9 * t + i) * K.seg(t, t0 + 0.8, t0 + 1.3)
        layers[n].location = (0.06 * k * u, BASE_Y[n] - loose * k / 5 - 0.10 * k * u, Z0 + 0.165 * k * u + bob)
        layers[n].rotation_euler = (math.radians(-6) * u, 0, math.radians(3 * (1 if i % 2 else -1)) * u)
    for i, (n, o) in enumerate(tags.items()):
        s = K.pop(t, T["layers"] - 0.25 + 0.1 * i)
        o.scale = (max(s, 1e-4),) * 3; o.rotation_euler = (0, 0, math.radians(-AZ * 0.6))
    for k, c in enumerate(cracks):
        c.data.bevel_factor_end = K.o3(K.seg(t, T["broke"] + 0.02 * k, T["broke"] + 0.18 + 0.02 * k))
    K._set(K._bsdf(crack_m), "Emission Strength", 4.0 * K.seg(t, T["broke"], T["broke"] + 0.08))
    on = K.seg(t, T["television"] - 0.12, T["television"] + 0.18) * (1 - K.seg(t, T["broke"] + 0.15, T["broke"] + 0.45))
    glitch = T["broke"] - 0.02 < t < T["broke"] + 0.45
    K._set(K._bsdf(screen), "Emission Strength", 1.6 * on * ((0.4 + 0.6 * abs(math.sin(t * 53))) if glitch else 1.0))
    bar_off.default_value = (0.11 * math.sin(t * 97) if glitch else 0.0)
    K._set(K._bsdf(led), "Emission Strength", 9.0 * K.seg(t, T["various"] + 0.45, T["various"] + 0.7) * (0.92 + 0.08 * math.sin(t * 37)))
    wave.default_value = -0.1 + 0.55 * K.seg(t, T["layers"] - 0.35, T["layers"] + 0.75)
    glow.default_value = 7.0 * K.seg(t, T["layers"] - 0.4, T["layers"] - 0.25)
    dust.location = (0.02 * math.sin(t * 0.7), 0.0, 0.03 * t)
    loc, tgt = cam_at(t)
    K.aim(cam, loc, tgt, focus=K.vlerp((0, 0.0, 0.44), (0.12, -0.3, 0.92), K.io2(K.seg(t, T["various"], T["layers"]))))

K.animate(frame); frame(0.0)
K.render(a, sc)
