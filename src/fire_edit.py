"""TOLY SUMMER × EMINEM — v3 "fire lyric" edit.

Style of style_reference_v3.mov: pure black, very wide heavy type (Unbounded Black),
white words with an orange 3D edge, key words burning orange with glow, sparks,
words burning away, emoji stickers. The two faces are original-photo cut-outs with no
background, used as stickers that move only as a whole (never altered).

Timeline (s): 0 intro | 2.05 Toly | 4.45 L1 | 6.55 L2 | 8.55 L3 | 10.55 L4 | 12.58 finale | 15.0
"""
import math, os
import cv2, numpy as np, skia
from core import *
from fx import Embers, Dust

SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
LY = T['lyrics']
FONTS = os.path.join(ROOT, 'assets', 'fonts')
TF_CYR = skia.Typeface.MakeFromFile(os.path.join(FONTS, 'Unbounded-Black-cyrillic.ttf'))
TF_LAT = skia.Typeface.MakeFromFile(os.path.join(FONTS, 'Unbounded-Black-latin.ttf'))
TF_EMO = skia.Typeface.MakeFromFile('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf')


def wt(who, line, k, lead=0.03):
    return LY[who][line][k][1][0] - lead


class MixFont:
    """Unbounded ships Cyrillic and Latin as separate files: pick the face per character."""
    def __init__(self, size):
        self.size = size
        self.cyr, self.lat = skia.Font(TF_CYR, size), skia.Font(TF_LAT, size)
        for f in (self.cyr, self.lat):
            f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True)

    def getSize(self):
        return self.size

    def pick(self, ch):
        return self.cyr if 0x400 <= ord(ch) <= 0x4FF else self.lat

    def measureText(self, text):
        return sum(self.pick(ch).measureText(ch) for ch in text)


def ufont(text, size):
    return MixFont(size)


# ------------------------------------------------------------------ sprites
def _load_rgba(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return skia.Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGRA2RGBA), colorType=skia.kRGBA_8888_ColorType).withDefaultMipmaps()


FACE = {n: _load_rgba(os.path.join(ROOT, 'assets', 'photos', f'{n}_face.png')) for n in ('toly', 'eminem')}
EMO = {}


def emoji_img(ch):
    if ch not in EMO:
        s = skia.Surface(170, 170)
        c = s.getCanvas(); c.clear(skia.ColorTRANSPARENT)
        f = skia.Font(TF_EMO, 109)
        w = f.measureText(ch)
        c.drawString(ch, (170 - w) / 2, 128, f, skia.Paint(AntiAlias=True))
        EMO[ch] = s.makeImageSnapshot().withDefaultMipmaps()
    return EMO[ch]


def sprite(c, img, cx, cy, h, rot=0.0, alpha=1.0, glow=0.0, glow_col='#ff6a1a'):
    """Draw an image (face cut-out / emoji) as one rigid object."""
    if alpha <= 0.005 or h < 2:
        return
    k = h / img.height()
    c.save(); c.translate(cx, cy); c.rotate(rot); c.scale(k, k)
    if glow > 0:
        gp = skia.Paint()
        gp.setImageFilter(skia.ImageFilters.DropShadowOnly(0, 0, 26 / k, 26 / k, C(glow_col, glow * alpha), None))
        c.drawImage(img, -img.width() / 2, -img.height() / 2, SAMP, gp)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    c.drawImage(img, -img.width() / 2, -img.height() / 2, SAMP, p)
    c.restore()


def pop(t, t0, t1=None, dur_in=0.32, dur_out=0.22):
    """Scale envelope: back-ease pop in at t0, quick shrink out at t1."""
    s = e_back(prog(t, t0, t0 + dur_in), 2.2) if t >= t0 else 0.0
    if t1 is not None and t > t1:
        s *= 1 - e_in(prog(t, t1, t1 + dur_out))
    return s


