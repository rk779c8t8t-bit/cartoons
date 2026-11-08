"""Tiny 2D motion-graphics engine: rough kinetic type, camera, shapes, grain."""
import math
import zlib
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT = str(Path(__file__).parent / "fonts" / "anton.ttf")

# palette (RGB 0..1)
def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

CREAM = rgb("#F7D49B")
MAROON = rgb("#2C0303")
BROWN = rgb("#4A2412")
BLACK = rgb("#0E0B09")
TAN = rgb("#D9B27A")
GHOST_DARK = rgb("#4A1610")
FLASH = rgb("#FFF1D6")

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def ph(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else float(t >= t0)

def out_cubic(x): return 1 - (1 - x) ** 3
def out_expo(x): return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def in_quad(x): return x * x
def in_cubic(x): return x * x * x
def in_out(x): return 3 * x * x - 2 * x * x * x

def out_back(x, s=1.9):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2

def spring(t, t0, freq=9.0, decay=7.0):
    """damped oscillation starting at 1 -> 0 (0 before t0)."""
    if t < t0:
        return 0.0
    d = t - t0
    return math.exp(-decay * d) * math.cos(2 * math.pi * freq * d)

def lerp(a, b, x): return a + (b - a) * x

# ---------------------------------------------------------------- glyphs
@lru_cache(maxsize=64)
def _font(size):
    return ImageFont.truetype(FONT, size)

def _q(size):
    return max(8, int(round(size / 4.0)) * 4)

def _roughen(a, size, seed):
    """Wobbly hand-cut edges like the reference lettering."""
    h, w = a.shape
    rng = np.random.default_rng(seed)
    amp = max(0.7, size * 0.0065)
    cell = max(8, int(size * 0.13))
    gh, gw = h // cell + 2, w // cell + 2
    nx = cv2.resize(rng.standard_normal((gh, gw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    ny = cv2.resize(rng.standard_normal((gh, gw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    out = cv2.remap(a, xx + nx * amp, yy + ny * amp, cv2.INTER_LINEAR, borderValue=0)
    # slightly soften then re-sharpen for crisp but organic edge
    out = cv2.GaussianBlur(out, (0, 0), max(0.6, size * 0.003))
    return np.clip((out - 0.5) * 2.2 + 0.5, 0, 1).astype(np.float32)

@lru_cache(maxsize=1500)
def glyph(s, size, outline=0):
    """Returns (alpha mask, cx, cy) where (cx,cy) is the cap-box centre in mask coords."""
    f = _font(size)
    l, _, r, _ = f.getbbox(s)
    cap_t, cap_b = f.getbbox("H")[1], f.getbbox("H")[3]
    _, top, _, bot = f.getbbox(s + "H")
    pad = int(size * 0.12) + 6 + outline * 2
    w = (r - l) + 2 * pad
    h = (bot - top) + 2 * pad
    im = Image.new("L", (max(w, 1), max(h, 1)), 0)
    ImageDraw.Draw(im).text((pad - l, pad - top), s, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255.0
    a = _roughen(a, size, zlib.crc32(f"{s}|{size}".encode()))
    if outline:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * outline + 1, 2 * outline + 1))
        a = np.clip(cv2.dilate(a, k) - cv2.erode(a, k), 0, 1)
    cx = pad + (r - l) / 2.0
    cy = pad + (cap_t + cap_b) / 2.0 - top
    return a, cx, cy

def cap_w(s, size):
    f = _font(_q(size))
    l, _, r, _ = f.getbbox(s)
    return (r - l) * size / _q(size)

def cap_h(size):
    return size * 0.86

def fit(s, width, max_cap=None):
    """font size so that s is `width` px wide (cap box), optionally capped in height."""
    w100 = cap_w(s, 400) / 400.0
    size = width / max(w100, 1e-6)
    if max_cap is not None:
        size = min(size, max_cap / 0.86)
    return size

def advance(s, size):
    return _font(_q(size)).getlength(s) * size / _q(size)

# ---------------------------------------------------------------- frame + camera
class Frame:
    def __init__(self):
        self.img = np.zeros((H, W, 3), np.float32)
        self.cam = dict(dx=0.0, dy=0.0, z=1.0, r=0.0)

    # camera as 2x3 affine about frame centre
    def cam_m(self):
        c = self.cam
        z, a = c["z"], math.radians(c["r"])
        L = np.array([[z * math.cos(a), -z * math.sin(a)], [z * math.sin(a), z * math.cos(a)]], np.float32)
        C = np.array([W / 2, H / 2], np.float32)
        t = C + np.array([c["dx"], c["dy"]], np.float32) - L @ C
        return L, t

    def shake(self, t, hits, freq=1.0):
        for th, amp in hits:
            if t >= th:
                a = amp * math.exp(-(t - th) * 11.0)
                self.cam["dx"] += a * math.sin(t * 97 * freq + th * 13)
                self.cam["dy"] += a * math.cos(t * 83 * freq + th * 7)
                self.cam["r"] += a * 0.02 * math.sin(t * 61 + th)

    def bg(self, col):
        self.img[:] = col

    def _blend(self, x0, y0, wmask, col):
        reg = self.img[y0:y0 + wmask.shape[0], x0:x0 + wmask.shape[1]]
        reg += (np.asarray(col, np.float32) - reg) * wmask[..., None]

    def _clip_mask(self, clip, x0, y0, bw, bh):
        L, tc = self.cam_m()
        cx0, cy0, cx1, cy1 = clip
        pts = np.array([[cx0, cy0], [cx1, cy0], [cx1, cy1], [cx0, cy1]], np.float32) @ L.T + tc
        m = np.zeros((bh, bw), np.uint8)
        p = np.round((pts - [x0, y0]) * 16).astype(np.int32)
        cv2.fillPoly(m, [p], 255, cv2.LINE_AA, shift=4)
        return m.astype(np.float32) / 255.0

    def text(self, s, size, x, y, col, sc=1.0, rot=0.0, sx=1.0, sy=1.0, alpha=1.0,
             clip=None, outline=0):
        if alpha <= 0.003 or sc <= 0.001:
            return
        q = _q(size)
        a, gcx, gcy = glyph(s, q, outline)
        k = size / q
        L, tc = self.cam_m()
        th = math.radians(rot)
        R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]], np.float32)
        S = np.diag([sc * sx * k, sc * sy * k]).astype(np.float32)
        A = L @ R @ S
        b = L @ np.array([x, y], np.float32) + tc - A @ np.array([gcx, gcy], np.float32)
        h, w = a.shape
        corners = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32) @ A.T + b
        x0 = int(max(0, math.floor(corners[:, 0].min())))
        y0 = int(max(0, math.floor(corners[:, 1].min())))
        x1 = int(min(W, math.ceil(corners[:, 0].max())))
        y1 = int(min(H, math.ceil(corners[:, 1].max())))
        if x1 <= x0 or y1 <= y0:
            return
        M = np.hstack([A, (b - [x0, y0])[:, None]]).astype(np.float32)
        wm = cv2.warpAffine(a, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
        if clip is not None:
            wm *= self._clip_mask(clip, x0, y0, x1 - x0, y1 - y0)
        if alpha < 1:
            wm *= alpha
        self._blend(x0, y0, wm, col)

    def letters(self, s, size, x, y, col, fn, **kw):
        """Draw word letter-by-letter; fn(i, n) -> dict(dx,dy,rot,sc,alpha) per letter."""
        total = advance(s, size)
        start = x - total / 2
        n = len(s)
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            lx = start + advance(s[:i], size) + advance(ch, size) / 2
            p = fn(i, n)
            if p is None:
                continue
            self.text(ch, size, lx + p.get("dx", 0), y + p.get("dy", 0), col,
                      sc=p.get("sc", 1), rot=p.get("rot", 0), alpha=p.get("alpha", 1), **kw)

    def poly(self, pts, col, alpha=1.0, thick=0, closed=True):
        L, tc = self.cam_m()
        P = np.asarray(pts, np.float32) @ L.T + tc
        m = np.zeros((H, W), np.uint8)
        p = np.round(P * 16).astype(np.int32)
        if thick:
            cv2.polylines(m, [p], closed, 255, max(1, int(thick * self.cam["z"])), cv2.LINE_AA, shift=4)
        else:
            cv2.fillPoly(m, [p], 255, cv2.LINE_AA, shift=4)
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            return
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        self._blend(x0, y0, m[y0:y1, x0:x1].astype(np.float32) / 255 * alpha, col)

    def rect(self, x0, y0, x1, y1, col, alpha=1.0, thick=0):
        self.poly([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], col, alpha, thick)

    def star(self, x, y, r, col, rot=0.0, alpha=1.0, thick=0):
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = math.radians(rot) - math.pi / 2 + i * math.pi / 5
            pts.append([x + rr * math.cos(a), y + rr * math.sin(a)])
        self.poly(pts, col, alpha, thick)

    def flash(self, col, a):
        if a > 0.003:
            self.img += (np.asarray(col, np.float32) - self.img) * a


# ---------------------------------------------------------------- layout helpers
def layout_lines(lines, width=960, line_gap=34, max_cap=420, cy=960, align="left", x_left=None):
    """lines: list of list of words. Each line is scaled to fill `width`.
    Returns dict word_index -> (size, cx, cy) in reading order."""
    gap_k = 0.28
    rows = []
    for words in lines:
        s = " ".join(words)
        size = fit(s, width, max_cap)
        rows.append((words, size))
    total_h = sum(cap_h(sz) for _, sz in rows) + line_gap * (len(rows) - 1)
    y = cy - total_h / 2
    out = []
    xl = (W - width) / 2 if x_left is None else x_left
    for words, size in rows:
        hgt = cap_h(size)
        line_w = sum(cap_w(w, size) for w in words) + gap_k * size * (len(words) - 1)
        x = xl if align == "left" else (W - line_w) / 2
        for wd in words:
            ww = cap_w(wd, size)
            out.append((wd, size, x + ww / 2, y + hgt / 2))
            x += ww + gap_k * size
        y += hgt + line_gap
    return out
