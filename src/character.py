"""Animated character rig: stylized head sprite (mesh-warped for head turns,
jaw / lip-sync, blinks, brows) on a hand-built vector body with posable arms.

Local units: origin = neck pivot, y down; a face is ~580 units wide.
"""
import json, math, os
import cv2, numpy as np, skia
from core import ROOT, P, C, lin, rad, path_poly, clamp, lerp, ADD

RIG = json.load(open(os.path.join(ROOT, 'assets', 'chars', 'rig.json')))


class Head:
    def __init__(self, name):
        bgra = cv2.imread(os.path.join(ROOT, 'assets', 'chars', f'{name}_head.png'), cv2.IMREAD_UNCHANGED)
        self.img = cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA)
        self.r = RIG[name]
        h, w = self.img.shape[:2]
        rows = np.where(self.img[..., 3].max(axis=1) > 0)[0]
        yb = rows.max()
        fade = np.clip((yb - np.arange(h)) / 60.0, 0, 1)
        self.img[..., 3] = (self.img[..., 3] * fade[:, None]).astype(np.uint8)
        ncol = self.img[yb - 70:yb - 50, w // 2 - 30:w // 2 + 30, :3].reshape(-1, 3)
        self.neck_col = '#%02x%02x%02x' % tuple(int(v) for v in np.median(ncol, axis=0))
        self.neck_bottom = yb
        self.w, self.h = w, h
        X, Y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
        self.X, self.Y = X, Y
        mx, my, mw = self.r['mouth']
        chin = self.r['chin']
        jaw_half = mw * 3.2
        fx = np.clip(1 - (np.abs(X - mx) / jaw_half) ** 2, 0, 1) ** 1.5
        fy = np.where(Y < my, 0.0, np.where(Y <= chin, 1.0, np.clip(1 - (Y - chin) / (mw * 2.5), 0, 1)))
        # the band right under the mouth line ramps in so the lower lip moves fully
        self.jaw = (fx * fy).astype(np.float32)
        b = np.zeros_like(X)
        for bx, by in self.r['brows']:
            b += np.exp(-(((X - bx) / (mw * 1.9)) ** 2 + ((Y - by) / (mw * 1.0)) ** 2))
        self.brow = b.astype(np.float32)
        ex = [e[0] for e in self.r['eyes']]
        self.cx = (ex[0] + ex[1]) / 2
        self.R = max(self.cx, w - self.cx) * 1.04
        # skin colour sampled between the eyes and brows
        sx, sy = int(self.r['eyes'][0][0]), int((self.r['eyes'][0][1] + self.r['brows'][0][1]) / 2)
        self.skin = tuple(int(v) for v in np.median(
            self.img[sy - 4:sy + 4, sx - 10:sx + 10, :3].reshape(-1, 3), axis=0))
        lx, ly = int(mx), int(my + mw * 0.35)
        self.lip = tuple(int(v) for v in np.median(self.img[ly - 3:ly + 3, lx - 8:lx + 8, :3].reshape(-1, 3), axis=0))

    def render(self, mouth=0.0, blink=0.0, brow=0.0, yaw=0.0, smirk=0.0):
        r = self.r
        mx, my, mw = r['mouth']
        op = mouth * mw * 1.25
        mapy = self.Y - op * self.jaw + brow * mw * 0.35 * self.brow
        img = cv2.remap(self.img, self.X, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        s = max(1, int(round(mw / 17)))
        if op > 1.5:
            # mouth interior: dark lens with teeth and tongue
            m = np.zeros(img.shape[:2], np.uint8)
            cy = my + op * 0.42
            ax = (int(mw * (1.0 - 0.18 * mouth) * 16), int((op * 0.55 + 2) * 16))
            cen = (int(mx * 16), int(cy * 16))
            cv2.ellipse(m, cen, ax, smirk * 6, 0, 360, 255, -1, cv2.LINE_AA, 4)
            mf = (m.astype(np.float32) / 255)[..., None]
            inner = np.zeros_like(img, dtype=np.float32)
            inner[..., :3] = (52, 10, 18)
            yy = self.Y[..., None]
            teeth = np.clip((cy - op * 0.25 - yy) / 2.0 + 0.5, 0, 1)
            tongue = np.clip((yy - (cy + op * 0.18)) / 3.0, 0, 1)
            inner[..., :3] = inner[..., :3] * (1 - teeth) + np.array([238, 228, 214]) * teeth
            inner[..., :3] = inner[..., :3] * (1 - tongue) + np.array([170, 50, 62]) * tongue
            imgf = img.astype(np.float32)
            imgf[..., :3] = imgf[..., :3] * (1 - mf) + inner[..., :3] * mf
            img = imgf.astype(np.uint8)
            # lip outline
            cv2.ellipse(img, cen, ax, smirk * 6, 0, 360, (60, 18, 30, 255), max(2, s * 2), cv2.LINE_AA, 4)
        if blink > 0.05:
            for ex, ey, rw, rh in r['eyes']:
                ey2 = ey - op * 0 - brow * mw * 0.35 * 0.4
                cyl = ey2 - rh * 2.4 * (1 - blink)
                cen = (int(ex * 16), int(cyl * 16))
                ax = (int(rw * 1.25 * 16), int(rh * 1.7 * 16))
                cv2.ellipse(img, cen, ax, 0, 0, 360, self.skin + (255,), -1, cv2.LINE_AA, 4)
                cv2.ellipse(img, cen, ax, 0, 15, 165, (40, 14, 22, 255), max(2, s * 2), cv2.LINE_AA, 4)
        if abs(yaw) > 0.002:
            u = np.clip((self.X - self.cx) / self.R, -0.999, 0.999)
            th = np.arcsin(u) - yaw
            mapx = (self.cx + self.R * np.sin(np.clip(th, -1.5707, 1.5707))).astype(np.float32)
            # slight perspective: far side shrinks vertically
            k = 1 + 0.10 * np.sin(yaw) * u
            mapy2 = (r['pivot'][1] * 0.55 + (self.Y - r['pivot'][1] * 0.55) / k).astype(np.float32)
            img = cv2.remap(img, mapx, mapy2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return img


# ------------------------------------------------------------------ poses
# Arm pose for the screen-left arm, mirrored for the screen-right arm:
# (upper angle, forearm angle, upper length factor, fore length factor, hand, hand angle offset)
# angle 0 = straight down, +pi/2 = toward the body centre.
POSES = {
    'rest':      (0.08, 0.20, 1.0, 1.0, 'fist', 0.0),
    'cross':     (0.42, 1.62, 1.0, 0.95, 'fist', 0.0),
    'cross_b':   (0.38, 1.50, 1.0, 0.95, 'fist', 0.0),
    'mic':       (0.30, 2.62, 1.0, 0.92, 'mic', 0.0),
    'point_self': (0.32, 2.05, 1.0, 0.85, 'point', 0.35),
    'beckon':    (-0.35, 3.05, 0.95, 0.85, 'open', 0.0),
    'point_up':  (-0.55, 3.45, 1.0, 0.95, 'point', 0.0),
    'point_fwd': (0.25, 2.30, 0.8, 0.55, 'point', 0.6),
    'open':      (-0.55, -1.05, 1.0, 0.9, 'open', 0.0),
    'fist_up':   (-0.45, 3.25, 1.0, 0.9, 'fist', 0.0),
    'chest':     (0.30, 1.95, 1.0, 0.80, 'open', 0.3),
    'down_out':  (-0.35, -0.25, 1.0, 1.0, 'open', 0.0),
}


def blend_pose(a, b, t):
    pa = POSES[a] if isinstance(a, str) else a
    pb = POSES[b] if isinstance(b, str) else b
    return tuple(lerp(pa[k], pb[k], t) for k in range(4)) + (pa[4] if t < 0.5 else pb[4], lerp(pa[5], pb[5], t))


class Character:
    def __init__(self, name):
        self.name = name
        self.head = Head(name)
        r = RIG[name]
        self.pivot = r['pivot']
        if name == 'eminem':
            self.sleeve, self.sleeve_dk, self.sleeve_hi = '#1a161d', '#0d0b10', '#3d3743'
            self.shoulder_x, self.shoulder_y = 390, 150
            self.upper, self.fore = 340, 320
            self.arm_w = 150
        else:
            self.sleeve, self.sleeve_dk, self.sleeve_hi = '#0f6466', '#083f42', '#2d8c86'
            self.shoulder_x, self.shoulder_y = 370, 150
            self.upper, self.fore = 320, 300
            self.arm_w = 140
        self.skin = '#%02x%02x%02x' % tuple(r['skin'])
        self.skin_dk = '#%02x%02x%02x' % tuple(int(v * 0.72) for v in r['skin'])

    # ------------------------------------------------------------ body pieces
    def torso_path(self):
        sx = self.shoulder_x + 110
        p = skia.Path()
        p.moveTo(-200, -60)
        p.cubicTo(-300, 0, -sx + 120, 30, -sx + 10, 150)
        p.cubicTo(-sx - 40, 300, -sx - 20, 900, -sx - 40, 2000)
        p.lineTo(sx + 40, 2000)
        p.cubicTo(sx + 20, 900, sx + 40, 300, sx - 10, 200)
        p.cubicTo(sx - 120, 30, 300, 0, 200, -60)
        p.close()
        return p

    def draw_torso(self, c, t, light):
        tp = self.torso_path()
        if self.name == 'eminem':
            c.drawPath(tp, P('#16131a'))
            c.save(); c.clipPath(tp, doAntiAlias=True)
            c.drawPath(path_poly([(120, -100), (1000, -100), (1000, 2100), (300, 2100)]), P('#0b090d'))
            # shirt (grey tee) in the jacket opening
            c.drawPath(path_poly([(-220, -60), (220, -60), (290, 2100), (-290, 2100)]), P('#85838b'))
            c.drawPath(path_poly([(60, -60), (220, -60), (290, 2100), (120, 2100)]), P('#6a6870'))
            # jacket front panels
            for sgn in (-1, 1):
                pp = skia.Path()
                pp.moveTo(sgn * 215, -60)
                pp.cubicTo(sgn * 175, 300, sgn * 200, 900, sgn * 260, 2100)
                pp.lineTo(sgn * 1000, 2100); pp.lineTo(sgn * 1000, -60); pp.close()
                c.drawPath(pp, P('#17141b' if sgn < 0 else '#0e0c11'))
                c.drawPath(pp, P('#000000', 1.0, stroke=10))
                # zipper edge highlight
                ze = skia.Path(); ze.moveTo(sgn * 215, -40); ze.cubicTo(sgn * 175, 300, sgn * 200, 900, sgn * 260, 2100)
                c.drawPath(ze, P('#55505c', 0.9, stroke=7))
            # white trim stripes (track-jacket nod to the era)
            c.restore()
            c.drawPath(tp, P('#050306', stroke=14))
            # shoulder highlight
            hl = skia.Path(); hl.moveTo(-self.shoulder_x - 90, 110); hl.cubicTo(-400, 20, -300, 0, -230, -40)
            c.drawPath(hl, P('#4a4452', 0.9, stroke=16))
        else:
            c.drawPath(tp, P('#0f5c60'))
            c.save(); c.clipPath(tp, doAntiAlias=True)
            c.drawPath(path_poly([(180, -100), (1000, -100), (1000, 2100), (330, 2100)]), P('#0a4245'))
            # red centre panel
            c.drawPath(path_poly([(-170, -60), (170, -60), (230, 2100), (-230, 2100)]), P('#a3162a'))
            c.drawPath(path_poly([(30, -60), (170, -60), (230, 2100), (40, 2100)]), P('#82101f'))
            c.drawPath(path_poly([(-6, -60), (6, -60), (8, 2100), (-8, 2100)]), P('#4c0710'))
            # gold trim with ornament
            for sgn in (-1, 1):
                tr = path_poly([(sgn * 160, -60), (sgn * 230, -60), (sgn * 300, 2100), (sgn * 215, 2100)])
                c.drawPath(tr, P('#ffffff', shader=lin(0, -60, 0, 1400, ['#f3c95a', '#c58a26', '#e9b544'])))
                for k in range(14):
                    y = 20 + k * 120 + (t * 0) % 1
                    x = sgn * (195 + y * 0.03)
                    lf = skia.Path(); lf.addOval(skia.Rect(-11, -28, 11, 28))
                    c.save(); c.translate(x, y); c.rotate(sgn * (25 if k % 2 else -25))
                    c.drawPath(lf, P('#7d4a10')); c.restore()
                    c.drawCircle(x + sgn * 4, y + 60, 7, P('#fff0b8'))
                c.drawPath(tr, P('#5a3207', stroke=6))
                # white flowers on teal
                for k in range(5):
                    fx, fy = sgn * (300 + 50 * (k % 2)), 260 + k * 240
                    for a in range(5):
                        ang = a * 2 * math.pi / 5 + t * 0.2
                        c.drawCircle(fx + 20 * math.cos(ang), fy + 20 * math.sin(ang), 15, P('#f4efe2'))
                    c.drawCircle(fx, fy, 9, P('#f2b230'))
                # gold vine on teal
                vp = skia.Path(); vp.moveTo(sgn * 250, 0)
                vp.cubicTo(sgn * 420, 300, sgn * 280, 600, sgn * 400, 900)
                vp.cubicTo(sgn * 480, 1150, sgn * 320, 1300, sgn * 380, 1700)
                c.drawPath(vp, P('#d9a93a', 0.85, stroke=12))
            c.restore()
            c.drawPath(tp, P('#062a2c', stroke=14))
            hl = skia.Path(); hl.moveTo(-self.shoulder_x - 90, 110); hl.cubicTo(-400, 20, -300, 0, -230, -40)
            c.drawPath(hl, P('#3aa39a', 0.8, stroke=14))

    def draw_front(self, c, t):
        """Pieces that sit in front of the neck: collar, chain."""
        if self.name == 'eminem':
            # tee neckline
            nk = skia.Path()
            nk.moveTo(-200, -30); nk.quadTo(0, 120, 200, -30); nk.lineTo(196, 190); nk.lineTo(-196, 190); nk.close()
            c.drawPath(nk, P('#85838b'))
            c.drawPath(path_poly([(60, 45), (200, -30), (196, 190), (60, 190)]), P('#6a6870'))
            rib = skia.Path(); rib.moveTo(-200, -30); rib.quadTo(0, 120, 200, -30)
            c.drawPath(rib, P('#9c9aa3', stroke=22)); c.drawPath(rib, P('#2a272e', stroke=4))
            # popped jacket collar
            for sgn in (-1, 1):
                cl = path_poly([(sgn * 185, -130), (sgn * 285, -50), (sgn * 260, 140), (sgn * 212, 30)])
                c.drawPath(cl, P('#1f1b24' if sgn < 0 else '#121015'))
                c.drawPath(cl, P('#000000', stroke=8))
            # ball chain
            n = 34
            for i in range(n + 1):
                u = i / n
                x = lerp(-150, 150, u)
                y = -20 + 300 * (1 - (2 * u - 1) ** 2) ** 0.9
                c.drawCircle(x, y, 8, P('#2b2a30'))
                c.drawCircle(x - 1.5, y - 1.5, 5.5, P('#d8d8e0'))
        else:
            # mandarin stand collar, red with gold edge
            for sgn in (-1, 1):
                cl = skia.Path()
                cl.moveTo(sgn * 175, -150)
                cl.cubicTo(sgn * 185, -40, sgn * 150, 40, sgn * 10, 60)
                cl.lineTo(sgn * 10, -10)
                cl.cubicTo(sgn * 90, -20, sgn * 125, -90, sgn * 128, -165)
                cl.close()
                c.drawPath(cl, P('#ffffff', shader=lin(0, -190, 0, 80, ['#c2182e', '#8e0f20'])))
                c.drawPath(cl, P('#e7b444', stroke=11))
                c.drawPath(cl, P('#5a3207', stroke=3))
            for k in range(3):
                c.drawCircle(0, 110 + k * 130, 11, P('#f1c45a')); c.drawCircle(0, 110 + k * 130, 11, P('#5a3207', stroke=3))

    # ------------------------------------------------------------ arms
    def arm_points(self, side, pose):
        a1, a2, l1, l2 = pose[:4]
        sx = -side * self.shoulder_x  # side -1 => screen-left arm
        sx = side * self.shoulder_x
        mir = -side  # screen-left arm: toward centre is +x
        S = (sx, self.shoulder_y)
        E = (S[0] + mir * math.sin(a1) * self.upper * l1, S[1] + math.cos(a1) * self.upper * l1)
        Wr = (E[0] + mir * math.sin(a2) * self.fore * l2, E[1] + math.cos(a2) * self.fore * l2)
        return S, E, Wr

    def draw_arm(self, c, side, pose, t):
        S, E, Wr = self.arm_points(side, pose)
        hand, hang = pose[4], pose[5]
        mir = -side
        w = self.arm_w
        seg = skia.Path(); seg.moveTo(*S); seg.lineTo(*E)
        fseg = skia.Path(); fseg.moveTo(*E); fseg.lineTo(*Wr)
        out = P('#060205', stroke=w + 16)
        c.drawPath(seg, out)
        c.drawPath(seg, P(self.sleeve, stroke=w))
        # sleeve shading line
        if self.name == 'eminem':
            c.drawPath(fseg, P('#060205', stroke=w * 0.92 + 16))
            c.drawPath(fseg, P(self.sleeve, stroke=w * 0.92))
            # white stripe
            c.drawPath(seg, P('#3d3743', 0.9, stroke=w * 0.18))
            c.drawPath(fseg, P('#3d3743', 0.9, stroke=w * 0.16))
            c.drawCircle(*E, w * 0.46, P(self.sleeve))
            cuff_col = '#0b090d'
            # cuff
            dx, dy = Wr[0] - E[0], Wr[1] - E[1]; L = math.hypot(dx, dy) + 1e-6
            cf = skia.Path(); cf.moveTo(Wr[0] - dx / L * 40, Wr[1] - dy / L * 40); cf.lineTo(*Wr)
            c.drawPath(cf, P(cuff_col, stroke=w * 0.95))
        else:
            c.drawPath(fseg, P('#3a1a10', stroke=w * 0.72 + 14))
            c.drawPath(fseg, P(self.skin, stroke=w * 0.72))
            c.drawPath(fseg, P(self.skin_dk, 0.5, stroke=w * 0.25))
            # short sleeve with gold/red cuff ending at the elbow
            dx, dy = E[0] - S[0], E[1] - S[1]; L = math.hypot(dx, dy) + 1e-6
            cf = skia.Path(); cf.moveTo(E[0] - dx / L * 70, E[1] - dy / L * 70); cf.lineTo(E[0] + dx / L * 25, E[1] + dy / L * 25)
            c.drawPath(cf, P('#5a3207', stroke=w + 22, cap=skia.Paint.kButt_Cap))
            c.drawPath(cf, P('#e3b041', stroke=w + 14, cap=skia.Paint.kButt_Cap))
            cf2 = skia.Path(); cf2.moveTo(E[0] - dx / L * 45, E[1] - dy / L * 45); cf2.lineTo(E[0] + dx / L * 5, E[1] + dy / L * 5)
            c.drawPath(cf2, P('#a3162a', stroke=w + 14, cap=skia.Paint.kButt_Cap))
        self.draw_hand(c, Wr, math.atan2(Wr[1] - E[1], Wr[0] - E[0]) + mir * hang, hand, mir, t)

    def draw_hand(self, c, Wr, ang, kind, mir, t):
        c.save(); c.translate(*Wr); c.rotate(math.degrees(ang) - 90); c.scale(0.78, 0.78)
        sk, ol = P(self.skin), P('#3a1a10', stroke=9)
        dk = P(self.skin_dk, 0.8)
        if kind == 'mic':
            # mic in fist, pointing along the forearm direction
            body = skia.RRect.MakeRectXY(skia.Rect(-26, 20, 26, 300), 20, 20)
            c.drawRRect(body, P('#141216')); c.drawRRect(body, P('#000000', stroke=6))
            c.drawCircle(0, 330, 62, P('#000000'))
            c.drawCircle(0, 330, 56, P('#ffffff', shader=rad(-18, 312, 70, ['#e8e8ee', '#8a8a94', '#3a3a40'])))
            for k in range(-2, 3):
                c.drawLine(k * 20, 282, k * 20, 378, P('#2a2a30', 0.6, stroke=3))
            c.drawLine(-50, 330, 50, 330, P('#2a2a30', 0.6, stroke=3))
        palm = skia.Rect(-70, -10, 70, 130)
        if kind == 'open':
            for k, (fx, ln) in enumerate([(-48, 120), (-16, 140), (16, 135), (46, 110)]):
                fr = skia.RRect.MakeRectXY(skia.Rect(fx - 17, 80, fx + 17, 80 + ln), 17, 17)
                c.drawRRect(fr, ol); c.drawRRect(fr, sk)
            th = skia.Path(); th.addRRect(skia.RRect.MakeRectXY(skia.Rect(-17, 0, 17, 110), 17, 17))
            c.save(); c.translate(mir * -60, 40); c.rotate(mir * 50); c.drawPath(th, ol); c.drawPath(th, sk); c.restore()
            c.drawOval(palm, ol); c.drawOval(palm, sk)
        else:
            if kind == 'point':
                fr = skia.RRect.MakeRectXY(skia.Rect(-18, 60, 18, 230), 18, 18)
                c.drawRRect(fr, ol); c.drawRRect(fr, sk)
            fist = skia.Rect(-72, -5, 72, 135)
            c.drawRoundRect(fist, 55, 55, ol); c.drawRoundRect(fist, 55, 55, sk)
            for k in range(3 if kind == 'point' else 4):
                x = -50 + k * 32 + (32 if kind == 'point' else 0) * 0
                c.drawLine(x, 85, x, 125, P('#3a1a10', 0.55, stroke=5))
            c.drawRoundRect(skia.Rect(-72, 70, -20, 135), 25, 25, dk) if mir > 0 else None
        c.restore()

    # ------------------------------------------------------------ full draw
    def draw(self, c, x, y, s, t, mouth=0.0, blink=0.0, brow=0.0, yaw=0.0, roll=0.0, nod=0.0,
             poses=('rest', 'rest'), bounce=0.0, lean=0.0, rim=None, tint=None, alpha=1.0, front_arm=None,
             shadow=True):
        """poses = (screen-left arm pose, screen-right arm pose); each a name or tuple."""
        if alpha <= 0.01:
            return
        pl = POSES[poses[0]] if isinstance(poses[0], str) else poses[0]
        pr = POSES[poses[1]] if isinstance(poses[1], str) else poses[1]
        lp = skia.Paint()
        if rim:
            lp.setImageFilter(skia.ImageFilters.DropShadow(0, 0, rim[2] * s, rim[2] * s, C(rim[0], rim[1]), None))
        lp.setAlphaf(alpha)
        c.saveLayer(None, lp)
        c.save()
        c.translate(x, y + bounce)
        c.scale(s, s)
        c.rotate(lean)
        self.draw_torso(c, t, rim)
        # back arm(s): crossed arms -> left one behind; mic arm in front
        front = front_arm
        order = [(-1, pl), (1, pr)]
        if front is None:
            front = 1 if pr[4] in ('mic', 'point', 'open') and pr[1] > 1.2 else (-1 if pl[1] > 1.2 else None)
        backs = [o for o in order if o[0] != front]
        fronts = [o for o in order if o[0] == front]
        for side, pose in backs:
            if pose[1] < 2.3:
                self.draw_arm(c, side, pose, t)
        # neck (vector) bridging the head sprite and the collar
        nw = 100 if self.name == 'eminem' else 92
        ntop = self.head.neck_bottom - self.pivot[1] - 200
        nk = skia.Path(); nk.moveTo(-nw, ntop); nk.lineTo(nw, ntop); nk.quadTo(nw + 5, -40, nw + 40, 40)
        nk.lineTo(-nw - 40, 40); nk.quadTo(-nw - 5, -40, -nw, ntop); nk.close()
        c.drawPath(nk, P('#ffffff', shader=lin(0, ntop, 0, 40, [self.head.neck_col, self.skin_dk])))
        c.drawPath(path_poly([(nw * 0.25, ntop), (nw, ntop), (nw + 40, 40), (nw * 0.35, 40)]), P('#000000', 0.16))
        # head
        img = self.head.render(mouth=mouth, blink=blink, brow=brow, yaw=yaw)
        sk = skia.Image.fromarray(img, colorType=skia.kRGBA_8888_ColorType)
        c.save()
        c.translate(0, nod * 30)
        c.rotate(roll)
        c.translate(yaw * -40, 0)
        c.drawImage(sk, -self.pivot[0], -self.pivot[1], skia.SamplingOptions(skia.FilterMode.kLinear), None)
        c.restore()
        self.draw_front(c, t)
        for side, pose in backs:
            if pose[1] >= 2.3:
                self.draw_arm(c, side, pose, t)
        for side, pose in fronts:
            self.draw_arm(c, side, pose, t)
        c.restore()
        if tint:
            # scene light: gradient laid only onto the character pixels
            tp = skia.Paint(); tp.setShader(tint); tp.setBlendMode(skia.BlendMode.kSrcATop)
            c.drawPaint(tp)
        c.restore()
