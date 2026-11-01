"""Choreography: what is on screen at time t.

Word timings come from config/timeline.json (T[...] / SYL[...]); this file
decides how each line moves, glows, breaks and explodes. Every value is a
pure function of t.
"""
import json, math, os
from engine import (item, clamp, smooth, out_expo, out_cubic, in_cubic, in_out_cubic, out_back,
                    lerp, decay, window, hash01, jitter, FontBank, Burst, ROOT)

TL = json.load(open(os.path.join(ROOT, "config", "timeline.json")))
AN = json.load(open(os.path.join(ROOT, "analysis", "analysis.json")))
T, SYL, TXT = {}, {}, {}
for _ln in TL["lines"]:
    for _w in _ln["words"]:
        T[_w["id"]] = _w["t"]; SYL[_w["id"]] = _w.get("syl"); TXT[_w["id"]] = _w["text"]
END = TL["video"]["end"]
FB = FontBank()
CX, CY = 540.0, 960.0
MAXW = 960.0

# palette
RED = (1.0, 0.12, 0.04)
ORANGE = (1.0, 0.42, 0.06)
GOLD = (1.0, 0.72, 0.25)
WHITE = (1.0, 1.0, 1.0)
CYAN = (0.0, 0.85, 1.0)
WARM = (1.0, 0.82, 0.6)


def D(wid):
    s = TXT[wid]
    return s if "round" in s else s.upper()

def env(name, t):
    a = AN["env"][name]
    i = int(clamp(t * AN["fps"], 0, len(a) - 1))
    return a[i]

def kick(t):
    return env("kick", t)

def fit(wid, max_w=MAXW, max_size=400, font="black"):
    return FB.fit(D(wid), font, max_w, max_size)

def row(ids, size, cx=CX, gap=0.26, font="black"):
    ws = [FB.width(D(i), font, size) for i in ids]
    total = sum(ws) + gap * size * (len(ids) - 1)
    x = cx - total / 2; out = []
    for w in ws:
        out.append(x + w / 2); x += w + gap * size
    return out

def nlet(wid):
    return len(D(wid))


# ====================================================================== events
FLASHES, SHAKES, GLITCHES, CHROMAS, RINGS, PUFFS, BURSTS, ZOOMS = [], [], [], [], [], [], [], []
_seed = [100]

def _s():
    _seed[0] += 1; return _seed[0]

def flash(t0, amt, col=WARM, d=0.07): FLASHES.append((t0, amt, col, d))
def shake(t0, amp, d=0.12): SHAKES.append((t0, amp, d, _s()))
def glitch_ev(t0, amt, dur=0.06): GLITCHES.append((t0, amt, dur))
def chroma_ev(t0, amt, d=0.1): CHROMAS.append((t0, amt, d))
def ring(t0, x, y, maxr=700, life=0.45, thick=14, bright=1.0, distort=18): RINGS.append((t0, x, y, maxr, life, thick, bright, distort))
def puff(t0, x, y, r0=120, grow=500, life=1.4, amt=1.0): PUFFS.append(dict(t0=t0, x=x, y=y, r0=r0, grow=grow, life=life, amt=amt))
def zoom_ev(t0, amt, d=0.12): ZOOMS.append((t0, amt, d))
def sparks(t0, x, y, n=60, **kw):
    kw.setdefault("seed", _s()); BURSTS.append(Burst(t0, x, y, n=n, **kw))
def debris(t0, x, y, n=40, color=ORANGE, **kw):
    kw.setdefault("seed", _s()); kw.setdefault("size", (2, 6)); kw.setdefault("streak", 0.02)
    BURSTS.append(Burst(t0, x, y, n=n, kind="debris", color=color, **kw))
def flames_up(t0, x, y, w, n=30, dur=0.4, **kw):
    kw.setdefault("seed", _s())
    BURSTS.append(Burst(t0, x, y, n=n, speed=(120, 520), ang=(-90, 50), g=-380, drag=1.6, life=(0.3, 0.8),
                        size=(1, 3), area=(w, 30), delay=dur, streak=0.05, **kw))


# ---------------- line 1 positions
L1 = dict(ty_y0=930, ty_y1=690, gor_y=905, kak_y=1080, ogon_y=1260, ya_y=1000, row_y=830, ag_y=1090)
L5 = dict(L1)

