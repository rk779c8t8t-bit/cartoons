"""Shared helpers: timing, easing, noise, palette, skia paints, kinetic type."""
import json, math, os
import numpy as np
import skia

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
T = json.load(open(os.path.join(ROOT, 'assets', 'timing.json')))
PRE = T['pre']
DUR = T['dur']
BEATS = np.array(T['beats'])
VOC = np.array(T['voc_env'])
KICK = np.array(T['kick'])
ENV_RATE = T['env_rate']

FONT_PATH = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FONT_PATH_XB = '/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf'
TF = skia.Typeface.MakeFromFile(FONT_PATH)
TF_XB = skia.Typeface.MakeFromFile(FONT_PATH_XB)


def C(hexs, a=1.0):
    hexs = hexs.lstrip('#')
    r, g, b = int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16)
    return skia.Color(r, g, b, int(255 * max(0, min(1, a))))


PAL = dict(
    black='#070204', night='#14050a', burg='#3a0a12', wine='#5c0f1c', red='#b5121b',
    hot='#e8321e', orange='#f5761a', yellow='#ffc93c', cream='#f6e6c4', gold='#e2a93b',
    gold_hi='#ffe7a1', gold_dk='#8a5212', brown='#3b1606', ink='#1c0710',
)


# ---------------------------------------------------------------- math / easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, t):
    return a + (b - a) * t


def sstep(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else float(t >= a)


def e_out(t):
    return 1 - (1 - t) ** 3


def e_in(t):
    return t ** 3


def e_io(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def e_back(t, s=1.7):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def e_elastic(t):
    if t <= 0: return 0.0
    if t >= 1: return 1.0
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi / 3)) + 1


