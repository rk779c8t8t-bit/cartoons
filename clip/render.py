"""EMINEM x TOLY SUMMER -- animated music clip renderer.

Timeline is written in *audio time* `a` (seconds of the source track).
Video time t = a + PRE.  Beat grid: 114.5 BPM, B(k) = 0.03 + 0.5242 k
  0.00-0.55  intro swoop          | -1.0-0.55 INTRO: gold dust, distant silhouette
  0.55-2.39  Toly Summer's hook   | TOLY: spotlight snaps, line-drawn figure -> portrait
  2.39-2.65  pre-drop             | shatter -> shards become gold rings -> tunnel
  2.65-4.75  drop, bar 1          | EMINEM: city, figure built from gold lines, snap zooms
  4.75-6.85  bar 2                | close-ups, whip pan, slash transition
  6.85-7.89  bar 3 (first half)   | FACE-OFF: both figures, orbiting camera, portal ring
  7.89-8.94  bar 3 (second half)  | COIN: two sides of one coin
  8.94-9.99  stop-time build      | two medallions, freezes on the breaks
  9.99       final hit            | FINAL emblem, shockwave, titles; reverb tail to 12.8
"""
import sys, os, math, argparse, subprocess
import numpy as np, cv2
import skia
from scipy.io import wavfile
from engine import *
from world import *

ap = argparse.ArgumentParser()
ap.add_argument('--assets'); ap.add_argument('--fonts'); ap.add_argument('--audio')
ap.add_argument('--start', type=int, default=0); ap.add_argument('--end', type=int, default=-1)
ap.add_argument('--out'); ap.add_argument('--png', default='')
ap.add_argument('--frames', default='')
args = ap.parse_args()

PRE, A_END = 1.0, 12.8
NF = int(round((PRE + A_END) * FPS))
BP = 0.5242
def B(k): return 0.03 + BP * k
DROP = B(5); FINAL = B(19)
BEATS = [B(k) for k in range(0, 20)]

# ------------------------------------------------------------------ assets
A = args.assets; F = args.fonts
PT = {n: Portrait(f'{A}/{n}.npz', f'{A}/{n}_paths.pkl') for n in ['toly_a', 'toly_c', 'em_a', 'em_b', 'em_d']}
SHARDS = Shards(PT['toly_a'])
CITY = City()
PART = Particles(650, 1)
SMOKE = Smoke()
UNB = lambda s: Type(f'{F}/unbounded-900.ttf', s)
T_TOLY = UNB(176); T_SUMMER = UNB(112); T_EM_BIG = UNB(420); T_EM_T = UNB(150); T_TS_T = UNB(92)
T_CAP = Type(f'{F}/oswald-300.ttf', 46); T_CAP2 = Type(f'{F}/oswald-300.ttf', 34)
T_LBL = Type(f'{F}/oswald-700.ttf', 44); T_DET = Type(f'{F}/oswald-700.ttf', 64); T_RIM = Type(f'{F}/oswald-700.ttf', 30)
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone)

# audio envelope (for subtle audio-reactive glow)
sr, aud = wavfile.read(args.audio)
aud = aud.astype(np.float32).mean(1) / 32768
hop = sr // FPS
aud = np.concatenate([aud, np.zeros(hop * 4, np.float32)])
ENV = np.array([np.sqrt((aud[i * hop:(i + 1) * hop] ** 2).mean() + 1e-9) for i in range(NF + 2)])
ENV = np.convolve(ENV, np.ones(3) / 3, 'same'); ENV /= ENV.max()

# ambient time with freezes on the stop-time breaks
FREEZES = [(9.37, 9.466), (9.645, 9.728)]
_g = np.arange(-1.5, 13.5, 0.001)
_sp = np.ones_like(_g)
for f0, f1 in FREEZES:
    _sp[(_g >= f0) & (_g < f1)] = 0.0
_tw = np.cumsum(_sp) * 0.001
def TW(a): return float(np.interp(a, _g, _tw))
def frozen(a): return any(f0 <= a < f1 for f0, f1 in FREEZES)

# ------------------------------------------------------------------ helpers
def bg_fill(canvas, top, mid, bot, my=0.5):
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)], [col(top), col(mid), col(bot)], [0, my, 1])
    canvas.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))

def glow_spot(ctx, x, y, r, color, a, main=True, g=0.12):
    a *= 0.45
    if a <= 0.005: return
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 1), [col(color, 1), col(color, 0.45), col(color, 0.12), col(color, 0)], [0, 0.25, 0.6, 1])
    p = skia.Paint(Shader=sh, BlendMode=SCREEN); p.setAlphaf(cl(a))
    if main: ctx.c.drawCircle(x, y, r, p)
    if g > 0:
        p2 = skia.Paint(Shader=sh); p2.setAlphaf(cl(a * g)); ctx.g.drawCircle(x, y, r, p2)

def cone(ctx, cam, apex, base, rr, a, color=(255, 210, 140)):
    if a <= 0.01: return
    ax, ay, az = cam.proj(*apex)
    lx, ly, lz = cam.proj(base[0] - rr, base[1], base[2])
    rx_, ry_, rz = cam.proj(base[0] + rr, base[1], base[2])
    bx, by, _ = cam.proj(*base)
    if min(az, lz, rz) < 20: return
    p = skia.Path(); p.moveTo(ax, ay); p.lineTo(lx, ly); p.lineTo(rx_, ry_); p.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(ax, ay), skia.Point(bx, by)], [col(color, 0.0), col(color, 0.28), col(color, 0.55)], [0, 0.6, 1])
    pp = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=PLUS); pp.setAlphaf(cl(a))
    pp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    ctx.c.drawPath(p, pp)
    pg = skia.Paint(AntiAlias=True, Shader=sh); pg.setAlphaf(cl(a * 0.35)); ctx.g.drawPath(p, pg)

def ring(ctx, sc, r, w, a, color=GOLD, glow=1.0, prog=1.0, start=-90.0, dash=None, phase=0.0):
    if a <= 0.004: return
    p = skia.Path(); p.addArc(skia.Rect(-r, -r, r, r), start, 359.9)
    if dash:
        eff = skia.DashPathEffect.Make([dash[0], dash[1]], phase)
        ctx.c.drawPath(p, paint(color, a, stroke=w / max(sc, 1e-4), effect=eff))
        if glow: ctx.g.drawPath(p, paint(color, a * glow, stroke=w * 2.5 / max(sc, 1e-4), effect=eff))
    else:
        gold_stroke(ctx, p, w, a=a, glow=glow, prog=prog, sc=sc, color=color)

def floor_rings(ctx, sc, radii, a, color=GOLD):
    for i, r in enumerate(radii):
        ring(ctx, sc, r, 1.6, a * (1 - i / (len(radii) + 1)), color=color, glow=0.5)

def particles(ctx, cam, a, bright=1.0, **kw):
    e = ENV[min(int((a + PRE) * FPS), len(ENV) - 1)]
    PART.draw(ctx, cam, TW(a), bright * (0.75 + 0.5 * e), **kw)

def shake(a, times, amp, dec=0.18, f=70):
    s = pulses(a, times, dec)
    return (wobble(a, f, 1.3) * amp * s, wobble(a, f * 1.1, 4.1) * amp * s)

# ================================================================== SHOT 1 : INTRO + TOLY
STARS1 = [(-230, -1010, -60, 1), (250, -930, 40, 2), (-280, -700, 120, 3), (210, -640, -90, 2.5), (60, -1120, 150, 3.5), (-120, -1180, 60, 1.5), (300, -800, -120, 3)]

