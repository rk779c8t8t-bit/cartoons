"""Choreography for 'SLAVA MARLOW / TOLY SUMMER' fragment.

Word timings come from config/timeline.json (T[...]). Every value is a pure
function of t. Style: black space, white type, fire-orange accents.
"""
import json, math, os
from engine import (item, clamp, smooth, out_expo, out_cubic, in_cubic, in_out_cubic, out_back, out_elastic,
                    lerp, decay, hash01, jitter, FontBank, Burst, ROOT)

TL = json.load(open(os.path.join(ROOT, "config", "timeline.json")))
AN = json.load(open(os.path.join(ROOT, "analysis", "analysis.json")))
T, TXT, LINE_START = {}, {}, {}
for _ln in TL["lines"]:
    LINE_START[_ln["id"]] = _ln["words"][0]["t"]
    for _w in _ln["words"]:
        T[_w["id"]] = _w["t"]; TXT[_w["id"]] = _w["text"]
END = TL["video"]["end"]
AEND = TL.get("outro", {}).get("audio_end", END)
FB = FontBank()
CX, CY = 540.0, 960.0

WHITE = (1.0, 1.0, 1.0)
ORANGE = (1.0, 0.42, 0.06)
FIRE = (1.0, 0.3, 0.03)
GOLD = (1.0, 0.72, 0.25)
WARM = (1.0, 0.8, 0.55)
RED = (1.0, 0.12, 0.04)
CYAN = (0.0, 0.85, 1.0)


def D(wid): return TXT[wid].upper()
def kick(t):
    a = AN["env"]["kick"]; return a[int(clamp(t * AN["fps"], 0, len(a) - 1))]
def fit(wid, max_w, max_size, font="unb"): return FB.fit(D(wid), font, max_w, max_size)
def width(wid, size, font="unb"): return FB.width(D(wid), font, size)
def row(ids, size, cx=CX, gap=0.3, font="unb"):
    ws = [width(i, size, font) for i in ids]
    x = cx - (sum(ws) + gap * size * (len(ids) - 1)) / 2; out = []
    for w in ws: out.append(x + w / 2); x += w + gap * size
    return out
def nxt(line_id):
    ids = [l["id"] for l in TL["lines"]]
    i = ids.index(line_id)
    return LINE_START[ids[i + 1]] if i + 1 < len(ids) else END + 1
def W(wid, **kw):
    kw.setdefault("font", "unb"); kw.setdefault("bevel", 0.25)
    return item(key=wid, text=D(wid), **kw)
def rect(key, x, y, w, h, color=ORANGE, alpha=1.0, rot=0.0, glow=0.6, z=1):
    return dict(kind="rect", key=key, x=x, y=y, w=w, h=h, color=color, alpha=alpha, rot=rot, glow=glow,
                glow_col=color, z=z)
def rot_about(x, y, deg, cx=CX, cy=CY):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c


# ====================================================================== events
FLASHES, SHAKES, GLITCHES, CHROMAS, RINGS, PUFFS, BURSTS, ZOOMS = [], [], [], [], [], [], [], []
_seed = [500]
def _s(): _seed[0] += 1; return _seed[0]
def flash(t0, amt, col=WARM, d=0.07): FLASHES.append((t0, amt, col, d))
def shake(t0, amp, d=0.12): SHAKES.append((t0, amp, d, _s()))
def glitch_ev(t0, amt, dur=0.06): GLITCHES.append((t0, amt, dur))
def chroma_ev(t0, amt, d=0.1): CHROMAS.append((t0, amt, d))
def ring(t0, x, y, maxr=700, life=0.45, thick=14, bright=1.0, distort=18): RINGS.append((t0, x, y, maxr, life, thick, bright, distort))
def puff(t0, x, y, r0=120, grow=500, life=1.4, amt=1.0): PUFFS.append(dict(t0=t0, x=x, y=y, r0=r0, grow=grow, life=life, amt=amt))
def zoom_ev(t0, amt, d=0.12): ZOOMS.append((t0, amt, d))
def sparks(t0, x, y, n=60, **kw):
    kw.setdefault("seed", _s()); BURSTS.append(Burst(t0, x, y, n=n, **kw))
def flames_up(t0, x, y, w, n=30, dur=0.4, **kw):
    kw.setdefault("seed", _s())
    BURSTS.append(Burst(t0, x, y, n=n, speed=(120, 520), ang=(-90, 50), g=-380, drag=1.6, life=(0.3, 0.8),
                        size=(1, 3), area=(w, 30), delay=dur, streak=0.05, **kw))
def trail(t0, x0, x1, y, n=120, dur=0.25):
    """Fire trail left behind a word sliding from x0 to x1."""
    BURSTS.append(Burst(t0, (x0 + x1) / 2, y, n=n, speed=(40, 260), ang=(-90, 120), g=-300, drag=2.0,
                        life=(0.3, 0.9), size=(2, 5), area=(abs(x1 - x0), 90), delay=dur, streak=0.06, seed=_s()))


