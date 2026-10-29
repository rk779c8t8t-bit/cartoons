"""Animated props: umbrella, cleaning cloth."""
import math
import bpy
import geo
import mats
from mats import hexc


class Umbrella:
    def __init__(self, name="umbrella", color="#ffbf00"):
        self.M = mats.fabric(name + "_canvas", hexc(color), rough=0.55, weave=60)
        self.Mh = mats.basic(name + "_handle", hexc("#5a3a22"), rough=0.4, coat=0.5)
        self.Mt = mats.basic(name + "_tip", hexc("#d9d4c8"), rough=0.3, metal=0.6)
        self.root = geo.empty(name, (0, 0, 0))
        # shaft along +Z from hand (origin) up to canopy apex
        geo.cylinder(name + "_shaft", (0, 0, 0.45), 0.012, 0.9, self.Mt, self.root, seg=10)
        geo.tube(name + "_hook", [(0, 0, 0.02), (0, 0, -0.08), (0.03, 0, -0.13), (0.07, 0, -0.1)], [0.017] * 4, self.Mh, self.root, ring=10)
        self.canopy = geo.empty(name + "_canopy", (0, 0, 0.9), self.root)
        # 8 panel canopy (cone with scalloped look via 8 segments)
        geo.cone(name + "_cone", (0, 0, -0.16), 0.62, 0.02, 0.32, self.M, self.canopy, seg=8)
        for k in range(8):
            a = k * math.pi / 4
            geo.tube(f"{name}_rib{k}", [(0, 0, 0.0), (0.31 * math.cos(a), 0.31 * math.sin(a), -0.15), (0.62 * math.cos(a), 0.62 * math.sin(a), -0.33)], [0.006] * 3, self.Mt, self.canopy, ring=6)
            geo.sphere(f"{name}_ribtip{k}", (0.63 * math.cos(a), 0.63 * math.sin(a), -0.33), (0.012, 0.012, 0.012), self.Mt, self.canopy, seg=8, rings=4)
        geo.sphere(name + "_top", (0, 0, 0.02), (0.025, 0.025, 0.04), self.Mt, self.canopy, seg=10, rings=6)

    def key(self, frame, loc, rot=(0, 0, 0), open_=1.0):
        r = self.root
        r.location = loc
        r.rotation_euler = rot
        r.keyframe_insert("location", frame=frame)
        r.keyframe_insert("rotation_euler", frame=frame)
        c = self.canopy
        o = max(open_, 0.0)
        c.scale = (0.12 + 0.88 * o, 0.12 + 0.88 * o, 1.0 + 1.6 * (1 - o))
        c.keyframe_insert("scale", frame=frame)


def cloth(name="cloth", color="#e8f1fb"):
    m = mats.fabric(name + "_m", hexc(color), rough=0.9, weave=200)
    ob = geo.sphere(name, (0, 0, 0), (0.07, 0.05, 0.02), m, seg=12, rings=6)
    geo.displace(ob, 0.015, 0.05)
    return ob
