"""Scene compositions + timeline for TOLY SUMMER x EMINEM.

Global timeline (s):  0.00 intro | 2.05 Toly | 4.40 shatter -> Eminem L1 | 6.48 whip -> L2
                      8.45 glitch -> L3 | 10.55 flash -> L4 | 12.58 finale | 15.0 end
"""
import math
import numpy as np, skia
from scipy.spatial import Delaunay
from core import *
from fx import *
from typo import Word, Block
from character import Character, POSES, blend_pose

SHOW_TITLE = True   # final "TOLY SUMMER × EMINEM" card

CH = {}


def ch(name):
    if name not in CH:
        CH[name] = Character(name)
    return CH[name]


LY = T['lyrics']
LE = T['line_end']


def wt(who, line, k, lead=0.04):
    return LY[who][line][k][1][0] - lead


def mouth(t, who):
    for line, end in zip(LY[who], LE[who]):
        syl = [s for _, ss in line for s in ss]
        if syl[0] - 0.06 <= t <= end + 0.06:
            return syllable_mouth(t, syl, end)
    return 0.0


def blink(t, seed):
    period = 2.6 + seed * 0.37
    ph = (t + seed * 1.13) % period
    return clamp(1 - abs(ph - 0.07) / 0.07) if ph < 0.14 else 0.0


def idle(t, seed, amp=1.0):
    roll = noise1(t * 0.9, seed) * 3.0 * amp + (beat_pulse(t, 6) - 0.3) * 2.2 * amp * (1 if int(t / 0.5) % 2 else -1)
    nod = beat_pulse(t, 7) * 0.7 * amp
    bounce = beat_pulse(t, 8) * 14 * amp
    return roll, nod, bounce


def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, rot=0.0, dx=0.0, dy=0.0):
    c.translate(cx + dx, cy + dy)
    c.rotate(rot)
    c.scale(zoom, zoom)
    c.translate(-cx, -cy)


def shake_amt(t, hits, amp=16, dur=0.3):
    a = 0
    for h in hits:
        if h <= t < h + dur:
            a = max(a, amp * (1 - (t - h) / dur) ** 2)
    return a


SH = Shake(3)

# ======================================================================== INTRO
DUST_I = Dust(260, 1)
SKY_FAR = Skyline(7, hmin=260, hmax=820)
SKY_NEAR = Skyline(9, hmin=160, hmax=520)


def scene_intro(c, t):
    bg_grad(c, '#030102', '#120306', '#050102')
    p = prog(t, 0, 2.05)
    c.save()
    zoom = 1 + 0.45 * e_in(p)
    cam(c, zoom, cy=880)
    glow_spot(c, W / 2, 880, 900, '#5c0f1c', 0.55 * clamp(t * 1.5))
    # skyline silhouette fades up from the dark
    SKY_FAR.draw(c, t, H + 40 - 140 * e_out(prog(t, 0.6, 2.0)), col='#160307', win='#c26a2a',
                 alpha=0.9 * prog(t, 0.5, 1.4), win_a=0.4 * prog(t, 0.9, 1.8))
    # heartbeat shockwaves on the two sub pulses
    for hb in (0.0, 1.03):
        shockwave(c, W / 2, 880, (t - hb) / 0.9, 900, width=26)
    # concentric 3D rings
    for k, (r, tilt0, sp) in enumerate([(250, 1.1, 0.7), (370, 1.25, -0.5), (500, 1.35, 0.35)]):
        a = prog(t, 0.1 + k * 0.18, 0.6 + k * 0.18) * (1 - prog(t, 1.85, 2.05))
        rr = r * (1 - 0.85 * e_in(prog(t, 1.65, 2.05)))
        ring3d(c, W / 2, 880, rr, tilt0 + 0.25 * math.sin(t * 1.3 + k), t * sp + k, a,
               dash=[40, 22] if k == 1 else None, t=t, width=4)
    # wire icosahedron draws itself, spins up, collapses into a point
    sz = 1.25 * (1 - e_in(prog(t, 1.7, 2.05)))
    spin = t * 0.8 + 3 * e_in(prog(t, 1.4, 2.05))
    wire_ico(c, t, W / 2, 880, sz * 1.0, (spin * 0.7, spin, 0.3), draw_p=e_out(prog(t, 0.15, 1.4)),
             alpha=prog(t, 0.1, 0.5), width=4)
    # particles rushing toward camera, streaking near the drop
    DUST_I.draw(c, t, t * 500 + 1400 * e_in(p), alpha=clamp(t * 2), cy=880,
                streak=2.2 * e_in(prog(t, 1.3, 2.05)))
    # anamorphic flare + core
    core = e_in(prog(t, 1.2, 2.05))
    glow_spot(c, W / 2, 880, 140 + 700 * core, '#ffcf6b', 0.25 + 0.75 * core)
    c.drawRect(skia.Rect(-200, 876, W + 200, 884), P('#ffe7a1', 0.5 * core + 0.15 * beat_pulse(t), blur=6, blend=ADD))
    c.restore()
    # flash into the drop
    c.drawRect(skia.Rect(0, 0, W, H), P('#fff3d0', e_in(prog(t, 1.85, 2.05)) * 0.95))


