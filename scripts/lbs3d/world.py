"""Kitchen set, props, noodle creature, lights, camera and render settings."""
import math

import bpy
from mathutils import Vector

from .core import (obj, empty, curve_obj, set_curve_points, resample, new_mat, textured_mat,
                   flourable, rng, clamp, link)

COUNTER_Z = 0.0     # island countertop surface (stage for the kitten)
FLOOR_Z = -0.92


class Kitchen:
    def __init__(self):
        M = self.M = {}
        M["wood"] = textured_mat("butcher", "wood", (0.86, 0.6, 0.34), (0.7, 0.42, 0.2), scale=3.0, rough=0.45, coat=0.25)
        M["teal"] = new_mat("teal", (0.1, 0.62, 0.66), rough=0.35, coat=0.4)
        M["yellow"] = new_mat("yellow", (1.0, 0.68, 0.05), rough=0.35, coat=0.4)
        M["wall"] = new_mat("wall", (0.62, 0.86, 0.78), rough=0.8)
        M["tiles"] = textured_mat("tiles", "tiles", (0.35, 0.68, 0.98), (0.95, 0.97, 1.0), scale=7.0, rough=0.15, coat=0.6)
        M["floor"] = textured_mat("floor", "checker", (0.96, 0.9, 0.78), (0.86, 0.36, 0.22), scale=1.6, rough=0.3, coat=0.3)
        M["steel"] = new_mat("steel", (0.85, 0.86, 0.9), rough=0.18, metal=1.0)
        M["redpot"] = new_mat("redpot", (0.92, 0.12, 0.08), rough=0.2, coat=1.0)
        M["bluebowl"] = new_mat("bluebowl", (0.25, 0.55, 1.0), rough=0.2, coat=1.0)
        M["porcelain"] = new_mat("porcelain", (0.98, 0.98, 0.97), rough=0.12, coat=1.0)
        M["tomato"] = new_mat("tomato", (0.95, 0.07, 0.03), rough=0.18, coat=1.0, sss=0.2)
        M["stem"] = new_mat("stem", (0.15, 0.6, 0.12), rough=0.5)
        M["egg"] = new_mat("egg", (1.0, 0.92, 0.8), rough=0.45, sss=0.2)
        M["kraft"] = flourable("kraft", (0.86, 0.68, 0.45), rough=0.8, sheen=0.2)
        M["flour"] = new_mat("flourm", (0.98, 0.97, 0.95), rough=0.95, sheen=0.8)
        M["glass"] = new_mat("glass", (0.9, 0.97, 1.0), rough=0.05, transm=1.0, ior=1.45)
        M["sauce"] = new_mat("sauce", (0.9, 0.06, 0.02), rough=0.12, coat=1.0, sss=0.3)
        M["sky"] = new_mat("sky", (0.6, 0.85, 1.0), emit=(0.65, 0.88, 1.0), emit_str=2.5)
        M["green"] = new_mat("plant", (0.18, 0.7, 0.22), rough=0.45, sss=0.2)
        M["terracotta"] = new_mat("terracotta", (0.85, 0.4, 0.22), rough=0.7)
        M["door"] = new_mat("doorm", (0.3, 0.7, 0.55), rough=0.4, coat=0.3)
        M["brass"] = new_mat("brass", (1.0, 0.75, 0.3), rough=0.25, metal=1.0)
        M["pink"] = new_mat("jarpink", (1.0, 0.45, 0.6), rough=0.3, coat=0.6)
        M["purple"] = new_mat("jarpurple", (0.6, 0.4, 1.0), rough=0.3, coat=0.6)
        M["orange"] = new_mat("jarorange", (1.0, 0.55, 0.1), rough=0.3, coat=0.6)
        M["stool"] = new_mat("stool", (1.0, 0.35, 0.3), rough=0.35, coat=0.5)
        M["basil"] = new_mat("basil", (0.1, 0.62, 0.12), rough=0.3, coat=0.5, sss=0.3)
        self.build_room()
        self.build_props()

    # ------------------------------------------------------------------ room
    def build_room(self):
        M = self.M
        # island
        obj("island_top", "rcube", (0, 0, COUNTER_Z - 0.035), (4.2, 1.5, 0.07), M["wood"], b=0.06)
        obj("island_body", "cube", (0, 0, (COUNTER_Z + FLOOR_Z) / 2 - 0.03), (4.0, 1.36, abs(FLOOR_Z) - 0.05), M["teal"])
        for i, x in enumerate((-1.5, -0.5, 0.5, 1.5)):
            obj(f"island_door{i}", "rcube", (x, -0.69, -0.47), (0.9, 0.04, 0.75), M["teal"], b=0.1)
            obj(f"island_knob{i}", "sphere", (x + 0.34, -0.72, -0.2), (0.025,) * 3, M["brass"])
        obj("floor", "cube", (0, 2, FLOOR_Z - 0.05), (20, 20, 0.1), M["floor"])
        # back wall with counter, tiles, cabinets, window, door
        BY = 2.9
        obj("backwall", "cube", (0, BY + 0.05, 1.0), (14, 0.1, 5), M["wall"])
        obj("sidewall", "cube", (-4.2, 0, 1.0), (0.1, 12, 5), M["wall"])
        obj("backsplash", "cube", (1.4, BY - 0.01, 0.35), (4.6, 0.04, 0.7), M["tiles"])
        obj("back_counter", "rcube", (1.4, BY - 0.35, COUNTER_Z - 0.035), (4.8, 0.7, 0.07), M["wood"], b=0.06)
        obj("back_base", "cube", (1.4, BY - 0.35, (COUNTER_Z + FLOOR_Z) / 2), (4.7, 0.66, abs(FLOOR_Z)), M["yellow"])
        for i, x in enumerate((-0.4, 0.5, 1.4, 2.3, 3.2)):
            obj(f"bdoor{i}", "rcube", (x, BY - 0.69, -0.45), (0.8, 0.04, 0.75), M["yellow"], b=0.1)
            obj(f"bknob{i}", "sphere", (x - 0.3, BY - 0.72, -0.2), (0.025,) * 3, M["brass"])
        for i, x in enumerate((-0.35, 0.55, 2.35, 3.25)):
            obj(f"ucab{i}", "rcube", (x, BY - 0.2, 1.35), (0.85, 0.4, 0.75), M["yellow"], b=0.1)
            obj(f"ucabk{i}", "sphere", (x - 0.32, BY - 0.41, 1.06), (0.025,) * 3, M["brass"])
        # window
        obj("window_sky", "cube", (1.45, BY - 0.02, 0.95), (0.9, 0.02, 0.8), M["sky"])
        obj("window_frame_t", "rcube", (1.45, BY - 0.05, 1.37), (1.0, 0.08, 0.06), M["porcelain"], b=0.2)
        obj("window_frame_b", "rcube", (1.45, BY - 0.08, 0.53), (1.05, 0.14, 0.06), M["porcelain"], b=0.2)
        obj("window_frame_m", "cube", (1.45, BY - 0.05, 0.95), (0.04, 0.05, 0.8), M["porcelain"])
        obj("window_frame_l", "cube", (0.97, BY - 0.05, 0.95), (0.05, 0.08, 0.86), M["porcelain"])
        obj("window_frame_r", "cube", (1.93, BY - 0.05, 0.95), (0.05, 0.08, 0.86), M["porcelain"])
        for i, x in enumerate((1.2, 1.7)):
            obj(f"potplant{i}", "cylinder", (x, BY - 0.12, 0.62), (0.07, 0.07, 0.12), M["terracotta"])
            obj(f"plant{i}", "sphere", (x, BY - 0.12, 0.74), (0.1, 0.09, 0.09), M["green"])
        # shelf with jars
        obj("shelf", "rcube", (-0.0, BY - 0.12, 0.75), (0.01, 0.01, 0.01), M["wood"])
        jars = [M["pink"], M["purple"], M["orange"], M["bluebowl"], M["redpot"]]
        for i in range(5):
            x = 2.85 + i * 0.13 - 0.3
            obj(f"jar{i}", "cylinder", (x, BY - 0.35, 0.09), (0.05, 0.05, 0.18 + 0.03 * (i % 2)), jars[i])
            obj(f"jarlid{i}", "cylinder", (x, BY - 0.35, 0.2 + 0.015 * (i % 2)), (0.052, 0.052, 0.03), M["brass"])
        # stove pot on back counter
        obj("bpot", "cylinder", (0.2, BY - 0.35, 0.13), (0.2, 0.2, 0.26), M["bluebowl"])
        obj("bpotlid", "sphere", (0.2, BY - 0.35, 0.26), (0.205, 0.205, 0.05), M["steel"])
        # hanging utensils rail
        obj("rail", "cylinder", (2.8, BY - 0.06, 0.62), (0.012, 0.012, 1.0), M["brass"], rot=(0, math.pi / 2, 0))
        for i in range(4):
            x = 2.45 + i * 0.24
            obj(f"ladle{i}", "cylinder", (x, BY - 0.07, 0.48), (0.008, 0.008, 0.26), M["steel"])
            obj(f"ladleh{i}", "sphere", (x, BY - 0.08, 0.34), (0.045, 0.045, 0.03), M["steel"])
        # door to the rest of the house (left side of back wall)
        self.door_pivot = empty("door_pivot", (-2.6, BY - 0.02, FLOOR_Z))
        obj("door", "rcube", (0.45, 0, 1.0), (0.9, 0.06, 2.0), M["door"], self.door_pivot, b=0.03)
        obj("door_knob", "sphere", (0.8, -0.06, 0.95), (0.04,) * 3, M["brass"], self.door_pivot)
        obj("door_hole", "cube", (-2.15, BY + 0.03, FLOOR_Z + 1.0), (0.92, 0.1, 2.02),
            new_mat("hall", (1.0, 0.85, 0.6), emit=(1.0, 0.85, 0.6), emit_str=1.2))
        obj("door_frame", "cube", (-2.15, BY - 0.03, FLOOR_Z + 2.04), (1.05, 0.08, 0.07), M["porcelain"])
        # a lamp
        obj("lampcord", "cylinder", (0.0, 0.0, 2.6), (0.006, 0.006, 1.6), M["steel"])
        obj("lampshade", "cone", (0.0, 0.0, 1.75), (0.3, 0.3, 0.25), M["redpot"], r2=0.35)

    # ------------------------------------------------------------------ props
    def build_props(self):
        M = self.M
        P = self.props = {}
        # stool (scene 1)
        st = P["stool"] = empty("stool")  # tall bar stool standing on the floor
        obj("stool_seat", "cylinder", (0, 0, 0.765), (0.17, 0.17, 0.05), M["stool"], st)
        obj("stool_ring", "torus", (0, 0, 0.3), (0.13, 0.13, 0.13), M["brass"], st, r=0.08)
        for k in range(4):
            a = k * 2 * math.pi / 4 + 0.78
            obj(f"stool_leg{k}", "cylinder", (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.37), (0.018, 0.018, 0.76), M["wood"], st,
                rot=(math.sin(a) * 0.08, -math.cos(a) * 0.08, 0))
        # mixing bowl
        b = P["bowl"] = empty("bowl")
        prof = [(0.0, 0.0), (0.07, 0.0), (0.12, 0.02), (0.16, 0.06), (0.18, 0.11), (0.185, 0.14)]
        obj("bowl_shell", "bowl", (0, 0, 0), (1, 1, 1), M["bluebowl"], b, prof=tuple(prof))
        obj("bowl_rim", "torus", (0, 0, 0.14), (0.185, 0.185, 0.185), M["bluebowl"], b, r=0.05)
        P["batter"] = obj("bowl_batter", "sphere", (0, 0, 0.1), (0.165, 0.165, 0.03), M["egg"], b)
        # whisk/spoon
        sp = P["spoon"] = empty("spoon")
        obj("spoon_handle", "cylinder", (0, 0, 0.12), (0.012, 0.012, 0.24), M["wood"], sp)
        obj("spoon_head", "sphere", (0, 0, 0.0), (0.035, 0.012, 0.05), M["wood"], sp)
        # flour bag
        fb = P["flourbag"] = empty("flourbag")
        obj("flourbag_body", "rcube", (0, 0, 0.14), (0.17, 0.11, 0.28), M["kraft"], fb, b=0.25)
        obj("flourbag_top", "rcube", (0, 0, 0.3), (0.16, 0.04, 0.06), M["kraft"], fb, b=0.3)
        obj("flourbag_wheat", "sphere", (0, -0.056, 0.14), (0.045, 0.005, 0.07), M["yellow"], fb)
        # eggs
        P["eggs"] = [obj(f"egg{i}", "sphere", (0, 0, 0), (0.028, 0.028, 0.036), M["egg"]) for i in range(3)]
        # tomatoes
        P["tomatoes"] = []
        for i in range(6):
            t = empty(f"tomato{i}")
            obj(f"tomato_b{i}", "sphere", (0, 0, 0), (0.042, 0.042, 0.037), M["tomato"], t)
            obj(f"tomato_s{i}", "cone", (0, 0, 0.036), (0.022, 0.022, 0.012), M["stem"], t)
            P["tomatoes"].append(t)
        # big pot with lid (spaghetti pot) and empty pot (landing pot)
        for name, mat, r, h in (("pot", M["redpot"], 0.21, 0.3), ("pot2", M["steel"], 0.2, 0.26)):
            p = P[name] = empty(name)
            prof = [(0.0, 0.0), (r * 0.95, 0.0), (r, 0.02), (r, h)]
            obj(f"{name}_shell", "bowl", (0, 0, 0), (1, 1, 1), mat, p, prof=tuple(prof))
            obj(f"{name}_rim", "torus", (0, 0, h), (r, r, r), mat, p, r=0.06)
            obj(f"{name}_inside", "cylinder", (0, 0, 0.02), (r * 0.97, r * 0.97, 0.01),
                new_mat(f"{name}_in", (0.25, 0.25, 0.28), rough=0.3, metal=0.8), p)
            for s in (-1, 1):
                obj(f"{name}_handle{s}", "torus", (s * (r + 0.02), 0, h * 0.82), (0.035, 0.02, 0.03), M["steel"], p,
                    rot=(math.pi / 2, 0, 0), r=0.3)
            P[name + "_h"] = h
        lid = P["lid"] = empty("lid")
        obj("lid_dome", "sphere", (0, 0, 0), (0.225, 0.225, 0.05), M["steel"], lid)
        obj("lid_knob", "sphere", (0, 0, 0.055), (0.03, 0.03, 0.022), M["redpot"], lid)
        # sauce jar
        j = P["jar"] = empty("saucejar")
        obj("jar_sauce", "cylinder", (0, 0, 0.2), (0.13, 0.13, 0.4), M["sauce"], j)
        obj("jar_lid", "cylinder", (0, 0, 0.415), (0.125, 0.125, 0.05), M["yellow"], j)
        obj("jar_label", "cylinder", (0, 0, 0.2), (0.132, 0.132, 0.1), M["porcelain"], j)
        # plate
        pl = P["plate"] = empty("plate")
        prof = [(0.0, 0.0), (0.16, 0.0), (0.19, 0.012), (0.25, 0.03), (0.26, 0.035)]
        obj("plate_shell", "bowl", (0, 0, 0.005), (1, 1, 1), M["porcelain"], pl, prof=tuple(prof))
        obj("plate_rim", "torus", (0, 0, 0.04), (0.255, 0.255, 0.255), new_mat("plate_rim", (0.3, 0.6, 1.0), rough=0.1, coat=1.0), pl, r=0.025)
        # fork (oversized)
        fk = P["fork"] = empty("fork")
        obj("fork_handle", "rcube", (0, 0, -0.17), (0.03, 0.012, 0.3), M["steel"], fk, b=0.4)
        obj("fork_neck", "rcube", (0, 0, 0.0), (0.06, 0.012, 0.06), M["steel"], fk, b=0.3)
        for k in range(4):
            obj(f"fork_tine{k}", "rcube", (-0.03 + k * 0.02, 0, 0.07), (0.008, 0.008, 0.12), M["steel"], fk, b=0.4)
        # mom's tasting fork (normal size relative to her)
        mf = P["momfork"] = empty("momfork")
        obj("mf_handle", "rcube", (0, 0, -0.1), (0.018, 0.008, 0.2), M["steel"], mf, b=0.4)
        for k in range(3):
            obj(f"mf_tine{k}", "rcube", (-0.012 + k * 0.012, 0, 0.03), (0.005, 0.005, 0.06), M["steel"], mf, b=0.4)
        # flour patches (mess), flour cloud puffs
        P["patches"] = [obj(f"flourpatch{i}", "sphere", (0, 0, 0), (0.2, 0.16, 0.006), M["flour"]) for i in range(8)]
        P["puffs"] = [obj(f"puff{i}", "sphere", (0, 0, 0), (0.1,) * 3, M["flour"], u=24, v=14) for i in range(46)]
        P["dust"] = [obj(f"dust{i}", "sphere", (0, 0, 0), (0.008,) * 3, M["flour"], u=8, v=6) for i in range(40)]
        # plated spaghetti (scene 7+)
        self.dish = Dish(M)
        self.hide_all_props()

    def hide_all_props(self):
        P = self.props
        for k, v in P.items():
            if isinstance(v, list):
                for o in v:
                    place(o, None)
            elif hasattr(v, "location"):
                place(v, None)
        self.dish.show(False)


