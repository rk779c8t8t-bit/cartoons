"""TOLY SUMMER × EMINEM — photo-based music edit (v2).

The original photos are never altered: each photo is drawn as one flat card that
moves as a whole (scale / rotate / translate / fade). Cut-out copies of the same
pixels are only used for layering text behind the person.

Timeline (s): 0 intro | 2.05 Toly | 4.40 swap | 4.55 L1 | 6.55 L2 | 8.50 L3 | 10.55 L4 | 12.58 finale | 15.0
"""
import math, os
import cv2, numpy as np, skia
from core import *
from fx import (bg_grad, vignette, glow_spot, Dust, Embers, rays, halftone, spot_beam, ring3d, shockwave,
                wire_ico, grain)
from typo import Word, Block

SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
LY, LE = T['lyrics'], T['line_end']


def wt(who, line, k, lead=0.03):
    return LY[who][line][k][1][0] - lead


def load(name, cut=False):
    p = os.path.join(ROOT, 'assets', 'photos', f'{name}{"_cut" if cut else ""}.png')
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    a = cv2.cvtColor(a, cv2.COLOR_BGRA2RGBA if cut else cv2.COLOR_BGR2RGBA)
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()


class Photo:
    def __init__(self, name):
        self.img, self.cut = load(name), load(name, True)
        self.w, self.h = self.img.width(), self.img.height()
        self.aspect = self.w / self.h

    def draw(self, c, cx, cy, h, rot=0.0, alpha=1.0, iz=1.0, ix=0.0, iy=0.0, mode='full', border=True,
             shadow=True, ghost=None):
        """Card centred at (cx, cy), card height h px. iz/ix/iy = zoom/pan of the photo inside the card."""
        if alpha <= 0.005 or h < 4:
            return
        w = h * self.aspect
        rr = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), h * 0.022, h * 0.022)
        c.save()
        c.translate(cx, cy)
        c.rotate(rot)
        if mode == 'full' and shadow:
            c.drawRRect(rr.makeOffset(h * 0.015, h * 0.03), P('#000000', 0.65 * alpha, blur=h * 0.03))
        c.clipRRect(rr, doAntiAlias=True)
        k = h / self.h * iz
        c.translate(ix * w, iy * h)
        c.scale(k, k)
        pa = skia.Paint(AntiAlias=True)
        pa.setAlphaf(alpha)
        if ghost:
            pa.setColorFilter(skia.ColorFilters.Blend(C(ghost, 1), skia.BlendMode.kMultiply))
            pa.setBlendMode(ADD)
        c.drawImage(self.cut if mode == 'cut' else self.img, -self.w / 2, -self.h / 2, SAMP, pa)
        c.restore()
        if mode == 'full' and border and not ghost:
            c.save(); c.translate(cx, cy); c.rotate(rot)
            c.drawRRect(rr, P('#000000', 0.35 * alpha, stroke=h * 0.05, blur=h * 0.02))  # inner edge shade
            c.drawRRect(rr, P('#ffcf6b', alpha, stroke=max(3, h * 0.006)))
            c.restore()


PH = {}


def ph(n):
    if n not in PH:
        PH[n] = Photo(n)
    return PH[n]


def card(c, n, st, t, mode='full', blur_trail=True, **kw):
    """st(t) -> dict(cx, cy, h, rot, alpha, iz, ix, iy). Draws motion-trail ghosts when moving fast."""
    s = st(t)
    if blur_trail and mode == 'full':
        s0 = st(t - 1 / 60)
        v = math.hypot(s['cx'] - s0['cx'], s['cy'] - s0['cy']) + abs(s['h'] - s0['h']) * 0.5
        if v > 25:
            n_g = 4
            for g in range(n_g, 0, -1):
                sg = st(t - g * 0.006)
                ph(n).draw(c, alpha=s.get('alpha', 1) * 0.18, shadow=False, border=False,
                           **{k: sg[k] for k in sg if k != 'alpha'}, **kw)
    ph(n).draw(c, mode=mode, **s, **kw)


def S(cx, cy, h, rot=0.0, alpha=1.0, iz=1.0, ix=0.0, iy=0.0):
    return dict(cx=cx, cy=cy, h=h, rot=rot, alpha=alpha, iz=iz, ix=ix, iy=iy)


def punch(t, amt=0.06, decay=11):
    return 1 + amt * beat_pulse(t, decay)


