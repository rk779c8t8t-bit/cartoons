"""The nine shots of «Над котёнком все смеялись». Each function builds and animates one shot.

Timeline: 30 fps, 9 shots x 120 frames = 36 s. TAIL = extra frames rendered after the
shot's own 120 frames so the editor can cross-dissolve into the next shot.
"""
import math
import random
import bpy
from mathutils import Vector

import common
import env as envmod
import props
from characters import Actor
from mats import hexc

FPS = 30
DUR = 120
TAIL = {1: 0, 2: 10, 3: 12, 4: 0, 5: 0, 6: 0, 7: 8, 8: 12, 9: 0}


def frames_for(n):
    return DUR + TAIL[n]


# ----------------------------------------------------------------- helpers
def key_interp(ob, path, frame, interp="QUAD", easing="EASE_IN"):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.5:
                    kp.interpolation = interp
                    kp.easing = easing


def set_light(preset, sun_rot=None):
    P = {
        "morning": dict(top="#5f9fe0", hor="#fde7c4", ws=0.9, clouds=0.35, cc="#ffffff", sun=4.0, sc="#ffe2b8", rot=(50, 0, -30), fill="#bcd4ff"),
        "overcast": dict(top="#8ea3b8", hor="#d9dde0", ws=0.9, clouds=0.9, cc="#c9cfd6", sun=1.5, sc="#e6ecf5", rot=(55, 0, -25), fill="#c8d4e6"),
        "rain": dict(top="#6d7c8c", hor="#aab4bd", ws=0.85, clouds=1.0, cc="#9aa5b0", sun=0.7, sc="#cfdbe8", rot=(60, 0, -20), fill="#9fb2c8"),
        "windy": dict(top="#7d9bbb", hor="#dfe2e0", ws=0.95, clouds=0.85, cc="#e8ecef", sun=2.0, sc="#f1efe6", rot=(55, 0, 40), fill="#c4d2e4"),
        "golden": dict(top="#6f9bd0", hor="#ffd29a", ws=1.0, clouds=0.45, cc="#ffe8cc", sun=4.2, sc="#ffcf8a", rot=(70, 0, 40), fill="#ffd9b0"),
    }[preset]
    common.world_sky(P["top"], P["hor"], P["ws"], clouds=P["clouds"], cloud_color=P["cc"])
    sun = common.sun("Sun", sun_rot or P["rot"], P["sun"], P["sc"], angle=4.0)
    return sun, P


def fill_light(loc, target, energy=150, color="#dfe9ff", size=4.0):
    return common.area("Fill", loc, target, energy, size, color, shadow=False)


def blinks(actor, frames):
    for f in frames:
        actor.blink(f)


def cam_shake(cam, f0, f1, strength=0.04):
    fc = cam.animation_data.action.fcurves
    for idx in (0, 2):
        c = fc.find("location", index=idx)
        m = c.modifiers.new("NOISE")
        m.scale = 2.0
        m.strength = strength
        m.use_restricted_range = True
        m.frame_start = f0
        m.frame_end = f1
        m.blend_in = 2
        m.blend_out = 6


def board_on_rock(alpha_deg, R=(1.35, -6.5, 0.32)):
    """Board pivot transform when the board rests on the rock with pitch alpha (south end up for alpha>0)."""
    a = math.radians(alpha_deg)
    c = (R[0], R[1] - 0.42 * math.cos(a), R[2] + 0.42 * math.sin(a) + 0.02)
    return c, (-a, 0, 0)


def key_obj(ob, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=frame)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert("rotation_euler", frame=frame)
    if scale is not None:
        ob.scale = scale
        ob.keyframe_insert("scale", frame=frame)


def branch_rest(E, frame, lift_deg=0.0):
    b = E.objs["branch"]
    key_obj(b, frame, (-2.3, -6.15, 0.15), (0, -math.radians(lift_deg), 0))


# =================================================================== SHOT 1
def shot1():
    sun, _ = set_light("morning", (50, 0, -35))
    fill_light((1, 4, 3), (-1.5, 7.5, 0.8), 120, "#cfe0ff")
    E = envmod.Env(wet=False)
    E.sway_trees(1, 130, 0.5)
    k = Actor("ryzhik", loc=(-4.5, 8.6))
    k.bag_mode(1, "front")
    hold = dict(sh_L_x=38, sh_R_x=38, sh_L_y=-18, sh_R_y=-18, el_L=78, el_R=78)
    k.key(1, rot=90, smile=0.45, ear_L=5, ear_R=5, tail_up=0.3, brow=0.15, **hold)
    k.walk(1, 90, (-1.25, 7.85), step=9, stride=22, arm=0)
    k.key(96, head_rx=-12, gaze_y=10, **{kk: v for kk, v in k.aim((0, 11.5, 2.5)).items() if kk in ("head_rz", "gaze_x")})
    k.key(104, rot=20, smile=0.6, brow=0.3)
    k.key(112, smile=0.8, brow=0.35, ear_L=12, ear_R=12, tail_up=0.6, head_ry=-6, **k.aim((-1.0, 6.15, 0.95)))
    k.key(122, smile=0.85, head_ry=-8)
    blinks(k, [30, 74, 100])
    k.add_life()
    cam, tgt = common.camera("Cam", lens=24, fstop=4.0)
    common.cam_key(cam, tgt, 1, (0.6, 0.6, 3.6), (-1.6, 9.6, 2.0), lens=22)
    common.cam_key(cam, tgt, 24, (-0.2, 3.6, 2.0), (-3.4, 8.3, 0.9), lens=26)
    common.cam_key(cam, tgt, 52, (-1.35, 7.2, 0.3), (-2.75, 8.25, 0.12), lens=40)
    common.cam_key(cam, tgt, 80, (-0.75, 7.0, 0.65), (-1.75, 7.95, 0.65), lens=42)
    common.cam_key(cam, tgt, 106, (-1.0, 6.15, 0.95), (-1.25, 7.85, 0.85), lens=45)
    common.cam_key(cam, tgt, 122, (-1.02, 6.3, 0.95), (-1.25, 7.85, 0.88), lens=48)
    return dict(cams=[cam])


