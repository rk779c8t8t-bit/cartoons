"""Parametric stylized cat rig used for Milo (kitten chef) and Mom (adult cat).

The rig is a hierarchy of empties + smooth primitives; every frame the choreography
calls Cat.pose(**controls) which sets transforms. Character design constants live
in MILO / MOM dictionaries and never change between scenes (character consistency).
"""
import math

from mathutils import Vector

from .core import (obj, empty, curve_obj, set_curve_points, new_mat, fur_mat, flourable,
                   set_flour, clamp)

MILO = dict(
    name="Milo", scale=1.0,
    head_r=0.12, body=(0.095, 0.085, 0.09), leg=0.06, arm=(0.052, 0.05),
    fur=(1.0, 0.33, 0.02), stripe=(0.75, 0.16, 0.01), cream=(1.0, 0.8, 0.55),
    iris=(1.0, 0.55, 0.03), nose=(1.0, 0.45, 0.55),
    top=(0.96, 0.96, 0.97), apron=(0.2, 0.55, 1.0), sleeve=(0.96, 0.96, 0.97),
    hat=True, eye=(0.31, 0.37), lashes=False, chest_fluff=False,
)

MOM = dict(
    name="Mom", scale=2.6,
    head_r=0.092, body=(0.105, 0.092, 0.165), leg=0.12, arm=(0.085, 0.08),
    fur=(1.0, 0.62, 0.3), stripe=(0.92, 0.42, 0.14), cream=(1.0, 0.88, 0.72),
    iris=(0.2, 0.78, 0.25), nose=(0.98, 0.5, 0.58),
    top=(1.0, 0.45, 0.62), apron=(0.99, 0.96, 0.9), sleeve=(1.0, 0.45, 0.62),
    hat=False, eye=(0.27, 0.32), lashes=True, chest_fluff=True, tail_k=0.6,
)


