"""Step 2: render the edit "TWO WORLDS" (Eminem x Toly Summer).

Every frame is composed procedurally from the two portraits:
  * cut-out person layers + background plates  -> 2.5D parallax
  * per-shot camera (zoom / pan / roll / yaw "orbit") with speed ramps
  * head turn / nod / tilt warp synced to the beat
  * motion blur (sub-frame sampling), flashes, shake, glitch, shockwave,
    chromatic aberration, bloom, light leaks, particles, god rays, fog, grain
  * per-world colour grade (warm "realm" for Toly, cold "steel" for Eminem)

Usage:
  python3 render.py                      # full quality -> ../final_edit.mp4
  python3 render.py --preview            # half-res, fewer motion-blur samples
  python3 render.py --still 5.5 6.0      # write PNG stills for given times
All cut times live in timeline.py-style constants below (BEATS / SHOTS).
"""
import argparse
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "assets", "build")
FINAL_DIR = os.path.dirname(HERE)

W, H = 1080, 1920
FPS = 30
DURATION = 13.0
MB_SAMPLES = 4          # motion-blur sub-frames
SHUTTER = 0.5           # fraction of a frame the shutter is open (180 deg)

# ----------------------------------------------------------------------------
# Music map (from librosa analysis of the original audio, see README)
# ----------------------------------------------------------------------------
INTRO_HITS = [0.03, 0.84, 1.35, 1.76, 2.11, 3.03, 3.40]
KICKS = [3.70 + i * 0.525 for i in range(14)]     # 3.70 ... 10.525 (114 BPM)
DROP = 10.86                                     # biggest hit, after silence
DROP2 = 11.36                                    # second swell of the drop

cv2.setNumThreads(1)


# ----------------------------------------------------------------------------
# small math helpers
# ----------------------------------------------------------------------------
def clamp01(x):
    return min(1.0, max(0.0, x))


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def ease_out(u, p=3):
    u = clamp01(u)
    return 1 - (1 - u) ** p


def ease_in(u, p=3):
    return clamp01(u) ** p


def ramp(u):
    """Speed ramp: fast - slow - fast."""
    v = 2 * clamp01(u) - 1
    return 0.5 + 0.5 * (0.35 * v + 0.65 * v ** 3)


def ramp_out(u):
    """Speed ramp: very fast start that settles into slow motion."""
    u = clamp01(u)
    return 1 - (1 - u) ** 5 * 0.85 - 0.15 * (1 - u)


def pulse(t, times, decay=0.12, amp=1.0):
    v = 0.0
    for ti in times:
        if 0 <= t - ti < decay * 8:
            v += math.exp(-(t - ti) / decay)
    return v * amp


def rng(seed):
    return np.random.default_rng(seed)


def hash_noise(t, seed=0, freq=8.0):
    """Smooth 1D noise in [-1,1] (sum of sines with seeded phases)."""
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 2 * math.pi, 4)
    fr = freq * np.array([1.0, 1.7, 2.9, 4.3])
    return float(np.sum(np.sin(fr * t + ph) * np.array([0.5, 0.25, 0.15, 0.1])))


# ----------------------------------------------------------------------------
# assets
# ----------------------------------------------------------------------------
class Char:
    pass


def periodic_noise(h, w, seed, power=2.2, lo=2):
    r = rng(seed)
    f = np.fft.fft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    k = np.sqrt(fx ** 2 + fy ** 2)
    k[0, 0] = 1
    filt = 1 / (k ** (power / 2))
    filt[k < lo] *= 0.3
    n = np.real(np.fft.ifft2(f * filt))
    n = (n - n.min()) / (n.max() - n.min())
    return n.astype(np.float32)


