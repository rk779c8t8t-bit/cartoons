"""Edit timeline. All times are absolute seconds in the original track.

Word times come from ASR word timestamps (sherpa-onnx zipformer) cross-checked
against vocal-band onsets of the track; beat grid ~103.4 BPM (0.58 s / beat).
"""
import math

from engine import (BLACK, BROWN, CREAM, FLASH, GHOST_DARK, MAROON, TAN, W, H, Frame,
                    cap_h, cap_w, clamp, fit, in_cubic, in_out, in_quad, layout_lines, lerp,
                    out_back, out_cubic, out_expo, ph, spring)

T_START = 17.82      # just before "Y'all"
T_AUDIO_END = 40.07  # right after "Shady"
T_END = 41.10        # echo tail + outro

# ---------------------------------------------------------------- helpers
def slam(t, t0, frm=1.6, d=0.11):
    """scale that lands hard at t0 (starts slightly before)."""
    x = ph(t, t0 - 0.03, d)
    return lerp(frm, 1.0, out_expo(x)), clamp((t - t0 + 0.03) / 0.035)

def popin(t, t0, d=0.16):
    x = ph(t, t0 - 0.02, d)
    return max(0.0, out_back(x, 2.2)) if x > 0 else 0.0

def vis(t, t0):
    return t >= t0 - 0.02


# ---------------------------------------------------------------- S1  Y'all act like you never seen a
S1 = [["Y’ALL"], ["ACT", "LIKE"], ["YOU", "NEVER"], ["SEEN", "A"]]
S1_T = [17.91, 18.21, 18.44, 18.66, 18.79, 19.02, 19.22]
S1_L = layout_lines(S1, width=940, max_cap=330, cy=930)

def s1(F, t):
    F.bg(MAROON)
    F.cam["z"] = 1.0 + 0.05 * ph(t, 17.82, 1.55)
    hits = []
    for i, ((wd, size, x, y), t0) in enumerate(zip(S1_L, S1_T)):
        if not vis(t, t0):
            continue
        sc, al = slam(t, t0, 1.55 if i else 2.2)
        rot = (1 - out_expo(ph(t, t0, 0.14))) * (-10 if i % 2 else 8)
        F.text(wd, size, x, y, CREAM, sc=sc, rot=rot, alpha=al)
        hits.append((t0, 9 if i else 16))
    F.shake(t, hits)


# ---------------------------------------------------------------- S2  WHITE person before
def s2(F, t):
    F.bg(CREAM)
    F.shake(t, [(19.36, 34), (19.62, 8), (19.92, 10)])
    # whip zoom out of the scene
    F.cam["z"] *= 1 + 0.35 * in_cubic(ph(t, 20.08, 0.14))
    size = fit("WHITE", 960)
    sc, al = slam(t, 19.36, 2.6, 0.13)
    F.text("WHITE", size, 540, 960, MAROON, sc=sc, sy=1.75, alpha=al)
    if vis(t, 19.62):
        y = lerp(260, 420, out_expo(ph(t, 19.60, 0.12)))
        s = fit("PERSON", 620)
        F.text("PERSON", s, 540, y, MAROON, clip=(0, 300, W, 560))
        F.rect(230, 548, 850, 556, MAROON, alpha=out_expo(ph(t, 19.62, 0.2)))
    if vis(t, 19.92):
        y = lerp(1700, 1500, out_expo(ph(t, 19.90, 0.12)))
        s = fit("BEFORE", 620)
        F.text("BEFORE", s, 540, y, MAROON, clip=(0, 1370, W, 1640))
        F.rect(230, 1364, 850, 1372, MAROON, alpha=out_expo(ph(t, 19.92, 0.2)))
    F.flash(FLASH, 0.85 * (1 - ph(t, 19.36, 0.08)))


# ---------------------------------------------------------------- S3  Jaws all on the floor (falling)
S3_ROW = layout_lines([["ALL", "ON", "THE"]], width=900, max_cap=260, cy=760, align="center")
S3_T = [20.62, 20.81, 20.96]