def _events():
    # intro: a small fire flash out of black
    flash(0.0, 0.18, ORANGE, 0.12); sparks(0.0, CX, 900, 40, speed=(150, 700), ang=(0, 360), life=(0.3, 0.8))
    puff(0.0, CX, 900, 80, 260, 1.0, 0.5)
    t = T["i_gorish"]
    flash(t, 0.3, WARM, 0.07); shake(t, 16); zoom_ev(t, 0.06); chroma_ev(t, 0.012)
    sparks(t, CX, 880, 90, speed=(400, 1700), ang=(0, 360), life=(0.3, 0.9), front=True)
    flash(T["i_kak"], 0.08, ORANGE, 0.05); shake(T["i_kak"], 6)
    t = T["i_ogon"]
    flash(t, 0.32, ORANGE, 0.1); shake(t, 12); trail(t, -200, CX, 1230, 160, 0.22)
    flames_up(t + 0.1, CX, 1180, 760, 90, 0.7)
    flash(2.45, 0.35, WARM, 0.06); glitch_ev(2.47, 0.3, 0.05)
    # V1
    t = T["a_gori"]
    flash(t, 0.35, WARM, 0.07); shake(t, 18); zoom_ev(t, 0.07); ring(t, CX, 760, 900, 0.4, 12, 0.6, 22)
    sparks(t, CX, 760, 80, speed=(400, 1500), ang=(0, 360), life=(0.3, 0.8))
    for w in ("a_ya", "a_goryu"): shake(T[w], 6); flash(T[w], 0.06, ORANGE, 0.04)
    t = T["a_tozhe"]; flash(t, 0.14, ORANGE, 0.06); shake(t, 10)
    sparks(t, CX, 1230, 50, speed=(300, 1100), ang=(-90, 200), life=(0.3, 0.7))
    # V2
    flash(T["b_no"], 0.1, WARM, 0.05)
    t = T["b_ogon"]
    flash(t, 0.6, (1.0, 0.55, 0.15), 0.12); shake(t, 20); zoom_ev(t, 0.06); chroma_ev(t, 0.015)
    ring(t, CX, 860, 1000, 0.45, 16, 0.7, 26); puff(t, CX, 860, 160, 600, 1.2, 0.8)
    sparks(t, CX, 860, 180, speed=(400, 1900), ang=(0, 360), life=(0.4, 1.0), area=(700, 100))
    flames_up(t, CX, 820, 760, 80, 0.5)
    t = T["b_dorozhe"]
    flash(t, 0.3, GOLD, 0.08); shake(t, 14); zoom_ev(t, 0.08)
    sparks(t, CX, 1280, 70, speed=(200, 1000), ang=(-90, 240), life=(0.4, 0.9), heat=0.9)
    glitch_ev(5.93, 0.6, 0.07)
    # V3
    for w in ("c_scha", "c_ya", "c_u", "c_slavy", "c_zavtra", "c_v", "c_shkolu"):
        flash(T[w], 0.12, WARM, 0.035); shake(T[w], 7, 0.06)
    flash(T["c_zavtra"], 0.35, WARM, 0.05); glitch_ev(T["c_zavtra"] - 0.02, 0.4, 0.04)
    t = 7.70  # школу hits the floor
    shake(t, 34, 0.12); flash(t, 0.15, ORANGE, 0.05); zoom_ev(t, 0.04)
    sparks(t, CX, 1660, 90, speed=(200, 1100), ang=(-90, 140), g=1600, life=(0.3, 0.7), front=True)
    puff(t, CX, 1700, 160, 500, 0.9, 0.9)
    # V4
    for w in ("d_ne", "d_ishchu", "d_slavy", "d_ya", "d_prosto"):
        flash(T[w], 0.08, ORANGE, 0.04); shake(T[w], 5, 0.06)
    t = 9.66  # end of the typed word
    flash(t, 0.7, (1.0, 0.65, 0.3), 0.08); shake(t, 18); zoom_ev(t, 0.07); ring(t, CX, 1420, 1000, 0.4, 14, 0.7, 22)
    sparks(t, CX, 1420, 160, speed=(400, 1800), ang=(0, 360), life=(0.3, 0.9), area=(900, 80), front=True)
    # V5
    t = T["e_a"]; flash(t, 0.2, WARM, 0.06); shake(t, 10)
    flash(T["e_penitsa"], 0.22, GOLD, 0.1)
    # V6
    for k, w in enumerate(("f_snova", "f_vseh")):
        flash(T[w], 0.14, WARM, 0.04); shake(T[w], 12, 0.08); zoom_ev(T[w], 0.05); glitch_ev(T[w], 0.2, 0.04)
    for k in range(8):
        tk = T["f_oteniki"] + k * 0.064; shake(tk, 5, 0.05)
    for k in range(7):
        tk = T["f_benikal"] + k * 0.045; shake(tk, 6, 0.05)
    t = T["f_benikal"]; flash(t, 0.2, ORANGE, 0.06)
    sparks(t, CX, 1290, 90, speed=(300, 1300), ang=(0, 360), life=(0.3, 0.8))
    t = T["f_echo"]; glitch_ev(t, 0.35, 0.06); chroma_ev(t, 0.02); flash(t, 0.12, WARM, 0.05)
    # V7
    for w in ("g_oni", "g_schas", "g_v"): shake(T[w], 6, 0.06)
    t = T["g_agonii"]; flash(t, 0.3, ORANGE, 0.08); sparks(t, CX, 990, 120, speed=(300, 1500), ang=(0, 360), life=(0.4, 1.0))
    flames_up(t, CX, 950, 700, 70, 0.6)
    t = T["g_a"]
    flash(t, 0.85, (1.0, 0.85, 0.65), 0.09); shake(t, 26, 0.1); zoom_ev(t, 0.08); chroma_ev(t, 0.03)
    ring(t, CX, CY, 1200, 0.5, 20, 0.8, 34); glitch_ev(t, 0.3, 0.04)
    sparks(t, CX, CY, 200, speed=(600, 2400), ang=(0, 360), life=(0.3, 0.9), front=True)
    # V8
    for w in ("h_pod", "h_pesenki", "h_pro", "h_vareniki"):
        flash(T[w], 0.08, WARM, 0.04); shake(T[w], 6, 0.06)
    t = T["h_vareniki"]; sparks(t, CX, 1330, 60, speed=(200, 900), ang=(-90, 200), life=(0.3, 0.8))
    if "h_haha" in T:
        for k in range(3): shake(T["h_haha"] + k * 0.16, 9, 0.06); flash(T["h_haha"] + k * 0.16, 0.08, WARM, 0.04)
    # outro: words burn away into rising embers
    sparks(AEND + 0.2, CX, 1100, 380, speed=(40, 380), ang=(-90, 120), g=-260, drag=1.2, life=(0.6, 1.3),
           size=(1, 3), area=(900, 700), delay=0.7, streak=0.05, heat=0.85)

_events()


