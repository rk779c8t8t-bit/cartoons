"""Choreography of the 9 scenes. Every frame is a pure function of (scene, t):
frames can be rendered in any order, resumed, or re-rendered individually."""
import math

import bpy
from mathutils import Vector

from . import core, world, characters
from .core import kf, seg, smooth, ease_out, ease_in, back_out, elastic_out, lerp, clamp, bounce_arc, rng
from .world import place, aim, FLOOR_Z

PI = math.pi


def run_cycle(t, freq=3.2, amp=0.9):
    ph = t * freq * 2 * PI
    s = math.sin(ph)
    return dict(legs=(amp * s, -amp * s), arm_l=(amp * 0.9 * s - 0.3, 0.35, 0), arm_r=(-amp * 0.9 * s - 0.3, -0.35, 0),
                elbow=(-1.0, -1.0)), abs(math.sin(ph)) * 0.025


def walk_cycle(t, freq=1.6, amp=0.45):
    ph = t * freq * 2 * PI
    s = math.sin(ph)
    return dict(legs=(amp * s, -amp * s), arm_l=(amp * 0.6 * s, 0.15, 0), arm_r=(-amp * 0.6 * s, -0.15, 0),
                elbow=(-0.3, -0.3)), abs(math.sin(ph)) * 0.012


def snake_spine(head, direction, t, length=1.0, lift=0.2, wiggle=0.06, n=14, ring=0.05, freq=7.0, speed=9.0, bounce=0.0):
    """Points from tail to head for a creature slithering with its head at `head`
    travelling along unit 2D `direction`."""
    d = Vector((direction[0], direction[1], 0)).normalized()
    side = Vector((-d.y, d.x, 0))
    pts = []
    for i in range(n):
        s = i / (n - 1)
        back = (1 - s) * length
        p = Vector(head) - d * back
        p += side * wiggle * math.sin(freq * s - speed * t) * (0.4 + 0.6 * (1 - s))
        z = ring + lift * smooth((s - 0.6) / 0.4) + bounce * max(0.0, math.sin(PI * 2 * s - t * 10)) * (1 - s)
        pts.append(Vector((p.x, p.y, Vector(head).z * 0 + z)))
    return pts