def _build_events():
    # ---------- LINE 1
    # intro (before the first word): ember crackle rising out of the dark core
    sparks(0.0, CX, 960, 45, speed=(60, 380), ang=(-90, 300), g=-120, drag=1.2, life=(0.4, 1.0), size=(1, 3),
           area=(500, 300), streak=0.05, heat=0.8)
    t = T["l1_ty"]
    flash(t, 0.22, ORANGE, 0.12); ring(t, CX, 930, 650, 0.5, 12, 0.9, 14); shake(t, 10)
    sparks(t, CX, 930, 70, speed=(400, 1500), ang=(0, 360), life=(0.3, 0.8))
    puff(t, CX, 950, 160, 420, 1.3, 0.6)
    for i in range(nlet("l1_gorish")):
        ti = T["l1_gorish"] + i * 0.045
        flames_up(ti, CX - 380 + i * 115, L1["gor_y"] - 60, 60, n=10, dur=0.3)
    s2 = SYL["l1_gorish"][1]
    flames_up(s2, CX, L1["gor_y"] - 70, 800, n=70, dur=0.35)
    t = T["l1_kak"]  # the drop
    flash(t, 0.45, WARM, 0.09); ring(t, CX, L1["kak_y"], 900, 0.5, 18, 1.0, 26); shake(t, 22, 0.15)
    glitch_ev(t, 0.35, 0.07); chroma_ev(t, 0.012); zoom_ev(t, 0.07)
    sparks(t, CX, L1["kak_y"], 140, speed=(500, 2000), ang=(0, 360), life=(0.4, 1.0), front=True)
    for k, s in enumerate(SYL["l1_ogon"]):
        sparks(s, CX, L1["ogon_y"], 70 + 40 * k, speed=(300, 1300), ang=(-90, 160), g=700, area=(700, 120), life=(0.4, 1.1))
        flash(s, 0.18 + 0.1 * k, ORANGE, 0.08); shake(s, 9)
    flames_up(T["l1_ogon"], CX, L1["ogon_y"] - 80, 760, n=90, dur=0.5)
    t = T["l1_ya"]
    flash(t, 0.35, (1.0, 0.8, 0.6), 0.06); ring(t, CX, L1["ya_y"], 1100, 0.5, 24, 1.0, 30)
    shake(t, 24, 0.14); glitch_ev(t, 0.3, 0.06); chroma_ev(t, 0.02); zoom_ev(t, 0.09)
    sparks(t, CX, L1["ya_y"], 120, speed=(600, 2200), ang=(0, 360), life=(0.3, 0.8), front=True)
    for wid in ("l1_u", "l1_menya"):
        flash(T[wid], 0.1, ORANGE, 0.06); shake(T[wid], 6); glitch_ev(T[wid], 0.15, 0.04)
    syl = SYL["l1_agonia"]
    for k, s in enumerate(syl[:-1]):
        flash(s, 0.2, ORANGE, 0.06); shake(s, 10); glitch_ev(s, 0.25, 0.05)
        sparks(s, CX - 300 + k * 230, L1["ag_y"], 45, speed=(300, 1200), ang=(0, 360), life=(0.3, 0.7))
    s = syl[-1]
    flash(s, 0.75, (1.0, 0.55, 0.25), 0.1); ring(s, CX, L1["ag_y"], 1200, 0.55, 26, 1.0, 34)
    ring(s + 0.06, CX, L1["ag_y"], 800, 0.45, 12, 0.6, 0)
    shake(s, 32, 0.18); glitch_ev(s, 0.65, 0.12); chroma_ev(s, 0.025); zoom_ev(s, 0.08)
    puff(s, CX, L1["ag_y"], 260, 900, 1.6, 1.4)
    sparks(s, CX, L1["ag_y"], 260, speed=(500, 2400), ang=(0, 360), life=(0.4, 1.2), area=(800, 150))
    debris(s, CX, L1["ag_y"], 50, ORANGE, speed=(300, 1400), ang=(0, 360), life=(0.4, 1.0), area=(800, 150), g=1200)
    glitch_ev(3.93, 0.7, 0.1)

    # ---------- LINE 2
    t = T["l2_lubov"]
    sparks(t + 0.1, CX, 820, 40, speed=(40, 160), ang=(-90, 120), g=-60, drag=0.8, life=(0.8, 1.6), size=(1, 2), area=(800, 120), delay=0.6, heat=0.6)
    glitch_ev(T["l2_ili"], 0.12, 0.05); glitch_ev(T["l2_eto2"], 0.22, 0.06)
    for k, s in enumerate(SYL["l2_paranoia"]):
        glitch_ev(s, 0.35 + 0.08 * k, 0.07); chroma_ev(s, 0.012); shake(s, 7, 0.08)
    t = T["l2_q"]
    flash(t, 0.4, (1.0, 0.3, 0.2), 0.08); ring(t, CX, 980, 1000, 0.45, 18, 0.9, 26); shake(t, 22)
    glitch_ev(t + 0.03, 0.3, 0.04); chroma_ev(t, 0.015); zoom_ev(t, 0.06)
    sparks(t, CX, 980, 120, speed=(500, 1900), ang=(0, 360), life=(0.3, 0.9))

    # ---------- LINE 3
    pos = [(330, 700), (740, 960), (540, 1240)]
    for k, wid in enumerate(("l3_la1", "l3_la2", "l3_la3")):
        t = T[wid]; x, y = pos[k]
        flash(t, 0.16 + 0.1 * k, (1.0, 0.6, 0.3), 0.06)
        shake(t, 8 + 6 * k); zoom_ev(t, 0.03 + 0.02 * k)
        sparks(t, x, y, 40 + 30 * k, speed=(300, 1300), ang=(0, 360), life=(0.3, 0.8))
    for k, wid in enumerate(("l3_ela1", "l3_ela2", "l3_ela3")):
        flash(T[wid], 0.06, GOLD, 0.05)
    glitch_ev(9.55, 0.3, 0.12)

    # ---------- LINE 4
    for wid in ("l4_ty", "l4_gorish", "l4_kak", "l4_ogon"):
        glitch_ev(T[wid], 0.4, 0.06); chroma_ev(T[wid], 0.012); shake(T[wid], 9)
        flash(T[wid], 0.12, ORANGE, 0.05)
    t = T["l4_ya"]
    flash(t, 0.45, WARM, 0.08); ring(t, CX, 1420, 900, 0.5, 18, 1.0, 24); shake(t, 18); glitch_ev(t, 0.3, 0.06)
    sparks(t, CX, 1420, 120, speed=(400, 1800), ang=(-90, 300), life=(0.4, 1.0))
    for wid in ("l4_bla1", "l4_bla2", "l4_bla3"):
        glitch_ev(T[wid], 0.15, 0.04)
    glitch_ev(T["l4_round"], 0.35, 0.08)

    # ---------- LINE 5 (bigger)
    t = T["l5_ty"]
    flash(t, 0.9, (1.0, 0.9, 0.75), 0.13); ring(t, CX, 900, 1200, 0.55, 28, 1.0, 36)
    ring(t + 0.07, CX, 900, 900, 0.5, 14, 0.7, 0); shake(t, 30, 0.18); zoom_ev(t, 0.1)
    sparks(t, CX, 900, 200, speed=(600, 2400), ang=(0, 360), life=(0.4, 1.1))
    puff(t, CX, 950, 220, 700, 1.6, 1.0)
    for i in range(nlet("l5_gorish")):
        ti = T["l5_gorish"] + i * 0.03
        flames_up(ti, CX - 380 + i * 115, L5["gor_y"] - 60, 70, n=18, dur=0.25)
        sparks(ti, CX - 380 + i * 115, L5["gor_y"], 10, speed=(200, 700), ang=(-90, 90), life=(0.2, 0.5))
    flames_up(SYL["l5_gorish"][1], CX, L5["gor_y"] - 70, 850, n=140, dur=0.35)
    flash(SYL["l5_gorish"][1], 0.15, ORANGE, 0.06)
    t = T["l5_kak"]
    flash(t, 0.35, WARM, 0.07); ring(t, CX, L5["kak_y"], 800, 0.45, 14, 0.9, 22); shake(t, 16); glitch_ev(t, 0.4, 0.06)
    for k, s in enumerate(SYL["l5_ogon"]):
        sparks(s, CX, L5["ogon_y"], 160 + 80 * k, speed=(400, 1800), ang=(-90, 170), g=800, area=(800, 140), life=(0.4, 1.2))
        flash(s, 0.3 + 0.12 * k, ORANGE, 0.08); shake(s, 14)
    flames_up(T["l5_ogon"], CX, L5["ogon_y"] - 90, 860, n=200, dur=0.55)
    t = T["l5_ya"]
    flash(t, 0.45, (1.0, 0.85, 0.7), 0.07); ring(t, CX, L5["ya_y"], 1300, 0.55, 30, 1.0, 40)
    ring(t + 0.08, CX, L5["ya_y"], 1000, 0.5, 14, 0.8, 0)
    shake(t, 34, 0.16); glitch_ev(t, 0.5, 0.08); chroma_ev(t, 0.03); zoom_ev(t, 0.12)
    sparks(t, CX, L5["ya_y"], 220, speed=(700, 2600), ang=(0, 360), life=(0.3, 0.9), front=True)
    for wid in ("l5_u", "l5_menya"):
        flash(T[wid], 0.16, RED, 0.06); shake(T[wid], 10); glitch_ev(T[wid], 0.3, 0.05); chroma_ev(T[wid], 0.01)
    syl = SYL["l5_agonia"]
    for k, s in enumerate(syl[:-1]):
        flash(s, 0.3, ORANGE, 0.06); shake(s, 14); glitch_ev(s, 0.35, 0.05)
        sparks(s, CX - 300 + k * 230, L5["ag_y"], 80, speed=(300, 1500), ang=(0, 360), life=(0.3, 0.8))
    s = syl[-1]
    flash(s, 0.95, (1.0, 0.6, 0.3), 0.12); ring(s, CX, L5["ag_y"], 1400, 0.6, 32, 1.0, 44)
    ring(s + 0.07, CX, L5["ag_y"], 1000, 0.5, 16, 0.8, 0); ring(s + 0.14, CX, L5["ag_y"], 700, 0.4, 8, 0.5, 0)
    shake(s, 40, 0.2); glitch_ev(s, 0.8, 0.14); chroma_ev(s, 0.035); zoom_ev(s, 0.1)
    puff(s, CX, L5["ag_y"], 300, 1100, 1.4, 1.8); puff(s + 0.05, CX - 250, L5["ag_y"] + 100, 200, 700, 1.2, 1.0)
    sparks(s, CX, L5["ag_y"], 380, speed=(600, 2800), ang=(0, 360), life=(0.4, 1.3), area=(900, 160))
    debris(s, CX, L5["ag_y"], 90, ORANGE, speed=(300, 1700), ang=(0, 360), life=(0.4, 1.0), area=(900, 160), g=1300)
    debris(s, CX, L5["ag_y"], 40, (1.0, 0.9, 0.7), speed=(500, 2000), ang=(0, 360), life=(0.3, 0.7), area=(900, 160), g=900, front=True)
    # final disintegration into particles
    td = 15.98
    sparks(td, CX, L5["ag_y"], 650, speed=(80, 900), ang=(-90, 230), g=-250, drag=1.4, life=(0.35, 0.9),
           size=(1, 3), area=(900, 230), delay=0.2, streak=0.03, front=True)
    sparks(td, CX, L5["row_y"], 250, speed=(80, 700), ang=(-90, 230), g=-250, drag=1.4, life=(0.35, 0.8),
           size=(1, 3), area=(700, 170), delay=0.18, streak=0.03, front=True)
    flash(16.12, 0.5, (1.0, 0.7, 0.4), 0.035)