def sway(t, amp=2.5):
    """Rotation flips side on every beat with an eased swing."""
    ph_, i = beat_phase(t)
    side = 1 if i % 2 else -1
    return side * amp * (1 - e_out(clamp(ph_ * 1.6))) * 0.8 + side * amp * 0.2


def hit_env(t, t0, up=0.06, down=0.35):
    if t < t0:
        return 0.0
    if t < t0 + up:
        return e_out((t - t0) / up)
    return max(0.0, 1 - e_out((t - t0 - up) / down))


def light_lines(c, t, ang, n, alpha, seed=0, col='#ffcf6b', speed=900):
    if alpha <= 0.01:
        return
    c.save(); c.translate(W / 2, H / 2); c.rotate(ang)
    for k in range(n):
        y = (rnd(k, seed) - 0.5) * 2600
        L = 200 + 700 * rnd(k, seed + 1)
        x = ((t * speed * (0.6 + rnd(k, seed + 2)) + rnd(k, seed + 3) * 4000) % 4000) - 2000
        wdt = 1.5 + 3 * rnd(k, seed + 4)
        sh = lin(x - L, 0, x, 0, [C(col, 0), C(col, alpha)])
        c.drawRect(skia.Rect(x - L, y, x, y + wdt), P('#ffffff', 1, shader=sh, blend=ADD))
    c.restore()


def frame_lines(c, t, a, inset=46):
    """Thin gold safe-frame with corner ticks (editorial look)."""
    if a <= 0.01:
        return
    pp = P('#ffcf6b', 0.35 * a, stroke=2)
    c.drawRect(skia.Rect(inset, inset, W - inset, H - inset), pp)
    L = 70
    for x, y, sx, sy in [(inset, inset, 1, 1), (W - inset, inset, -1, 1), (inset, H - inset, 1, -1),
                         (W - inset, H - inset, -1, -1)]:
        c.drawLine(x, y, x + sx * L, y, P('#ffe7a1', a, stroke=5))
        c.drawLine(x, y, x, y + sy * L, P('#ffe7a1', a, stroke=5))


def bars(c, t, a, seed, col='#b5121b', n=3):
    """Big translucent geometric slabs drifting behind the photo (depth layers)."""
    for k in range(n):
        ang = -18 + rnd(k, seed) * 36
        y = H * (0.15 + 0.7 * rnd(k, seed + 1)) + math.sin(t * 0.7 + k) * 60
        hgt = 60 + 220 * rnd(k, seed + 2)
        c.save(); c.translate(W / 2, y); c.rotate(ang)
        c.drawRect(skia.Rect(-1400, -hgt / 2, 1400, hgt / 2), P(col, a * (0.18 + 0.2 * rnd(k, seed + 3))))
        c.restore()


def tri_outline(c, cx, cy, r, rot, a, col='#ffcf6b', width=4):
    if a <= 0.01:
        return
    pts = [(cx + r * math.cos(rot + i * 2.094), cy + r * math.sin(rot + i * 2.094)) for i in range(3)]
    c.drawPath(path_poly(pts), P(col, a * 0.4, stroke=width * 4, blur=width * 2, blend=ADD))
    c.drawPath(path_poly(pts), P(col, a, stroke=width))


def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0, dx=0.0, dy=0.0):
    c.translate(cx + dx, cy + dy); c.rotate(rot); c.scale(zoom, zoom); c.translate(-cx, -cy)


SH = Shake(7)


def shake(t, hits, amp=18, dur=0.28):
    a = 0
    for h in hits:
        if h <= t < h + dur:
            a = max(a, amp * (1 - (t - h) / dur) ** 2)
    return SH.at(t, a)


# ============================================================== INTRO 0 - 2.05
DUST = Dust(220, 1)


def toly_intro_state(t):
    p = prog(t, 0.25, 2.05)
    h = lerp(260, 1150, e_in(p) * 0.55 + p * 0.45) * (1 + 0.05 * hit_env(t, 1.03))
    return S(W / 2, 1000, h, rot=lerp(-14, -2, e_out(p)), alpha=prog(t, 0.25, 0.8), iz=1.0)