def face(c, t, name, cx, cy, h, t0, t1=None, rot=0.0, glow=0.85, bob=True):
    s = pop(t, t0, t1)
    if s <= 0.001:
        return
    if bob:
        cy += -beat_pulse(t, 8) * 18 + math.sin(t * 2.3) * 8
        rot += math.sin(t * 1.7) * 3 + (beat_pulse(t, 9) * 3 * (1 if int(t / 0.5) % 2 else -1))
        s *= 1 + 0.045 * beat_pulse(t, 10)
    sprite(c, FACE[name], cx, cy, h * s, rot, 1.0, glow)


def emoji(c, t, ch, cx, cy, h, t0, t1=None, rot=0.0, float_amp=10):
    s = pop(t, t0, t1)
    if s <= 0.001:
        return
    sprite(c, emoji_img(ch), cx, cy + math.sin(t * 3 + cx) * float_amp, h * s,
           rot + math.sin(t * 2.4 + cy) * 6, 1.0, 0.35, '#ff8a2a')


# ------------------------------------------------------------------ type
HOT_FILL = ['#fff6c0', '#ffd25a', '#ff9a24', '#ff5a10']


def draw_word_glyph(c, ch, f, x, y, style, t, alpha, heat=0.0):
    """One character. style: 'white' | 'hot' | 'hollow'. heat 0..1 turns white into fire (burn-out)."""
    size = f.getSize()
    blob = skia.TextBlob.MakeFromString(ch, f.pick(ch))
    if blob is None or alpha <= 0.003:
        return
    top, bot = y - size * 0.78, y + size * 0.05
    hot = style == 'hot' or heat > 0.5
    if style == 'hollow' and heat < 0.5:
        c.drawTextBlob(blob, x, y, P('#ff7a1a', alpha * 0.5, stroke=size * 0.05, blur=size * 0.08, blend=ADD))
        c.drawTextBlob(blob, x, y, P('#fff1e0', alpha, stroke=max(2.5, size * 0.03)))
        return
    # 3D edge (down-right), orange for white text, deep red-orange for hot text
    depth = max(3, int(size * 0.075))
    edge_a, edge_b = ('#ff7a1a', '#7a2006') if not hot else ('#c2360c', '#3a0a04')
    for i in range(depth, 0, -max(1, depth // 7)):
        k = i / depth
        col = '#%02x%02x%02x' % tuple(int(lerp(int(edge_a[j:j + 2], 16), int(edge_b[j:j + 2], 16), k)) for j in (1, 3, 5))
        c.drawTextBlob(blob, x + i * 0.45, y + i, P(col, alpha))
    if hot:
        fl = 0.85 + 0.15 * math.sin(t * 23 + x * 0.01)
        c.drawTextBlob(blob, x, y, P('#ff5a10', alpha * 0.55 * fl, blur=size * 0.22, blend=ADD))
        c.drawTextBlob(blob, x, y, P('#ff8a2a', alpha * 0.6 * fl, blur=size * 0.07, blend=ADD))
        sh = lin(0, top, 0, bot, HOT_FILL, [0, 0.35, 0.7, 1.0])
        c.drawTextBlob(blob, x, y, P('#ffffff', alpha, shader=sh))
    else:
        c.drawTextBlob(blob, x, y, P('#000000', alpha * 0.35, blur=size * 0.12))
        c.drawTextBlob(blob, x, y, P('#ffffff', alpha, shader=lin(0, top, 0, bot, ['#ffffff', '#f3ece4', '#e2d6c8'])))
        if heat > 0:
            sh = lin(0, top, 0, bot, HOT_FILL, [0, 0.35, 0.7, 1.0])
            c.drawTextBlob(blob, x, y, P('#ffffff', alpha * clamp(heat * 2), shader=sh))


class W_:
    def __init__(self, text, t0, style='white', size=1.0, ent='pop', under=False, burn=None):
        self.text, self.t0, self.style, self.size, self.ent, self.under, self.burn = text, t0, style, size, ent, under, burn


class Lyric:
    """Stacked centred lines of words; whole block can tilt in 3D, drift and burn away."""
    def __init__(self, lines, cy, size=120, max_w=880, tilt=0.0, rot=0.0, cx=W / 2, gap=0.28, lead=1.12):
        self.cx, self.cy, self.tilt, self.rot = cx, cy, tilt, rot
        rows, y = [], 0.0
        for line in lines:
            fs = [ufont(w.text, size * w.size) for w in line]
            wd = [f.measureText(w.text) for f, w in zip(fs, line)]
            sp = size * gap
            tot = sum(wd) + sp * (len(line) - 1)
            if tot > max_w:
                k = max_w / tot
                fs = [ufont(w.text, size * w.size * k) for w in line]
                wd = [f.measureText(w.text) for f, w in zip(fs, line)]
                sp *= k
                tot = sum(wd) + sp * (len(line) - 1)
            lh = max(f.getSize() for f in fs) * 0.82
            y += lh
            x = -tot / 2
            for f, w, d in zip(fs, line, wd):
                rows.append(dict(w=w, f=f, x=x, y=y, width=d,
                                 xs=[f.measureText(w.text[:i]) for i in range(len(w.text))],
                                 cw=[f.measureText(ch) for ch in w.text]))
                x += d + sp
            y += lh * (lead - 1) + size * 0.12
        self.items = rows
        self.h = y
        for it in rows:
            it['y'] -= y / 2  # centre vertically on cy

    def draw(self, c, t, burn_t=None, drift=(0, 0), extra_rot=0.0, scale=1.0):
        c.save()
        c.translate(self.cx + drift[0], self.cy + drift[1])
        c.rotate(self.rot + extra_rot)
        c.scale(scale, scale)
        if self.tilt:
            m = skia.Matrix(); m.setAll(1, 0, 0, 0, 1, 0, self.tilt * 0.0006, 0, 1)
            c.concat(m)
        for it in self.items:
            self._word(c, t, it, burn_t if it['w'].burn is None else it['w'].burn)
        c.restore()

    def _word(self, c, t, it, burn_t):
        w, f = it['w'], it['f']
        lt = t - w.t0
        if lt < 0:
            return
        size = f.getSize()
        n = len(w.text)
        bt = (t - burn_t) if burn_t is not None else -1
        if bt > 0.75:
            return
        if w.under:
            up = e_out(prog(t, w.t0 + 0.1, w.t0 + 0.4)) * (1 - prog(bt, 0, 0.3) if bt > 0 else 1)
            if up > 0:
                yb = it['y'] + size * 0.2
                c.drawRect(skia.Rect(it['x'], yb, it['x'] + it['width'] * up, yb + size * 0.07),
                           P('#ff7a1a', 1))
                c.drawRect(skia.Rect(it['x'], yb, it['x'] + it['width'] * up, yb + size * 0.07),
                           P('#ff5a10', 0.6, blur=size * 0.08, blend=ADD))
        for i, ch in enumerate(w.text):
            if ch == ' ':
                continue
            d = i * 0.03
            p = clamp((lt - d) / 0.28)
            if p <= 0:
                continue
            dx = dy = rot = 0.0
            sx = sy = 1.0
            a = clamp(p * 4)
            if w.ent == 'pop':
                s = e_back(p, 2.6); sx = sy = lerp(0.3, 1.0, s); dy = lerp(size * 0.4, 0, e_out(p))
            elif w.ent == 'slam':
                s = lerp(2.2, 1.0, e_out(p)); sx = sy = s; a = clamp(p * 6)
            elif w.ent == 'side':
                dx = lerp(-size * 2.5, 0, e_out(p)); rot = lerp(-25, 0, e_out(p))
            elif w.ent == 'drop':
                dy = lerp(-size * 1.6, 0, e_back(p, 1.8)); rot = lerp((rnd(i, n) - 0.5) * 40, 0, e_out(p))
            elif w.ent == 'flip':
                sy = math.cos((1 - e_back(p, 1.5)) * math.pi / 2) if p < 1 else 1.0
            heat = 0.0
            if bt > 0:   # burn away: heat up, flicker, rise, crumble into sparks
                q = clamp((bt - (i / max(1, n)) * 0.15) / 0.5)
                heat = clamp(q * 3)
                a *= (1 - e_in(q)) * (0.6 + 0.4 * (int(t * 60 + i) % 3 != 0))
                dy -= q * size * 0.5
                self._sparks(c, it, i, q, size)
            dy -= beat_pulse(t, 10) * size * 0.04
            lx = it['x'] + it['xs'][i]
            px, py = lx + it['cw'][i] / 2, it['y'] - size * 0.38
            c.save(); c.translate(px + dx, py + dy); c.rotate(rot); c.scale(sx, sy); c.translate(-px, -py)
            draw_word_glyph(c, ch, f, lx, it['y'], w.style, t, a, heat)
            c.restore()

    @staticmethod
    def _sparks(c, it, i, q, size):
        if q <= 0 or q >= 1:
            return
        x0 = it['x'] + it['xs'][i]
        cw = it['cw'][i]
        for k in range(9):
            sx = x0 + rnd(k * 31 + i, 4) * cw
            sy = it['y'] - rnd(k * 17 + i, 5) * size * 0.75
            vy = -(120 + 260 * rnd(k + i * 7, 6)) * q
            vx = (rnd(k + i * 3, 7) - 0.5) * 120 * q
            a = (1 - q) * (0.6 + 0.4 * rnd(k, 8))
            r = 2 + 3 * rnd(k + i, 9)
            c.drawCircle(sx + vx, sy + vy, r * 2.5, P('#ff6a1a', a * 0.4, blend=ADD))
            c.drawCircle(sx + vx, sy + vy, r, P('#ffe7a0', a))


# ------------------------------------------------------------------ background
SPARKS = Embers(55, 21)
ASH = Dust(90, 22, depth=(400, 3000))


def background(c, t, heat=0.4):
    c.clear(C('#000000'))
    # faint warm haze from below + drifting sparks (like the reference)
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffffff', shader=rad(W / 2, H * 1.05, H * 0.7,
               [C('#ff4a10', 0.20 * heat), C('#ff4a10', 0)])))
    c.drawRect(skia.Rect(0, 0, W, H), P('#ffffff', shader=rad(W / 2, H * 0.45, H * 0.6,
               [C('#3a0c06', 0.35 * heat), C('#000000', 0)])))
    SPARKS.draw(c, t, H + 30, alpha=0.55 + 0.4 * heat, boost=0.6)
    ASH.draw(c, t, t * 90, alpha=0.35, color='#ff9a4a', twinkle=True)