def cam1(a):
    # dolly from far away into Toly's portrait, then fly through it
    if a < 0.0:
        d = lerp(5600, 4000, eio(seg(a, -1.0, 0.0)))
    elif a < B(1):
        d = lerp(4000, 2500, seg(a, 0.0, B(1)) ** 1.6)
    elif a < B(2):
        d = lerp(2500, 1750, eoc(seg(a, B(1), B(2))))
    elif a < 2.39:
        d = lerp(1750, 400, eio(seg(a, B(2), B(2) + 0.36)))
        d = lerp(d, 330, seg(a, B(2) + 0.36, 2.39))
    else:
        d = lerp(330, -2600, eie(seg(a, 2.39, DROP)))
    py = lerp(-450, -520, seg(a, -1.0, B(2)))
    py = lerp(py, -813, eio(seg(a, B(2), B(2) + 0.36)))
    yaw = lerp(0.07, 0.0, seg(a, -1.0, B(2))) + lerp(0.0, 0.16, eio(seg(a, B(2), 2.39))) - 0.08 * seg(a, B(2), B(2) + 0.2)
    sy = lerp(0, 250, eio(seg(a, B(2), B(2) + 0.36)))
    sy = lerp(sy, 0, eio(seg(a, 2.39, DROP)))
    roll = 0.012 * wobble(a, 0.9) + 0.03 * pulse(a, B(1), 0.3)
    sh = shake(a, [B(1)], 6)
    return Cam.orbit((0, py, 0), d, yaw, 0.02, roll, shift=(sh[0], sy + sh[1])), d

def shot_stage(ctx, a):
    c = ctx.c
    cam, dist = cam1(a)
    on = seg(a, B(1) - 0.02, B(1) + 0.03)          # spotlight snap
    lift = 0.35 + 0.65 * on
    bg_fill(c, (6, 2, 3), lerp_col((14, 3, 6), (44, 7, 14), on), (8, 2, 4), 0.55)
    tw = TW(a)
    # far haze glow behind the singer
    hx, hy, hz = cam.proj(0, -650, 2500)
    glow_spot(ctx, hx, hy, min(1400 * 1100 / max(hz, 300), 1100), (150, 28, 40), 0.5 * lift, g=0.0)
    SMOKE.draw(c, tw, 0.10 + 0.12 * on, which=(1,))
    # gyroscope rings behind (Toly's 'stage' world)
    for k in range(6):
        appear = ss(B(1) + k * 0.05, B(1) + k * 0.05 + 0.25, a)
        if appear <= 0: continue
        bump = pulses(a, [B(2), B(3), B(4)], 0.22)
        rr = 230 + k * 150
        rot = (0.35 * math.sin(tw * 0.5 + k), 0.45 * math.cos(tw * 0.4 + k * 1.7), 0)
        def fr(cx, sc, rr=rr, k=k):
            ring(cx, sc, rr * (1 + 0.04 * bump), 2.2 + 1.5 * bump, appear * (0.55 + 0.35 * bump), glow=0.9)
            ring(cx, sc, rr + 14, 1.0, appear * 0.35, dash=(18, 26), phase=tw * 40 * (1 if k % 2 else -1), glow=0.4)
        draw_plane(ctx, cam, (0, -640, 700 + k * 40), fr, rot=rot)
    # floor
    def ffl(cx, sc):
        sh_ = skia.GradientShader.MakeRadial(skia.Point(0, 0), 700, [col((255, 190, 110), 0.55), col((200, 60, 50), 0.18), col((0, 0, 0), 0)], [0, 0.45, 1])
        p = skia.Paint(Shader=sh_, BlendMode=PLUS); p.setAlphaf(cl(0.15 + 0.85 * on)); cx.c.drawCircle(0, 0, 700, p)
        floor_rings(cx, sc, [300, 520, 800, 1150], 0.25 + 0.5 * on)
    draw_plane(ctx, cam, (0, 0, 0), ffl, rot=(0, math.pi / 2, 0), ext=300)
    # horizon line
    hp = eoe(seg(a, -0.7, 0.2))
    if hp > 0:
        L = skia.Path(); L.moveTo(-6000 * hp, 0); L.lineTo(6000 * hp, 0)
        draw_plane(ctx, cam, (0, 0, 3200), lambda cx, sc: gold_stroke(cx, L, 1.6, a=0.7, glow=1.0, sc=sc), ext=500)
    # swoop ring (rises with the pitch glide)
    sw = seg(a, 0.0, B(1) + 0.25)
    if 0 < sw < 1:
        rr = lerp(60, 900, eoe(sw)); yy = lerp(-20, -520, eoc(sw))
        draw_plane(ctx, cam, (0, yy, 0), lambda cx, sc: ring(cx, sc, rr, 3.0, math.sin(sw * math.pi) * 0.9, glow=1.2), rot=(0, math.pi / 2, 0), ext=300)
    # spotlight cone
    flick = 0.12 + 0.05 * math.sin(a * 37) * (1 - on)
    cone(ctx, cam, (0, -2600, -150), (0, 0, 0), 300, (flick + 0.5 * on * (1 + 0.25 * pulses(a, [B(2), B(3), B(4)], 0.2))) * ss(450, 1600, dist))
    # figure
    fig_a = 1 - seg(a, B(2) + 0.2, B(2) + 0.42)
    pose = pose_mix('toly', 'sing', 'singo', eob(seg(a, B(3), B(3) + 0.18)))
    bob = 10 * pulses(a, [B(2), B(3), B(4)], 0.12) * on
    if fig_a > 0 or a < B(2) + 0.6:
        def ffig(cx, sc):
            sil = draw_figure(cx, 'toly', pose, sc, fill_a=1.0, line_p=1.0, line_a=lerp(0.32, 0.5, on) * fig_a,
                              det_a=0.6 * on, glow=0.6, bob=bob, sway=6 * wobble(a, 1.5), t=tw, tilt=3 * wobble(a, 2))
            if a >= B(1):
                gold_stroke(cx, sil, 3.2, a=fig_a, glow=1.4, prog=eoe(seg(a, B(1), B(1) + 0.4)), sc=sc, color=GOLD_L)
        draw_plane(ctx, cam, (0, 0, 0), ffig)
    # portrait emerges from darkness inside the silhouette
    if a > B(2) - 0.1 and a < 2.41:
        P = PT['toly_a']
        r = eoc(seg(a, B(2) + 0.05, B(2) + 0.5))
        lp = eoe(seg(a, B(2) - 0.05, B(2) + 0.45))
        la = 1.0 - 0.7 * seg(a, B(2) + 0.45, B(3) + 0.3) + 0.4 * pulses(a, [B(3), B(4)], 0.15)
        br = 1 + 0.015 * math.sin(tw * 2.0)
        draw_plane(ctx, cam, (0, -813, -8), lambda cx, sc: P.draw(cx, 330 * br, sc, reveal=r, rim=0.9 + 0.6 * pulses(a, [B(3), B(4)], 0.2), lines=lp, line_a=la))
    # shatter -> ring
    if a >= 2.39:
        te = seg(a, 2.39, 2.58); tr = seg(a, 2.50, DROP)
        draw_plane(ctx, cam, (0, -813, -8), lambda cx, sc: SHARDS.draw(cx, 330, sc, te, tr, ring_r=150, spin=tr * 1.5))
        for k in range(1, 16):
            ra = ss(2.48 + k * 0.008, 2.56 + k * 0.008, a)
            z = k * 260
            draw_plane(ctx, cam, (0, -813, z), lambda cx, sc, k=k: (ring(cx, sc, 150 + 24 * (k % 3), 3.0, ra * 0.9, glow=1.3),
                                                                     ring(cx, sc, 200 + 24 * (k % 3), 1.2, ra * 0.5, dash=(10, 16), phase=k * 9, glow=0.6)))
    # sparkles
    if a > B(1):
        for i, (x, y, z, ph) in enumerate(STARS1):
            tb = BEATS[1 + i % 4] + 0.06 * i
            tw_ = pulse(a, tb, 0.35) * (a >= tb) + 0.25 * (0.5 + 0.5 * math.sin(tw * 3 + ph))
            X, Y, Z = cam.proj(x, y, z)
            if Z > 50 and a < 2.45:
                draw_star(ctx, X, Y, 26 * 1100 / Z * 2.2 * tw_, cl(tw_ * 1.2), 0)
    particles(ctx, cam, a, bright=0.5 + 0.6 * on + 0.8 * seg(a, 2.39, DROP), focus=max(dist, 300))
    # intro caption
    cp = lambda i: seg(a, -0.8 + i * 0.05, -0.45 + i * 0.05)
    ca = 1 - seg(a, 0.25, 0.5)
    if ca > 0 and a < 0.55:
        trk = 0.55 + 0.25 * seg(a, -0.8, 0.5)
        T_CAP.draw(ctx, 'ДВА МИРА', W / 2, 1420, cp, tracking=trk, depth=0, fill='solid', color=GOLD_L, a=ca, glow=0.5, rise=0.2)
        L = skia.Path(); w_ = 300 * eoe(seg(a, -0.5, 0.1)); L.moveTo(W / 2 - w_, 1460); L.lineTo(W / 2 + w_, 1460)
        gold_stroke(ctx, L, 1.4, a=0.8 * ca, glow=1.0)
    # TOLY SUMMER title
    if a > B(3) - 0.05:
        ex = eie(seg(a, 2.39, 2.62))
        ctx.save(); ctx.translate(W / 2, 400); ctx.scale(1 + 2.4 * ex); ctx.translate(-W / 2, -400)
        ta = 1 - ex
        T_TOLY.draw(ctx, 'TOLY', W / 2, 360, lambda i: seg(a, B(3) + i * 0.05, B(3) + 0.25 + i * 0.05), a=ta, slam=0.35, glow=0.25)
        T_SUMMER.draw(ctx, 'SUMMER', W / 2, 500, lambda i: seg(a, B(3) + 0.26 + i * 0.04, B(3) + 0.5 + i * 0.04), a=ta, slam=0.3, glow=0.2)
        swoosh(ctx, W / 2, 400, 420, 150, -7, eoe(seg(a, B(3) + 0.3, B(4) + 0.1)), a=0.9 * ta, w=3.2)
        ctx.restore()

