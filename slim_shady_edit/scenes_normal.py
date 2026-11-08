"""Jon Lajoie — Everyday Normal Guy 2: lyric edit timeline (absolute track seconds).

Word times: sherpa-onnx ASR word timestamps + vocal-band energy; tempo ~89 BPM (0.67 s / beat).
"""
import math

from engine import (BLACK, BROWN, CREAM, FLASH, MAROON, TAN, W, H, Frame, cap_h, cap_w, clamp,
                    fit, in_cubic, in_out, in_quad, layout_lines, lerp, out_back, out_cubic,
                    out_expo, ph, spring)

T_START = 67.52
T_AUDIO_END = 88.84
T_END = 89.95
ECHO_FROM = 88.26     # "Ghostbusters"
ECHO_DELAY = 0.335    # half a beat at 89 BPM
OUT_NAME = "everyday_normal_guy_lyric_edit"
MF = "MOTHER*UCKER"
# "-fucker" spans to remove from the vocal band in the audio
CENSOR = []   # audio left uncensored


def slam(t, t0, frm=1.6, d=0.11):
    x = ph(t, t0 - 0.03, d)
    return lerp(frm, 1.0, out_expo(x)), clamp((t - t0 + 0.03) / 0.035)

def popin(t, t0, d=0.16):
    x = ph(t, t0 - 0.02, d)
    return max(0.0, out_back(x, 2.2)) if x > 0 else 0.0

def vis(t, t0):
    return t >= t0 - 0.02

def circle(F, x, y, r, col, alpha=1.0, thick=0):
    pts = [[x + r * math.cos(a * math.pi / 32), y + r * math.sin(a * math.pi / 32)] for a in range(64)]
    F.poly(pts, col, alpha, thick)

def pops(F, t, items, col, mode="pop"):
    """items: (word, size, x, y, t0)."""
    for wd, s, x, y, t0 in items:
        if not vis(t, t0):
            continue
        if mode == "pop":
            F.text(wd, s, x, y, col, sc=popin(t, t0, 0.13))
        elif mode == "slam":
            sc, al = slam(t, t0, 1.6, 0.1)
            F.text(wd, s, x, y, col, sc=sc, alpha=al)
        elif mode == "rise":
            k = out_expo(ph(t, t0 - 0.02, 0.12))
            F.text(wd, s, x, y + 120 * (1 - k), col, alpha=k)

def lay(lines, times, **kw):
    L = layout_lines(lines, **kw)
    return [(w, s, x, y, t0) for (w, s, x, y), t0 in zip(L, times)]


# ---------------------------------------------------------------- A  Yo, what can I say?
A_ROWS = lay([["WHAT", "CAN"], ["I", "SAY?"]], [67.88, 68.08, 68.24, 68.44], width=860,
             max_cap=300, cy=1180, align="center")

def sA(F, t):
    F.bg(MAROON)
    F.shake(t, [(67.64, 24), (68.44, 10)])
    s = fit("YO,", 760)
    up = out_expo(ph(t, 67.86, 0.16))
    sc, al = slam(t, 67.64, 2.4, 0.12)
    F.text("YO,", s, 540, lerp(960, 520, up), CREAM, sc=sc * lerp(1, 0.62, up), alpha=al,
           rot=-6 * up)
    pops(F, t, A_ROWS, CREAM)


# ---------------------------------------------------------------- B  It's just a day in my life
B_ROWS = lay([["IT’S", "JUST", "A"], ["DAY", "IN", "MY"]], [68.68, 68.88, 69.08, 69.20, 69.44, 69.56],
             width=700, max_cap=200, cy=520, align="center")

def sB(F, t):
    F.bg(CREAM)
    F.shake(t, [(69.76, 26)])
    pops(F, t, B_ROWS, MAROON, "rise")
    # "day" timeline: a sun dot travels along a line
    k = ph(t, 68.68, 1.32)
    F.rect(90, 1530, 990, 1536, MAROON, alpha=0.8)
    for i in range(7):
        F.rect(90 + i * 150 - 3, 1515, 90 + i * 150 + 3, 1550, MAROON, alpha=0.8)
    circle(F, lerp(90, 990, in_out(k)), 1533, 26, MAROON)
    if vis(t, 69.76):
        s = fit("LIFE", 720)
        sc, al = slam(t, 69.76, 2.2, 0.11)
        F.text("LIFE", s, 540, 1110, MAROON, sc=sc, alpha=al, sy=1.25)
        F.flash(FLASH, 0.6 * (1 - ph(t, 69.76, 0.07)))