# ====================================================================== lines
def intro(t, S):
    if t > T["a_gori"] + 0.02: return
    blow = in_cubic((t - 2.42) / 0.16)
    fade = 1 - smooth((t - 2.47) / 0.1)
    gz = 1 + 3.5 * blow
    back = smooth((t - T["i_kak"]) / 0.25)  # ГОРИШЬ steps back when КАК ОГОНЬ arrive
    a = t - T["i_ty"]
    if a >= 0:
        S["items"].append(W("i_ty", size=110 * gz, x=CX, y=CY + (560 - CY) * gz, alpha=smooth(a / 0.05) * fade * (1 - 0.6 * back),
                            style="white", glow=0.2, glow_col=ORANGE, z=1))
    a = t - T["i_gorish"]
    if a >= 0:
        txt = D("i_gorish")
        letters = [dict(s=1 + 0.035 * math.sin(t * 13 + i * 1.3) + 0.05 * kick(t),
                        heat=clamp(0.78 + 0.18 * math.sin(t * 9 + i * 2.1) + 0.2 * kick(t)), a=smooth((a - i * 0.02) / 0.04))
                   for i in range(len(txt))]
        size = fit("i_gorish", 930, 400) * lerp(3.4, 1, out_expo(a / 0.2)) * lerp(1, 0.9, back)
        S["items"].append(W("i_gorish", size=size * gz, sy=1.9, x=CX, y=CY + (lerp(830, 760, back) - CY) * gz,
                            alpha=fade * lerp(1, 0.35, back), style="hot", letters=letters, bevel=0.4, depth=6,
                            depth_vec=(0, 4), depth_col=(0.25, 0.03, 0.0), glow=lerp(0.9, 0.35, back), glow_col=FIRE,
                            blur=3 * back, z=1))
    a = t - T["i_kak"]
    if a >= 0:
        S["items"].append(W("i_kak", size=120 * gz * lerp(1.6, 1, out_expo(a / 0.15)), x=CX, y=CY + (1060 - CY) * gz,
                            alpha=smooth(a / 0.04) * fade, style="white", glow=0.25, glow_col=ORANGE, z=2))
    a = t - T["i_ogon"]
    if a >= 0:
        grow = 1 + 0.12 * in_cubic((t - 1.94) / 0.5)
        x = lerp(-300, CX, out_expo(a / 0.28))
        e = math.exp(-a / 0.3)
        gh = tuple((-70 * k * (0.3 + e), 0, 0.55 * (0.6 ** k) * (0.4 + e), FIRE) for k in (1, 2, 3, 4))
        S["items"].append(W("i_ogon", size=fit("i_ogon", 900, 300) * grow * gz, x=CX + (x - CX) * gz,
                            y=CY + (1230 - CY) * gz, alpha=smooth(a / 0.04) * fade, style="fire", bevel=0.3, depth=6,
                            depth_col=(0.3, 0.04, 0.0), glow=0.9 + 0.3 * kick(t), glow_col=FIRE, ghosts=gh, z=3))
        S["bg"]["flames"] = 0.3 * smooth(a / 0.2)
        S["heat"] = dict(amt=0.5, box=(60, 1080, 1020, 1350))
    if 2.4 < t < 2.6:
        S["cam"]["zoom_blur"] = 0.15 * smooth((t - 2.4) / 0.08)


def v1(t, S):
    t0, t1 = LINE_START["V1"], nxt("V1")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    out = in_cubic((t - (t1 - 0.09)) / 0.09); ox = -1300 * out
    a = t - T["a_gori"]
    if a >= 0:
        S["items"].append(W("a_gori", size=fit("a_gori", 920, 300) * lerp(5, 1, out_expo(a / 0.16)), x=CX + ox, y=760,
                            alpha=smooth(a / 0.03), style="white", depth=5, depth_vec=(0, 4), depth_col=(0.35, 0.06, 0.0),
                            glow=0.35 + 0.2 * kick(t), glow_col=ORANGE, z=2))
        bw = 760 * out_expo((t - (T["a_gori"] + 0.1)) / 0.3)
        S["items"].append(rect("a_bar", CX + ox, 900, bw, 12, ORANGE, glow=0.8))
    xs = row(["a_ya", "a_goryu"], 170)
    for k, w in enumerate(("a_ya", "a_goryu")):
        a = t - T[w]
        if a < 0: continue
        side = -1 if k == 0 else 1
        x = lerp(xs[k] + side * 900, xs[k], out_expo(a / 0.16))
        S["items"].append(W(w, size=170, x=x + ox, y=1050, alpha=smooth(a / 0.03), style="white", glow=0.2, glow_col=ORANGE, z=2))
    a = t - T["a_tozhe"]
    if a >= 0:
        S["items"].append(W("a_tozhe", size=200 * lerp(2, 1, out_back(a / 0.2, 2.0)), x=CX + ox, y=1260,
                            rot=lerp(-20, -4, out_expo(a / 0.25)), alpha=smooth(a / 0.03), style="fire", depth=5,
                            depth_col=(0.3, 0.04, 0.0), glow=0.8, glow_col=FIRE, z=2))
    if out > 0: S["cam"]["zoom_blur"] = 0.0