def lerp_col(c0, c1, t):
    return tuple(int(lerp(c0[i], c1[i], t)) for i in range(3))

# ================================================================== SHOT 2 : EMINEM / CITY
SNAPS = [B(6), B(7), B(8)]
def cam2(a):
    d = lerp(3900, 2750, eoe(seg(a, DROP, DROP + 0.45)))
    for t0, amt in zip(SNAPS, (520, 470, 430)):
        d -= amt * eoe(seg(a, t0, t0 + 0.22))
    d -= 80 * seg(a, DROP, B(9))
    d -= 1750 * eie(seg(a, B(9) - 0.14, B(9)))        # rush into the face -> match cut
    py = -560 - 60 * sum(eoe(seg(a, t, t + 0.22)) for t in SNAPS) - 60 * eie(seg(a, B(9) - 0.14, B(9)))
    yaw = -0.11 + 0.2 * eio(seg(a, DROP, B(9)))
    roll = 0.04 * pulse(a, B(6), 0.3) - 0.04 * pulse(a, B(7), 0.3) + 0.03 * pulse(a, B(8), 0.3) + 0.008 * wobble(a, 1.3)
    sh = shake(a, [DROP] + SNAPS, 9, 0.16)
    return Cam.orbit((0, py, 0), d, yaw, -0.075, roll, shift=sh), d

EM_LET = [B(6) + i * BP / 2 for i in range(6)]

def shot_city(ctx, a):
    c = ctx.c
    cam, dist = cam2(a)
    tw = TW(a)
    beat = pulses(a, BEATS[5:10], 0.16)
    # sky
    hx, hy, _ = cam.proj(0, 0, cam.z + 60000)
    sh = skia.GradientShader.MakeLinear([skia.Point(0, hy - 1500), skia.Point(0, hy + 400)],
                                        [col((10, 2, 5)), col((120, 20, 26)), col((14, 3, 6))], [0, 1500 / 1900, 1])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    # sun disc
    def fsun(cx, sc):
        g = skia.GradientShader.MakeRadial(skia.Point(0, 0), 3000, [col((236, 132, 76)), col((170, 40, 34)), col((90, 12, 20), 0.0)], [0, 0.55, 1])
        cx.c.drawCircle(0, 0, 3000, skia.Paint(Shader=g, AntiAlias=True))
        for k in range(7):  # retro bands
            yy = 600 + k * 330
            hgt = 40 + k * 26
            cx.c.drawRect(skia.Rect(-3200, yy, 3200, yy + hgt), paint((60, 10, 16), 0.9))
        ring(cx, sc, 3000, 3, 0.8, glow=1.2)
        ring(cx, sc, 3400, 1.5, 0.45, dash=(60, 90), phase=tw * 200, glow=0.5)
    draw_plane(ctx, cam, (0, -3100, 6400), fsun, ext=800)
    SMOKE.draw(c, tw, 0.35, which=(0, 1), drift=(60, -18))
    CITY.draw(ctx, cam, flick=beat)
    # rooftop floor with perspective grid
    def ffl(cx, sc):
        cx.c.drawRect(skia.Rect(-6000, -400, 6000, 4000), paint((10, 3, 5)))
        g = skia.Path()
        for x in range(-3000, 3001, 300):
            g.moveTo(x, -350); g.lineTo(x * 1.0, 3800)
        for z in range(-300, 3800, 300):
            g.moveTo(-3000, z); g.lineTo(3000, z)
        cx.c.drawPath(g, paint(GOLD, 0.16, stroke=1.4 / max(sc, 1e-3)))
        e = skia.Path(); e.moveTo(-6000, -350); e.lineTo(6000, -350)
        gold_stroke(cx, e, 2.4, a=0.85, glow=1.0, sc=sc)
        sp = skia.GradientShader.MakeRadial(skia.Point(0, 0), 600, [col((255, 150, 90), 0.45), col((0, 0, 0), 0)], [0, 1])
        cx.c.drawCircle(0, 0, 600, skia.Paint(Shader=sp, BlendMode=PLUS))
    draw_plane(ctx, cam, (0, 0, 0), ffl, rot=(0, math.pi / 2, 0), ext=250)
    # giant EMINEM letters behind him
    def flet(cx, sc):
        T_EM_BIG.draw(cx, 'EMINEM', 0, 0, lambda i: seg(a, EM_LET[i], EM_LET[i] + 0.2), a=0.95, slam=0.55, depth=9, glow=0.18, rise=0.0)
    draw_plane(ctx, cam, (0, -260, 520), flet, ext=600)
    # backlight
    bx, by, bz = cam.proj(0, -620, 60)
    glow_spot(ctx, bx, by, min(900 * 1100 / max(bz, 200), 900), (255, 110, 70), 0.3 + 0.25 * beat, g=0.1)
    # figure, built from lines
    k = 0
    seq = [(DROP, 'idle'), (B(6), 'point'), (B(7), 'rap'), (B(8), 'raise'), (B(8) + BP / 2, 'wide')]
    pa = seq[0][1]; pb = pa; tt = 0
    for i in range(len(seq) - 1, -1, -1):
        if a >= seq[i][0]:
            pb = seq[i][1]; pa = seq[i - 1][1] if i > 0 else pb; tt = eob(seg(a, seq[i][0], seq[i][0] + 0.15), 1.4); break
    pose = pose_mix('em', pa, pb, tt)
    lp = eoe(seg(a, DROP, DROP + 0.32))
    fa = ss(DROP + 0.12, DROP + 0.4, a)
    bob = 16 * beat
    def ffig(cx, sc):
        draw_figure(cx, 'em', pose, sc, fill_a=fa, line_p=lp, line_a=1.0, det_a=0.6, glow=1.0, bob=bob,
                    sway=10 * wobble(a, 1.7), tilt=5 * math.sin(a * math.pi / BP * 2) * seg(a, B(6), B(9)), t=tw)
        # construction lines
        cpr = seg(a, DROP, DROP + 0.25); cfade = 1 - seg(a, DROP + 0.25, DROP + 0.55)
        if cfade > 0:
            for (x0, y0, ang) in ((0, -838, -90), (-148, -700, 200), (148, -700, -20), (0, -405, 90), (-88, -10, 160), (88, -10, 20), (0, -600, 180), (0, -600, 0)):
                Lp = skia.Path(); Lp.moveTo(x0, y0)
                Lp.lineTo(x0 + math.cos(math.radians(ang)) * 2400, y0 + math.sin(math.radians(ang)) * 2400)
                gold_stroke(cx, Lp, 1.2, a=0.7 * cfade, glow=0.8, prog=eoe(cpr), sc=sc)
    draw_plane(ctx, cam, (0, 0, 0), ffig)
    particles(ctx, cam, a, bright=1.0 + 0.6 * beat, focus=max(dist, 400), rise=2.2)