def _set_hide(o, hide):
    o.hide_render = hide
    for c in o.children:
        _set_hide(c, hide)


def place(o, loc, rot=(0, 0, 0), scale=None):
    """Show object at loc (or hide when loc is None)."""
    if loc is None:
        _set_hide(o, True)
        return
    _set_hide(o, False)
    o.location = loc
    o.rotation_euler = rot
    if scale is not None:
        o.scale = scale if hasattr(scale, "__len__") else (scale,) * 3


# ---------------------------------------------------------------------- noodle creature

class Noodle:
    """A living bundle of golden spaghetti: several strands braided around a spine,
    a curly 'mop' at the head and two cute eyes. Spine is set every frame."""

    def __init__(self, n=9, ring=0.035, thick=0.011, name="noodle"):
        self.mat = new_mat("pasta", (1.0, 0.66, 0.16), rough=0.22, coat=0.6, sss=0.25)
        self.n, self.ring = n, ring
        self.strands = [curve_obj(f"{name}_s{k}", 48, bevel=thick, material=self.mat) for k in range(n)]
        self.curls = [curve_obj(f"{name}_c{k}", 24, bevel=thick, material=self.mat) for k in range(5)]
        white = new_mat("nd_white", (1, 1, 1), rough=0.1, coat=1.0)
        black = new_mat("nd_black", (0.01, 0.01, 0.01), rough=0.1, coat=1.0)
        hl = new_mat("nd_hl", (1, 1, 1), emit=(1, 1, 1), emit_str=6)
        blush = new_mat("nd_blush", (1.0, 0.45, 0.45), rough=0.5)
        line = new_mat("nd_line", (0.45, 0.2, 0.05), rough=0.5)
        self.headE = empty(f"{name}_head")
        self.eyes = []
        self.pupils = []
        for s in (-1, 1):
            e = obj(f"{name}_eye{s}", "sphere", (s * 0.036, -0.03, 0.03), (0.03, 0.022, 0.034), white, self.headE)
            p = obj(f"{name}_pupil{s}", "sphere", (0, -0.85, 0.05), (0.55, 0.3, 0.6), black, e)
            obj(f"{name}_hl{s}", "sphere", (0.3, -0.75, 0.4), (0.25, 0.2, 0.25), hl, p)
            obj(f"{name}_blush{s}", "sphere", (s * 0.065, -0.02, -0.012), (0.018, 0.006, 0.01), blush, self.headE)
            self.eyes.append(e)
            self.pupils.append(p)
        self.smile = curve_obj(f"{name}_smile", 5, bevel=0.004, material=line, parent=self.headE)
        set_curve_points(self.smile, [(-0.025, -0.05, -0.012), (-0.012, -0.056, -0.022), (0, -0.057, -0.025),
                                      (0.012, -0.056, -0.022), (0.025, -0.05, -0.012)])
        self.visible(False)

    def visible(self, v):
        for o in self.strands + self.curls:
            o.hide_render = not v
        _set_hide(self.headE, not v)

    def set(self, spine, t=0.0, look=(0, 0), blink=1.0, ring=None, face_dir=None, eyes_scale=1.0,
            show_curls=True, strands=None, head_up=None):
        """spine: list of points from tail to head (world coords)."""
        ring = self.ring if ring is None else ring
        pts = resample(spine, 48)
        n = len(pts)
        tangents = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
        up = Vector((0, 0, 1))
        frames = []
        nrm = (up - tangents[0] * tangents[0].dot(up))
        if nrm.length < 1e-4:
            nrm = Vector((1, 0, 0))
        nrm.normalize()
        for i in range(n):  # parallel transport
            T = tangents[i]
            nrm = (nrm - T * T.dot(nrm))
            if nrm.length < 1e-5:
                nrm = T.orthogonal()
            nrm.normalize()
            frames.append((nrm.copy(), T.cross(nrm)))
        count = self.n if strands is None else strands
        for k, cobj in enumerate(self.strands):
            if k >= count:
                cobj.hide_render = True
                continue
            cobj.hide_render = False
            out = []
            ph = 2 * math.pi * k / self.n
            for i in range(n):
                u = i / (n - 1)
                taper = math.sin(min(1.0, u * 1.0 + 0.12) * math.pi) ** 0.5
                rr = ring * (0.35 + 0.65 * taper) * (1 + 0.25 * math.sin(k * 1.7 + u * 9 + t * 3))
                a = ph + u * 11.0 + t * 1.5
                N, B = frames[i]
                out.append(pts[i] + N * math.cos(a) * rr + B * math.sin(a) * rr)
            set_curve_points(cobj, out)
        head = pts[-1]
        T = tangents[-1]
        # head orientation: face toward face_dir (horizontal) with up = world up
        fd = Vector(face_dir) if face_dir is not None else Vector((T.x, T.y, 0))
        if fd.length < 1e-4:
            fd = Vector((0, -1, 0))
        fd.normalize()
        self.headE.location = head + (Vector(head_up) if head_up is not None else Vector((0, 0, ring * 0.9)))
        ang = math.atan2(fd.x, -fd.y)
        self.headE.rotation_euler = (0, 0, ang)
        self.headE.scale = (eyes_scale,) * 3
        for e, p in zip(self.eyes, self.pupils):
            e.scale = (0.03, 0.022, 0.034 * max(0.08, blink))
            p.location = (look[0] * 0.35, -0.85, 0.05 + look[1] * 0.35)
        # curly mop around the head
        for k, c in enumerate(self.curls):
            c.hide_render = not show_curls
            if not show_curls:
                continue
            cp = []
            base = 2 * math.pi * k / len(self.curls)
            for i in range(24):
                u = i / 23
                a = base + u * 2 * math.pi * 1.2 + t * (1 + 0.2 * k)
                r = ring * (1.2 + 0.6 * math.sin(u * math.pi)) * (1 + 0.15 * math.sin(t * 4 + k))
                off = Vector((math.cos(a) * r, math.sin(a) * r * 0.8, (u - 0.5) * ring * 1.4 + 0.25 * ring * math.sin(a * 2)))
                cp.append(head - T * ring * 0.8 + off)
            set_curve_points(c, cp)