def drop(t, t_land, y_rest, fall=0.16, h0=-500):
    """y and squash for an object that lands at t_land."""
    if t < t_land:
        x = ph(t, t_land - fall, fall)
        return lerp(h0, y_rest, in_quad(x)), 1.0, 1.0
    sp = spring(t, t_land, 7, 9)
    return y_rest + 14 * sp, 1 + 0.16 * sp, 1 - 0.2 * sp

def s3(F, t):
    F.bg(BROWN)
    F.shake(t, [(20.22, 18), (20.62, 7), (20.81, 6), (20.96, 6), (21.08, 38)])
    knock = -40 * max(0.0, spring(t, 21.08, 4, 8)) if t >= 21.08 else 0
    # JAWS
    s = fit("JAWS", 760)
    y, sx, sy = drop(t, 20.22, 420)
    F.text("JAWS", s, 540, y + knock, CREAM, sx=sx, sy=sy)
    for (wd, size, x, yr), t0 in zip(S3_ROW, S3_T):
        if t > t0 - 0.2:
            y, sx, sy = drop(t, t0, yr, 0.13)
            F.text(wd, size, x, y + knock * 0.8, CREAM, sx=sx, sy=sy)
    # FLOOR lands at the bottom with a floor line
    if t > 21.08 - 0.15:
        s = fit("FLOOR", 960)
        y, sx, sy = drop(t, 21.08, 1260, 0.15, -700)
        F.text("FLOOR", s, 540, y, CREAM, sx=sx, sy=1.35 * sy)
    if t >= 21.08:
        k = out_expo(ph(t, 21.08, 0.18))
        F.rect(540 - 520 * k, 1545, 540 + 520 * k, 1561, CREAM)
        # dust chips
        for i in range(10):
            d = ph(t, 21.08, 0.4)
            dirx = (i - 4.5) / 4.5
            x = 540 + dirx * (200 + 520 * out_cubic(d))
            yy = 1530 - 220 * math.sin(math.pi * min(1, d * 1.2)) * (0.5 + 0.5 * abs(math.sin(i * 7.3)))
            if d < 1:
                F.rect(x - 7, yy - 7, x + 7, yy + 7, CREAM, alpha=1 - d)


# ---------------------------------------------------------------- S4  like Pam, like Tommy
def s4(F, t):
    F.bg(CREAM)
    F.cam["r"] = -2.5
    F.shake(t, [(21.45, 14), (21.92, 14)])
    # small vertical "LIKE"s
    for t0, x, y, r in [(21.28, 115, 640, -90), (21.69, 965, 1290, 90)]:
        if vis(t, t0):
            s = fit("LIKE", 230)
            F.text("LIKE", s, x, y, MAROON, sc=popin(t, t0), rot=r)
    if vis(t, 21.45):
        s = fit("PAM,", 700, 520)
        x = lerp(-700, 610, out_expo(ph(t, 21.43, 0.13)))
        F.text("PAM,", s, x, 640, MAROON, rot=-4)
    if vis(t, 21.69):
        F.rect(60, 958, 60 + 960 * out_expo(ph(t, 21.69, 0.2)), 966, MAROON)
    if vis(t, 21.92):
        s = fit("TOMMY", 720, 520)
        x = lerp(1800, 470, out_expo(ph(t, 21.90, 0.13)))
        F.text("TOMMY", s, x, 1290, MAROON, rot=-4)