def load_assets(scale):
    A = {}
    for name, orig_w, lm in (
        ("toly", 1000, dict(eyes=(461, 278), facew=330, headc=(478, 255), headr=(185, 255),
                            pivot=(472, 470), mouth=(470, 405), leye=(405, 285), reye=(517, 270),
                            fairy=(838, 765), vest=(560, 720), collar=(560, 520))),
        ("eminem", 500, dict(eyes=(238, 219), facew=300, headc=(240, 225), headr=(175, 245),
                             pivot=(240, 450), mouth=(240, 360), leye=(175, 220), reye=(300, 218),
                             earring=(370, 330), necklace=(240, 520))),
    ):
        c = Char()
        c.name = name
        rgb = cv2.imread(os.path.join(BUILD, name + "_hr.png"))[:, :, ::-1].astype(np.float32) / 255
        a = cv2.imread(os.path.join(BUILD, name + "_alpha.png"), 0).astype(np.float32) / 255
        plate = cv2.imread(os.path.join(BUILD, name + "_plate.png"))[:, :, ::-1].astype(np.float32) / 255
        k = rgb.shape[1] / orig_w
        a = clean_alpha(a, name)
        if name == "eminem":
            # pull the matte in a little (kills the grey halo) and add a cold rim light
            a = cv2.erode(a, np.ones((5, 5), np.uint8))
            a = cv2.GaussianBlur(a, (0, 0), 1.5)
            rim = np.clip(a - cv2.GaussianBlur(a, (0, 0), 14), 0, 1)
            rgb = rgb * (1 - 0.25 * rim[..., None]) + rim[..., None] * np.array([0.55, 0.75, 1.0], np.float32) * 0.9
        c.k = k
        c.lm = {kk: (np.array(v, np.float32) * k if isinstance(v, tuple) else v * k) for kk, v in lm.items()}
        c.premult = [np.dstack([rgb * a[..., None], a])]
        c.full = [rgb]
        for _ in range(2):
            c.premult.append(cv2.pyrDown(c.premult[-1]))
            c.full.append(cv2.pyrDown(c.full[-1]))
        c.plate = plate
        c.plate_blur = [cv2.GaussianBlur(plate, (0, 0), 6 * k / 2.4), cv2.GaussianBlur(plate, (0, 0), 16 * k / 2.4)]
        A[name] = c

    # procedural textures (made at final res; preview just samples them)
    A["concrete"] = periodic_noise(1200, 1200, 7, 1.6, 1) * 0.6 + periodic_noise(1200, 1200, 8, 2.6) * 0.4
    A["fog"] = periodic_noise(512, 512, 11, 2.8)
    A["fog2"] = periodic_noise(512, 512, 12, 2.4)
    A["raynoise"] = np.convolve(rng(5).random(4096), np.ones(9) / 9, mode="same").astype(np.float32)
    A["grain"] = [rng(100 + i).standard_normal((H // 2, W // 2)).astype(np.float32) for i in range(6)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    A["X"], A["Y"] = xx, yy
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    A["vignette"] = np.clip(1.15 - d ** 2 * 0.65, 0.25, 1).astype(np.float32)[..., None]
    return A


def clean_alpha(a, name):
    m = (a > 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        keep = (lab == big).astype(np.uint8)
        # fill holes
        inv = 1 - keep
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
        for i in range(1, n2):
            x, y, w, h, area = st2[i]
            if x > 0 and y > 0 and x + w < a.shape[1] and y + h < a.shape[0]:
                keep[lab2 == i] = 1
        keepf = cv2.GaussianBlur(cv2.dilate(keep, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 3)
        a = np.minimum(a, keepf)
    a = cv2.erode(a, np.ones((3, 3), np.uint8))
    h = a.shape[0]
    fade_from = 0.80 if name == "eminem" else 0.965
    ramp_ = np.clip((np.arange(h) / h - fade_from) / (1 - fade_from), 0, 1)
    a = a * (1 - smooth_arr(ramp_))[:, None]
    return a.astype(np.float32)


def smooth_arr(u):
    return u * u * (3 - 2 * u)


A = None  # filled per process


# ----------------------------------------------------------------------------
# camera + layers
# ----------------------------------------------------------------------------
def cam(focus, zoom, at, rot=0.0, yaw=0.0, pitch=0.0):
    """Homography: source point `focus` lands on output `at`, scaled by zoom."""
    r = math.radians(rot)
    c, s = math.cos(r) * zoom, math.sin(r) * zoom
    fx, fy = focus
    M = np.array([[c, -s, at[0] - (c * fx - s * fy)],
                  [s, c, at[1] - (s * fx + c * fy)],
                  [0, 0, 1]], np.float64)
    if yaw or pitch:
        f = 1500.0
        P = np.array([[1, 0, 0], [0, 1, 0],
                      [math.tan(math.radians(yaw)) / f, math.tan(math.radians(pitch)) / f, 1]])
        T = np.array([[1, 0, -at[0]], [0, 1, -at[1]], [0, 0, 1]])
        Ti = np.array([[1, 0, at[0]], [0, 1, at[1]], [0, 0, 1]])
        M = Ti @ P @ T @ M
    return M


def char_cam(ch, focus, facew_px, at, rot=0.0, yaw=0.0, pitch=0.0):
    f = ch.lm[focus] if isinstance(focus, str) else np.array(focus, np.float32) * ch.k
    return cam(f, facew_px / ch.lm["facew"], at, rot, yaw, pitch)


def _zoom_of(M):
    return math.sqrt(abs(np.linalg.det(M[:2, :2])))


def warp(levels, M, border=cv2.BORDER_CONSTANT):
    z = _zoom_of(M)
    lvl = 0
    while lvl + 1 < len(levels) and z * (2 ** (lvl + 1)) < 0.75:
        lvl += 1
    S = np.diag([2.0 ** lvl, 2.0 ** lvl, 1.0])
    return cv2.warpPerspective(levels[lvl], M @ S, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)


def project(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return v[:2] / v[2]


def head_warp(layer, ch, M, rot_deg, dy=0.0, dx=0.0):
    """Turn / nod the head of a warped person layer around the neck pivot."""
    if abs(rot_deg) < 1e-3 and abs(dy) < 1e-3 and abs(dx) < 1e-3:
        return layer
    z = _zoom_of(M)
    pv = project(M, ch.lm["pivot"])
    hc = project(M, ch.lm["headc"])
    rx, ry = ch.lm["headr"] * z
    x0 = int(max(0, hc[0] - rx * 1.6)); x1 = int(min(W, hc[0] + rx * 1.6))
    y0 = int(max(0, hc[1] - ry * 1.6)); y1 = int(min(H, pv[1] + ry * 0.4))
    if x1 <= x0 or y1 <= y0:
        return layer
    X = A["X"][y0:y1, x0:x1]
    Y = A["Y"][y0:y1, x0:x1]
    d = np.sqrt(((X - hc[0]) / rx) ** 2 + ((Y - hc[1]) / ry) ** 2)
    w = np.clip((1.5 - d) / 0.55, 0, 1)
    w = w * w * (3 - 2 * w)
    a = -math.radians(rot_deg) * w
    ca, sa = np.cos(a), np.sin(a)
    sx = pv[0] + ca * (X - pv[0]) - sa * (Y - pv[1]) - dx * z * w
    sy = pv[1] + sa * (X - pv[0]) + ca * (Y - pv[1]) - dy * z * w
    out = layer.copy()
    out[y0:y1, x0:x1] = cv2.remap(layer, sx.astype(np.float32), sy.astype(np.float32),
                                  cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return out


def person(ch, M, head=(0, 0, 0)):
    lay = warp(ch.premult, M)
    lay = head_warp(lay, ch, M, *head)
    return lay


def over(canvas, lay, opacity=1.0):
    a = lay[:, :, 3:4] * opacity
    return canvas * (1 - a) + lay[:, :, :3] * opacity


def screen(a, b, k=1.0):
    return 1 - (1 - a) * (1 - b * k)


# ----------------------------------------------------------------------------
# environments
# ----------------------------------------------------------------------------
def realm_bg(t, focus=(480, 330), zoom=1.0, at=(W / 2, H / 2), rot=0.0, blur=0, sun=1.0, fog=0.5):
    """Toly's mountain realm: plate + fog + god rays."""
    ch = A["toly"]
    M = cam(np.array(focus) * ch.k, zoom * 1920 / ch.plate.shape[0] * 1.0, at, rot)
    src = ch.plate if blur == 0 else ch.plate_blur[blur - 1]
    img = cv2.warpPerspective(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if fog > 0:
        img = add_fog(img, t, fog, tint=(0.95, 0.97, 1.0))
    if sun > 0:
        img = god_rays(img, t, (W * 0.15, -H * 0.05), (1.0, 0.86, 0.6), 0.35 * sun)
    return img


def steel_bg(t, shift=(0, 0), zoom=1.0, light=(W / 2, H * 0.32), beams=1.0, haze=0.4):
    """Eminem's cold steel world: concrete wall, backlight, beams, haze."""
    tex = A["concrete"]
    M = cam((600, 600), 2.2 * zoom, (W / 2 + shift[0], H / 2 + shift[1]))
    n = cv2.warpPerspective(tex, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    X, Y = A["X"], A["Y"]
    d = np.sqrt(((X - light[0]) / 700) ** 2 + ((Y - light[1]) / 800) ** 2)
    glow = np.exp(-d ** 2 * 1.6)
    base = 0.04 + 0.30 * glow + (n - 0.5) * (0.08 + 0.10 * glow)
    img = np.dstack([base * 0.78, base * 0.9, base * 1.12])
    # floor darkness
    img *= np.clip(1.25 - (Y / H) ** 1.5 * 0.9, 0.2, 1)[..., None]
    if beams > 0:
        img = god_rays(img, t, (W * 0.5 + 150 * math.sin(t * 0.7), -H * 0.15), (0.6, 0.75, 1.0), 0.45 * beams, sharp=True)
    if haze > 0:
        img = add_fog(img, t * 1.4, haze, tint=(0.55, 0.65, 0.85))
    return img.astype(np.float32)


def add_fog(img, t, amount, tint=(1, 1, 1)):
    f1 = A["fog"]
    f2 = A["fog2"]
    sh = int(t * 40) % 512
    sh2 = int(t * 25) % 512
    a = np.roll(f1, sh, axis=1)
    b = np.roll(f2, -sh2, axis=1)
    f = cv2.resize((a * 0.6 + b * 0.4), (W, H), interpolation=cv2.INTER_LINEAR)
    f = np.clip((f - 0.35) * 1.8, 0, 1) * amount
    f *= np.clip(A["Y"] / H * 1.2 - 0.1, 0.15, 1)  # heavier near bottom
    return img * (1 - f[..., None] * 0.6) + f[..., None] * np.array(tint, np.float32) * 0.6


def god_rays(img, t, src, color, amount, sharp=False):
    h, w = H // 4, W // 4
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) * 4
    ang = np.arctan2(yy - src[1], xx - src[0])
    dist = np.sqrt((yy - src[1]) ** 2 + (xx - src[0]) ** 2)
    rn = A["raynoise"]
    idx = ((ang + math.pi) / (2 * math.pi) * 4096 * (3 if sharp else 1.5) + t * 30).astype(np.int64) % 4096
    r = rn[idx]
    r = np.clip((r - 0.45) * (6 if sharp else 3), 0, 1)
    r *= np.exp(-dist / (H * 0.9))
    r = cv2.GaussianBlur(r, (0, 0), 1.5)
    r = cv2.resize(r, (W, H), interpolation=cv2.INTER_LINEAR)
    return screen(img, r[..., None] * np.array(color, np.float32), amount)


def particles(img, t, seed, n, color, size=(2, 9), speed=(-20, -80), drift=30, glow=1.0, region=(0, 0, W, H),
              burst=None):
    r = rng(seed)
    x0 = r.uniform(region[0], region[2], n)
    y0 = r.uniform(region[1], region[3], n)
    sz = r.uniform(size[0], size[1], n) ** 1.0
    vy = r.uniform(min(speed), max(speed), n)
    ph = r.uniform(0, 6.28, n)
    tw = r.uniform(2, 6, n)
    out = img
    for i in range(n):
        if burst is not None:
            bt, bc, bv = burst
            dt = max(0.0, t - bt)
            ang = ph[i] * 1.0
            sp = bv * (0.3 + sz[i] / size[1])
            dist = sp * (1 - math.exp(-dt * 2.2)) / 2.2
            x = bc[0] + math.cos(ang) * (dist + r.uniform(0, 1) * 0)
            y = bc[1] + math.sin(ang) * dist + 40 * dt * dt
        else:
            x = (x0[i] + drift * math.sin(t * 0.8 + ph[i])) % W
            y = (y0[i] + vy[i] * t) % H
        inten = glow * (0.55 + 0.45 * math.sin(t * tw[i] + ph[i]))
        s = sz[i]
        rad = int(s * 3) + 1
        xi, yi = int(x), int(y)
        xa, xb = max(0, xi - rad), min(W, xi + rad + 1)
        ya, yb = max(0, yi - rad), min(H, yi + rad + 1)
        if xa >= xb or ya >= yb:
            continue
        gy, gx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
        g = np.exp(-((gx - x) ** 2 + (gy - y) ** 2) / (s * s)) * inten
        out[ya:yb, xa:xb] = screen(out[ya:yb, xa:xb], g[..., None] * np.array(color, np.float32))
    return out


# ----------------------------------------------------------------------------
# grading
# ----------------------------------------------------------------------------
def grade(img, look, exposure=1.0):
    x = np.clip(img * exposure, 0, 4)
    lum = (x * np.array([0.299, 0.587, 0.114], np.float32)).sum(2, keepdims=True)
    if look == "realm":      # warm gold highlights, teal shadows
        sat, con = 1.12, 1.12
        sh, hi = np.array([-0.01, 0.025, 0.04]), np.array([0.05, 0.015, -0.04])
    elif look == "steel":    # cold, desaturated, hard contrast
        x = x * 0.8
        sat, con = 0.6, 1.18
        sh, hi = np.array([-0.01, 0.01, 0.05]), np.array([-0.01, 0.01, 0.03])
    elif look == "duo":      # teal / orange blockbuster
        sat, con = 1.0, 1.2
        sh, hi = np.array([-0.02, 0.02, 0.05]), np.array([0.05, 0.02, -0.03])
    else:
        return x
    x = lum + (x - lum) * sat
    x = (x - 0.45) * con + 0.45
    w = np.clip(lum, 0, 1)
    x = x + (1 - w) * sh.astype(np.float32) * 1.0 + w * hi.astype(np.float32)
    return np.clip(x, 0, 4).astype(np.float32)


# ----------------------------------------------------------------------------
# post effects
# ----------------------------------------------------------------------------
def zoom_blur(img, amount, center=(W / 2, H / 2), n=7):
    if amount < 0.004:
        return img
    acc = np.zeros_like(img)
    for i in range(n):
        s = 1 + amount * i / (n - 1)
        M = np.array([[s, 0, center[0] * (1 - s)], [0, s, center[1] * (1 - s)]], np.float32)
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / n


def chroma(img, amt):
    if amt < 0.0005:
        return img
    out = img.copy()
    for ch, s in ((0, 1 + amt), (2, 1 - amt)):
        M = np.array([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]], np.float32)
        out[:, :, ch] = cv2.warpAffine(img[:, :, ch], M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return out


def glitch(img, amt, seed):
    if amt <= 0.01:
        return img
    r = rng(seed)
    out = img.copy()
    # RGB split
    dx = int(30 * amt) + 1
    out[:, :, 0] = np.roll(img[:, :, 0], dx, axis=1)
    out[:, :, 2] = np.roll(img[:, :, 2], -dx, axis=1)
    # slice displacement
    for _ in range(int(4 + 10 * amt)):
        y = int(r.uniform(0, H))
        h = int(r.uniform(8, 140) * (0.5 + amt))
        sh = int(r.normal(0, 120 * amt))
        out[y:y + h] = np.roll(out[y:y + h], sh, axis=1)
    # a couple of colour blocks
    for _ in range(int(3 * amt)):
        x, y = int(r.uniform(0, W - 200)), int(r.uniform(0, H - 60))
        out[y:y + int(r.uniform(10, 60)), x:x + int(r.uniform(80, 400))] *= np.array(
            [r.uniform(0.3, 1.5), r.uniform(0.3, 1.5), r.uniform(0.3, 1.8)], np.float32)
    # scanlines
    out[::3] *= 1 - 0.18 * amt
    return out


def shockwave(img, t, t0, center, speed=2600, width=220, amp=18):
    dt = t - t0
    if dt < 0 or dt > 0.7:
        return img
    rad = dt * speed
    X, Y = A["X"], A["Y"]
    dxx, dyy = X - center[0], Y - center[1]
    d = np.sqrt(dxx ** 2 + dyy ** 2) + 1e-3
    k = (d - rad) / width
    f = amp * math.exp(-dt * 3.5) * np.exp(-k * k) * np.sin(k * 3.0)
    sx = (X - dxx / d * f).astype(np.float32)
    sy = (Y - dyy / d * f).astype(np.float32)
    out = cv2.remap(img, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ring = np.exp(-k * k * 2) * 0.35 * math.exp(-dt * 4)
    return screen(out, ring[..., None] * np.array([1.0, 0.85, 0.6], np.float32))


def bloom(img, strength=0.5, thresh=0.72):
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = np.clip(small - thresh, 0, None)
    b = cv2.GaussianBlur(b, (0, 0), 6) * 0.6 + cv2.GaussianBlur(b, (0, 0), 22) * 0.8
    b = cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + b * strength


def light_leak(img, t, amount, seed=3):
    if amount <= 0.01:
        return img
    r = rng(seed)
    out = img
    X, Y = A["X"][::4, ::4], A["Y"][::4, ::4]
    acc = np.zeros(X.shape + (3,), np.float32)
    for i in range(3):
        cx = W * (r.uniform(-0.2, 1.2) + 0.25 * math.sin(t * r.uniform(0.6, 1.4) + i))
        cy = H * (r.uniform(0, 1) + 0.15 * math.cos(t * r.uniform(0.5, 1.2) + i))
        rad = r.uniform(400, 900)
        col = [(1.0, 0.55, 0.2), (1.0, 0.3, 0.15), (1.0, 0.8, 0.45)][i]
        g = np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (rad * rad))
        acc += g[..., None] * np.array(col, np.float32)
    acc = cv2.resize(acc, (W, H))
    return screen(out, np.clip(acc, 0, 1), amount)


def shake_frame(img, dx, dy, rot, zoom=1.0):
    if abs(dx) < 0.3 and abs(dy) < 0.3 and abs(rot) < 0.02 and zoom == 1.0:
        return img
    M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, zoom)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)


# ----------------------------------------------------------------------------
# SHOTS  (each returns a graded float RGB frame)
#   t  = global time, u = 0..1 inside the shot, lt = seconds inside the shot
# ----------------------------------------------------------------------------
T_, E_ = "toly", "eminem"


def beat_nod(t, amp=6.0):
    """Head nod that hits on each kick (sharp down, soft return)."""
    v = 0.0
    for k in KICKS:
        dt = t - k
        if 0 <= dt < 0.5:
            v += math.sin(min(dt / 0.09, 1) * math.pi / 2) * math.exp(-dt / 0.16)
    return v * amp


def sh_awaken(t, u, lt):
    """INTRO: Toly's eyes emerge from darkness, light sweeps across."""
    ch = A[T_]
    z = lerp(1500, 1650, ramp_out(u))
    M = char_cam(ch, "eyes", z, (W / 2, H * 0.47), rot=lerp(-3, -1, u), yaw=lerp(-6, 0, u))
    img = realm_bg(t, focus=(470, 260), zoom=2.2, blur=2, sun=0.4, fog=0.3)
    img = over(img, person(ch, M, (lerp(-2.0, 0.5, smooth(u)), 0, 0)))
    # sweep of light
    X, Y = A["X"], A["Y"]
    pos = lerp(-600, 1700, ease_out(u, 2))
    band = np.exp(-(((X * 0.7 + Y * 0.5) - pos) / 420) ** 2)
    expo = 0.30 + 0.75 * ease_out(u, 2)
    img = img * (0.35 + 0.65 * band[..., None]) * expo
    img = grade(img, "realm")
    return particles(img, t, 21, 35, (1.0, 0.8, 0.45), size=(2, 6), glow=0.7)


def sh_realm(t, u, lt):
    """Whip out to Toly in his mountain realm (speed ramp fast->slow)."""
    ch = A[T_]
    v = ramp_out(u)
    z = lerp(1400, 600, v)
    M = char_cam(ch, "eyes", z, (W / 2 + lerp(0, -20, v), lerp(H * 0.47, H * 0.36, v)), rot=lerp(4, 0, v),
                 yaw=lerp(8, 2, v))
    img = realm_bg(t, focus=(470, 330), zoom=lerp(1.5, 1.05, v), at=(W / 2 + lerp(40, -30, u), H / 2),
                   blur=1, sun=1.0, fog=0.5)
    img = over(img, person(ch, M, (lerp(-1.5, 1.5, smooth(u)), 0, 0)))
    img = grade(img, "realm")
    img = particles(img, t, 22, 45, (1.0, 0.82, 0.5), size=(2, 8), glow=0.9)
    return zoom_blur(img, 0.12 * (1 - v) ** 2)


def sh_cold_eyes(t, u, lt):
    ch = A[E_]
    z = lerp(1900, 2050, u)
    M = char_cam(ch, "eyes", z, (W / 2, H * 0.5), rot=lerp(1.5, 0, u))
    img = steel_bg(t, light=(W / 2, H * 0.3), beams=0.3, haze=0.2)
    img = over(img, person(ch, M))
    return grade(img, "steel", 1.05)


def sh_cold_face(t, u, lt):
    ch = A[E_]
    v = ramp(u)
    M = char_cam(ch, "eyes", lerp(860, 940, v), (W / 2 + lerp(-40, 20, v), H * 0.42), rot=lerp(-2, 1, v),
                 yaw=lerp(-9, 4, v))
    img = steel_bg(t, shift=(lerp(80, -60, v), 0), light=(W * 0.5, H * 0.3), beams=0.8)
    img = over(img, person(ch, M, (lerp(1.5, -2.0, smooth(u)), 0, 0)))
    img = grade(img, "steel")
    return particles(img, t, 31, 40, (0.75, 0.85, 1.0), size=(1.5, 4), speed=(40, 120), glow=0.6)


def sh_vest_tilt(t, u, lt):
    """Tilt up from the golden embroidery to Toly's face."""
    ch = A[T_]
    v = ramp(u)
    fx = lerp(560, 465, v)
    fy = lerp(720, 300, v)
    M = char_cam(ch, (fx, fy), lerp(1250, 900, v), (W / 2, H * 0.5), rot=lerp(-5, 2, v), yaw=lerp(5, -3, v))
    img = realm_bg(t, focus=(480, 300), zoom=1.8, blur=2, sun=0.8, fog=0.2)
    img = over(img, person(ch, M, (lerp(0, -2, smooth(u)), 0, 0)))
    img = grade(img, "realm", 1.05)
    img = particles(img, t, 23, 40, (1.0, 0.85, 0.55), size=(2, 7), glow=0.8)
    return light_leak(img, t, 0.25 * (1 - u))


def sh_steel_medium(t, u, lt):
    ch = A[E_]
    v = ramp(u)
    M = char_cam(ch, "eyes", lerp(540, 600, v), (W / 2 + lerp(30, -10, v), H * 0.40), rot=lerp(1.5, -1, v),
                 yaw=lerp(6, -4, v), pitch=lerp(-4, 0, v))
    img = steel_bg(t, shift=(lerp(-50, 50, v), 0), light=(W * 0.5, H * 0.26), beams=1.0, haze=0.5)
    img = over(img, person(ch, M, (lerp(-1, 2, smooth(u)), 0, 0)))
    img = grade(img, "steel")
    return particles(img, t, 32, 60, (0.7, 0.8, 1.0), size=(1.5, 5), speed=(60, 160), glow=0.7)


def sh_diag_split(t, u, lt):
    """Diagonal split: Toly top-left, Eminem bottom-right, seam slides in."""
    a = sh_split_part(T_, t, u, (W * 0.42, H * 0.30), 620)
    b = sh_split_part(E_, t, u, (W * 0.58, H * 0.66), 620)
    X, Y = A["X"], A["Y"]
    off = lerp(-700, 0, ease_out(u * 3, 3))
    line = (Y - H * 0.5) - (X - W / 2) * 0.55 - off * 0.0
    m = np.clip(line / 4 + 0.5, 0, 1)[..., None]
    seam = np.exp(-(line / 10) ** 2)[..., None] * np.array([1.0, 0.9, 0.7], np.float32)
    # slide halves in from opposite corners
    a = shake_frame(a, -off * 0.6, -off * 0.3, 0)
    b = shake_frame(b, off * 0.6, off * 0.3, 0)
    img = a * (1 - m) + b * m
    return screen(img, seam, 1.4)


def sh_split_part(who, t, u, at, fw, look=None):
    ch = A[who]
    v = smooth(u)
    if who == T_:
        bg = realm_bg(t, focus=(470, 300), zoom=1.6, blur=2, sun=0.7, fog=0.3)
        M = char_cam(ch, "eyes", fw * lerp(1.0, 1.08, v), at, rot=lerp(-1, 1, v), yaw=lerp(-4, 3, v))
        img = over(bg, person(ch, M, (lerp(-1, 1.5, v), beat_nod(t, 4), 0)))
        return grade(img, look or "realm")
    bg = steel_bg(t, light=(at[0], at[1] - 300), beams=0.6, haze=0.3)
    M = char_cam(ch, "eyes", fw * lerp(1.0, 1.08, v), at, rot=lerp(1, -1, v), yaw=lerp(4, -3, v))
    img = over(bg, person(ch, M, (lerp(1, -1.5, v), beat_nod(t, 4), 0)))
    return grade(img, look or "steel")


def sh_fairy(t, u, lt):
    """Push into the fairy on Toly's sleeve - magic charge before the beat."""
    ch = A[T_]
    v = ease_in(u, 2)
    M = char_cam(ch, "fairy", lerp(2200, 4200, v), (W / 2, H * 0.5), rot=lerp(0, 8, v))
    img = realm_bg(t, focus=(480, 300), zoom=2.0, blur=2, sun=0.5, fog=0.2)
    img = over(img, person(ch, M))
    img = grade(img, "realm", lerp(1.0, 1.6, v))
    img = particles(img, t, 24, 90, (1.0, 0.9, 0.6), size=(2, 10), glow=0.6 + 1.2 * v,
                    burst=(3.40, (W / 2, H * 0.5), 900))
    img = zoom_blur(img, 0.15 * v)
    return img + v ** 3 * 0.9


def sh_steel_hero(t, u, lt):
    """DROP-IN: Eminem low-angle hero with beams and falling ash."""
    ch = A[E_]
    v = ramp_out(u)
    M = char_cam(ch, "eyes", lerp(760, 680, v), (W / 2, H * 0.40), rot=lerp(-4, -1, v), yaw=lerp(-6, 3, v),
                 pitch=lerp(6, 3, v))
    img = steel_bg(t, shift=(0, lerp(-80, 0, v)), light=(W * 0.5, H * 0.22), beams=1.3, haze=0.5)
    img = over(img, person(ch, M, (lerp(0, -2, v), beat_nod(t, 7), 0)))
    img = grade(img, "steel", 1.05)
    return particles(img, t, 33, 80, (0.75, 0.85, 1.0), size=(1.5, 5), speed=(80, 220), glow=0.8)


def sh_realm_hero(t, u, lt):
    ch = A[T_]
    v = ramp_out(u)
    M = char_cam(ch, "eyes", lerp(700, 610, v), (W / 2 + 10, H * 0.36), rot=lerp(4, 0.5, v), yaw=lerp(7, -2, v),
                 pitch=lerp(5, 2, v))
    img = realm_bg(t, focus=(470, 320), zoom=lerp(1.25, 1.1, v), at=(W / 2 + lerp(-40, 30, u), H / 2), blur=1,
                   sun=1.3, fog=0.5)
    img = over(img, person(ch, M, (lerp(2, -1, v), beat_nod(t, 7), 0)))
    img = grade(img, "realm", 1.05)
    return particles(img, t, 25, 60, (1.0, 0.82, 0.5), size=(2, 8), glow=1.0)


def sh_steel_ecu(t, u, lt):
    ch = A[E_]
    punch = pulse(t, [5.14], 0.10)
    M = char_cam(ch, "eyes", lerp(1700, 1850, u) * (1 + 0.12 * punch), (W / 2, H * 0.48),
                 rot=lerp(-1, 1, u) + 2 * punch)
    img = steel_bg(t, beams=0.4, haze=0.2)
    img = over(img, person(ch, M, (0, beat_nod(t, 4), 0)))
    img = grade(img, "steel", 1.05 + 0.3 * punch)
    return chroma(img, 0.006 + 0.012 * punch)


def sh_realm_ecu(t, u, lt):
    ch = A[T_]
    v = ramp(u)
    M = char_cam(ch, "eyes", lerp(1500, 1650, v), (W / 2 + lerp(-50, 40, v), H * 0.47), rot=lerp(3, -2, v),
                 yaw=lerp(10, -6, v))
    img = realm_bg(t, focus=(470, 260), zoom=2.2, blur=2, sun=0.6, fog=0.2)
    img = over(img, person(ch, M, (lerp(-2, 2, v), beat_nod(t, 3), 0)))
    img = grade(img, "realm", 1.05)
    return light_leak(img, t, 0.35)


def sh_strips(t, u, lt):
    """Kinetic eye-strips: horizontal bands of both faces sliding opposite ways.
    On the 6.325 kick the bands swap people."""
    swap = t >= KICKS[5]
    bands = 4
    bh = H // bands
    out = np.zeros((H, W, 3), np.float32)
    feats = [(E_, "eyes"), (T_, "eyes"), (E_, "mouth"), (T_, "eyes")]
    if swap:
        feats = [(T_, "eyes"), (E_, "eyes"), (T_, "mouth"), (E_, "eyes")]
    lt2 = t - (KICKS[5] if swap else KICKS[4])
    intro = ease_out(lt2 / 0.25, 3)
    for i, (who, feat) in enumerate(feats):
        ch = A[who]
        dirn = 1 if i % 2 == 0 else -1
        slide = dirn * (lerp(W * 1.1, 0, intro) + lt2 * 120)
        cy = bh * i + bh / 2
        M = char_cam(ch, feat, 1250 if feat == "eyes" else 1100, (W / 2 + slide, cy), rot=0)
        if who == T_:
            bg = np.full((H, W, 3), (0.12, 0.15, 0.13), np.float32)
        else:
            bg = np.full((H, W, 3), (0.05, 0.06, 0.08), np.float32)
        lay = over(bg, person(ch, M, (0, beat_nod(t, 3), 0)))
        lay = grade(lay, "realm" if who == T_ else "steel")
        out[bh * i:bh * (i + 1)] = lay[bh * i:bh * (i + 1)]
        # thin glowing divider
        if i > 0:
            out[bh * i - 3:bh * i + 3] = np.array([1.0, 0.85, 0.55], np.float32)
    return out


def sh_echo(t, u, lt):
    """Eminem with stroboscopic echo trails (time echo) + speed ramp push."""
    ch = A[E_]
    acc = None
    bg = steel_bg(t, light=(W * 0.5, H * 0.25), beams=1.0, haze=0.4)
    img = bg.copy()
    for k, (dt, op) in enumerate([(0.24, 0.18), (0.16, 0.25), (0.08, 0.35), (0.0, 1.0)]):
        uu = clamp01((lt - dt) / 0.52)
        v = ramp(uu)
        M = char_cam(ch, "eyes", lerp(620, 900, v), (W / 2 + lerp(-120, 0, v), H * 0.42), rot=lerp(-6, 1, v),
                     yaw=lerp(-8, 2, v))
        lay = person(ch, M, (lerp(3, -1, v), 0, 0))
        if op < 1:
            lay[:, :, :3] *= np.array([0.6, 0.8, 1.4], np.float32)
        img = over(img, lay, op)
    return grade(img, "steel", 1.05)


def sh_double_exposure(t, u, lt, push=(0, 1), big=False):
    """Worlds merge: Eminem's face in the sky above Toly's mountains."""
    ch_t, ch_e = A[T_], A[E_]
    v = ramp(u) if not big else ease_out(u, 2)
    p = lerp(push[0], push[1], v)
    img = realm_bg(t, focus=(470, 200), zoom=lerp(1.15, 1.25, p), at=(W / 2, H * 0.45), blur=1, sun=1.2,
                   fog=0.6)
    # Eminem as a giant in the clouds (screen blend, soft mask)
    Me = char_cam(ch_e, "eyes", lerp(900, 980, p), (W / 2 + lerp(20, -10, p), H * 0.24), rot=lerp(-1, 1, p))
    e = person(ch_e, Me, (lerp(1, -1, p), beat_nod(t, 3), 0))
    X, Y = A["X"], A["Y"]
    mask = np.clip(1.25 - Y / (H * 0.5), 0, 1)[..., None]
    lum = (e[:, :, :3] * np.array([0.3, 0.59, 0.11], np.float32)).sum(2, keepdims=True)
    eg = np.clip((lum - 0.05) * 1.25, 0, 1) * np.array([0.85, 0.92, 1.05], np.float32)
    img = screen(img, eg * e[:, :, 3:4] * mask, 0.85)
    img = img * (1 - 0.35 * e[:, :, 3:4] * mask * (1 - lum))  # darken where his shadows are
    # Toly in front
    Mt = char_cam(ch_t, "eyes", lerp(380, 430, p), (W / 2 + lerp(10, 0, p), H * 0.63), rot=lerp(1, -0.5, p),
                  yaw=lerp(3, -2, p))
    img = over(img, person(ch_t, Mt, (lerp(-1, 1.5, p), beat_nod(t, 5), 0)))
    img = add_fog(img, t + 3, 0.35)
    img = grade(img, "duo", 1.05)
    return particles(img, t, 26, 70, (1.0, 0.85, 0.55), size=(2, 8), glow=0.9)


def sh_quick(t, u, lt, who, feat, fw, rot0, look):
    ch = A[who]
    M = char_cam(ch, feat, fw * lerp(1.15, 1.0, ease_out(u, 3)), (W / 2, H * 0.47), rot=lerp(rot0, rot0 * 0.2, ease_out(u)))
    if who == T_:
        bg = realm_bg(t, focus=(470, 260), zoom=2.0, blur=2, sun=0.6, fog=0.2)
    else:
        bg = steel_bg(t, beams=0.6, haze=0.2)
    img = over(bg, person(ch, M, (0, beat_nod(t, 4), 0)))
    return grade(img, look, 1.05)


def sh_tension(t, u, lt):
    """10.00 - 10.75: stutter alternation with rising tension."""
    seg = int(lt / 0.2625)
    lu = (lt % 0.2625) / 0.2625
    if seg == 0:
        img = sh_quick(t, lu, 0, E_, "eyes", 1100, -3, "steel")
    elif seg == 1:
        img = sh_quick(t, lu, 0, T_, "eyes", 1250, 3, "realm")
    else:
        a = sh_quick(t, lu, 0, E_, "eyes", lerp(1400, 2000, lu), 0, "steel")
        b = sh_quick(t, lu, 0, T_, "eyes", lerp(1500, 2100, lu), 0, "realm")
        img = a * 0.5 + b * 0.5 if int(lt * 30) % 2 else (a * 0.7 + b * 0.3)
    return chroma(img, 0.004 + 0.02 * u)


def sh_breath(t, u, lt):
    """The silence before the drop: only rim light and eyes, not pure black."""
    img = sh_faceoff(t, 0.0, 0.0, intensity=0.0)
    return img * 0.12 + np.array([0.01, 0.012, 0.02], np.float32)


def sh_faceoff(t, u, lt, intensity=1.0):
    """FINAL: top/bottom face-off, glowing seam."""
    dt = max(0.0, t - DROP)
    punch = math.exp(-dt / 0.35)
    v = ease_out(min(1, dt / 2.0), 3)
    late = smooth((t - 11.7) / 1.3)
    seam_y = H * 0.5 + 18 * math.sin(t * 2)
    fw = lerp(640, 700, v) * (1 + 0.25 * punch * intensity) * (1 + 0.06 * late)
    top = sh_split_part_final(E_, t, (W / 2, seam_y * 0.47), fw, v)
    bot = sh_split_part_final(T_, t, (W / 2, seam_y + (H - seam_y) * 0.47), fw * 1.02, v)
    Y = A["Y"]
    m = np.clip((Y - seam_y) / 3 + 0.5, 0, 1)[..., None]
    img = top * (1 - m) + bot * m
    seam = np.exp(-((Y - seam_y) / (6 + 30 * punch * intensity)) ** 2)[..., None]
    img = screen(img, seam * np.array([1.0, 0.82, 0.5], np.float32), 1.5 * (0.6 + 0.4 * intensity))
    if intensity > 0:
        img = particles(img, t, 27, 120, (1.0, 0.85, 0.55), size=(2, 9), glow=1.2,
                        burst=(DROP, (W / 2, seam_y), 1900))
    return img


def sh_split_part_final(who, t, at, fw, v):
    ch = A[who]
    if who == T_:
        bg = realm_bg(t, focus=(470, 260), zoom=1.9, blur=2, sun=1.0, fog=0.3)
        M = char_cam(ch, "eyes", fw, at, rot=lerp(2, 0, v), yaw=lerp(-6, 2, v))
        img = over(bg, person(ch, M, (lerp(-2, 1.5, v), beat_nod(t, 3), 0)))
        return grade(img, "realm", 1.05)
    bg = steel_bg(t, light=(at[0], at[1] - 250), beams=0.9, haze=0.3)
    M = char_cam(ch, "eyes", fw, at, rot=lerp(-2, 0, v), yaw=lerp(6, -2, v))
    img = over(bg, person(ch, M, (lerp(2, -1.5, v), beat_nod(t, 3), 0)))
    return grade(img, "steel", 1.05)


# quick-cut section 7.90 - 8.95 (half-beat cuts)
QUICK = [
    (E_, "mouth", 1300, -4, "steel"),
    (T_, "eyes", 1350, 4, "realm"),
    (E_, "earring", 1500, -3, "steel"),
    (T_, "vest", 1400, 5, "realm"),
]


def sh_quickcuts(t, u, lt):
    seg = min(3, int(lt / 0.2625))
    lu = (lt - seg * 0.2625) / 0.2625
    who, feat, fw, rot, look = QUICK[seg]
    img = sh_quick(t, lu, 0, who, feat, fw, rot, look)
    return chroma(img, 0.008 * (1 - lu))


# ----------------------------------------------------------------------------
# TIMELINE   (start, end, shot, motion-blur samples)
# ----------------------------------------------------------------------------
SHOTS = [
    (0.00, 0.84, sh_awaken),
    (0.84, 1.35, sh_realm),
    (1.35, 1.76, sh_cold_eyes),
    (1.76, 2.11, sh_cold_face),
    (2.11, 2.62, sh_vest_tilt),
    (2.62, 3.03, sh_steel_medium),
    (3.03, 3.40, sh_diag_split),
    (3.40, 3.70, sh_fairy),
    (KICKS[0], KICKS[1], sh_steel_hero),
    (KICKS[1], KICKS[2], sh_realm_hero),
    (KICKS[2], KICKS[3], sh_steel_ecu),
    (KICKS[3], KICKS[4], sh_realm_ecu),
    (KICKS[4], KICKS[6], sh_strips),
    (KICKS[6], KICKS[7], sh_echo),
    (KICKS[7], KICKS[8], lambda t, u, lt: sh_double_exposure(t, u, lt, (0, 0.4))),
    (KICKS[8], KICKS[10], sh_quickcuts),
    (KICKS[10], KICKS[12], lambda t, u, lt: sh_double_exposure(t, u, lt, (0.3, 1.0))),
    (KICKS[12], 10.80, sh_tension),
    (10.80, DROP, sh_breath),
    (DROP, DURATION + 1, sh_faceoff),
]

# cut points that get a flash / shake / glitch
FLASH_HITS = [(0.84, 0.9), (1.35, 0.5), (2.11, 1.0), (3.03, 0.6), (3.70, 1.2), (4.225, 0.7), (4.75, 0.7),
              (5.275, 0.6), (5.80, 0.8), (6.325, 0.8), (6.85, 0.6), (7.375, 0.9), (7.90, 0.6), (8.1625, 0.5),
              (8.425, 0.6), (8.6875, 0.5), (8.95, 1.0), (10.00, 0.7), (10.2625, 0.6), (10.525, 0.7),
              (DROP, 1.8), (DROP2, 0.5)]
SHAKE_HITS = [(3.70, 1.0), (4.225, 0.6), (4.75, 0.6), (5.14, 0.5), (5.80, 0.6), (6.325, 0.6), (6.85, 0.5),
              (7.375, 0.5), (7.90, 0.5), (8.425, 0.5), (8.95, 0.8), (9.475, 0.6), (9.72, 0.5), (10.00, 0.7),
              (10.525, 0.8), (DROP, 2.0), (DROP2, 0.6)]
GLITCH_WIN = [(1.35, 0.12, 1.0), (3.03, 0.10, 0.8), (6.85, 0.08, 0.6), (8.95, 0.07, 0.6), (10.525, 0.2, 0.9),
              (DROP - 0.03, 0.10, 1.0)]


def shot_at(t):
    for s, e, f in SHOTS:
        if s <= t < e:
            return s, e, f
    return SHOTS[-1]


def render_raw(t):
    s, e, f = shot_at(t)
    lt = t - s
    u = clamp01(lt / (e - s)) if e - s < 5 else clamp01(lt / (DURATION - s))
    return f(t, u, lt)


def render_frame(i):
    t0 = i / FPS
    s, e, _ = shot_at(t0)
    # motion blur: sample inside the shutter, but never across a cut
    offs = [(k / max(1, MB_SAMPLES - 1) - 0.5) * SHUTTER / FPS for k in range(MB_SAMPLES)] if MB_SAMPLES > 1 else [0]
    ts = [min(max(t0 + o, s), e - 1e-4) for o in offs]
    acc = None
    for tt in ts:
        fr = render_raw(tt)
        acc = fr if acc is None else acc + fr
    img = acc / len(ts)
    return post(img, t0, i)


def post(img, t, i):
    # shake (decaying noise)
    sh = 0.0
    for ht, a in SHAKE_HITS:
        dt = t - ht
        if 0 <= dt < 0.6:
            sh += a * math.exp(-dt / 0.13)
    if sh > 0.01:
        dx = hash_noise(t, 1, 60) * 28 * sh
        dy = hash_noise(t, 2, 55) * 34 * sh
        rot = hash_noise(t, 3, 40) * 1.6 * sh
        img = shake_frame(img, dx, dy, rot, 1.0 + 0.05 * min(sh, 1.5))
    # drop shockwave
    img = shockwave(img, t, DROP, (W / 2, H / 2))
    img = shockwave(img, t, DROP2, (W / 2, H / 2), amp=8, width=160)
    # glitch windows
    for gt, gd, ga in GLITCH_WIN:
        if gt <= t < gt + gd:
            img = glitch(img, ga * (1 - (t - gt) / gd * 0.5), seed=int(t * 1000))
    # chromatic aberration grows with shake
    img = chroma(img, 0.0015 + 0.004 * min(sh, 2))
    # flashes (white -> warm)
    fl = 0.0
    for ht, a in FLASH_HITS:
        dt = t - ht
        if 0 <= dt < 0.5:
            fl += a * math.exp(-dt / 0.06)
    img = bloom(img, 0.3 + 0.4 * min(fl, 1.5), 0.82)
    if fl > 0.01:
        img = img + np.array([1.0, 0.93, 0.82], np.float32) * min(fl, 1.6) * 0.55
    img = img * A["vignette"]
    # outro fade (keep a faint glow, never a dead black frame until the last ~0.25 s)
    if t > DURATION - 0.9:
        k = clamp01((DURATION - t) / 0.9)
        img = img * (0.02 + 0.98 * k ** 1.5)
    # film grain
    g = cv2.resize(A["grain"][i % len(A["grain"])], (W, H), interpolation=cv2.INTER_LINEAR)
    img = img + g[..., None] * 0.022
    # filmic roll-off
    img = np.clip(img, 0, None)
    img = np.where(img < 0.8, img, 0.8 + 0.2 * (1 - np.exp(-(img - 0.8) / 0.2)))
    return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------
def init_worker(scale):
    global A
    A = load_assets(scale)


def worker(i):
    return render_frame(i)


def make_audio(out_wav):
    """Original audio + an echo tail of the drop so the ending rings out."""
    src = os.path.join(BUILD, "original_audio.wav")
    fc = ("[0:a]atrim=0:11.9,asetpts=PTS-STARTPTS,afade=t=out:st=11.75:d=0.15[dry];"
          "[0:a]atrim=10.86:11.75,asetpts=PTS-STARTPTS,lowpass=f=3500,volume=0.38,adelay=11400|11400[e1];"
          "[0:a]atrim=10.86:11.75,asetpts=PTS-STARTPTS,lowpass=f=2200,volume=0.17,adelay=11950|11950[e2];"
          "[dry][e1][e2]amix=inputs=3:normalize=0,apad=whole_dur=%.2f,atrim=0:%.2f,"
          "afade=t=out:st=%.2f:d=0.8[a]" % (DURATION, DURATION, DURATION - 0.8))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[a]",
                    "-ar", "48000", "-c:a", "pcm_s16le", out_wav], check=True)


def main():
    global W, H, MB_SAMPLES, A
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--still", nargs="*", type=float)
    ap.add_argument("--out", default=os.path.join(FINAL_DIR, "final_edit.mp4"))
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=DURATION)
    args = ap.parse_args()
    if args.preview:
        MB_SAMPLES = 1

    if args.still:
        init_worker(1)
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for t in args.still:
            fr = render_frame(int(round(t * FPS)))
            p = os.path.join(HERE, "stills", f"still_{t:05.2f}.jpg")
            cv2.imwrite(p, fr[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
            print(p)
        return

    audio = os.path.join(BUILD, "edit_audio.wav")
    make_audio(audio)
    n0, n1 = int(round(args.start * FPS)), int(round(args.end * FPS))
    vf = "scale=540:960" if args.preview else "null"
    enc = (["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"] if args.preview else
           ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-maxrate", "40M", "-bufsize", "60M",
            "-profile:v", "high", "-level", "4.2"])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", f"{args.start}", "-i", audio,
           "-vf", vf, *enc, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
           "-shortest", "-movflags", "+faststart", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(args.workers, initializer=init_worker, initargs=(1,)) as pool:
        for k, fr in enumerate(pool.imap(worker, range(n0, n1), chunksize=2)):
            ff.stdin.write(fr.tobytes())
            if k % 30 == 0:
                print(f"frame {n0 + k}/{n1}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", args.out)


if __name__ == "__main__":
    main()