# ---------------------------------------------------------------- C  I'm up early in the morning,
def sC(F, t):
    F.bg(CREAM)
    F.shake(t, [(70.48, 14)])
    # rising sun behind the words
    k = out_cubic(ph(t, 70.0, 1.4))
    circle(F, 540, lerp(1900, 1250, k), 330, TAN)
    for i in range(12):
        a = i * math.pi / 6 + t * 0.6
        r0, r1 = 380, 380 + 90 * k
        cy = lerp(1900, 1250, k)
        F.poly([[540 + r0 * math.cos(a), cy + r0 * math.sin(a)],
                [540 + r1 * math.cos(a), cy + r1 * math.sin(a)]], TAN, thick=12, closed=False)
    for wd, x, t0 in (("I’M", 330, 70.04), ("UP", 700, 70.28)):
        if vis(t, t0):
            s = fit("I’M UP", 640, 240)
            kk = out_expo(ph(t, t0 - 0.02, 0.14))
            off = 0 if wd == "UP" else 0
            F.text(wd, s, x + off, lerp(900, 430, kk), MAROON, alpha=kk)
    if vis(t, 70.48):
        s = fit("EARLY", 940)
        sc, al = slam(t, 70.48, 1.8, 0.1)
        F.text("EARLY", s, 540, 780, MAROON, sc=sc, alpha=al, sy=1.2)
    row = lay([["IN", "THE", "MORNING,"]], [70.88, 71.04, 71.20], width=880, max_cap=220, cy=1150,
              align="center")
    pops(F, t, row, MAROON)


# ---------------------------------------------------------------- D  in bed early at night
def sD(F, t):
    F.bg(BLACK)
    for i in range(16):   # night sky
        x = (i * 263) % 1000 + 40
        y = (i * 151) % 700 + 260
        a = ph(t, 71.5 + i * 0.03, 0.2) * (0.5 + 0.5 * math.sin(t * 6 + i))
        F.star(x, y, 9 + (i % 3) * 4, CREAM, rot=i * 20, alpha=a)
    F.shake(t, [(72.44, 18)])
    if vis(t, 71.52):
        F.text("IN", fit("IN", 130), 200, 620, CREAM, sc=popin(t, 71.52))
    if vis(t, 71.68):
        s = fit("BED", 520)
        lie = out_back(ph(t, 71.80, 0.25), 1.4)
        if lie <= 0:
            F.text("BED", s, 620, 640, CREAM, sc=popin(t, 71.68))
        else:   # the word "lies down" in bed
            F.text("BED", s, 620, 640 + 40 * lie, CREAM, rot=lerp(0, 8, lie), sy=lerp(1, 0.55, lie))
        if lie > 0:   # the "pillow"
            F.rect(340, 760, 860, 776, CREAM, alpha=min(1, lie))
    row = lay([["EARLY", "AT"]], [71.88, 72.20], width=700, max_cap=230, cy=1000, align="center")
    pops(F, t, row, CREAM)
    if vis(t, 72.44):
        s = fit("NIGHT", 960)
        sc, al = slam(t, 72.44, 1.9, 0.1)
        F.text("NIGHT", s, 540, 1340, CREAM, sc=sc, alpha=al, sy=1.2)


# ---------------------------------------------------------------- E  to be productive at work,
def sE(F, t):
    F.bg(BROWN)
    F.shake(t, [(73.60, 8), (73.84, 22)])
    row = lay([["TO", "BE"]], [72.68, 72.80], width=360, max_cap=200, cy=520, align="center")
    pops(F, t, row, CREAM)
    if vis(t, 73.04):
        s = fit("PRODUCTIVE", 960)
        n = len("PRODUCTIVE")

        def build(i, _n):
            a = ph(t, 73.02 + i * 0.04, 0.08)
            if a <= 0:
                return None
            return dict(dy=-60 * (1 - out_expo(a)), alpha=a)
        F.letters("PRODUCTIVE", s, 540, 860, CREAM, build)
        # progress bar fills with the word
        k = ph(t, 73.02, 0.04 * n + 0.1)
        F.rect(60, 1060, 1020, 1100, CREAM, thick=6)
        F.rect(72, 1072, 72 + 936 * out_cubic(k), 1088, CREAM)
    row = lay([["AT", "WORK,"]], [73.60, 73.84], width=760, max_cap=360, cy=1400, align="center")
    pops(F, t, row, CREAM, "slam")