def noise1(x, seed=0):
    """Smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i
    def h(n):
        n = (n * 374761393 + seed * 668265263) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 32767.5 - 1
    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def rnd(i, seed=0):
    return (noise1(i + 0.0, seed * 31 + 7) + 1) / 2


# ---------------------------------------------------------------- audio sync
def voc_at(t):
    i = (t - PRE) * ENV_RATE
    if i < 0 or i >= len(VOC) - 1:
        return 0.0
    i0 = int(i)
    return float(VOC[i0] * (1 - (i - i0)) + VOC[i0 + 1] * (i - i0))


def kick_at(t):
    i = int((t - PRE) * ENV_RATE)
    if i < 0 or i >= len(KICK):
        return 0.0
    return float(KICK[max(0, i - 1):i + 2].max())


def beat_pulse(t, decay=7.0):
    past = BEATS[BEATS <= t]
    if len(past) == 0:
        return 0.0
    return math.exp(-(t - past[-1]) * decay)


def beat_phase(t):
    past = BEATS[BEATS <= t]
    if len(past) == 0:
        return 0.0, -1
    i = len(past) - 1
    nxt = BEATS[i + 1] if i + 1 < len(BEATS) else past[-1] + 0.51
    return (t - past[-1]) / (nxt - past[-1]), i


def syllable_mouth(t, syllables, end):
    """Mouth opening 0..1 driven by syllable schedule, modulated by vocal energy."""
    m = 0.0
    for k, s in enumerate(syllables):
        nxt = syllables[k + 1] if k + 1 < len(syllables) else end
        d = max(0.08, nxt - s)
        if s - 0.03 <= t <= nxt:
            u = (t - s + 0.03) / (d + 0.03)
            shape = math.sin(math.pi * clamp(u * 1.15)) ** 0.7
            m = max(m, shape)
    v = clamp(voc_at(t) * 1.3)
    return clamp(m * (0.55 + 0.6 * v))


# ---------------------------------------------------------------- paints
def P(color='#ffffff', a=1.0, stroke=0, blur=0, shader=None, blend=None, cap=None):
    p = skia.Paint(AntiAlias=True)
    p.setColor(C(color, a) if isinstance(color, str) else color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        p.setStrokeCap(cap if cap is not None else skia.Paint.kRound_Cap)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
        if isinstance(color, str) and a < 1:
            p.setAlphaf(a)
    if blend is not None:
        p.setBlendMode(blend)
    return p


def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [C(c) if isinstance(c, str) else c for c in cols], pos)


def rad(cx, cy, r, cols, pos=None):
    return skia.GradientShader.MakeRadial((cx, cy), max(1, r), [C(c) if isinstance(c, str) else c for c in cols], pos)


ADD = skia.BlendMode.kPlus
SCREEN = skia.BlendMode.kScreen


def path_poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def star4(canvas, x, y, r, color='#fff3c4', a=1.0):
    if r <= 0.3 or a <= 0.01:
        return
    p = skia.Path()
    k = r * 0.18
    p.moveTo(x, y - r); p.quadTo(x + k, y - k, x + r, y); p.quadTo(x + k, y + k, x, y + r)
    p.quadTo(x - k, y + k, x - r, y); p.quadTo(x - k, y - k, x, y - r); p.close()
    canvas.drawCircle(x, y, r * 0.9, P(color, a * 0.35, blur=r * 0.6, blend=ADD))
    canvas.drawPath(p, P(color, a))


# ---------------------------------------------------------------- kinetic type
def font(size, xb=False, condense=0.86):
    f = skia.Font(TF_XB if xb else TF, size)
    f.setScaleX(condense)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def text_width(text, f):
    return f.measureText(text)


def gold_shader(top, bottom):
    return lin(0, top, 0, bottom, ['#fff6c8', '#ffd76a', '#e9a93a', '#b8741c', '#ffcf6b'],
               [0, 0.3, 0.55, 0.82, 1.0])


def fire_shader(top, bottom, t):
    o = 0.08 * math.sin(t * 9)
    return lin(0, top, 0, bottom, ['#fff7d6', '#ffd34a', '#ff8a1c', '#e8321e', '#8f0d14'],
               [0, 0.22 + o, 0.5 + o, 0.78, 1.0])


def draw_glyphs(canvas, text, f, x, y, style='gold', t=0.0, depth=None, alpha=1.0, glow=None,
                outline=None):
    """Draw text with extrusion + outline + fill. (x, y) = left baseline."""
    size = f.getSize()
    if alpha <= 0.003:
        return
    blob = skia.TextBlob.MakeFromString(text, f)
    if blob is None:
        return
    depth = int(size * 0.09) if depth is None else depth
    top, bot = y - size * 0.74, y + size * 0.02
    if glow:
        canvas.drawTextBlob(blob, x, y, P(glow[0], alpha * glow[1], blur=size * 0.18, blend=ADD))
    if style == 'hollow':
        canvas.drawTextBlob(blob, x, y, P('#ffe7a1', alpha, stroke=max(2, size * 0.035)))
        return
    ext_col = {'gold': '#4a1d06', 'cream': '#3b0710', 'fire': '#5a0a0a', 'red': '#24040a',
               'white': '#3b0710', 'dark': '#000000'}.get(style, '#2b0a08')
    if depth > 0:
        stepc = max(1, depth // 10)
        for i in range(depth, 0, -stepc):
            canvas.drawTextBlob(blob, x + i * 0.55, y + i, P(ext_col, alpha))
    ol = outline if outline is not None else max(2.0, size * 0.045)
    canvas.drawTextBlob(blob, x, y, P('#1a0508', alpha, stroke=ol))
    if style == 'gold':
        fill = P('#ffffff', alpha, shader=gold_shader(top, bot))
    elif style == 'fire':
        fill = P('#ffffff', alpha, shader=fire_shader(top, bot, t))
    elif style == 'cream':
        fill = P('#f6e6c4', alpha)
    elif style == 'red':
        fill = P('#ffffff', alpha, shader=lin(0, top, 0, bot, ['#ff5a3c', '#c8141d', '#7d0a12']))
    elif style == 'white':
        fill = P('#fffaf0', alpha)
    else:
        fill = P(style, alpha)
    fill.setAlphaf(alpha)
    canvas.drawTextBlob(blob, x, y, fill)
    if style in ('gold', 'fire'):
        # specular sweep
        sw = (t * 0.9) % 2.2 - 0.6
        sh = skia.GradientShader.MakeLinear(
            [(x + sw * 900 - 200, top), (x + sw * 900 + 200, bot)],
            [C('#ffffff', 0), C('#ffffff', 0.55), C('#ffffff', 0)], [0.35, 0.5, 0.65])
        canvas.drawTextBlob(blob, x, y, P('#ffffff', alpha * 0.8, shader=sh, blend=ADD))


def glyph_layout(text, f):
    """Per-character x offsets (left) using per-char measurement with kerning approx."""
    xs, acc = [], 0.0
    for i, ch in enumerate(text):
        xs.append(acc)
        acc = f.measureText(text[:i + 1])
    return xs, acc


def pill(canvas, x0, y0, x1, y1, p, color='#e2a93b', width=6, alpha=1.0):
    """Outlined rounded capsule drawn on progressively (like the reference highlights)."""
    if p <= 0:
        return
    path = skia.Path()
    path.addRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), (y1 - y0) / 2, (y1 - y0) / 2))
    pt = P(color, alpha, stroke=width)
    if p < 0.999:
        pe = skia.TrimPathEffect.Make(0, clamp(p))
        if pe is not None:
            pt.setPathEffect(pe)
    canvas.drawPath(path, P(color, alpha * 0.5, stroke=width * 3, blur=width * 2, blend=ADD))
    canvas.drawPath(path, pt)


class Shake:
    def __init__(self, seed):
        self.seed = seed

    def at(self, t, amp):
        return (noise1(t * 23, self.seed) * amp, noise1(t * 23, self.seed + 5) * amp,
                noise1(t * 17, self.seed + 9) * amp * 0.004)