def scene_intro(c, t):
    bg_grad(c, '#020001', '#0e0205', '#020001')
    glow_spot(c, W / 2, 1000, 950, '#4a0a14', 0.7 * prog(t, 0, 1))
    light_lines(c, t, -30, 18, 0.5 * prog(t, 0.3, 1.2), seed=2)
    for hb in (0.0, 1.03):
        shockwave(c, W / 2, 1000, (t - hb) / 0.9, 950, width=22)
    for k, (r, tl, sp) in enumerate([(520, 1.15, 0.6), (640, 1.3, -0.4)]):
        ring3d(c, W / 2, 1000, r * (1 + 0.6 * e_in(prog(t, 1.6, 2.05))), tl, t * sp + k,
               prog(t, 0.2 + k * 0.2, 0.8 + k * 0.2), dash=[40, 24] if k else None, t=t)
    tri_outline(c, W / 2, 1000, 760, t * 0.3 - 1.57, 0.5 * prog(t, 0.5, 1.2))
    DUST.draw(c, t, t * 450 + 1200 * e_in(prog(t, 0, 2.05)), alpha=clamp(t * 2), cy=1000,
              streak=2.0 * e_in(prog(t, 1.2, 2.05)))
    card(c, 'toly', toly_intro_state, t)
    frame_lines(c, t, prog(t, 0.6, 1.2))
    c.drawRect(skia.Rect(0, 0, W, H), P('#fff3d0', 0.95 * e_in(prog(t, 1.88, 2.05))))


# ============================================================== TOLY 2.05 - 4.40
EMB = Embers(60, 4)
TG = [wt('toly', 0, k) for k in range(4)]  # ГОРИ, Я ГОРЮ ТОЖЕ
TOLY_BACK = Block([[Word('ГОРИ,', TG[0], 'fire', 'slam', 1.0, glow=('#ff6a1a', 0.9), depth=18)]],
                  y_top=250, size=330, max_w=1040)
TOLY_MID = Block([[Word('Я', TG[1], 'cream', 'drop', 0.8), Word('ГОРЮ', TG[2], 'fire', 'zoom', 1.0, pill=True,
                        glow=('#ff6a1a', 0.7))]], y_top=1290, size=180)
TOLY_FRONT = Block([[Word('ТОЖЕ', TG[3], 'gold', 'slam', 1.0, glow=('#ffb347', 0.9), depth=20)]],
                   y_top=1500, size=300, max_w=1000)


def toly_state(t):
    pin = e_out(prog(t, 2.05, 2.5))
    h = lerp(1400, 1350, pin) * punch(t, 0.05) * (1 + 0.10 * hit_env(t, TG[0]) + 0.12 * hit_env(t, TG[3]))
    out = e_in(prog(t, 4.36, 4.58))
    cx = W / 2 + 26 * math.sin(t * math.pi / 0.98) - 900 * out
    cy = 1010 + 18 * math.sin(t * math.pi / 0.49) - 1500 * out
    return S(cx, cy, h, rot=sway(t, 2.2) - 25 * out, iz=1.0 + 0.06 * prog(t, 2.05, 4.4), iy=0.02)


def scene_toly(c, t):
    surge = hit_env(t, TG[3], 0.08, 0.6)
    bg_grad(c, '#120204', '#3a0709', '#1e0305')
    glow_spot(c, W / 2, H, 1300, '#ff4a12', 0.45 + 0.35 * surge + 0.15 * beat_pulse(t))
    bars(c, t, 1.0, 5, '#7d0a12')
    light_lines(c, t, -22, 22, 0.55, seed=4, col='#ff9a3a', speed=1300)
    ring3d(c, W / 2, 1000, 680 * punch(t, 0.04), 0.2, t * 0.3, 0.9, width=5)
    tri_outline(c, W / 2, 1050, 860 * punch(t, 0.05), -1.57 + t * 0.15, 0.55, col='#ff9a3a')
    c.save()
    dx, dy, rr = shake(t, [TG[0], TG[3]], 22)
    cam(c, 1.0 + 0.03 * prog(t, 2.05, 4.4), dx=dx, dy=dy, rot=rr * 15)
    card(c, 'toly', toly_state, t)
    TOLY_BACK.draw(c, t, exit_t=4.34, exit_kind='up')
    card(c, 'toly', toly_state, t, mode='cut')      # person in front of "ГОРИ,"
    EMB.draw(c, t, H + 40, alpha=1, boost=1 + surge)
    c.restore()
    TOLY_MID.draw(c, t, exit_t=4.36, exit_kind='scatter')
    TOLY_FRONT.draw(c, t, exit_t=4.36, exit_kind='zoom')
    frame_lines(c, t, 1)
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffd9a0', 0.9 * (1 - prog(t, 2.05, 2.3))))
    c.drawRect(skia.Rect(0, 0, W, H), P('#ff7a1a', 0.3 * hit_env(t, TG[3], 0.03, 0.3), blend=ADD))