# ---------------------------------------------------------------- F  I gotta be well rested
def sF(F, t):
    F.bg(CREAM)
    F.cam["z"] = 1 + 0.06 * in_out(ph(t, 75.16, 0.8))
    row = lay([["I", "GOTTA", "BE"]], [74.08, 74.24, 74.60], width=760, max_cap=230, cy=470,
              align="center")
    pops(F, t, row, MAROON)
    if vis(t, 74.88):
        s = fit("WELL", 560)
        F.text("WELL", s, 540, 760, MAROON, sc=popin(t, 74.88, 0.15))
    if vis(t, 75.16):
        s = fit("RESTED", 960)
        k = ph(t, 75.14, 0.5)                     # slow, sleepy settle
        F.text("RESTED", s, 540, lerp(1000, 1180, out_cubic(k)), MAROON, alpha=clamp(k * 4),
               rot=lerp(-10, 3, out_cubic(k)), sy=1.2)
        for i, (dx, dy) in enumerate(((330, -170), (400, -260), (480, -360))):   # z z z
            a = ph(t, 75.40 + i * 0.12, 0.15)
            if a > 0:
                F.text("Z", 70 + i * 30, 540 + dx, 1180 + dy - 20 * math.sin(t * 4 + i), MAROON,
                       alpha=a, rot=-12)


# ---------------------------------------------------------------- G  Yeah, motherfucker, you heard what I just said
def sG(F, t):
    F.bg(MAROON if t < 77.0 else BLACK)
    F.shake(t, [(75.92, 14), (76.16, 34), (78.0, 10)], 1.3)
    if t < 77.0:
        if vis(t, 75.92):
            s = fit("YEAH,", 560)
            F.text("YEAH,", s, 540, 480, CREAM, sc=popin(t, 75.92, 0.12), rot=-5)
        if vis(t, 76.16):
            s = fit("MOTHER-", 960)
            sc, al = slam(t, 76.16, 2.2, 0.1)
            F.text("MOTHER-", s, 540, 900, CREAM, sc=sc, alpha=al, rot=-3)
            s2 = fit("*UCKER,", 960)
            sc, al = slam(t, 76.40, 2.2, 0.1)
            if vis(t, 76.40):
                F.text("*UCKER,", s2, 540, 1290, CREAM, sc=sc, alpha=al, rot=3)
            F.flash(FLASH, 0.5 * (1 - ph(t, 76.16, 0.06)))
        return
    rows = lay([["YOU", "HEARD"], ["WHAT", "I"], ["JUST", "SAID"]],
               [77.04, 77.22, 77.48, 77.68, 77.84, 78.00], width=880, max_cap=330, cy=960,
               align="center", line_gap=30)
    for i, (wd, s, x, y, t0) in enumerate(rows):
        if vis(t, t0):
            d = -1 if i % 2 == 0 else 1
            k = out_expo(ph(t, t0 - 0.03, 0.1))
            F.text(wd, s, x + d * 900 * (1 - k), y, CREAM)


# ---------------------------------------------------------------- H  I'm just a regular everyday normal motherfucker (#1: ID card)
def id_card(F, t, items, col, bgc):
    x0, x1 = 70, 1010
    k = out_expo(ph(t, 78.15, 0.2))
    F.rect(x0, lerp(1900, 360, k), x1, lerp(2900, 1560, k), col, thick=10)
    if k < 0.98:
        return
    F.rect(x0, 360, x1, 470, col)
    F.text("I’M JUST A", fit("I’M JUST A", 420), 540, 415, bgc, alpha=ph(t, 78.22, 0.05))
    for y in (760, 1030, 1300):
        F.rect(x0 + 40, y, x1 - 40, y + 4, col, alpha=0.6)