def cam(c, zoom=1.0, rot=0.0, dx=0.0, dy=0.0, cx=W / 2, cy=H / 2):
    c.translate(cx + dx, cy + dy); c.rotate(rot); c.scale(zoom, zoom); c.translate(-cx, -cy)


SH = Shake(11)


def shake(t, hits, amp=14, dur=0.25):
    a = 0
    for h in hits:
        if h <= t < h + dur:
            a = max(a, amp * (1 - (t - h) / dur) ** 2)
    return SH.at(t, a)


# ------------------------------------------------------------------ blocks
TG = [wt('toly', 0, k) for k in range(4)]
E1 = [wt('eminem', 0, k) for k in range(8)]
E2 = [wt('eminem', 1, k) for k in range(5)]
E3 = [wt('eminem', 2, k) for k in range(6)]
E4 = [wt('eminem', 3, k) for k in range(7)]
FIN = 12.58

B_TOLY = Lyric([[W_('ГОРИ,', TG[0], 'white', 1.35, 'pop', under=True)],
                [W_('Я', TG[1], 'white', 0.95, 'pop'), W_('ГОРЮ', TG[2], 'hot', 0.95, 'pop')],
                [W_('ТОЖЕ', TG[3], 'hot', 1.5, 'slam')]], cy=1180, size=150, tilt=0.0)