# =================================================================== SHOT 2
def shot2():
    sun, _ = set_light("overcast", (55, 0, -10))
    fill_light((-2.5, 5.5, 2.5), (0, 9, 0.8), 140, "#d0dcef")
    E = envmod.Env(wet=False)
    E.sway_trees(1, 140, 0.6)
    k = Actor("ryzhik", loc=(-0.9, 8.6), rot=119)
    f = Actor("fox", loc=(0.75, 9.65), rot=-60)
    r = Actor("raccoon", loc=(1.4, 9.15), rot=-80)
    k.bag_mode(1, "back")
    # kitten: hopeful little wave
    k.key(1, smile=0.6, brow=0.25, ear_L=4, ear_R=4, tail_up=0.3, **k.aim((0.75, 9.65, 0.95)))
    k.key(10, sh_L_x=40, sh_L_y=30, el_L=80, smile=0.75)
    k.key(16, sh_L_y=40, sh_L_z=12)
    k.key(22, sh_L_y=30, sh_L_z=-10)
    k.key(30, sh_L_x=0, sh_L_y=8, sh_L_z=0, el_L=10, smile=0.6)
    # they notice the boots
    f.key(1, smile=0.4, **f.aim((0.0, 8.8, 0.9)))
    r.key(1, smile=0.4, head_rz=-30, **{kk: v for kk, v in r.aim((0.75, 9.65, 0.95)).items() if kk != "head_rz"})
    f.key(14, **f.aim((-0.9, 8.6, 0.1)), eyes_open=1.1, brow=0.3)
    f.key(24, **f.aim((1.4, 9.15, 0.95)), smile=0.8)
    r.key(26, **r.aim((0.75, 9.65, 0.95)))
    r.key(34, **r.aim((-0.9, 8.6, 0.1)), eyes_open=1.1)
    f.key(34, **f.aim((-0.9, 8.6, 0.1)), sh_R_x=65, sh_R_y=-5, el_R=15, smile=0.9)
    f.laugh(38, 86, period=5)
    r.key(40, smile=1.0)
    r.laugh(42, 88, period=6)
    f.key(92, sh_R_x=20, el_R=20, smile=0.8, mouth_open=0.2, eyes_open=0.7)
    r.key(92, sh_L_x=40, el_L=90, sh_L_y=-10, smile=0.8, mouth_open=0.3, eyes_open=0.6, head_ry=8)
    f.key(130, sh_R_x=5, el_R=15, smile=0.6, mouth_open=0.1, eyes_open=0.8)
    r.key(130, sh_L_x=35, smile=0.6, mouth_open=0.15)
    # kitten reaction
    k.key(40, smile=0.4, brow=0.4, **k.aim((0.75, 9.65, 1.0)))
    k.key(50, smile=0.0, frown=0.3, brow=0.85, ear_L=35, ear_R=35, tail_up=-0.4, eyes_open=0.95, **k.aim((-0.9, 8.5, 0.0)))
    k.key(62, rot=55, frown=0.55, brow=1.0, ear_L=55, ear_R=55, tail_up=-0.8, head_rx=14, gaze_y=-18, gaze_x=0, head_rz=0, eyes_open=0.85)
    k.key(80, hips_z=-0.07, spine_rx=24, leg_L_x=32, leg_R_x=32, knee_L=62, knee_R=62, sh_L_x=45, sh_R_x=45, sh_L_y=-4, sh_R_y=-4, el_L=30, el_R=30, head_rx=12)
    k.key(100, hips_z=-0.09, spine_rx=26, leg_L_x=36, leg_R_x=36, knee_L=70, knee_R=70, sh_L_x=50, sh_R_x=50, sh_L_y=-8, sh_R_y=-8, el_L=26, el_R=26, head_rx=8, gaze_y=-5)
    k.key(130, hips_z=-0.09, spine_rx=27, head_rx=4, brow=1.0, gaze_y=-2, frown=0.6)
    blinks(k, [8, 57, 112])
    blinks(f, [20, 96])
    blinks(r, [12, 100])
    for a in (k, f, r):
        a.add_life()
    cam, tgt = common.camera("Cam", lens=32, fstop=3.2)
    common.cam_key(cam, tgt, 1, (-1.25, 7.0, 0.95), (0.35, 9.3, 0.75), lens=32)
    common.cam_key(cam, tgt, 50, (-0.95, 7.3, 0.92), (0.6, 9.3, 0.75), lens=34)
    common.cam_key(cam, tgt, 82, (-0.35, 7.55, 0.45), (-0.85, 8.6, 0.55), lens=38)
    common.cam_key(cam, tgt, 130, (-0.3, 7.7, 0.4), (-0.85, 8.6, 0.55), lens=42)
    return dict(cams=[cam])


# =================================================================== SHOT 3
def _rain_emitter(name, center, size, hole=None, hole_r=0.0, frames=(1, 140), height=4.0, count=4000, end=None):
    import bmesh
    import geo
    bm = bmesh.new()
    n = 24
    for i in range(n):
        for j in range(n):
            x0 = center[0] - size[0] / 2 + size[0] * i / n
            y0 = center[1] - size[1] / 2 + size[1] * j / n
            x1, y1 = x0 + size[0] / n, y0 + size[1] / n
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            inside = hole is not None and math.hypot(cx - hole[0], cy - hole[1]) < hole_r
            if hole is not None and hole_r < 0:
                inside = not (math.hypot(cx - hole[0], cy - hole[1]) < -hole_r)
            if inside:
                continue
            vs = [bm.verts.new((x0, y0, height)), bm.verts.new((x1, y0, height)), bm.verts.new((x1, y1, height)), bm.verts.new((x0, y1, height))]
            bm.faces.new(vs)
    ob = geo._mesh_obj(name, bm, None, smooth=False)
    ob.hide_render = False
    ps = ob.modifiers.new("rain", "PARTICLE_SYSTEM").particle_system
    st = ps.settings
    st.count = count
    st.frame_start = frames[0] - 30
    st.frame_end = end if end is not None else frames[1]
    st.lifetime = 30
    st.emit_from = "FACE"
    st.normal_factor = 0.0
    st.object_align_factor = (0, 0, -7.0)
    st.render_type = "OBJECT"
    st.instance_object = bpy.data.objects["drop_proto"]
    st.particle_size = 1.0
    st.size_random = 0.5
    st.use_rotations = False
    st.physics_type = "NEWTON"
    ob.show_instancer_for_render = False
    return ob


