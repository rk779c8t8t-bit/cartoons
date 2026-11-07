"""Background / environment generators drawn with skia (flat-vector style of the reference)."""
import math
import numpy as np, skia
from core import *

_rng = np.random.default_rng(11)


def bg_grad(c, top, bottom, mid=None):
    cols = [top, mid, bottom] if mid else [top, bottom]
    c.drawRect(skia.Rect(-400, -400, W + 400, H + 400), P('#ffffff', shader=lin(0, 0, 0, H, cols)))


def vignette(c, strength=0.75):
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffffff', shader=rad(W / 2, H * 0.45, H * 0.75,
               [C('#000000', 0), C('#000000', 0), C('#000000', strength)], [0, 0.55, 1.0])))


def glow_spot(c, x, y, r, color, a):
    if a <= 0.005:
        return
    c.drawCircle(x, y, r, P('#ffffff', shader=rad(x, y, r, [C(color, a), C(color, 0)]), blend=ADD))


# ------------------------------------------------------------------ particles
class Dust:
    """3D particle field projected through a pinhole camera."""
    def __init__(self, n, seed, spread=(1600, 2600), depth=(200, 3000)):
        r = np.random.default_rng(seed)
        self.p = np.stack([r.uniform(-spread[0], spread[0], n), r.uniform(-spread[1], spread[1], n),
                           r.uniform(depth[0], depth[1], n)], 1)
        self.size = r.uniform(1.5, 5.0, n)
        self.ph = r.uniform(0, 6.28, n)
        self.depth = depth

    def draw(self, c, t, z_travel, color='#ffd27a', alpha=1.0, f=900, cx=W / 2, cy=H / 2, streak=0.0, twinkle=True):
        if alpha <= 0.01:
            return
        z = (self.p[:, 2] - z_travel) % (self.depth[1] - self.depth[0]) + self.depth[0]
        x = cx + self.p[:, 0] / z * f
        y = cy + self.p[:, 1] / z * f
        rr = self.size * f / z
        fade = np.clip((self.depth[1] - z) / 600, 0, 1) * np.clip((z - self.depth[0]) / 150, 0, 1)
        pg = P(color, 1, blend=ADD)
        for i in range(len(z)):
            a = alpha * fade[i] * ((0.55 + 0.45 * math.sin(t * 5 + self.ph[i])) if twinkle else 1)
            if a < 0.02 or not (-50 < x[i] < W + 50 and -50 < y[i] < H + 50):
                continue
            r_ = max(0.6, min(rr[i], 18))
            if streak > 0:
                dx, dy = (x[i] - cx), (y[i] - cy)
                L = math.hypot(dx, dy) + 1e-6
                k = streak * r_ * 6
                pg.setAlphaf(a * 0.8)
                pg.setStrokeWidth(r_ * 0.9); pg.setStyle(skia.Paint.kStroke_Style); pg.setStrokeCap(skia.Paint.kRound_Cap)
                c.drawLine(x[i] - dx / L * k, y[i] - dy / L * k, x[i], y[i], pg)
                pg.setStyle(skia.Paint.kFill_Style)
            else:
                pg.setAlphaf(a * 0.35)
                c.drawCircle(x[i], y[i], r_ * 2.6, pg)
                pg.setAlphaf(a)
                c.drawCircle(x[i], y[i], r_, pg)


class Embers:
    def __init__(self, n, seed):
        r = np.random.default_rng(seed)
        self.x = r.uniform(0, W, n); self.v = r.uniform(120, 420, n); self.ph = r.uniform(0, 100, n)
        self.s = r.uniform(2, 7, n); self.life = r.uniform(1.5, 3.5, n)

    def draw(self, c, t, base_y=H, alpha=1.0, boost=1.0):
        if alpha <= 0.01:
            return
        for i in range(len(self.x)):
            age = (t + self.ph[i]) % self.life[i]
            y = base_y - age * self.v[i] * boost
            x = self.x[i] + math.sin(age * 2.3 + self.ph[i]) * 40 + age * 30
            a = alpha * (1 - age / self.life[i]) * min(1, age * 4)
            if a < 0.02:
                continue
            col = '#ffd04a' if i % 3 else '#ff6a1a'
            c.drawCircle(x, y, self.s[i] * 2.8, P(col, a * 0.35, blend=ADD))
            c.drawCircle(x, y, self.s[i], P('#fff1b0', a))