def v2(t, S):
    t0, t1 = LINE_START["V2"], nxt("V2")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    inn = 1300 * (1 - out_expo((t - t0) / 0.14))
    cut = 1 - smooth((t - (t1 - 0.07)) / 0.05)
    dor = smooth((t - T["b_dorozhe"]) / 0.2)
    dim = lerp(1, 0.45, dor); shrink = lerp(1, 0.88, dor)
    xs = row(["b_no", "b_moy"], 150)
    for k, w in enumerate(("b_no", "b_moy")):
        a = t - T[w]
        if a < 0: continue
        S["items"].append(W(w, size=150 * shrink * lerp(1.5, 1, out_expo(a / 0.12)), x=CX + (xs[k] - CX) * shrink + inn,
                            y=640, alpha=smooth(a / 0.03) * cut * dim, style="white", z=2))
    a = t - T["b_ogon"]
    if a >= 0:
        S["items"].append(W("b_ogon", size=fit("b_ogon", 860, 300) * lerp(0.3, 1, out_back(a / 0.22, 2.2)) * shrink * (1 + 0.04 * kick(t)),
                            x=CX + inn, y=850, alpha=smooth(a / 0.03) * cut * lerp(1, 0.6, dor), style="fire", depth=6,
                            depth_col=(0.3, 0.04, 0.0), glow=1.0 + 0.3 * kick(t), glow_col=FIRE, z=2))
        S["bg"]["flames"] = 0.38 * math.exp(-max(0, a - 0.3) / 0.8)
        S["heat"] = dict(amt=0.5 * cut, box=(60, 720, 1020, 980))
    a = t - T["b_pochemu"]
    if a >= 0:
        txt = D("b_pochemu")
        letters = [dict(a=smooth((a - i * 0.025) / 0.03), dy=0.3 * (1 - out_expo((a - i * 0.025) / 0.15))) for i in range(len(txt))]
        S["items"].append(W("b_pochemu", font="unbx", size=fit("b_pochemu", 700, 105, "unbx") * shrink, x=CX + inn, y=1050,
                            letters=letters, alpha=cut * dim, style="white", z=2))
    a = t - T["b_dorozhe"]
    if a >= 0:
        grow = lerp(0.2, 1, out_back(a / 0.25, 1.8)) * (1 + 0.1 * out_cubic(a / 0.5)) * (1 + 0.03 * kick(t))
        S["items"].append(W("b_dorozhe", size=fit("b_dorozhe", 880, 300) * grow, sy=1.35, x=CX + inn, y=1290,
                            alpha=smooth(a / 0.03) * cut, style="gold", sweep=-500 + a * 2400, bevel=0.45, depth=8,
                            depth_vec=(0, 4), depth_col=(0.3, 0.13, 0.02), glow=0.7, glow_col=GOLD, z=3))


def v3(t, S):
    t0, t1 = LINE_START["V3"], nxt("V3")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    tz = T["c_zavtra"]
    ids = ["c_scha", "c_ya", "c_u", "c_slavy", "c_zavtra", "c_v", "c_shkolu"]
    # hard camera snaps on every word
    n = sum(1 for w in ids if t >= T[w])
    S["cam"]["rot"] += [0, -3, 2.5, -2, 3, -2.5, 2, -3][n]
    S["cam"]["zoom"] *= [1, 1.04, 0.98, 1.06, 1.0, 1.05, 0.98, 1.03][n]
    if t < tz:
        for w, x, y, sz, st in (("c_scha", CX, 720, 300, "white"),):
            a = t - T[w]
            if a >= 0:
                S["items"].append(W(w, size=sz * lerp(1.4, 1, out_expo(a / 0.08)), x=x, y=y, style=st, depth=5,
                                    depth_vec=(0, 4), glow=0.25, glow_col=ORANGE, z=2))
        xs = row(["c_ya", "c_u"], 160)
        for k, w in enumerate(("c_ya", "c_u")):
            a = t - T[w]
            if a >= 0:
                S["items"].append(W(w, size=160 * lerp(1.5, 1, out_expo(a / 0.08)), x=xs[k], y=960, style="white", z=2))
        a = t - T["c_slavy"]
        if a >= 0:
            S["items"].append(W("c_slavy", size=fit("c_slavy", 900, 260) * lerp(1.4, 1, out_expo(a / 0.08)), x=CX, y=1180,
                                style="hot", heat=0.85, depth=5, depth_col=(0.3, 0.04, 0.0), glow=0.7, glow_col=FIRE, z=2))
            S["items"].append(rect("c_bar", CX, 1330, 820 * out_expo(a / 0.25), 10, ORANGE))
    else:
        cut = 1 - smooth((t - (t1 - 0.04)) / 0.04)
        a = t - tz
        S["items"].append(W("c_zavtra", size=fit("c_zavtra", 820, 230) * lerp(1.4, 1, out_expo(a / 0.08)), x=CX, y=700,
                            alpha=cut, style="white", depth=5, depth_vec=(0, 4), glow=0.25, glow_col=ORANGE,
                            x_=0, z=2) | dict(x=CX + jitter(t, 7, 40) * 10 * math.exp(-max(0, t - 7.70) / 0.08) * (t > 7.70)))
        a = t - T["c_v"]
        if a >= 0:
            S["items"].append(W("c_v", size=150 * lerp(1.5, 1, out_expo(a / 0.08)), x=CX, y=900, alpha=cut, style="white", z=2))
        a = t - T["c_shkolu"]
        if a >= 0:
            tf, th = 7.52, 7.70  # tip over, then hit the floor
            fall = in_cubic((t - tf) / (th - tf))
            bounce = math.exp(-max(0, t - th) / 0.05) * math.sin(max(0, t - th) * 60) * 30 * (t > th)
            y = lerp(1120, 1560, fall) - abs(bounce)
            rot = lerp(0, 11, smooth((t - (tf - 0.05)) / (th - tf + 0.05)))
            S["items"].append(W("c_shkolu", font="dela", bevel=0.35, size=fit("c_shkolu", 820, 260, "dela") * lerp(1.4, 1, out_expo(a / 0.08)),
                                x=CX + 10 * fall, y=y, rot=rot, alpha=cut, style="fire", depth=7, depth_vec=(0, 5),
                                depth_col=(0.3, 0.04, 0.0), glow=0.8, glow_col=FIRE, z=3))