_build_events()


# ====================================================================== words
def ty_word(wid, t, big, s_from, y0, y1, gz, cy0, fade, heat_style=False, echo=False):
    t0 = T[wid]; a = t - t0
    if a < 0: return None
    nxt = T[wid.replace("_ty", "_gorish")]
    m = out_expo((t - nxt) / 0.3)
    sc = lerp(s_from, 1.0, out_expo(a / 0.26)) * (1 + 0.05 * min(a, 0.5)) * (1 + 0.035 * kick(t))
    size = lerp(big, 290, m) * sc
    x, y = CX, lerp(y0, y1, m)
    x, y = CX + (x - CX) * gz, cy0 + (y - cy0) * gz
    ghosts = ()
    if echo:
        e = math.exp(-a / 0.35)
        ghosts = tuple((0, 26 * k * e, 0.35 * e / k, ORANGE) for k in (1, 2, 3))
    return item(key=wid, text=D(wid), size=size * gz, x=x, y=y, rot=lerp(-7, 0, out_expo(a / 0.4)),
                alpha=smooth(a / 0.05) * fade, style="hot" if heat_style else "white", heat=1.0,
                bevel=0.35, depth=7, depth_vec=(2.5, 3.5), glow=0.35 + 0.3 * kick(t), glow_col=RED, ghosts=ghosts, z=2)