# ======================================================================== TOLY
EMB = Embers(70, 4)
T_GORI, T_YA, T_GORYU, T_TOZHE = (wt('toly', 0, k) for k in range(4))
TOLY_TEXT = Block([
    [Word('ГОРИ,', T_GORI, 'fire', 'slam', size=1.3, glow=('#ff6a1a', 0.9))],
    [Word('Я', T_YA, 'cream', 'drop', size=0.9), Word('ГОРЮ', T_GORYU, 'fire', 'zoom', size=1.0, pill=True,
                                                       glow=('#ff6a1a', 0.7))],
    [Word('ТОЖЕ', T_TOZHE, 'gold', 'slam', size=1.45, glow=('#ffb347', 0.9))],
], y_top=150, size=150)


def scene_toly(c, t):
    surge = e_out(prog(t, T_TOZHE, T_TOZHE + 0.25))
    bg_grad(c, '#1a0306', '#7a1410', '#3a0808')
    c.save()
    zoom = 1.0 + 0.06 * prog(t, 2.05, 4.4) + 0.05 * surge
    s = shake_amt(t, [T_GORI, T_TOZHE], 18)
    dx, dy, rr = SH.at(t, s)
    cam(c, zoom, cy=1000, dx=dx, dy=dy, rot=rr * 20)
    rise = e_out(prog(t, 2.05, 2.6))
    glow_spot(c, W / 2, 1500, 1100, '#ff5a1a', 0.35 + 0.3 * surge)
    SKY_FAR.draw(c, t, H - 380 + 300 * (1 - rise), col='#2a0508', win='#ffb347', alpha=1, win_a=0.8, xoff=-30 * t)
    flames(c, t, H - 300, (650 + 500 * surge) * rise, seed=1, alpha=1)
    SKY_NEAR.draw(c, t, H - 150 + 200 * (1 - rise), col='#170306', win='#ff8a2a', alpha=1, win_a=0.5, xoff=-60 * t)
    # Toly rises into frame
    ty = 1270 + 900 * (1 - e_out(prog(t, 2.1, 2.7)))
    roll, nod, bounce = idle(t, 1)
    pa = prog(t, 2.75, 3.0)
    poses = (blend_pose('cross', 'rest', pa), blend_pose('cross', 'mic', pa))
    if t > T_TOZHE:
        poses = (blend_pose('rest', 'fist_up', e_out(prog(t, T_TOZHE, T_TOZHE + 0.15))), poses[1])
    yaw = 0.12 * math.sin(t * 2.1) + 0.1
    ch('toly').draw(c, W / 2 + 10, ty, 0.68, t, mouth=mouth(t, 'toly'), blink=blink(t, 1), brow=0.6 * surge,
                    yaw=yaw, roll=roll, nod=nod, bounce=bounce, poses=poses,
                    rim=('#ff7a1a', 0.75 + 0.25 * surge, 34),
                    tint=lin(0, 900, 0, H, [C('#ff8a2a', 0), C('#ff5a1a', 0.38 + 0.2 * surge)]))
    flames(c, t + 3.3, H + 60, (300 + 650 * surge) * rise, n=9, seed=4, alpha=0.95,
           layers=FLAME_LAYERS[1:])
    EMB.draw(c, t, H, alpha=rise, boost=1 + surge)
    c.restore()
    TOLY_TEXT.draw(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffd9a0', (1 - prog(t, 2.05, 2.4)) * 0.9))
    c.drawRect(skia.Rect(0, 0, W, H), P('#ff8a2a', 0.25 * (1 - prog(t, T_TOZHE, T_TOZHE + 0.3)) * (t > T_TOZHE), blend=ADD))


# ======================================================================== EMINEM L1
E1 = [wt('eminem', 0, k) for k in range(8)]
EM1_TEXT = Block([
    [Word('NOW,', E1[0], 'gold', 'slam', size=1.4, glow=('#ffb347', 0.7))],
    [Word('THIS', E1[1], 'cream', 'drop', 0.82), Word('LOOKS', E1[2], 'cream', 'drop', 0.82),
     Word('LIKE', E1[3], 'cream', 'drop', 0.82), Word('A', E1[4], 'cream', 'drop', 0.82)],
    [Word('JOB', E1[5], 'gold', 'zoom', 1.3, pill=True, glow=('#ffb347', 0.6)),
     Word('FOR', E1[6], 'cream', 'rise', 0.9), Word('ME', E1[7], 'gold', 'slam', 1.3, glow=('#ffb347', 0.6))],
], y_top=130, size=140)
DUST_E = Dust(120, 5, depth=(400, 3000))


def stage_bg(c, t, cx=W / 2, cy=1020, beams=True):
    bg_grad(c, '#0e0207', '#3a0a12', '#120306')
    rays(c, t, cx, cy, 26, '#2b070e', '#1d0509', t * 0.12, alpha=1)
    halftone(c, 0, 1500, W, H, 26, 7, '#000000', 0.35)
    if beams:
        for k, (bx, sp) in enumerate([(-200, 0.7), (W / 2, 0), (W + 200, -0.6)]):
            sw = math.sin(t * 1.1 + k * 2) * 220 * (1 if k != 1 else 0.3)
            spot_beam(c, bx, -80, cx + sw, 1700, 30, 330, '#ffd27a', 0.22 if k == 1 else 0.14)


def scene_em1(c, t):
    stage_bg(c, t)
    c.save()
    z0 = lerp(1.45, 1.0, e_io(prog(t, 4.45, 5.25)))
    pj = prog(t, E1[5], E1[5] + 0.12) - prog(t, E1[5] + 0.25, E1[5] + 0.7)
    zoom = z0 + 0.12 * e_out(clamp(pj))
    s = shake_amt(t, [E1[0], E1[5], E1[7]], 14)
    dx, dy, rr = SH.at(t, s)
    cam(c, zoom, cy=880, dx=dx, dy=dy, rot=rr * 15)
    # halo disc behind the head
    hx, hy = W / 2, 870
    c.drawCircle(hx, hy, 470, P('#ffffff', shader=rad(hx, hy, 470, ['#6e1420', '#3a0a12'])))
    ring3d(c, hx, hy, 480, 0.15 * math.sin(t), t * 0.2, 1.0, width=6)
    ring3d(c, hx, hy, 420, 0.1, -t * 0.3, 0.6, dash=[26, 16], t=t, width=3)
    for k in range(9):
        a = rnd(k, 3) * 6.28 + t * 0.4
        star4(c, hx + math.cos(a) * (520 + 60 * rnd(k, 8)), hy + math.sin(a) * (520 + 60 * rnd(k, 8)),
              12 + 10 * math.sin(t * 4 + k), a=0.8)
    roll, nod, bounce = idle(t, 2)
    pose_l = 'rest'; pose_r = 'rest'
    if t > E1[1]:
        pose_r = blend_pose('rest', 'open', e_out(prog(t, E1[1], E1[1] + 0.2)))
    if t > E1[5]:
        pose_r = blend_pose('open', 'fist_up', e_out(prog(t, E1[5] - 0.05, E1[5] + 0.1)))
    if t > E1[6]:
        pose_r = blend_pose('fist_up', 'rest', e_out(prog(t, E1[6], E1[6] + 0.2)))
        pose_l = blend_pose('rest', 'point_self', e_out(prog(t, E1[6], E1[6] + 0.18)))
    yaw = lerp(-0.22, 0.1, e_io(prog(t, 4.5, 5.4))) + 0.06 * math.sin(t * 3)
    ch('eminem').draw(c, W / 2, 1330, 0.68, t, mouth=mouth(t, 'eminem'), blink=blink(t, 2),
                      brow=clamp(pj * 2) * 0.9, yaw=yaw, roll=roll, nod=nod, bounce=bounce, poses=(pose_l, pose_r),
                      rim=('#ffcf6b', 0.55, 26),
                      tint=lin(0, 500, 0, H, [C('#ffcf6b', 0.10), C('#3a0a12', 0.35)]))
    DUST_E.draw(c, t, t * 120, alpha=0.8, cy=900)
    c.restore()
    EM1_TEXT.draw(c, t, exit_t=6.42, exit_kind='up')


# ======================================================================== EMINEM L2
E2 = [wt('eminem', 1, k) for k in range(5)]
EM2_TEXT = Block([
    [Word('SO', E2[0], 'cream', 'drop', 0.9), Word('EVERYBODY,', E2[1], 'gold', 'drop', 1.05, glow=('#ffb347', 0.5))],
    [Word('JUST', E2[2], 'cream', 'rise', 0.75)],
    [Word('FOLLOW', E2[3], 'gold', 'snake', 1.3, glow=('#ffb347', 0.6)), Word('ME', E2[4], 'cream', 'snake', 1.3)],
], y_top=130, size=140)
CROWD = []
_r = np.random.default_rng(21)
for row, (yy, sc, n) in enumerate([(1180, 0.42, 11), (1300, 0.55, 9), (1450, 0.72, 8), (1640, 0.95, 6), (1880, 1.2, 5)]):
    for k in range(n):
        x = (k + 0.5) / n * (W + 300) - 150 + _r.uniform(-30, 30) + (row % 2) * 40
        CROWD.append((row, x, yy, sc, _r.uniform(0, 6.28), _r.choice(['#2e2230', '#3a2a36', '#2a2030', '#43303c'])))


def draw_crowd(c, t, rows, light, turn, march):
    for row, x, yy, sc, ph, col in CROWD:
        if row not in rows:
            continue
        if abs(x - W / 2) < 150 * sc and row <= 2:
            continue
        lt = clamp(light * 1.6 - row * 0.15)
        bob = -abs(math.sin((t * math.pi / 0.5) + ph * 0.3)) * 14 * sc * light
        tw = turn * (1 if x < W / 2 else -1)
        xm = x + march * (W / 2 - x) * 0.12
        face = '#%02x%02x%02x' % tuple(int(lerp(a, b, lt)) for a, b in zip((70, 40, 44), (214, 170, 140)))
        body = col if lt < 0.5 else '#4a3a48'
        crowd_person(c, xm, yy + bob, sc, body=body, face=face, tie='#b5121b' if lt > 0.3 else '#4a0c14', a=1, turn=tw)


def scene_em2(c, t):
    bg_grad(c, '#12060e', '#2a1222', '#0a0306')
    light = e_out(prog(t, E2[1], E2[1] + 0.6))
    turn = e_out(prog(t, E2[3], E2[3] + 0.3))
    march = e_io(prog(t, E2[3], 8.6))
    c.save()
    z = lerp(1.25, 1.0, e_io(prog(t, 6.55, 7.5)))
    s = shake_amt(t, [E2[3]], 12)
    dx, dy, rr = SH.at(t, s)
    cam(c, z, cy=1000, dx=dx, dy=dy + lerp(-120, 0, e_io(prog(t, 6.55, 7.5))), rot=lerp(-3, 0, e_io(prog(t, 6.55, 7.6))))
    halftone(c, 0, 0, W, 900, 30, 6, '#ffcf6b', 0.08, grad_dir=-1)
    for k in range(5):
        spot_beam(c, (k + 0.5) / 5 * W, -50, (k + 0.5) / 5 * W + math.sin(t * 1.5 + k) * 120, 1500, 20, 160,
                  '#ffd27a', 0.10 * light)
    spot_beam(c, W / 2, -80, W / 2, 1600, 40, 360, '#ffe2a0', 0.28)
    draw_crowd(c, t, [0, 1, 2], light, turn, march)
    roll, nod, bounce = idle(t, 3)
    wave = math.sin(t * 13) * 0.35
    pr = POSES['beckon']; pr = (pr[0], pr[1] + wave) + pr[2:]
    pose_r = blend_pose('rest', pr, e_out(prog(t, E2[0] - 0.1, E2[0] + 0.15)))
    pose_l = 'rest'
    if t > E2[3] - 0.05:
        pose_r = blend_pose(pr, 'point_up', e_out(prog(t, E2[3] - 0.05, E2[3] + 0.12)))
    yaw = 0.25 * math.sin(t * 1.6) * (1 - turn) + (-0.15 * turn)
    lean = -3 * turn
    ch('eminem').draw(c, W / 2, 1300, 0.6, t, mouth=mouth(t, 'eminem'), blink=blink(t, 3), brow=0.5 * light,
                      yaw=yaw, roll=roll, nod=nod, bounce=bounce, lean=lean, poses=(pose_l, pose_r),
                      rim=('#ffe2a0', 0.6, 24), tint=lin(0, 400, 0, H, [C('#ffe2a0', 0.12), C('#12060e', 0.4)]))
    draw_crowd(c, t, [3, 4], light, turn, march)
    # chevrons pointing toward the star of the show
    if turn > 0:
        for k in range(6):
            for sgn in (-1, 1):
                x = W / 2 + sgn * (480 - ((t * 400 + k * 90) % 450))
                y = 1120
                a = turn * 0.9 * clamp(1 - abs(x - W / 2) / 520)
                pth = path_poly([(x - sgn * 18, y - 26), (x + sgn * 8, y), (x - sgn * 18, y + 26)], close=False)
                c.drawPath(pth, P('#ffcf6b', a, stroke=8))
    c.restore()
    EM2_TEXT.draw(c, t, exit_t=8.40, exit_kind='scatter')


# ======================================================================== EMINEM L3
E3 = [wt('eminem', 2, k) for k in range(6)]
EM3_TEXT = Block([
    [Word('’CAUSE', E3[0], 'cream', 'flip', 0.9), Word('WE', E3[1], 'cream', 'flip', 0.9),
     Word('NEED', E3[2], 'gold', 'flip', 0.95)],
    [Word('A', E3[3], 'cream', 'rise', 0.75), Word('LITTLE', E3[4], 'cream', 'rise', 0.75)],
], y_top=120, size=140)
EM3_BIG = Block([[Word('CONTROVERSY', E3[5], 'gold', 'glitch', 1.0, glow=('#ff2a3c', 0.9))]],
                y_top=1440, size=190, max_w=1010)


def scene_em3(c, t):
    hit = E3[5]
    hv = e_out(prog(t, hit, hit + 0.2))
    spin = 0.35 * t + 0.6 * e_out(prog(t, hit, hit + 0.5))
    bg_grad(c, '#2a0408', '#5c0a12', '#1a0206')
    rays(c, t, W / 2, 900, 22, '#c8141d', '#8a0d16', spin, alpha=1)
    halftone(c, 0, 1200, W, H, 28, 9, '#1a0206', 0.6)
    # black hazard bands
    c.save(); c.translate(W / 2, 1000); c.rotate(-18 + 4 * math.sin(t))
    for k, (yo, hgt) in enumerate([(-760, 90), (520, 140)]):
        c.drawRect(skia.Rect(-1400, yo, 1400, yo + hgt), P('#0a0204'))
        pp = P('#e2a93b', 0.9, stroke=5)
        pp.setPathEffect(skia.DashPathEffect.Make([60, 40], -t * 300 * (1 if k else -1)))
        c.drawLine(-1400, yo + 14, 1400, yo + 14, pp)
        c.drawLine(-1400, yo + hgt - 14, 1400, yo + hgt - 14, pp)
    c.restore()
    c.save()
    s = shake_amt(t, [E3[0], hit], 22, 0.35)
    dx, dy, rr = SH.at(t, s)
    zoom = lerp(1.0, 1.08, prog(t, 8.5, 10.5)) + 0.06 * hv
    roll_cam = math.sin(t * 2.2) * 4 + (6 * hv * math.sin(t * 9) * (1 - prog(t, hit, hit + 0.6)))
    cam(c, zoom, cy=1000, dx=dx, dy=dy, rot=roll_cam + rr * 20)
    # echo heads (controversy chorus)
    echo = e_back(prog(t, hit, hit + 0.25))
    if echo > 0:
        for sgn in (-1, 1):
            ch('eminem').draw(c, W / 2 + sgn * 330 * echo, 1300 - 60 * echo, 0.55, t + 1.3,
                              mouth=mouth(t - 0.08, 'eminem'), yaw=-sgn * 0.3, roll=sgn * 8,
                              poses=('rest', 'rest'), alpha=0.85 * echo,
                              tint=lin(0, 600, 0, H, [C('#ff2a3c', 0.6), C('#5c0a12', 0.75)]))
    roll, nod, bounce = idle(t, 4, 1.3)
    bi, _ = beat_phase(t)
    _, bidx = beat_phase(t)
    yaw = 0.28 * math.sin(t * math.pi / 0.98)
    pose_l = blend_pose('rest', 'open', e_out(prog(t, E3[2], E3[2] + 0.2)))
    pose_r = blend_pose('rest', 'point_fwd', e_out(prog(t, hit - 0.05, hit + 0.12)))
    ch('eminem').draw(c, W / 2, 1520, 0.92, t, mouth=mouth(t, 'eminem'), blink=blink(t, 4),
                      brow=1.0 * hv + 0.3 * beat_pulse(t, 6), yaw=yaw, roll=roll, nod=nod, bounce=bounce,
                      poses=(pose_l, pose_r), rim=('#ff3a2a', 0.8, 30),
                      tint=lin(0, 500, 0, H, [C('#ff4a2a', 0.15), C('#3a0408', 0.45)]))
    c.restore()
    EM3_TEXT.draw(c, t)
    # CONTROVERSY on a tilted 3D plane
    c.save()
    m = skia.Matrix()
    tilt = 0.00025 * math.sin(t * 2.5)
    m.setAll(1, 0, 0, 0, 1, 0, tilt, 0, 1)
    c.translate(W / 2, 1380); c.concat(m); c.rotate(-4 + 3 * math.sin(t * 3)); c.translate(-W / 2, -1380)
    if t > hit:
        c.drawRect(skia.Rect(-100, 1395, W + 100, 1690), P('#0a0204', 0.85 * hv))
    EM3_BIG.draw(c, t)
    c.restore()


# ======================================================================== EMINEM L4
E4 = [wt('eminem', 3, k) for k in range(7)]
EM4_TEXT = Block([
    [Word('’CAUSE', E4[0], 'cream', 'drop', 0.75), Word('IT', E4[1], 'cream', 'drop', 0.75),
     Word('FEELS', E4[2], 'cream', 'drop', 0.75), Word('SO', E4[3], 'cream', 'drop', 0.75)],
    [Word('EMPTY', E4[4], 'hollow', 'zoom', 1.55, exit_kind='drift')],
    [Word('WITHOUT', E4[5], 'gold', 'slam', 1.15, glow=('#ffb347', 0.8)),
     Word('ME', E4[6], 'gold', 'slam', 1.35, glow=('#ffcf6b', 1.0), pill=True)],
], y_top=130, size=140)
DUST_V = Dust(90, 8, depth=(300, 2500))


def floor_grid(c, t, horizon, alpha, col='#e2a93b'):
    if alpha <= 0.01:
        return
    for k in range(-12, 13):
        x0 = W / 2 + k * 40
        x1 = W / 2 + k * 420
        c.drawLine(x0, horizon, x1, H + 200, P(col, alpha * 0.35, stroke=2))
    for k in range(14):
        u = ((k + t * 0.6) % 14) / 14
        y = horizon + (H + 200 - horizon) * u ** 2.2
        c.drawLine(-100, y, W + 100, y, P(col, alpha * 0.4 * u, stroke=2))


def scene_em4(c, t):
    me = E4[6]
    mv = e_out(prog(t, me, me + 0.18))
    empty = prog(t, E4[4], E4[5])
    bg_grad(c, '#050103', '#14030a', '#030102')
    glow_spot(c, W / 2, 1100, 900, '#3a0a12', 0.7)
    floor_grid(c, t, 1180, 0.9 - 0.4 * empty)
    c.save()
    s = shake_amt(t, [E4[5], me], 20)
    dx, dy, rr = SH.at(t, s)
    zoom = 1.0 + 0.04 * prog(t, 10.5, 11.9) + 0.22 * e_out(prog(t, E4[5], me + 0.15))
    cam(c, zoom, cy=880, dx=dx, dy=dy, rot=rr * 15)
    spot_beam(c, W / 2, -80, W / 2, 1750, 40, 380, '#fff0c8', 0.30 + 0.25 * mv)
    floor_ring(c, W / 2, 1720, 430, 90, 0.8, t)
    roll, nod, bounce = idle(t, 5, 0.8)
    pose = ('rest', 'rest')
    po = e_out(prog(t, E4[2], E4[2] + 0.25))
    pose = (blend_pose('rest', 'open', po), blend_pose('rest', 'open', po))
    if t > E4[5] - 0.1:
        pp = e_out(prog(t, E4[5] - 0.1, E4[5] + 0.1))
        pose = (blend_pose('open', 'point_self', pp), blend_pose('open', 'rest', pp))
    nod += 0.8 * empty * (1 - prog(t, E4[5] - 0.2, E4[5]))
    ch('eminem').draw(c, W / 2, 1360, 0.64, t, mouth=mouth(t, 'eminem'), blink=blink(t, 5),
                      brow=-0.3 * empty + 1.0 * mv, yaw=-0.12 + 0.05 * math.sin(t * 2), roll=roll, nod=nod,
                      bounce=bounce, poses=pose, rim=('#fff0c8', 0.5 + 0.4 * mv, 26),
                      tint=lin(0, 400, 0, H, [C('#fff0c8', 0.08), C('#050103', 0.55)]))
    DUST_V.draw(c, t, t * 80, alpha=0.6, cy=900, color='#ffe2a0')
    shockwave(c, W / 2, 900, (t - me) / 0.7, 1100, width=40)
    c.restore()
    EM4_TEXT.draw(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffffff', 0.85 * (1 - prog(t, 10.55, 10.75))))


# ======================================================================== FINALE
FIN = 12.58
DUST_F = Dust(200, 12)
EMB_F = Embers(50, 13)
TITLE = Block([
    [Word('TOLY', FIN + 0.35, 'gold', 'drop', 1.0, glow=('#ffb347', 0.5)),
     Word('SUMMER', FIN + 0.45, 'gold', 'drop', 1.0, glow=('#ffb347', 0.5))],
    [Word('×', FIN + 0.75, 'cream', 'zoom', 0.8)],
    [Word('EMINEM', FIN + 0.95, 'gold', 'slam', 1.25, glow=('#ffcf6b', 0.7))],
], y_top=150, size=130)


def scene_finale(c, t):
    lt = t - FIN
    bg_grad(c, '#12030a', '#3a0a12', '#1a0306')
    orbit = e_io(prog(t, FIN, 15.0))
    rays(c, t, W / 2 - 60 * orbit, 1000, 30, '#4a0c16', '#2a060c', t * 0.25, alpha=1)
    glow_spot(c, W / 2, 1050, 900, '#ffb347', 0.25)
    ring3d(c, W / 2 - 40 * orbit, 1000, 520, 0.2 + 0.2 * math.sin(t), t * 0.3, 1.0, width=6)
    ring3d(c, W / 2 - 40 * orbit, 1000, 600, 1.2, -t * 0.4, 0.7, dash=[30, 20], t=t, width=3)
    SKY_FAR.draw(c, t, H - 320, col='#2a0508', win='#ffb347', win_a=0.7, xoff=-80 * orbit)
    flames(c, t, H - 240, 420, seed=2, alpha=0.95)
    c.save()
    zoom = lerp(1.15, 1.0, e_out(prog(t, FIN, FIN + 0.6))) + 0.05 * orbit
    s = shake_amt(t, [FIN], 26, 0.5)
    dx, dy, rr = SH.at(t, s)
    cam(c, zoom, cy=1100, dx=dx + 40 * orbit, dy=dy, rot=rr * 20)
    ent = e_back(prog(t, FIN, FIN + 0.45), 1.3)
    breath = math.sin(t * 2.4) * 6
    # Toly left, Eminem right, turned toward each other
    ch('toly').draw(c, lerp(-300, 300, ent) + 30 * orbit, 1330 + breath, 0.5, t, blink=blink(t, 6),
                    yaw=0.22, roll=-2 + noise1(t, 9) * 2, poses=('cross', 'cross'),
                    rim=('#ff8a2a', 0.8, 26), tint=lin(0, 900, 0, H, [C('#ff8a2a', 0), C('#ff5a1a', 0.3)]))
    pe = e_out(prog(t, FIN + 0.9, FIN + 1.3))
    ch('eminem').draw(c, lerp(W + 300, 780, ent) + 10 * orbit, 1320 - breath, 0.52, t, blink=blink(t, 7),
                      yaw=-0.22, roll=2 + noise1(t, 10) * 2,
                      poses=(blend_pose('fist_up', 'cross', pe), blend_pose('rest', 'cross', pe)),
                      rim=('#ffcf6b', 0.8, 26), tint=lin(0, 900, 0, H, [C('#ffcf6b', 0.05), C('#ff5a1a', 0.3)]))
    flames(c, t + 2.0, H + 80, 260, n=9, seed=5, alpha=0.9, layers=FLAME_LAYERS[1:])
    EMB_F.draw(c, t, H, alpha=1)
    DUST_F.draw(c, t, lt * 300, alpha=0.9, cy=1000, streak=0.6 * (1 - prog(t, FIN, FIN + 0.8)))
    shockwave(c, W / 2, 1000, lt / 0.9, 1300, width=50)
    c.restore()
    if SHOW_TITLE:
        TITLE.draw(c, t)
    c.drawRect(skia.Rect(0, 0, W, H), P('#fff3d0', 0.95 * (1 - prog(t, FIN, FIN + 0.3))))
    # iris out to black with a gold edge
    ir = prog(t, 14.25, 14.9)
    if ir > 0:
        r = lerp(1400, 0, e_in(ir))
        pth = skia.Path(); pth.addRect(skia.Rect(-10, -10, W + 10, H + 10)); pth.addCircle(W / 2, 900, max(r, 0.1))
        pth.setFillType(skia.PathFillType.kEvenOdd)
        c.drawPath(pth, P('#000000'))
        if r > 1:
            c.drawCircle(W / 2, 900, r, P('#ffcf6b', 0.9, stroke=8))
            c.drawCircle(W / 2, 900, r, P('#ffcf6b', 0.5, stroke=26, blur=14, blend=ADD))
    if t >= 14.9:
        c.clear(C('#000000'))


# ======================================================================== transitions
def render_scene(fn, t):
    s = skia.Surface(W, H)
    fn(s.getCanvas(), t)
    return s.makeImageSnapshot()


_pts = []
_r2 = np.random.default_rng(42)
for gy in range(-1, 18):
    for gx in range(-1, 11):
        _pts.append((gx * W / 9 + _r2.uniform(-40, 40), gy * H / 16 + _r2.uniform(-40, 40)))
_pts = np.array(_pts)
TRI = Delaunay(_pts).simplices


def trans_shatter(c, t, t0=4.40, t1=4.85):
    scene_em1(c, t)
    p = prog(t, t0, t1)
    img = render_scene(scene_toly, min(t, t0))
    cx, cy = W / 2, 1000
    samp = skia.SamplingOptions(skia.FilterMode.kLinear)
    for k, tri in enumerate(TRI):
        pts = _pts[tri]
        gx, gy = pts.mean(0)
        d = math.hypot(gx - cx, gy - cy) + 1
        delay = d / 1500 * 0.35
        q = clamp((p - delay) / (1 - delay + 1e-6))
        if q >= 1:
            continue
        e = e_in(q)
        vx, vy = (gx - cx) / d, (gy - cy) / d
        mx = vx * 900 * e + (rnd(k, 1) - 0.5) * 300 * e
        my = vy * 900 * e + 1400 * e * e
        rot = (rnd(k, 2) - 0.5) * 300 * e
        flip = math.cos(e * math.pi * (1 + rnd(k, 3)))
        sc = 1 + 0.5 * e
        path = path_poly([tuple(v) for v in pts])
        c.save()
        c.translate(gx + mx, gy + my); c.rotate(rot); c.scale(sc * flip, sc); c.translate(-gx, -gy)
        pa = skia.Paint(); pa.setAlphaf(1 - e * 0.6)
        c.save(); c.clipPath(path, doAntiAlias=True)
        c.drawImage(img, 0, 0, samp, pa)
        c.restore()
        if q > 0:
            c.drawPath(path, P('#ffd37a', (1 - q) * 0.9, stroke=3))
        c.restore()
    # crack flash just before the break
    fl = 1 - abs(t - t0) / 0.06
    if fl > 0:
        for tri in TRI[::3]:
            c.drawPath(path_poly([tuple(v) for v in _pts[tri]]), P('#fff3c4', fl * 0.8, stroke=2.5))


def trans_whip(c, t, fa, fb, t0, t1):
    p = e_io(prog(t, t0, t1))
    ia, ib = render_scene(fa, t), render_scene(fb, t)
    samp = skia.SamplingOptions(skia.FilterMode.kLinear)
    speed = math.sin(p * math.pi)
    for img, off in ((ia, -p * W * 1.1), (ib, (1 - p) * W * 1.1)):
        n = 6
        for k in range(n):
            pa = skia.Paint(); pa.setAlphaf(1.0 / (k + 1) if k else 1.0)
            pa.setAlphaf(0.9 if k == 0 else 0.22)
            c.drawImage(img, off + (k - n / 2) * 40 * speed, 0, samp, pa)
    for k in range(14):
        y = rnd(k, 5) * H
        c.drawRect(skia.Rect(-10, y, W + 10, y + 3 + 6 * rnd(k, 6)), P('#ffd37a', 0.6 * speed, blend=ADD))


def trans_glitch(c, t, fa, fb, t0, t1):
    p = prog(t, t0, t1)
    ia, ib = render_scene(fa, t), render_scene(fb, t)
    samp = skia.SamplingOptions(skia.FilterMode.kLinear)
    c.drawImage(ia if p < 0.5 else ib, 0, 0, samp, None)
    fr = int(t * 60)
    y = 0
    k = 0
    while y < H:
        h = 20 + rnd(k + fr * 13, 7) * 160
        use_b = rnd(k + fr * 7, 8) < p
        off = (rnd(k + fr * 3, 9) - 0.5) * 260 * math.sin(p * math.pi)
        img = ib if use_b else ia
        c.save(); c.clipRect(skia.Rect(0, y, W, y + h))
        c.drawImage(img, off, 0, samp, None)
        if rnd(k + fr, 10) < 0.25:
            c.drawRect(skia.Rect(0, y, W, y + h), P('#ff1a3c' if k % 2 else '#19e3ff', 0.25, blend=ADD))
        c.restore()
        y += h
        k += 1
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffffff', 0.35 * math.sin(p * math.pi) * (fr % 2)))


# ======================================================================== frame
def render(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(C('#000000'))
    if t < 2.05:
        scene_intro(c, t)
    elif t < 4.40:
        scene_toly(c, t)
    elif t < 4.85:
        trans_shatter(c, t)
    elif t < 6.46:
        scene_em1(c, t)
    elif t < 6.70:
        trans_whip(c, t, scene_em1, scene_em2, 6.46, 6.70)
    elif t < 8.44:
        scene_em2(c, t)
    elif t < 8.66:
        trans_glitch(c, t, scene_em2, scene_em3, 8.44, 8.66)
    elif t < 10.55:
        scene_em3(c, t)
    elif t < FIN:
        scene_em4(c, t)
    else:
        scene_finale(c, t)
    # global finishing: beat glow, vignette, grain
    if 2.05 < t < FIN:
        c.drawRect(skia.Rect(0, 0, W, H), P('#ff9a3a', 0.05 * kick_at(t), blend=ADD))
    vignette(c, 0.7)
    grain(c, t, 0.07)
    return surf