def v4(t, S):
    t0, t1 = LINE_START["V4"], nxt("V4")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    out = in_cubic((t - (t1 - 0.07)) / 0.07)
    al = 1 - out
    left = 110
    stack = (("d_ne", 560, "white"), ("d_ishchu", 720, "white"), ("d_slavy", 880, "hot"), ("d_ya", 1040, "white"),
             ("d_prosto", 1200, "white"))
    ny = 0
    for w, y, st in stack:
        a = t - T[w]
        if a < 0: continue
        ny = y
        sz = 145
        x = left + width(w, sz) / 2
        S["items"].append(W(w, size=sz * lerp(1.35, 1, out_expo(a / 0.1)), x=x - 90 * (1 - out_expo(a / 0.1)), y=y,
                            alpha=smooth(a / 0.03) * al, style=st, heat=0.85, glow=0.5 if st == "hot" else 0.15,
                            glow_col=FIRE, z=2))
    if ny:
        S["items"].append(rect("d_bar", 62, (520 + ny + 60) / 2, 10, ny + 60 - 520, ORANGE, alpha=al))
    a = t - T["d_rabotayu"]
    if a >= 0:
        txt = D("d_rabotayu"); n = len(txt)
        dur = 0.42
        times = [dur * math.sqrt(i / n) for i in range(n)]  # gaps shrink: accelerating typing
        shown = sum(1 for x in times if a >= x)
        done = a >= dur
        letters = [dict(a=1.0 if i < shown else 0.0, s=1.0 if (a - times[i]) > 0.03 or i >= shown else 1.25) for i in range(n)]
        size = fit("d_rabotayu", 940, 170, "mono")
        hot = smooth((a - dur) / 0.06)
        S["items"].append(W("d_rabotayu", font="mono", bevel=0.0, size=size * (1 + 0.08 * math.exp(-max(0, a - dur) / 0.1) * done),
                            x=CX, y=1420, letters=letters, alpha=al, style="hot", heat=lerp(0.0, 0.95, hot),
                            tint=WHITE, tint_amt=1 - hot, glow=0.2 + 0.8 * hot, glow_col=FIRE, z=3))
        if not done or int(t * 8) % 2 == 0:
            letters_w = FB.layout(txt, "mono")[1] * size / 200
            cx = CX - letters_w / 2 + letters_w * shown / n + size * 0.08
            S["items"].append(rect("d_caret", cx, 1420, size * 0.08, size * 0.85, ORANGE if not done else WHITE, alpha=al * (1 - hot)))


def v5(t, S):
    t0, t1 = LINE_START["V5"], nxt("V5")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    out = in_cubic((t - (t1 - 0.08)) / 0.08)
    sc = 1 - 0.9 * out; al = 1 - out
    a = t - T["e_a"]
    if a >= 0:
        dim = smooth((t - T["e_sok"]) / 0.2)
        S["items"].append(W("e_a", size=330 * lerp(0.3, 1, out_elastic(a / 0.5)) * lerp(1, 0.6, dim) * sc,
                            x=CX, y=lerp(820, 600, dim), alpha=al * lerp(1, 0.4, dim), style="white", depth=5,
                            depth_vec=(0, 4), glow=0.3, glow_col=ORANGE, z=1))
    xs = row(["e_sok", "e_v"], 170)
    for k, w in enumerate(("e_sok", "e_v")):
        a = t - T[w]
        if a < 0: continue
        S["items"].append(W(w, size=170 * lerp(0.4, 1, out_back(a / 0.2)) * sc, x=CX + (xs[k] - CX) * sc,
                            y=870 + 20 * math.sin(t * 3 + k), alpha=al, style="white", z=2))
    a = t - T["e_bokal"]
    if a >= 0:
        txt = D("e_bokal")
        letters = [dict(a=smooth((a - i * 0.03) / 0.05), dy=0.5 * (1 - out_back((a - i * 0.03) / 0.3)) + 0.03 * math.sin(t * 6 + i))
                   for i in range(len(txt))]
        S["items"].append(W("e_bokal", font="unbx", size=fit("e_bokal", 960, 150, "unbx") * sc, x=CX, y=1050, letters=letters,
                            alpha=al, style="white", glow=0.25, glow_col=GOLD, z=2))
    a = t - T["e_penitsa"]
    if a >= 0:
        txt = D("e_penitsa")
        letters = [dict(dy=0.06 * math.sin(t * 9 + i * 0.9) - 0.4 * (1 - out_back((a - i * 0.025) / 0.3)),
                        a=smooth((a - i * 0.025) / 0.05)) for i in range(len(txt))]
        S["items"].append(W("e_penitsa", size=fit("e_penitsa", 900, 240) * sc * (1 + 0.04 * kick(t)), x=CX, y=1250,
                            letters=letters, alpha=al, style="gold", sweep=-400 + a * 1500, bevel=0.4, depth=5,
                            depth_vec=(0, 4), depth_col=(0.3, 0.13, 0.02), glow=0.8, glow_col=GOLD, z=3))
    a = t - T["e_echo"]
    if a >= 0:
        e = math.exp(-a / 0.35)
        gh = tuple((0, 34 * k * (0.4 + e), 0.5 * 0.55 ** k, GOLD) for k in (1, 2, 3))
        S["items"].append(W("e_echo", size=96 * lerp(1.4, 1, out_expo(a / 0.15)) * sc, x=CX, y=1440, alpha=al * smooth(a / 0.04),
                            style="gold", outline=3, fill=0.15, glow=0.35, glow_col=GOLD, ghosts=gh, z=2))
    # foam: from the bottom while the line plays, plus a burst out of ПЕНИТСЯ
    S["bubbles"] = [dict(t0=T["e_bokal"], t1=t1, x0=400, x1=680, y0=1560, ysp=40, rise=420, n=90, seed=3, amount=0.9 * al, rmax=20),
                    dict(t0=T["e_penitsa"], t1=t1, x0=200, x1=880, y0=1300, ysp=120, rise=260, n=130, seed=4, amount=1.3 * al, rmax=18, front=True)]
    S["bg"]["red"] = 0.22; S["bg"]["underlight"] = 0.3


