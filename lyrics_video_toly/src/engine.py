"""Rendering engine: kinetic typography + VFX on numpy/OpenCV.

Everything is a pure function of time, so any frame can be rendered
independently (this is what makes multi-process rendering possible).
"""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "fonts")
FONTS = {
    "black": "InterDisplay-Black.otf",
    "italic": "InterDisplay-BlackItalic.otf",
    "xbold": "InterDisplay-ExtraBold.otf",
    "mono": "JetBrainsMono-ExtraBold.ttf",
    "unb": "Unbounded-Black.ttf",
    "unbx": "Unbounded-ExtraBold.ttf",
    "dela": "DelaGothicOne.ttf",
}
REF = 200.0  # layout reference font size


# ----------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def smooth(x):
    x = clamp(x); return x * x * (3 - 2 * x)

def out_expo(x):
    x = clamp(x); return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)

def out_cubic(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def in_cubic(x):
    x = clamp(x); return x ** 3

def in_out_cubic(x):
    x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def out_back(x, s=1.9):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

def out_elastic(x):
    x = clamp(x)
    if x in (0.0, 1.0): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1

def lerp(a, b, x):
    return a + (b - a) * x

def decay(t, t0, d):
    """0 before t0, jumps to 1 at t0, exponential decay with time constant d."""
    if t < t0: return 0.0
    return math.exp(-(t - t0) / d)

def window(t, t0, t1, fin=0.05, fout=0.05):
    if t < t0 - 1e-9 or t > t1 + fout: return 0.0
    a = smooth((t - t0) / fin) if fin > 0 else 1.0
    b = 1.0 - smooth((t - t1) / fout) if fout > 0 else (1.0 if t <= t1 else 0.0)
    return a * b

def hash01(*args):
    h = 0
    for a in args:
        h = (h * 1000003) ^ (int(a * 1000) & 0xFFFFFFFF)
    h = (h ^ (h >> 13)) * 0x5bd1e995 & 0xFFFFFFFF
    return ((h ^ (h >> 15)) & 0xFFFFFF) / float(0xFFFFFF)

def jitter(t, seed, rate=30.0):
    """Stepped random in [-1,1] that changes `rate` times per second."""
    k = math.floor(t * rate)
    return hash01(k, seed) * 2 - 1


# ----------------------------------------------------------------- textures
def fbm(n, beta, seed):
    rng = np.random.default_rng(seed)
    F = np.fft.fft2(rng.standard_normal((n, n)))
    ky = np.fft.fftfreq(n)[:, None]; kx = np.fft.fftfreq(n)[None, :]
    k = np.sqrt(kx * kx + ky * ky); k[0, 0] = 1
    F *= 1.0 / k ** beta; F[0, 0] = 0
    x = np.real(np.fft.ifft2(F))
    lo, hi = np.percentile(x, 1), np.percentile(x, 99)
    return np.clip((x - lo) / (hi - lo), 0, 1).astype(np.float32)

def make_lut(stops, n=1024):
    xs = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops], np.float32)
    v = np.linspace(0, 1, n)
    return np.stack([np.interp(v, xs, cs[:, i]) for i in range(3)], 1).astype(np.float32)

FIRE_LUT = make_lut([(0.0, (0, 0, 0)), (0.18, (0.22, 0.01, 0.0)), (0.38, (0.75, 0.06, 0.01)),
                     (0.55, (1.0, 0.28, 0.02)), (0.7, (1.0, 0.55, 0.08)), (0.85, (1.0, 0.82, 0.35)),
                     (1.0, (1.0, 1.0, 0.92))])
METAL_LUT = make_lut([(0.0, (0.16, 0.05, 0.04)), (0.3, (0.5, 0.04, 0.02)), (0.5, (0.95, 0.18, 0.03)),
                      (0.7, (1.0, 0.5, 0.08)), (0.88, (1.0, 0.85, 0.45)), (1.0, (1.0, 0.98, 0.9))])

def lut(L, v):
    idx = np.clip((v * (len(L) - 1)).astype(np.int32), 0, len(L) - 1)
    return L[idx]