# ================================================================== SHOT 3 : CLOSE-UPS
TOWERS = [(-1500, 2600, 700), (-900, 1500, 520), (-480, 3200, 420), (520, 2200, 560), (1100, 1300, 480), (1700, 3000, 800), (60, 4200, 900), (-2200, 4000, 900), (2400, 4200, 1000)]

def draw_towers(ctx, cam, tw, beat, tint=(22, 5, 9)):
    for (x, z, w) in sorted(TOWERS, key=lambda q: -q[1]):
        def ft(cx, sc, w=w, x=x):
            cx.c.drawRect(skia.Rect(-w / 2, -6000, w / 2, 400), paint(tint))
            e = skia.Path(); e.moveTo(-w / 2, 400); e.lineTo(-w / 2, -6000); e.moveTo(w / 2, 400); e.lineTo(w / 2, -6000)
            gold_stroke(cx, e, 1.8, a=0.55, glow=0.7, sc=sc)
            gp = skia.Path()
            for yy in range(-5800, 300, 180):
                gp.moveTo(-w / 2 + 20, yy); gp.lineTo(w / 2 - 20, yy)
            cx.c.drawPath(gp, paint((255, 170, 90), 0.10 + 0.08 * beat, stroke=10 / 1.0))
        draw_plane(ctx, cam, (x, -1500, z), ft, ext=500)

def shot_close(ctx, a, which):
    c = ctx.c
    tw = TW(a)
    if which == 'a':
        t0 = B(9)
        d = lerp(1180, 1040, eio(seg(a, t0, B(11)))) - 110 * eoe(seg(a, B(10), B(10) + 0.2))
        yaw = lerp(0.07, -0.05, eio(seg(a, t0, B(11)))); pitch = -0.2; roll = lerp(0.0, -0.05, eio(seg(a, t0, B(11))))
        name = 'em_a'; halo = (200, 50, 40); P = PT[name]
        rev = eoc(seg(a, t0, t0 + 0.3)); lp = eoe(seg(a, t0 - 0.03, t0 + 0.32)); la = 1.0 - 0.7 * seg(a, t0 + 0.3, t0 + 0.7)
    else:
        t0 = B(11)
        d = lerp(1040, 960, eio(seg(a, t0, B(13)))) - 120 * eoe(seg(a, B(12), B(12) + 0.2))
        yaw = lerp(-0.08, 0.05, eio(seg(a, t0 - 0.1, B(13)))); pitch = -0.24; roll = 0.075
        name = 'em_b'; halo = (230, 40, 34); P = PT[name]
        rev = 1.0; lp = eoe(seg(a, t0, t0 + 0.25)); la = 1.0 - 0.6 * seg(a, t0 + 0.25, t0 + 0.6) + 0.5 * pulse(a, B(12), 0.2)
    sh = shake(a, [t0, B(10), B(12)], 8, 0.14)
    cam = Cam.orbit((0, 0, 0), d, yaw, pitch, roll, shift=sh)
    beat = pulses(a, BEATS[9:14], 0.16)
    bg_fill(c, (10, 2, 4), (52, 8, 14), (14, 3, 6), 0.6)
    SMOKE.draw(c, tw, 0.32 if which == 'a' else 0.45, which=(0, 1), drift=(-30, -40))
    draw_towers(ctx, cam, tw, beat)
    # halo disc
    def fh(cx, sc):
        g = skia.GradientShader.MakeRadial(skia.Point(0, 0), 620, [col(halo, 0.9), col(halo, 0.35), col(halo, 0)], [0, 0.55, 1])
        cx.c.drawCircle(0, 0, 620, skia.Paint(Shader=g, AntiAlias=True))
        ring(cx, sc, 440, 4.0, 0.9, glow=1.2)
        ring(cx, sc, 480, 1.5, 0.6, dash=(14, 22), phase=tw * 60, glow=0.6)
        pr = seg(a, BEATS[10] if a > BEATS[10] else BEATS[9], (BEATS[10] if a > BEATS[10] else BEATS[9]) + 0.5)
        for tb in BEATS[9:14]:
            q = seg(a, tb, tb + 0.45)
            if 0 < q < 1:
                ring(cx, sc, 440 + 320 * eoe(q), 3.0 * (1 - q), (1 - q) * 0.9, glow=1.4)
    draw_plane(ctx, cam, (0, -80, 520), fh, rot=(yaw, -pitch, 0))
    # portrait (billboard)
    br = 1 + 0.01 * math.sin(tw * 2.2)
    draw_plane(ctx, cam, (0, 0, 0), lambda cx, sc: P.draw(cx, 1000 * br, sc, reveal=rev, rim=1.0 + 0.8 * beat, lines=lp, line_a=la),
               rot=(yaw, -pitch, 0))
    particles(ctx, cam, a, bright=1.0 + 0.5 * beat, focus=d, rise=2.0)
    if which == 'b':
        ctx.save(); ctx.translate(985, 960); ctx.rotate(-90)
        T_DET.draw(ctx, 'DETROIT', 0, 0, lambda i: seg(a, t0 + 0.05 + i * 0.04, t0 + 0.3 + i * 0.04), tracking=0.45, depth=3, glow=0.3)
        ctx.restore()
        L = skia.Path(); L.moveTo(1010, 600); L.lineTo(1010, 600 + 720 * eoe(seg(a, t0, t0 + 0.4)))
        gold_stroke(ctx, L, 1.5, a=0.7, glow=0.8)
    else:
        lab = lambda i: seg(a, t0 + 0.1 + i * 0.04, t0 + 0.35 + i * 0.04)
        T_CAP2.draw(ctx, 'MARSHALL MATHERS', W / 2, 1780, lab, tracking=0.5, depth=0, fill='solid', color=GOLD_L, a=0.85, glow=0.4, rise=0.3)

# ================================================================== SHOT 4 : FACE-OFF
def cam4(a):
    t0, t1 = 6.66, B(15)
    d = lerp(1900, 1520, eio(seg(a, t0, t1)))
    d = lerp(d, 120, eie(seg(a, B(15) - 0.16, B(15) + 0.04)))
    yaw = lerp(-0.4, 0.17, eio(seg(a, t0, t1)))
    py = lerp(-480, -560, eio(seg(a, t0, t1)))
    pitch = lerp(-0.06, -0.01, eio(seg(a, t0, t1)))
    sh = shake(a, [B(14)], 7)
    return Cam.orbit((0, py, 0), d, yaw, pitch, 0.012 * wobble(a, 1.1), shift=sh), d

def hand_world(kind, pose_name, base_x, side):
    p = POSES[kind][pose_name][side]
    return (base_x + p[0], p[1], 0)