B_L1a = Lyric([[W_('NOW,', E1[0], 'white', 1.5, 'slam', under=True)],
               [W_('THIS', E1[1], 'white', 0.75, 'pop'), W_('LOOKS', E1[2], 'white', 0.75, 'pop'),
                W_('LIKE', E1[3], 'white', 0.75, 'pop'), W_('A', E1[4], 'white', 0.75, 'pop')]],
              cy=1090, size=150, tilt=-0.4, rot=-4)
B_L1b = Lyric([[W_('JOB', E1[5], 'hot', 1.7, 'slam')],
               [W_('FOR', E1[6], 'white', 0.7, 'side'), W_('ME', E1[7], 'hot', 1.0, 'pop', under=True)]],
              cy=1500, size=150, tilt=0.5, rot=3)
B_L2 = Lyric([[W_('SO', E2[0], 'white', 0.8, 'drop')],
              [W_('EVERYBODY,', E2[1], 'hot', 1.0, 'drop')],
              [W_('JUST', E2[2], 'white', 0.6, 'flip')],
              [W_('FOLLOW', E2[3], 'white', 1.05, 'side', under=True)],
              [W_('ME', E2[4], 'hot', 1.3, 'pop')]], cy=1180, size=150, max_w=780, tilt=0.15, rot=-3)