# ---------------------------------------------------------------- S5  just burst in the door
def s5(F, t):
    F.bg(MAROON)
    tb = 22.84
    open_k = out_expo(ph(t, tb, 0.22))
    F.shake(t, [(22.36, 10), (tb, 40)])
    # revealed DOOR behind the panels
    if t >= tb - 0.01:
        s = fit("DOOR", 980)
        sc, _ = slam(t, tb + 0.02, 1.9, 0.15)
        F.text("DOOR", s, 540, 960, CREAM, sc=sc, sy=2.0)
        for i in range(14):
            d = ph(t, tb, 0.45)
            if d >= 1:
                continue
            a = i * 2 * math.pi / 14 + 0.3
            r = 120 + 900 * out_cubic(d)
            x, y = 540 + r * math.cos(a), 960 + r * math.sin(a) * 1.4
            F.rect(x - 10, y - 10, x + 10, y + 10, CREAM, alpha=1 - d)
    # two door panels with the words printed across them
    dx = 760 * open_k
    words = [("JUST", 22.20, 520, 520), ("BURST", 22.36, 860, 900), ("IN THE", 22.60, 560, 1300)]
    for side in (-1, 1):
        off = side * dx
        x0, x1 = (0, 540) if side < 0 else (540, W)
        if open_k >= 1:
            continue
        F.rect((x0 - 80 if side < 0 else x0) + off, -80, (x1 + 80 if side > 0 else x1) + off, H + 80, CREAM)
        F.rect((540 if side < 0 else 540) + off - 3, -50, 540 + off + 3, H + 50, MAROON, alpha=0.6)
        clip = ((x0 - 80 if side < 0 else x0) + off, -80, (x1 + 80 if side > 0 else x1) + off, H + 80)
        for wd, t0, width, y in words:
            if wd == "IN THE":
                if vis(t, 22.60):
                    s = fit("IN THE", width, 300)
                    F.text("IN", s, 540 - cap_w("IN THE", s) / 2 + cap_w("IN", s) / 2 + off, y,
                           MAROON, sc=popin(t, 22.60), clip=clip)
                if vis(t, 22.72):
                    s = fit("IN THE", width, 300)
                    F.text("THE", s, 540 + cap_w("IN THE", s) / 2 - cap_w("THE", s) / 2 + off, y,
                           MAROON, sc=popin(t, 22.72), clip=clip)
                continue
            if vis(t, t0):
                s = fit(wd, width, 400)
                sc, al = slam(t, t0, 1.5)
                F.text(wd, s, 540 + off, y, MAROON, sc=sc, alpha=al, clip=clip)
        # knob
        F.rect(540 + side * 40 + off - 8, 1060, 540 + side * 40 + off + 8, 1110, MAROON)


# ---------------------------------------------------------------- S6  and started whoopin' her ass worse than before
S6_W = [("AND", 23.08, 520, (-1, 0)), ("STARTED", 23.22, 900, (1, 0)),
        ("WHOOPIN’", 23.50, 980, (0, -1)), ("HER", 23.84, 620, (-1, 0))]

def s6(F, t):
    if 23.92 <= t < 24.20:
        F.bg(CREAM)
    else:
        F.bg(MAROON)
    hits = [(w[1], 22) for w in S6_W] + [(23.92, 48), (24.20, 14), (24.44, 10), (24.58, 16)]
    F.shake(t, hits, 1.3)
    if t < 23.92:
        for i, (wd, t0, width, (ddx, ddy)) in enumerate(S6_W):
            t1 = S6_W[i + 1][1] if i + 1 < len(S6_W) else 23.92
            if not (t0 - 0.06 <= t < t1 + 0.07):
                continue
            k = 1 - out_expo(ph(t, t0 - 0.05, 0.08))
            e = in_quad(ph(t, t1 - 0.01, 0.07))
            nx = S6_W[i + 1][3] if i + 1 < len(S6_W) else (0, 1)
            x = 540 + ddx * 1100 * k + nx[0] * 1300 * e
            y = 960 + ddy * 1300 * k + nx[1] * 1700 * e
            s = fit(wd, width, 560)
            rot = (8 if i % 2 else -8) * (1 - out_expo(ph(t, t0, 0.2))) + (3 if i % 2 else -3)
            F.text(wd, s, x, y, CREAM, rot=rot, sy=1.25)
    elif t < 24.20:
        s = fit("ASS", 940)
        sc, _ = slam(t, 23.92, 2.4, 0.1)
        jit = 4 * math.sin(t * 70)
        F.text("ASS", s, 540, 960, MAROON, sc=sc, rot=jit, sy=1.55)
        F.flash(FLASH, 0.8 * (1 - ph(t, 23.92, 0.07)))
    else:
        rows = layout_lines([["WORSE"], ["THAN"], ["BEFORE"]], width=900, max_cap=430, cy=960,
                            align="center")
        for (wd, s, x, y), t0, r in zip(rows, (24.20, 24.44, 24.58), (-6, 4, -3)):
            if vis(t, t0):
                sc, al = slam(t, t0, 1.7, 0.1)
                F.text(wd, s, x, y, CREAM, sc=sc, rot=r, alpha=al)