# ============================================================== EMINEM L1 4.40 - 6.55
E1 = [wt('eminem', 0, k) for k in range(8)]
L1_BACK = Block([[Word('NOW,', E1[0], 'gold', 'slam', 1.0, glow=('#ffb347', 0.7), depth=22)]],
                y_top=230, size=380, max_w=1020)
L1_MID = Block([[Word('THIS', E1[1], 'white', 'drop'), Word('LOOKS', E1[2], 'white', 'drop')],
                [Word('LIKE', E1[3], 'white', 'drop'), Word('A', E1[4], 'white', 'drop')]],
               cx=270, y_top=1330, size=120, max_w=480)
L1_JOB = Block([[Word('JOB', E1[5], 'gold', 'zoom', 1.0, glow=('#ffb347', 0.8), depth=18)]],
               cx=700, y_top=1320, size=270)
L1_FORME = Block([[Word('FOR', E1[6], 'cream', 'rise', 0.75), Word('ME', E1[7], 'gold', 'slam', 1.0, pill=True,
                        glow=('#ffb347', 0.6))]], y_top=1610, size=190)


def em1_state(t):
    ent = e_out(prog(t, 4.40, 4.62))
    h = lerp(1200, 1260, prog(t, 4.6, 6.5)) * punch(t, 0.05) * (1 + 0.14 * hit_env(t, E1[0]) + 0.16 * hit_env(t, E1[5])
                                                               + 0.1 * hit_env(t, E1[7]))
    _, bi = beat_phase(t)
    target = [-70, 70][bi % 2]
    ph_, _ = beat_phase(t)
    cx = W / 2 + lerp(-target, target, e_io(clamp(ph_ * 2))) * 0.6
    out = e_in(prog(t, 6.42, 6.58))
    cy = lerp(H + 900, 960, ent) + 20 * math.sin(t * 6.4)
    return S(cx, cy, h * (1 + 1.4 * out), rot=sway(t, 2.0) + lerp(12, 0, ent), alpha=1 - out * 0.8,
             iz=1.0 + 0.08 * prog(t, 4.5, 6.5))


def stage(c, t, base='#1a0306', rcol='#2b070e'):
    bg_grad(c, '#060102', base, '#060102')
    rays(c, t, W / 2, 980, 24, rcol, '#0e0205', t * 0.1, alpha=1)
    halftone(c, 0, 1450, W, H, 26, 7, '#000000', 0.45)


def scene_em1(c, t):
    stage(c, t)
    spot_beam(c, W / 2, -80, W / 2, 1700, 40, 420, '#ffd27a', 0.22)
    light_lines(c, t, 90, 16, 0.4, seed=8)
    ring3d(c, W / 2, 960, 640 * punch(t, 0.04), 0.1, -t * 0.2, 0.8, dash=[34, 20], t=t, width=4)
    c.save()
    dx, dy, rr = shake(t, [E1[0], E1[5], E1[7]], 18)
    cam(c, lerp(1.08, 1.0, e_out(prog(t, 4.45, 5.0))), dx=dx, dy=dy, rot=rr * 15)
    card(c, 'eminem', em1_state, t)
    L1_BACK.draw(c, t, exit_t=6.40, exit_kind='up')
    card(c, 'eminem', em1_state, t, mode='cut')
    c.restore()
    L1_MID.draw(c, t, exit_t=6.40, exit_kind='scatter')
    L1_JOB.draw(c, t, exit_t=6.40, exit_kind='zoom')
    L1_FORME.draw(c, t, exit_t=6.40, exit_kind='scatter')
    frame_lines(c, t, 1)
    c.drawRect(skia.Rect(0, 0, W, H), P('#fff3d0', 0.5 * hit_env(t, E1[0], 0.02, 0.2)))


# ============================================================== EMINEM L2 6.55 - 8.50
E2 = [wt('eminem', 1, k) for k in range(5)]
L2_TOP = Block([[Word('SO', E2[0], 'white', 'drop', 0.8), Word('EVERYBODY,', E2[1], 'gold', 'drop', 1.0,
                      glow=('#ffb347', 0.5))],
                [Word('JUST', E2[2], 'cream', 'flip', 0.7)]], y_top=170, size=150)
L2_FOLLOW = Block([[Word('FOLLOW', E2[3], 'gold', 'snake', 1.0, glow=('#ffb347', 0.7), depth=16)],
                   [Word('ME', E2[4], 'white', 'snake', 1.05, pill=True)]], y_top=1440, size=230)