def v6(t, S):
    t0, t1 = LINE_START["V6"], nxt("V6")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    spin = in_cubic((t - (t1 - 0.12)) / 0.12)
    gr = 160 * spin; gal = 1 - smooth((t - (t1 - 0.05)) / 0.05)
    words = (("f_snova", 690, -8, 185, "white"), ("f_vseh", 900, 6, 200, "fire"))
    def put(w, x, y, rot, **kw):
        px, py = rot_about(x, y, gr)
        S["items"].append(W(w, x=px, y=py, rot=rot + gr, **kw))
    for w, y, r, sz, st in words:
        a = t - T[w]
        if a < 0: continue
        s = lerp(2.3, 1, out_back(a / 0.18, 2.4)) * (1 + 0.06 * kick(t))
        put(w, CX + 15 * math.sin(t * 5), y, r + lerp(25, 0, out_expo(a / 0.2)) * (1 if r > 0 else -1), size=sz * s,
            alpha=smooth(a / 0.03) * gal, style=st, depth=5, depth_vec=(0, 4), depth_col=(0.3, 0.04, 0.0),
            glow=0.3 if st == "white" else 0.9, glow_col=FIRE, z=2)
    for w, y, r, gap, st in (("f_oteniki", 1100, -4, 0.064, "white"), ("f_benikal", 1290, 3, 0.045, "fire")):
        a = t - T[w]
        if a < 0: continue
        txt = D(w)
        letters = []
        for i in range(len(txt)):
            u = a - i * gap
            letters.append(dict(a=smooth(u / 0.02), s=lerp(2.2, 1, out_back(u / 0.14, 2.6)),
                                rot=(hash01(i, 77) - 0.5) * 50 * (1 - out_expo(u / 0.2)) + 4 * jitter(t, 300 + i, 10),
                                dy=0.04 * jitter(t, 330 + i, 12)))
        put(w, CX, y, r, size=fit(w, 900, 230), letters=letters, alpha=gal, style=st, depth=5, depth_vec=(0, 4),
            depth_col=(0.3, 0.04, 0.0), glow=0.3 if st == "white" else 0.9, glow_col=FIRE, z=2)
    a = t - T["f_echo"]
    if a >= 0:
        sp = out_expo(a / 0.25) * 34
        for k, (dy, col, st, rr) in enumerate(((-sp, WHITE, "white", -3), (sp, ORANGE, "fire", 3))):
            put("f_echo", CX + (k * 2 - 1) * sp * 0.6, 1480 + dy, rr * out_expo(a / 0.25), size=120, alpha=gal * smooth(a / 0.03) * (0.95 if k == 0 else 0.75),
                style=st, outline=3 if k else 0, fill=0.0 if k else 1.0, glow=0.4, glow_col=FIRE, z=2 + k)
            S["items"][-1]["key"] = "f_echo%d" % k
    S["cam"]["zoom_blur"] = max(S["cam"].get("zoom_blur", 0), 0.1 * spin)


def v7(t, S):
    t0, t1 = LINE_START["V7"], nxt("V7")
    if t < t0 - 0.01 or t > t1 + 0.01: return
    ta = T["g_a"]
    def theta(x):
        d = x - t0; return 15 * d + 30 * d * d
    freeze = t >= ta
    th = theta(min(t, ta))
    dimA = smooth((t - ta) / 0.03)
    out = smooth((t - (t1 - 0.06)) / 0.06)
    lay = []
    xs1 = row(["g_oni", "g_schas"], 160); lay += [("g_oni", xs1[0], 800, 160, "white"), ("g_schas", xs1[1], 800, 160, "white")]
    agsz = fit("g_agonii", 640, 210)
    xs2 = row(["g_v", "g_agonii"], agsz); lay += [("g_v", xs2[0], 990, agsz * 0.7, "white"), ("g_agonii", xs2[1], 990, agsz, "fire")]
    lay += [("g_vert", CX, 1170, fit("g_vert", 860, 200), "white")]
    for w, x, y, sz, st in lay:
        a = t - T[w]
        if a < 0: continue
        px, py = rot_about(x, y, th)
        jit = 0 if freeze else 1
        S["items"].append(W(w, size=sz * lerp(1.6, 1, out_expo(a / 0.12)), x=px, y=py, rot=th, alpha=smooth(a / 0.03) * lerp(1, 0.25, dimA) * (1 - out),
                            style=st, depth=5, depth_vec=(0, 4), depth_col=(0.3, 0.04, 0.0),
                            glow=(0.25 if st == "white" else 0.9) * (1 + 0.3 * kick(t) * jit), glow_col=FIRE, z=2, mblur=not freeze))
    a = t - ta
    if a >= 0:
        S["items"].append(W("g_a", size=330 * lerp(2.2, 1, out_expo(a / 0.07)) * (1 - 0.8 * out), x=CX, y=CY, style="hot", heat=1.0,
                            alpha=1 - out, bevel=0.5, depth=8, depth_vec=(0, 5), depth_col=(0.35, 0.05, 0.0), glow=1.1,
                            glow_col=FIRE, z=4))
    if T["g_agonii"] <= t < ta:
        S["bg"]["flames"] = 0.35 * smooth((t - T["g_agonii"]) / 0.2)
    if not freeze:
        S["embers"]["speed"] = 1.0 + 1.5 * (t - t0)


def v8(t, S):
    t0 = LINE_START["V8"]
    if t < t0 - 0.01: return
    end_pop = 0.0
    drift = 140 * in_out_cubic((t - (AEND - 0.15)) / (END - AEND))   # everything floats up after the song
    dis = clamp((t - (AEND + 0.15)) / 0.85)                            # ...and burns away
    words = (("h_pod", 400, 760, 170, -6, "white", "unb"), ("h_pesenki", CX, 950, None, 3, "fire", "unb"),
             ("h_pro", 680, 1140, 170, 5, "white", "unb"), ("h_vareniki", CX, 1340, None, -3, "white", "dela"))
    hop_all = 0.0
    if "h_haha" in T:
        a = t - T["h_haha"]
        if a >= 0:
            hop_all = sum(math.sin(clamp((a - k * 0.16) / 0.16) * math.pi) for k in range(3)) * 90
    vanish = smooth((t - (T["h_haha"] + 0.5)) / 0.1) if "h_haha" in T else 0
    for w, x, y, sz, r, st, font in words:
        a = t - T[w]
        if a < 0: continue
        if sz is None: sz = fit(w, 960 if w == "h_vareniki" else 880, 260, font)
        sp = out_elastic(a / 0.55)
        squash = 1 + 0.35 * math.exp(-a / 0.18) * math.sin(a * 32)
        txt = D(w)
        letters = [dict(dy=-0.08 * abs(math.sin(t * 7 + i * 0.8)) * (w == "h_vareniki"), rot=6 * math.sin(t * 6 + i)) for i in range(len(txt))]
        S["items"].append(W(w, font=font, size=sz * lerp(0.2, 1, sp) * (1 - end_pop), sx=1 / squash, sy=squash,
                            x=x, y=y - 120 * (1 - out_back(a / 0.3, 2.5)) - hop_all - drift, rot=r + 8 * math.sin(t * 4 + y),
                            letters=letters, alpha=smooth(a / 0.03) * (1 - vanish), style=st, bevel=0.35, depth=6,
                            depth_vec=(0, 5), depth_col=(0.3, 0.05, 0.0), outline=0, glow=0.3 if st == "white" else 0.8,
                            glow_col=FIRE, dissolve=dis, z=2))
    if "h_haha" in T:
        a = t - T["h_haha"]
        if a >= 0:
            S["items"].append(W("h_haha", size=fit("h_haha", 700, 150), x=CX, y=1560 - hop_all, alpha=smooth(a / 0.03) * (1 - vanish),
                                style="hot", heat=0.9, glow=0.6, glow_col=FIRE, z=3))
    o = smooth((t - AEND) / (END - AEND))
    S["cam"]["zoom"] *= 1 + 0.07 * o
    S["bg"]["red"] = 0.16 + 0.25 * math.sin(math.pi * o)   # last warm breath, then dark
    S["embers"].update(amount=0.35 + 0.5 * o, count=0.45 + 0.5 * o, speed=0.7)
    S["fade"] = 1 - smooth((t - (END - 0.55)) / 0.55)