class Textures:
    def __init__(self):
        self.smoke1 = fbm(512, 2.3, 11)
        self.smoke2 = fbm(512, 2.0, 22)
        self.fire = fbm(512, 1.55, 33)
        self.fine = fbm(512, 1.1, 44)
        rng = np.random.default_rng(55)
        self.grain = [rng.normal(0, 1, (960, 540)).astype(np.float32) for _ in range(6)]

    @staticmethod
    def sample(tex, X, Y):
        n = tex.shape[0]
        return tex[(Y.astype(np.int32)) % n, (X.astype(np.int32)) % n]


# ----------------------------------------------------------------- fonts / sprites
class FontBank:
    def __init__(self):
        self._fonts = {}
        self._layout = {}
        self._sprites = {}

    def font(self, key, size):
        k = (key, size)
        if k not in self._fonts:
            self._fonts[k] = ImageFont.truetype(os.path.join(FONT_DIR, FONTS[key]), size)
        return self._fonts[k]

    def layout(self, text, key):
        """Letter origins at REF size, word centred at (0,0), cap-height centred."""
        k = (text, key)
        if k in self._layout: return self._layout[k]
        f = self.font(key, int(REF))
        total = f.getlength(text)
        cap = -f.getbbox("Н", anchor="ls")[1]
        letters = []
        for i, ch in enumerate(text):
            x0 = f.getlength(text[:i]); adv = f.getlength(text[:i + 1]) - x0
            ox, oy = x0 - total / 2, cap / 2
            letters.append((ch, ox, oy, ox + adv / 2, 0.0))
        res = (letters, total, cap)
        self._layout[k] = res
        return res

    def sprite(self, key, ch, size):
        q = int(round(1.07 ** round(math.log(max(size, 6)) / math.log(1.07))))
        q = max(6, min(q, 1700))
        k = (key, ch, q)
        if k not in self._sprites:
            f = self.font(key, q)
            x0, y0, x1, y1 = f.getbbox(ch, anchor="ls")
            p = 4
            w, h = max(1, x1 - x0 + 2 * p), max(1, y1 - y0 + 2 * p)
            im = Image.new("L", (w, h), 0)
            ImageDraw.Draw(im).text((p - x0, p - y0), ch, font=f, anchor="ls", fill=255)
            arr = np.asarray(im, np.float32) / 255.0
            self._sprites[k] = (arr, (p - x0, p - y0), q)
        return self._sprites[k]

    def fit(self, text, key, max_w, max_size):
        _, total, _ = self.layout(text, key)
        return min(max_size, max_w / total * REF)

    def width(self, text, key, size):
        return self.layout(text, key)[1] * size / REF


def M_T(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)
def M_S(sx, sy=None): return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1]], np.float64)
def M_R(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)
def M_Sh(k): return np.array([[1, k, 0], [0, 1, 0], [0, 0, 1]], np.float64)


ITEM_DEFAULTS = dict(text="", font="black", size=100.0, x=540.0, y=960.0, rot=0.0, sx=1.0, sy=1.0,
                     shear=0.0, alpha=1.0, style="white", heat=1.0, color=(1, 1, 1), tint=None, tint_amt=0.0,
                     glow=0.0, glow_col=(1.0, 0.25, 0.05), depth=0, depth_vec=(3.0, 4.0),
                     depth_col=(0.32, 0.03, 0.01), bevel=0.0, outline=0.0, fill=1.0, blur=0.0,
                     dissolve=0.0, ghosts=(), letters=None, z=0, burn_col=(1.0, 0.45, 0.05), sweep=None)

def item(**kw):
    d = dict(ITEM_DEFAULTS); d.update(kw); return d

NUM_KEYS = ("size", "x", "y", "rot", "sx", "sy", "shear", "alpha")

def lerp_item(a, b, f):
    c = dict(b)
    for k in NUM_KEYS:
        c[k] = a[k] + (b[k] - a[k]) * f
    if a.get("letters") and b.get("letters") and len(a["letters"]) == len(b["letters"]):
        c["letters"] = [{kk: la.get(kk, 0) + (lb.get(kk, 0) - la.get(kk, 0)) * f for kk in lb}
                        for la, lb in zip(a["letters"], b["letters"])]
    return c


