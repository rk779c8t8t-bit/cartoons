"""Core 2.5D motion-graphics engine: camera, planes, easing, drawing primitives."""
import math
import numpy as np
import skia

W, H = 1080, 1920
FPS = 60

# ---------------------------------------------------------------- palette
def argb(r, g, b, a=255):
    return (int(a) << 24) | (int(r) << 16) | (int(g) << 8) | int(b)

GOLD = (242, 196, 107)
GOLD_L = (255, 232, 170)
GOLD_D = (176, 112, 42)
RED = (196, 34, 40)
BURG = (74, 10, 18)
INK = (12, 4, 6)

def col(rgb, a=1.0):
    return argb(rgb[0], rgb[1], rgb[2], max(0, min(255, a * 255)))

# ---------------------------------------------------------------- easing
def cl(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def lerp(a, b, t):
    return a + (b - a) * t

def seg(x, a, b):
    return cl((x - a) / (b - a))

def ss(a, b, x):
    t = cl((x - a) / (b - a))
    return t * t * (3 - 2 * t)

def eoe(t):  # ease out expo
    t = cl(t)
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)

def eie(t):  # ease in expo
    t = cl(t)
    return 0.0 if t <= 0 else 2 ** (10 * t - 10)

def eio(t):  # ease in-out cubic
    t = cl(t)
    return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2

def eos(t):  # ease out sine
    return math.sin(cl(t) * math.pi / 2)

def eob(t, s=1.7):  # ease out back
    t = cl(t) - 1
    return t * t * ((s + 1) * t + s) + 1

def eoc(t):
    return 1 - (1 - cl(t)) ** 3

def pulse(x, t0, dec):
    return 0.0 if x < t0 else math.exp(-(x - t0) / dec)

def pulses(x, ts, dec):
    return sum(pulse(x, t, dec) for t in ts)

def wobble(x, f, seed=0.0):
    return (math.sin(x * f + seed) + 0.6 * math.sin(x * f * 1.93 + seed * 2.1) + 0.3 * math.sin(x * f * 3.7 + seed * 3.3)) / 1.9

# ---------------------------------------------------------------- camera
class Cam:
    def __init__(self, pos=(0, 0, -1100), yaw=0.0, pitch=0.0, roll=0.0, f=1100.0, shift=(0, 0)):
        self.x, self.y, self.z = pos
        self.yaw, self.pitch, self.roll, self.f = yaw, pitch, roll, f
        self.sx, self.sy = shift
        self._upd()

    def _upd(self):
        self.cy_, self.sy_ = math.cos(self.yaw), math.sin(self.yaw)
        self.cp_, self.sp_ = math.cos(self.pitch), math.sin(self.pitch)
        self.cr_, self.sr_ = math.cos(self.roll), math.sin(self.roll)

    @staticmethod
    def orbit(pivot, dist, yaw=0.0, pitch=0.0, roll=0.0, f=1100.0, shift=(0, 0)):
        fx = math.sin(yaw) * math.cos(pitch)
        fy = math.sin(pitch)
        fz = math.cos(yaw) * math.cos(pitch)
        pos = (pivot[0] - dist * fx, pivot[1] - dist * fy, pivot[2] - dist * fz)
        return Cam(pos, yaw, pitch, roll, f, shift)

    def to_cam(self, x, y, z):
        dx, dy, dz = x - self.x, y - self.y, z - self.z
        x1 = dx * self.cy_ - dz * self.sy_
        z1 = dx * self.sy_ + dz * self.cy_
        y1 = dy * self.cp_ - z1 * self.sp_
        z2 = dy * self.sp_ + z1 * self.cp_
        return x1, y1, z2

    def proj(self, x, y, z):
        x1, y1, z2 = self.to_cam(x, y, z)
        zz = max(z2, 1e-3)
        u, v = self.f * x1 / zz, self.f * y1 / zz
        u, v = u * self.cr_ - v * self.sr_, u * self.sr_ + v * self.cr_
        return W / 2 + u + self.sx, H / 2 + v + self.sy, z2

    def proj_np(self, P):
        dx, dy, dz = P[:, 0] - self.x, P[:, 1] - self.y, P[:, 2] - self.z
        x1 = dx * self.cy_ - dz * self.sy_
        z1 = dx * self.sy_ + dz * self.cy_
        y1 = dy * self.cp_ - z1 * self.sp_
        z2 = dy * self.sp_ + z1 * self.cp_
        zz = np.maximum(z2, 1e-3)
        u, v = self.f * x1 / zz, self.f * y1 / zz
        u, v = u * self.cr_ - v * self.sr_, u * self.sr_ + v * self.cr_
        return W / 2 + u + self.sx, H / 2 + v + self.sy, z2


