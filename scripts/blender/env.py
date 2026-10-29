"""School yard environment: building, plaza, garden path, big tree with breakable branch, props, weather."""
import math
import random
import bpy
from mathutils import Vector

import geo
import mats
from mats import hexc

R = random.Random(7)


class Env:
    def __init__(self, wet=False, detail=1.0, garden=True, school=True, puddles=None):
        self.wet = wet
        self.detail = detail
        self.objs = {}
        self._materials()
        self.ground()
        if school:
            self.school()
        self.plaza_props()
        if garden:
            self.garden()
        self.background()
        if puddles if puddles is not None else wet:
            self.puddles()

    # ------------------------------------------------------------ materials
    def _materials(self):
        w = self.wet
        self.M = M = {}
        M["grass"] = mats.noisy("grass", hexc("#3f7a26" if not w else "#346a20"), hexc("#9cc457" if not w else "#78a842"),
                                scale=0.6, rough=0.9 if not w else 0.55, bump=0.4, detail=8)
        M["path"] = self._paving(w)
        M["plaster"] = mats.noisy("plaster", hexc("#f2e3c6"), hexc("#e6cfa8"), scale=2.0, rough=0.85, bump=0.08)
        M["plaster2"] = mats.noisy("plaster2", hexc("#e9b98a"), hexc("#dca777"), scale=2.0, rough=0.85, bump=0.08)
        M["roof"] = self._roof()
        M["trim"] = mats.basic("trim", hexc("#fbf8f1"), rough=0.5)
        M["glass"] = mats.basic("glass", hexc("#2b4a66"), rough=0.05, coat=1.0, emission=hexc("#ffd9a0"), emit_strength=0.25)
        M["door"] = mats.wood("door", hexc("#6e3f22"), hexc("#8a5530"), scale=2.0, rough=0.5)
        M["stone"] = mats.noisy("stone", hexc("#a49a8c"), hexc("#cfc6b6"), scale=3.0, rough=0.85 if not w else 0.4, bump=0.6)
        M["bark"] = self._bark()
        M["drybark"] = mats.noisy("drybark", hexc("#5a4632"), hexc("#8a7358"), scale=6.0, rough=0.9, bump=0.8)
        M["leaf"] = mats.noisy("leaf", hexc("#2f6a22"), hexc("#7fb346"), scale=2.5, rough=0.6, bump=0.5, detail=4)
        M["leaf2"] = mats.noisy("leaf2", hexc("#3d7a2a"), hexc("#a3c455"), scale=2.5, rough=0.6, bump=0.5, detail=4)
        M["hedge"] = mats.noisy("hedge", hexc("#2a5a20"), hexc("#5d9a38"), scale=3.0, rough=0.7, bump=0.8, detail=6)
        M["dryleaf"] = mats.noisy("dryleaf", hexc("#a0622a"), hexc("#d79a45"), scale=8.0, rough=0.7, bump=0.2)
        M["board"] = mats.wood("board", hexc("#a8763e"), hexc("#d2a463"), scale=4.0, rough=0.6)
        M["metal"] = mats.basic("metal", hexc("#2d3238"), rough=0.35, metal=0.8)
        M["bench"] = mats.wood("bench", hexc("#9c5a2c"), hexc("#c27a3c"), scale=3.0, rough=0.5)
        M["lamp"] = mats.basic("lampglass", hexc("#fff4d8"), rough=0.2, emission=hexc("#ffe2a8"), emit_strength=2.0)
        M["water"] = mats.basic("puddle", hexc("#5c6670"), rough=0.02, coat=1.0, spec=0.8)
        M["soil"] = mats.noisy("soil", hexc("#4a3424"), hexc("#6b4b32"), scale=6.0, rough=0.9 if not w else 0.5, bump=0.5)
        M["hill"] = mats.noisy("hill", hexc("#6f9a4a"), hexc("#9cbf62"), scale=0.3, rough=0.9, bump=0.0)
        M["far"] = mats.noisy("fartree", hexc("#4a7a3a"), hexc("#7aa456"), scale=1.5, rough=0.9, bump=0.0)
        for c in ("#f6d84a", "#f27a8a", "#ffffff", "#b58ce6", "#ff9f43"):
            M["flower" + c] = mats.basic("flower" + c, hexc(c), rough=0.5, sheen=0.4)
        M["flowerc"] = mats.basic("flowerc", hexc("#f2b33a"), rough=0.5)

    def _paving(self, wet):
        m = bpy.data.materials.new("paving")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        v = nt.nodes.new("ShaderNodeTexVoronoi")
        v.feature = "DISTANCE_TO_EDGE"
        v.inputs["Scale"].default_value = 5.0
        nt.links.new(tc.outputs["Object"], v.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].position = 0.035
        ramp.color_ramp.elements[0].color = hexc("#8a7c6a" if not wet else "#4a4038")
        ramp.color_ramp.elements[1].color = hexc("#d8c6a6" if not wet else "#a8977c")
        nt.links.new(v.outputs["Distance"], ramp.inputs["Fac"])
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 6.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 0.35
        nt.links.new(ramp.outputs["Color"], mix.inputs[6])
        nt.links.new(nz.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.5
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Max"].default_value = 0.04
        nt.links.new(v.outputs["Distance"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Roughness"].default_value = 0.75 if not wet else 0.38
        b.inputs["Specular IOR Level"].default_value = 0.5
        return m

    def _roof(self):
        m = bpy.data.materials.new("roof")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        bt = nt.nodes.new("ShaderNodeTexBrick")
        bt.inputs["Scale"].default_value = 3.0
        bt.inputs["Color1"].default_value = hexc("#b5502f")
        bt.inputs["Color2"].default_value = hexc("#9a4027")
        bt.inputs["Mortar"].default_value = hexc("#6a2a18")
        bt.inputs["Mortar Size"].default_value = 0.015
        nt.links.new(tc.outputs["UV"] if False else tc.outputs["Object"], bt.inputs["Vector"])
        nt.links.new(bt.outputs["Color"], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.4
        nt.links.new(bt.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Roughness"].default_value = 0.6 if not self.wet else 0.5
        return m

    def _bark(self):
        m = bpy.data.materials.new("bark")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (6.0, 6.0, 1.0)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        w = nt.nodes.new("ShaderNodeTexWave")
        w.wave_type = "BANDS"
        w.bands_direction = "X"
        w.inputs["Scale"].default_value = 3.0
        w.inputs["Distortion"].default_value = 8.0
        w.inputs["Detail"].default_value = 6.0
        nt.links.new(mp.outputs["Vector"], w.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = hexc("#3b2a1c")
        ramp.color_ramp.elements[1].color = hexc("#7a5c40")
        nt.links.new(w.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.9
        nt.links.new(w.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Roughness"].default_value = 0.9
        return m

    # --------------------------------------------------------------- ground
    def ground(self):
        M = self.M
        g = geo.box("ground", (0, 0, -0.05), (160, 160, 0.1), M["grass"])
        plaza = geo.box("plaza", (0, 7.6, 0.0), (15, 9.2, 0.04), M["path"], bevel=0.02)
        path = geo.box("path", (0, -9.0, 0.0), (2.3, 24.0, 0.04), M["path"], bevel=0.02)
        # kerb stones
        for sx in (-1, 1):
            geo.box(f"kerb{sx}", (1.2 * sx, -9.0, 0.03), (0.14, 24.0, 0.08), M["stone"], bevel=0.02)
        self.objs["path"] = path

    # --------------------------------------------------------------- school
    def school(self):
        M = self.M
        y0 = 12.0
        geo.box("school_body", (0, y0 + 4, 2.3), (14, 8, 4.6), M["plaster"])
        geo.box("school_plinth", (0, y0 + 4, 0.3), (14.2, 8.2, 0.6), M["stone"])
        geo.box("school_cornice", (0, y0 + 4, 4.62), (14.4, 8.4, 0.18), M["trim"], bevel=0.03)
        # gable roof
        import bmesh
        bm = bmesh.new()
        w, d, h = 7.6, 4.6, 2.4
        vs = [bm.verts.new(v) for v in ((-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0), (-w, 0, h), (w, 0, h))]
        for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)):
            bm.faces.new([vs[i] for i in f])
        roof = geo._mesh_obj("school_roof", bm, M["roof"], smooth=False)
        roof.location = (0, y0 + 4, 4.7)
        # central entrance block (warmer colour)
        geo.box("entrance_block", (0, y0 - 0.25, 2.6), (3.6, 0.6, 5.2), M["plaster2"])
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in ((-2.1, -0.5, 0), (2.1, -0.5, 0), (2.1, 0.5, 0), (-2.1, 0.5, 0), (0, -0.5, 1.4), (0, 0.5, 1.4))]
        for f in ((0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4), (0, 3, 2, 1)):
            bm.faces.new([vs[i] for i in f])
        gable = geo._mesh_obj("entrance_gable", bm, M["roof"], smooth=False)
        gable.location = (0, y0 - 0.3, 5.2)
        # round window (decorative) above door - no text, simple
        geo.cylinder("ent_round", (0, y0 - 0.56, 4.3), 0.42, 0.06, M["glass"], rot=(math.pi / 2, 0, 0), seg=40)
        geo.torus("ent_round_frame", (0, y0 - 0.6, 4.3), 0.44, 0.05, M["trim"], rot=(math.pi / 2, 0, 0))
        # door
        geo.box("door_frame", (0, y0 - 0.56, 1.3), (1.9, 0.1, 2.7), M["trim"], bevel=0.03)
        for sx in (-1, 1):
            geo.box(f"door{sx}", (0.42 * sx, y0 - 0.62, 1.22), (0.8, 0.08, 2.35), M["door"], bevel=0.02)
            geo.sphere(f"doorknob{sx}", (0.1 * sx, y0 - 0.7, 1.15), (0.05, 0.05, 0.05), M["metal"])
        geo.cylinder("door_arch", (0, y0 - 0.6, 2.4), 0.95, 0.12, M["trim"], rot=(math.pi / 2, 0, 0), seg=40)
        # steps
        for i in range(3):
            geo.box(f"step{i}", (0, y0 - 0.9 - i * 0.32, 0.09 + (2 - i) * 0.12), (2.8 + i * 0.4, 0.34 + 0.0, 0.18 + (2 - i) * 0.24), M["stone"], bevel=0.02)
        # windows
        for x in (-5.6, -3.6, 3.6, 5.6):
            for z in (1.7, 3.6):
                self._window(f"win_{x}_{z}", (x, y0 - 0.02, z))
        # flower boxes under ground floor windows
        for x in (-5.6, -3.6, 3.6, 5.6):
            geo.box(f"fbox{x}", (x, y0 - 0.2, 0.95), (1.2, 0.3, 0.25), M["door"], bevel=0.02)
            for k in range(6):
                c = ("#f27a8a", "#f6d84a", "#ffffff", "#b58ce6")[k % 4]
                geo.sphere(f"fbf{x}_{k}", (x - 0.5 + k * 0.2, y0 - 0.22, 1.13), (0.08, 0.08, 0.07), M["flower" + c], seg=10, rings=6)
        # small bell tower on roof
        geo.box("tower", (0, y0 + 2.5, 7.2), (1.2, 1.2, 1.6), M["plaster"])
        geo.cone("tower_roof", (0, y0 + 2.5, 8.55), 1.0, 0.0, 1.2, M["roof"], seg=4, rot=(0, 0, math.pi / 4))
        geo.cylinder("tower_win", (0, y0 + 1.88, 7.25), 0.34, 0.06, M["glass"], rot=(math.pi / 2, 0, 0), seg=40)
        geo.torus("tower_win_f", (0, y0 + 1.86, 7.25), 0.36, 0.045, M["trim"], rot=(math.pi / 2, 0, 0))
        # wall lamps
        for sx in (-1, 1):
            geo.box(f"wlamp{sx}", (1.35 * sx, y0 - 0.7, 2.6), (0.18, 0.18, 0.3), M["lamp"], bevel=0.03)
        # drainpipes
        for sx in (-1, 1):
            geo.cylinder(f"pipe{sx}", (6.9 * sx, y0 - 0.1, 2.3), 0.07, 4.6, M["metal"], seg=12)

    def _window(self, name, loc):
        M = self.M
        x, y, z = loc
        geo.box(name + "_frame", (x, y - 0.03, z), (1.15, 0.12, 1.45), M["trim"], bevel=0.03)
        geo.box(name + "_glass", (x, y - 0.06, z), (0.95, 0.1, 1.25), M["glass"])
        geo.box(name + "_mull", (x, y - 0.12, z), (0.06, 0.04, 1.25), M["trim"])
        geo.box(name + "_mull2", (x, y - 0.12, z + 0.15), (0.95, 0.04, 0.06), M["trim"])
        geo.box(name + "_sill", (x, y - 0.15, z - 0.76), (1.3, 0.25, 0.08), M["trim"], bevel=0.02)

    # ----------------------------------------------------------- props
    def plaza_props(self):
        M = self.M
        # benches
        self._bench("bench1", (-4.8, 6.5), 0.0)
        self._bench("bench2", (4.8, 6.0), 0.0)
        # lamp posts along path
        for i, y in enumerate((-12.5, -3.0, 4.0)):
            for sx in (-1, 1):
                if y == 4.0 and sx == 1:
                    continue
                self._lamp(f"lamp{i}{sx}", (1.65 * sx, y))
        # planters on plaza
        for x, y in ((-6.3, 10.6), (6.3, 10.6), (-2.6, 10.9), (2.6, 10.9)):
            geo.cylinder(f"planter{x}{y}", (x, y, 0.3), 0.45, 0.6, M["stone"], seg=24)
            b = geo.sphere(f"plant{x}{y}", (x, y, 0.95), (0.55, 0.55, 0.6), M["hedge"], seg=16, rings=10)
            geo.displace(b, 0.15, 0.4)

    def _bench(self, name, pos, rot):
        M = self.M
        x, y = pos
        p = geo.empty(name, (x, y, 0), rot=(0, 0, rot))
        for i in range(3):
            geo.box(f"{name}_s{i}", (0, -0.15 + i * 0.15, 0.45), (1.6, 0.12, 0.05), M["bench"], p, bevel=0.01)
        for i in range(2):
            geo.box(f"{name}_b{i}", (0, 0.22, 0.65 + i * 0.16), (1.6, 0.05, 0.11), M["bench"], p, bevel=0.01)
        for sx in (-1, 1):
            geo.box(f"{name}_l{sx}", (0.7 * sx, 0.0, 0.22), (0.06, 0.45, 0.45), M["metal"], p)

    def _lamp(self, name, pos):
        M = self.M
        x, y = pos
        geo.cylinder(name + "_post", (x, y, 1.4), 0.055, 2.8, M["metal"], seg=12)
        geo.cylinder(name + "_base", (x, y, 0.12), 0.14, 0.24, M["metal"], seg=12)
        geo.box(name + "_head", (x, y, 2.95), (0.28, 0.28, 0.36), M["lamp"], bevel=0.03)
        geo.cone(name + "_cap", (x, y, 3.2), 0.24, 0.02, 0.16, M["metal"], seg=4, rot=(0, 0, math.pi / 4))

    # ----------------------------------------------------------- garden
    def garden(self):
        M = self.M
        # big tree beside the path (scenes 4-9)
        self.tree("bigtree", (-2.7, -6.4), 0.45, 3.4, 2.6, seed=3, main=True)
        # other trees
        for i, (x, y, s) in enumerate(((-6.0, -1.5, 0.8), (5.8, -2.5, 0.9), (-5.2, -13.0, 0.85), (6.0, -12.0, 0.8),
                                       (-9.5, 4.0, 1.0), (9.5, 3.0, 1.0), (-11, -8, 1.1), (11, -7, 1.0),
                                       (-9.0, 13.0, 1.1), (9.5, 14.0, 1.0))):
            self.tree(f"tree{i}", (x, y), 0.3 * s, 2.6 * s, 1.9 * s, seed=i + 10)
        # low stone garden wall on the right side of the path
        wall = geo.box("gwall", (2.35, -6.5, 0.27), (0.35, 9.0, 0.54), M["stone"], bevel=0.04)
        geo.box("gwall_top", (2.35, -6.5, 0.56), (0.45, 9.1, 0.07), M["stone"], bevel=0.02)
        self.objs["gwall"] = wall
        # hedge behind the wall and bushes
        for i, y in enumerate([-10.4 + k * 1.1 for k in range(9)]):
            b = geo.sphere(f"hedge{i}", (3.15, y, 0.55), (0.65, 0.7, 0.65), M["hedge"], seg=16, rings=10)
            geo.displace(b, 0.18, 0.35)
        # the bush that closes the rabbit's nook (north side)
        nb = geo.sphere("nookbush", (1.7, -4.75, 0.42), (0.62, 0.48, 0.5), M["hedge"], seg=20, rings=12)
        geo.displace(nb, 0.12, 0.3)
        for k in range(7):
            c = ("#f27a8a", "#ffffff", "#f6d84a")[k % 3]
            a = k * 0.9
            geo.sphere(f"nbf{k}", (1.7 + 0.55 * math.cos(a), -4.75 - 0.4 * abs(math.sin(a)) - 0.05, 0.45 + 0.3 * math.sin(a * 1.7)), (0.06, 0.06, 0.05), M["flower" + c], seg=10, rings=6)
        # flower beds on the left
        for i in range(3):
            x, y = -3.6, -11.5 + i * 3.4
            geo.box(f"bed{i}", (x, y, 0.06), (1.4, 2.4, 0.16), M["soil"], bevel=0.04)
            for k in range(18):
                c = ("#f6d84a", "#f27a8a", "#ffffff", "#b58ce6", "#ff9f43")[k % 5]
                self._flower(f"bf{i}_{k}", (x - 0.5 + (k % 3) * 0.5 + R.uniform(-0.1, 0.1), y - 1.0 + (k // 3) * 0.38 + R.uniform(-0.08, 0.08)), c)
        # flowers along the kerb of path
        for k in range(26):
            c = ("#f6d84a", "#ffffff", "#f27a8a", "#b58ce6")[k % 4]
            side = -1 if k % 2 else 1
            y = -14 + k * 0.62
            if side == 1 and -7.6 < y < -4.4:
                continue
            self._flower(f"kf{k}", (1.55 * side if side < 0 else 1.5, y), c, s=0.8)
        # rock (fulcrum) and the board
        rock = geo.sphere("rock", (1.35, -6.5, 0.12), (0.22, 0.17, 0.18), M["stone"], seg=16, rings=8)
        geo.displace(rock, 0.03, 0.2)
        self.objs["rock"] = rock
        bp = geo.empty("board_pivot", (0.85, -8.45, 0.03), rot=(0, 0, 0.5))
        geo.box("board", (0, 0, 0), (0.17, 1.6, 0.04), M["board"], bp, bevel=0.008)
        for k in range(3):
            geo.box(f"board_nail{k}", (0.0, -0.6 + k * 0.6, 0.021), (0.012, 0.012, 0.004), M["metal"], bp)
        self.objs["board"] = bp
        self.branch()
        # garden lawn tufts
        self.grass_tufts()

    def _flower(self, name, pos, color, s=1.0):
        M = self.M
        x, y = pos
        h = R.uniform(0.18, 0.3) * s
        geo.cylinder(name + "_st", (x, y, h / 2), 0.008, h, M["leaf"], seg=6)
        for k in range(5):
            a = k * 2 * math.pi / 5
            geo.sphere(f"{name}_p{k}", (x + 0.035 * s * math.cos(a), y + 0.035 * s * math.sin(a), h), (0.03 * s, 0.03 * s, 0.012 * s), M["flower" + color], seg=8, rings=4)
        geo.sphere(name + "_c", (x, y, h + 0.006), (0.018 * s, 0.018 * s, 0.012 * s), M["flowerc"], seg=8, rings=4)

    def tree(self, name, pos, r, h, crown, seed=0, main=False):
        M = self.M
        rr = random.Random(seed)
        x, y = pos
        root = geo.empty(name, (x, y, 0))
        pts = [(0, 0, -0.2), (0.05, 0.02, h * 0.4), (-0.05, 0.05, h * 0.75), (0.0, 0.0, h)]
        geo.tube(name + "_trunk", pts, [r * 1.35, r, r * 0.85, r * 0.7], M["bark"], root, ring=16)
        # roots flare
        for k in range(4):
            a = k * math.pi / 2 + rr.uniform(-0.3, 0.3)
            geo.tube(f"{name}_root{k}", [(0, 0, 0.35), (math.cos(a) * r * 1.4, math.sin(a) * r * 1.4, 0.05), (math.cos(a) * r * 2.0, math.sin(a) * r * 2.0, -0.05)],
                     [r * 0.5, r * 0.3, r * 0.1], M["bark"], root, ring=10)
        # limbs
        for k in range(4):
            a = k * math.pi / 2 + rr.uniform(-0.4, 0.4)
            p0 = (0, 0, h * 0.85)
            p1 = (math.cos(a) * crown * 0.5, math.sin(a) * crown * 0.5, h + crown * 0.4)
            geo.tube(f"{name}_limb{k}", [p0, p1], [r * 0.55, r * 0.25], M["bark"], root, ring=10)
        sway = geo.empty(name + "_crown", (0, 0, h), root)
        self.objs[name + "_crown"] = sway
        n = 9 if main else 6
        for k in range(n):
            a = rr.uniform(0, 2 * math.pi)
            d = rr.uniform(0.2, 0.75) * crown
            cz = rr.uniform(0.4, 1.3) * crown
            s = rr.uniform(0.55, 0.85) * crown
            b = geo.sphere(f"{name}_leaves{k}", (math.cos(a) * d, math.sin(a) * d, cz), (s, s, s * 0.85), M["leaf" if k % 2 else "leaf2"], sway, seg=24, rings=14)
            geo.displace(b, 0.3 * crown / 2.5, 0.22, subdiv=1)
        return root

    def branch(self):
        """Dry branch that breaks off the big tree. Modelled lying on the ground; pivot = broken heavy end."""
        M = self.M
        piv = geo.empty("branch_pivot", (-2.3, -6.15, 0.15))
        self.objs["branch"] = piv
        limb = [(0, 0, 0), (1.2, 0.05, -0.02), (2.4, 0.12, -0.05), (3.6, 0.15, -0.07), (4.6, 0.2, -0.09)]
        geo.tube("branch_limb", limb, [0.15, 0.13, 0.1, 0.075, 0.05], M["drybark"], piv, ring=14)
        for k in range(5):
            a = k * 2 * math.pi / 5
            geo.cone(f"branch_splinter{k}", (-0.03, 0.08 * math.cos(a), 0.08 * math.sin(a)), 0.035, 0.0, 0.16, M["drybark"], piv,
                     rot=(0, -math.pi / 2, 0), seg=6)
        rr = random.Random(21)
        twigs = [
            # side fork reaching north to the ground: closes the nook on the west
            [(2.85, 0.12, -0.04), (2.95, 0.5, 0.05), (3.0, 0.9, -0.02), (3.05, 1.15, -0.1)],
            [(3.05, 0.13, -0.04), (3.1, 0.35, 0.35), (3.2, 0.5, 0.7)],
        ]
        # thicket of dry twigs sticking up along the light end (rabbit can't pass)
        for k in range(9):
            x = 3.0 + k * 0.18
            zb = -0.05 - k * 0.004
            lean = rr.uniform(-0.35, 0.35)
            h = rr.uniform(0.55, 0.85)
            twigs.append([(x, 0.15, zb), (x + 0.05 + lean * 0.3, 0.15 + rr.uniform(-0.15, 0.25), zb + h * 0.5), (x + 0.1 + lean, 0.15 + rr.uniform(-0.3, 0.4), zb + h)])
        for k in range(4):
            x = 1.0 + k * 0.5
            twigs.append([(x, 0.08, -0.02), (x + 0.2, rr.uniform(-0.5, 0.5), 0.3), (x + 0.35, rr.uniform(-0.8, 0.8), rr.uniform(0.35, 0.6))])
        for i, t in enumerate(twigs):
            n = len(t)
            radii = [0.045, 0.03, 0.018, 0.012][:n] if i else [0.05, 0.04, 0.03, 0.02]
            geo.tube(f"branch_twig{i}", t, radii, M["drybark"], piv, ring=8)
            # sub-twigs and dry leaves
            ex, ey, ez = t[-1]
            mx, my, mz = t[-2]
            geo.tube(f"branch_sub{i}", [(mx, my, mz), (mx + rr.uniform(-0.2, 0.2), my + rr.uniform(-0.25, 0.25), mz + rr.uniform(0.15, 0.3))], [0.012, 0.006], M["drybark"], piv, ring=6)
            for k in range(3):
                lx, ly, lz = ex + rr.uniform(-0.12, 0.12), ey + rr.uniform(-0.12, 0.12), ez + rr.uniform(-0.08, 0.06)
                geo.sphere(f"branch_leaf{i}_{k}", (lx, ly, lz), (0.055, 0.032, 0.008), M["dryleaf"], piv, seg=8, rings=4,
                           rot=(rr.uniform(0, 1), rr.uniform(0, 1), rr.uniform(0, 3)))
        # stub on the tree where the branch broke off (visible after the fall)
        geo.cone("branch_stub", (-2.45, -6.15, 3.05), 0.13, 0.09, 0.3, M["drybark"], rot=(0, math.radians(70), 0), seg=10)
        return piv

    def grass_tufts(self, count=1600):
        """Instanced grass tufts on the lawns near the action."""
        M = self.M
        rr = random.Random(5)
        tuft = geo.empty("tuft_proto", (0, 0, -50))
        blades = []
        import bmesh
        bm = bmesh.new()
        for k in range(7):
            a = k * 2 * math.pi / 7 + rr.uniform(-0.3, 0.3)
            lean = rr.uniform(0.15, 0.35)
            h = rr.uniform(0.09, 0.16)
            bx, by = math.cos(a) * 0.02, math.sin(a) * 0.02
            v1 = bm.verts.new((bx - 0.008 * math.sin(a), by + 0.008 * math.cos(a), 0))
            v2 = bm.verts.new((bx + 0.008 * math.sin(a), by - 0.008 * math.cos(a), 0))
            v3 = bm.verts.new((bx + math.cos(a) * lean * h, by + math.sin(a) * lean * h, h))
            bm.faces.new((v1, v2, v3))
        proto = geo._mesh_obj("tuft_mesh", bm, M["leaf2"], smooth=False)
        proto.location = (0, 0, -50)
        coll = bpy.data.collections.new("tufts")
        bpy.context.scene.collection.children.link(coll)
        for k in range(count):
            # lawn strip between path and flower beds (left) and around tree
            if k % 2 == 0:
                x = rr.uniform(-5.0, -1.3)
            else:
                x = rr.uniform(1.3, 2.15)
            y = rr.uniform(-14.0, 2.0)
            if -4.4 < x < -2.8 and -12.7 < y < -3.4:
                continue
            ob = bpy.data.objects.new(f"tuft{k}", proto.data)
            coll.objects.link(ob)
            s = rr.uniform(0.8, 1.6)
            ob.location = (x, y, 0.0)
            ob.scale = (s, s, s)
            ob.rotation_euler = (0, 0, rr.uniform(0, 6.28))

    def background(self):
        M = self.M
        # hills and far tree line
        for i, (x, y, sx, sz) in enumerate(((-30, 50, 40, 8), (25, 60, 45, 10), (0, 75, 60, 12), (-60, 10, 30, 7), (60, 0, 30, 8), (0, -70, 60, 9), (-50, -40, 30, 8), (50, -45, 30, 8))):
            geo.sphere(f"hill{i}", (x, y, -sz * 0.35), (sx, sx * 0.6, sz), M["hill"], seg=32, rings=16)
        rr = random.Random(11)
        for k in range(46):
            a = rr.uniform(0, 2 * math.pi)
            d = rr.uniform(22, 34)
            x, y = math.cos(a) * d, math.sin(a) * d
            s = rr.uniform(2.0, 3.6)
            b = geo.sphere(f"fartree{k}", (x, y, s * 0.9), (s, s, s * 1.15), M["far"], seg=12, rings=8)
        # fence around the yard
        for k in range(40):
            for sx in (-1, 1):
                y = -18 + k * 0.8
                geo.box(f"fence{sx}_{k}", (8.0 * sx, y, 0.45), (0.08, 0.1, 0.9), M["trim"])
        for sx in (-1, 1):
            for z in (0.3, 0.7):
                geo.box(f"rail{sx}{z}", (8.0 * sx, -2.0, z), (0.05, 32.0, 0.07), M["trim"])

    def puddles(self):
        M = self.M
        rr = random.Random(3)
        spots = [(-0.4, -12.6, 0.9, 0.5), (-0.5, -10.5, 0.7, 0.4), (0.2, -3.0, 0.6, 0.35), (-0.6, 0.6, 0.55, 0.3), (3.5, 8.0, 1.1, 0.6), (-2.5, 6.5, 0.9, 0.5), (0.6, 9.2, 0.7, 0.4), (4.9, 10.3, 0.7, 0.35)]
        for i, (x, y, a, b) in enumerate(spots):
            p = geo.sphere(f"puddle{i}", (x, y, 0.021), (a, b, 0.002), M["water"], seg=32, rings=8)
            self.objs[f"puddle{i}"] = p

    # ---------------------------------------------------------- weather
    def rain(self, center=(0, 0), size=8.0, frames=(1, 140), count=6000, height=6.0):
        M = self.M
        dropm = mats.basic("raindrop", hexc("#dfeaf5"), rough=0.05, alpha=0.45, emission=hexc("#cfe0f0"), emit_strength=0.4)
        drop = geo.cylinder("drop_proto", (0, 0, -60), 0.006, 0.22, dropm, seg=6)
        drop.rotation_euler = (math.pi / 2, 0, 0)
        em = geo.box("rain_emitter", (center[0], center[1], height), (size, size, 0.01), None)
        em.hide_render = True
        ps = em.modifiers.new("rain", "PARTICLE_SYSTEM").particle_system
        st = ps.settings
        st.count = count
        st.frame_start = frames[0] - 40
        st.frame_end = frames[1]
        st.lifetime = 40
        st.emit_from = "FACE"
        st.normal_factor = 0.0
        st.object_align_factor = (0, 0, -9.0)
        st.render_type = "OBJECT"
        st.instance_object = drop
        st.particle_size = 1.0
        st.size_random = 0.4
        st.use_rotations = True
        st.rotation_mode = "VEL"
        st.effector_weights.gravity = 1.0
        st.physics_type = "NEWTON"
        em.show_instancer_for_render = False
        return em

    def flying_leaves(self, n=24, frames=(1, 120), area=((-3, 3), (-9, -3)), seed=1, wind=(4.0, 0.5)):
        M = self.M
        rr = random.Random(seed)
        leaves = []
        for k in range(n):
            ob = geo.sphere(f"fly_leaf{k}", (0, 0, 0), (0.05, 0.03, 0.006), M["dryleaf" if k % 3 else "leaf2"], seg=8, rings=4)
            x0 = rr.uniform(*area[0]) - wind[0] * 0.8
            y0 = rr.uniform(*area[1])
            z0 = rr.uniform(0.2, 3.5)
            f0, f1 = frames
            ph = rr.uniform(0, 6.28)
            for f in range(f0, f1 + 1, 4):
                t = (f - f0) / 30.0
                ob.location = (x0 + wind[0] * t + 0.3 * math.sin(t * 3 + ph), y0 + wind[1] * t + 0.2 * math.cos(t * 2 + ph), max(0.05, z0 - 0.35 * t + 0.25 * math.sin(t * 4 + ph)))
                ob.rotation_euler = (t * 5 + ph, t * 3, t * 4)
                ob.keyframe_insert("location", frame=f)
                ob.keyframe_insert("rotation_euler", frame=f)
            leaves.append(ob)
        return leaves

    def sway_trees(self, f0, f1, amp=1.0, period=40):
        for k, ob in self.objs.items():
            if not k.endswith("_crown"):
                continue
            ob.rotation_euler = (0, 0, 0)
            ob.keyframe_insert("rotation_euler", frame=f0)
            fc_list = ob.animation_data.action.fcurves
            for idx in (0, 1):
                fc = fc_list.find("rotation_euler", index=idx)
                m = fc.modifiers.new("NOISE")
                m.scale = period
                m.strength = 0.03 * amp
                m.phase = hash(k) % 100 + idx * 13