B_L3a = Lyric([[W_('’CAUSE', E3[0], 'white', 0.75, 'flip'), W_('WE', E3[1], 'white', 0.75, 'flip')],
               [W_('NEED', E3[2], 'white', 1.2, 'pop', under=True)],
               [W_('A', E3[3], 'white', 0.6, 'pop'), W_('LITTLE', E3[4], 'white', 0.6, 'pop')]],
              cy=880, size=150, tilt=-0.3, rot=2)
B_L3b = Lyric([[W_('CONTROVERSY', E3[5], 'hot', 1.0, 'slam')]], cy=1330, size=160, max_w=900, rot=-10)
B_L4a = Lyric([[W_('’CAUSE', E4[0], 'white', 0.62, 'pop'), W_('IT', E4[1], 'white', 0.62, 'pop')],
               [W_('FEELS', E4[2], 'white', 0.62, 'pop'), W_('SO', E4[3], 'white', 0.62, 'pop')],
               [W_('EMPTY', E4[4], 'hollow', 1.45, 'pop')]], cy=960, size=150, tilt=0.4, rot=-3)
B_L4b = Lyric([[W_('WITHOUT', E4[5], 'hot', 1.05, 'slam')],
               [W_('ME', E4[6], 'hot', 1.9, 'slam', under=True)]], cy=1400, size=150, rot=2)
B_FIN = Lyric([[W_('TOLY', FIN + 0.35, 'white', 0.85, 'pop'), W_('SUMMER', FIN + 0.45, 'white', 0.85, 'pop')],
               [W_('×', FIN + 0.70, 'hot', 1.0, 'slam')],
               [W_('EMINEM', FIN + 0.90, 'hot', 1.25, 'slam', under=True)]], cy=1430, size=130)


