"""Procedural, rig-like animal characters built from primitives.

Each character is a hierarchy of empties (joints) with mesh parts. Animation is
keyframed through Actor.key(frame, **channels) which always keys *every* channel
so holds and transitions stay predictable.

Coordinates: character faces -Y, Z up. Character's left = +X.
"""
import math
import bpy
from mathutils import Vector

import geo
import mats
from mats import hexc

D2R = math.pi / 180.0

# ---------------------------------------------------------------------------
# Character definitions (single source of truth for the design – mirrors
# docs/character_bible.md)
# ---------------------------------------------------------------------------
CHARACTERS = {
    "ryzhik": dict(
        label="Ryzhik (kitten)", height=1.0,
        fur="#e9a25f", fur2="#fbe6c8", fur_tip="#ffd7a6", stripes="#cf7f3f",
        eye="#f2a52a", eye_dark="#7a3d06", nose="#f08a9a", inner_ear="#f5b3b8",
        ears="cat", muzzle="cat", tail="cat",
        outfit=dict(kind="jacket", color="#86b4d6", worn=0.6, worn_color="#b7d2e6", patch="#5d8fb8", buttons="#d9d2c0"),
        shoes=dict(kind="boots_worn", color="#7a4a2a", scuff="#b08460", sole="#3b2618"),
        backpack="#22336b", head_scale=(1.0, 0.95, 0.92), eye_r=0.074,
    ),
    "puppy": dict(
        label="Puppy (Druzhok)", height=0.98,
        fur="#efd9b4", fur2="#fff4e2", fur_tip="#fff3dc", patch="#a86a3a", ear_color="#9a5e33",
        eye="#7a4520", eye_dark="#2e1607", nose="#2a1d1a",
        ears="floppy", muzzle="dog", tail="dog",
        outfit=dict(kind="jacket", color="#2f6fd0", worn=0.0, buttons="#f5c52a"),
        shoes=dict(kind="rainboots", color="#d8382f"),
        backpack=None, head_scale=(1.02, 0.98, 0.94), eye_r=0.066,
    ),
    "rabbit": dict(
        label="Rabbit (Pushinka)", height=0.86,
        fur="#f4f2f0", fur2="#ffffff", fur_tip="#ffffff", patch="#9c9aa0", inner_ear="#f3a7b8",
        eye="#3a2a33", eye_dark="#0d080b", nose="#ee8fa6",
        ears="bunny", muzzle="bunny", tail="bunny",
        outfit=dict(kind="overalls", color="#8fe0c4", under="#fdfaf2"),
        shoes=dict(kind="sneakers", color="#f7b6c6", sole="#ffffff"),
        backpack="#f2a65a", head_scale=(1.0, 0.95, 0.95), eye_r=0.07,
    ),
    "fox": dict(
        label="Fox (Lisa)", height=1.05,
        fur="#d9b98a", fur2="#fbf5ea", fur_tip="#f3dfbf", ear_tip="#5a3a22",
        eye="#7f9a3c", eye_dark="#2e3a10", nose="#2a1d1a", inner_ear="#f6d6c0",
        ears="fox", muzzle="fox", tail="fox",
        outfit=dict(kind="vest", color="#3f9a55", under="#fbfaf5", buttons="#e7e2d0"),
        shoes=dict(kind="shoes", color="#18161a"),
        backpack=None, head_scale=(1.0, 0.95, 0.92), eye_r=0.064,
    ),
    "raccoon": dict(
        label="Raccoon (Senya)", height=1.05,
        fur="#8e9096", fur2="#e9e7e4", fur_tip="#c3c4c8", mask="#2e2c31", stripes="#3b393f",
        eye="#5a3a20", eye_dark="#1a0f05", nose="#1d1a1c", inner_ear="#e5e1dd",
        ears="round", muzzle="raccoon", tail="raccoon",
        outfit=dict(kind="vest", color="#8a2234", under="#fbfaf5", buttons="#e8d7b0"),
        shoes=dict(kind="sneakers", color="#f5f5f2", sole="#d9d9d9", stripe="#8a2234"),
        backpack=None, head_scale=(1.0, 0.95, 0.92), eye_r=0.064,
    ),
}

# channels and their neutral values
NEUTRAL = dict(
    x=0.0, y=0.0, rot=0.0, lift=0.0,
    hips_z=0.0, hips_rx=0.0, hips_ry=0.0,
    spine_rx=0.0, spine_ry=0.0, spine_rz=0.0,
    head_rx=0.0, head_ry=0.0, head_rz=0.0,
    sh_L_x=0.0, sh_L_y=8.0, sh_L_z=0.0, el_L=10.0,
    sh_R_x=0.0, sh_R_y=8.0, sh_R_z=0.0, el_R=10.0,
    leg_L_x=0.0, leg_L_y=0.0, leg_R_x=0.0, leg_R_y=0.0, knee_L=0.0, knee_R=0.0,
    ear_L=0.0, ear_R=0.0,
    gaze_x=0.0, gaze_y=0.0, eyes_open=1.0,
    brow=0.0, brow_h=0.0,
    smile=0.3, frown=0.0, mouth_open=0.0,
    tail_up=0.0, tail_side=0.0,
)