def gorish_word(wid, t, y, gz, cy0, fade, fast=False):
    t0 = T[wid]
    if t < t0: return None
    n = nlet(wid); st = 0.03 if fast else 0.045
    s2 = SYL[wid][1]
    letters = []
    for i in range(n):
        ti = t0 + i * st
        u = (t - ti)
        pos = (t - s2) / 0.32 * (n + 2) - 1.5
        boost = math.exp(-((i - pos) / 1.3) ** 2) * 0.45 if t >= s2 else 0.0
        h = clamp(u / (0.18 if fast else 0.35)) * (0.82 if not fast else 0.9) + (0.5 if fast else 0) * clamp(u / 0.05)
        letters.append(dict(dx=0, dy=0.4 * (1 - out_expo(u / 0.2)), s=lerp(1.6, 1, out_expo(u / 0.18)),
                            a=smooth(u / 0.05), rot=lerp(-25, 0, out_expo(u / 0.25)) * (1 if i % 2 else -1),
                            heat=clamp(h + boost + 0.08 * kick(t), 0, 1)))
    size = fit(wid, 940, 235) * (1 + 0.025 * kick(t))
    return item(key=wid, text=D(wid), size=size * gz, x=CX, y=cy0 + (y - cy0) * gz, alpha=fade, style="hot",
                letters=letters, bevel=0.45, depth=6, depth_vec=(2, 3.2), depth_col=(0.18, 0.02, 0.01),
                glow=0.55 + 0.25 * kick(t), glow_col=ORANGE, z=2)


def kak_word(wid, t, y, gz, cy0, fade):
    t0 = T[wid]; a = t - t0
    if a < 0: return None
    yy = lerp(y - 260, y, out_back(a / 0.2, 1.4))
    return item(key=wid, text=D(wid), size=150 * lerp(1.8, 1, out_expo(a / 0.2)) * gz, x=CX,
                y=cy0 + (yy - cy0) * gz, alpha=smooth(a / 0.04) * fade, style="white", bevel=0.3, depth=5,
                glow=0.3, glow_col=RED, z=2)


def ogon_word(wid, t, y, gz, cy0, fade, big=False):
    t0 = T[wid]; a = t - t0
    if a < 0: return None
    syl = SYL[wid]
    letters = []
    txt = D(wid)
    for i in range(len(txt)):
        ts = syl[0] if i < 2 else syl[1]
        u = t - ts
        letters.append(dict(a=smooth(u / 0.04), s=lerp(0.2, 1, out_back(u / 0.22, 2.2)),
                            dy=-0.25 * (1 - out_expo(u / 0.25)), rot=0, heat=1.0))
    size = fit(wid, 880 if big else 900, 300 if big else 270) * (1 + 0.03 * kick(t))
    size *= 1 + 0.04 * min(a, 1.0)
    out = [item(key=wid, text=txt, size=size * gz, x=CX, y=cy0 + (y - cy0) * gz, alpha=fade, style="fire",
                letters=letters, bevel=0.3, depth=8, depth_vec=(2.2, 3.6), depth_col=(0.3, 0.04, 0.0),
                glow=0.7 + 0.3 * kick(t), glow_col=ORANGE, rot=lerp(-6, 0, out_expo(a / 0.3)), z=2)]
    if big:  # giant outline echo behind
        out.append(item(key=wid + "_bg", text=txt, size=size * gz * (1.9 + 0.35 * a), x=CX, y=cy0 + (y - cy0) * gz,
                        alpha=0.16 * smooth(a / 0.1) * fade, style="color", color=ORANGE, outline=3, fill=0.0,
                        glow=0.15, glow_col=ORANGE, z=-1, mblur=False))
    return out


def ya_word(wid, t, y, fade_end, big=1.0):
    t0 = T[wid]; a = t - t0
    if a < 0 or t > fade_end + 0.12: return None
    z = lerp(0.18, 1.0, out_expo(a / 0.14)) * (1 + 0.1 * a)
    out_f = in_cubic((t - fade_end) / 0.12)
    size = fit(wid, 1000, 1050 * big)
    return item(key=wid, text=D(wid), size=size * z * (1 + 0.8 * out_f), x=CX, y=y,
                alpha=smooth(a / 0.03) * (1 - out_f), style="hot", heat=1.0, bevel=0.5, depth=10,
                depth_vec=(3, 4.5), depth_col=(0.35, 0.05, 0.0), glow=1.1, glow_col=ORANGE,
                blur=out_f * 10, z=3)


def umenya_words(t, ids, y, alt_colors=False, end=None):
    xs = row(ids, 200)
    out = []
    tension = clamp((t - T[ids[0]]) / 0.7)
    for k, wid in enumerate(ids):
        a = t - T[wid]
        if a < 0: continue
        side = -1 if k == 0 else 1
        x = lerp(xs[k] + side * 700, xs[k], out_expo(a / 0.2))
        jx = jitter(t, 11 + k, 24) * 7 * tension; jy = jitter(t, 21 + k, 24) * 5 * tension
        style, tint, ta = "white", None, 0.0
        if alt_colors:
            nk = sum(1 for kk in AN["kicks"] if kk <= t)
            if nk % 2: tint, ta = (1.0, 0.1, 0.05), 1.0
        gh = ((6 * tension, 0, 0.5 * tension, RED), (-6 * tension, 0, 0.5 * tension, CYAN)) if alt_colors else ()
        out.append(item(key=wid, text=D(wid), size=200, x=x + jx, y=y + jy, rot=jitter(t, 31 + k, 12) * 1.5 * tension,
                        alpha=smooth(a / 0.04), style=style, tint=tint, tint_amt=ta, bevel=0.3, depth=5,
                        glow=0.3 + 0.3 * tension, glow_col=RED, ghosts=gh, z=2))
    return out