# ---------------------------------------------------------------- S7  they first were divorced
def s7(F, t):
    F.bg(CREAM)
    F.shake(t, [(25.50, 22), (25.64, 12)])
    row = layout_lines([["THEY", "FIRST", "WERE"]], width=820, max_cap=200, cy=560, align="center")
    for (wd, s, x, y), t0 in zip(row, (24.92, 25.08, 25.30)):
        if vis(t, t0):
            F.text(wd, s, x, y + 30 * (1 - out_expo(ph(t, t0 - 0.02, 0.1))), MAROON,
                   alpha=ph(t, t0 - 0.02, 0.05))
    if vis(t, 25.50):
        s = fit("DIVORCED,", 920)
        sc, al = slam(t, 25.50, 1.5, 0.1)
        k = out_expo(ph(t, 25.66, 0.25))
        sy = 1.25
        cy = 1060
        top_clip = (-200, 0, W + 200, cy)
        bot_clip = (-200, cy, W + 200, H)
        F.text("DIVORCED,", s, 540 - 70 * k, cy - 40 * k, MAROON, sc=sc, sy=sy, alpha=al,
               clip=(-200, 0 - 40 * k, W + 200, cy - 40 * k), rot=-2 * k)
        F.text("DIVORCED,", s, 540 + 70 * k, cy + 40 * k, MAROON, sc=sc, sy=sy, alpha=al,
               clip=(-200, cy + 40 * k, W + 200, H + 200), rot=2 * k)
        if k > 0:
            F.rect(80, cy - 3, 80 + 920 * k, cy + 3, MAROON)


# ---------------------------------------------------------------- S8  throwin' her over furniture (agh!)
def s8(F, t):
    F.bg(BROWN)
    if 26.88 <= t < 26.95:
        F.bg(MAROON)
    F.shake(t, [(25.98, 10), (26.45, 26), (26.88, 34)])
    # THROWIN' thrown along an arc
    s = fit("THROWIN’", 900, 330)
    x_ = ph(t, 25.80, 0.18)
    x = lerp(-500, 540, out_cubic(x_))
    y = lerp(1500, 430, out_cubic(x_)) - 260 * math.sin(math.pi * x_) * (1 - x_)
    rot = lerp(-200, -4, out_cubic(x_))
    F.text("THROWIN’", s, x, y, CREAM, rot=rot)
    if vis(t, 26.00):
        sh = fit("HER", 260)
        F.text("HER", sh, 210, 720, CREAM, sc=popin(t, 26.00))
    if vis(t, 26.17):
        so = fit("OVER", 480)
        k = ph(t, 26.13, 0.16)
        x = lerp(360, 720, out_cubic(k))
        y = 720 - 220 * math.sin(math.pi * k)
        F.text("OVER", so, x, y, CREAM, rot=lerp(-30, 0, out_cubic(k)))
    if vis(t, 26.45):
        sf = fit("FURNITURE", 940)
        k = ph(t, 26.40, 0.12)
        y = lerp(2300, 1070, out_expo(k))
        rot = -4 + 14 * spring(t, 26.45, 3.5, 7) if t >= 26.45 else 40
        F.text("FURNITURE", sf, 540, y, CREAM, rot=rot, sy=1.3)
    if vis(t, 26.88):
        sa = fit("(AGH!)", 560)
        sc, al = slam(t, 26.88, 2.2, 0.09)
        F.text("(AGH!)", sa, 560, 1480, CREAM, sc=sc, alpha=al, rot=8 + 5 * spring(t, 26.88, 6, 5))
        F.flash(FLASH, 0.35 * (1 - ph(t, 26.88, 0.06)))