# satellite copies of the photo: (angle on the ring, delay)
SAT = [(-2.6, 0.00), (-0.55, 0.06), (2.1, 0.12), (0.5, 0.18), (-1.6, 0.24), (3.0, 0.30)]


def em2_main(t):
    ent = e_out(prog(t, 6.52, 6.75))
    fol = e_io(prog(t, E2[3], 8.45))
    h = lerp(2600, 820, ent) * punch(t, 0.06) * (1 + 0.12 * hit_env(t, E2[1]) + 0.15 * hit_env(t, E2[3]))
    return S(W / 2 + 40 * math.sin(t * 3.2), lerp(980, 1000, fol) - 30 * fol, h, rot=sway(t, 3) * (1 - ent * 0.3),
             iz=1.05, alpha=1)


def sat_state(k, t):
    ang, dl = SAT[k]
    a = e_back(prog(t, E2[1] + dl, E2[1] + dl + 0.25), 1.4)
    fol = e_io(prog(t, E2[3] + dl * 0.5, 8.40 + dl * 0.2))
    rad_ = 430 + 25 * beat_pulse(t)
    x0, y0 = W / 2 + math.cos(ang + t * 0.5) * rad_, 1000 + math.sin(ang + t * 0.5) * rad_ * 1.15
    # "follow": they line up in a column trailing behind the main photo
    x1, y1 = W / 2 + (k - 2.5) * 6, 1000 + 260 + k * 70
    x = lerp(x0, x1, fol); y = lerp(y0, y1, fol)
    return S(x, y, 330 * a * (1 - 0.2 * fol), rot=(rnd(k, 3) - 0.5) * 30 * (1 - fol), alpha=clamp(a * 1.5) * 0.95)


def scene_em2(c, t):
    stage(c, t, '#1c0710', '#2a0a14')
    halftone(c, 0, 0, W, 700, 30, 6, '#ffcf6b', 0.07, grad_dir=-1)
    bars(c, t, 1.0, 9, '#5c0f1c')
    for k in range(5):
        spot_beam(c, (k + 0.5) / 5 * W, -50, (k + 0.5) / 5 * W + math.sin(t * 1.5 + k) * 160, 1600, 18, 170,
                  '#ffd27a', 0.10 * prog(t, E2[1], E2[1] + 0.4))
    c.save()
    dx, dy, rr = shake(t, [E2[1], E2[3]], 16)
    cam(c, 1.0, dx=dx, dy=dy, rot=rr * 15 + lerp(-2, 2, prog(t, 6.5, 8.5)))
    for k in reversed(range(len(SAT))):
        card(c, 'eminem', lambda tt, k=k: sat_state(k, tt), t, blur_trail=False)
    card(c, 'eminem', em2_main, t)
    c.restore()
    L2_TOP.draw(c, t, exit_t=8.40, exit_kind='up')
    L2_FOLLOW.draw(c, t, exit_t=8.42, exit_kind='scatter')
    # chevrons pointing down the follow line
    fa = prog(t, E2[3], E2[3] + 0.2) * (1 - prog(t, 8.38, 8.5))
    for k in range(5):
        y = 380 + ((t * 500 + k * 80) % 400)
        for sgn in (-1, 1):
            x = W / 2 + sgn * 470
            c.drawPath(path_poly([(x - 26, y - 14), (x, y + 10), (x + 26, y - 14)], close=False),
                       P('#ffcf6b', fa * (1 - ((t * 500 + k * 80) % 400) / 400), stroke=7))
    frame_lines(c, t, 1)


# ============================================================== EMINEM L3 8.50 - 10.55
E3 = [wt('eminem', 2, k) for k in range(6)]
HIT3 = E3[5]
L3_TOP = Block([[Word('’CAUSE', E3[0], 'white', 'flip', 0.85), Word('WE', E3[1], 'white', 'flip', 0.85),
                 Word('NEED', E3[2], 'gold', 'flip', 1.0)],
                [Word('A', E3[3], 'cream', 'rise', 0.7), Word('LITTLE', E3[4], 'cream', 'rise', 0.7)]],
               y_top=150, size=150)
L3_BIG = Block([[Word('CONTROVERSY', HIT3, 'gold', 'glitch', 1.0, glow=('#ff2a3c', 0.9), depth=16)]],
               cx=0, y_top=-100, size=250, max_w=1800)