# ----------------------------------------------------------------- text renderer
class TextLayer:
    def __init__(self, W, H, fonts, tex):
        self.W, self.H, self.fonts, self.tex = W, H, fonts, tex
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), np.float32)
        self.glow = np.zeros((H, W, 3), np.float32)
        self.add = np.zeros((H, W, 3), np.float32)

    def clear(self):
        self.rgb.fill(0); self.a.fill(0); self.glow.fill(0); self.add.fill(0)

    def _letter_mats(self, it):
        letters, total, cap = self.fonts.layout(it["text"], it["font"])
        k = it["size"] / REF
        Mw = M_T(it["x"], it["y"]) @ M_R(it["rot"]) @ M_Sh(it["shear"]) @ M_S(it["sx"] * k, it["sy"] * k)
        smax = max(abs(it["sx"]), abs(it["sy"])) * it["size"]
        out = []
        for i, (ch, ox, oy, cx, cy) in enumerate(letters):
            if ch == " ": continue
            lf = it["letters"][i] if it["letters"] else {}
            la = lf.get("a", 1.0)
            if la <= 0.003: continue
            ls = lf.get("s", 1.0)
            if ls <= 0.01: continue
            Ml = (M_T(cx + lf.get("dx", 0) * REF, cy + lf.get("dy", 0) * REF) @ M_R(lf.get("rot", 0)) @ M_S(ls)
                  @ M_T(-cx, -cy))
            spr, (sox, soy), q = self.fonts.sprite(it["font"], ch, smax * ls)
            Ms = M_T(ox, oy) @ M_S(REF / q) @ M_T(-sox, -soy)
            A = (Mw @ Ml @ Ms)[:2]
            out.append((i, spr, A, la, lf.get("heat", it["heat"])))
        return out

    def draw(self, variants, t):
        """variants: list of item dicts (motion-blur samples, last = current)."""
        it = variants[-1]
        if it["alpha"] <= 0.003 or not it["text"].strip(): return
        per = [self._letter_mats(v) for v in variants]
        # union bbox
        xs, ys = [], []
        for mats in per:
            for (_, spr, A, _, _) in mats:
                h, w = spr.shape
                c = A @ np.array([[0, w, 0, w], [0, 0, h, h], [1, 1, 1, 1]], np.float64)
                xs += [c[0].min(), c[0].max()]; ys += [c[1].min(), c[1].max()]
        if not xs: return
        dv = it["depth_vec"]
        pad = int(4 + it["blur"] * 3 + it["depth"] * max(abs(dv[0]), abs(dv[1])) + it["outline"]
                  + max([abs(g[0]) + abs(g[1]) for g in it["ghosts"]] + [0]))
        x0 = max(0, int(math.floor(min(xs))) - pad); x1 = min(self.W, int(math.ceil(max(xs))) + pad)
        y0 = max(0, int(math.floor(min(ys))) - pad); y1 = min(self.H, int(math.ceil(max(ys))) + pad)
        if x1 - x0 < 2 or y1 - y0 < 2: return
        bw, bh = x1 - x0, y1 - y0
        mask = np.zeros((bh, bw), np.float32)
        heatm = np.zeros((bh, bw), np.float32)
        wv = 1.0 / len(variants)
        for mats in per:
            for (i, spr, A, la, lh) in mats:
                Ar = A.copy(); Ar[0, 2] -= x0; Ar[1, 2] -= y0
                m = cv2.warpAffine(spr, Ar, (bw, bh), flags=cv2.INTER_LINEAR, borderValue=0)
                m *= la * wv
                mask += m; heatm += m * lh
        np.clip(mask, 0, 1, out=mask)
        heat = heatm / np.maximum(mask, 1e-4)
        if it["blur"] > 0.3:
            mask = cv2.GaussianBlur(mask, (0, 0), it["blur"])
            heat = cv2.GaussianBlur(heat, (0, 0), it["blur"])
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)

        # dissolve (burn-away)
        burn_edge = None
        if it["dissolve"] > 0:
            nd = 0.65 * self.tex.sample(self.tex.fine, gx * 1.3, gy * 1.3) + 0.35 * self.tex.sample(self.tex.fire, gx * 0.5, gy * 0.5)
            p = it["dissolve"] * 1.15 - 0.05
            keep = np.clip((nd - p) / 0.04, 0, 1)
            burn_edge = np.clip(1 - np.abs(nd - p) / 0.06, 0, 1) * mask * (it["dissolve"] < 0.999)
            mask = mask * keep

        if it["outline"] > 0:
            k = max(1, int(it["outline"]))
            er = cv2.erode(mask, np.ones((2 * k + 1, 2 * k + 1), np.uint8))
            outl = np.clip(mask - er, 0, 1)
            mask = outl + (mask - outl) * it["fill"]

        col = self._color(it, gx, gy, heat, t, mask, (y0, y1))
        A = mask * it["alpha"]
        R = self.rgb[y0:y1, x0:x1]; Aa = self.a[y0:y1, x0:x1]

        # ghosts (additive doubles / RGB-split / echoes)
        for g in it["ghosts"]:
            gdx, gdy, ga, gc = g[0], g[1], g[2], g[3]
            Mg = np.float32([[1, 0, gdx], [0, 1, gdy]])
            sm = cv2.warpAffine(A, Mg, (bw, bh), flags=cv2.INTER_LINEAR, borderValue=0)
            self.add[y0:y1, x0:x1] += sm[..., None] * (np.array(gc, np.float32) * ga)

        # extrusion depth
        if it["depth"] > 0:
            n = int(it["depth"]); dc = np.array(it["depth_col"], np.float32)
            for s in range(n, 0, -1):
                Md = np.float32([[1, 0, dv[0] * s], [0, 1, dv[1] * s]])
                sm = cv2.warpAffine(A, Md, (bw, bh), flags=cv2.INTER_LINEAR, borderValue=0)
                c = dc * (0.35 + 0.65 * (1 - s / n))
                R *= (1 - sm)[..., None]; R += sm[..., None] * c
                Aa *= (1 - sm); Aa += sm

        R *= (1 - A)[..., None]; R += col * A[..., None]
        Aa *= (1 - A); Aa += A
        if it["glow"] > 0:
            self.glow[y0:y1, x0:x1] += A[..., None] * (np.array(it["glow_col"], np.float32) * it["glow"])
        if burn_edge is not None:
            bc = np.array(it["burn_col"], np.float32)
            self.add[y0:y1, x0:x1] += burn_edge[..., None] * bc * 2.2 * it["alpha"]
            self.glow[y0:y1, x0:x1] += burn_edge[..., None] * bc * 1.5 * it["alpha"]

    def draw_rect(self, it):
        """Filled rotated rectangle (graphic accents: bars, underlines, frames)."""
        if it["alpha"] <= 0.003 or it["w"] < 0.5 or it["h"] < 0.5: return
        c, s_ = math.cos(math.radians(it["rot"])), math.sin(math.radians(it["rot"]))
        hw, hh = it["w"] / 2, it["h"] / 2
        pts = np.array([[it["x"] + dx * c - dy * s_, it["y"] + dx * s_ + dy * c]
                        for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))])
        x0 = max(0, int(pts[:, 0].min()) - 3); x1 = min(self.W, int(pts[:, 0].max()) + 3)
        y0 = max(0, int(pts[:, 1].min()) - 3); y1 = min(self.H, int(pts[:, 1].max()) + 3)
        if x1 - x0 < 1 or y1 - y0 < 1: return
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(m, [np.round((pts - [x0, y0]) * 16).astype(np.int32)], 255, cv2.LINE_AA, 4)
        A = m.astype(np.float32) / 255 * it["alpha"]
        col = np.array(it["color"], np.float32)
        R = self.rgb[y0:y1, x0:x1]; Aa = self.a[y0:y1, x0:x1]
        R *= (1 - A)[..., None]; R += A[..., None] * col
        Aa *= (1 - A); Aa += A
        if it.get("glow", 0) > 0:
            self.glow[y0:y1, x0:x1] += A[..., None] * (np.array(it.get("glow_col", col), np.float32) * it["glow"])

    def _color(self, it, gx, gy, heat, t, mask, yr):
        st = it["style"]
        vv = (gy - yr[0]) / max(1, yr[1] - yr[0])
        if st == "white":
            base = np.array([1.0, 0.975, 0.95], np.float32)
            col = base * (1.0 - 0.10 * vv[..., None])
        elif st == "color":
            col = np.broadcast_to(np.array(it["color"], np.float32), gx.shape + (3,)).copy()
        elif st == "fire":
            n = self.tex.sample(self.tex.fire, gx * 0.45, gy * 0.45 + t * 380) * 0.8 + \
                self.tex.sample(self.tex.smoke2, gx * 0.9, gy * 0.9 + t * 600) * 0.2
            v = np.clip(0.60 + 0.30 * (n - 0.5) + 0.26 * (vv - 0.4) * heat, 0.45, 0.93)
            col = lut(FIRE_LUT, v)
        elif st == "hot":
            n = self.tex.sample(self.tex.fire, gx * 0.45, gy * 0.45 + t * 380)
            v = np.clip(heat * (0.80 + 0.35 * (n - 0.5)) + 0.12 * (vv - 0.4) * heat, 0, 1)
            col = lut(METAL_LUT, v)
        elif st == "gold":
            band = np.sin(vv * 7.0 + gx * 0.004) * 0.5 + 0.5
            c1 = np.array([0.55, 0.28, 0.05], np.float32); c2 = np.array([1.0, 0.86, 0.45], np.float32)
            col = c1 + (c2 - c1) * band[..., None]
            sw = it["sweep"]
            if sw is not None:
                sp = np.exp(-(((gx + gy * 0.45) - sw) / 70.0) ** 2)
                col = col + sp[..., None] * np.array([1.0, 0.95, 0.8], np.float32)
        elif st == "love":
            c1 = np.array([1.0, 0.42, 0.42], np.float32); c2 = np.array([0.85, 0.02, 0.10], np.float32)
            col = c1 + (c2 - c1) * vv[..., None]
        elif st == "red":
            n = self.tex.sample(self.tex.fire, gx * 0.6, gy * 0.6 + t * 200)
            col = np.array([1.0, 0.10, 0.05], np.float32) * (0.8 + 0.4 * n)[..., None]
        else:
            col = np.ones(gx.shape + (3,), np.float32)
        if it["tint"] is not None and it["tint_amt"] > 0:
            col = col + (np.array(it["tint"], np.float32) - col) * it["tint_amt"]
        if it["bevel"] > 0:
            sig = max(1.2, it["size"] * max(abs(it["sx"]), abs(it["sy"])) * 0.025)
            b = cv2.GaussianBlur(mask, (0, 0), sig)
            gxx = cv2.Sobel(b, cv2.CV_32F, 1, 0, ksize=3); gyy = cv2.Sobel(b, cv2.CV_32F, 0, 1, ksize=3)
            lam = np.clip((gxx * 0.55 + gyy * 0.85) * sig * 1.6, -1, 1)
            col = col * (1.0 + it["bevel"] * lam)[..., None]
        return col