# ---------------------------------------------------------------- S9  it's the return of the
def s9(F, t):
    F.bg(MAROON)
    F.cam["r"] = 2.0 * ph(t, 27.2, 0.9)
    F.shake(t, [(27.52, 16)])
    top = layout_lines([["IT’S", "THE"]], width=520, max_cap=200, cy=600, align="center")
    for (wd, s, x, y), t0 in zip(top, (27.20, 27.40)):
        if vis(t, t0):
            F.text(wd, s, x, y, CREAM, sc=popin(t, t0))
    if vis(t, 27.50):
        s = fit("RETURN", 940)
        k = out_expo(ph(t, 27.48, 0.2))
        x = lerp(1700, 540, k)
        # rewind ghost trail
        for g in range(4, 0, -1):
            gx = x + g * 160 * (1 - k)
            F.text("RETURN", s, gx, 960, TAN, alpha=0.18 * (5 - g) * (1 - k), sy=1.2)
        F.text("RETURN", s, x, 960, CREAM, sy=1.2)
    bot = layout_lines([["OF", "THE"]], width=420, max_cap=200, cy=1330, align="center")
    for (wd, s, x, y), t0 in zip(bot, (27.84, 27.96)):
        if vis(t, t0):
            F.text(wd, s, x, y, CREAM, sc=popin(t, t0))


# ---------------------------------------------------------------- S10  "oh, wait, no way, you're kidding
def s10(F, t):
    if t < 28.40:                      # OH, bouncing
        F.bg(CREAM)
        s = fit("“OH,", 760)
        F.text("“OH,", s, 540, 960, MAROON, sc=popin(t, 28.16, 0.22),
               rot=6 * spring(t, 28.16, 3, 4))
    elif t < 28.76:                    # WAIT: dead still comic pause
        F.bg(BLACK)
        s = fit("WAIT,", 520)
        F.text("WAIT,", s, 540, 960, CREAM)
    elif t < 29.00:                    # hard static cuts
        F.bg(CREAM)
        F.text("NO", fit("NO", 760), 540, 960, MAROON)
    elif t < 29.24:
        F.bg(MAROON)
        F.text("WAY,", fit("WAY,", 960), 540, 960, CREAM)
    else:
        F.bg(CREAM)
        s = fit("YOU’RE", 560)
        F.text("YOU’RE", s, 540, 640, MAROON)
        if vis(t, 29.44):
            sk = fit("KIDDING", 980)
            def wob(i, n):
                d = t - 29.44
                if d < -0.02:
                    return None
                return dict(dy=-26 * abs(math.sin(d * 16 + i * 0.9)) * math.exp(-d * 1.2),
                            rot=7 * math.sin(d * 14 + i * 1.3) * math.exp(-d * 1.2),
                            sc=out_back(ph(t, 29.42 + i * 0.012, 0.12)))
            F.letters("KIDDING", sk, 540, 1080, MAROON, wob)


# ---------------------------------------------------------------- S11  he didn't just say what I think he did, did he?
S11 = [["HE", "DIDN’T"], ["JUST", "SAY"], ["WHAT", "I", "THINK"], ["HE", "DID,"], ["DID", "HE?”"]]
S11_T = [29.92, 30.08, 30.42, 30.64, 30.84, 31.00, 31.12, 31.34, 31.48, 31.76, 31.96]
S11_L = layout_lines(S11, width=860, max_cap=270, cy=960, line_gap=30)
S11_C = ((S11_L[9][2] + S11_L[10][2]) / 2, S11_L[9][3])

def s11(F, t):
    F.bg(MAROON)
    F.cam["z"] = 1.0 + 0.08 * in_out(ph(t, 29.9, 2.3))
    last = ph(t, 31.94, 0.14)
    for i, ((wd, s, x, y), t0) in enumerate(zip(S11_L, S11_T)):
        if not vis(t, t0):
            continue
        k = popin(t, t0, 0.15)
        dy = 50 * (1 - clamp(k))
        al = 1.0
        rot = 0.0
        sc = k
        if i >= 9:     # "DID HE?" - final punch, rotate the line as a group
            rot = -6 * out_expo(last)
            g = 1 + 0.12 * out_expo(last)
            sc *= g
            cx, cy = S11_C
            a = math.radians(rot)
            px, py = (x - cx) * g, (y - cy) * g
            x = cx + px * math.cos(a) - py * math.sin(a)
            y = cy + px * math.sin(a) + py * math.cos(a)
        elif last > 0:
            al = 1 - 0.6 * last
        F.text(wd, s, x, y + dy, CREAM, sc=sc, alpha=al, rot=rot)
    F.shake(t, [(31.96, 12)])