def em3_state(t):
    ent = e_out(prog(t, 8.45, 8.7))
    h = lerp(300, 1250, ent) * punch(t, 0.07) * (1 + 0.2 * hit_env(t, HIT3, 0.05, 0.5))
    ph_, bi = beat_phase(t)
    dirx = [1, -1, 1, -1][bi % 4]
    diry = [1, 1, -1, -1][bi % 4]
    k = e_io(clamp(ph_ * 1.5))
    cx = W / 2 + 90 + dirx * 40 * k
    cy = 1080 + diry * 30 * k
    return S(cx, cy, h, rot=lerp(25, -5, ent) + sway(t, 3.5), iz=1.05 + 0.1 * prog(t, 8.6, 10.5))


def scene_em3(c, t):
    hv = hit_env(t, HIT3, 0.05, 0.6)
    bg_grad(c, '#1a0204', '#4a070e', '#120203')
    rays(c, t, W / 2, 1000, 20, '#7d0a12', '#3a0509', 0.3 * t + 0.6 * e_out(prog(t, HIT3, HIT3 + 0.5)))
    c.save(); c.translate(W / 2, 1000); c.rotate(-20 + 3 * math.sin(t))
    for yo, hgt in [(-820, 110), (600, 150)]:
        c.drawRect(skia.Rect(-1500, yo, 1500, yo + hgt), P('#050102'))
        pp = P('#ffcf6b', 0.9, stroke=5)
        pp.setPathEffect(skia.DashPathEffect.Make([70, 40], -t * 320))
        c.drawLine(-1500, yo + 16, 1500, yo + 16, pp)
        c.drawLine(-1500, yo + hgt - 16, 1500, yo + hgt - 16, pp)
    c.restore()
    c.save()
    dx, dy, rr = shake(t, [E3[0], E3[2], HIT3], 24, 0.32)
    cam(c, 1.0 + 0.05 * hv, dx=dx, dy=dy, rot=rr * 20 + 2.5 * math.sin(t * 2.2))
    # RGB echo copies of the whole photo on the beat (the photo itself is untouched)
    eb = 0.6 * beat_pulse(t, 9) + 0.9 * hv
    if eb > 0.02:
        s = em3_state(t)
        for col, ox in (('#ff1a3c', -28), ('#19e3ff', 28)):
            ph('eminem').draw(c, cx=s['cx'] + ox * eb, cy=s['cy'], h=s['h'] * (1 + 0.02 * eb), rot=s['rot'],
                              alpha=0.55 * clamp(eb), iz=s['iz'], shadow=False, border=False, ghost=col)
    card(c, 'eminem', em3_state, t)
    c.restore()
    # CONTROVERSY runs vertically up the left edge, glitching in
    c.save()
    c.translate(150 + 10 * math.sin(t * 20) * hv, 1100); c.rotate(-90)
    c.scale(1 + 0.1 * hv, 1 + 0.1 * hv)
    if t > HIT3:
        c.drawRect(skia.Rect(-1000, -330, 1000, -60), P('#050102', 0.8 * e_out(prog(t, HIT3, HIT3 + 0.1))))
    L3_BIG.draw(c, t)
    c.restore()
    L3_TOP.draw(c, t)
    frame_lines(c, t, 1)
    c.drawRect(skia.Rect(0, 0, W, H), P('#ff1a3c', 0.25 * hit_env(t, HIT3, 0.02, 0.25), blend=ADD))


# ============================================================== EMINEM L4 10.55 - 12.58
E4 = [wt('eminem', 3, k) for k in range(7)]
ME4 = E4[6]
L4_TOP = Block([[Word('’CAUSE', E4[0], 'white', 'drop', 0.8), Word('IT', E4[1], 'white', 'drop', 0.8),
                 Word('FEELS', E4[2], 'white', 'drop', 0.8), Word('SO', E4[3], 'white', 'drop', 0.8)]],
               y_top=170, size=120)
L4_EMPTY = Block([[Word('EMPTY', E4[4], 'hollow', 'zoom', 1.0, exit_kind='drift')]], y_top=520, size=310,
                 max_w=1040)
L4_WM = Block([[Word('WITHOUT', E4[5], 'gold', 'slam', 1.0, glow=('#ffb347', 0.8), depth=18)],
               [Word('ME', ME4, 'gold', 'slam', 1.6, glow=('#ffcf6b', 1.0), depth=24)]],
              y_top=1330, size=200)