class Production:
    def __init__(self):
        core.reset()
        self.K = world.Kitchen()
        self.lights = world.lights_and_world()
        self.cam = world.camera()
        self.milo = characters.Cat(characters.MILO)
        self.mom = characters.Cat(characters.MOM)
        self.nd = world.Noodle(n=11, ring=0.055, thick=0.0135)
        self.leftover = world.Noodle(n=1, ring=0.0, thick=0.013, name="leftover")
        self.P = self.K.props

    # ------------------------------------------------------------------ helpers
    def reset_frame(self):
        P = self.P
        for k, v in P.items():
            items = v if isinstance(v, list) else [v]
            for o in items:
                if hasattr(o, "parent") and o.parent is not None and o.parent.name.startswith(("Milo", "Mom")):
                    o.parent = None
                    o.scale = (1, 1, 1)
        self.K.hide_all_props()
        self.nd.visible(False)
        self.leftover.visible(False)
        world._set_hide(self.mom.root, True)
        world._set_hide(self.milo.root, False)
        self.K.door_pivot.rotation_euler = (0, 0, 0)
        for o in self.P["tomatoes"]:
            o.scale = (1, 1, 1)

    def show_mom(self, v=True):
        world._set_hide(self.mom.root, not v)
        self.mom.mouth_open.hide_render = True if not v else self.mom.mouth_open.hide_render

    def hold(self, prop, cat, side, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
        world._set_hide(prop, False)
        prop.parent = cat.hand[side]
        prop.location = loc
        prop.rotation_euler = rot
        s = scale / cat.P["scale"]
        prop.scale = (s, s, s)

    def tomatoes(self, spots):
        for o, sp in zip(self.P["tomatoes"], spots):
            if sp is None:
                place(o, None)
            else:
                place(o, sp[0], rot=sp[1] if len(sp) > 1 else (0, 0, 0))

    def mess(self, floor=True):
        """flour + scattered props left from the chaos (scenes 6-9)"""
        P = self.P
        spots = [(-0.55, -0.1, 0.002), (-0.25, 0.25, 0.002), (0.6, 0.2, 0.002), (-0.9, -0.3, 0.002), (0.95, -0.25, 0.002)]
        for o, s in zip(P["patches"], spots):
            place(o, s, rot=(0, 0, s[0] * 3), scale=(0.2, 0.15, 0.006))
        if floor:
            for o, s in zip(P["patches"][5:], [(-0.6, -1.1, FLOOR_Z + 0.003), (0.4, 0.95, FLOOR_Z + 0.003), (-1.3, 1.1, FLOOR_Z + 0.003)]):
                place(o, s, rot=(0, 0, 1.0), scale=(0.45, 0.3, 0.01))
        self.tomatoes([((0.75, -0.35, 0.037), (1.4, 0, 0.3)), ((-0.7, 0.35, 0.037), (0.5, 1.2, 0)),
                       ((1.25, 0.1, 0.037), (0, 1.6, 0)), ((-1.05, -0.4, 0.037), (2.1, 0.4, 0)),
                       ((0.3, -1.3, FLOOR_Z + 0.037), (1.2, 0, 0)), None])
        place(P["bowl"], (-1.3, 0.25, 0.06), rot=(1.2, 0, 0.4))
        place(P["pot2"], (-1.0, 0.1, 0))
        place(P["lid"], (1.1, 0.35, 0.03), rot=(0.2, 0.1, 0))
        place(P["spoon"], (0.95, -0.15, 0.015), rot=(PI / 2, 0, 1.0))
        place(P["flourbag"], (-1.5, -0.2, 0.06), rot=(PI / 2 - 0.1, 0, 0.6))

    def camera_shots(self, t, shots):
        for (a, b, fn) in shots:
            if a <= t < b or (b == shots[-1][1] and t >= a):
                return fn(t - a, b - a)
        return shots[-1][2](t - shots[-1][0], shots[-1][1] - shots[-1][0])

    # ------------------------------------------------------------------ dispatch
    def frame(self, scene, t):
        self.reset_frame()
        getattr(self, f"s{scene}")(t)

    # ================================================================== SCENE 1
    def s1(self, t):
        P, m = self.P, self.milo
        place(P["stool"], (0, -0.95, FLOOR_Z))
        place(P["bowl"], (0.45, -0.35, 0))
        place(P["flourbag"], (-0.5, -0.25, 0), rot=(0, 0, 0.35))
        place(P["pot"], (-1.0, 0.0, 0))
        place(P["lid"], (-1.0, 0.0, 0.32))
        for e, p in zip(P["eggs"], [(0.78, -0.42, 0.036), (0.85, -0.34, 0.036), (0.74, -0.3, 0.036)]):
            place(e, p)
        self.tomatoes([None, ((0.2, -0.55, 0.037), (0, 0, 0.3)), ((0.28, -0.6, 0.037), (0, 0, 1)),
                       ((0.24, -0.49, 0.037), (0, 0, 2)), ((-0.25, -0.58, 0.037),), None])
        base = Vector((0, -0.95, FLOOR_Z + 0.79))
        # tomato flight: in the air from frame 0, caught at 1.9s
        tom = P["tomatoes"][0]
        catch = 1.9
        hand_pt = Vector((0.13, -1.06, base.z + 0.36))
        if t < catch:
            f = t / catch
            z = hand_pt.z + 0.1 + 0.62 * 4 * f * (1 - f) - 0.1 * f
            place(tom, (hand_pt.x + 0.04 * math.sin(f * 3), hand_pt.y - 0.05 * f, z), rot=(t * 7, t * 5, 0))
            tz = z
        else:
            self.hold(tom, m, 1, loc=(0, -0.01, -0.03))
            tz = hand_pt.z
        up = clamp((tz - (base.z + 0.34)) / 0.6)
        look_up = up if t < catch + 0.15 else kf(t, [(catch + 0.15, up), (2.3, 0.0)])
        wink = 1 - (seg(t, 2.4, 2.55) - seg(t, 2.75, 2.9))
        wave = seg(t, 3.0, 3.3) - seg(t, 3.85, 4.0)
        mp = dict(
            loc=base + Vector((0, 0, -0.02 * math.exp(-((t - catch) / 0.08) ** 2))),
            rz=kf(t, [(0, 0.15), (2.2, 0.0)]),
            squash=1 - 0.12 * math.exp(-((t - catch - 0.05) / 0.07) ** 2) + 0.04 * math.exp(-((t - 0.1) / 0.1) ** 2),
            head=(0.55 * look_up, 0.12 * math.sin(t * 2.0), 0.0),
            look=(0.0, 0.9 * look_up),
            eye_open=(1.0, wink),
            eye_big=1.0 + 0.08 * look_up,
            brow=0.6 * look_up + 0.5 * (1 - wink),
            smile=0.75 + 0.35 * seg(t, 2.0, 2.4),
            mouth=0.35 * math.exp(-((t - catch - 0.15) / 0.18) ** 2) + 0.25 * wave,
            arm_r=kf(t, [(0, (-2.7, -0.35, 0)), (0.35, (-2.3, -0.3, 0)), (1.3, (-1.75, -0.45, 0)),
                         (catch, (-1.6, -0.45, 0)), (2.2, (-1.3, -0.5, 0)), (2.6, (-1.4, -0.4, 0)), (4, (-1.35, -0.4, 0))]),
            arm_l=(lerp(-0.2, -0.4, wave), 0.25 + 2.3 * wave, 0.0),
            elbow=(-0.3 - 0.9 * wave * (0.5 + 0.5 * math.sin(t * 22)), kf(t, [(0, -0.1), (1.3, -0.9), (2.6, -1.4)])),
            legs=(0, 0), tail_wag=t * 4.0, tail_up=0.6, ears=0.3 * look_up,
            hat_tilt=0.12 * math.sin(t * 9) * math.exp(-max(0, t - catch) * 2) * (t > catch),
        )
        m.pose(**mp)
        # camera: fast push-in from a low wide shot (scale gag) to Milo's face
        f = ease_out(seg(t, 0, 1.8))
        loc = lerp((0.85, -2.6, -0.25), (0.16, -1.95, base.z + 0.4), f)
        tgt = lerp((0.0, -0.6, -0.05), (0.0, -0.95, base.z + 0.3), f)
        loc = Vector(loc) + Vector((-0.08 * seg(t, 1.8, 4), 0.06 * seg(t, 1.8, 4), 0.02 * seg(t, 1.8, 4)))
        aim(self.cam, loc, tgt, lens=lerp(24, 34, f), fstop=3.2)

    # ================================================================== SCENE 2
    def s2(self, t):
        P, m = self.P, self.milo
        mpos = Vector((-0.05, -0.2, 0))
        bowl = Vector((0.2, -0.32, 0))
        place(P["bowl"], bowl)
        place(P["batter"], (0, 0, 0.1))
        place(P["pot"], (-0.9, 0.25, 0))
        place(P["lid"], (-0.9, 0.25, 0.32))
        for e, p in zip(P["eggs"], [(0.48, -0.25, 0.036), (0.52, -0.16, 0.036), (0.42, -0.12, 0.036)]):
            place(e, p)
        self.tomatoes([((0.3, -0.62, 0.037),), ((0.4, -0.58, 0.037), (0, 0, 1)), ((0.35, -0.52, 0.037),), None, None, None])
        poof = 2.35
        # flour bag: on counter -> grabbed -> slips -> falls -> poof
        bag0 = Vector((-0.32, -0.15, 0))
        if t < 1.65:
            place(P["flourbag"], bag0, rot=(0, 0, 0.4))
        elif t < 2.05:
            self.hold(P["flourbag"], m, 0, loc=(0.02, -0.06, -0.12), rot=(0.3, 0, 0.2))
        else:
            f = seg(t, 2.05, poof)
            hp = Vector((-0.2, -0.32, 0.26))
            p = lerp(hp, (-0.12, -0.42, 0.06), ease_in(f))
            rot = (lerp(0.3, PI / 2 - 0.15, ease_in(f)), 0, 0.3 + f)
            place(P["flourbag"], p, rot=rot)
        stir = t < 1.5
        flour = smooth(seg(t, poof + 0.15, poof + 0.35)) * (1 - smooth(seg(t, 3.55, 3.95)))
        shake = seg(t, 3.45, 3.95)
        shake_rz = 0.5 * math.sin(shake * PI * 7) * math.sin(shake * PI) if 0 < shake < 1 else 0
        blink = 1 - (seg(t, 3.05, 3.12) - seg(t, 3.2, 3.27))
        surprised = smooth(seg(t, 2.0, 2.2))
        if stir:
            ph = t * 2 * PI * 2
            arm_r = (-1.25 + 0.15 * math.sin(ph), -0.55 + 0.25 * math.cos(ph), 0)
            el_r = -0.5
            self.hold(P["spoon"], m, 1, loc=(0, 0, -0.17), rot=(0.25 * math.sin(ph), 0.3 * math.cos(ph), 0))
            place(P["batter"], (0, 0, 0.1), rot=(0, 0, ph * 0.2))
        else:
            place(P["spoon"], (0.24, -0.28, 0.12), rot=(0.5, -0.4, 0))
            arm_r = kf(t, [(1.5, (-1.2, -0.4, 0)), (2.1, (-1.9, -0.3, 0)), (2.4, (-2.6, -0.6, 0)), (3.0, (-0.1, -0.3, 0))])
            el_r = -0.3
        arm_l = kf(t, [(0, (-0.4, 0.3, 0)), (1.35, (-0.4, 0.3, 0)), (1.65, (-1.2, 0.5, 0)), (1.9, (-1.9, 0.2, 0)),
                       (2.05, (-2.0, 0.2, 0)), (2.4, (-2.7, 0.6, 0)), (3.0, (-0.1, 0.3, 0))])
        mp = dict(
            loc=mpos, rz=kf(t, [(0, 0.55), (1.4, 0.55), (1.7, -0.5), (2.0, -0.3), (2.3, 0.0)]) + shake_rz,
            squash=1 + 0.06 * math.sin(t * 2 * PI * 2) * stir - 0.1 * surprised * (1 - seg(t, 2.6, 3.0)),
            head=(kf(t, [(0, -0.25), (1.4, -0.25), (1.8, 0.1), (2.2, 0.25), (3.0, 0.0)]),
                  0.08 * math.sin(t * 4) * stir + 0.3 * math.sin(shake * PI * 9) * (0 < shake < 1), 0),
            look=(kf(t, [(0, 0.3), (1.4, 0.3), (1.7, -0.4), (2.2, 0.0)]), kf(t, [(0, -0.6), (1.4, -0.6), (2.0, 0.6), (2.6, 0.0)])),
            eye_open=blink, eye_big=1 + 0.2 * surprised, pupil=1 - 0.3 * surprised,
            brow=0.9 * surprised, smile=lerp(0.8, -0.2, surprised) + 0.8 * seg(t, 3.7, 4.0),
            mouth=0.6 * surprised * (1 - seg(t, 2.35, 2.5)),
            arm_l=arm_l, arm_r=arm_r, elbow=(-0.4, el_r), tail_wag=t * 5, tail_up=0.5 + 0.4 * surprised,
            ears=0.5 * surprised - 0.6 * seg(t, poof, poof + 0.3) * (1 - seg(t, 3.4, 3.6)), flour=flour,
            hat_tilt=0.2 * math.sin(shake * PI * 8) * (0 < shake < 1),
        )
        m.pose(**mp)
        # flour cloud
        R = rng(11)
        cloud = seg(t, poof, poof + 0.3)
        fade = seg(t, 2.85, 3.4)
        origin = Vector((-0.12, -0.42, 0.08))
        for i, pf in enumerate(P["puffs"]):
            d = Vector((R.uniform(-1, 1), R.uniform(-1.6, 0.5), R.uniform(0.1, 1.2))).normalized()
            size = R.uniform(0.07, 0.17)
            if t < poof or fade >= 1:
                place(pf, None)
                continue
            dist = 0.45 * ease_out(cloud) * R.uniform(0.4, 1.0) + 0.15 * fade
            s = size * (0.3 + 0.9 * ease_out(cloud)) * (1 - ease_in(fade))
            place(pf, origin + d * dist + Vector((0, 0, 0.1 * fade)), scale=(s, s, s * 0.9))
        for i, dpt in enumerate(P["dust"]):
            d = Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(0.2, 1.0))).normalized()
            if 3.45 < t < 4.0:  # flour flying off during the shake
                f = seg(t, 3.45, 4.0)
                c = Vector((mpos.x, mpos.y, 0.3))
                place(dpt, c + d * (0.12 + 0.5 * f) + Vector((0, 0, -0.3 * f * f)), scale=0.008 * (1 - f) + 0.002)
            elif poof < t < 3.4:
                f = seg(t, poof, 3.4)
                place(dpt, origin + d * (0.1 + 0.7 * f), scale=0.007)
            else:
                place(dpt, None)
        if t > poof:
            for o, s in zip(P["patches"][:3], [(-0.1, -0.4, 0.002), (0.15, -0.15, 0.002), (-0.35, -0.3, 0.002)]):
                place(o, s, rot=(0, 0, s[0] * 5), scale=(0.2 * min(1, cloud * 2), 0.15 * min(1, cloud * 2), 0.006))
        # camera: 3/4 medium shot with slow orbit; shake on poof
        sh = 0.02 * math.exp(-(t - poof) * 4) * (t > poof)
        shake_v = (sh * math.sin(t * 90), 0, sh * math.cos(t * 77))
        a = lerp(-0.35, -0.12, smooth(t / 4))
        r = lerp(1.15, 0.95, smooth(t / 4))
        loc = (math.sin(a) * r + 0.05, -math.cos(a) * r - 0.2, 0.42)
        aim(self.cam, loc, (0.05, -0.25, 0.25), lens=30, fstop=4.0, shake=shake_v)

    # ================================================================== SCENE 3
    def s3(self, t):
        P, m, nd = self.P, self.milo, self.nd
        pot = Vector((0.15, 0.05, 0))
        place(P["pot"], pot)
        place(P["bowl"], (0.75, 0.25, 0))
        place(P["flourbag"], (-0.7, 0.3, 0), rot=(0, 0, 0.6))
        for o, s in zip(P["patches"][:2], [(-0.25, -0.35, 0.002), (0.0, -0.45, 0.002)]):
            place(o, s, rot=(0, 0, 1), scale=(0.18, 0.13, 0.006))
        self.tomatoes([((0.6, -0.4, 0.037),), ((0.68, -0.33, 0.037),), None, None, None, None])
        mpos0 = Vector((-0.18, -0.2, 0))
        # lid
        lid_up = seg(t, 0.25, 0.75)
        if t < 1.0:
            place(P["lid"], pot + Vector((-0.06 * lid_up, -0.05 * lid_up, 0.32 + 0.16 * lid_up)), rot=(0.25 * lid_up, -0.35 * lid_up, 0))
        else:
            p = bounce_arc(t, 1.0, 1.55, pot + Vector((-0.06, -0.05, 0.48)), (0.55, -0.3, 0.03), 0.25)
            place(P["lid"], p, rot=(t * 9 * (t < 1.55) + 0.2, 0.3, 0) if t < 1.55 else (0.15, 0.1, 0))
        jump = seg(t, 1.0, 1.45)
        mpos = mpos0 + Vector((-0.2 * ease_out(jump), -0.08 * ease_out(jump), 0.18 * math.sin(PI * jump)))
        shock = smooth(seg(t, 0.95, 1.15))
        reach = kf(t, [(0, 0), (0.2, 1), (0.8, 1), (1.0, 0.6)])
        mp = dict(
            loc=mpos, rz=kf(t, [(0, 0.9), (1.0, 0.75), (1.4, 0.55)]),
            squash=1 - 0.1 * math.exp(-((t - 1.45) / 0.06) ** 2) + 0.08 * math.exp(-((t - 1.2) / 0.12) ** 2),
            lean=kf(t, [(0, 0.15), (0.8, 0.0), (1.2, -0.25), (2.0, -0.1)]),
            head=(kf(t, [(0, 0.0), (0.9, 0.5), (1.4, 0.45), (2.2, 0.4), (2.9, 0.1)]), 0, kf(t, [(0, 0.0), (2.4, 0.0), (2.9, -0.2)])),
            look=(0.0, kf(t, [(0, -0.2), (0.9, 0.7), (2.2, 0.6), (2.9, 0.1)])),
            eye_big=1 + 0.3 * shock, pupil=1 - 0.45 * shock, brow=1.2 * shock,
            smile=lerp(0.6, -0.4, shock), mouth=0.75 * shock * (1 - 0.6 * seg(t, 1.6, 2.2)),
            arm_r=lerp((-2.3, -0.2, 0), (-2.2, 0.2, 0), shock) if t > 0.2 else lerp((-0.1, -0.25, 0), (-2.3, -0.2, 0), reach),
            arm_l=lerp((-0.1, 0.25, 0), (-2.0, 0.5, 0), shock), elbow=(-1.2 * shock, -0.6),
            ears=0.8 * shock, tail_up=0.5 + 0.9 * shock, tail_wag=0.3 * math.sin(t * 30) * shock,
            hat_tilt=0.25 * math.sin(t * 25) * math.exp(-max(0, t - 1.2) * 3) * shock,
            legs=(-0.5 * math.sin(PI * jump), -0.5 * math.sin(PI * jump)),
        )
        m.pose(**mp)
        # noodle creature rising from the pot, then turning toward Milo
        rise = ease_out(seg(t, 0.75, 1.9))
        nd.visible(rise > 0.01)
        if rise > 0.01:
            h = 0.05 + 0.72 * rise
            sway = 0.04 * math.sin(t * 3)
            turn = smooth(seg(t, 2.1, 2.9))
            mh = m.root.location
            pts = []
            for i in range(12):
                s = i / 11
                z = 0.02 + h * s
                x = pot.x + sway * s * s
                y = pot.y
                pts.append(Vector((x, y, z)))
            # bend the top toward Milo
            tip = pts[-1]
            bend_to = Vector((lerp(tip.x, mh.x + 0.15, 0.5), lerp(tip.y, mh.y + 0.05, 0.5), 0.55))
            for i in range(7, 12):
                w = ((i - 7) / 4) ** 1.5 * turn
                pts[i] = pts[i].lerp(bend_to + Vector((0, 0, (i - 9) * 0.04)), w)
            fd = (mh - pts[-1]).normalized() * turn + Vector((0, -1, 0)) * (1 - turn)
            blink = 1 - (seg(t, 2.95, 3.02) - seg(t, 3.1, 3.17))
            nd.set(pts, t=t, face_dir=(fd.x, fd.y, 0), blink=blink, look=(0.2 * turn, -0.2 * turn), eyes_scale=1.2)
        # camera: low side shot -> crash zoom on Milo's eyes at 3.0s
        if t < 2.95:
            f = smooth(t / 2.95)
            aim(self.cam, lerp((0.15, -1.55, 0.18), (-0.05, -1.35, 0.25), f), lerp((0.0, 0.0, 0.32), (-0.05, -0.05, 0.42), f),
                lens=26, fstop=4.0)
        else:
            f = ease_out(seg(t, 2.95, 3.25))
            hp = mpos + Vector((0, 0, 0.35))
            camdir = Vector((math.sin(0.55), -math.cos(0.55), 0.05)).normalized()
            loc = hp + camdir * lerp(1.3, 0.78, f) + Vector((0, 0, 0.02))
            loc = loc + Vector((0, 0, 0.004 * math.sin(t * 60))) * (1 - f)
            aim(self.cam, loc, hp + Vector((0, 0, 0.02)), lens=50, fstop=2.8)

    # ================================================================== SCENE 4
    def s4(self, t):
        P, m, nd = self.P, self.milo, self.nd
        pot2 = Vector((-0.9, -0.15, 0))
        place(P["pot2"], pot2)
        place(P["pot"], (0.95, 0.35, 0))
        patch = Vector((-0.5, -0.22, 0.002))
        place(P["patches"][0], patch, scale=(0.22, 0.16, 0.006))
        place(P["patches"][1], (0.2, 0.2, 0.002), scale=(0.15, 0.12, 0.006))
        # noodle path: head goes from x=1.1 -> -0.45 along y=-0.1
        hx = kf(t, [(0, 0.95), (1.5, 0.25), (2.8, -0.2), (4.0, -0.45)], ease=lambda x: x)
        head = Vector((hx, -0.12 + 0.05 * math.sin(t * 3), 0))
        nd.visible(True)
        spine = snake_spine(head, (-1, 0), t, length=1.1, lift=0.32, wiggle=0.07, ring=0.055, bounce=0.05)
        look_m = smooth(seg(t, 1.0, 1.5))
        nd.set(spine, t=t, face_dir=(-1, -0.6 * look_m, 0), look=(0.0, 0.0), eyes_scale=1.2)
        # tomatoes knocked when noodle passes
        tspots = []
        R = rng(5)
        for i, tx in enumerate((0.75, 0.62, 0.5, 0.35)):
            tp = Vector((tx, -0.18 + 0.08 * (i % 2), 0.037))
            hit = 1.5 * (0.95 - tx) / 0.7
            if t < hit:
                tspots.append((tp,))
            else:
                f = seg(t, hit, hit + 0.7)
                tgt = Vector((tx - 0.3 - 0.2 * i, -0.65 - 0.1 * i, -0.3 if i % 2 else 0.037))
                p = bounce_arc(t, hit, hit + 0.7, tp, tgt, 0.2 + 0.05 * i)
                tspots.append((p, (t * 8, t * 6, 0)))
        tspots += [None, None]
        self.tomatoes(tspots)
        # bowl pushed aside
        bp = kf(t, [(0, (0.05, 0.12, 0)), (1.75, (0.05, 0.12, 0)), (2.2, (-0.15, 0.4, 0))])
        place(P["bowl"], bp, rot=(0, 0, 0.6 * seg(t, 1.75, 2.2)))
        # wooden spoon: wrapped & lifted by the noodle
        sp = Vector((0.45, -0.05, 0.015))
        if t < 0.95:
            place(P["spoon"], sp, rot=(PI / 2, 0, 0.3))
        else:
            f = seg(t, 0.95, 1.6)
            h = nd.headE.location
            p = lerp(sp, h + Vector((0.12, 0.05, 0.12)), smooth(f))
            place(P["spoon"], p, rot=(PI / 2 + f * 2, t * 6 * f, 0.3))
        # Milo: watching -> runs left -> slips on flour -> flies into pot2 -> peeks
        run_start, slip, land = 1.05, 1.95, 2.65
        if t < run_start:
            mpos = Vector((-0.05, -0.3, 0))
            rz = kf(t, [(0, 0.0), (0.6, 0.5), (1.0, 0.7)])
            mp = dict(eye_big=1.2, pupil=0.6, brow=1.0, mouth=0.5, smile=-0.3, ears=0.6,
                      arm_l=(-1.5, 0.6, 0), arm_r=(-1.5, -0.6, 0), elbow=(-1.0, -1.0), look=(0.4, 0.0),
                      head=(0.1, 0.0, 0.2))
        elif t < slip:
            f = seg(t, run_start, slip)
            mpos = Vector((lerp(-0.05, patch.x + 0.04, f), lerp(-0.3, patch.y, f), 0))
            cyc, bob = run_cycle(t, freq=4.0)
            rz = -PI / 2 + 0.25
            mp = dict(eye_big=1.25, pupil=0.6, brow=1.0, mouth=0.6, smile=-0.4, ears=-0.4, lean=0.3,
                      head=(0.0, 0.0, -0.9), look=(-0.6, 0.0), **cyc)
            mpos.z += bob
        elif t < land:
            f = seg(t, slip, land)
            p = bounce_arc(t, slip, land, (patch.x + 0.04, patch.y, 0), (pot2.x, pot2.y, 0.04), 0.42)
            mpos = Vector(p)
            rz = -PI / 2 + 0.25
            mp = dict(eye_big=1.35, pupil=0.5, brow=1.3, mouth=0.9, smile=-0.6, ears=0.9,
                      lean=-0.9 * math.sin(PI * f) - 0.2, legs=(-1.4 * math.sin(PI * min(1, f * 1.5)), -1.2 * math.sin(PI * min(1, f * 1.5))),
                      arm_l=(-2.8, 0.5, 0), arm_r=(-2.8, -0.5, 0), elbow=(-0.2, -0.2), hat_tilt=0.4 * math.sin(f * 12))
        else:
            peek = smooth(seg(t, 2.9, 3.4))
            mpos = Vector((pot2.x, pot2.y, -0.3 + 0.2 * peek))
            rz = kf(t, [(land, 0.0), (3.3, 0.4)])
            mp = dict(eye_big=1.15, pupil=0.7, brow=0.6, mouth=0.0, smile=-0.2, ears=0.3 + 0.4 * peek,
                      look=(0.9, 0.0), head=(0.0, 0.0, 0.0), arm_l=(-2.4, 0.2, 0), arm_r=(-2.4, -0.2, 0), elbow=(-1.5, -1.5),
                      squash=1 - 0.2 * math.exp(-((t - land) / 0.06) ** 2))
        mp.setdefault("tail_wag", t * 6)
        m.pose(loc=mpos, rz=rz, **mp)
        # camera: fast lateral tracking following the action, low angle
        cx = kf(t, [(0, 0.45), (1.0, 0.25), (1.9, -0.35), (2.7, -0.6), (4.0, -0.55)])
        shake = 0.012 * math.exp(-max(0, t - land) * 6) * (t > land)
        aim(self.cam, (cx + 0.15, -1.65, 0.3), (cx - 0.05, -0.1, 0.13), lens=27, fstop=5.0,
            shake=(shake * math.sin(t * 80), 0, shake * math.cos(t * 70)))

    # ================================================================== SCENE 5
    def s5(self, t):
        P, m, nd = self.P, self.milo, self.nd
        jar = Vector((0.0, 0.1, 0))
        place(P["jar"], jar)
        place(P["patches"][0], (0.6, -0.25, 0.002), scale=(0.18, 0.12, 0.006))
        self.tomatoes([((0.8, 0.3, 0.037),), None, None, None, None, None])
        nd.visible(True)
        cut1, cut2 = 0.8, 1.6
        if t < cut2:
            # chase along the counter from right to left (toward jar)
            mx = kf(t, [(0, 1.3), (cut2, 0.2)], ease=lambda x: x)
            mpos = Vector((mx, -0.2, 0))
            cyc, bob = run_cycle(t, freq=4.5, amp=1.0)
            mpos.z += bob
            m.pose(loc=mpos, rz=-PI / 2 + 0.3, lean=0.35, head=(0, 0, 0.6), look=(0.7, 0), eye_big=1.25, pupil=0.6,
                   brow=1.0, mouth=0.7, smile=-0.4, ears=-0.6, tail_wag=t * 9, tail_up=0.9, **cyc)
            hop = abs(math.sin(t * 6.0))
            head = Vector((mx + 0.55, -0.15, 0))
            spine = snake_spine(head, (-1, 0), t, length=1.0, lift=0.2 + 0.18 * hop, wiggle=0.05, ring=0.055, bounce=0.12)
            nd.set(spine, t=t, face_dir=(-1, -0.3, 0), look=(-0.5, 0), eyes_scale=1.2, head_up=(0, 0, 0.05 + 0.12 * hop))
            if t < cut1:   # A: low, frontal-ish, Milo running toward the lens
                aim(self.cam, (mx - 0.75, -0.75, 0.12), (mx + 0.15, -0.18, 0.18), lens=24, fstop=4.0)
            else:          # B: side tracking, both in frame
                aim(self.cam, (mx + 0.05, -1.3, 0.28), (mx + 0.22, -0.15, 0.2), lens=24, fstop=5.0)
            return
        # C: jar hiding gag (front of jar)
        tl = t - cut2
        hide = smooth(seg(tl, 0.0, 0.35))
        peek = smooth(seg(tl, 1.05, 1.35))
        dbl = seg(tl, 1.6, 1.9)
        mpos = Vector(kf(tl, [(0, (0.2, -0.2, 0)), (0.18, (0.32, 0.22, 0)), (0.35, (0.02, 0.42, 0)),
                              (1.05, (0.02, 0.42, 0)), (1.35, (-0.16, 0.3, 0))]))
        tremble = 0.03 * math.sin(tl * 60) * (0.35 < tl < 1.05)
        rzm = kf(tl, [(0, 0.0), (0.18, -2.4), (0.35, -0.3), (0.5, 0.0)])
        m.pose(loc=mpos, rz=rzm + tremble, lean_side=-0.4 * peek, lean=0.15 * peek,
               head=(0.0, -0.25 * peek, 0.7 * peek),
               look=(0.9 * peek, 0.0), eye_big=1.15 + 0.25 * dbl, pupil=0.8 - 0.3 * dbl,
               brow=0.6 + 0.8 * dbl, mouth=0.4 * dbl, smile=0.1 - 0.4 * dbl, ears=0.4 + 0.6 * dbl - 0.8 * (0.35 < tl < 1.05),
               arm_l=(-1.2 * peek, 0.4, 0), arm_r=(-1.5, -0.4, 0), elbow=(-1.0, -1.2),
               tail_wag=tl * 4, tail_up=0.6 + 0.6 * dbl, hat_tilt=0.3 * math.sin(dbl * PI * 3) * (0 < dbl < 1),
               squash=1 - 0.08 * (0.35 < tl < 1.05))
        # noodle comes around the right side of the jar and peeks out at the same moment
        arr = smooth(seg(tl, 0.2, 1.0))
        hx = lerp(0.9, 0.24, arr)
        pts = []
        for i in range(14):
            s = i / 13
            ang = lerp(0.0, -1.5 * peek, s)
            if s < 0.6:
                p = Vector((lerp(1.4, hx + 0.2, s / 0.6), 0.45 + 0.05 * math.sin(s * 9 - tl * 6), 0.055))
            else:
                u = (s - 0.6) / 0.4
                p = Vector((lerp(hx + 0.2, hx - 0.06 * peek, u), lerp(0.45, 0.3 - 0.1 * peek, u), 0.055 + 0.24 * u * u))
            pts.append(p)
        blink = 1 - (seg(tl, 1.65, 1.7) - seg(tl, 1.8, 1.85))
        nd.set(pts, t=t, face_dir=(-1 * peek + (1 - peek) * -1, -0.4 * peek, 0), look=(-0.6 * peek, 0), blink=blink,
               eyes_scale=1.25 + 0.2 * dbl)
        # camera: front of jar, slow push; tiny snap on the double take
        f = smooth(tl / 2.4)
        sn = 0.02 * math.exp(-((tl - 1.62) / 0.05) ** 2)
        aim(self.cam, Vector(lerp((0.05, -1.35, 0.3), (0.02, -0.95, 0.26), f)) + Vector((0, sn, 0)), (0.02, 0.1, 0.24), lens=32, fstop=3.5)

    # ================================================================== SCENE 6
    def s6(self, t):
        P, m, nd = self.P, self.milo, self.nd
        jar = Vector((-0.45, 0.25, 0))
        place(P["jar"], jar)
        plate = Vector((0.18, -0.12, 0))
        place(P["plate"], plate)
        place(P["patches"][0], (-0.6, -0.3, 0.002), scale=(0.2, 0.14, 0.006))
        fork_rest = Vector((-0.22, -0.32, 0.012))
        nd.visible(True)
        reach = smooth(seg(t, 0.15, 0.9))
        dock = smooth(seg(t, 2.1, 2.6))
        wind = seg(t, 2.6, 4.0)
        # noodle body: from behind the jar (right side) toward the plate; head over plate
        pts = []
        head0 = Vector((0.0, 0.15, 0.28))
        headp = Vector((plate.x + 0.02, plate.y + 0.03, 0.2 - 0.12 * dock))
        hp = head0.lerp(headp, reach)
        for i in range(14):
            s = i / 13
            base = Vector((lerp(0.9, 0.45, s), lerp(0.35, 0.15, s), 0.055))
            if s < 0.65:
                p = base + Vector((0, 0.04 * math.sin(9 * s - t * 4), 0))
            else:
                u = (s - 0.65) / 0.35
                p = base.lerp(hp, smooth(u))
            pts.append(p)
        # winding: last part of the spine spirals around the fork axis
        fork_axis = Vector((plate.x - 0.02, plate.y + 0.0, 0.0))
        if wind > 0:
            turns = 1.8 * wind
            for i in range(9, 14):
                u = (i - 9) / 4
                a = u * turns * 2 * PI + t * 8
                r = 0.06 * (1 - 0.3 * u)
                spiral = fork_axis + Vector((math.cos(a) * r, math.sin(a) * r, 0.06 + 0.08 * u))
                pts[i] = pts[i].lerp(spiral, smooth(wind * 1.5) * (0.4 + 0.6 * u))
        happy = smooth(seg(t, 2.4, 2.8))
        nd.set(pts, t=t, face_dir=(0.2 - 0.6 * happy, -1, 0) if reach > 0.5 else (-1, -0.2, 0),
               look=(0.4 * (1 - happy), -0.5 * reach * (1 - happy)), eyes_scale=1.2 + 0.1 * reach,
               blink=1 - 0.8 * happy * (0.5 + 0.5 * math.sin(t * 3)) * 0, head_up=(0.06 * happy, -0.02, 0.07 + 0.06 * happy))
        # Milo: peeks, notices, idea, grabs fork, twirls
        idea = smooth(seg(t, 0.9, 1.25))
        grab = seg(t, 1.45, 1.75)
        walk = seg(t, 1.75, 2.45)
        mpos = Vector((lerp(-0.3, -0.15, walk), lerp(-0.12, -0.2, walk), 0))
        if t < 1.75:
            if t > 1.45:
                self.hold(P["fork"], m, 1, loc=(0, 0, -0.04), rot=(0, 0, 0), scale=1.0)
            else:
                place(P["fork"], fork_rest, rot=(PI / 2, 0, 0.4))
        else:
            self.hold(P["fork"], m, 1, loc=(0, -0.02, -0.04), rot=(PI + 0.25 * math.sin(t * 2), 0, t * 8 * wind), scale=1.0)
        cyc, bob = walk_cycle(t, freq=2.4, amp=0.5)
        walking = 0 < walk < 1
        mp = dict(
            loc=mpos + Vector((0, 0, bob if walking else 0)),
            rz=kf(t, [(0, 0.3), (1.4, 0.3), (1.6, -0.2), (1.9, 0.6), (2.5, 0.7)]),
            head=(kf(t, [(0, 0.05), (0.9, -0.15), (1.3, 0.2), (1.5, -0.3), (2.5, -0.3)]), 0.25 * (1 - idea) * reach, kf(t, [(0, 0.3), (0.9, 0.5), (1.3, 0.0)])),
            look=(kf(t, [(0, 0.5), (0.9, 0.6), (1.2, 0.0), (1.5, -0.4), (2.4, 0.3)]), kf(t, [(0, 0.2), (0.9, -0.5), (1.2, 0.3), (2.4, -0.5)])),
            eye_big=1.0 + 0.25 * idea * (1 - seg(t, 1.5, 2.0)), pupil=1.0 + 0.2 * idea,
            brow=kf(t, [(0, 0.3), (0.6, 0.9), (0.9, 0.0), (1.2, 1.2), (1.8, 0.4)]),
            brow_ang=kf(t, [(0, 0.0), (0.6, 0.0), (0.9, 0.35), (1.15, 0.0)]),
            smile=kf(t, [(0, -0.1), (0.8, 0.0), (1.2, 1.0)]), mouth=0.4 * idea * (1 - seg(t, 1.4, 1.6)),
            ears=0.3 + 0.5 * idea, tail_up=0.4 + 0.6 * idea, tail_wag=t * 4,
            arm_r=kf(t, [(0, (-0.2, -0.3, 0)), (1.45, (-0.9, -0.2, 0)), (1.75, (-1.3, -0.3, 0)), (2.6, (-1.6, -0.2, 0))]) if t < 2.6 else
            (-1.6 + 0.25 * math.sin(t * 8), -0.2 + 0.25 * math.cos(t * 8), 0),
            arm_l=(-0.4 - 0.4 * idea + (cyc["arm_l"][0] if walking else 0), 0.3, 0),
            elbow=(-0.6, -0.8), legs=cyc["legs"] if walking else (0, 0),
        )
        m.pose(**mp)
        # camera: close on face + fork, gentle arc
        f = smooth(t / 4)
        aim(self.cam, lerp((-0.75, -1.3, 0.45), (0.45, -1.2, 0.42), f), lerp((-0.1, -0.1, 0.22), (0.05, -0.12, 0.18), f), lens=30, fstop=3.5)

    # ================================================================== SCENE 7
    def s7(self, t):
        P, m = self.P, self.milo
        plate = Vector((0, 0, 0))
        place(P["plate"], plate)
        d = self.K.dish
        d.show(True)
        d.root.location = plate + Vector((0, 0, 0.0))
        grow = smooth(seg(t, 0.0, 1.5))
        sauce = back_out(seg(t, 1.55, 1.85)) if t > 1.55 else 0.0
        basil = smooth(seg(t, 2.15, 2.75))
        cheese = 1.0 if t > 2.75 else 0.0
        d.set(grow=0.25 + 0.75 * grow, sauce=sauce, basil=basil, cheese=cheese, spin=-grow * 1.5)
        # sauce drop falling in before it lands
        if 1.3 < t < 1.6:
            f = seg(t, 1.3, 1.58)
            place(P["patches"][7], None)
        # Milo behind the plate, twirling then presenting
        mpos = Vector((-0.12, 0.33, 0))
        if t < 1.5:
            self.hold(P["fork"], m, 1, loc=(0, -0.02, -0.04), rot=(PI, 0, t * 10), scale=1.0)
            arm_r = (-1.5 + 0.2 * math.sin(t * 10), -0.3 + 0.2 * math.cos(t * 10), 0)
        else:
            place(P["fork"], (0.32, 0.12, 0.012), rot=(PI / 2, 0, 1.2))
            arm_r = kf(t, [(1.5, (-1.5, -0.3, 0)), (2.0, (-1.9, -0.2, 0)), (2.4, (-1.7, -0.6, 0)), (3.0, (-0.3, -1.0, 0)), (4, (-0.3, -1.1, 0))])
        arm_l = kf(t, [(0, (-0.3, 0.3, 0)), (2.0, (-0.3, 0.3, 0)), (2.3, (-1.8, 0.2, 0)), (2.7, (-1.8, 0.3, 0)), (3.1, (-0.3, 1.1, 0))])
        m.pose(loc=mpos, rz=0.0, head=(kf(t, [(0, -0.35), (2.6, -0.3), (3.0, 0.1)]), 0.1 * math.sin(t * 2), 0),
               look=(0, kf(t, [(0, -0.7), (2.6, -0.6), (3.0, 0.0)])), smile=1.0, mouth=0.25 * seg(t, 3.0, 3.2),
               eye_open=1 - 0.85 * seg(t, 3.1, 3.3), brow=0.4, arm_l=arm_l, arm_r=arm_r, elbow=(-0.6, -0.6),
               tail_wag=t * 5, tail_up=0.9, ears=0.4)
        # leftover happy noodle curling around the rim
        lo = self.leftover
        lo.visible(True)
        pts = []
        for i in range(16):
            s = i / 15
            a = lerp(-2.6, 1.0, s) + 0.1 * math.sin(t * 3)
            r = 0.3
            z = 0.02 + 0.12 * smooth((s - 0.8) / 0.2) + 0.01 * math.sin(s * 12 + t * 5)
            pts.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
        lo.set(pts, t=t, face_dir=(-0.6, -1, 0), look=(0.0, 0.3), eyes_scale=0.8, show_curls=False,
               head_up=(0, 0, 0.035 + 0.01 * math.sin(t * 6)), blink=1 - (seg(t, 3.3, 3.36) - seg(t, 3.45, 3.5)))
        # sparkle on the finished dish (emissive tiny stars)
        R = rng(21)
        for i, dpt in enumerate(P["dust"][:14]):
            if t > 3.0:
                f = (t - 3.0) * 1.5 + i * 0.07
                ph = (f % 1.0)
                a = R.random() * 6.28
                place(dpt, (math.cos(a) * 0.18, math.sin(a) * 0.18 - 0.02, 0.12 + 0.15 * ph), scale=0.006 * math.sin(PI * ph))
        # camera: cinematic orbit around the plate at food level
        ang = lerp(-0.85, 0.75, smooth(t / 4))
        r = lerp(0.85, 0.7, smooth(t / 4))
        cz = lerp(0.42, 0.3, smooth(t / 4))
        aim(self.cam, (math.sin(ang) * r, -math.cos(ang) * r, cz), (0.0, 0.05, 0.12), lens=40, fstop=2.4)

    # ================================================================== SCENE 8
    def s8(self, t):
        P, m, mom = self.P, self.milo, self.mom
        self.mess()
        plate = Vector((0.12, 0.22, 0))
        place(P["plate"], plate)
        d = self.K.dish
        d.show(True)
        d.root.location = plate
        d.set(grow=1, sauce=1, basil=1, cheese=1)
        lo = self.leftover
        lo.visible(True)
        self.show_mom(True)
        door = smooth(seg(t, 0.0, 0.45))
        self.K.door_pivot.rotation_euler = (0, 0, 1.6 * door)
        # mom walks from door to the back of the island
        w = seg(t, 0.25, 1.45)
        start = Vector((-2.15, 2.75, FLOOR_Z))
        stop = Vector((0.15, 0.95, FLOOR_Z))
        mpos = start.lerp(stop, smooth(w))
        cyc, bob = walk_cycle(t, freq=1.9, amp=0.5)
        walking = 0 < w < 1
        shock = smooth(seg(t, 1.45, 1.65)) * (1 - smooth(seg(t, 2.1, 2.4)))
        notice = smooth(seg(t, 2.1, 2.4))
        taste = seg(t, 2.5, 2.95)
        chew = seg(t, 2.95, 3.5)
        joy = smooth(seg(t, 3.5, 3.62))
        ang = math.atan2(stop.x - start.x, -(stop.y - start.y)) if walking else 0.0
        mom_mp = dict(
            loc=mpos + Vector((0, 0, bob if walking else 0)), rz=ang * (1 - seg(t, 1.2, 1.45)) if t < 1.45 else 0.0,
            head=(lerp(0.0, -0.45, notice) - 0.15 * shock + 0.25 * joy, 0.1 * math.sin(t * 3) * walking, 0.0),
            look=(0, lerp(0.0, -0.7, notice) * (1 - joy)), eye_big=1 + 0.3 * shock + 0.25 * joy, pupil=1 - 0.4 * shock + 0.3 * joy,
            brow=1.3 * shock + 0.8 * joy, smile=lerp(0.6, -0.3, shock) + 0.6 * joy, mouth=0.8 * shock + 0.5 * joy + 0.3 * chew * abs(math.sin(chew * 20)),
            eye_open=1 - 0.94 * smooth(seg(t, 2.95, 3.05)) * (1 - joy), ears=0.6 * shock + 0.6 * joy,
            tail_up=0.4 + 0.8 * joy, tail_wag=t * 3,
            lean=0.35 * notice * (1 - 0.6 * joy),
        )
        if walking:
            mom_mp.update(cyc)
        elif t < 2.1:
            mom_mp.update(arm_l=(-2.0 * shock, 0.6 * shock + 0.15, 0), arm_r=(-2.0 * shock, -0.6 * shock - 0.15, 0), elbow=(-1.6 * shock, -1.6 * shock))
        else:
            # right paw (index 0 is -X... use index 1) tastes with a fork
            arm_tgt = kf(t, [(2.1, (-0.2, -0.15, 0)), (2.5, (-1.2, -0.2, 0)), (2.8, (-1.1, -0.1, 0)), (2.95, (-2.0, 0.15, 0)), (3.5, (-2.0, 0.15, 0)), (3.65, (-2.6, -0.6, 0))])
            mom_mp.update(arm_r=arm_tgt, elbow=(-0.3, kf(t, [(2.1, -0.3), (2.8, -0.5), (2.95, -1.7), (3.5, -1.7), (3.65, -0.4)])),
                          arm_l=(-0.4 - 1.6 * joy, 0.2 + 0.5 * joy, 0))
            if t > 2.45:
                self.hold(P["momfork"], mom, 1, loc=(0, -0.01, -0.02), rot=(PI if t < 2.9 else 0.3, 0, 0), scale=0.75)
        mom.pose(**mom_mp)
        # Milo waits nervously beside the plate
        nerv = 1 - joy
        m.pose(loc=(-0.25, 0.05, 0), rz=kf(t, [(0, 0.6), (1.0, 2.6), (3.0, 2.5)]),
               head=(0.45 if t > 1.2 else 0.1, 0, 0.0), look=(0.0, 0.5 if t > 1.2 else 0.0),
               smile=lerp(-0.1, 1.0, joy), mouth=0.3 * joy, brow=0.6 * nerv + 0.8 * joy, eye_big=1.05 + 0.1 * joy,
               arm_l=(-1.0 * nerv, 0.2, 0), arm_r=(-1.0 * nerv, -0.2, 0), elbow=(-1.2 * nerv, -1.2 * nerv),
               tail_wag=t * 6 * (1 + joy), ears=-0.3 * nerv + 0.6 * joy, squash=1 + 0.08 * joy * math.sin(t * 30))
        # leftover noodle around the plate
        pts = []
        for i in range(16):
            s = i / 15
            a = lerp(2.2, -0.9, s)
            pts.append(Vector((plate.x + math.cos(a) * 0.3, plate.y + math.sin(a) * 0.3, 0.02 + 0.12 * smooth((s - 0.8) / 0.2))))
        lo.set(pts, t=t, face_dir=(-0.4, 1, 0) if t > 1.4 else (-0.6, -1, 0), eyes_scale=0.8, show_curls=False,
               head_up=(0, 0, 0.035), look=(0, 0.3))
        # cameras: A wide from the front (Milo + plate foreground, mom enters in back)
        if t < 1.45:
            aim(self.cam, (0.55, -1.75, 0.5), (-0.6, 1.2, 0.2), lens=26, fstop=6.0)
        elif t < 2.1:  # B: mom's shocked face
            aim(self.cam, (0.25, -0.6, 0.45), (0.15, 0.95, 0.38), lens=40, fstop=3.0)
        else:          # C: tasting, slow push
            f = smooth(seg(t, 2.1, 4.0))
            aim(self.cam, lerp((0.45, -0.75, 0.35), (0.32, -0.42, 0.36), f), (0.12, 0.85, 0.3), lens=34, fstop=3.5)

    # ================================================================== SCENE 9
    def s9(self, t):
        P, m, mom = self.P, self.milo, self.mom
        self.mess()
        plate = Vector((0.12, 0.22, 0))
        place(P["plate"], plate)
        d = self.K.dish
        d.show(True)
        d.root.location = plate
        d.set(grow=1, sauce=1, basil=1, cheese=1)
        self.show_mom(True)
        # mom: "more please!" -- taps plate with fork & raises paw, nodding happily
        nod = math.sin(t * 14) * (1 - seg(t, 1.6, 1.9))
        more = seg(t, 0.0, 0.25)
        mom.pose(loc=(0.15, 0.95, FLOOR_Z), rz=0.0, head=(0.1 + 0.15 * nod, 0.15 * math.sin(t * 5), 0.0),
                 look=(0, -0.2), eye_open=0.12 if t < 1.5 else 1.0, smile=1.2, mouth=0.55, eye_big=1.15, brow=0.9, ears=0.6,
                 arm_l=(-2.7, -0.55 - 0.35 * math.sin(t * 14), 0), elbow=(-0.2 - 0.4 * math.sin(t * 14), -0.9),
                 arm_r=(-1.3 + 0.15 * math.sin(t * 16), -0.2, 0), lean=0.15, tail_up=1.0, tail_wag=t * 5)
        self.hold(P["momfork"], mom, 1, loc=(0, -0.01, -0.02), rot=(PI * 0.7, 0, 0), scale=0.75)
        # Milo: big grin, adjusts hat, bows
        adj = seg(t, 1.2, 1.9)
        bow = smooth(seg(t, 2.75, 3.15)) * (1 - smooth(seg(t, 3.55, 3.9)) * 0.4)
        m.pose(loc=(-0.25, -0.08, 0), rz=kf(t, [(0, 2.4), (0.9, 2.4), (1.25, 0.15), (4, 0.1)]),
               head=(kf(t, [(0, 0.45), (0.9, 0.45), (1.2, 0.0)]) - 0.2 * bow, 0.15 * math.sin(adj * PI * 2), 0),
               look=(0, 0.1), smile=1.2, mouth=0.45 * seg(t, 0.2, 0.5) * (1 - seg(t, 2.6, 2.8)), eye_big=1.1,
               eye_open=1 - 0.88 * bow, brow=0.5,
               arm_l=kf(t, [(0, (-0.4, 0.3, 0)), (1.2, (-0.4, 0.3, 0)), (1.4, (-2.9, 0.3, 0)), (1.9, (-2.9, 0.3, 0)), (2.3, (-0.6, 0.3, 0)),
                            (2.8, (-1.2, -0.5, 0)), (4, (-1.2, -0.5, 0))]),
               arm_r=kf(t, [(0, (-0.4, -0.3, 0)), (2.6, (-0.3, -0.3, 0)), (2.9, (0.6, -1.0, 0)), (4, (0.6, -1.0, 0))]),
               elbow=(kf(t, [(0, -0.3), (1.3, -1.2), (2.2, -0.3), (2.8, -1.6)]), -0.4),
               hat_tilt=0.35 * math.sin(adj * PI * 3) * (0 < adj < 1) - 0.05, lean=0.75 * bow, tail_up=1.0, tail_wag=t * 5,
               ears=0.4, squash=1 + 0.05 * math.sin(t * 6))
        lo = self.leftover
        lo.visible(True)
        pts = []
        for i in range(16):
            s = i / 15
            a = lerp(2.2, -0.9, s) + 0.1 * math.sin(t * 2)
            pts.append(Vector((plate.x + math.cos(a) * 0.3, plate.y + math.sin(a) * 0.3, 0.02 + 0.14 * smooth((s - 0.8) / 0.2))))
        lo.set(pts, t=t, face_dir=(-0.5, -1, 0), eyes_scale=0.85, show_curls=False,
               head_up=(0.02 * math.sin(t * 7), 0, 0.04 + 0.015 * math.sin(t * 7)), look=(0, 0.2),
               blink=1 - (seg(t, 3.2, 3.25) - seg(t, 3.35, 3.4)))
        # sparkles around Milo at the bow
        R = rng(33)
        for i, dpt in enumerate(P["dust"][:16]):
            if t > 2.8:
                ph = ((t - 2.8) * 1.2 + i * 0.06) % 1.0
                a = R.random() * 6.28
                place(dpt, (-0.25 + math.cos(a) * 0.25, -0.08 + math.sin(a) * 0.12, 0.1 + 0.4 * R.random() + 0.1 * ph),
                      scale=0.007 * math.sin(PI * ph))
        # camera: medium on Milo, slow pull back to reveal the kitchen
        if t < 1.3:   # mom asks for more
            f = smooth(t / 1.3)
            aim(self.cam, lerp((0.5, -1.0, 0.55), (0.45, -0.85, 0.55), f), (0.1, 0.6, 0.45), lens=30, fstop=4.0)
        else:         # Milo, proud; slow pull-back reveal
            f = smooth(seg(t, 1.3, 4.0))
            aim(self.cam, lerp((-0.1, -1.0, 0.36), (0.3, -2.7, 0.8), f), lerp((-0.2, 0.0, 0.25), (-0.05, 0.4, 0.25), f),
                lens=lerp(32, 30, f), fstop=lerp(3.5, 6.0, f))