def agonia_word(wid, t, y, power=1.0):
    syl = SYL[wid]
    t0 = syl[0]
    if t < t0: return None
    txt = D(wid)
    smap = [0, 1, 1, 2, 2, 3]
    size = fit(wid, 880, 280)
    letters = []
    after = t - syl[-1]
    for i in range(len(txt)):
        ts = syl[smap[i]]; u = t - ts
        p = out_expo(u / 0.17)
        dx0 = (hash01(i, 3 + power) - 0.5) * 3.2; dy0 = (hash01(i, 7 + power) - 0.5) * 4.5
        r0 = (hash01(i, 9 + power) - 0.5) * 200
        jx = jitter(t, 40 + i, 30) * 0.02 * power * (after > 0); jy = jitter(t, 50 + i, 30) * 0.02 * power * (after > 0)
        letters.append(dict(dx=dx0 * (1 - p) + jx, dy=dy0 * (1 - p) + jy, rot=r0 * (1 - p), s=lerp(2.8, 1, p),
                            a=smooth(u / 0.03), heat=1.0))
    sc = 1 + 0.07 * clamp(after, 0, 1) + 0.04 * kick(t)
    gh = ()
    if after > 0:
        e = math.exp(-after / 0.25)
        gh = ((14 * e * power, 0, 0.6 * e, RED), (-14 * e * power, 0, 0.6 * e, CYAN))
    return item(key=wid, text=txt, size=size * sc, x=CX, y=y, style="fire", letters=letters, bevel=0.35,
                depth=9, depth_vec=(2.4, 3.8), depth_col=(0.3, 0.03, 0.0), glow=1.1 + 0.4 * power * kick(t),
                glow_col=(1.0, 0.18, 0.03), ghosts=gh, z=3)


# ====================================================================== lines
def line1(t, S):
    if t > 4.06: return
    tya = T["l1_ya"]
    gz = 1 + 5 * in_cubic((t - (tya - 0.02)) / 0.16)
    fade = 1 - smooth((t - tya) / 0.1)
    if t < tya + 0.12:
        S["items"] += [w for w in (
            ty_word("l1_ty", t, 420, 3.2, L1["ty_y0"], L1["ty_y1"], gz, CY, fade),
            gorish_word("l1_gorish", t, L1["gor_y"], gz, CY, fade),
            kak_word("l1_kak", t, L1["kak_y"], gz, CY, fade)) if w]
        og = ogon_word("l1_ogon", t, L1["ogon_y"], gz, CY, fade)
        if og: S["items"] += og
        if T["l1_gorish"] + 0.15 < t < tya + 0.05:
            S["heat"] = dict(amt=0.6 + 0.8 * (t > T["l1_ogon"]), box=(60, L1["gor_y"] - 300, 1020, L1["ogon_y"] + 150))
    w = ya_word("l1_ya", t, L1["ya_y"], T["l1_u"] - 0.06)
    if w: S["items"].append(w)
    # у меня + агония, with TV-off collapse at the end
    col = in_cubic((t - 3.93) / 0.11)
    its = umenya_words(t, ["l1_u", "l1_menya"], L1["row_y"])
    ag = agonia_word("l1_agonia", t, L1["ag_y"])
    if ag: its.append(ag)
    for it in its:
        it["sy"] *= max(0.02, 1 - col); it["sx"] *= 1 + 0.5 * col; it["alpha"] *= 1 - smooth((t - 4.0) / 0.04)
    S["items"] += its
    if ag and t > SYL["l1_agonia"][-1]:
        S["heat"] = dict(amt=0.9, box=(40, L1["ag_y"] - 260, 1040, L1["ag_y"] + 160))
    # world
    drop = smooth((t - T["l1_kak"]) / 0.05)
    S["bg"].update(red=0.45 + 0.35 * drop + 0.5 * (1 - smooth((t - 0.1) / 0.3)), flames=0.38 * drop + 0.1, smoke=0.6, underlight=0.4 + 0.5 * drop)
    S["embers"].update(amount=0.5 + 0.4 * drop, count=0.5 + 0.4 * drop, speed=1.0 + 0.6 * drop)
    if tya - 0.02 < t < tya + 0.16:
        S["cam"]["zoom_blur"] = 0.12 * (1 - abs((t - tya - 0.03) / 0.13))