def em4_state(t):
    small = lerp(1.0, 0.82, e_out(prog(t, 10.55, E4[5])))
    big = e_out(prog(t, ME4 - 0.02, ME4 + 0.12))
    h = lerp(700 * small, 1500, big) * punch(t, 0.04) * (1 + 0.1 * hit_env(t, E4[5]))
    cy = lerp(1060, 980, big) + 14 * math.sin(t * 2)
    return S(W / 2, cy, h, rot=lerp(-3, 0, big) + 1.2 * math.sin(t * 1.3),
             alpha=lerp(0.85, 1, big), iz=1.0)


def scene_em4(c, t):
    big = e_out(prog(t, ME4 - 0.02, ME4 + 0.12))
    bg_grad(c, '#020001', '#0c0206', '#020001')
    glow_spot(c, W / 2, 1000, 800 + 300 * big, '#3a0a12', 0.7 + 0.3 * big)
    spot_beam(c, W / 2, -80, W / 2, 1750, 30, 360 + 200 * big, '#fff0c8', 0.22 + 0.3 * big)
    DUSTV.draw(c, t, t * 70, alpha=0.6, cy=1000, color='#ffe2a0', twinkle=True)
    c.save()
    dx, dy, rr = shake(t, [E4[5], ME4], 24)
    cam(c, 1.0, dx=dx, dy=dy, rot=rr * 15)
    L4_EMPTY.draw(c, t)
    card(c, 'eminem', em4_state, t)
    shockwave(c, W / 2, 1000, (t - ME4) / 0.7, 1200, width=44)
    c.restore()
    L4_TOP.draw(c, t, exit_t=E4[5], exit_kind='up')
    L4_WM.draw(c, t)
    frame_lines(c, t, 1)
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffffff', 0.9 * (1 - prog(t, 10.52, 10.72))))
    c.drawRect(skia.Rect(0, 0, W, H), P('#fff0c8', 0.35 * hit_env(t, ME4, 0.02, 0.25), blend=ADD))


DUSTV = Dust(80, 8, depth=(300, 2500))

# ============================================================== FINALE 12.58 - 15.0
FIN = 12.58
DUSTF = Dust(200, 12)
TITLE_TOP = Block([[Word('TOLY', FIN + 0.30, 'white', 'drop', 1.0), Word('SUMMER', FIN + 0.40, 'white', 'drop', 1.0)]],
                  y_top=170, size=150)
TITLE_X = Block([[Word('×', FIN + 0.70, 'gold', 'zoom', 1.0, glow=('#ffcf6b', 0.9))]], y_top=360, size=150)
TITLE_BOT = Block([[Word('EMINEM', FIN + 0.90, 'gold', 'slam', 1.0, glow=('#ffcf6b', 0.8), depth=20)]],
                  y_top=1530, size=260)


def fin_state(side, t):
    ent = e_back(prog(t, FIN + (0 if side < 0 else 0.12), FIN + 0.5 + (0 if side < 0 else 0.12)), 1.3)
    drift = prog(t, FIN, 15.0)
    h = 780 * (1 + 0.05 * drift)
    x = W / 2 + side * lerp(900, 262, ent) + side * 10 * math.sin(t * 1.4)
    y = 1030 + side * 50 + side * -20 * drift
    return S(x, y, h, rot=side * lerp(25, 6, ent) - side * 1.5 * drift, iz=1.0 + 0.04 * drift)


def scene_finale(c, t):
    lt = t - FIN
    bg_grad(c, '#0a0103', '#3a0a12', '#0a0103')
    rays(c, t, W / 2, 1000, 28, '#4a0c16', '#22050b', t * 0.2)
    glow_spot(c, W / 2, 1000, 950, '#ffb347', 0.22)
    light_lines(c, t, -30, 20, 0.45, seed=13)
    ring3d(c, W / 2, 1000, 650, 0.15 + 0.15 * math.sin(t), t * 0.3, 1.0, width=6)
    ring3d(c, W / 2, 1000, 760, 1.15, -t * 0.4, 0.7, dash=[30, 20], t=t, width=3)
    tri_outline(c, W / 2, 1010, 900, -1.57 + t * 0.1, 0.4)
    c.save()
    dx, dy, rr = shake(t, [FIN], 26, 0.5)
    cam(c, lerp(1.12, 1.0, e_out(prog(t, FIN, FIN + 0.6))) + 0.04 * prog(t, FIN + 0.6, 15), dx=dx, dy=dy, rot=rr * 20)
    card(c, 'toly', lambda tt: fin_state(-1, tt), t)
    card(c, 'eminem', lambda tt: fin_state(1, tt), t)
    DUSTF.draw(c, t, lt * 300, alpha=0.9, cy=1000, streak=0.8 * (1 - prog(t, FIN, FIN + 0.8)))
    shockwave(c, W / 2, 1000, lt / 0.9, 1300, width=50)
    c.restore()
    TITLE_TOP.draw(c, t)
    TITLE_X.draw(c, t)
    TITLE_BOT.draw(c, t)
    frame_lines(c, t, 1)
    c.drawRect(skia.Rect(0, 0, W, H), P('#fff3d0', 0.95 * (1 - prog(t, FIN, FIN + 0.3))))
    ir = prog(t, 14.25, 14.9)
    if ir > 0:
        r = lerp(1400, 0, e_in(ir))
        pth = skia.Path(); pth.addRect(skia.Rect(-10, -10, W + 10, H + 10)); pth.addCircle(W / 2, 1000, max(r, 0.1))
        pth.setFillType(skia.PathFillType.kEvenOdd)
        c.drawPath(pth, P('#000000'))
        if r > 1:
            c.drawCircle(W / 2, 1000, r, P('#ffcf6b', 0.9, stroke=8))
            c.drawCircle(W / 2, 1000, r, P('#ffcf6b', 0.5, stroke=26, blur=14, blend=ADD))
    if t >= 14.9:
        c.clear(C('#000000'))