# ------------------------------------------------------------------ fire
FLAME_LAYERS = [('#7d0a12', 1.00, 0.8), ('#c8141d', 0.86, 1.0), ('#ef4a1c', 0.68, 1.25),
                ('#f9921e', 0.48, 1.5), ('#ffd04a', 0.28, 1.9)]


def flames(c, t, base_y, h, x0=-60, width=W + 120, n=11, seed=0, alpha=1.0, layers=FLAME_LAYERS):
    if alpha <= 0.01 or h <= 2:
        return
    for li, (col, hs, sp) in enumerate(layers):
        path = skia.Path()
        path.addRect(skia.Rect(x0 - 50, base_y - 2, x0 + width + 50, H + 400))
        nn = n + li * 2
        tw = width / nn
        for i in range(-1, nn + 1):
            off = (li * 0.37 + (i % 2) * 0.5) * tw
            xc = x0 + i * tw + off + math.sin(t * 1.7 + i * 1.3 + li) * tw * 0.15
            hh = h * hs * (0.45 + 0.55 * (noise1(t * 2.6 * sp + i * 1.91 + li * 7.3, seed + li) + 1) / 2)
            w2 = tw * (0.62 + 0.1 * math.sin(i * 2.1))
            tip = xc + math.sin(t * 5.3 * sp + i * 2.7) * w2 * 0.45
            fp = skia.Path()
            fp.moveTo(xc - w2, base_y + 5)
            fp.quadTo(xc - w2 * 0.35, base_y - hh * 0.55, tip, base_y - hh)
            fp.quadTo(xc + w2 * 0.45, base_y - hh * 0.45, xc + w2, base_y + 5)
            fp.close()
            path.addPath(fp)
        pp = P(col, alpha)
        c.drawPath(path, pp)
    # hot glow
    c.drawRect(skia.Rect(x0, base_y - h * 1.2, x0 + width, base_y + 200),
               P('#ffffff', shader=lin(0, base_y - h * 1.2, 0, base_y + 100,
                                         [C('#ff6a1a', 0), C('#ff8a2a', 0.35 * alpha)]), blend=ADD))


# ------------------------------------------------------------------ city skyline
class Skyline:
    def __init__(self, seed, n=26, hmin=200, hmax=760):
        r = np.random.default_rng(seed)
        self.b = []
        x = -200
        while x < W + 200:
            w = r.uniform(70, 170)
            h = r.uniform(hmin, hmax)
            wins = []
            for wy in range(30, int(h) - 20, 34):
                for wx in range(14, int(w) - 18, 26):
                    if r.random() < 0.42:
                        wins.append((wx, wy, r.uniform(0, 6.28)))
            self.b.append((x, w, h, wins, r.random() < 0.3))
            x += w + r.uniform(-10, 18)

    def draw(self, c, t, base_y, col='#1a0408', win='#ffb347', alpha=1.0, win_a=1.0, xoff=0):
        if alpha <= 0.01:
            return
        bp = P(col, alpha)
        for x, w, h, wins, ant in self.b:
            xx = x + xoff
            c.drawRect(skia.Rect(xx, base_y - h, xx + w, base_y + 600), bp)
            if ant:
                c.drawRect(skia.Rect(xx + w / 2 - 3, base_y - h - 60, xx + w / 2 + 3, base_y - h), bp)
            if win_a > 0.01:
                for wx, wy, ph in wins:
                    a = alpha * win_a * (0.55 + 0.45 * math.sin(t * 1.5 + ph))
                    c.drawRect(skia.Rect(xx + wx, base_y - h + wy, xx + wx + 10, base_y - h + wy + 14), P(win, a))