def sH(F, t):
    F.bg(CREAM)
    F.shake(t, [(78.52, 12), (79.24, 12), (79.80, 12), (80.20, 26)])
    id_card(F, t, None, MAROON, CREAM)
    for wd, y, t0, wdt in (("REGULAR", 630, 78.52, 860), ("EVERYDAY", 900, 79.24, 860),
                           ("NORMAL", 1170, 79.80, 760), (MF, 1440, 80.20, 880)):
        if vis(t, t0):
            s = fit(wd, min(wdt, 780), 210)
            # "stamped" into the form
            sc, al = slam(t, t0, 1.45, 0.09)
            F.text(wd, s, 590, y, MAROON, sc=sc, alpha=al)
            if wd == MF:
                F.flash(FLASH, 0.4 * (1 - ph(t, t0, 0.06)))
    # tick boxes
    for i, t0 in enumerate((78.52, 79.24, 79.80, 80.20)):
        y = 560 + i * 270
        F.rect(108, y, 148, y + 40, MAROON, thick=5)
        if vis(t, t0):
            F.poly([[114, y + 20], [126, y + 34], [146, y + 4]], MAROON, thick=7, closed=False)


# ---------------------------------------------------------------- I  I don't like margarine,
def sI(F, t):
    F.bg(BLACK)
    F.shake(t, [(81.48, 14), (81.86, 30)])
    row = lay([["I", "DON’T", "LIKE"]], [80.72, 80.96, 81.24], width=760, max_cap=250, cy=640,
              align="center")
    pops(F, t, row, CREAM, "rise")
    if vis(t, 81.48):
        s = fit("MARGARINE,", 960)
        sc, al = slam(t, 81.48, 1.5, 0.1)
        rej = out_expo(ph(t, 81.86, 0.12))
        F.text("MARGARINE,", s, 540 + 14 * math.sin(t * 60) * rej * (1 - ph(t, 81.86, 0.3)), 1000,
               CREAM, sc=sc, alpha=al * (1 - 0.45 * rej))
        if rej > 0:     # struck out
            F.poly([[60, 1080], [60 + 960 * rej, 1080 - 150 * rej]], CREAM, thick=26, closed=False)


# ---------------------------------------------------------------- J  I much prefer the taste of butter
def sJ(F, t):
    F.bg(CREAM)
    F.shake(t, [(83.30, 16)])
    rows = lay([["I", "MUCH", "PREFER"], ["THE", "TASTE", "OF"]],
               [82.08, 82.20, 82.40, 82.68, 82.84, 83.16], width=820, max_cap=210, cy=600,
               align="center", line_gap=26)
    pops(F, t, rows, MAROON)
    if vis(t, 83.30):
        s = fit("BUTTER", 820)
        k = ph(t, 83.22, 0.1)
        y = lerp(-300, 1200, in_quad(k))
        j = spring(t, 83.32, 4.5, 4.5)       # soft jelly wobble, like a block of butter
        bw, bh = 470 * (1 + 0.15 * j), 210 * (1 - 0.18 * j)
        F.rect(540 - bw - 30, y - bh - 20, 540 + bw + 30, y + bh + 20, TAN)
        F.rect(540 - bw - 30, y - bh - 20, 540 + bw + 30, y + bh + 20, MAROON, thick=8)
        F.text("BUTTER", s, 540, y, MAROON, sx=1 + 0.15 * j, sy=1.2 * (1 - 0.18 * j))


# ---------------------------------------------------------------- K  I'm just a regular everyday normal motherfucker (#2: fly-ins + pattern)
def sK(F, t):
    F.bg(MAROON)
    F.shake(t, [(83.88, 16), (84.56, 16), (85.16, 16), (85.52, 34)], 1.3)
    sp = fit("NORMAL", 460)
    for r in range(-1, 10):
        dirn = 1 if r % 2 else -1
        off = ((t - 83.5) * 300 * dirn) % 520
        for c in range(-1, 3):
            F.text("NORMAL", sp, c * 520 + off, 100 + r * 200, BROWN, outline=3, alpha=0.5)
    row = lay([["I’M", "JUST", "A"]], [83.55, 83.66, 83.78], width=520, max_cap=180, cy=400,
              align="center")
    pops(F, t, row, CREAM)
    for i, (wd, y, t0, wdt, r) in enumerate((("REGULAR", 680, 83.88, 900, -4),
                                             ("EVERYDAY", 940, 84.56, 940, 3),
                                             ("NORMAL", 1200, 85.16, 800, -3),
                                             (MF, 1450, 85.52, 960, 2))):
        if vis(t, t0):
            s = fit(wd, wdt, 230)
            d = -1 if i % 2 == 0 else 1
            k = out_expo(ph(t, t0 - 0.04, 0.1))
            F.text(wd, s, 540 + d * 1100 * (1 - k), y, CREAM, rot=r)