def shot_faceoff(ctx, a):
    c = ctx.c
    cam, dist = cam4(a)
    tw = TW(a)
    hit = pulse(a, B(14), 0.3) * (a >= B(14))
    beat = pulses(a, [B(13), B(14), B(15)], 0.18)
    bg_fill(c, (8, 2, 4), (40, 7, 14), (10, 3, 5), 0.6)
    # Eminem's city on the right, Toly's stage beams on the left
    CITY.draw(ctx, cam, flick=beat, xclip=(-200, 1e5))
    SMOKE.draw(c, tw, 0.25, which=(0,), drift=(30, -20))
    for k, x in enumerate((-700, -1300, -1900)):
        cone(ctx, cam, (x + 500, -3000, 900), (x, 0, 300 + 250 * k), 280, 0.22 + 0.2 * beat, color=(255, 190, 150))
    def fwall(cx, sc):
        for k in range(5):
            ring(cx, sc, 200 + k * 140, 2.0, 0.4 + 0.3 * beat, glow=0.7)
    draw_plane(ctx, cam, (-1400, -900, 1800), fwall, rot=(0.0, 0.0, 0.0))
    # floor
    def ffl(cx, sc):
        g = skia.GradientShader.MakeRadial(skia.Point(0, 0), 1300, [col((255, 170, 100), 0.4), col((120, 20, 30), 0.15), col((0, 0, 0), 0)], [0, 0.5, 1])
        cx.c.drawCircle(0, 0, 1300, skia.Paint(Shader=g, BlendMode=PLUS))
        floor_rings(cx, sc, [380, 620, 900, 1250, 1650], 0.55 + 0.4 * beat)
        Lp = skia.Path(); Lp.moveTo(0, -1800); Lp.lineTo(0, 1800)
        gold_stroke(cx, Lp, 1.6, a=0.5, glow=0.6, sc=sc)
    draw_plane(ctx, cam, (0, 0, 120), ffl, rot=(0, math.pi / 2, 0), ext=300)
    # portal ring
    def fring(cx, sc):
        g = skia.GradientShader.MakeRadial(skia.Point(0, 0), 430, [col((255, 210, 140), 0.25 + 0.5 * hit), col((200, 60, 40), 0.1), col((0, 0, 0), 0)], [0, 0.7, 1])
        cx.c.drawCircle(0, 0, 430, skia.Paint(Shader=g, BlendMode=PLUS))
        ring(cx, sc, 430, 9.0, 1.0, glow=1.0 + hit)
        ring(cx, sc, 400, 2.5, 0.8, color=GOLD_L, glow=0.8)
        ring(cx, sc, 470, 3.0, 0.7, dash=(40, 30), phase=tw * 120, glow=0.8)
        ring(cx, sc, 505, 1.2, 0.5, dash=(8, 14), phase=-tw * 80, glow=0.4)
    draw_plane(ctx, cam, (0, -560, 120), fring, ext=300)
    # the two figures
    tp = pose_mix('toly', 'singR', 'up', eob(seg(a, B(14), B(14) + 0.16)))
    ep = pose_mix('em', 'pointL', 'fistL', eob(seg(a, B(14), B(14) + 0.16)))
    bob = 12 * beat
    draw_plane(ctx, cam, (-560, 0, 0), lambda cx, sc: draw_figure(cx, 'toly', tp, sc, line_a=1.0, glow=1.0, bob=bob, sway=6 * wobble(a, 1.4), t=tw), rot=(-0.28, 0, 0))
    draw_plane(ctx, cam, (560, 0, 0), lambda cx, sc: draw_figure(cx, 'em', ep, sc, line_a=1.0, glow=1.0, bob=bob, sway=8 * wobble(a, 1.6, 2), t=tw), rot=(0.28, 0, 0))
    # name plates on the floor in front of each
    for x, name, ry in ((-560, 'TOLY SUMMER', -0.28), (560, 'EMINEM', 0.28)):
        def fl(cx, sc, name=name):
            T_LBL.draw(cx, name, 0, 0, lambda i: seg(a, 6.85 + i * 0.03, 7.1 + i * 0.03), tracking=0.3, depth=0, fill='solid', color=GOLD_L, glow=0.4, rise=0.3)
        draw_plane(ctx, cam, (x, 110, -40), fl, rot=(ry, 0, 0))
    # energy arc on the strike
    if a >= B(14):
        p0 = cam.proj(-560 + POSES['toly']['up']['lh'][0], POSES['toly']['up']['lh'][1], 0)
        p1 = cam.proj(0, -560, 120)
        p2 = cam.proj(560 + POSES['em']['fistL']['lh'][0], POSES['em']['fistL']['lh'][1], 0)
        if min(p0[2], p1[2], p2[2]) > 50:
            arc = skia.Path(); arc.moveTo(p0[0], p0[1]); arc.quadTo(p1[0], p1[1] - 260, p2[0], p2[1])
            pr = eoe(seg(a, B(14), B(14) + 0.18)); fa = 1 - seg(a, B(14) + 0.25, B(15))
            gold_stroke(ctx, arc, 4.0, a=fa, glow=1.6, prog=pr, color=GOLD_L)
            gold_stroke(ctx, arc, 1.5, a=fa, glow=0.5, start=cl(pr - 0.25), prog=pr, color=(255, 255, 230))
    particles(ctx, cam, a, bright=1.0 + 0.5 * beat, focus=dist)

# ================================================================== SHOT 5 : COIN
RIM_TEXT = None
def rim_text_path():
    global RIM_TEXT
    if RIM_TEXT is not None: return RIM_TEXT
    txt = 'EMINEM  •  TOLY SUMMER  •  EMINEM  •  TOLY SUMMER  •  '
    f = T_RIM.font
    gl = f.textToGlyphs(txt); ws = f.getWidths(gl)
    tot = sum(ws); R = 352
    sc_ = 2 * math.pi * R / tot
    path = skia.Path(); x = 0
    for g, w in zip(gl, ws):
        ang = (x + w / 2) * sc_ / R - math.pi / 2
        gp = f.getPath(g)
        if gp is not None and gp.countPoints() > 0:
            m = skia.Matrix()
            m.setTranslate(-w / 2, 11)
            m.postRotate(math.degrees(ang) + 90)
            m.postTranslate(R * math.cos(ang), R * math.sin(ang))
            gp.transform(m); path.addPath(gp)
        x += w
    RIM_TEXT = path
    return path

def coin_face(cx, sc, P, tw, mirror=False, size=830, line_a=0.35):
    R = 400
    clip = skia.Path(); clip.addCircle(0, 0, R - 14)
    cx.save(); cx.clip(clip)
    g = skia.GradientShader.MakeRadial(skia.Point(0, -40), R, [col((150, 26, 30)), col((60, 8, 14)), col((22, 4, 8))], [0, 0.6, 1])
    cx.c.drawCircle(0, 0, R, skia.Paint(Shader=g))
    cx.save()
    if mirror: cx.scale(-1, 1)
    cx.translate(0, 60)
    P.draw(cx, size, sc, reveal=1.0, rim=0.7, lines=1.0, line_a=line_a, feat_a=0.8)
    cx.restore()
    band = skia.Path(); band.addCircle(0, 0, 352)
    cx.c.drawPath(band, paint((26, 4, 8), 0.92, stroke=56 / 1.0))
    cx.restore()
    cx.save(); cx.rotate(math.degrees(tw * 0.35) * (-1 if mirror else 1))
    rt = rim_text_path()
    cx.c.drawPath(rt, paint(shader=gold_shader(-380, 380), a=1.0))
    cx.g.drawPath(rt, paint(GOLD, 0.25))
    cx.restore()
    ring(cx, sc, R - 6, 12.0, 1.0, glow=1.0)
    ring(cx, sc, 380, 2.0, 0.9, color=GOLD_L, glow=0.5)
    ring(cx, sc, 324, 2.0, 0.9, color=GOLD_L, glow=0.5)