# ====================================================================== frame
def frame(t):
    t = max(0.0, t)
    S = dict(items=[], cam=dict(zoom=1.0, rot=0.0, x=0.0, y=0.0), flash=(0.0, 0.0, 0.0), glitch=0.0, chroma=0.0,
             bg=dict(red=0.16, smoke=0.3, flames=0.0, underlight=0.15, bright=1.0, smoke_speed=0.6),
             embers=dict(amount=0.35, count=0.45, speed=1.0), heat=None, rings=[], puffs=PUFFS, fade=1.0, bloom=0.8,
             bubbles=[])
    for fn in (intro, v1, v2, v3, v4, v5, v6, v7, v8, pictures):
        fn(t, S)
    S["cam"]["y"] += 70
    k = kick(t)
    S["bg"]["bright"] *= 1 + 0.25 * k
    S["cam"]["zoom"] *= 1 + 0.012 * k
    for (t0, amt, col, d) in FLASHES:
        e = decay(t, t0, d)
        if e > 0.002: S["flash"] = tuple(f + c * amt * e for f, c in zip(S["flash"], col))
    sx = sy = sr = 0.0
    for (t0, amp, d, sd) in SHAKES:
        e = decay(t, t0, d)
        if e > 0.01:
            sx += amp * e * jitter(t, sd, 45); sy += amp * e * jitter(t, sd + 1, 45); sr += amp * e * 0.05 * jitter(t, sd + 2, 30)
    S["cam"]["x"] += sx; S["cam"]["y"] += sy; S["cam"]["rot"] += sr
    for (t0, amt, d) in ZOOMS:
        S["cam"]["zoom"] *= 1 + amt * decay(t, t0, d)
    S["cam"]["zoom"] = max(S["cam"]["zoom"], 1.0 + 0.01 + abs(sx) / 500 + abs(sy) / 900 + abs(S["cam"]["rot"]) / 40)
    for (t0, amt, dur) in GLITCHES:
        if t0 <= t <= t0 + dur: S["glitch"] += amt
    for (t0, amt, d) in CHROMAS:
        S["chroma"] += amt * decay(t, t0, d)
    for (t0, x, y, maxr, life, th, br, dist) in RINGS:
        a = t - t0
        if 0 <= a <= life:
            f = a / life
            S["rings"].append((x, y, maxr * out_expo(f * 0.8), th * (1 + 1.5 * f), 0.6 * br * (1 - f) ** 4, dist * (1 - f) ** 1.5))
    S["glitch"] = min(S["glitch"], 1.0)
    return S


# ====================================================================== pictures
def img(key, name, x, y, size, rot=0.0, alpha=1.0, glow=0.25, glow_col=FIRE, z=0, shadow=0.55, **kw):
    d = dict(kind="img", key=key, name=name, x=x, y=y, size=size, rot=rot, alpha=alpha, glow=glow, glow_col=glow_col,
             z=z, shadow=shadow)
    d.update(kw); return d


def pic(S, t, key, name, t_in, t_out, x, y, size, rot=0.0, bob=1.0, enter=0.35, ph=0.0, exit_=0.14, **kw):
    """Spring pop-in, gentle float, quick pop-out. Returns (scale, alpha) or None."""
    a = t - t_in
    if a < 0 or t > t_out + exit_: return None
    e = in_cubic((t - t_out) / exit_)
    sc = lerp(0.0, 1.0, out_back(a / enter, 2.4)) * (1 - 0.85 * e) * (1 + 0.05 * kick(t))
    al = smooth(a / 0.05) * (1 - e)
    S["items"].append(img(key, name, x, y + 14 * bob * math.sin(t * 3.1 + ph), size * sc,
                          rot=rot + 6 * bob * math.sin(t * 2.3 + ph) + lerp(-25, 0, out_expo(a / 0.4)), alpha=al, **kw))
    return sc, al