def garment(name, color, under, kind):
    """Torso garment shader: vest (V-neck showing shirt), overalls (bib + shirt), jacket (plain)."""
    key = ("garment", name)
    if key in mats._cache:
        return mats._cache[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def math_node(op, a=None, bval=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        if bval is not None:
            n.inputs[1].default_value = bval
        if a is not None:
            nt.links.new(a, n.inputs[0])
        return n

    # object space of unit sphere scaled: x,y,z in [-1,1]
    absx = math_node("ABSOLUTE", sep.outputs["X"])
    if kind == "vest":
        # shirt visible where y<0 (front) and |x| < (z - 0.05)*0.9 (V neck) ; also top (z>0.75) shirt collar
        zt = math_node("SUBTRACT", sep.outputs["Z"], 0.05)
        zk = math_node("MULTIPLY", zt.outputs[0], 0.95)
        v = math_node("LESS_THAN", absx.outputs[0])
        nt.links.new(zk.outputs[0], v.inputs[1])
    else:  # overalls: shirt where z > 0.25 except bib (|x|<0.45 & front)
        top = math_node("GREATER_THAN", sep.outputs["Z"], 0.28)
        bibx = math_node("GREATER_THAN", absx.outputs[0], 0.42)
        back = math_node("GREATER_THAN", sep.outputs["Y"], -0.15)
        notbib = math_node("MAXIMUM", bibx.outputs[0])
        nt.links.new(back.outputs[0], notbib.inputs[1])
        v = math_node("MULTIPLY", top.outputs[0])
        nt.links.new(notbib.outputs[0], v.inputs[1])
    front = math_node("LESS_THAN", sep.outputs["Y"], 0.0)
    mask = math_node("MULTIPLY", v.outputs[0])
    nt.links.new(front.outputs[0] if kind == "vest" else v.outputs[0], mask.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mask.outputs[0], mix.inputs["Factor"])
    mix.inputs[6].default_value = hexc(color)
    mix.inputs[7].default_value = hexc(under)
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 120.0
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.1
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 0.5
    b.inputs["Specular IOR Level"].default_value = 0.3
    mats._cache[key] = m
    return m


def _ell_surface_y(c, r, x, z, out=0.0):
    """y of the front (-Y) surface of an axis aligned ellipsoid (centre c, radii r) at x,z."""
    k = 1 - ((x - c[0]) / r[0]) ** 2 - ((z - c[2]) / r[2]) ** 2
    k = max(k, 0.0)
    return c[1] - r[1] * math.sqrt(k) - out


class Actor:
    def __init__(self, cid, name=None, loc=(0, 0), rot=0.0):
        self.cid = cid
        self.d = CHARACTERS[cid]
        self.name = name or cid
        self.state = dict(NEUTRAL)
        self.state.update(x=loc[0], y=loc[1], rot=rot)
        self.j = {}
        self.parts = {}
        self._build()
        self.apply_state()

    # ------------------------------------------------------------------ build
    def _m(self):
        d = self.d
        n = self.name
        M = {}
        M["fur"] = mats.fur(n + "_fur", hexc(d["fur"]), hexc(d["fur_tip"]),
                            stripes=hexc(d["stripes"]) if d.get("stripes") and self.cid == "ryzhik" else None,
                            stripe_scale=2.6)
        M["furhead"] = mats.fur(n + "_furhead", hexc(d["fur"]), hexc(d["fur_tip"]))
        if d.get("stripes") and self.cid == "ryzhik":
            M["tabby"] = mats.fur(n + "_tabby", hexc(d["stripes"]), None, var=0.05)
        M["fur2"] = mats.fur(n + "_fur2", hexc(d["fur2"]), hexc("#ffffff"), var=0.06)
        if d.get("patch"):
            M["patch"] = mats.fur(n + "_patch", hexc(d["patch"]), None, var=0.1)
        if d.get("ear_color"):
            M["earc"] = mats.fur(n + "_earc", hexc(d["ear_color"]), None)
        if d.get("mask"):
            M["mask"] = mats.fur(n + "_mask", hexc(d["mask"]), None, var=0.05, fuzz=0.15)
        if d.get("ear_tip"):
            M["eartip"] = mats.fur(n + "_eartip", hexc(d["ear_tip"]), None)
        M["inner"] = mats.basic(n + "_inner", hexc(d.get("inner_ear", d["fur2"])), rough=0.6, sheen=0.5)
        M["white"] = mats.basic("eye_white", hexc("#fbfbf8"), rough=0.15, coat=1.0)
        M["iris"] = mats.eye_iris(n + "_iris", hexc(d["eye"]), hexc(d["eye_dark"]))
        M["pupil"] = mats.basic("pupil", hexc("#050405"), rough=0.05, coat=1.0)
        M["hl"] = mats.basic("eye_hl", (1, 1, 1), rough=0.1, emission=(1, 1, 1), emit_strength=6.0)
        M["nose"] = mats.basic(n + "_nose", hexc(d["nose"]), rough=0.3, coat=0.5)
        M["mouth"] = mats.basic("mouth_line", hexc("#4a2224"), rough=0.6)
        M["mouthin"] = mats.basic("mouth_in", hexc("#5a1e26"), rough=0.5)
        M["tongue"] = mats.basic("tongue", hexc("#f07a8a"), rough=0.4)
        M["lash"] = mats.basic("lash", hexc("#231a18"), rough=0.6)
        o = d["outfit"]
        if o["kind"] == "jacket":
            M["cloth"] = mats.fabric(n + "_cloth", hexc(o["color"]), worn=o.get("worn", 0.0),
                                     worn_color=hexc(o["worn_color"]) if o.get("worn_color") else None)
            M["sleeve"] = M["cloth"]
        else:
            M["cloth"] = garment(n + "_garment", o["color"], o["under"], o["kind"])
            M["sleeve"] = mats.fabric(n + "_shirt", hexc(o["under"]))
            M["cloth_main"] = mats.fabric(n + "_clothmain", hexc(o["color"]))
        if o.get("patch"):
            M["clothpatch"] = mats.fabric(n + "_cpatch", hexc(o["patch"]), weave=200)
        if o.get("buttons"):
            M["button"] = mats.basic(n + "_btn", hexc(o["buttons"]), rough=0.3, coat=0.6)
        s = d["shoes"]
        if s["kind"] == "boots_worn":
            M["shoe"] = mats.leather_worn(n + "_boot", hexc(s["color"]), hexc(s["scuff"]))
            M["sole"] = mats.basic(n + "_sole", hexc(s["sole"]), rough=0.8)
        elif s["kind"] == "rainboots":
            M["shoe"] = mats.basic(n + "_boot", hexc(s["color"]), rough=0.2, coat=0.8)
            M["sole"] = mats.basic(n + "_sole", hexc("#7a1d18"), rough=0.6)
        elif s["kind"] == "shoes":
            M["shoe"] = mats.basic(n + "_shoe", hexc(s["color"]), rough=0.12, coat=1.0)
            M["sole"] = mats.basic(n + "_sole", hexc("#3a2a20"), rough=0.6)
        else:
            M["shoe"] = mats.fabric(n + "_shoe", hexc(s["color"]), rough=0.7)
            M["sole"] = mats.basic(n + "_sole", hexc(s.get("sole", "#ffffff")), rough=0.6)
            if s.get("stripe"):
                M["shoestripe"] = mats.basic(n + "_stripe", hexc(s["stripe"]), rough=0.5)
        if d.get("backpack"):
            M["bag"] = mats.fabric(n + "_bag", hexc(d["backpack"]), rough=0.75, weave=90)
            M["bag2"] = mats.basic(n + "_bag2", tuple(c * 0.6 for c in hexc(d["backpack"])[:3]), rough=0.7)
        M["mud"] = mats.noisy("mud", hexc("#3d2a1a"), hexc("#5b4128"), scale=30, rough=0.5, bump=0.6)
        self.M = M
        return M

    def _build(self):
        d = self.d
        n = self.name
        M = self._m()
        J = self.j
        P = self.parts
        sh = d["height"]

        J["root"] = geo.empty(n + "_root", (0, 0, 0))
        J["root"].scale = (sh, sh, sh)
        J["hips"] = geo.empty(n + "_hips", (0, 0, 0.30), J["root"])
        J["spine"] = geo.empty(n + "_spine", (0, 0, 0.0), J["hips"])

        # ---- torso / clothing
        tor_c, tor_r = (0, 0, 0.15), (0.165, 0.135, 0.225)
        P["torso"] = geo.sphere(n + "_torso", tor_c, tor_r, M["cloth"], J["spine"], seg=40, rings=20)
        # belly fur visible at the bottom for non-jacket? keep pelvis in fur under clothes
        P["pelvis"] = geo.sphere(n + "_pelvis", (0, 0, 0.0), (0.135, 0.11, 0.07), M["cloth_main"] if "cloth_main" in M else M["cloth"], J["spine"])
        o = d["outfit"]
        P["collar"] = geo.torus(n + "_collar", (0, -0.005, 0.355), 0.085, 0.028, M["cloth"] if o["kind"] == "jacket" else M["sleeve"], J["spine"], scale=(1.05, 0.9, 1))
        # chest fur / neck
        P["neck"] = geo.sphere(n + "_neck", (0, -0.02, 0.36), (0.085, 0.075, 0.06), M["fur2"], J["spine"])
        if o["kind"] == "jacket":
            # zipper / placket line and buttons
            for i, z in enumerate((0.27, 0.17, 0.07)):
                y = _ell_surface_y(tor_c, tor_r, 0.0, z) - 0.004
                geo.sphere(f"{n}_btn{i}", (0.0, y, z), (0.017, 0.008, 0.017), M["button"], J["spine"], seg=16, rings=8)
            # pockets
            for sx in (-1, 1):
                y = _ell_surface_y(tor_c, tor_r, 0.09 * sx, 0.06) + 0.002
                geo.box(f"{n}_pocket{sx}", (0.092 * sx, y, 0.06), (0.06, 0.012, 0.045), M["cloth"], J["spine"], rot=(0, 0, -0.45 * sx), bevel=0.006)
            if o.get("patch"):
                y = _ell_surface_y(tor_c, tor_r, 0.08, 0.22) + 0.0
                p = geo.box(n + "_patch", (0.085, y, 0.22), (0.05, 0.012, 0.045), M["clothpatch"], J["spine"], rot=(0.25, 0.1, -0.5), bevel=0.005)
                P["patch"] = p
            # hem
        else:
            if o.get("buttons"):
                for i, z in enumerate((0.13, 0.05) if o["kind"] == "vest" else (0.26,)):
                    for sx in ((0,) if o["kind"] == "vest" else (-1, 1)):
                        x = 0.0 if o["kind"] == "vest" else 0.07 * sx
                        y = _ell_surface_y(tor_c, tor_r, x, z) - 0.004
                        geo.sphere(f"{n}_btn{i}{sx}", (x, y, z), (0.015, 0.008, 0.015), M["button"], J["spine"], seg=16, rings=8)
            if o["kind"] == "overalls":
                for sx in (-1, 1):
                    pts = [(0.07 * sx, _ell_surface_y(tor_c, tor_r, 0.07 * sx, 0.24) - 0.006, 0.24),
                           (0.09 * sx, -0.06, 0.36), (0.09 * sx, 0.06, 0.36),
                           (0.07 * sx, -_ell_surface_y(tor_c, tor_r, 0.07 * sx, 0.24) + 0.006, 0.22)]
                    geo.tube(f"{n}_strap{sx}", pts, [0.012] * 4, M["cloth_main"], J["spine"], ring=8)

        # ---- head
        J["neck"] = geo.empty(n + "_neckj", (0, 0, 0.37), J["spine"])
        J["head"] = geo.empty(n + "_head", (0, 0, 0.0), J["neck"])
        hs = d["head_scale"]
        hc, hr = (0, 0, 0.22), (0.27 * hs[0], 0.245 * hs[1], 0.24 * hs[2])
        self.hc, self.hr = hc, hr
        P["head"] = geo.sphere(n + "_headm", hc, hr, M["furhead"], J["head"], seg=48, rings=24, subsurf=1)
        self._face(hc, hr)
        self._ears(hc, hr)

        # ---- arms
        for side, sx in (("L", 1), ("R", -1)):
            sj = geo.empty(f"{n}_sh_{side}", (0.155 * sx, 0, 0.30), J["spine"])
            J["sh_" + side] = sj
            geo.sphere(f"{n}_upper_{side}", (0, 0, -0.075), (0.055, 0.055, 0.1), M["sleeve"], sj)
            ej = geo.empty(f"{n}_el_{side}", (0, 0, -0.15), sj)
            J["el_" + side] = ej
            geo.sphere(f"{n}_fore_{side}", (0, 0, -0.065), (0.05, 0.05, 0.09), M["sleeve"], ej)
            geo.torus(f"{n}_cuff_{side}", (0, 0, -0.135), 0.042, 0.014, M["sleeve"] if o["kind"] == "jacket" else M["sleeve"], ej)
            hj = geo.empty(f"{n}_hand_{side}", (0, 0, -0.17), ej)
            J["hand_" + side] = hj
            geo.sphere(f"{n}_paw_{side}", (0, -0.005, 0), (0.05, 0.045, 0.055), M["furhead"] if self.cid != "raccoon" else M["mask"], hj)
            # little thumb
            geo.sphere(f"{n}_thumb_{side}", (-0.03 * sx, -0.03, 0.01), (0.02, 0.02, 0.025), M["furhead"] if self.cid != "raccoon" else M["mask"], hj)

        # ---- legs
        s = d["shoes"]
        for side, sx in (("L", 1), ("R", -1)):
            lj = geo.empty(f"{n}_leg_{side}", (0.078 * sx, 0, 0.02), J["hips"])
            J["leg_" + side] = lj
            legm = M["furhead"] if o["kind"] == "jacket" else (M["cloth_main"])
            geo.sphere(f"{n}_thigh_{side}", (0, 0, -0.1), (0.065, 0.065, 0.12), legm, lj)
            kj = geo.empty(f"{n}_knee_{side}", (0, 0, -0.17), lj)
            J["knee_" + side] = kj
            fj = geo.empty(f"{n}_foot_{side}", (0, 0, -0.095), kj)
            J["foot_" + side] = fj
            self._shoe(fj, side, sx)

        # ---- tail
        J["tail"] = geo.empty(n + "_tailj", (0, 0.12, 0.03), J["hips"])
        self._tail()

        # ---- backpack (worn on back)
        if d.get("backpack"):
            bp = geo.empty(n + "_bagback", (0, 0.16, 0.2), J["spine"])
            J["bag_back"] = bp
            self._bag(bp, n + "_bagb")
            for sx in (-1, 1):
                pts = [(0.08 * sx, 0.12, 0.31), (0.1 * sx, 0.0, 0.37), (0.1 * sx, -0.11, 0.3), (0.1 * sx, -0.12, 0.15), (0.09 * sx, 0.1, 0.05)]
                geo.tube(f"{n}_bstrap{sx}", pts, [0.012] * 5, M["bag2"], J["spine"], ring=8)
            # straps belong to backpack visibility – parent to bag_back via world fix
            for sx in (-1, 1):
                st = bpy.data.objects[f"{n}_bstrap{sx}"]
                st.parent = bp
                st.location = (0, -0.16, -0.2)
            bf = geo.empty(n + "_bagfront", (0, -0.24, 0.17), J["spine"], rot=(0.15, 0, 0))
            J["bag_front"] = bf
            self._bag(bf, n + "_bagf")
            bf.scale = (0.001, 0.001, 0.001)

    def _bag(self, parent, name):
        M = self.M
        b = geo.box(name, (0, 0, 0), (0.22, 0.1, 0.25), M["bag"], parent, bevel=0.035, bevel_seg=3, smooth=True)
        geo.box(name + "_pocket", (0, -0.0, -0.05), (0.16, 0.12, 0.1), M["bag2"], parent, bevel=0.025, bevel_seg=3, smooth=True)
        geo.tube(name + "_handle", [(-0.04, 0, 0.12), (0, 0, 0.16), (0.04, 0, 0.12)], [0.01] * 3, M["bag2"], parent, ring=8)
        return b

    def _shoe(self, fj, side, sx):
        n, M, s = self.name, self.M, self.d["shoes"]
        k = s["kind"]
        # ground contact: foot joint world z = 0.30 + 0.02 - 0.17 - 0.095 = 0.055
        P = self.parts
        if k == "boots_worn":
            P["boot_" + side] = geo.sphere(f"{n}_boot_{side}", (0, -0.035, 0.0), (0.072, 0.115, 0.06), M["shoe"], fj, seg=32)
            geo.cylinder(f"{n}_bootshaft_{side}", (0, 0.0, 0.06), 0.068, 0.11, M["shoe"], fj, radius2=0.072)
            geo.torus(f"{n}_bootrim_{side}", (0, 0.0, 0.115), 0.07, 0.012, M["shoe"], fj)
            geo.box(f"{n}_sole_{side}", (0, -0.035, -0.045), (0.14, 0.23, 0.025), M["sole"], fj, bevel=0.01)
            # laces
            for i in range(3):
                geo.box(f"{n}_lace{i}_{side}", (0, -0.075 + i * 0.03, 0.045 + i * 0.012), (0.05, 0.008, 0.008), M["sole"], fj, rot=(0.6, 0, 0))
            # scuffed toe-cap patch and a stitched repair
            geo.sphere(f"{n}_toecap_{side}", (0, -0.1, -0.005), (0.06, 0.05, 0.045), M["shoe"], fj, seg=24)
        elif k == "rainboots":
            geo.sphere(f"{n}_boot_{side}", (0, -0.03, 0.0), (0.07, 0.11, 0.058), M["shoe"], fj)
            geo.cylinder(f"{n}_bootshaft_{side}", (0, 0.0, 0.08), 0.066, 0.15, M["shoe"], fj, radius2=0.074)
            geo.box(f"{n}_sole_{side}", (0, -0.03, -0.045), (0.135, 0.22, 0.022), M["sole"], fj, bevel=0.01)
        elif k == "shoes":
            geo.sphere(f"{n}_boot_{side}", (0, -0.035, -0.005), (0.068, 0.115, 0.05), M["shoe"], fj)
            geo.box(f"{n}_sole_{side}", (0, -0.035, -0.045), (0.13, 0.22, 0.02), M["sole"], fj, bevel=0.01)
            geo.sphere(f"{n}_sock_{side}", (0, 0.01, 0.05), (0.055, 0.055, 0.04), M["sleeve"], fj)
        else:
            geo.sphere(f"{n}_boot_{side}", (0, -0.035, 0.0), (0.07, 0.115, 0.055), M["shoe"], fj)
            geo.box(f"{n}_sole_{side}", (0, -0.035, -0.045), (0.14, 0.23, 0.03), M["sole"], fj, bevel=0.012)
            if "shoestripe" in M:
                for sx2 in (-1, 1):
                    geo.box(f"{n}_stripe{sx2}_{side}", (0.066 * sx2, -0.03, 0.0), (0.008, 0.09, 0.02), M["shoestripe"], fj, rot=(0.3, 0, 0))
            geo.sphere(f"{n}_sock_{side}", (0, 0.01, 0.05), (0.055, 0.055, 0.04), M["sole"], fj)

    def _face(self, hc, hr):
        n, M, d, J, P = self.name, self.M, self.d, self.j, self.parts
        H = J["head"]
        kind = d["muzzle"]
        # muzzle geometry per species
        if kind == "cat":
            mc, mr = (0, -0.175, 0.15), (0.12, 0.085, 0.075)
            cheeks = [((0.1, -0.14, 0.14), (0.1, 0.09, 0.07)), ((-0.1, -0.14, 0.14), (0.1, 0.09, 0.07))]
            nose = ((0, -0.262, 0.19), (0.032, 0.02, 0.022))
        elif kind == "dog":
            mc, mr = (0, -0.2, 0.13), (0.115, 0.12, 0.085)
            cheeks = [((0.09, -0.15, 0.12), (0.09, 0.09, 0.07)), ((-0.09, -0.15, 0.12), (0.09, 0.09, 0.07))]
            nose = ((0, -0.315, 0.17), (0.045, 0.03, 0.032))
        elif kind == "bunny":
            mc, mr = (0, -0.18, 0.14), (0.1, 0.08, 0.07)
            cheeks = [((0.085, -0.15, 0.13), (0.085, 0.08, 0.065)), ((-0.085, -0.15, 0.13), (0.085, 0.08, 0.065))]
            nose = ((0, -0.255, 0.175), (0.026, 0.016, 0.018))
        elif kind == "fox":
            mc, mr = (0, -0.235, 0.13), (0.085, 0.15, 0.062)
            cheeks = [((0.13, -0.12, 0.12), (0.11, 0.09, 0.08)), ((-0.13, -0.12, 0.12), (0.11, 0.09, 0.08))]
            nose = ((0, -0.38, 0.16), (0.028, 0.022, 0.022))
        else:  # raccoon
            mc, mr = (0, -0.2, 0.13), (0.105, 0.1, 0.07)
            cheeks = [((0.12, -0.13, 0.13), (0.1, 0.09, 0.075)), ((-0.12, -0.13, 0.13), (0.1, 0.09, 0.075))]
            nose = ((0, -0.297, 0.16), (0.034, 0.024, 0.024))
        self.mc, self.mr = mc, mr
        muzzle_mat = M["fur2"]
        P["muzzle"] = geo.sphere(n + "_muzzle", mc, mr, muzzle_mat, H, seg=32)
        for i, (c, r) in enumerate(cheeks):
            geo.sphere(f"{n}_cheek{i}", c, r, M["fur2"] if kind in ("cat", "bunny", "fox", "raccoon") else M["fur"], H)
        geo.sphere(n + "_nose", nose[0], nose[1], M["nose"], H, seg=24)
        if kind == "cat":
            # tabby "M" marks on the forehead
            for i, (x, z, ang, ln) in enumerate(((0.0, 0.42, 0.0, 0.05), (0.045, 0.405, -0.25, 0.04), (-0.045, 0.405, 0.25, 0.04))):
                y = _ell_surface_y(hc, hr, x, z) + 0.009
                geo.sphere(f"{n}_tabby{i}", (x, y, z), (0.011, 0.01, ln), M["tabby"], H, rot=(-0.6, ang, 0))
        if kind == "dog":
            # brown eye patch over left eye
            geo.sphere(n + "_epatch", (0.105, -0.16, 0.29), (0.1, 0.09, 0.09), M["patch"], H)
        if kind == "bunny":
            geo.sphere(n + "_crown", (0, 0.02, 0.36), (0.18, 0.2, 0.1), M["patch"], H)
            # buck teeth
            for sx in (-1, 1):
                geo.box(f"{n}_tooth{sx}", (0.011 * sx, -0.247, 0.11), (0.02, 0.008, 0.026), M["white"], H, bevel=0.004)
        if kind == "raccoon":
            for sx in (-1, 1):
                geo.sphere(f"{n}_mask{sx}", (0.1 * sx, -0.165, 0.26), (0.11, 0.08, 0.07), M["mask"], H, rot=(0, 0.25 * sx, 0))
            geo.sphere(n + "_stripe", (0, -0.225, 0.34), (0.012, 0.03, 0.05), M["mask"], H)
        if kind == "fox":
            # neat combed fur tuft on top of the head
            pts = [(-0.06, -0.02, 0.445), (-0.01, -0.12, 0.45), (0.05, -0.18, 0.425), (0.09, -0.2, 0.39)]
            geo.tube(n + "_tuft", pts, [0.045, 0.04, 0.028, 0.008], M["furhead"], H, ring=12)

        # ---- eyes
        er = d["eye_r"]
        ex = 0.1 if kind not in ("fox", "raccoon") else 0.105
        ez = 0.255
        for side, sx in (("L", 1), ("R", -1)):
            x = ex * sx
            sy = _ell_surface_y(hc, hr, x, ez)
            cy = sy + er * 0.55
            ej = geo.empty(f"{n}_eye_{side}", (x, cy, ez), H)
            J["eye_" + side] = ej
            bj = geo.empty(f"{n}_blink_{side}", (0, 0, 0), ej)
            J["blink_" + side] = bj
            bj.scale = (1, 1, 1)
            geo.sphere(f"{n}_eyeball_{side}", (0, 0, 0), (er, er, er * 1.12), M["white"], bj, seg=32)
            gj = geo.empty(f"{n}_gaze_{side}", (0, 0, 0), bj)
            J["gaze_" + side] = gj
            geo.sphere(f"{n}_iris_{side}", (0, -er * 0.8, 0), (er * 0.78, er * 0.32, er * 0.86), M["iris"], gj, seg=32)
            geo.sphere(f"{n}_pupil_{side}", (0, -er * 1.07, 0), (er * 0.44, er * 0.08, er * 0.5), M["pupil"], gj, seg=24)
            geo.sphere(f"{n}_hl1_{side}", (er * 0.25 * sx - er * 0.05, -er * 1.1, er * 0.32), (er * 0.2, er * 0.06, er * 0.2), M["hl"], bj, seg=12, rings=6)
            geo.sphere(f"{n}_hl2_{side}", (-er * 0.22 * sx, -er * 1.08, -er * 0.3), (er * 0.09, er * 0.04, er * 0.09), M["hl"], bj, seg=10, rings=5)
            # upper lash line (gives the eye a defined, appealing shape)
            lash = [(-er * 0.95, -er * 0.25, er * 0.45), (-er * 0.5, -er * 0.78, er * 0.95), (0, -er * 0.92, er * 1.08),
                    (er * 0.5, -er * 0.78, er * 0.95), (er * 0.98 * sx if False else er * 0.98, -er * 0.25, er * 0.5)]
            geo.tube(f"{n}_lash_{side}", lash, [er * 0.04, er * 0.06, er * 0.065, er * 0.06, er * 0.035], M["lash"], bj, ring=8)
            # brows
            bj2 = geo.empty(f"{n}_browj_{side}", (x * 0.95, _ell_surface_y(hc, hr, x * 0.95, ez + er * 1.6) + 0.006, ez + er * 1.6), H)
            J["brow_" + side] = bj2
            bm = M["mask"] if "mask" in M else (M["fur"] if kind != "cat" else M["fur"])
            browc = mats.basic(n + "_browc", tuple(c * 0.5 for c in hexc(d["fur"])[:3]) if kind != "raccoon" else hexc("#e9e7e4"), rough=0.8, sheen=0.5)
            geo.tube(f"{n}_brow_{side}", [(-0.034, 0.004, -0.006), (0, 0, 0.006), (0.034, 0.004, -0.006)], [0.006, 0.008, 0.006], browc, bj2, ring=8)

        # ---- mouth (shape keys: smile, frown) and open mouth
        mz = mc[2] - mr[2] * 0.45
        w = 0.05

        def mpts(lift_end, mid_drop, open_=0.0):
            pts = []
            for i, t in enumerate((-1.0, -0.55, 0.0, 0.55, 1.0)):
                x = t * w
                z = mz + lift_end * (abs(t) ** 2) - mid_drop * (1 - abs(t) ** 2) * (0.6 if abs(t) < 0.1 else 1.0)
                if kind == "cat" and abs(t) < 0.1:
                    z += 0.012
                y = _ell_surface_y(mc, mr, x, z) - 0.002
                pts.append((x, y, z))
            return pts
        base = mpts(0.004, 0.006)
        P["mouth"] = geo.tube(n + "_mouth", base, [0.0045] * 5, M["mouth"], H, ring=8, samples=5,
                              shape_keys={"smile": mpts(0.022, 0.016), "frown": mpts(-0.02, -0.006)})
        oj = geo.empty(n + "_mopen", (0, _ell_surface_y(mc, mr, 0, mz - 0.025) + 0.012, mz - 0.025), H)
        J["mopen"] = oj
        geo.sphere(n + "_mouthin", (0, 0, 0), (0.042, 0.02, 0.032), M["mouthin"], oj)
        geo.sphere(n + "_tongue", (0, -0.008, -0.014), (0.03, 0.016, 0.016), M["tongue"], oj)
        oj.scale = (0.001, 0.001, 0.001)

    def _ears(self, hc, hr):
        n, M, d, J = self.name, self.M, self.d, self.j
        H = J["head"]
        k = d["ears"]
        for side, sx in (("L", 1), ("R", -1)):
            if k == "cat":
                pos, tilt = (0.15 * sx, 0.0, 0.41), (0.0, -0.32 * sx, 0)
            elif k == "fox":
                pos, tilt = (0.15 * sx, 0.01, 0.42), (0.0, -0.3 * sx, 0)
            elif k == "bunny":
                pos, tilt = (0.075 * sx, 0.02, 0.43), (-0.08, -0.12 * sx, 0)
            elif k == "round":
                pos, tilt = (0.17 * sx, 0.02, 0.39), (0.0, -0.55 * sx, 0)
            else:  # floppy
                pos, tilt = (0.2 * sx, 0.0, 0.40), (0.0, 0.0, 0)
            ej = geo.empty(f"{n}_ear_{side}", pos, H, rot=tilt)
            J["ear_" + side] = ej
            J["ear0_" + side] = tilt
            if k in ("cat", "fox"):
                big = 1.0 if k == "cat" else 1.25
                geo.cone(f"{n}_earo_{side}", (0, 0, 0.07 * big), 0.085 * big, 0.008, 0.17 * big, M["furhead"], ej, scale=(1, 0.42, 1))
                geo.cone(f"{n}_eari_{side}", (0, -0.018, 0.06 * big), 0.06 * big, 0.004, 0.13 * big, M["inner"], ej, scale=(1, 0.3, 1))
                if k == "fox":
                    geo.cone(f"{n}_eartip_{side}", (0, 0, 0.165 * big), 0.035 * big, 0.004, 0.06 * big, M["eartip"], ej, scale=(1, 0.5, 1))
                if k == "cat":
                    # small fur tufts inside the ear
                    geo.cone(f"{n}_tuft_{side}", (0, -0.03, 0.04), 0.02, 0.002, 0.08, M["fur2"], ej, scale=(1, 0.5, 1), rot=(0.3, 0, 0))
            elif k == "bunny":
                geo.sphere(f"{n}_earo_{side}", (0, 0, 0.19), (0.055, 0.03, 0.2), M["patch"], ej)
                geo.sphere(f"{n}_eari_{side}", (0, -0.017, 0.19), (0.036, 0.018, 0.165), M["inner"], ej)
            elif k == "round":
                geo.sphere(f"{n}_earo_{side}", (0, 0, 0.05), (0.07, 0.03, 0.075), M["furhead"], ej)
                geo.sphere(f"{n}_eari_{side}", (0, -0.015, 0.045), (0.05, 0.02, 0.055), M["inner"], ej)
            else:
                # floppy dog ear hanging down the side of the head
                geo.sphere(f"{n}_earo_{side}", (0.075 * sx, 0, -0.12), (0.042, 0.095, 0.16), M["earc"], ej, rot=(0, -0.3 * sx, 0))

    def _tail(self):
        n, M, d, J = self.name, self.M, self.d, self.j
        T = J["tail"]
        k = d["tail"]
        if k == "cat":
            base = [(0, 0, 0), (0, 0.12, 0.02), (0, 0.22, 0.12), (0, 0.24, 0.27), (0, 0.18, 0.38), (0, 0.1, 0.4)]
            up = [(0, 0, 0), (0, 0.08, 0.08), (0, 0.12, 0.22), (0, 0.12, 0.38), (0, 0.05, 0.48), (0, -0.03, 0.47)]
            down = [(0, 0, 0), (0, 0.1, -0.06), (0, 0.2, -0.14), (0, 0.32, -0.18), (0, 0.44, -0.2), (0, 0.54, -0.18)]
            left = [(x + 0.0, y, z) for (x, y, z) in base]
            left = [(0, 0, 0), (0.05, 0.12, 0.02), (0.15, 0.2, 0.1), (0.24, 0.2, 0.24), (0.24, 0.12, 0.34), (0.18, 0.06, 0.36)]
            right = [(-x, y, z) for (x, y, z) in left]
            radii = [0.04, 0.038, 0.036, 0.034, 0.032, 0.028]
            mat = M["fur"]
        elif k == "fox":
            base = [(0, 0, 0), (0, 0.12, -0.02), (0, 0.24, 0.0), (0, 0.32, 0.08), (0, 0.36, 0.18)]
            up = [(0, 0, 0), (0, 0.1, 0.06), (0, 0.17, 0.18), (0, 0.18, 0.3), (0, 0.12, 0.38)]
            down = [(0, 0, 0), (0, 0.1, -0.08), (0, 0.2, -0.16), (0, 0.3, -0.2), (0, 0.4, -0.2)]
            left = [(0, 0, 0), (0.06, 0.12, 0.0), (0.16, 0.2, 0.06), (0.22, 0.22, 0.15), (0.24, 0.18, 0.24)]
            right = [(-x, y, z) for (x, y, z) in left]
            radii = [0.035, 0.08, 0.1, 0.085, 0.03]
            mat = M["fur"]
        elif k == "raccoon":
            base = [(0, 0, 0), (0, 0.12, -0.03), (0, 0.24, -0.02), (0, 0.33, 0.06), (0, 0.38, 0.16)]
            up = [(0, 0, 0), (0, 0.1, 0.06), (0, 0.17, 0.18), (0, 0.18, 0.3), (0, 0.12, 0.38)]
            down = [(0, 0, 0), (0, 0.1, -0.08), (0, 0.2, -0.16), (0, 0.3, -0.2), (0, 0.4, -0.2)]
            left = [(0, 0, 0), (0.06, 0.12, 0.0), (0.16, 0.2, 0.06), (0.22, 0.22, 0.15), (0.24, 0.18, 0.24)]
            right = [(-x, y, z) for (x, y, z) in left]
            radii = [0.04, 0.075, 0.085, 0.075, 0.035]
            mat = mats.fur(n + "_ringtail", hexc(d["fur"]), None, stripes=hexc(d["stripes"]), stripe_scale=7.0)
            # bands follow object Z – rotate texture by tilting tail object's coords: use Y direction bands
            nt = mat.node_tree
            for nd in nt.nodes:
                if nd.type == "TEX_WAVE":
                    nd.bands_direction = "Y"
        elif k == "dog":
            base = [(0, 0, 0), (0, 0.06, 0.05), (0, 0.08, 0.13), (0, 0.05, 0.19)]
            up = [(0, 0, 0), (0, 0.04, 0.07), (0, 0.04, 0.15), (0, 0.0, 0.2)]
            down = [(0, 0, 0), (0, 0.08, -0.02), (0, 0.14, -0.06), (0, 0.18, -0.1)]
            left = [(0, 0, 0), (0.04, 0.06, 0.05), (0.09, 0.07, 0.12), (0.1, 0.04, 0.17)]
            right = [(-x, y, z) for (x, y, z) in left]
            radii = [0.035, 0.032, 0.028, 0.02]
            mat = M["fur"]
        else:  # bunny puff
            geo.sphere(n + "_tailm", (0, 0.03, 0.02), (0.07, 0.06, 0.065), M["fur2"], T)
            self.parts["tail"] = None
            return
        ob = geo.tube(n + "_tailm", base, radii, mat, T, ring=14, samples=6,
                      shape_keys={"up": up, "down": down, "left": left, "right": right})
        self.parts["tail"] = ob
        if k == "fox":
            # white tip
            tip = base[-1]
            geo.sphere(n + "_tailtip", tip, (0.05, 0.05, 0.06), M["fur2"], T)
            self.parts["tailtip"] = bpy.data.objects[n + "_tailtip"]

    # ----------------------------------------------------------------- props
    def bag_mode(self, frame, mode):
        """mode: 'back', 'front' (hugged to chest) or 'none'."""
        if "bag_back" not in self.j:
            return
        for k, on in (("bag_back", mode == "back"), ("bag_front", mode == "front")):
            ob = self.j[k]
            ob.scale = (1, 1, 1) if on else (0.001, 0.001, 0.001)
            ob.keyframe_insert("scale", frame=frame)
            fc = ob.animation_data.action.fcurves
            for c in fc:
                if c.data_path == "scale":
                    for kp in c.keyframe_points:
                        kp.interpolation = "CONSTANT"

    def add_mud(self, side="R", n=5, seed=1):
        import random
        rr = random.Random(seed)
        fj = self.j["foot_" + side]
        blobs = []
        for i in range(n):
            x = rr.uniform(-0.05, 0.05)
            y = rr.uniform(-0.13, 0.02)
            z = rr.uniform(-0.01, 0.06)
            b = geo.sphere(f"{self.name}_mud{side}{i}", (x, y, z), (rr.uniform(0.02, 0.035), rr.uniform(0.02, 0.035), 0.018), self.M["mud"], fj, seg=12, rings=6)
            blobs.append(b)
        return blobs

    def head_world(self):
        h = self.d["height"]
        return Vector((self.state["x"], self.state["y"], 0.9 * h + self.state["lift"]))

    def aim(self, target, head=0.6, limit=60):
        """Return channel values (head_rz, head_rx, gaze_x, gaze_y) to look at a world point."""
        hp = self.head_world()
        d = Vector(target) - hp
        yaw = math.degrees(math.atan2(d.x, -d.y)) - self.state["rot"]
        yaw = (yaw + 180) % 360 - 180
        pitch = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        hz = max(-limit, min(limit, yaw * head))
        hx = max(-30, min(30, -pitch * head))
        gx = max(-28, min(28, yaw - hz))
        gy = max(-25, min(25, pitch + hx))
        return dict(head_rz=hz, head_rx=hx, gaze_x=gx, gaze_y=gy)

    # ---------------------------------------------------------------- animate
    def apply_state(self, s=None):
        s = s or self.state
        J = self.j
        r = J["root"]
        r.location = (s["x"], s["y"], s["lift"])
        r.rotation_euler = (0, 0, s["rot"] * D2R)
        J["hips"].location = (0, 0, 0.30 + s["hips_z"])
        J["hips"].rotation_euler = (s["hips_rx"] * D2R, s["hips_ry"] * D2R, 0)
        J["spine"].rotation_euler = (s["spine_rx"] * D2R, s["spine_ry"] * D2R, s["spine_rz"] * D2R)
        J["head"].rotation_euler = (s["head_rx"] * D2R, s["head_ry"] * D2R, s["head_rz"] * D2R)
        for side, sx in (("L", 1), ("R", -1)):
            J["sh_" + side].rotation_euler = (-s[f"sh_{side}_x"] * D2R, -sx * s[f"sh_{side}_y"] * D2R, sx * s[f"sh_{side}_z"] * D2R)
            J["el_" + side].rotation_euler = (-s[f"el_{side}"] * D2R, 0, 0)
            J["leg_" + side].rotation_euler = (-s[f"leg_{side}_x"] * D2R, -sx * s[f"leg_{side}_y"] * D2R, 0)
            J["knee_" + side].rotation_euler = (s[f"knee_{side}"] * D2R, 0, 0)
            J["foot_" + side].rotation_euler = ((s[f"leg_{side}_x"] - s[f"knee_{side}"]) * D2R * 0.6, 0, 0)
            t0 = J["ear0_" + side]
            e = s[f"ear_{side}"]
            if self.d["ears"] == "floppy":
                J["ear_" + side].rotation_euler = (t0[0] + e * 0.3 * D2R, t0[1] + sx * e * 0.4 * D2R, t0[2])
            elif self.d["ears"] == "bunny":
                J["ear_" + side].rotation_euler = (t0[0] + e * 1.0 * D2R, t0[1] - sx * e * 0.5 * D2R, t0[2])
            else:
                J["ear_" + side].rotation_euler = (t0[0] + e * 0.55 * D2R, t0[1] - sx * e * 0.85 * D2R, t0[2])
            J["gaze_" + side].rotation_euler = (-s["gaze_y"] * D2R, 0, s["gaze_x"] * D2R)
            J["eye_" + side].scale = (1, 1, s["eyes_open"])
            b = s["brow"]
            J["brow_" + side].rotation_euler = (0, sx * b * 0.35 * D2R * -1, 0)
            J["brow_" + side].location.z = J["brow_" + side].location.z * 0 + self._brow_z(side) + s["brow_h"] * 0.01 + abs(b) * 0.0
        mo = s["mouth_open"]
        v = max(mo, 0.001)
        J["mopen"].scale = (0.6 + 0.4 * v, 1.0 if mo > 0.01 else 0.001, v)
        mo_ob = self.parts["mouth"]
        kb = mo_ob.data.shape_keys.key_blocks
        kb["smile"].value = max(0.0, s["smile"])
        kb["frown"].value = max(0.0, s["frown"])
        t = self.parts.get("tail")
        if t is not None:
            kb = t.data.shape_keys.key_blocks
            kb["up"].value = max(0.0, s["tail_up"])
            kb["down"].value = max(0.0, -s["tail_up"])
            kb["left"].value = max(0.0, s["tail_side"])
            kb["right"].value = max(0.0, -s["tail_side"])
            tip = self.parts.get("tailtip")
            if tip is not None:
                # approximate tip follow: blend positions
                pass

    def _brow_z(self, side):
        if not hasattr(self, "_bz"):
            self._bz = {s: self.j["brow_" + s].location.z for s in ("L", "R")}
        return self._bz[side]

    def _keyall(self, frame):
        J = self.j
        r = J["root"]
        r.keyframe_insert("location", frame=frame)
        r.keyframe_insert("rotation_euler", index=2, frame=frame)
        for k in ("hips",):
            J[k].keyframe_insert("location", index=2, frame=frame)
            J[k].keyframe_insert("rotation_euler", frame=frame)
        for k in ("spine", "head"):
            J[k].keyframe_insert("rotation_euler", frame=frame)
        for side in ("L", "R"):
            for k in ("sh_", "el_", "leg_", "knee_", "foot_", "ear_", "gaze_", "brow_"):
                J[k + side].keyframe_insert("rotation_euler", frame=frame)
            J["eye_" + side].keyframe_insert("scale", frame=frame)
            J["brow_" + side].keyframe_insert("location", index=2, frame=frame)
        J["mopen"].keyframe_insert("scale", frame=frame)
        for kb in self.parts["mouth"].data.shape_keys.key_blocks[1:]:
            kb.keyframe_insert("value", frame=frame)
        t = self.parts.get("tail")
        if t is not None:
            for kb in t.data.shape_keys.key_blocks[1:]:
                kb.keyframe_insert("value", frame=frame)

    def _targets(self, ch):
        J = self.j
        T = []
        if ch in ("x", "y", "lift"):
            T.append((J["root"], "location", "xyl".index(ch[0]) if ch != "lift" else 2))
        elif ch == "rot":
            T.append((J["root"], "rotation_euler", 2))
        elif ch == "hips_z":
            T.append((J["hips"], "location", 2))
        elif ch in ("hips_rx", "hips_ry"):
            T.append((J["hips"], "rotation_euler", 0 if ch.endswith("x") else 1))
        elif ch.startswith("spine_") or ch.startswith("head_"):
            T.append((J[ch.split("_")[0]], "rotation_euler", "xyz".index(ch[-1])))
        elif ch.startswith("sh_"):
            side = ch[3]
            T.append((J["sh_" + side], "rotation_euler", "xyz".index(ch[-1])))
        elif ch.startswith("el_"):
            T.append((J[ch], "rotation_euler", 0))
        elif ch.startswith("leg_"):
            side = ch[4]
            T.append((J["leg_" + side], "rotation_euler", "xyz".index(ch[-1])))
            T.append((J["foot_" + side], "rotation_euler", 0))
        elif ch.startswith("knee_"):
            T.append((J[ch], "rotation_euler", 0))
            T.append((J["foot_" + ch[-1]], "rotation_euler", 0))
        elif ch.startswith("ear_"):
            T += [(J[ch], "rotation_euler", i) for i in range(3)]
        elif ch.startswith("gaze_"):
            T += [(J["gaze_" + sd], "rotation_euler", i) for sd in "LR" for i in (0, 2)]
        elif ch == "eyes_open":
            T += [(J["eye_" + sd], "scale", 2) for sd in "LR"]
        elif ch in ("brow", "brow_h"):
            T += [(J["brow_" + sd], "rotation_euler", 1) for sd in "LR"] + [(J["brow_" + sd], "location", 2) for sd in "LR"]
        elif ch in ("smile", "frown"):
            T.append((self.parts["mouth"].data.shape_keys.key_blocks[ch], "value", -1))
        elif ch == "mouth_open":
            T += [(J["mopen"], "scale", i) for i in range(3)]
        elif ch.startswith("tail_"):
            t = self.parts.get("tail")
            if t is not None:
                T += [(kb, "value", -1) for kb in t.data.shape_keys.key_blocks[1:]]
        return T

    def key_only(self, frame, **ch):
        """Key only the given channels (safe to call out of chronological order, e.g. during a walk)."""
        st = dict(self.state)
        st.update(ch)
        self.apply_state(st)
        for c in ch:
            for ob, path, idx in self._targets(c):
                if idx < 0:
                    ob.keyframe_insert(path, frame=frame)
                else:
                    ob.keyframe_insert(path, index=idx, frame=frame)
        self.apply_state()

    def hold_only(self, f0, f1, **ch):
        """Key the channels at both ends of a span (keeps a look/expression during other motion)."""
        self.key_only(f0, **ch)
        self.key_only(f1, **ch)

    def key(self, frame, **ch):
        for k, v in ch.items():
            if k not in self.state:
                raise KeyError(f"unknown channel {k}")
            self.state[k] = v
        self.apply_state()
        self._keyall(frame)

    def key_tmp(self, frame, **ch):
        """Key a temporary variation without changing persistent state."""
        s = dict(self.state)
        s.update(ch)
        self.apply_state(s)
        self._keyall(frame)
        self.apply_state()

    # ---------------------------------------------------------- locomotion
    def face_dir(self, dx, dy):
        return math.degrees(math.atan2(dx, -dy))

    def walk(self, f0, f1, to, step=8, stride=24.0, run=False, face=None, arm=None, extra=None, end_keys=True):
        """Walk from current position to `to` between frames f0..f1 with an alternating gait."""
        x0, y0 = self.state["x"], self.state["y"]
        x1, y1 = to
        rot = self.face_dir(x1 - x0, y1 - y0) if face is None else face
        if abs(x1 - x0) + abs(y1 - y0) < 1e-6:
            rot = self.state["rot"]
        self.key(f0, rot=rot) if abs(((rot - self.state["rot"] + 180) % 360) - 180) < 1 else self.key(f0)
        if abs(((rot - self.state["rot"] + 180) % 360) - 180) >= 1:
            self.key(f0 + 4, rot=rot)
        arm = stride * (0.9 if not run else 1.4) if arm is None else arm
        lean = 12.0 if run else 3.0
        n = max(1, int((f1 - f0) / step))
        stepf = (f1 - f0) / n
        base = dict(self.state)
        extra = extra or {}
        for i in range(n + 1):
            f = f0 + i * stepf
            t = i / n
            ramp = min(1.0, min(i, n - i) / 1.0) if n > 2 else 0.6
            ph = 1 if i % 2 == 0 else -1
            amp = stride * (0.4 + 0.6 * ramp)
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            cont = dict(x=x, y=y, rot=rot if f > f0 + 3 else self.state["rot"],
                        leg_L_x=ph * amp, leg_R_x=-ph * amp,
                        knee_L=8.0 if ph < 0 else 2.0, knee_R=8.0 if ph > 0 else 2.0,
                        sh_L_x=base["sh_L_x"] - ph * arm * ramp, sh_R_x=base["sh_R_x"] + ph * arm * ramp,
                        el_L=base["el_L"] + (25 if run else 8), el_R=base["el_R"] + (25 if run else 8),
                        hips_z=-0.018 * (1.4 if run else 1.0) * ramp,
                        spine_rx=base["spine_rx"] + lean * ramp, spine_rz=ph * 4.0 * ramp,
                        head_rx=base["head_rx"] - lean * 0.6 * ramp)
            cont.update(extra)
            if i == n and end_keys:
                cont.update(leg_L_x=0, leg_R_x=0, knee_L=0, knee_R=0, sh_L_x=base["sh_L_x"], sh_R_x=base["sh_R_x"],
                            el_L=base["el_L"], el_R=base["el_R"], hips_z=0.0, spine_rx=base["spine_rx"], spine_rz=0.0,
                            head_rx=base["head_rx"])
                self.key(round(f), **cont)
            else:
                self.key_only(round(f), **cont)
                # passing pose between contacts: body up, knee bent on swing leg
                if i < n:
                    fp = f + stepf / 2
                    tp = (i + 0.5) / n
                    pas = dict(cont)
                    pas.update(x=x0 + (x1 - x0) * tp, y=y0 + (y1 - y0) * tp, leg_L_x=0, leg_R_x=0,
                               knee_L=(35 if run else 22) * ramp if ph > 0 else 0, knee_R=(35 if run else 22) * ramp if ph < 0 else 0,
                               sh_L_x=base["sh_L_x"], sh_R_x=base["sh_R_x"],
                               hips_z=(0.02 if run else 0.008) * ramp, spine_rz=0.0)
                    self.key_only(round(fp), **pas)
        self.state.update(x=x1, y=y1, rot=rot)
        return f1

    def laugh(self, f0, f1, period=5, point=None):
        """Thoughtless giggle: bouncing shoulders, squinted eyes, open-close mouth."""
        f = f0
        i = 0
        while f <= f1:
            up = i % 2 == 0
            ch = dict(hips_z=0.008 if up else -0.004, spine_rx=self.state["spine_rx"] + (4 if up else 0),
                      head_rx=self.state["head_rx"] + (-8 if up else -3), mouth_open=0.75 if up else 0.4,
                      eyes_open=0.55, smile=1.0, brow=-0.2)
            self.key_only(f, **ch)
            f += period
            i += 1

    def blink(self, frame):
        for side in ("L", "R"):
            b = self.j["blink_" + side]
            for f, sz in ((frame - 1, 1.0), (frame + 1, 0.08), (frame + 2, 0.08), (frame + 4, 1.0)):
                b.scale = (1, 1, sz)
                b.keyframe_insert("scale", index=2, frame=f)
            b.scale = (1, 1, 1)

    def wag(self, f0, f1, period=6, amp=1.0):
        f = f0
        i = 0
        while f <= f1:
            self.key_only(f, tail_side=amp if i % 2 == 0 else -amp)
            f += period
            i += 1
        self.key_only(f1 + period, tail_side=self.state["tail_side"])

    def add_life(self, strength=1.0, seed=0):
        """Subtle procedural idle noise (breathing / micro head motion)."""
        J = self.j
        targets = [(J["head"], "rotation_euler", 0, 0.012), (J["head"], "rotation_euler", 2, 0.015),
                   (J["spine"], "rotation_euler", 1, 0.006), (J["hips"], "location", 2, 0.002)]
        for ob, path, idx, st in targets:
            ad = ob.animation_data
            if ad is None or ad.action is None:
                continue
            fc = ad.action.fcurves.find(path, index=idx)
            if fc is None:
                continue
            m = fc.modifiers.new("NOISE")
            m.scale = 18.0
            m.strength = st * strength
            m.phase = seed * 7.3 + idx * 3.1 + hash(ob.name) % 50

    def finalize(self):
        """Smooth interpolation for all actions."""
        for ob in [self.j[k] for k in self.j if not k.startswith("ear0")] + [self.parts["mouth"]]:
            pass