def rot3(px, py, pz, ry=0.0, rx=0.0, rz=0.0):
    if rz:
        c, s = math.cos(rz), math.sin(rz)
        px, py = px * c - py * s, px * s + py * c
    if rx:
        c, s = math.cos(rx), math.sin(rx)
        py, pz = py * c - pz * s, py * s + pz * c
    if ry:
        c, s = math.cos(ry), math.sin(ry)
        px, pz = px * c + pz * s, -px * s + pz * c
    return px, py, pz

# ---------------------------------------------------------------- drawing context (main + glow)
class Ctx:
    """Draws simultaneously on the main canvas and (optionally) on a glow canvas."""
    def __init__(self, c, g):
        self.c, self.g = c, g

    def save(self):
        self.c.save(); self.g.save()

    def restore(self):
        self.c.restore(); self.g.restore()

    def concat(self, m):
        self.c.concat(m); self.g.concat(m)

    def translate(self, x, y):
        self.c.translate(x, y); self.g.translate(x, y)

    def rotate(self, d):
        self.c.rotate(d); self.g.rotate(d)

    def scale(self, sx, sy=None):
        sy = sx if sy is None else sy
        self.c.scale(sx, sy); self.g.scale(sx, sy)

    def clip(self, path, aa=True):
        self.c.clipPath(path, skia.ClipOp.kIntersect, aa); self.g.clipPath(path, skia.ClipOp.kIntersect, aa)


def draw_plane(ctx, cam, center, fn, rot=(0.0, 0.0, 0.0), ext=400.0, near=40.0):
    """Map local 2D coordinates of a plane placed in 3D onto the screen (true perspective)."""
    ry, rx, rz = rot
    src, dst = [], []
    for lx, ly in ((-ext, -ext), (ext, -ext), (ext, ext), (-ext, ext)):
        px, py, pz = rot3(lx, ly, 0.0, ry, rx, rz)
        X, Y, Z = cam.proj(center[0] + px, center[1] + py, center[2] + pz)
        if Z < near:
            return False
        src.append(skia.Point(lx, ly)); dst.append(skia.Point(X, Y))
    m = skia.Matrix()
    if not m.setPolyToPoly(src, dst):
        return False
    sc = math.hypot(dst[1].x() - dst[0].x(), dst[1].y() - dst[0].y()) / (2 * ext)
    ctx.save(); ctx.concat(m)
    fn(ctx, sc)
    ctx.restore()
    return True


def paint(color=None, a=1.0, stroke=None, blur=0.0, blend=None, shader=None, cap=None, effect=None, cf=None):
    p = skia.Paint(AntiAlias=True)
    if color is not None:
        p.setColor(col(color, a) if isinstance(color, tuple) else color)
    if shader is not None:
        p.setShader(shader)
        p.setAlphaf(cl(a))
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0.05:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if blend is not None:
        p.setBlendMode(blend)
    if effect is not None:
        p.setPathEffect(effect)
    if cf is not None:
        p.setColorFilter(cf)
    return p

PLUS = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen


def trim(a, b=None):
    if b is None:
        a, b = 0.0, a
    a, b = cl(a), cl(b)
    if b - a <= 0.0005:
        return None
    if a <= 0 and b >= 1:
        return None
    return skia.TrimPathEffect.Make(a, b)