# ----------------------------------------------------------------- particles
class Burst:
    """Analytic particle burst (positions are closed-form functions of age)."""
    def __init__(self, t0, x, y, n=60, speed=(300, 1400), ang=(-90, 360), g=900.0, drag=2.2,
                 life=(0.35, 1.1), size=(1, 3), streak=0.035, area=(0, 0), seed=1, kind="spark",
                 color=(1, 1, 1), heat=1.0, delay=0.0, front=False):
        rng = np.random.default_rng(seed)
        self.front = front
        self.t0, self.kind, self.color, self.heat = t0, kind, np.array(color, np.float32), heat
        self.g, self.k, self.streak = g, drag, streak
        a = np.radians(ang[0] + (rng.random(n) - 0.5) * ang[1])
        sp = speed[0] + (speed[1] - speed[0]) * rng.random(n) ** 1.6
        self.vx, self.vy = np.cos(a) * sp, np.sin(a) * sp
        self.x0 = x + (rng.random(n) - 0.5) * area[0]
        self.y0 = y + (rng.random(n) - 0.5) * area[1]
        self.life = life[0] + (life[1] - life[0]) * rng.random(n)
        self.size = size[0] + (size[1] - size[0]) * rng.random(n)
        self.delay = rng.random(n) * delay
        self.fl = rng.random(n) * 100
        self.tmax = t0 + delay + life[1] + 0.05

    def pos(self, a):
        k = self.k
        e = np.exp(-k * a)
        x = self.x0 + self.vx / k * (1 - e)
        y = self.y0 + self.vy / k * (1 - e) + self.g / k * (a - (1 - e) / k)
        return x, y