class Dish:
    """The finished spaghetti: a twirled nest (grow via bevel_factor_end), sauce, basil."""

    def __init__(self, M):
        pasta = new_mat("pasta_dish", (1.0, 0.68, 0.18), rough=0.22, coat=0.6, sss=0.25)
        self.root = empty("dish")
        self.loops = []
        R = rng(7)
        for k in range(26):
            c = curve_obj(f"nest{k}", 40, bevel=0.0065, material=pasta, parent=self.root)
            pts = []
            r0 = 0.07 + 0.11 * R.random()
            zc = 0.04 + 0.075 * (1 - r0 / 0.19) + R.uniform(-0.01, 0.01)
            a0 = R.random() * 6.28
            tilt = R.uniform(-0.35, 0.35)
            for i in range(40):
                a = a0 + i / 39 * 2 * math.pi * 1.4
                r = r0 * (1 - 0.25 * i / 39)
                pts.append((math.cos(a) * r, math.sin(a) * r, zc + math.sin(a + tilt * 3) * 0.02 * r / 0.19 + tilt * 0.03 * math.cos(a)))
            set_curve_points(c, pts)
            self.loops.append(c)
        self.sauce = obj("dish_sauce", "sphere", (0, 0, 0.115), (0.085, 0.085, 0.035), M["sauce"], self.root)
        self.drops = []
        for k in range(5):
            a = k * 1.256 + 0.3
            d = obj(f"dish_drop{k}", "sphere", (math.cos(a) * 0.07, math.sin(a) * 0.07, 0.1), (0.03, 0.02, 0.018), M["sauce"], self.root,
                    rot=(0, 0, a))
            self.drops.append(d)
        self.basil = empty("basil", (0.0, -0.01, 0.15), self.root)
        for s in (-1, 1):
            obj(f"basil_leaf{s}", "sphere", (s * 0.022, 0, 0), (0.028, 0.014, 0.004), M["basil"], self.basil, rot=(0.15, s * 0.25, s * 0.5))
        self.cheese = []
        R = rng(3)
        cheese_m = new_mat("parm", (1.0, 0.97, 0.85), rough=0.6)
        for k in range(14):
            a = R.random() * 6.28
            r = R.random() * 0.06
            self.cheese.append(obj(f"parm{k}", "cube", (math.cos(a) * r, math.sin(a) * r, 0.145 + R.random() * 0.01),
                                   (0.006, 0.006, 0.004), cheese_m, self.root, rot=(R.random(), R.random(), R.random())))

    def show(self, v):
        _set_hide(self.root, not v)

    def set(self, grow=1.0, sauce=1.0, basil=1.0, cheese=1.0, spin=0.0):
        self.root.rotation_euler = (0, 0, spin)
        for k, c in enumerate(self.loops):
            f = clamp(grow * len(self.loops) - k)
            c.hide_render = f <= 0.01
            c.data.bevel_factor_end = max(0.01, f)
        self.sauce.hide_render = sauce < 0.02
        s = max(sauce, 1e-3)
        self.sauce.scale = (0.085 * s, 0.085 * s, 0.035 * min(1.0, s * 1.2))
        for d in self.drops:
            d.hide_render = sauce < 0.6
        self.basil.hide_render = basil < 0.01
        for c in self.basil.children:
            c.hide_render = basil < 0.01
        self.basil.location.z = 0.15 + 0.3 * (1 - basil) ** 2
        self.basil.rotation_euler = (0, 0, (1 - basil) * 6)
        for c in self.cheese:
            c.hide_render = cheese < 0.5