# ---------------------------------------------------------------- S12  and Dr. Dre said  (mask wipes)
def s12(F, t):
    F.bg(CREAM)
    F.cam["z"] = 1 + 0.05 * in_out(ph(t, 33.25, 0.4))
    F.shake(t, [(32.84, 14)])
    if vis(t, 32.24):
        s = fit("AND", 260)
        k = out_expo(ph(t, 32.22, 0.14))
        F.text("AND", s, 540, 430, MAROON, clip=(400, 0, 400 + 300 * k, 600))
    if vis(t, 32.44):
        s = fit("DR.", 420)
        k = out_expo(ph(t, 32.42, 0.14))
        F.text("DR.", s, 540, 680, MAROON, clip=(0, 840 - 330 * k, W, 840))
    if vis(t, 32.84):
        s = fit("DRE", 800)
        k = out_expo(ph(t, 32.82, 0.16))
        top = 880
        bot = top + cap_h(s) * 1.1
        edge = lerp(top, bot + 40, k)
        F.text("DRE", s, 540, (top + bot) / 2, MAROON, sy=1.1, clip=(0, top - 40, W, edge))
        if k < 1:
            F.rect(40, edge - 10, 1040, edge + 10, MAROON)
    if vis(t, 33.20):
        s = fit("SAID", 400)
        k = out_expo(ph(t, 33.18, 0.14))
        F.text("SAID", s, 540, 1610, MAROON, clip=(1040 - 1000 * k, 1460, 1040, 1720))


# ---------------------------------------------------------------- S13  nothing, you idiots (letters assemble / explode)
def s13(F, t):
    F.bg(BROWN)
    F.shake(t, [(33.65, 10), (34.16, 14), (34.32, 26)])
    s = fit("NOTHING,", 960)
    ex = ph(t, 34.14, 0.35)

    def assemble(i, n):
        a = ph(t, 33.56 + i * 0.012, 0.15)
        if a <= 0:
            return None
        seed = i * 2.39 + 1
        k = 1 - out_expo(a)
        e = out_cubic(ex)
        return dict(dx=math.cos(seed * 3) * 700 * k + math.cos(seed * 5) * 900 * e,
                    dy=math.sin(seed * 4) * 900 * k + (math.sin(seed * 7) * 700 - 300) * e,
                    rot=(math.sin(seed) * 120) * k + math.sin(seed * 9) * 200 * e,
                    alpha=1 - ex)
    if ex < 1:
        F.letters("NOTHING,", s, 540, 960 - 80 * out_cubic(ex), CREAM, assemble)
    if vis(t, 34.16):
        sy = fit("YOU", 360)
        F.text("YOU", sy, 540, 640, CREAM, sc=popin(t, 34.16, 0.12))
    if vis(t, 34.32):
        si = fit("IDIOTS,", 940)
        sc, al = slam(t, 34.32, 2.0, 0.1)
        F.text("IDIOTS,", si, 540, 1100, CREAM, sc=sc, alpha=al, rot=-5, sy=1.3)


# ---------------------------------------------------------------- S14  Dr. Dre's DEAD
def s14(F, t):
    F.bg(BLACK)
    F.shake(t, [(34.80, 6), (35.10, 8), (35.36, 52)])
    knock = -90 * out_expo(ph(t, 35.36, 0.12))
    row = layout_lines([["DR.", "DRE’S"]], width=640, max_cap=220, cy=330, align="center")
    for (wd, s, x, y), t0 in zip(row, (34.80, 35.10)):
        if vis(t, t0):
            F.text(wd, s, x, y + knock, CREAM, sc=popin(t, t0, 0.12))
    if vis(t, 35.36):
        s = fit("DEAD", 950)
        sc, al = slam(t, 35.36, 3.2, 0.1)
        F.text("DEAD", s, 540, 1060, CREAM, sc=sc, alpha=al, sy=1.75)
        F.flash(FLASH, 0.9 * (1 - ph(t, 35.36, 0.09)))
        for y in (560, 1560):
            w = 520 * out_expo(ph(t, 35.40, 0.2))
            F.rect(540 - w, y - 6, 540 + w, y + 6, CREAM)