def draw_burst(b, t, hot, col, s):
    if t < b.t0 or t > b.tmax: return
    a = t - b.t0 - b.delay
    alive = (a >= 0) & (a < b.life)
    if not alive.any(): return
    idx = np.nonzero(alive)[0]
    aa = a[idx]; k = b.k
    def P(age):
        e = np.exp(-k * age)
        return (b.x0[idx] + b.vx[idx] / k * (1 - e),
                b.y0[idx] + b.vy[idx] / k * (1 - e) + b.g / k * (age - (1 - e) / k))
    x1, y1 = P(aa); x0, y0 = P(np.maximum(aa - b.streak, 0))
    f = (1 - aa / b.life[idx]) ** 1.3 * (0.7 + 0.3 * np.sin(b.fl[idx] + t * 55))
    sz = b.size[idx]
    sh = 4; m = s * (1 << sh)
    for j in range(len(idx)):
        v = float(f[j])
        if v < 0.02: continue
        p0 = (int(x0[j] * m), int(y0[j] * m)); p1 = (int(x1[j] * m), int(y1[j] * m))
        th = max(1, int(round(sz[j] * s * (0.5 + 0.5 * v))))
        if b.kind == "spark":
            cv2.line(hot, p0, p1, float(min(1.0, v * b.heat)), th, cv2.LINE_AA, sh)
        else:
            c = tuple(float(cc * v) for cc in b.color)
            cv2.line(col, p0, p1, c, th, cv2.LINE_AA, sh)