# ============================================================== transitions + frame
def snapshot(fn, t):
    s = skia.Surface(W, H)
    fn(s.getCanvas(), t)
    return s.makeImageSnapshot()


def trans_swap(c, t, t0=4.40, t1=4.62):
    """Toly card flies out up-left while the Eminem stage comes in, gold light wipe between."""
    p = prog(t, t0, t1)
    scene_em1(c, t)
    a = snapshot(scene_toly, t)
    pa = skia.Paint(); pa.setAlphaf(1 - e_in(p))
    c.save(); c.translate(-W * 0.15 * e_in(p), -H * 0.08 * e_in(p))
    c.drawImage(a, 0, 0, SAMP, pa)
    c.restore()
    x = lerp(-200, W + 200, e_io(p))
    c.save(); c.translate(x, H / 2); c.rotate(20)
    c.drawRect(skia.Rect(-60, -1600, 60, 1600), P('#ffcf6b', 0.8 * math.sin(p * math.pi), blur=40, blend=ADD))
    c.drawRect(skia.Rect(-6, -1600, 6, 1600), P('#fff6d8', math.sin(p * math.pi)))
    c.restore()


def trans_push(c, t, fa, fb, t0, t1):
    """Whole-frame push-through: old frame scales toward the camera and fades, new frame
    rises from behind, red light bar sweeps across. Photos are never sliced."""
    p = prog(t, t0, t1)
    ia, ib = snapshot(fa, t), snapshot(fb, t)
    e = e_io(p)
    c.save(); cam(c, lerp(0.85, 1.0, e)); pb = skia.Paint(); pb.setAlphaf(clamp(p * 2)); c.drawImage(ib, 0, 0, SAMP, pb); c.restore()
    c.save(); cam(c, lerp(1.0, 1.6, e_in(p)), rot=-6 * e_in(p)); pa = skia.Paint(); pa.setAlphaf(1 - e_in(p))
    c.drawImage(ia, 0, 0, SAMP, pa); c.restore()
    c.save(); c.translate(W / 2, lerp(-300, H + 300, e)); c.rotate(-12)
    c.drawRect(skia.Rect(-1400, -90, 1400, 90), P('#ff1a3c', 0.7 * math.sin(p * math.pi), blur=50, blend=ADD))
    c.drawRect(skia.Rect(-1400, -5, 1400, 5), P('#fff6d8', math.sin(p * math.pi)))
    c.restore()


def render(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(C('#000000'))
    if t < 2.05:
        scene_intro(c, t)
    elif t < 4.40:
        scene_toly(c, t)
    elif t < 4.62:
        trans_swap(c, t)
    elif t < 6.52:
        scene_em1(c, t)
    elif t < 8.45:
        scene_em2(c, t)
    elif t < 8.62:
        trans_push(c, t, scene_em2, scene_em3, 8.45, 8.62)
    elif t < 10.55:
        scene_em3(c, t)
    elif t < FIN:
        scene_em4(c, t)
    else:
        scene_finale(c, t)
    if 2.05 < t < FIN:
        c.drawRect(skia.Rect(0, 0, W, H), P('#ff9a3a', 0.04 * kick_at(t), blend=ADD))
    vignette(c, 0.65)
    grain(c, t, 0.06)
    return surf