def shot3():
    import geo, mats
    sun, _ = set_light("rain", (60, 0, -15))
    fill_light((4.3, 8.5, 2.5), (4.4, 11.5, 0.8), 160, "#a9bdd6")
    E = envmod.Env(wet=True, garden=False)
    k = Actor("ryzhik", loc=(4.62, 11.5), rot=0)
    p = Actor("puppy", loc=(2.7, 10.3), rot=-130)
    k.bag_mode(1, "back")
    # kitten alone, hugging himself, ears down, looking down
    k.key(1, smile=0.0, frown=0.45, brow=0.9, ear_L=50, ear_R=50, tail_up=-0.8, head_rx=18, gaze_y=-12,
          sh_L_x=55, sh_R_x=55, sh_L_y=-30, sh_R_y=-30, el_L=95, el_R=95, eyes_open=0.85, spine_rx=6)
    k.key(30, head_rx=20, head_ry=4)
    # puppy walks in holding the closed umbrella
    p.key(1, smile=0.4, brow=0.2, sh_R_x=35, el_R=60, sh_R_y=-8, tail_up=0.2, **p.aim((4.62, 11.5, 0.9)))
    p.walk(1, 38, (3.92, 11.22), step=9, stride=20, arm=12)
    p.key(42, rot=72, smile=0.6, brow=0.35, **p.aim((4.62, 11.5, 0.9)))
    # raises & opens umbrella
    p.key(52, sh_R_x=125, sh_R_y=-25, el_R=35, sh_L_x=10)
    p.key(62, sh_R_x=135, sh_R_y=-30, el_R=30, smile=0.85, tail_up=0.5)
    p.wag(66, 126, period=6, amp=0.8)
    p.key(130, sh_R_x=135, sh_R_y=-30, el_R=30, smile=0.9, eyes_open=0.9, **p.aim((4.62, 11.5, 0.95)))
    U = props.Umbrella()
    con = U.root.constraints.new("COPY_LOCATION")
    con.target = p.j["hand_R"]
    # closed: carried like a cane (tip down); open: held straight up over both
    U.key(1, (0, 0, 0), (math.radians(180), 0, 0), 0.0)
    U.key(42, (0, 0, 0), (math.radians(180), 0, 0), 0.0)
    U.key(50, (0, 0, 0), (math.radians(10), math.radians(8), 0), 0.0)
    U.key(55, (0, 0, 0), (math.radians(5), math.radians(6), 0), 0.15)
    U.key(60, (0, 0, 0), (0, math.radians(6), 0), 1.05)
    U.key(64, (0, 0, 0), (0, math.radians(6), 0), 0.97)
    U.key(68, (0, 0, 0), (0, math.radians(6), 0), 1.0)
    U.key(130, (0, 0, 0), (0, math.radians(6), 0), 1.0)
    # warm glow beneath the umbrella
    glow = common.point("UmbrellaGlow", (4.35, 11.2, 1.45), 0, 0.5, "#ffc64a", shadow=False)
    glow.data.energy = 0
    glow.data.keyframe_insert("energy", frame=50)
    glow.data.energy = 14
    glow.data.keyframe_insert("energy", frame=62)
    # kitten notices: rain stopped falling on him
    k.key(56, head_rx=16)
    k.key(64, head_rx=-14, gaze_y=22, eyes_open=1.18, brow=0.6, frown=0.0, mouth_open=0.25, ear_L=20, ear_R=20,
          sh_L_x=30, sh_R_x=30, el_L=60, el_R=60)
    k.key(76, rot=-12, head_rz=-35, head_rx=-6, gaze_x=-15, gaze_y=6, mouth_open=0.1, brow=0.45)
    k.key(92, smile=0.7, mouth_open=0.0, brow=0.25, ear_L=4, ear_R=4, tail_up=0.3, eyes_open=1.0, sh_L_x=10, sh_R_x=10, el_L=20, el_R=20, sh_L_y=6, sh_R_y=6)
    k.key(130, smile=0.95, head_rz=-32, head_ry=-6, tail_up=0.5, eyes_open=0.95)
    blinks(k, [22, 84, 112])
    blinks(p, [30, 90])
    k.add_life()
    p.add_life()
    # rain
    dropm = mats.basic("raindrop", hexc("#dfeaf5"), rough=0.05, alpha=0.5, emission=hexc("#d5e3f0"), emit_strength=0.6)
    geo.cylinder("drop_proto", (0, 0, -60), 0.005, 0.24, dropm, seg=6)
    hole = (4.32, 11.3)
    _rain_emitter("rain_main", (4.3, 10.6), (7.0, 5.0), hole, 0.75, (1, 140), 4.0, 9000)
    _rain_emitter("rain_hole", (4.3, 10.6), (7.0, 5.0), hole, -0.75, (1, 140), 4.0, 350, end=48)
    # puddle ripples: animated noise bump on the puddle material
    m = bpy.data.materials.get("puddle")
    if m:
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.inputs["Scale"].default_value = 18
        nt.links.new(mp.outputs["Vector"], v.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.25
        nt.links.new(v.outputs["Distance"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        mp.inputs["Location"].default_value = (0, 0, 0)
        mp.inputs["Location"].keyframe_insert("default_value", frame=1)
        mp.inputs["Location"].default_value = (0, 0, 6)
        mp.inputs["Location"].keyframe_insert("default_value", frame=140)
    cam, tgt = common.camera("Cam", lens=40, fstop=2.8)
    common.cam_key(cam, tgt, 1, (5.15, 9.3, 0.95), (4.35, 11.3, 0.85), lens=34)
    common.cam_key(cam, tgt, 60, (5.1, 9.45, 0.95), (4.35, 11.35, 0.95), lens=36)
    common.cam_key(cam, tgt, 132, (5.0, 9.75, 0.95), (4.38, 11.38, 0.95), lens=42)
    return dict(cams=[cam], ssr=True)


# ============================================================ garden shots
def _group_garden(E, positions):
    acts = {}
    for cid, (x, y, rot) in positions.items():
        acts[cid] = Actor(cid, loc=(x, y), rot=rot)
    return acts


def shot4():
    sun, _ = set_light("windy", (52, 0, 160))
    fill_light((3, -2, 3), (0, -7, 0.8), 160, "#d6e2f2")
    E = envmod.Env(wet=True)
    E.sway_trees(1, 130, 2.2, period=14)
    E.flying_leaves(30, (1, 120), area=((-4, 3), (-10, -3)), seed=4, wind=(3.5, 0.8))
    A = _group_garden(E, {"ryzhik": (-0.35, -10.6, 180), "puppy": (0.35, -10.9, 180), "fox": (-0.65, -11.9, 180),
                          "raccoon": (0.3, -12.1, 180), "rabbit": (1.55, -5.55, 170)})
    k, p, f, r, b = A["ryzhik"], A["puppy"], A["fox"], A["raccoon"], A["rabbit"]
    k.bag_mode(1, "back")
    b.key(1, head_rx=25, gaze_y=-12, smile=0.6, spine_rx=15, ear_L=-5, ear_R=-5, sh_L_x=40, el_L=60)
    b.key(30, head_rx=28, head_rz=10, smile=0.7)
    for a, to in ((k, (-0.35, -8.3)), (p, (0.35, -8.6)), (f, (-0.65, -9.5)), (r, (0.3, -9.75))):
        a.key(1, smile=0.45)
        a.walk(1, 46, to, step=9, stride=20)
    # gust & creak: everyone looks up at the tree
    look = (-1.8, -6.2, 3.2)
    for a, d in ((k, 0), (p, 2), (f, 3), (r, 4)):
        a.key(50 + d, smile=0.1, eyes_open=1.15, brow=0.6, ear_L=-5, ear_R=-5, **a.aim(look))
    b.key(48, spine_rx=0, head_rx=0, sh_L_x=0, el_L=10)
    b.key(54, eyes_open=1.2, brow=0.6, smile=0.0, ear_L=-12, ear_R=-12, **b.aim(look))
    # impact at 61: jump & step back
    b.key(61, lift=0.0, rot=170)
    b.key(65, lift=0.13, rot=40, mouth_open=0.5, eyes_open=1.3, brow=1.0, frown=0.3, sh_L_x=110, sh_R_x=110, el_L=40, el_R=40, ear_L=0, ear_R=0)
    b.key(71, lift=0.0, rot=20, x=1.6, y=-5.38)
    b.key(80, rot=10, sh_L_x=60, sh_R_x=60, sh_L_y=-20, sh_R_y=-20, el_L=110, el_R=110, mouth_open=0.15, hips_z=-0.04, spine_rx=10, ear_L=40, ear_R=40, **b.aim((0.0, -7.0, 0.6)))
    for fr in range(84, 122, 4):
        b.key_only(fr, spine_ry=2.0 if fr % 8 == 0 else -2.0)
    b.key(124, eyes_open=1.15, brow=1.0)
    for a, back, d in ((k, 0.45, 0), (p, 0.5, 1), (f, 0.75, 2), (r, 0.7, 3)):
        a.key(61 + d, eyes_open=1.3, brow=1.0, mouth_open=0.45, smile=0.0, frown=0.3, sh_L_x=70, sh_R_x=70, el_L=70, el_R=70,
              sh_L_y=-15, sh_R_y=-15, ear_L=40, ear_R=40, tail_up=-0.6, head_rx=-8)
        a.walk(63 + d, 78 + d, (a.state["x"], a.state["y"] - back), step=5, stride=16, arm=0, face=180)
        a.key(90 + d, mouth_open=0.1, sh_L_x=30, sh_R_x=30, el_L=40, el_R=40, **a.aim((1.55, -5.5, 0.6)))
        a.key(124, mouth_open=0.05)
    # fox and raccoon cling together
    f.key(96, rot=150, sh_L_x=60, sh_L_y=-30, el_L=60)
    r.key(98, rot=205, sh_R_x=60, sh_R_y=-30, el_R=60)
    for a, bl in ((k, [20, 100]), (p, [26, 108]), (f, [14, 104]), (r, [34, 110]), (b, [18, 112])):
        blinks(a, bl)
        a.add_life()
    # branch: attached, creaks, breaks, falls, bounces, settles
    br = E.objs["branch"]
    att_loc, att_rot = (-2.45, -6.15, 3.05), (0, math.radians(-26), math.radians(4))
    key_obj(br, 1, att_loc, att_rot)
    key_obj(br, 30, att_loc, att_rot)
    for fr, j in ((34, 1.5), (38, -1.2), (42, 1.8), (45, -1.0)):
        key_obj(br, fr, att_loc, (math.radians(j * 0.6), math.radians(-26 + j), math.radians(4)))
    key_obj(br, 48, att_loc, (0, math.radians(-20), math.radians(4)))
    key_obj(br, 52, (-2.42, -6.15, 2.95), (math.radians(4), math.radians(-6), math.radians(2)))
    key_interp(br, "location", 52, "QUAD", "EASE_IN")
    key_interp(br, "rotation_euler", 52, "QUAD", "EASE_IN")
    key_obj(br, 61, (-2.3, -6.15, 0.15), (0, math.radians(1.5), 0))
    key_obj(br, 65, (-2.3, -6.15, 0.24), (0, math.radians(-1.8), 0))
    key_obj(br, 69, (-2.3, -6.15, 0.15), (0, math.radians(0.3), 0))
    key_obj(br, 74, (-2.3, -6.15, 0.15), (0, 0, 0))
    cam, tgt = common.camera("Cam", lens=26, fstop=6.0)
    common.cam_key(cam, tgt, 1, (-1.9, -11.6, 1.6), (0.5, -7.6, 0.7), lens=28)
    common.cam_key(cam, tgt, 46, (-1.95, -11.2, 1.7), (0.1, -6.9, 1.5), lens=26)
    common.cam_key(cam, tgt, 64, (-1.6, -10.6, 2.0), (1.0, -6.0, 0.55), lens=32)
    common.cam_key(cam, tgt, 120, (-1.3, -10.0, 1.95), (1.25, -5.8, 0.5), lens=36)
    cam_shake(cam, 60, 74, 0.05)
    return dict(cams=[cam])


def shot5():
    sun, _ = set_light("windy", (50, 0, 140))
    fill_light((0, -6.5, 2.0), (-0.3, -8, 0.9), 150, "#d6e2f2")
    E = envmod.Env(wet=True)
    E.sway_trees(1, 130, 1.5, period=16)
    E.flying_leaves(16, (1, 120), area=((-3, 2), (-9, -6)), seed=8, wind=(3.0, 0.6))
    branch_rest(E, 1)
    k = Actor("ryzhik", loc=(-0.35, -7.9), rot=180)
    b = Actor("rabbit", loc=(1.6, -5.38), rot=10)
    p = Actor("puppy", loc=(-1.0, -8.35), rot=170)
    k.bag_mode(1, "back")
    rabbit = (1.6, -5.4, 0.6)
    board_end = (1.02, -9.45, 0.05)
    k.key(1, eyes_open=1.25, brow=1.0, frown=0.35, smile=0.0, ear_L=40, ear_R=40, tail_up=-0.6, mouth_open=0.15,
          sh_L_x=30, sh_R_x=30, el_L=40, el_R=40, head_rx=-4, gaze_y=2)
    k.key(14, eyes_open=1.2, gaze_x=-3)
    k.key(24, **k.aim(rabbit, head=0.35))
    k.key(36, **k.aim(rabbit, head=0.4), brow=0.9)
    k.key(46, **k.aim(board_end, head=0.45, limit=45), eyes_open=1.1)
    k.key(56, head_rz=0, head_rx=-2, gaze_x=0, gaze_y=0, brow=-0.7, eyes_open=0.88, frown=0.15, mouth_open=0.0, ear_L=-8, ear_R=-8, tail_up=0.4, brow_h=-0.6)
    k.key(64, sh_L_x=-20, sh_R_x=-20, sh_L_y=40, sh_R_y=40, el_L=90, el_R=90)
    k.bag_mode(66, "none")
    k.key(70, sh_L_x=0, sh_R_x=0, sh_L_y=8, sh_R_y=8, el_L=15, el_R=15)
    k.walk(72, 104, (0.95, -9.2), step=6, stride=34, run=True)
    k.key(112, rot=165, hips_z=-0.05, spine_rx=40, sh_L_x=70, sh_R_x=70, el_L=20, el_R=20, head_rx=-25, gaze_y=12, knee_L=40, knee_R=40, leg_L_x=25, leg_R_x=25)
    k.key(122, spine_rx=44, hips_z=-0.06)
    # dropped backpack
    import geo
    bag = geo.empty("dropped_bag", (-0.35, -7.75, 0.62))
    k._bag(bag, "ryzhik_bagdrop")
    bag.scale = (0.001, 0.001, 0.001)
    bag.keyframe_insert("scale", frame=65)
    bag.scale = (1, 1, 1)
    key_obj(bag, 66, (-0.35, -7.72, 0.62), (0, 0, 0), (1, 1, 1))
    key_obj(bag, 72, (-0.62, -7.75, 0.13), (math.radians(80), 0, math.radians(30)))
    key_interp(bag, "location", 66, "QUAD", "EASE_IN")
    key_obj(bag, 76, (-0.68, -7.78, 0.12), (math.radians(90), 0, math.radians(35)))
    # rabbit trembling in the nook
    b.key(1, eyes_open=1.2, brow=1.0, frown=0.35, sh_L_x=60, sh_R_x=60, sh_L_y=-20, sh_R_y=-20, el_L=110, el_R=110, ear_L=40, ear_R=40, hips_z=-0.04, **b.aim((-0.35, -7.9, 0.9)))
    for fr in range(4, 122, 4):
        b.key_only(fr, spine_ry=2.0 if fr % 8 == 0 else -2.0)
    p.key(1, eyes_open=1.2, brow=1.0, frown=0.3, ear_L=40, ear_R=40, **p.aim(rabbit))
    p.key(80, **p.aim((0.6, -9.0, 0.3)), brow=0.6)
    blinks(k, [10, 60, 117])
    for a in (k, b, p):
        a.add_life()
    cam, tgt = common.camera("Cam", lens=70, fstop=2.4)
    common.cam_key(cam, tgt, 1, (-0.33, -6.75, 0.95), (-0.35, -7.9, 0.88), lens=62)
    common.cam_key(cam, tgt, 56, (-0.32, -6.85, 0.93), (-0.35, -7.9, 0.86), lens=60)
    common.cam_key(cam, tgt, 70, (0.2, -7.0, 0.8), (-0.3, -8.0, 0.7), lens=40)
    common.cam_key(cam, tgt, 88, (1.0, -7.75, 0.6), (0.35, -8.6, 0.5), lens=30)
    common.cam_key(cam, tgt, 106, (1.75, -8.55, 0.55), (0.95, -9.3, 0.4), lens=32)
    common.cam_key(cam, tgt, 122, (1.8, -8.65, 0.5), (1.0, -9.35, 0.3), lens=34)
    return dict(cams=[cam])


def shot6():
    sun, _ = set_light("windy", (52, 0, 150))
    fill_light((3.5, -9, 2.5), (1.3, -6.8, 0.5), 160, "#d6e2f2")
    E = envmod.Env(wet=True)
    E.sway_trees(1, 130, 1.2, period=18)
    k = Actor("ryzhik", loc=(1.05, -9.75), rot=170)
    p = Actor("puppy", loc=(0.65, -7.0), rot=170)
    b = Actor("rabbit", loc=(1.6, -5.38), rot=10)
    k.bag_mode(1, "none")
    mud = k.add_mud("L", 6, seed=2)
    bp = E.objs["board"]
    # board: drag, lift over the rock, press down, release
    key_obj(bp, 1, (0.75, -8.7, 0.03), (0, 0, 0.35))
    key_obj(bp, 26, (1.3, -7.6, 0.05), (0, 0, 0.05))
    c, r = board_on_rock(30)
    key_obj(bp, 38, (1.35, -7.15, 0.2), (math.radians(-12), 0, 0))
    key_obj(bp, 46, c, r)
    for fr, a in ((54, 26), (66, 4), (76, -8), (98, -9), (104, 6), (108, 12), (112, 9), (122, 10)):
        c, r = board_on_rock(a)
        key_obj(bp, fr, c, r)
    # kitten pushes the board then presses its end down
    k.key(1, spine_rx=40, hips_z=-0.05, sh_L_x=70, sh_R_x=70, el_L=20, el_R=20, brow=-0.7, eyes_open=0.85, frown=0.2, ear_L=-6, ear_R=-6, knee_L=30, knee_R=30, leg_L_x=20, leg_R_x=20)
    k.walk(4, 30, (1.3, -8.55), step=7, stride=26, arm=0, face=180, extra=dict(spine_rx=38, sh_L_x=75, sh_R_x=75, el_L=25, el_R=25))
    k.key(38, x=1.35, y=-8.15, rot=180, spine_rx=10, hips_z=0.0, sh_L_x=110, sh_R_x=110, el_L=30, el_R=30, knee_L=0, knee_R=0, leg_L_x=0, leg_R_x=0, head_rx=-15)
    k.key(46, y=-8.05, sh_L_x=150, sh_R_x=150, el_L=25, el_R=25, sh_L_y=-6, sh_R_y=-6, head_rx=-20, gaze_y=10)
    k.key(54, sh_L_x=140, sh_R_x=140)
    k.key(66, spine_rx=25, sh_L_x=95, sh_R_x=95, el_L=15, el_R=15, eyes_open=0.35, frown=0.6, brow=-1.0, head_rx=0, gaze_y=0, mouth_open=0.2)
    k.key(76, spine_rx=42, hips_z=-0.06, knee_L=35, knee_R=35, leg_L_x=25, leg_R_x=25, sh_L_x=70, sh_R_x=70, el_L=10, el_R=10, eyes_open=0.25, head_rx=-12)
    for fr in range(80, 98, 4):
        k.key_only(fr, spine_ry=1.5 if fr % 8 == 0 else -1.5, hips_z=-0.065)
    k.key(98, spine_rx=44, eyes_open=0.3)
    k.key(106, spine_rx=10, hips_z=0.0, knee_L=0, knee_R=0, leg_L_x=0, leg_R_x=0, sh_L_x=20, sh_R_x=20, el_L=20, el_R=20, eyes_open=1.0, frown=0.0, brow=0.2, mouth_open=0.35, head_rx=-5)
    k.walk(108, 118, (1.35, -8.4), step=5, stride=14, face=180)
    k.key(122, mouth_open=0.3, smile=0.4, **k.aim((1.9, -7.4, 0.6)))
    # puppy lifts the light end of the branch with his paws
    p.key(1, eyes_open=1.1, brow=0.6, **p.aim((1.3, -7.8, 0.4)))
    p.walk(20, 44, (0.72, -6.42), step=8, stride=20, face=180)
    p.key(50, spine_rx=45, hips_z=-0.07, knee_L=40, knee_R=40, leg_L_x=30, leg_R_x=30, sh_L_x=75, sh_R_x=75, el_L=20, el_R=20, brow=-0.6, eyes_open=0.6, head_rx=-20)
    p.key(80, spine_rx=15, hips_z=-0.02, knee_L=10, knee_R=10, leg_L_x=8, leg_R_x=8, sh_L_x=105, sh_R_x=105, el_L=30, el_R=30, eyes_open=0.35, frown=0.5, mouth_open=0.2)
    p.key(98, spine_rx=14)
    p.key(104, spine_rx=0, hips_z=0, knee_L=0, knee_R=0, leg_L_x=0, leg_R_x=0, sh_L_x=15, sh_R_x=15, el_L=15, el_R=15, eyes_open=1.0, frown=0.0, mouth_open=0.3, smile=0.4)
    p.walk(106, 118, (0.65, -6.95), step=6, stride=14, face=180)
    p.key(122, smile=0.6, **p.aim((1.9, -7.4, 0.6)))
    # branch lifts
    branch_rest(E, 1)
    branch_rest(E, 56)
    branch_rest(E, 70, 4.0)
    branch_rest(E, 80, 6.5)
    branch_rest(E, 98, 6.8)
    branch_rest(E, 104, -0.4)
    branch_rest(E, 107, 0.4)
    branch_rest(E, 110, 0.0)
    # rabbit crawls out under the lifted branch
    b.key(1, eyes_open=1.2, brow=1.0, frown=0.3, sh_L_x=60, sh_R_x=60, sh_L_y=-20, sh_R_y=-20, el_L=110, el_R=110, ear_L=40, ear_R=40, hips_z=-0.04, **b.aim((1.3, -7.6, 0.5)))
    for fr in range(4, 66, 4):
        b.key_only(fr, spine_ry=2.0 if fr % 8 == 0 else -2.0)
    b.key(70, rot=-170 + 360, spine_rx=10, ear_L=60, ear_R=60)
    b.key(74, rot=180 + 10 - 360 + 360, brow=0.8)
    b.key(76, rot=-5, hips_z=-0.12, spine_rx=55, knee_L=60, knee_R=60, leg_L_x=45, leg_R_x=45, sh_L_x=80, sh_R_x=80, el_L=20, el_R=20, ear_L=80, ear_R=80, head_rx=-30)
    b.key(92, x=1.72, y=-6.45)
    b.key(98, x=1.85, y=-6.85, hips_z=0, spine_rx=10, knee_L=0, knee_R=0, leg_L_x=0, leg_R_x=0, sh_L_x=10, sh_R_x=10, el_L=10, el_R=10, ear_L=0, ear_R=0, head_rx=0)
    b.walk(98, 112, (1.95, -7.45), step=5, stride=22, run=True)
    b.key(122, eyes_open=1.0, brow=0.3, frown=0.0, smile=0.6, mouth_open=0.3, **b.aim((1.35, -8.4, 0.9)))
    for a, bl in ((k, [20, 112]), (p, [30, 115]), (b, [40])):
        blinks(a, bl)
        a.add_life()
    cam, tgt = common.camera("Cam", lens=28, fstop=4.0)
    common.cam_key(cam, tgt, 1, (-0.95, -9.0, 1.0), (1.15, -8.4, 0.35), lens=23)
    common.cam_key(cam, tgt, 46, (-0.95, -8.6, 1.0), (1.45, -7.15, 0.4), lens=22)
    common.cam_key(cam, tgt, 122, (-0.9, -8.5, 0.95), (1.5, -7.1, 0.4), lens=23)
    return dict(cams=[cam])


def shot7():
    sun, _ = set_light("windy", (50, 0, 200))
    fill_light((0.0, -10.5, 2.0), (1.3, -8, 0.8), 160, "#ffe6c8")
    sun.data.energy = 1.8
    sun.data.keyframe_insert("energy", frame=20)
    sun.data.energy = 4.0
    sun.data.keyframe_insert("energy", frame=100)
    sun.data.color = hexc("#f1efe6")[:3]
    sun.data.keyframe_insert("color", frame=20)
    sun.data.color = hexc("#ffd59c")[:3]
    sun.data.keyframe_insert("color", frame=100)
    E = envmod.Env(wet=True)
    E.sway_trees(1, 130, 0.5)
    branch_rest(E, 1)
    c, r = board_on_rock(10)
    key_obj(E.objs["board"], 1, c, r)
    k = Actor("ryzhik", loc=(1.35, -8.05), rot=-19)
    b = Actor("rabbit", loc=(1.95, -7.4), rot=-140)
    p = Actor("puppy", loc=(0.72, -7.75), rot=-30)
    f = Actor("fox", loc=(0.1, -6.95), rot=-110)
    r = Actor("raccoon", loc=(-0.25, -7.3), rot=-105)
    k.bag_mode(1, "none")
    k.add_mud("L", 6, seed=2)
    k.key(1, smile=0.3, mouth_open=0.2, brow=0.2, **k.aim((1.95, -7.4, 0.7)))
    b.key(1, smile=0.7, brow=0.2, eyes_open=1.1)
    b.walk(4, 18, (1.66, -8.28), step=5, stride=24, run=True)
    b.key(22, rot=-121, sh_L_x=80, sh_R_x=80, sh_L_y=-30, sh_R_y=-30, el_L=60, el_R=60, smile=1.0, eyes_open=0.4, head_ry=-12, head_rz=-10, ear_L=-10, ear_R=-10, spine_rx=10)
    b.key(100, sh_L_x=82, sh_R_x=82, eyes_open=0.35, smile=1.0)
    b.key(128, sh_L_x=70, sh_R_x=70, eyes_open=0.8, head_rz=-30)
    k.key(18, eyes_open=1.2, brow=0.6, mouth_open=0.3, smile=0.2)
    k.key(28, sh_L_x=60, sh_L_y=-20, el_L=60, sh_R_x=40, sh_R_y=-10, el_R=50, eyes_open=0.6, smile=0.85, mouth_open=0.0, brow=0.25, head_ry=10, head_rz=15, ear_L=0, ear_R=0, tail_up=0.6)
    k.key(80, eyes_open=0.5, smile=0.9)
    k.key(96, sh_L_x=40, el_L=50, sh_R_x=10, el_R=15, eyes_open=1.0, head_ry=3, smile=0.85, **k.aim((0.6, -10.6, 1.0), head=0.5))
    k.key(128, smile=0.9, head_ry=-4)
    p.key(1, smile=0.7, tail_up=0.6, brow=0.2, **p.aim((1.35, -8.05, 0.8)))
    p.key(30, spine_rx=-8, head_rx=-10, smile=1.0, eyes_open=0.6, sh_L_x=-10, sh_R_x=-10, sh_L_y=20, sh_R_y=20, el_L=100, el_R=100)
    p.wag(30, 122, period=5)
    # the two who laughed: surprise -> guilty looks -> ears down
    for a in (f, r):
        a.key(1, eyes_open=1.15, brow=0.5, smile=0.0, mouth_open=0.2, **a.aim((1.35, -8.05, 0.9)))
        a.key(40, eyes_open=1.2, mouth_open=0.3, brow=0.6)
    f.key(62, mouth_open=0.0, **f.aim((-0.25, -7.3, 0.95)))
    r.key(64, mouth_open=0.0, **r.aim((0.1, -6.95, 0.95)))
    for a in (f, r):
        a.key(80, brow=1.0, frown=0.5, ear_L=55, ear_R=55, tail_up=-0.7, eyes_open=0.9)
        a.key(96, head_rx=22, gaze_y=-15, gaze_x=0, head_rz=0, sh_L_x=20, sh_R_x=20, sh_L_y=-15, sh_R_y=-15, el_L=60, el_R=60)
        a.key(128, head_rx=24)
    for a, bl in ((k, [12, 60, 110]), (p, [40]), (f, [20, 88]), (r, [24, 92]), (b, [])):
        blinks(a, bl)
        a.add_life()
    cam, tgt = common.camera("Cam", lens=30, fstop=3.2)
    common.cam_key(cam, tgt, 1, (0.85, -10.55, 1.05), (0.75, -7.7, 0.75), lens=30)
    common.cam_key(cam, tgt, 60, (0.95, -10.2, 1.0), (0.95, -7.8, 0.8), lens=32)
    common.cam_key(cam, tgt, 128, (1.1, -9.3, 0.95), (1.4, -8.0, 0.9), lens=46)
    return dict(cams=[cam])


def shot8():
    import geo
    sun, _ = set_light("golden", (68, 0, 210))
    fill_light((0.5, -10.5, 2.0), (1.3, -8, 0.6), 180, "#ffe0bc")
    E = envmod.Env(wet=True)
    E.sway_trees(1, 140, 0.4)
    branch_rest(E, 1)
    c, r_ = board_on_rock(10)
    key_obj(E.objs["board"], 1, c, r_)
    k = Actor("ryzhik", loc=(1.35, -8.05), rot=-19)
    f = Actor("fox", loc=(0.1, -8.25), rot=100)
    r = Actor("raccoon", loc=(2.4, -8.6), rot=-110)
    p = Actor("puppy", loc=(0.95, -7.45), rot=-25)
    b = Actor("rabbit", loc=(1.85, -7.55), rot=-30)
    k.bag_mode(1, "none")
    mud = k.add_mud("L", 6, seed=2)
    k.key(1, smile=0.6, brow=0.2)
    p.key(1, smile=0.8, tail_up=0.5, **p.aim((1.35, -8.05, 0.8)))
    b.key(1, smile=0.8, **b.aim((1.35, -8.05, 0.8)))
    # fox comes closer and offers a paw
    f.key(1, ear_L=40, ear_R=40, brow=0.9, frown=0.3, smile=0.0, head_rx=12)
    f.walk(2, 20, (0.66, -8.28), step=8, stride=16, face=95)
    f.key(26, brow=0.8, **f.aim((1.35, -8.05, 0.95)))
    f.key(36, sh_R_x=62, sh_R_y=-12, el_R=20, smile=0.3, ear_L=25, ear_R=25)
    # raccoon kneels and cleans the boot with a cloth
    r.key(1, ear_L=40, ear_R=40, brow=0.9, frown=0.3, smile=0.0)
    r.walk(2, 18, (1.88, -8.2), step=8, stride=16)
    r.key(26, rot=-92, hips_z=-0.16, leg_L_x=75, leg_R_x=75, knee_L=110, knee_R=110, spine_rx=35, sh_R_x=70, sh_R_y=-15, el_R=25, sh_L_x=45, el_L=30, head_rx=15, gaze_y=-15)
    cl = props.cloth("cloth")
    base = Vector((1.5, -8.12, 0.12))
    cl.location = (1.9, -8.6, 0.35)
    cl.keyframe_insert("location", frame=18)
    for i, fr in enumerate(range(28, 92, 6)):
        off = 0.05 if i % 2 == 0 else -0.05
        cl.location = base + Vector((off, off * 0.5, 0.02 * (i % 2)))
        cl.rotation_euler = (0.3, 0.2 * (1 if i % 2 else -1), 0.5)
        cl.keyframe_insert("location", frame=fr)
        cl.keyframe_insert("rotation_euler", frame=fr)
        r.key_only(fr, sh_R_x=70 + (6 if i % 2 else -6), sh_R_z=8 if i % 2 else -8, hips_z=-0.16, leg_L_x=75, leg_R_x=75, knee_L=110, knee_R=110, spine_rx=35)
    for i, m in enumerate(mud):
        t0 = 30 + i * 9
        m.scale = m.scale.copy()
        sc = m.scale.copy()
        m.keyframe_insert("scale", frame=t0)
        m.scale = (0.001, 0.001, 0.001)
        m.keyframe_insert("scale", frame=t0 + 8)
    r.key(92, sh_R_x=50, sh_R_z=0, smile=0.4, brow=0.5, frown=0.0, head_rx=-10, **{kk: v for kk, v in r.aim((1.35, -8.05, 0.95)).items() if kk in ("gaze_x", "gaze_y")})
    cl.location = (1.68, -8.42, 0.4)
    cl.keyframe_insert("location", frame=104)
    r.key(108, hips_z=0, leg_L_x=0, leg_R_x=0, knee_L=0, knee_R=0, spine_rx=0, sh_R_x=25, el_R=60, ear_L=5, ear_R=5, smile=0.7, **r.aim((1.35, -8.05, 0.95)))
    r.key(132, smile=0.8, tail_up=0.3)
    # kitten: surprised -> accepts with a kind smile -> paw shake
    k.key(14, eyes_open=1.2, brow=0.7, mouth_open=0.2, smile=0.2, **k.aim((1.7, -8.5, 0.3)))
    k.key(32, **k.aim((0.66, -8.28, 0.95)), mouth_open=0.1)
    k.key(48, smile=0.9, mouth_open=0.0, brow=0.2, eyes_open=0.85, tail_up=0.5)
    k.key(60, sh_R_x=60, sh_R_y=-5, el_R=25)
    f.key(60, sh_R_x=60, smile=0.5)
    for i, fr in enumerate((66, 72, 78)):
        dz = 6 if i % 2 == 0 else -6
        k.key_only(fr, sh_R_x=60 + dz)
        f.key_only(fr, sh_R_x=60 + dz)
    k.key(86, sh_R_x=58, smile=1.0)
    f.key(86, sh_R_x=58, smile=0.9, ear_L=0, ear_R=0, brow=0.2, frown=0.0, tail_up=0.4)
    k.key(100, sh_R_x=5, el_R=15, **k.aim((1.7, -8.5, 0.8)))
    f.key(100, sh_R_x=5, el_R=15)
    k.key(132, smile=1.0, eyes_open=0.8, **k.aim((0.66, -8.28, 0.95)))
    p.wag(40, 126, period=6)
    b.key(50, sh_L_x=70, sh_R_x=70, sh_L_y=-20, sh_R_y=-20, el_L=70, el_R=70, smile=1.0, eyes_open=0.6)
    for i, fr in enumerate(range(54, 90, 4)):
        b.key_only(fr, sh_L_y=-10 if i % 2 else -28, sh_R_y=-10 if i % 2 else -28)
    b.key(94, sh_L_x=10, sh_R_x=10, sh_L_y=8, sh_R_y=8, el_L=15, el_R=15)
    for a, bl in ((k, [8, 56, 112]), (p, [30, 98]), (f, [44, 110]), (r, [50, 118]), (b, [20, 100])):
        blinks(a, bl)
        a.add_life()
    cam, tgt = common.camera("Cam", lens=36, fstop=3.2)
    common.cam_key(cam, tgt, 1, (1.2, -10.25, 0.95), (1.2, -8.1, 0.6), lens=34)
    common.cam_key(cam, tgt, 70, (1.2, -10.1, 0.95), (1.22, -8.1, 0.62), lens=36)
    common.cam_key(cam, tgt, 132, (1.22, -9.9, 0.95), (1.3, -8.05, 0.7), lens=40)
    return dict(cams=[cam])


def shot9():
    sun, _ = set_light("golden", (74, 0, 205))
    fill_light((0, -3, 2.5), (0, 1.5, 0.8), 200, "#ffe2c0")
    E = envmod.Env(wet=True, puddles=True)
    E.sway_trees(1, 130, 0.4)
    branch_rest(E, 1)
    c, r_ = board_on_rock(10)
    key_obj(E.objs["board"], 1, c, r_)
    pos = {"ryzhik": (0.0, 3.3), "puppy": (-0.58, 3.2), "rabbit": (0.58, 3.25), "fox": (-1.05, 3.8), "raccoon": (1.0, 3.85)}
    A = {cid: Actor(cid, loc=xy, rot=0) for cid, xy in pos.items()}
    k = A["ryzhik"]
    k.bag_mode(1, "back")
    for cid, a in A.items():
        a.key(1, smile=0.85, tail_up=0.4, brow=0.15)
        x, y = pos[cid]
        a.walk(1, 92 + (2 if cid in ("fox", "raccoon") else 0), (x, y - 2.6), step=10, stride=20)
    A["puppy"].wag(40, 120, period=6)
    def look(a, f0, f1, dx, dz=0.0, **extra):
        a.hold_only(f0, f1, head_rz=dx, gaze_x=dx * 0.4, gaze_y=dz, **extra)
    look(k, 1, 20, 0)
    look(k, 28, 42, -40, smile=0.95)
    look(k, 50, 64, 40, smile=1.0)
    look(k, 72, 86, 0, 4)
    look(A["puppy"], 32, 46, 35, smile=1.0)
    look(A["rabbit"], 54, 66, -35, smile=1.0)
    look(A["fox"], 68, 80, 25)
    look(A["raccoon"], 70, 82, -25)
    # final: Ryzhik looks at his friends and smiles; friends look back
    k.key(98, **k.aim((-0.58, 0.6, 0.95)), smile=1.0)
    k.key(108, **k.aim((0.58, 0.65, 0.9)), smile=1.0, eyes_open=0.75)
    k.key(120, head_rz=6, head_rx=-6, gaze_x=4, gaze_y=6, smile=1.0, eyes_open=0.8, head_ry=-6)
    A["puppy"].key(100, **A["puppy"].aim((0.0, 0.7, 0.95)), smile=1.0)
    A["rabbit"].key(102, **A["rabbit"].aim((0.0, 0.7, 0.95)), smile=1.0)
    A["fox"].key(104, smile=0.9)
    A["raccoon"].key(104, smile=0.9)
    for a, bl in ((k, [20, 86]), (A["puppy"], [44]), (A["rabbit"], [64]), (A["fox"], [30, 96]), (A["raccoon"], [50, 110])):
        blinks(a, bl)
        a.add_life()
    cam, tgt = common.camera("Cam", lens=40, fstop=4.0)
    common.cam_key(cam, tgt, 1, (0.1, -0.6, 0.95), (0.0, 3.4, 0.8), lens=36)
    common.cam_key(cam, tgt, 60, (0.12, -1.7, 1.15), (0.0, 2.6, 0.95), lens=36)
    common.cam_key(cam, tgt, 104, (0.15, -2.75, 1.55), (0.0, 2.0, 1.15), lens=36)
    common.cam_key(cam, tgt, 120, (0.15, -2.95, 1.62), (0.0, 1.95, 1.2), lens=36)
    return dict(cams=[cam])


SHOTS = {1: shot1, 2: shot2, 3: shot3, 4: shot4, 5: shot5, 6: shot6, 7: shot7, 8: shot8, 9: shot9}