def shot_coin(ctx, a):
    c = ctx.c
    tw = TW(a)
    d = lerp(2800, 1250, eoe(seg(a, B(15) - 0.04, B(15) + 0.3))) - 110 * eoe(seg(a, B(16), B(16) + 0.2))
    yaw = lerp(0.12, -0.1, eio(seg(a, B(15), B(17)))); pitch = lerp(0.06, -0.05, eio(seg(a, B(15), B(17))))
    cam = Cam.orbit((0, 0, 0), d, yaw, pitch, 0.02 * wobble(a, 0.8), shift=shake(a, [B(15), B(16)], 6))
    beat = pulses(a, [B(15), B(16)], 0.2)
    bg_fill(c, (8, 2, 4), (46, 8, 14), (8, 2, 4), 0.5)
    X, Y, _ = cam.proj(0, 0, 0)
    draw_rays(c, X, Y, tw * 6, 0.4 + 0.2 * beat, color=(120, 16, 24), r=1700)
    SMOKE.draw(c, tw, 0.2, which=(1,))
    glow_spot(ctx, X, Y, 800, (255, 120, 70), 0.2 + 0.2 * beat)
    theta = lerp(-3 * math.pi, 0, eoe(seg(a, B(15) - 0.04, B(15) + 0.32))) + math.pi * eio(seg(a, B(16), B(16) + 0.22))
    tilt = 0.18 * math.sin(tw * 1.3)
    # thickness: stacked rims along the normal
    nx, ny, nz = rot3(0, 0, 1, theta, tilt, 0)
    camv = (cam.x, cam.y, cam.z)
    facing = (nx * (0 - camv[0]) + ny * (0 - camv[1]) + nz * (0 - camv[2])) < 0
    layers = list(range(-6, 7))
    layers.sort(key=lambda k: -(k if facing else -k))
    for k in layers:
        off = k * 4.0
        ctr = (nx * off, ny * off, nz * off)
        if k == (6 if facing else -6):
            continue
        draw_plane(ctx, cam, ctr, lambda cx, sc: cx.c.drawCircle(0, 0, 400, paint((150, 92, 30) if abs(k) < 6 else GOLD_D)), rot=(theta, tilt, 0))
    front_off = -6 * 4.0 if facing else 6 * 4.0
    ctr = (nx * -24, ny * -24, nz * -24) if facing else (nx * 24, ny * 24, nz * 24)
    showing_front = math.cos(theta) > 0
    P = PT['em_d'] if showing_front else PT['toly_c']
    draw_plane(ctx, cam, ctr, lambda cx, sc: coin_face(cx, sc, P, tw, mirror=not showing_front), rot=(theta, tilt, 0))
    # coin glint
    gl = pulses(a, [B(15) + 0.3, B(16) + 0.24], 0.25)
    draw_star(ctx, X + 260, Y - 280, 60 * gl, gl, 0)
    particles(ctx, cam, a, bright=1.1 + 0.4 * beat, focus=d)

# ================================================================== SHOT 6 : DUO + FINAL
TOP = (0, -318); BOT = (0, 362); RX, RY = 238, 292

def medallion(cx, sc, P, prog, a, tw, rim=1.0, face=0.0, line_a=0.3, size=620):
    clip = skia.Path(); clip.addOval(skia.Rect(-RX + 12, -RY + 12, RX - 12, RY - 12))
    cx.save(); cx.clip(clip)
    g = skia.GradientShader.MakeRadial(skia.Point(0, -40), RY, [col((160, 30, 32)), col((70, 10, 16)), col((20, 4, 7))], [0, 0.6, 1])
    cx.c.drawPaint(skia.Paint(Shader=g))
    cx.save(); cx.translate(0, 70 + face)
    P.draw(cx, size, sc, reveal=1.0, rim=rim, lines=1.0, line_a=line_a, a=a)
    cx.restore()
    cx.restore()
    oval_frame(cx, RX, RY, sc, prog=prog, a=a, t=tw)