# ---------------------------------------------------------------- L  my favorite movies as a kid were Superman and Ghostbusters
def film_strip(F, t, col):
    off = (t * 260) % 120
    for x0 in (20, 1000):
        F.rect(x0, -10, x0 + 60, H + 10, col)
        for i in range(-1, 18):
            y = i * 120 + off
            F.rect(x0 + 16, y, x0 + 44, y + 60, CREAM if col is not CREAM else MAROON)

def sL(F, t):
    if t < 87.50:
        F.bg(CREAM)
        film_strip(F, t, MAROON)
        rows = lay([["MY"], ["FAVORITE"], ["MOVIES"]], [85.96, 86.16, 86.56], width=820,
                   max_cap=360, cy=760, align="center")
        pops(F, t, rows, MAROON, "slam")
        row = lay([["AS", "A", "KID", "WERE"]], [86.92, 87.08, 87.20, 87.40], width=760,
                  max_cap=170, cy=1380, align="center")
        pops(F, t, row, MAROON)
        F.shake(t, [(86.16, 10), (86.56, 10)])
        return
    if t < 88.26:
        # SUPERMAN flies up through the frame with speed lines
        F.bg(MAROON)
        F.shake(t, [(87.56, 18)])
        for i in range(14):
            x = 60 + (i * 197) % 960
            y = ((i * 331) - (t - 87.5) * 5200) % 2400 - 200
            F.rect(x, y, x + 6, y + 240, CREAM, alpha=0.35)
        s = fit("SUPERMAN", 960)
        k = out_expo(ph(t, 87.54, 0.14))
        F.text("SUPERMAN", s, 540, lerp(2300, 860, k) - 60 * ph(t, 87.7, 0.6), CREAM, rot=-6,
               sy=1.3)
        if vis(t, 87.95):
            F.text("AND", fit("AND", 300), 540, 1350, CREAM, sc=popin(t, 87.95, 0.12), rot=4)
        return
    # GHOSTBUSTERS: ghostly letters float in, then lock + echo outro
    F.bg(BLACK)
    F.shake(t, [(88.26, 26)])
    outro = ph(t, T_AUDIO_END, T_END - T_AUDIO_END)
    F.cam["z"] = 1 - 0.1 * out_cubic(outro)
    s = fit("GHOSTBUSTERS", 880)

    def ghost(i, n):
        a = ph(t, 88.24 + i * 0.022, 0.16)
        if a <= 0:
            return None
        fl = 0.75 + 0.25 * math.sin(t * 40 + i * 2)
        return dict(dy=-160 * (1 - out_expo(a)) + 10 * math.sin(t * 5 + i), alpha=a * fl,
                    rot=4 * math.sin(t * 4 + i))
    for g in range(3):     # visual echo matching the audio echo
        e = ph(t, T_AUDIO_END + g * ECHO_DELAY, 0.6)
        if 0 < e < 1:
            F.text("GHOSTBUSTERS", s, 540, 960, TAN, sc=1 + 0.45 * out_cubic(e), outline=4, sy=2.2,
                   alpha=(1 - e) * 0.8)
    F.letters("GHOSTBUSTERS", s, 540, 960, CREAM, ghost, sy=2.2)
    F.flash(MAROON, in_out(ph(t, T_END - 0.42, 0.42)))


SCENES = [(T_START, sA), (68.62, sB), (69.98, sC), (71.48, sD), (72.62, sE), (74.02, sF),
          (75.86, sG), (78.12, sH), (80.66, sI), (82.02, sJ), (83.50, sK), (85.90, sL)]

def scene_at(t):
    cur = SCENES[0][1]
    for t0, fn in SCENES:
        if t >= t0:
            cur = fn
    return cur

def render(t):
    F = Frame()
    sc = scene_at(t)
    sc(F, t)
    F.cam = dict(dx=0.0, dy=0.0, z=1.0, r=0.0)
    dark = F.img[H - 10, 540].mean() < 0.5
    if t < T_END - 0.42 and sc is not sL:
        F.star(540, 1745, 22, CREAM if dark else MAROON, rot=(t - T_START) * 40, alpha=0.95)
    return F.img