def line2(t, S):
    if t < T["l2_eto1"] - 0.02 or t > 7.75: return
    tq = T["l2_q"]
    blow = in_cubic((t - (tq - 0.05)) / 0.09)
    gz = 1 + 3 * blow
    fade = 1 - smooth((t - (tq - 0.04)) / 0.06)
    par0 = T["l2_paranoia"]
    nerv = clamp((t - par0) / 0.3)
    if t < tq + 0.12:
        # ЭТО
        a = t - T["l2_eto1"]
        if a >= 0:
            n = nlet("l2_eto1")
            letters = [dict(dx=(i - (n - 1) / 2) * 0.45 * (1 - out_cubic(a / 0.55)), a=smooth((a - i * 0.04) / 0.25)) for i in range(n)]
            S["items"].append(item(key="l2_eto1", text=D("l2_eto1"), size=150 * gz, x=CX, y=CY + (640 + 6 * math.sin(t * 2) - CY) * gz,
                                   alpha=0.92 * fade, blur=lerp(14, 0, out_cubic(a / 0.4)), letters=letters, style="white",
                                   glow=0.25, glow_col=RED, z=1))
        # ЛЮБОВЬ
        a = t - T["l2_lubov"]
        if a >= 0:
            n = nlet("l2_lubov")
            letters = []
            for i in range(n):
                u = a - i * 0.05
                jx = jitter(t, 60 + i, 20) * 0.05 * nerv * (hash01(math.floor(t * 20), i) > 0.55)
                letters.append(dict(dy=0.3 * (1 - out_cubic(u / 0.45)), dx=jx, a=smooth(u / 0.3) * (1 - 0.5 * nerv * (jitter(t, 70 + i, 15) > 0.5))))
            s = lerp(0.84, 1.0, in_out_cubic(a / 0.7)) * (1 + 0.03 * kick(t))
            gh = ((9 * nerv, 0, 0.55 * nerv, RED), (-9 * nerv, 0, 0.55 * nerv, CYAN)) if nerv > 0 else ()
            S["items"].append(item(key="l2_lubov", text=D("l2_lubov"), font="italic", size=fit("l2_lubov", 960, 250, "italic") * s * gz,
                                   x=CX + jitter(t, 80, 12) * 10 * nerv, y=CY + (850 + 8 * math.sin(t * 1.6) - CY) * gz,
                                   alpha=fade, blur=lerp(18, 0, out_cubic(a / 0.5)), letters=letters, style="love",
                                   bevel=0.3, glow=0.75 + 0.45 * kick(t), glow_col=(1.0, 0.08, 0.12), ghosts=gh,
                                   tint=WHITE, tint_amt=0.6 * nerv * (jitter(t, 90, 10) > 0.6), z=1))
        # ИЛИ
        a = t - T["l2_ili"]
        if a >= 0:
            fl = 1.0 if a > 0.07 else (0.25 if int(t * 60) % 2 else 0.95)
            S["items"].append(item(key="l2_ili", text=D("l2_ili"), size=120 * gz, x=CX + jitter(t, 91, 20) * 3 * nerv,
                                   y=CY + (1040 - CY) * gz, alpha=fl * fade, style="white", glow=0.2, glow_col=RED, z=1))
        # ЭТО (2)
        a = t - T["l2_eto2"]
        if a >= 0:
            e = math.exp(-a / 0.12)
            S["items"].append(item(key="l2_eto2", text=D("l2_eto2"), size=150 * gz, x=CX + jitter(t, 92, 30) * 18 * e,
                                   y=CY + (1170 - CY) * gz, alpha=smooth(a / 0.03) * fade, style="white",
                                   ghosts=((22 * e + 4 * nerv, 0, 0.6, RED), (-22 * e - 4 * nerv, 0, 0.6, CYAN)),
                                   glow=0.2, glow_col=RED, z=1))
        # ПАРАНОЙЯ
        a = t - par0
        if a >= 0:
            syl = SYL["l2_paranoia"]; smap = [0, 0, 1, 1, 2, 2, 3, 3]
            txt = D("l2_paranoia")
            letters = []
            for i in range(len(txt)):
                u = t - syl[smap[i]]
                e = math.exp(-max(u, 0) / 0.08)
                big = (hash01(math.floor(t * 15), i, 5) > 0.9) * 0.14
                letters.append(dict(a=smooth(u / 0.02) * (0.35 if (u < 0.08 and int(t * 60) % 2) else 1.0),
                                    dx=jitter(t, 100 + i, 24) * (0.03 + 0.35 * e + big),
                                    dy=jitter(t, 120 + i, 24) * (0.025 + 0.2 * e),
                                    rot=jitter(t, 140 + i, 24) * (3 + 30 * e), s=1 + 0.15 * e))
            k = 7 + 14 * math.exp(-min((t - s) for s in syl if s <= t) / 0.1) if t >= syl[0] else 0
            dup = jitter(t, 160, 8)
            gh = ((k, 0, 0.7, RED), (-k, 0, 0.7, CYAN), (0, 38 * dup, 0.22, WHITE))
            sx = 1 + (0.12 * jitter(t, 170, 10) if jitter(t, 171, 10) > 0.6 else 0)
            S["items"].append(item(key="l2_paranoia", text=txt, size=fit("l2_paranoia", 900, 190) * gz, x=CX,
                                   y=CY + (1370 - CY) * gz, sx=sx, alpha=fade, letters=letters, style="white",
                                   bevel=0.25, ghosts=gh, glow=0.45, glow_col=RED, z=2))
            S["glitch"] += 0.14 * nerv
    # "?"
    a = t - tq
    if a >= 0:
        rec = smooth((t - (T["l3_la1"] - 0.01)) / 0.22)
        S["items"].append(item(key="l2_q", text="?", size=720 * lerp(1.9, 1, out_expo(a / 0.08)) * (1 + 0.15 * rec),
                               x=CX, y=980, alpha=smooth(a / 0.02) * (1 - 0.85 * rec) * (1 - smooth((t - 7.4) / 0.3)),
                               style="hot", heat=0.62, bevel=0.5, depth=12, depth_vec=(3, 4), depth_col=(0.25, 0.01, 0.0),
                               glow=1.0 * (1 - 0.7 * rec), glow_col=RED, blur=4 * rec, z=-1 if rec > 0.05 else 3, mblur=False))
    S["bg"].update(red=0.3 + 0.25 * nerv, flames=0.08 * (1 - smooth((t - 4.03) / 0.4)), smoke=0.85, smoke_speed=0.45,
                   underlight=0.25)
    S["embers"].update(amount=0.35, count=0.4, speed=0.5)
    S["cam"]["rot"] += 1.1 * math.sin((t - 4.03) * 1.2)
    S["cam"]["zoom"] *= 1 + 0.018 * (t - 4.03)