# ---------------------------------------------------------------------- lights / camera / render

def lights_and_world(intensity=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("world")
    sc.world = w
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.75, 0.85, 1.0, 1)
    bg.inputs["Strength"].default_value = 0.3
    def area(name, loc, rot, energy, color, size):
        L = bpy.data.lights.new(name, "AREA")
        L.energy = energy * intensity
        L.color = color
        L.size = size
        o = bpy.data.objects.new(name, L)
        link(o)
        o.location = loc
        o.rotation_euler = rot
        return o
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 2.2 * intensity
    sun.color = (1.0, 0.9, 0.72)
    sun.angle = math.radians(8)
    so = bpy.data.objects.new("sun", sun)
    link(so)
    so.rotation_euler = (math.radians(50), math.radians(-25), math.radians(160))
    key = area("key", (-1.6, -2.2, 1.9), (math.radians(60), 0, math.radians(-35)), 130, (1.0, 0.92, 0.82), 2.0)
    fill = area("fill", (2.2, -1.8, 1.0), (math.radians(70), 0, math.radians(50)), 45, (0.8, 0.9, 1.0), 2.5)
    rim = area("rim", (0.5, 2.0, 1.6), (math.radians(-60), 0, math.radians(180)), 110, (1.0, 0.85, 0.6), 1.5)
    return dict(sun=so, key=key, fill=fill, rim=rim)


def camera():
    cd = bpy.data.cameras.new("cam")
    cd.lens = 35
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 24
    cd.clip_start = 0.01
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 4.0
    c = bpy.data.objects.new("cam", cd)
    link(c)
    bpy.context.scene.camera = c
    return c


def aim(cam, loc, target, lens=35, roll=0.0, fstop=None, shake=(0, 0, 0)):
    loc = Vector(loc) + Vector(shake)
    target = Vector(target)
    d = target - loc
    q = d.to_track_quat("-Z", "Y")
    cam.location = loc
    e = q.to_euler()
    cam.rotation_euler = e
    if roll:
        cam.rotation_mode = "XYZ"
        from mathutils import Matrix
        cam.matrix_world = cam.matrix_world @ Matrix.Rotation(roll, 4, "Z")
    cam.data.lens = lens
    cam.data.dof.focus_distance = d.length
    if fstop:
        cam.data.dof.aperture_fstop = fstop


def render_settings(width, height, samples, fast=False):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.04
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 4
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x = width
    sc.render.resolution_y = height
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Punchy"
    except Exception:
        try:
            sc.view_settings.look = "Punchy"
        except Exception:
            pass
    sc.render.fps = 30