class Embers:
    """Ambient embers drifting upward (analytic)."""
    def __init__(self, n=220, seed=7, W=1080, H=1920):
        r = np.random.default_rng(seed)
        self.x = r.random(n) * W; self.ph = r.random(n) * (H + 300)
        self.sp = 60 + r.random(n) ** 2 * 260; self.wob = 10 + r.random(n) * 50
        self.wf = 0.5 + r.random(n) * 2.0; self.sz = 1 + r.random(n) ** 3 * 4
        self.br = 0.25 + r.random(n) * 0.75; self.fl = r.random(n) * 50; self.n = n
        self.W, self.H = W, H

    def draw(self, t, hot, s, amount, speed_mul=1.0, count=1.0):
        if amount <= 0.01: return
        n = int(self.n * clamp(count, 0, 1))
        tt = t * speed_mul
        y = self.H + 150 - ((self.ph[:n] + tt * self.sp[:n]) % (self.H + 300))
        x = self.x[:n] + np.sin(tt * self.wf[:n] + self.fl[:n]) * self.wob[:n]
        y0 = y + self.sp[:n] * 0.03 * speed_mul
        f = self.br[:n] * (0.6 + 0.4 * np.sin(self.fl[:n] * 3 + t * 9)) * amount
        sh = 4; m = s * (1 << sh)
        for j in range(n):
            th = max(1, int(round(self.sz[j] * s)))
            cv2.line(hot, (int(x[j] * m), int(y0[j] * m)), (int(x[j] * m), int(y[j] * m)),
                     float(min(1, f[j])), th, cv2.LINE_AA, sh)