def line3(t, S):
    if t < T["l3_la1"] - 0.01 or t > 9.8: return
    out_p = in_cubic((t - 9.32) / 0.43)
    off = -380 * out_p
    pos = [(330, 700, -10, 270, "white"), (740, 960, 8, 270, "fire"), (540, 1240, -3, 380, "gold")]
    ids = ("l3_la1", "l3_la2", "l3_la3")
    for k, wid in enumerate(ids):
        a = t - T[wid]
        if a < 0: continue
        x, y, r, sz, st = pos[k]
        push = sum(math.exp(-(t - T[o]) / 0.1) * 0.08 for o in ids[k + 1:] if t >= T[o])
        s = lerp(2.0, 1, out_back(a / 0.24, 2.0)) * (1 + 0.08 * kick(t) + push)
        rr = r + lerp(28 * (1 if k % 2 else -1), 0, out_expo(a / 0.3))
        sw = (-400 + (t - T[wid]) * 1500) if st == "gold" else None
        S["items"].append(item(key=wid, text=D(wid), size=sz * s * (1 + 0.6 * out_p), x=x + off * 0.6, y=y + off,
                               rot=rr, alpha=smooth(a / 0.03) * (1 - out_p), style=st, sweep=sw, bevel=0.4, depth=7,
                               depth_col=(0.3, 0.12, 0.02) if st == "gold" else (0.3, 0.03, 0.0),
                               glow=(0.4 if st == "white" else 0.8) + 0.3 * kick(t),
                               glow_col=GOLD if st == "gold" else (ORANGE if st == "fire" else RED), z=2))
    eids = ("l3_ela1", "l3_ela2", "l3_ela3")
    xs = row(eids, 118, gap=0.3)
    for k, wid in enumerate(eids):
        a = t - T[wid]
        if a < 0: continue
        e = math.exp(-a / 0.4)
        gh = tuple((16 * j * (0.3 + e), -12 * j * (0.3 + e), 0.5 * (0.55 ** j), GOLD) for j in (1, 2, 3))
        s = lerp(1.35, 1, out_expo(a / 0.2))
        al = smooth(a / 0.05) * (1 - out_p)
        base = dict(text=D(wid), size=118 * s, x=xs[k] + off * 0.4, rot=-3, style="gold", outline=3, fill=0.2,
                    glow=0.35, glow_col=GOLD, sweep=-300 + a * 900)
        S["items"].append(item(key=wid, y=1530 + off * 0.5, alpha=al, ghosts=gh, z=2, **base))
        S["items"].append(item(key=wid + "_refl", y=1530 + off * 0.5 + 118 * 1.02, sy=-1, alpha=al * 0.2, blur=2, z=1, mblur=False, **base))
    S["bg"].update(red=0.55 + 0.2 * kick(t), flames=0.18 + 0.3 * out_p, smoke=0.6, underlight=0.5)
    S["embers"].update(amount=0.6, count=0.6, speed=1.2 + 2 * out_p)
    S["cam"]["x"] += off * 0.15; S["cam"]["y"] += off * 0.15


def line4(t, S):
    if t < T["l4_ty"] - 0.01 or t > 12.42: return
    R = -12.0
    ux, uy = math.cos(math.radians(R)), math.sin(math.radians(R))
    acc = in_cubic((t - 11.95) / 0.37)
    pan = 30 * (t - T["l4_ty"]) + 1300 * acc
    px, py = -0.45 * pan, -0.9 * pan
    lay = [("l4_ty", 290, 480, 210, "white"), ("l4_gorish", 560, 720, None, "hot"), ("l4_kak", 310, 950, 150, "white"),
           ("l4_ogon", 600, 1170, None, "fire"), ("l4_ya", 600, 1500, 390, "hot")]
    for wid, x, y, sz, st in lay:
        a = t - T[wid]
        if a < 0: continue
        if sz is None: sz = fit(wid, 740, 200)
        p = out_expo(a / 0.22)
        sx_ = x - ux * 900 * (1 - p); sy_ = y - uy * 900 * (1 - p)
        e = math.exp(-a / 0.1)
        grow = 1.0
        heat = 1.0
        if wid == "l4_ya":
            grow = 1 + 0.32 * out_cubic((t - T[wid]) / 0.32)
        if wid == "l4_gorish":
            heat = clamp(a / 0.2)
        S["items"].append(item(key=wid, text=D(wid), size=sz * grow * (1 + 0.04 * kick(t)), x=sx_ + px, y=sy_ + py, rot=R,
                               shear=-0.25 * e, alpha=smooth(a / 0.03) * (1 - smooth((t - 11.97) / 0.12)), style=st, heat=heat, bevel=0.35, depth=6,
                               depth_vec=(2.5, 3.5), ghosts=((24 * e, 0, 0.7 * e, RED), (-24 * e, 0, 0.7 * e, CYAN)),
                               glow=0.4 if st == "white" else 0.9, glow_col=ORANGE if st != "white" else RED, z=2))
    bids = ("l4_bla1", "l4_bla2", "l4_bla3")
    xs = row(bids, 84, cx=560, gap=0.3)
    for k, wid in enumerate(bids):
        a = t - T[wid]
        if a < 0: continue
        fl = 1.0 if a > 0.06 else (0.2 if int(t * 60) % 2 else 1.0)
        S["items"].append(item(key=wid, text=D(wid), size=84 * lerp(1.4, 1, out_expo(a / 0.15)), x=xs[k] + px * 0.5,
                               y=250 + (xs[k] - 560) * uy + py * 0.5, rot=R, alpha=fl * 0.95 * (1 - smooth((t - 11.97) / 0.12)), style="gold", outline=3,
                               fill=0.25, glow=0.3, glow_col=GOLD, ghosts=((10, -8, 0.3, GOLD),), z=2))
    a = t - T["l4_round"]
    if a >= 0:
        txt = D("l4_round")
        letters = [dict(a=1.0 if a > i * 0.014 else 0.0, dy=jitter(t, 200 + i, 20) * 0.04) for i in range(len(txt))]
        S["items"].append(item(key="l4_round", text=txt, font="mono", size=150, x=CX, y=CY,
                               rot=R * 0.5, mblur=False, letters=letters, style="white", ghosts=((8, 0, 0.6, RED), (-8, 0, 0.6, CYAN)),
                               glow=0.35, glow_col=RED, z=2))
    if T["l4_ogon"] < t < 11.95:
        S["heat"] = dict(amt=0.7, box=(60, 980, 1020, 1300))
    S["bg"].update(red=0.6, flames=0.35 + 0.4 * acc, smoke=0.55, underlight=0.6)
    S["embers"].update(amount=0.75, count=0.8, speed=2.0 + 4 * acc)
    S["cam"]["zoom"] *= 1 + 1.2 * acc
    S["cam"]["zoom_blur"] = max(S["cam"].get("zoom_blur", 0), 0.22 * acc)
    S["flash"] = tuple(f + c * 0.9 * acc ** 2 for f, c in zip(S["flash"], (1.0, 0.75, 0.5)))