def shot_final(ctx, a):
    c = ctx.c
    tw = TW(a)
    fz = frozen(a)
    # camera: slow push, anticipation pull-back before the final hit, snap on the hit
    d = lerp(1100, 1060, seg(a, B(17), 9.73)) + 50 * eio(seg(a, 9.73, FINAL)) - 45 * eoe(seg(a, FINAL, FINAL + 0.25))
    d -= 35 * eio(seg(a, FINAL + 0.25, A_END))
    yaw = 0.04 * math.sin(tw * 0.6) * (1 - 0.5 * seg(a, FINAL, A_END)); pitch = 0.02 * math.cos(tw * 0.5)
    cam = Cam.orbit((0, 20, 0), d, yaw, pitch, 0.0, shift=shake(a, [B(17), 9.466, 9.728, FINAL], 10, 0.15))
    hits = pulses(a, [9.466, 9.728], 0.18)
    fin = pulse(a, FINAL, 0.5) * (a >= FINAL)
    after = seg(a, FINAL, FINAL + 0.05)
    tail = seg(a, 10.78, A_END)
    bg_fill(c, (8, 2, 4), lerp_col((40, 7, 13), (70, 10, 18), after), (8, 2, 4), 0.5)
    X, Y, _ = cam.proj(0, 25, 0)
    ra = lerp(0.28, 0.45, after) + 0.35 * fin + 0.15 * pulse(a, 10.44, 0.3) * (a >= 10.44)
    draw_rays(c, X, Y, tw * 5 + 25 * fin * 0.3, ra * (1 - 0.5 * tail), color=(130, 18, 26), r=2000)
    SMOKE.draw(c, tw, 0.22, which=(0, 1))
    glow_spot(ctx, X, Y, 700, (255, 140, 80), 0.12 + 0.4 * fin + 0.15 * hits)
    # big outer frame (after the hit)
    if a >= FINAL:
        fp = eoe(seg(a, FINAL, FINAL + 0.7))
        def fbig(cx, sc):
            rr = skia.Path(); rr.addRRect(skia.RRect.MakeRectXY(skia.Rect(-445, -850, 445, 850), 230, 230))
            gold_stroke(cx, rr, 2.4, a=0.85, glow=0.9, prog=fp, sc=sc)
            rr2 = skia.Path(); rr2.addRRect(skia.RRect.MakeRectXY(skia.Rect(-462, -868, 462, 868), 245, 245))
            gold_stroke(cx, rr2, 1.0, a=0.55, glow=0.4, prog=fp, sc=sc, color=GOLD_L)
            if fp > 0.95:
                for (sx, sy) in ((-445, 0), (445, 0), (0, -850), (0, 850)):
                    draw_star(cx, sx, sy, 26 * (1 + 0.2 * math.sin(tw * 4 + sx)), 0.9)
        draw_plane(ctx, cam, (0, 25, 60), fbig)
    # shockwave
    q = seg(a, FINAL, FINAL + 0.7)
    if 0 < q < 1:
        def fsw(cx, sc):
            ring(cx, sc, 60 + 1500 * eoe(q), 30 * (1 - q) + 2, (1 - q) * 1.0, color=GOLD_L, glow=1.6)
            ring(cx, sc, 40 + 1100 * eoe(q * 0.9), 6 * (1 - q) + 1, (1 - q) * 0.6, glow=1.0)
        draw_plane(ctx, cam, (0, 25, -10), fsw)
    # split from the coin into two medallions
    sp = eoe(seg(a, B(17), B(17) + 0.38))
    if a < B(17) + 0.2:
        ha = 1 - seg(a, B(17), B(17) + 0.2)
        for sgn in (-1, 1):
            def fhalf(cx, sc, sgn=sgn):
                cl_ = skia.Path(); cl_.addRect(skia.Rect(-500, 0 if sgn > 0 else -500, 500, 500 if sgn > 0 else 0))
                cx.save(); cx.clip(cl_)
                coin_face(cx, sc, PT['toly_c'], tw, mirror=False)
                cx.restore()
            draw_plane(ctx, cam, (0, sgn * 260 * sp, 0), lambda cx, sc, f=fhalf: (cx.c.saveLayerAlpha(None, int(255 * ha)), cx.g.saveLayerAlpha(None, int(255 * ha)), f(cx, sc), cx.c.restore(), cx.g.restore()))
        L = skia.Path(); L.moveTo(-600, 0); L.lineTo(600, 0)
        draw_plane(ctx, cam, (0, 0, -20), lambda cx, sc: gold_stroke(cx, L, 5 * ha, a=ha, glow=2.0, sc=sc, color=GOLD_L))
    msc = lerp(0.55, 1.0, sp) * (1 + 0.05 * hits + 0.04 * fin)
    fprog = eoe(seg(a, B(17) + 0.05, B(17) + 0.5))
    for (pos, name, face) in ((TOP, 'em_a', 0), (BOT, 'toly_a', 0)):
        x, y = pos[0], pos[1] * sp
        def fm(cx, sc, name=name, face=face):
            cx.scale(msc)
            medallion(cx, sc * msc, PT[name], fprog, cl(sp * 1.5), tw, rim=1.0 + 0.8 * hits + fin, face=face,
                      line_a=0.3 + 0.5 * hits + 0.4 * fin)
        draw_plane(ctx, cam, (x, y, 0), fm)
    # connecting lines + central emblem
    lp = eoe(seg(a, 9.466, 9.466 + 0.2))
    def femb(cx, sc):
        L1 = skia.Path(); L1.moveTo(0, TOP[1] + RY); L1.lineTo(0, -80)
        L2 = skia.Path(); L2.moveTo(0, BOT[1] - RY); L2.lineTo(0, 130)
        for Lx in (L1, L2):
            gold_stroke(cx, Lx, 3.0, a=1.0, glow=1.4, prog=lp, sc=sc, color=GOLD_L)
        ep = eoe(seg(a, B(17) + 0.2, B(17) + 0.5))
        s = 1 + 0.25 * pulses(a, [9.466, 9.728], 0.15) + 0.35 * fin
        cx.save(); cx.translate(0, 25); cx.scale(s)
        cx.c.drawCircle(0, 0, 78, paint((26, 4, 8), ep))
        ring(cx, sc * s, 78, 4.0, ep, glow=1.2, prog=ep)
        ring(cx, sc * s, 94, 1.4, ep * 0.8, color=GOLD_L, glow=0.6, prog=ep)
        X1 = skia.Path(); X1.moveTo(-34, -34); X1.lineTo(34, 34)
        X2 = skia.Path(); X2.moveTo(34, -34); X2.lineTo(-34, 34)
        xp = eoe(seg(a, B(17) + 0.3, B(17) + 0.55))
        gold_stroke(cx, X1, 9, a=1.0, glow=1.6, prog=xp, sc=sc * s, color=GOLD_L)
        gold_stroke(cx, X2, 9, a=1.0, glow=1.6, prog=xp, sc=sc * s, color=GOLD_L)
        cx.restore()
    draw_plane(ctx, cam, (0, 0, -30), femb)
    # particles: converge on the stop-time hit, burst on the final
    vort = eie(seg(a, 9.728, FINAL)) * (a < FINAL)
    burst = eoe(seg(a, FINAL, FINAL + 0.9)) * (1 - seg(a, FINAL + 0.9, 12.0))
    X0, Y0, _ = cam.proj(0, 25, 0)
    particles(ctx, cam, a, bright=1.0 + 1.2 * fin + 0.6 * hits, focus=d, vortex=vort, vc=(X0, Y0), burst=burst)
    # titles
    if a >= FINAL - 0.01:
        ttl = lambda i: seg(a, FINAL + i * 0.035, FINAL + 0.22 + i * 0.035)
        T_EM_T.draw(ctx, 'EMINEM', W / 2, 238, ttl, slam=0.7, glow=0.22, depth=8)
        tt2 = lambda i: seg(a, FINAL + 0.12 + i * 0.03, FINAL + 0.32 + i * 0.03)
        T_TS_T.draw(ctx, 'TOLY SUMMER', W / 2, 1768, tt2, slam=0.7, glow=0.22, depth=6)
        swoosh(ctx, W / 2, 186, 430, 110, -5, eoe(seg(a, FINAL + 0.15, FINAL + 0.55)), a=0.9, w=3)
        swoosh(ctx, W / 2, 1732, 500, 86, 4, eoe(seg(a, FINAL + 0.25, FINAL + 0.65)), a=0.9, w=3)
        cap = lambda i: seg(a, 10.44 + i * 0.03, 10.7 + i * 0.03)
        T_CAP2.draw(ctx, 'ДВА МИРА  ·  ОДИН БИТ', W / 2, 1838, cap, tracking=0.45, depth=0, fill='solid', color=GOLD_L, a=0.85, glow=0.4, rise=0.3)
    # glint sweep on the second hit
    gs = seg(a, 10.44, 10.95)
    if 0 < gs < 1:
        xg = lerp(-500, W + 500, eio(gs))
        p = skia.Path(); p.moveTo(xg - 60, 0); p.lineTo(xg + 60, 0); p.lineTo(xg - 340, H); p.lineTo(xg - 460, H); p.close()
        c.drawPath(p, paint((255, 220, 160), 0.16 * math.sin(gs * math.pi), blur=30, blend=PLUS))
    # last glint
    lg = math.exp(-((a - 12.05) / 0.18) ** 2)
    if lg > 0.01:
        draw_star(ctx, X0 + 52, Y0 - 52, 90 * lg, lg, 20 * lg)

# ================================================================== COMPOSITING
SURF = {k: new_surface() for k in ('m', 'g', 'am', 'ag', 'bm', 'bg')}

def render_into(key, fn, a):
    m, g = SURF[key + 'm'], SURF[key + 'g']
    cm, cg = m.getCanvas(), g.getCanvas()
    cm.clear(skia.ColorBLACK); cg.clear(skia.ColorTRANSPARENT)
    fn(Ctx(cm, cg), a)
    return m.makeImageSnapshot(), g.makeImageSnapshot()

def blit(canvas, img, dx=0, dy=0, alpha=1.0, clip=None, blend=None):
    canvas.save()
    if clip is not None: canvas.clipPath(clip, skia.ClipOp.kIntersect, True)
    p = skia.Paint(); p.setAlphaf(cl(alpha))
    if blend: p.setBlendMode(blend)
    canvas.drawImage(img, dx, dy, SAMP, p)
    canvas.restore()

def smear(canvas, img, dx0, dx1, n=8, clip=None):
    for i in range(n):
        x = lerp(dx0, dx1, i / max(n - 1, 1))
        blit(canvas, img, x, 0, 1.0 / n, clip, PLUS)