class Cat:
    def __init__(self, P):
        self.P = P
        n = P["name"]
        hr = P["head_r"]
        rx, ry, rz = P["body"]
        self.mats_flour = []
        fur = fur_mat(f"{n}_fur", P["fur"], P["stripe"])
        cream = fur_mat(f"{n}_cream", P["cream"], P["cream"], stripe_scale=0.01)
        top = flourable(f"{n}_top", P["top"], rough=0.55, sheen=0.5)
        apron = flourable(f"{n}_apron", P["apron"], rough=0.5, sheen=0.5)
        sleeve = top if P["sleeve"] == P["top"] else flourable(f"{n}_sleeve", P["sleeve"])
        self.mats_flour = [fur, cream, top, apron]
        pink = new_mat(f"{n}_pink", P["nose"], rough=0.35, coat=0.3)
        inner = new_mat(f"{n}_ear", (1.0, 0.62, 0.66), rough=0.6, sss=0.3)
        white = new_mat(f"{n}_sclera", (0.98, 0.98, 0.98), rough=0.15, coat=0.6)
        iris = new_mat(f"{n}_iris", P["iris"], rough=0.15, coat=1.0, emit=P["iris"], emit_str=0.25)
        black = new_mat(f"{n}_pupil", (0.01, 0.01, 0.015), rough=0.1, coat=1.0)
        hl = new_mat(f"{n}_hl", (1, 1, 1), emit=(1, 1, 1), emit_str=6.0)
        mouthm = new_mat(f"{n}_mouth", (0.35, 0.03, 0.06), rough=0.5)
        line = new_mat(f"{n}_line", (0.25, 0.08, 0.04), rough=0.6)
        whisk = new_mat(f"{n}_whisker", (1, 1, 0.97), rough=0.4)
        self.fur_mat, self.cream_mat = fur, cream

        self.root = empty(n)
        self.root.scale = (P["scale"],) * 3
        self.hip = empty(f"{n}_hip", (0, 0, P["leg"]), self.root)
        # torso + clothing
        self.torso = obj(f"{n}_torso", "sphere", (0, 0, rz * 0.95), (rx, ry, rz), top, self.hip)
        obj(f"{n}_apron", "sphere", (0, -ry * 0.32, rz * 0.62), (rx * 0.9, ry * 0.72, rz * 0.78), apron, self.hip)
        obj(f"{n}_strap", "torus", (0, -ry * 0.05, rz * 1.72), (rx * 0.62, ry * 0.62, rz * 0.6), apron, self.hip,
            rot=(0.35, 0, 0), r=0.09)
        if P["hat"]:  # chef jacket buttons
            btn = new_mat(f"{n}_btn", (0.85, 0.85, 0.88), rough=0.2, coat=1.0)
            for i, z in enumerate((1.45, 1.22)):
                for s in (-1, 1):
                    obj(f"{n}_btn{i}{s}", "sphere", (s * rx * 0.33, -ry * 0.9, rz * z), (0.009,) * 3, btn, self.hip)
            obj(f"{n}_collar", "torus", (0, 0, rz * 1.8), (rx * 0.6, ry * 0.62, rz * 0.5), top, self.hip, r=0.22)
        if P["chest_fluff"]:
            obj(f"{n}_fluff", "sphere", (0, -ry * 0.6, rz * 1.62), (rx * 0.55, ry * 0.45, rz * 0.32), cream, self.hip)
            obj(f"{n}_fluff2", "sphere", (0, -ry * 0.75, rz * 1.45), (rx * 0.35, ry * 0.3, rz * 0.22), cream, self.hip)
            # cardigan buttons
            btn = new_mat(f"{n}_btn", (1.0, 0.95, 0.85), rough=0.2, coat=1.0)
            for i, z in enumerate((1.25, 1.02, 0.79)):
                obj(f"{n}_btn{i}", "sphere", (rx * 0.28, -ry * 0.93, rz * z), (0.007,) * 3, btn, self.hip)

        # ------------------------------------------------ head
        self.neck = empty(f"{n}_neck", (0, 0, rz * 1.85), self.hip)
        self.head = empty(f"{n}_head", (0, 0, hr * 0.85), self.neck)
        obj(f"{n}_skull", "sphere", (0, 0, 0), (hr * 1.1, hr * 0.98, hr * 0.94), fur, self.head)
        for s in (-1, 1):  # cheeks / muzzle
            obj(f"{n}_cheek{s}", "sphere", (s * hr * 0.33, -hr * 0.66, -hr * 0.33),
                (hr * 0.4, hr * 0.33, hr * 0.3), cream, self.head)
        obj(f"{n}_chin", "sphere", (0, -hr * 0.62, -hr * 0.52), (hr * 0.28, hr * 0.25, hr * 0.2), cream, self.head)
        obj(f"{n}_face", "sphere", (0, -hr * 0.3, -hr * 0.3), (hr * 0.7, hr * 0.7, hr * 0.5), cream, self.head)
        obj(f"{n}_nose", "sphere", (0, -hr * 0.97, -hr * 0.13), (hr * 0.12, hr * 0.075, hr * 0.08), pink, self.head)
        self.mouth_line = curve_obj(f"{n}_mouthline", 9, bevel=hr * 0.022, material=line, parent=self.head)
        self.mouth_open = obj(f"{n}_mouthopen", "sphere", (0, -hr * 0.97, -hr * 0.4),
                              (hr * 0.17, hr * 0.12, hr * 0.12), mouthm, self.head)
        self.tongue = obj(f"{n}_tongue", "sphere", (0, -hr * 0.05, -hr * 0.5), (0.7, 0.8, 0.45), pink, self.mouth_open)
        # whiskers
        for s in (-1, 1):
            for k in range(3):
                w = curve_obj(f"{n}_wh{s}{k}", 4, bevel=hr * 0.008, material=whisk, parent=self.head)
                y0, z0 = -hr * 0.9, -hr * (0.26 + 0.08 * k)
                pts = [(s * hr * 0.55, y0, z0), (s * hr * 0.9, y0 + hr * 0.02, z0 + hr * (0.06 - 0.06 * k)),
                       (s * hr * 1.1, y0 + hr * 0.08, z0 + hr * (0.1 - 0.12 * k)),
                       (s * hr * 1.3, y0 + hr * 0.16, z0 + hr * (0.12 - 0.2 * k))]
                set_curve_points(w, pts)
        # eyes
        ew, eh = P["eye"]
        self.eyes, self.balls, self.pupils, self.brows = [], [], [], []
        for s in (-1, 1):
            ep = empty(f"{n}_eye{s}", (s * hr * 0.4, -hr * 0.7, hr * 0.08), self.head, rot=(0, 0, s * 0.28))
            obj(f"{n}_sclera{s}", "sphere", (0, 0, 0), (hr * ew, hr * 0.26, hr * eh), white, ep)
            ball = empty(f"{n}_ball{s}", (0, 0, 0), ep)
            ir = obj(f"{n}_iris{s}", "sphere", (0, -hr * 0.235, 0), (hr * ew * 0.74, hr * 0.06, hr * eh * 0.74), iris, ball)
            pu = obj(f"{n}_pupil{s}", "sphere", (0, -0.5, 0), (0.55, 0.6, 0.62), black, ir)
            obj(f"{n}_hl1{s}", "sphere", (0.3, -1.3, 0.34), (0.26, 0.3, 0.24), hl, ir)
            obj(f"{n}_hl2{s}", "sphere", (-0.3, -1.3, -0.36), (0.12, 0.2, 0.12), hl, ir)
            br = obj(f"{n}_brow{s}", "sphere", (s * hr * 0.38, -hr * 0.8, hr * 0.52),
                     (hr * 0.15, hr * 0.05, hr * 0.04), line if not P["lashes"] else line, self.head)
            if P["lashes"]:
                for k in range(3):
                    la = curve_obj(f"{n}_lash{s}{k}", 3, bevel=hr * 0.012, material=black, parent=ep)
                    x0 = s * hr * ew * (0.55 + 0.17 * k)
                    set_curve_points(la, [(x0, -hr * 0.12, hr * eh * (0.8 - 0.18 * k)),
                                          (x0 + s * hr * 0.06, -hr * 0.14, hr * eh * (0.92 - 0.18 * k)),
                                          (x0 + s * hr * 0.13, -hr * 0.12, hr * eh * (0.98 - 0.2 * k))])
            self.eyes.append(ep)
            self.balls.append(ball)
            self.pupils.append(pu)
            self.brows.append(br)
        # ears
        self.ears = []
        for s in (-1, 1):
            ear = empty(f"{n}_earp{s}", (s * hr * 0.58, 0.0, hr * 0.62), self.head, rot=(0, s * 0.42, 0))
            obj(f"{n}_ear{s}", "cone", (0, 0, hr * 0.3), (hr * 0.4, hr * 0.17, hr * 0.7), fur, ear)
            obj(f"{n}_eari{s}", "cone", (0, -hr * 0.08, hr * 0.27), (hr * 0.27, hr * 0.07, hr * 0.55), inner, ear)
            self.ears.append(ear)
        # chef hat
        self.hat = None
        if P["hat"]:
            hatm = flourable(f"{n}_hatm", (0.99, 0.99, 1.0), rough=0.6, sheen=0.6)
            self.hat = empty(f"{n}_hat", (0, hr * 0.05, hr * 0.78), self.head, rot=(-0.12, 0.1, 0))
            obj(f"{n}_hatband", "cylinder", (0, 0, hr * 0.22), (hr * 0.7, hr * 0.7, hr * 0.48), hatm, self.hat)
            obj(f"{n}_hatpuff", "sphere", (0, 0, hr * 0.78), (hr * 0.95, hr * 0.9, hr * 0.62), hatm, self.hat)
            for k in range(5):
                a = k * 2 * math.pi / 5
                obj(f"{n}_hatp{k}", "sphere", (math.cos(a) * hr * 0.55, math.sin(a) * hr * 0.55, hr * 0.85),
                    (hr * 0.5,) * 3, hatm, self.hat)
            self.mats_flour.append(hatm)

        # ------------------------------------------------ arms / legs / tail
        a1, a2 = P["arm"]
        self.sh, self.el, self.hand = [], [], []
        for s in (-1, 1):
            sh = empty(f"{n}_sh{s}", (s * rx * 0.88, 0, rz * 1.5), self.hip)
            obj(f"{n}_upper{s}", "sphere", (0, 0, -a1 * 0.5), (rx * 0.3, rx * 0.3, a1 * 0.62), sleeve, sh)
            el = empty(f"{n}_el{s}", (0, 0, -a1), sh)
            obj(f"{n}_fore{s}", "sphere", (0, 0, -a2 * 0.45), (rx * 0.26, rx * 0.26, a2 * 0.6), fur, el)
            obj(f"{n}_paw{s}", "sphere", (0, 0, -a2 * 0.95), (rx * 0.3, rx * 0.3, rx * 0.28), cream, el)
            hd = empty(f"{n}_hand{s}", (0, 0, -a2 * 1.05), el)
            self.sh.append(sh)
            self.el.append(el)
            self.hand.append(hd)
        self.legs = []
        L = P["leg"]
        for s in (-1, 1):
            lp = empty(f"{n}_legp{s}", (s * rx * 0.48, 0, rz * 0.35), self.hip)
            obj(f"{n}_leg{s}", "sphere", (0, 0, -(L + rz * 0.35) * 0.5), (rx * 0.32, rx * 0.32, (L + rz * 0.35) * 0.55), fur, lp)
            obj(f"{n}_foot{s}", "sphere", (0, -rx * 0.12, -(L + rz * 0.35) + rx * 0.16),
                (rx * 0.36, rx * 0.48, rx * 0.2), cream, lp)
            self.legs.append(lp)
        self.tail = curve_obj(f"{n}_tail", 14, bevel=1.0, material=fur, parent=self.hip)
        self.tail.data.bevel_depth = rx * 0.2
        self.pose()

    # ---------------------------------------------------------------- pose
    def pose(self, loc=None, rz=0.0, squash=1.0, lean=0.0, lean_side=0.0,
             head=(0, 0, 0), look=(0, 0), eye_open=1.0, eye_big=1.0, pupil=1.0,
             brow=0.0, brow_ang=0.0, smile=0.6, mouth=0.0, ears=0.0,
             arm_l=(-0.1, 0.25, 0), arm_r=(-0.1, -0.25, 0), elbow=(-0.3, -0.3),
             legs=(0.0, 0.0), tail_wag=0.0, tail_up=0.5, hat_tilt=0.0, flour=0.0,
             hip_z=None):
        P = self.P
        hr = P["head_r"]
        if loc is not None:
            self.root.location = loc
        self.root.rotation_euler = (0, 0, rz)
        sc = P["scale"]
        sq = max(0.4, squash)
        self.root.scale = (sc / math.sqrt(sq), sc / math.sqrt(sq), sc * sq)
        self.hip.location.z = P["leg"] if hip_z is None else hip_z
        self.hip.rotation_euler = (lean, lean_side, 0)
        self.head.rotation_euler = (-head[0], head[1], head[2])
        for i, s in enumerate((-1, 1)):
            ep = self.eyes[i]
            eo = eye_open[i] if hasattr(eye_open, "__len__") else eye_open
            ep.scale = (eye_big, eye_big, eye_big * max(0.06, eo))
            self.balls[i].rotation_euler = (-look[1] * 0.6, 0, look[0] * 0.6)
            self.pupils[i].scale = (0.66 * pupil, 0.6, 0.72 * pupil)
            br = self.brows[i]
            br.location.z = hr * (0.5 + 0.12 * brow + 0.12 * (eye_big - 1))
            br.rotation_euler = (0, s * brow_ang, 0)
            self.ears[i].rotation_euler = (ears * 0.5, s * (0.42 + 0.5 * max(0, -ears)), 0)
        # mouth line: 'w' shape, corners lifted by smile
        xs = [-0.34, -0.25, -0.16, -0.07, 0.0, 0.07, 0.16, 0.25, 0.34]
        pts = []
        for x in xs:
            ax = abs(x)
            z = -0.3 - 0.07 * math.sin(clamp(ax / 0.16) * math.pi) * (1 if ax < 0.17 else 0)
            z += smile * 0.5 * max(0, ax - 0.14) ** 1.2 * 2.2 - (0.03 * mouth if ax < 0.2 else 0)
            y = -1.05 + 0.6 * ax * ax
            pts.append((x * hr, y * hr, z * hr))
        set_curve_points(self.mouth_line, pts)
        self.mouth_open.scale = (hr * (0.13 + 0.06 * mouth), hr * 0.1, hr * 0.16 * mouth + 1e-4)
        self.mouth_open.hide_render = mouth < 0.03
        self.mouth_open.location.z = -hr * (0.36 + 0.12 * mouth)
        for (sh, el, a, e) in ((self.sh[0], self.el[0], arm_l, elbow[0]), (self.sh[1], self.el[1], arm_r, elbow[1])):
            sh.rotation_euler = a
            el.rotation_euler = (e, 0, 0)
        for lp, a in zip(self.legs, legs):
            lp.rotation_euler = (a, 0, 0)
        # tail (in hip space): curls up behind
        rx, ry, rz = P["body"]
        tp = []
        for k in range(8):
            u = k / 7
            x = math.sin(u * 2.2 + tail_wag) * 0.6 * u * rx * (0.6 + abs(math.sin(tail_wag)) * 0.4)
            y = ry * (0.8 + 1.6 * u)
            z = rz * (0.35 + (tail_up * self.P.get('tail_k', 2.6)) * u * u + 0.4 * u)
            tp.append((x, y, z))
        set_curve_points(self.tail, tp, radii=[1.0 - 0.25 * (i / 13) for i in range(14)])
        if self.hat is not None:
            self.hat.rotation_euler = (-0.12 + hat_tilt * 0.3, 0.1 + hat_tilt, 0)
        set_flour(self.mats_flour, flour)

    def hand_world(self, side):
        """side 0=left (screen right when facing camera), 1=right"""
        return self.hand[side].matrix_world.translation.copy()