# ---------------------------------------------------------------- S15  he's locked in my basement (ha-ha!)
def s15(F, t):
    F.bg(MAROON)
    F.shake(t, [(35.80, 8), (36.32, 22), (36.46, 14)])
    rows = layout_lines([["HE’S", "LOCKED"], ["IN", "MY"]], width=760, max_cap=230, cy=520,
                        align="center", line_gap=26)
    for (wd, s, x, y), t0 in zip(rows, (35.64, 35.80, 36.04, 36.16)):
        if vis(t, t0):
            F.text(wd, s, x, y, CREAM, sc=popin(t, t0, 0.12))
    # the box draws itself (perimeter animation)
    x0, y0, x1, y1 = 70, 880, 1010, 1300
    lock = out_back(ph(t, 36.44, 0.14), 3) if t >= 36.44 else 0
    pad = 40 * (1 - lock)
    bx0, by0, bx1, by1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    per = 2 * ((bx1 - bx0) + (by1 - by0))
    k = out_cubic(ph(t, 35.80, 0.45))
    if k > 0:
        pts = [[bx0, by0], [bx1, by0], [bx1, by1], [bx0, by1], [bx0, by0]]
        L = k * per
        path = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            seg = math.dist(a, b)
            if L <= 0:
                break
            f = min(1, L / seg)
            path.append([a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f])
            L -= seg
        F.poly(path, CREAM, thick=12, closed=False)
    if vis(t, 36.32):
        s = fit("BASEMENT", 860, 330)
        k2 = ph(t, 36.20, 0.12)
        y = lerp(y0 - 400, (y0 + y1) / 2, in_quad(k2)) + 10 * spring(t, 36.32, 7, 9)
        F.text("BASEMENT", s, 540, y, CREAM, clip=(bx0 + 6, by0 + 6, bx1 - 6, by1 - 6))
    if lock > 0:   # lock bars snap across
        for xx in (230, 540, 850):
            hgt = (by1 - by0) * min(1, lock)
            F.rect(xx - 4, by0, xx + 4, by0 + hgt, CREAM, alpha=0.85)
        F.rect(500, by1 - 6, 580, by1 + 60, CREAM)     # padlock body
        F.poly([[515, by1 - 6], [515, by1 - 40], [565, by1 - 40], [565, by1 - 6]], CREAM,
               thick=10, closed=False)
    if vis(t, 36.62):
        s = fit("(HA-HA!)", 440)
        F.text("(HA-HA!)", s, 560, 1560, CREAM, sc=popin(t, 36.62, 0.12),
               rot=-8 + 7 * math.sin((t - 36.62) * 30))


# ---------------------------------------------------------------- S16  feminist women love EMINEM
def s16(F, t):
    F.bg(CREAM)
    F.shake(t, [(38.00, 18)])
    # repeating outline pattern after EMINEM lands
    if t >= 38.0:
        sp = fit("EMINEM", 560)
        a = 0.35 * ph(t, 38.0, 0.1)
        for r in range(-1, 9):
            dirn = 1 if r % 2 else -1
            off = ((t - 38.0) * 420 * dirn) % 600
            for c in range(-1, 3):
                F.text("EMINEM", sp, c * 600 + off, 120 + r * 240, TAN, outline=3, alpha=a)
    if vis(t, 36.95):
        s = fit("FEMINIST", 900)
        k = out_expo(ph(t, 36.93, 0.13))
        F.text("FEMINIST", s, lerp(-500, 540, k), 410, MAROON, clip=(0, 200, W, 620))
    if vis(t, 37.30):
        s = fit("WOMEN", 760)
        k = out_expo(ph(t, 37.28, 0.13))
        F.text("WOMEN", s, lerp(1600, 540, k), 720, MAROON)
    if vis(t, 37.76):
        s = fit("LOVE", 300)
        F.text("LOVE", s, 540, 960, MAROON, sc=popin(t, 37.76, 0.13), rot=-7)
    if vis(t, 37.96):
        s = fit("EMINEM", 960)

        def dropin(i, n):
            a = ph(t, 37.96 + i * 0.025 - 0.12, 0.12)
            if a <= 0:
                return None
            return dict(dy=-900 * (1 - in_quad(a)) + (16 * spring(t, 37.96 + i * 0.025, 7, 9)),
                        rot=(i - 2.5) * 3 * (1 - a))
        F.letters("EMINEM", s, 540, 1300, MAROON, dropin)