# ------------------------------------------------------------------ rays / sunburst
def rays(c, t, cx, cy, n, col_a, col_b, rot, alpha=1.0, r=3000, bg=True):
    if bg:
        c.drawCircle(cx, cy, r, P(col_b, alpha))
    p = skia.Path()
    for i in range(n):
        a0 = rot + i * 2 * math.pi / n
        a1 = a0 + math.pi / n
        p.moveTo(cx, cy)
        p.lineTo(cx + r * math.cos(a0), cy + r * math.sin(a0))
        p.lineTo(cx + r * math.cos(a1), cy + r * math.sin(a1))
        p.close()
    c.drawPath(p, P(col_a, alpha))


def halftone(c, x0, y0, x1, y1, step, rmax, col, alpha, grad_dir=1):
    pp = P(col, alpha)
    j = 0
    y = y0
    while y < y1:
        k = (y - y0) / max(1, (y1 - y0))
        r = rmax * (k if grad_dir > 0 else 1 - k)
        if r > 0.5:
            x = x0 + (step / 2 if j % 2 else 0)
            while x < x1:
                c.drawCircle(x, y, r, pp)
                x += step
        y += step * 0.866
        j += 1


# ------------------------------------------------------------------ spotlights
def spot_beam(c, x_top, y_top, x_bot, y_bot, w_top, w_bot, col, a):
    if a <= 0.01:
        return
    p = path_poly([(x_top - w_top, y_top), (x_top + w_top, y_top), (x_bot + w_bot, y_bot), (x_bot - w_bot, y_bot)])
    c.drawPath(p, P('#ffffff', shader=lin(x_top, y_top, x_bot, y_bot, [C(col, a), C(col, a * 0.25), C(col, 0)],
                                           [0, 0.7, 1.0]), blend=ADD))


def floor_ring(c, cx, cy, rx, ry, a, t):
    if a <= 0.01:
        return
    r = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
    c.drawOval(r, P('#ffffff', shader=rad(cx, cy, rx, [C('#ffcf6b', 0.35 * a), C('#ffcf6b', 0)]), blend=ADD))
    c.drawOval(r, P('#e2a93b', a * 0.4, stroke=22, blur=10, blend=ADD))
    c.drawOval(r, P('#ffd37a', a, stroke=6))
    r2 = skia.Rect(cx - rx * 0.8, cy - ry * 0.8, cx + rx * 0.8, cy + ry * 0.8)
    pp = P('#e2a93b', a * 0.7, stroke=3)
    pp.setPathEffect(skia.DashPathEffect.Make([30, 18], t * 80))
    c.drawOval(r2, pp)


# ------------------------------------------------------------------ 3D wire geometry
_phi = (1 + 5 ** 0.5) / 2
ICO_V = np.array([(-1, _phi, 0), (1, _phi, 0), (-1, -_phi, 0), (1, -_phi, 0), (0, -1, _phi), (0, 1, _phi),
                  (0, -1, -_phi), (0, 1, -_phi), (_phi, 0, -1), (_phi, 0, 1), (-_phi, 0, -1), (-_phi, 0, 1)], float)
ICO_V /= np.linalg.norm(ICO_V[0])
ICO_E = sorted({tuple(sorted((i, j))) for i in range(12) for j in range(12)
                if i < j and abs(np.linalg.norm(ICO_V[i] - ICO_V[j]) - np.linalg.norm(ICO_V[0] - ICO_V[1])) < 1e-3})


def rotm(ax, ay, az):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def project(pts, cx, cy, f=1100, zc=4.0, scale=1.0):
    z = pts[:, 2] + zc
    return np.stack([cx + pts[:, 0] * scale * f / z / zc, cy + pts[:, 1] * scale * f / z / zc], 1), z