# ------------------------------------------------------------------ frame
def render(t):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    heat = 0.35 + 0.35 * beat_pulse(t, 6) * (t > 2.05)
    background(c, t, heat)
    hits = [TG[0], TG[3], E1[0], E1[5], E2[1], E2[3], E3[5], E4[5], E4[6], FIN]
    dx, dy, rr = shake(t, hits, 16)
    c.save()
    cam(c, 1.0 + 0.025 * beat_pulse(t, 9), rot=rr * 12 + 1.2 * math.sin(t * 0.6), dx=dx, dy=dy)

    # ---------- intro: a single flame breathing in the dark, Toly's face rises out of the glow
    if t < 2.4:
        fl = pop(t, 0.05, 2.0)
        sprite(c, emoji_img('🔥'), W / 2, 960 - 30 * e_in(prog(t, 1.4, 2.0)),
               lerp(120, 260, prog(t, 0, 2.0)) * fl * (1 + 0.18 * math.exp(-max(0, t - 1.03) * 7) * (t > 1.03)),
               math.sin(t * 7) * 3, 1, 0.9 + 0.1 * math.sin(t * 20))
        c.drawCircle(W / 2, 960, 500, P('#ffffff', shader=rad(W / 2, 960, 500, [C('#ff5a10', 0.28 * fl), C('#ff5a10', 0)]), blend=ADD))
    # ---------- Toly 2.05 - 4.45
    face(c, t, 'toly', W / 2, 560, 760, 1.75, 4.42, glow=0.9)
    emoji(c, t, '🔥', 170, 330, 170, TG[0], 4.42, rot=-12)
    emoji(c, t, '❤', W / 2, 1680, 210, TG[3], 4.42)
    B_TOLY.draw(c, t, burn_t=4.40)
    # ---------- Eminem L1 4.45 - 6.55
    face(c, t, 'eminem', 720, 520, 720, 4.50, 6.42, rot=6)
    emoji(c, t, '🎤', 220, 470, 190, E1[1], 6.4, rot=-20)
    B_L1a.draw(c, t, burn_t=6.36)
    B_L1b.draw(c, t, burn_t=6.40)
    # ---------- L2 6.55 - 8.55: face leads, the words follow it
    if 6.45 < t < 8.7:
        fol = e_io(prog(t, E2[3], 8.40))
        fx = lerp(W / 2, 300, e_out(prog(t, 6.5, 6.8)))
        fx = lerp(fx, 790, fol)
        face(c, t, 'eminem', fx, lerp(470, 430, fol), 620, 6.50, 8.44, rot=lerp(-6, 8, fol))
        for k, ch_ in enumerate(['🙌', '👥', '🙌']):
            emoji(c, t, ch_, 180 + k * 360, 1760, 140, E2[1] + k * 0.06, 8.42)
    B_L2.draw(c, t, burn_t=8.40, drift=(lerp(0, 40, prog(t, E2[3], 8.4)), 0))
    # ---------- L3 8.55 - 10.55
    if 8.45 < t < 10.7:
        face(c, t, 'eminem', W / 2, 400, 560, 8.50, 10.45, rot=-4)
        emoji(c, t, '😈', 900, 640, 160, E3[5], 10.45, rot=12)
        emoji(c, t, '😎', 170, 1680, 150, E3[2], 10.45, rot=-10)
    B_L3a.draw(c, t, burn_t=10.40)
    jit = (rnd(int(t * 30), 3) - 0.5) * 18 * (1 - prog(t, E3[5], E3[5] + 0.5)) * (t > E3[5])
    B_L3b.draw(c, t, burn_t=10.42, drift=(jit, 0), scale=1 + 0.08 * beat_pulse(t, 8))
    # ---------- L4 10.55 - 12.58: the face shrinks into emptiness, then fills the frame on "ME"
    if 10.5 < t < FIN + 0.1:
        big = e_out(prog(t, E4[6] - 0.02, E4[6] + 0.12))
        h = lerp(lerp(560, 330, e_out(prog(t, 10.6, E4[5]))), 760, big)
        face(c, t, 'eminem', W / 2, lerp(440, 520, big), h, 10.55, FIN - 0.05, glow=0.6 + 0.4 * big)
        emoji(c, t, '💨', 820, 1080, 130, E4[4], E4[5])
    B_L4a.draw(c, t, burn_t=E4[5] - 0.05)
    B_L4b.draw(c, t, burn_t=FIN - 0.08)
    # ---------- finale: both faces, title, everything burns out
    if t >= FIN - 0.05:
        end = 14.25
        face(c, t, 'toly', 300, 720, 600, FIN, end, rot=-7)
        face(c, t, 'eminem', 790, 700, 600, FIN + 0.12, end + 0.08, rot=7)
        for k, (x, y, r) in enumerate([(120, 330, -15), (960, 300, 14), (W / 2, 1830, 0)]):
            emoji(c, t, '🔥', x, y, 140 + 30 * (k == 2), FIN + 0.2 + k * 0.1, end, rot=r)
        B_FIN.draw(c, t, burn_t=end)
    c.restore()
    # flashes on the big hits
    for h_, a_ in ((2.05, 0.55), (E4[6], 0.35), (FIN, 0.6)):
        c.drawRect(skia.Rect(0, 0, W, H), P('#ffb070', a_ * (1 - prog(t, h_, h_ + 0.25)) * (t >= h_), blend=ADD))
    c.drawRect(skia.Rect(0, 0, W, H), P('#000000', e_in(prog(t, 14.55, 14.95))))
    return surf