def compose(a):
    cm, cg = SURF['m'].getCanvas(), SURF['g'].getCanvas()
    cm.clear(skia.ColorBLACK); cg.clear(skia.ColorTRANSPARENT)
    ctx = Ctx(cm, cg)
    if a < DROP:
        shot_stage(ctx, a)
    elif a < B(9):
        shot_city(ctx, a)
    elif a < 5.70:
        shot_close(ctx, a, 'a')
    elif a < 5.92:
        # whip pan em_a -> em_b
        am, ag = render_into('a', lambda c_, aa: shot_close(c_, aa, 'a'), min(a, B(11)))
        bm, bg = render_into('b', lambda c_, aa: shot_close(c_, aa, 'b'), max(a, B(11)))
        if a < B(11):
            q = eie(seg(a, 5.70, B(11)))
            smear(cm, am, -W * q, -W * q + 260 * q, 10); smear(cg, ag, -W * q, -W * q + 260 * q, 4)
            q2 = 1 - eoe(seg(a, B(11) - 0.03, 5.92))
            if a > B(11) - 0.03:
                smear(cm, bm, W * q2, W * q2 + 200 * q2, 10); smear(cg, bg, W * q2, W * q2, 2)
        else:
            q2 = 1 - eoe(seg(a, B(11) - 0.03, 5.92))
            smear(cm, bm, W * q2 + 220 * q2, W * q2, 10); smear(cg, bg, W * q2, W * q2, 2)
    elif a < 6.66:
        shot_close(ctx, a, 'b')
    elif a < 6.90:
        # slash split: em_b halves slide apart over the face-off
        render_into('b', lambda c_, aa: shot_close(c_, aa, 'b'), min(a, 6.70))
        bm, bg = SURF['bm'].makeImageSnapshot(), SURF['bg'].makeImageSnapshot()
        shot_faceoff(ctx, a)
        q = eie(seg(a, 6.66, B(13) + 0.02))
        p0, p1 = (-200, 1560), (1280, 360)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; dl = math.hypot(dx, dy); nx, ny = -dy / dl, dx / dl
        for sgn in (-1, 1):
            half = skia.Path()
            far = 4000
            half.moveTo(p0[0] - dx, p0[1] - dy); half.lineTo(p1[0] + dx, p1[1] + dy)
            half.lineTo(p1[0] + dx + sgn * nx * far, p1[1] + dy + sgn * ny * far); half.lineTo(p0[0] - dx + sgn * nx * far, p0[1] - dy + sgn * ny * far); half.close()
            off = sgn * 1500 * q
            m_ = skia.Matrix.Translate(nx * off, ny * off); hp = skia.Path(half); hp.transform(m_)
            blit(cm, bm, nx * off, ny * off, 1.0, hp); blit(cg, bg, nx * off, ny * off, 1.0, hp)
            edge = skia.Path(); edge.moveTo(p0[0] - dx + nx * off, p0[1] - dy + ny * off); edge.lineTo(p1[0] + dx + nx * off, p1[1] + dy + ny * off)
            gold_stroke(ctx, edge, 5, a=1 - q * 0.6, glow=2.0, color=GOLD_L)
    elif a < 6.66 + 10:
        pass
    if 6.90 <= a < B(15) - 0.03:
        shot_faceoff(ctx, a)
    elif B(15) - 0.03 <= a < B(17):
        if a < B(15) + 0.05:
            render_into('a', shot_faceoff, a)
            am, ag = SURF['am'].makeImageSnapshot(), SURF['ag'].makeImageSnapshot()
            shot_coin(ctx, a)
            q = seg(a, B(15) - 0.03, B(15) + 0.05)
            blit(cm, am, 0, 0, 1 - q); blit(cg, ag, 0, 0, 1 - q)
        else:
            shot_coin(ctx, a)
    elif a >= B(17):
        shot_final(ctx, a)
    # slash line drawing before the split (drawn over em_b)
    if 6.56 <= a < 6.70:
        p0, p1 = (-200, 1560), (1280, 360)
        L = skia.Path(); L.moveTo(*p0); L.lineTo(*p1)
        gold_stroke(ctx, L, 5, a=1.0, glow=2.2, prog=eoe(seg(a, 6.56, 6.64)), color=GOLD_L)
    return SURF['m'], SURF['g']

# ================================================================== POST
rng = np.random.default_rng(11)
GRAIN = [(rng.standard_normal((H // 2, W // 2)).astype(np.float32)) for _ in range(6)]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
VIG = (1 - 0.55 * np.clip(rr, 0, 1.3) ** 2.4).astype(np.float32)[..., None]
FLASHES = [(B(1), 0.35, 0.15), (DROP, 0.9, 0.15), (B(9), 0.55, 0.12), (B(11), 0.3, 0.1), (B(13), 0.4, 0.12), (B(15), 0.45, 0.1),
           (B(17), 0.7, 0.14), (9.466, 0.3, 0.08), (9.728, 0.4, 0.08), (FINAL, 1.0, 0.2), (10.44, 0.22, 0.15)]
CAS = [(DROP, 1.0), (B(9), 0.7), (B(13), 0.6), (B(15), 0.5), (B(17), 0.7), (FINAL, 1.0)]

def post(a, fi, mS, gS):
    m = mS.toarray()[..., :3].astype(np.float32) / 255.0
    g = gS.toarray()
    ga = g[..., :3].astype(np.float32) * (g[..., 3:4].astype(np.float32) / 65025.0)
    sm = cv2.resize(ga, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    msm = cv2.resize(m, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    lum = msm.max(2, keepdims=True)
    sm = sm + np.clip(msm - 0.82, 0, 1) * 1.0
    e = ENV[min(fi, len(ENV) - 1)]
    b = cv2.GaussianBlur(sm, (0, 0), 3) * 0.55 + cv2.GaussianBlur(sm, (0, 0), 12) * 0.75 + cv2.GaussianBlur(sm, (0, 0), 34) * 0.5
    bloom = cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)
    img = m + bloom * (0.42 + 0.18 * e)
    # flashes
    fl = sum(amp * pulse(a, t, d) for t, amp, d in FLASHES)
    if fl > 0.003:
        img = img + fl * np.array([1.0, 0.86, 0.62], np.float32) * (0.55 + 0.45 * (1 - img.clip(0, 1)))
    # stop-time freeze: dim + desaturate
    if frozen(a):
        l = img.mean(2, keepdims=True)
        img = (img * 0.55 + l * 0.45) * 0.72
    # chromatic aberration on hits
    ca = sum(amp * pulse(a, t, 0.12) for t, amp in CAS)
    if ca > 0.03:
        s = 1 + 0.006 * ca
        M1 = np.float32([[s, 0, (1 - s) * W / 2], [0, s, (1 - s) * H / 2]])
        M2 = np.float32([[1 / s, 0, (1 - 1 / s) * W / 2], [0, 1 / s, (1 - 1 / s) * H / 2]])
        img[..., 0] = cv2.warpAffine(img[..., 0], M1, (W, H), borderMode=cv2.BORDER_REFLECT)
        img[..., 2] = cv2.warpAffine(img[..., 2], M2, (W, H), borderMode=cv2.BORDER_REFLECT)
    # tone: soft shoulder, warm highlights, burgundy shadows
    img = np.where(img > 0.75, 0.75 + 0.25 * np.tanh((img - 0.75) / 0.25), img)
    img = img * np.array([1.03, 0.99, 0.93], np.float32)
    img = img * VIG
    img = img + np.array([0.022, 0.004, 0.008], np.float32) * (1 - img.clip(0, 1))
    gr = cv2.resize(GRAIN[fi % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
    img = img + gr * 0.022
    # fades
    fade = ss(-1.0, -0.75, a) * (1 - ss(12.2, A_END - 0.05, a))
    img = img * fade
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)

# ================================================================== MAIN
def frame(fi):
    a = fi / FPS - PRE
    mS, gS = compose(a)
    return post(a, fi, mS, gS)

if __name__ == '__main__':
    if args.frames:
        os.makedirs(args.png, exist_ok=True)
        for f in [int(x) for x in args.frames.split(',')]:
            img = frame(f)
            cv2.imwrite(f'{args.png}/f{f:04d}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        sys.exit(0)
    end = NF if args.end < 0 else min(args.end, NF)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-x264-params', 'keyint=60', args.out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time; t0 = time.time()
    for f in range(args.start, end):
        pr.stdin.write(frame(f).tobytes())
        if (f - args.start) % 30 == 0:
            print(f'frame {f} ({time.time() - t0:.1f}s)', flush=True)
    pr.stdin.close(); pr.wait()