# ---------------------------------------------------------------- S17  "chicka-chicka-chicka, SLIM SHADY + outro
CHK = [(38.50, "“CHICKA-", 500, -7, MAROON), (38.82, "CHICKA-", 900, 5, BLACK),
       (39.12, "CHICKA,", 1300, -3, BROWN)]

def s17(F, t):
    if t < 39.40:
        cur = [c for c in CHK if t >= c[0] - 0.02]
        F.bg(cur[-1][4] if cur else MAROON)
        F.shake(t, [(c[0], 20) for c in CHK], 1.4)
        for t0, wd, y, r, _ in cur:
            s = fit(wd, 900, 270)
            sc, al = slam(t, t0, 1.9, 0.09)
            side = -1 if r < 0 else 1
            x = 540 + side * 900 * (1 - out_expo(ph(t, t0 - 0.03, 0.09)))
            F.text(wd, s, x, y, CREAM, sc=sc, alpha=al, rot=r)
        return
    F.bg(CREAM)
    F.shake(t, [(39.40, 26), (39.68, 34)])
    outro = ph(t, T_AUDIO_END, T_END - T_AUDIO_END)
    F.cam["z"] = 1 - 0.12 * out_cubic(outro)
    s1_ = fit("SLIM", 820)
    s2_ = fit("SHADY", 960)
    # echo copies expanding with the audio echo
    if t >= T_AUDIO_END - 0.05:
        for g in range(3):
            e = ph(t, T_AUDIO_END + g * 0.29, 0.6)
            if 0 < e < 1:
                F.text("SLIM", s1_, 540, 700, TAN, sc=1 + 0.5 * out_cubic(e), outline=4, alpha=1 - e)
                F.text("SHADY", s2_, 540, 1240, TAN, sc=1 + 0.5 * out_cubic(e), outline=4,
                       alpha=1 - e)
    sc, al = slam(t, 39.40, 2.0, 0.1)
    y = lerp(-300, 700, out_expo(ph(t, 39.37, 0.1)))
    F.text("SLIM", s1_, 540, y, MAROON, sc=sc, alpha=al, sy=1.2)
    if vis(t, 39.68):
        sc, al = slam(t, 39.68, 2.0, 0.1)
        y = lerp(2300, 1240, out_expo(ph(t, 39.65, 0.1)))
        F.text("SHADY", s2_, 540, y, MAROON, sc=sc, alpha=al, sy=1.35)
        F.flash(FLASH, 0.7 * (1 - ph(t, 39.68, 0.07)))
    # outro: final fade to maroon
    F.flash(MAROON, in_out(ph(t, T_END - 0.42, 0.42)))


SCENES = [(T_START, s1), (19.34, s2), (20.18, s3), (21.24, s4), (22.18, s5), (23.04, s6),
          (24.88, s7), (25.80, s8), (27.16, s9), (28.12, s10), (29.88, s11), (32.20, s12),
          (33.54, s13), (34.76, s14), (35.62, s15), (36.90, s16), (38.46, s17)]

def scene_at(t):
    cur = SCENES[0][1]
    for t0, fn in SCENES:
        if t >= t0:
            cur = fn
    return cur


def chrome(F, t, scene):
    """Persistent minimal decoration: star at the bottom + tiny EMINEM tag."""
    bgc = F.img[H - 10, 5]
    dark = bgc.mean() < 0.5
    col = CREAM if dark else MAROON
    frozen = scene is s10 and 28.40 <= t < 29.24
    rot = 0 if frozen else (t - T_START) * 40
    if t < T_END - 0.42:
        F.star(540, 1745, 22, col, rot=rot, alpha=0.95)
    if 17.9 <= t < T_END - 0.42 and scene is not s16:
        F.text("EMINEM", 44, 540, 175, col, alpha=0.75 * ph(t, 17.9, 0.2))
        F.rect(330, 173, 450, 176, col, alpha=0.6)
        F.rect(630, 173, 750, 176, col, alpha=0.6)


def render(t):
    F = Frame()
    sc = scene_at(t)
    sc(F, t)
    cam = dict(F.cam)
    F.cam = dict(dx=0.0, dy=0.0, z=1.0, r=0.0)
    chrome(F, t, sc)
    F.cam = cam
    return F.img