def line5(t, S):
    if t < T["l5_ty"] - 0.01: return
    tya = T["l5_ya"]
    gz = 1 + 6 * in_cubic((t - (tya - 0.02)) / 0.15)
    fade = 1 - smooth((t - tya) / 0.09)
    if t < tya + 0.12:
        S["items"] += [w for w in (
            ty_word("l5_ty", t, 460, 5.0, L5["ty_y0"], L5["ty_y1"], gz, CY, fade, heat_style=True, echo=True),
            gorish_word("l5_gorish", t, L5["gor_y"], gz, CY, fade, fast=True),
            kak_word("l5_kak", t, L5["kak_y"], gz, CY, fade)) if w]
        og = ogon_word("l5_ogon", t, L5["ogon_y"], gz, CY, fade, big=True)
        if og: S["items"] += og
        if T["l5_gorish"] + 0.1 < t < tya:
            S["heat"] = dict(amt=0.9 + 0.8 * (t > T["l5_ogon"]), box=(40, L5["gor_y"] - 320, 1040, L5["ogon_y"] + 160))
    w = ya_word("l5_ya", t, L5["ya_y"], T["l5_u"] - 0.06, big=1.05)
    if w:
        w["ghosts"] = ((16, 0, 0.6, RED), (-16, 0, 0.6, CYAN)); S["items"].append(w)
    its = umenya_words(t, ["l5_u", "l5_menya"], L5["row_y"], alt_colors=True)
    ag = agonia_word("l5_agonia", t, L5["ag_y"], power=1.6)
    if ag:
        its.append(ag)
        a2 = t - SYL["l5_agonia"][-1]
        if a2 > 0:
            S["items"].append(item(key="l5_ag_bg", text=ag["text"], size=ag["size"] * (1.7 + 0.5 * a2), x=CX, y=L5["ag_y"],
                                   alpha=0.14 * smooth(a2 / 0.08), style="color", color=RED, outline=3, fill=0.0,
                                   glow=0.2, glow_col=RED, z=-1, mblur=False))
    # final disintegration
    dis = clamp((t - 15.98) / 0.2)
    for it in its:
        it["dissolve"] = dis
    S["items"] += its
    if ag and t > SYL["l5_agonia"][-1]:
        S["heat"] = dict(amt=1.1, box=(30, L5["ag_y"] - 280, 1050, L5["ag_y"] + 170))
    S["bg"].update(red=0.7 + 0.25 * kick(t), flames=0.55 + 0.35 * (t > T["l5_ogon"]), smoke=0.7, underlight=0.8)
    S["embers"].update(amount=1.0, count=1.0, speed=1.6)
    S["cam"]["rot"] += 1.6 * math.sin((t - 12.32) * 1.9)
    if tya - 0.02 < t < tya + 0.16:
        S["cam"]["zoom_blur"] = 0.15 * (1 - abs((t - tya - 0.03) / 0.13))
    S["fade"] = 1 - 0.82 * smooth((t - 16.13) / 0.08)
    # whiteout tail from the line-4 transition
    wt = decay(t, T["l5_ty"], 0.09)
    S["flash"] = tuple(f + c * wt * 0.9 for f, c in zip(S["flash"], (1.0, 0.75, 0.5)))


# ====================================================================== frame
def frame(t):
    t = max(0.0, t)
    S = dict(items=[], cam=dict(zoom=1.0, rot=0.0, x=0.0, y=0.0), flash=(0.0, 0.0, 0.0), glitch=0.0, chroma=0.0,
             bg=dict(red=0.4, smoke=0.6, flames=0.0, underlight=0.4, bright=1.0), embers=dict(amount=0.4, count=0.4, speed=1.0),
             heat=None, rings=[], puffs=PUFFS, fade=1.0, bloom=1.0)
    # intro: everything fades in from the first frame (no pure-black frames)
    intro = 1 - smooth((t - 0.1) / 0.3)
    S["bg"]["bright"] = 1.0 + 0.6 * intro
    for fn in (line1, line2, line3, line4, line5):
        fn(t, S)
    k = kick(t)
    S["bg"]["bright"] *= 1 + 0.22 * k
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
            S["rings"].append((x, y, maxr * out_expo(f * 0.8), th * (1 + 1.5 * f), 0.7 * br * (1 - f) ** 4, dist * (1 - f) ** 1.5))
    S["glitch"] = min(S["glitch"], 1.0)
    return S