# ----------------------------------------------------------------- frame post
def glitch(img, amt, t, seed=0):
    """Digital glitch: slice displacement, RGB split, block shuffles. img float32 HxWx3."""
    if amt <= 0.01: return img
    H, W = img.shape[:2]
    k = math.floor(t * 30)
    rng = np.random.default_rng(int(k * 7919 + seed * 104729) & 0x7FFFFFFF)
    out = img
    # RGB split
    sh = int(6 + 40 * amt * rng.random())
    out = out.copy()
    out[..., 0] = np.roll(img[..., 0], sh, axis=1)
    out[..., 2] = np.roll(img[..., 2], -sh, axis=1)
    # slices
    ns = int(3 + 14 * amt)
    for _ in range(ns):
        if rng.random() > 0.35 + 0.6 * amt: continue
        y = int(rng.random() * H); h = int(6 + rng.random() * 120 * amt)
        dx = int((rng.random() - 0.5) * 260 * amt)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
        if rng.random() < 0.25 * amt:
            ch = int(rng.random() * 3); out[y:y + h, :, ch] *= 0.2
    # blocks
    nb = int(8 * amt)
    for _ in range(nb):
        bw, bh = int(40 + rng.random() * 260), int(10 + rng.random() * 80)
        sx, sy = int(rng.random() * (W - bw)), int(rng.random() * (H - bh))
        dx, dy = int(rng.random() * (W - bw)), int(np.clip(sy + (rng.random() - 0.5) * 200, 0, H - bh))
        out[dy:dy + bh, dx:dx + bw] = out[sy:sy + bh, sx:sx + bw] * (0.6 + 0.8 * rng.random())
    # scanlines
    if amt > 0.3:
        out[::3] *= 1 - 0.25 * amt
    return out


def chroma(img, amt):
    if amt < 0.0005: return img
    H, W = img.shape[:2]
    out = img.copy()
    for c, s in ((0, 1 + amt), (2, 1 - amt)):
        M = np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]])
        out[..., c] = cv2.warpAffine(img[..., c], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out


def radial_distort(img, cx, cy, R, width, strength):
    """Shockwave refraction ring."""
    H, W = img.shape[:2]
    s = 0.25
    gy, gx = np.mgrid[0:int(H * s), 0:int(W * s)].astype(np.float32) / s
    dx, dy = gx - cx, gy - cy
    r = np.sqrt(dx * dx + dy * dy) + 1e-3
    d = strength * np.exp(-((r - R) / width) ** 2) * np.sign(r - R) * -1
    mx = (dx / r * d).astype(np.float32); my = (dy / r * d).astype(np.float32)
    mx = cv2.resize(mx, (W, H)); my = cv2.resize(my, (W, H))
    GY, GX = np.mgrid[0:H, 0:W].astype(np.float32)
    return cv2.remap(img, GX + mx, GY + my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def draw_bubbles(pcol, s, t, sysdef):
    """Rising foam bubbles (analytic). sysdef: t0,t1,x0,x1,y0 (spawn line),rise,n,seed,amount."""
    r = np.random.default_rng(sysdef["seed"])
    n = sysdef["n"]
    birth = sysdef["t0"] + r.random(n) * (sysdef["t1"] - sysdef["t0"])
    life = 0.6 + r.random(n) * 1.0
    xs = sysdef["x0"] + r.random(n) * (sysdef["x1"] - sysdef["x0"])
    ys = sysdef["y0"] + (r.random(n) - 0.5) * sysdef.get("ysp", 60)
    sp = sysdef["rise"] * (0.5 + r.random(n))
    rad = 3 + r.random(n) ** 2 * sysdef.get("rmax", 22)
    ph = r.random(n) * 6.3
    a = t - birth
    sh = 4; m = s * (1 << sh)
    for i in np.nonzero((a > 0) & (a < life))[0]:
        f = a[i] / life[i]
        v = sysdef["amount"] * min(1, f * 6) * (1 - f) ** 0.7
        if f > 0.93: continue  # pop
        x = xs[i] + math.sin(ph[i] + a[i] * 7) * 10
        y = ys[i] - sp[i] * a[i] - 40 * a[i] ** 2
        rr = rad[i] * (0.6 + 0.6 * f)
        col = (v * 1.0, v * 0.86, v * 0.6)
        cv2.circle(pcol, (int(x * m), int(y * m)), int(rr * m), col, max(1, int(1.6 * s * 2)), cv2.LINE_AA, sh)
        cv2.circle(pcol, (int((x - rr * 0.35) * m), int((y - rr * 0.35) * m)), int(max(1, rr * 0.18) * m),
                   (v, v, v), -1, cv2.LINE_AA, sh)