def pictures(t, S):
    # --- intro: the fire itself is the opening flash, then rises above ГОРИШЬ
    if t < 2.62:
        a = t
        up = out_expo((t - T["i_gorish"]) / 0.3)
        blow = in_cubic((t - 2.42) / 0.16)
        size = lerp(lerp(60, 230, out_back(a / 0.3, 2.0)), 330, up) * (1 + 0.06 * math.sin(t * 17) + 0.08 * kick(t)) * (1 + 3 * blow)
        S["items"].append(img("p_fire", "fire", CX, lerp(900, 320, up) - 900 * blow, size, rot=4 * math.sin(t * 9),
                              alpha=1 - smooth((t - 2.47) / 0.1), glow=0.9, z=0))
    # --- V1: burning heart answers "я горю тоже"
    pic(S, t, "p_heart", "heartfire", T["a_goryu"], LINE_START["V2"] - 0.1, CX, 1560, 300, glow=0.6)
    # --- V2: money flies on ОГОНЬ, diamond on ДОРОЖЕ
    for k, (x0, x1, r) in enumerate(((-150, 300, -20), (1230, 790, 20))):
        a = t - (T["b_ogon"] + 0.06 * k)
        if 0 <= a and t < LINE_START["V3"] - 0.06:
            f = out_expo(a / 0.45)
            S["items"].append(img("p_money%d" % k, "money", lerp(x0, x1, f), lerp(1750, 1600, f) + 12 * math.sin(t * 4 + k),
                                  230, rot=r + 10 * math.sin(t * 3 + k), alpha=smooth(a / 0.05), glow=0.2, z=0))
    r = pic(S, t, "p_gem", "gem", T["b_dorozhe"], LINE_START["V3"] - 0.1, CX, 300, 300, glow=0.5, glow_col=(0.5, 0.8, 1.0))
    # --- V3: studio mic at "у Славы", school + backpack falling with ШКОЛУ
    pic(S, t, "p_mic", "mic", T["c_slavy"], T["c_zavtra"] - 0.03, 840, 330, 250, rot=-18, exit_=0.03)
    pic(S, t, "p_school", "school", T["c_zavtra"], LINE_START["V4"] - 0.04, CX, 320, 270, exit_=0.04)
    a = t - T["c_shkolu"]
    if a >= 0 and t < LINE_START["V4"] - 0.02:
        tf, th = 7.56, 7.72
        fall = in_cubic((t - tf) / (th - tf))
        bounce = abs(math.exp(-max(0, t - th) / 0.05) * math.sin(max(0, t - th) * 55) * 40) * (t > th)
        S["items"].append(img("p_bag", "backpack", lerp(900, 870, fall), lerp(850, 1640, fall) - bounce,
                              230 * out_back(a / 0.25, 2.2), rot=lerp(8, 38, fall), z=3))
    # --- V4: laptop shakes while РАБОТАЮ is typed
    a = t - T["d_rabotayu"]
    if a >= 0 and t < LINE_START["V5"]:
        typing = a < 0.42
        jx = jitter(t, 900, 30) * 6 * typing
        e = in_cubic((t - (LINE_START["V5"] - 0.08)) / 0.08)
        S["items"].append(img("p_laptop", "laptop", 830 + jx, 690 + jitter(t, 901, 30) * 4 * typing,
                              270 * out_back(a / 0.25, 2.2) * (1 + 0.12 * math.exp(-max(0, a - 0.42) / 0.1) * (not typing)) * (1 - e),
                              rot=-8, alpha=1 - e, glow=0.2 + 0.8 * math.exp(-max(0, a - 0.42) / 0.15) * (not typing), z=1))
    # --- V5: champagne glass; the foam rises out of it
    pic(S, t, "p_glass", "glass", T["e_bokal"], LINE_START["V6"] - 0.08, CX, 1610, 380, glow=0.35, glow_col=GOLD, bob=0.6)
    # --- V6: cool face, crazy face doubles on (Беникал)
    pic(S, t, "p_cool", "cool", T["f_snova"], LINE_START["V7"] - 0.1, 850, 330, 250, rot=12)
    r = pic(S, t, "p_crazy", "crazy", T["f_benikal"], LINE_START["V7"] - 0.1, 230, 1730, 240, rot=-10, ph=1.0)
    a = t - T["f_echo"]
    if r and a >= 0:
        sp = out_expo(a / 0.25) * 90
        S["items"].append(img("p_crazy2", "crazy", 230 + sp, 1730 - sp * 0.3, 240 * r[0], rot=10, alpha=0.55 * r[1],
                              tint=ORANGE, tint_amt=0.6, z=-1, shadow=0))
    # --- V7: an orange vortex spins behind the rotating text; faces react
    a = t - T["g_oni"]
    if a >= 0 and t < LINE_START["V8"]:
        e = smooth((t - (LINE_START["V8"] - 0.1)) / 0.1)
        S["items"].append(img("p_vortex", "cyclone", CX, CY, 900 * out_cubic(a / 0.4) * (1 + 0.05 * kick(t)),
                              rot=-(120 * a + 160 * a * a) if t < T["g_a"] else -(120 * (T["g_a"] - T["g_oni"]) + 160 * (T["g_a"] - T["g_oni"]) ** 2),
                              alpha=0.3 * (1 - e), tint=(1.0, 0.45, 0.08), tint_amt=1.0, glow=0.25, z=-2, shadow=0, blur=1.5))
    pic(S, t, "p_dizzy", "dizzy", T["g_vert"], T["g_a"] - 0.02, CX, 250, 240, exit_=0.05)
    pic(S, t, "p_scream", "scream", T["g_a"], LINE_START["V8"] - 0.08, CX, 1660, 300, enter=0.12)
    # --- V8: music notes and bouncing dumplings, then everything drifts up and fades
    out_o = smooth((t - (AEND + 0.1)) / 0.8)
    drift = 140 * in_out_cubic((t - (AEND - 0.15)) / (END - AEND))
    a = t - T["h_pesenki"]
    if a >= 0:
        S["items"].append(img("p_notes", "notes", CX + 30 * math.sin(t * 2), 300 + 16 * math.sin(t * 3) - drift,
                              250 * out_back(a / 0.35, 2.2), rot=8 * math.sin(t * 2.5), alpha=smooth(a / 0.05) * (1 - out_o), z=0))
    for k, (x, y) in enumerate(((230, 1640), (CX, 1700), (850, 1640))):
        a = t - (T["h_vareniki"] + 0.09 * k)
        if a < 0: continue
        hop = abs(math.sin(a * 7 + k)) * 60 * math.exp(-max(0, a - 0.2) / 0.9)
        sq = 1 + 0.25 * math.exp(-a / 0.15) * math.sin(a * 35)
        S["items"].append(img("p_dump%d" % k, "dumpling", x, y - hop - drift * (1.2 + 0.3 * k),
                              270 * out_back(a / 0.3, 2.6) * (1 - 0.3 * out_o), sx=1 / sq, sy=sq,
                              rot=(k - 1) * 14 + 10 * math.sin(t * 3 + k) + 40 * out_o * (k - 1), alpha=1 - out_o, z=0))