def wire_ico(c, t, cx, cy, size, rot, draw_p=1.0, alpha=1.0, col='#ffcf6b', width=4):
    if alpha <= 0.01:
        return
    pts = ICO_V @ rotm(*rot).T
    P2, z = project(pts, cx, cy, scale=size)
    n = len(ICO_E)
    for k, (i, j) in enumerate(ICO_E):
        pe = clamp(draw_p * n - k * 0.6 * (draw_p < 1))
        pe = clamp(draw_p * 1.6 - k / n * 0.6) if draw_p < 1 else 1.0
        if pe <= 0:
            continue
        depth = clamp(1.3 - (z[i] + z[j]) / 2 / 5)
        a = alpha * (0.35 + 0.65 * depth)
        x0, y0 = P2[i]; x1, y1 = P2[j]
        x1, y1 = x0 + (x1 - x0) * pe, y0 + (y1 - y0) * pe
        c.drawLine(x0, y0, x1, y1, P(col, a * 0.5, stroke=width * 4, blur=width * 2, blend=ADD))
        c.drawLine(x0, y0, x1, y1, P('#fff3c4', a, stroke=width))
    for i in range(12):
        c.drawCircle(*P2[i], width * 2.2 * draw_p, P('#fff3c4', alpha * draw_p))


def ring3d(c, cx, cy, r, tilt, spin, alpha, col='#e2a93b', width=4, dash=None, t=0):
    if alpha <= 0.01:
        return
    c.save(); c.translate(cx, cy); c.rotate(math.degrees(spin))
    rect = skia.Rect(-r, -r * abs(math.cos(tilt)), r, r * abs(math.cos(tilt)))
    c.drawOval(rect, P(col, alpha * 0.45, stroke=width * 4, blur=width * 2.5, blend=ADD))
    pp = P(col, alpha, stroke=width)
    if dash:
        pp.setPathEffect(skia.DashPathEffect.Make(dash, t * 120))
    c.drawOval(rect, pp)
    c.restore()


def shockwave(c, cx, cy, p, rmax, col='#ffd37a', width=30):
    if p <= 0 or p >= 1:
        return
    r = rmax * e_out(p)
    a = (1 - p) ** 1.5
    c.drawCircle(cx, cy, r, P(col, a * 0.5, stroke=width * (1 - p) + 2, blur=12, blend=ADD))
    c.drawCircle(cx, cy, r, P('#fff6d8', a, stroke=max(1.5, width * 0.25 * (1 - p))))


# ------------------------------------------------------------------ crowd (reference: rows of suits)
def crowd_person(c, x, y, s, body='#3a2a34', face='#c9a088', tie='#b5121b', a=1.0, turn=0.0):
    if a <= 0.01:
        return
    c.save(); c.translate(x, y); c.scale(s, s)
    sh = skia.Path(); sh.moveTo(-60, 0); sh.cubicTo(-62, -70, -40, -95, 0, -95); sh.cubicTo(40, -95, 62, -70, 60, 0)
    sh.lineTo(66, 200); sh.lineTo(-66, 200); sh.close()
    c.drawPath(sh, P(body, a))
    c.drawPath(path_poly([(-16, -95), (16, -95), (0, -40)]), P('#efe6d8', a))
    c.drawPath(path_poly([(-6, -88), (6, -88), (8, -30), (0, -18), (-8, -30)]), P(tie, a))
    c.drawRect(skia.Rect(-14, -125, 14, -92), P(face, a))
    c.drawOval(skia.Rect(-30 + turn * 8, -185, 30 + turn * 8, -110), P(face, a))
    c.drawOval(skia.Rect(-31 + turn * 8, -190, 31 + turn * 8, -150), P('#2a1a12', a))
    c.restore()


def grain(c, t, amount=0.06, tex=[]):
    if not tex:
        r = np.random.default_rng(5)
        for k in range(6):
            n = (r.random((480, 270)) * 255).astype(np.uint8)
            rgba = np.dstack([n, n, n, np.full_like(n, 255)])
            tex.append(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType))
    img = tex[int(t * FPS) % len(tex)]
    p = skia.Paint(); p.setAlphaf(amount); p.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(img, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear), p)