def gold_stroke(ctx, path, width, a=1.0, glow=1.0, prog=1.0, start=0.0, color=GOLD, glow_w=2.5, sc=1.0):
    """Gold line with a soft halo; width given in screen px (sc = px per local unit)."""
    if a <= 0.003 or prog - start <= 0.0005:
        return
    eff = trim(start, prog)
    w = width / max(sc, 1e-4)
    ctx.c.drawPath(path, paint(color, a, stroke=w, effect=eff))
    if glow > 0:
        ctx.g.drawPath(path, paint(color, a * glow, stroke=w * glow_w, effect=eff))


def star_path(r, k=0.16):
    p = skia.Path()
    pts = []
    for i in range(8):
        ang = i * math.pi / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * k
        pts.append((rr * math.cos(ang), rr * math.sin(ang)))
    p.moveTo(*pts[0])
    for i in range(1, 9):
        a0 = pts[(i - 1) % 8]; a1 = pts[i % 8]
        p.quadTo(0, 0, *a1) if i % 2 == 0 and False else p.lineTo(*a1)
    p.close()
    return p

STAR = star_path(1.0, 0.13)


def draw_star(ctx, x, y, r, a=1.0, rot=0.0):
    if a <= 0.01 or r < 0.5:
        return
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(r)
    ctx.c.drawPath(STAR, paint(GOLD_L, a))
    ctx.g.drawPath(STAR, paint(GOLD_L, a))
    ctx.restore()
    ctx.g.drawCircle(x, y, r * 0.5, paint(GOLD, a * 0.8, blur=r * 0.4))


def capsule(p0, p1, r0, r1):
    path = skia.Path()
    path.addCircle(p0[0], p0[1], r0)
    path.addCircle(p1[0], p1[1], r1)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    d = math.hypot(dx, dy) or 1e-3
    nx, ny = -dy / d, dx / d
    q = skia.Path()
    q.moveTo(p0[0] + nx * r0, p0[1] + ny * r0)
    q.lineTo(p1[0] + nx * r1, p1[1] + ny * r1)
    q.lineTo(p1[0] - nx * r1, p1[1] - ny * r1)
    q.lineTo(p0[0] - nx * r0, p0[1] - ny * r0)
    q.close()
    return union(path, q)


def union(*paths):
    out = paths[0]
    for p in paths[1:]:
        r = skia.Op(out, p, skia.PathOp.kUnion_PathOp)
        if r is not None:
            out = r
    return out


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def ellipse_path(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def circle_path(cx, cy, r, start_deg=-90.0):
    p = skia.Path()
    p.addArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), start_deg, 359.9)
    return p


def gold_shader(y0, y1, x0=0.0, x1=0.0):
    return skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)],
        [argb(255, 246, 214), argb(248, 208, 120), argb(196, 128, 44), argb(250, 214, 140), argb(255, 240, 196)],
        [0.0, 0.42, 0.55, 0.8, 1.0])


def tint_cf(t, color=(1.18, 0.86, 0.45), dark=0.0):
    """Lerp from identity colours toward a gold monochrome."""
    lw = (0.3, 0.55, 0.15)
    m = []
    for i in range(3):
        row = [0.0] * 5
        for j in range(3):
            row[j] = (1 - t) * (1.0 if i == j else 0.0) + t * color[i] * lw[j]
        row[4] = 0.0
        m += row
    m += [0, 0, 0, 1, 0]
    return skia.ColorFilters.Matrix(m)


def ik(S, T, L1, L2, prefer=1):
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = math.hypot(dx, dy)
    d = max(1.0, min(d, L1 + L2 - 1.0))
    base = math.atan2(dy, dx)
    ca = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    A = math.acos(max(-1.0, min(1.0, ca)))
    e1 = (S[0] + L1 * math.cos(base + A), S[1] + L1 * math.sin(base + A))
    e2 = (S[0] + L1 * math.cos(base - A), S[1] + L1 * math.sin(base - A))
    hand = (S[0] + d * math.cos(base), S[1] + d * math.sin(base))
    return (e1 if prefer > 0 else e2), hand


def new_surface():
    return skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType))
