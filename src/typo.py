"""Kinetic typography: per-letter entrances, highlight capsules, glitch, exits."""
import math
import skia
from core import *


class Word:
    def __init__(self, text, t0, style='cream', ent='drop', size=1.0, pill=False, glow=None, exit_kind=None,
                 depth=None):
        self.text, self.t0, self.style, self.ent, self.size = text, t0, style, ent, size
        self.pill, self.glow, self.exit_kind, self.depth = pill, glow, exit_kind, depth


class Block:
    """Lines of words laid out centered at cx starting at y_top."""
    def __init__(self, lines, cx=W / 2, y_top=260, size=130, max_w=960, gap=0.22, line_gap=1.02, condense=0.86):
        self.lines = lines
        self.cx, self.y_top, self.size, self.max_w = cx, y_top, size, max_w
        self.items = []
        y = y_top
        for line in lines:
            # fit line to width
            fs = []
            for w in line:
                fs.append(font(size * w.size, condense=condense))
            sp = size * gap
            widths = [f.measureText(w.text) for f, w in zip(fs, line)]
            total = sum(widths) + sp * (len(line) - 1)
            k = min(1.0, max_w / total)
            if k < 1:
                fs = [font(size * w.size * k, condense=condense) for w in line]
                widths = [f.measureText(w.text) for f, w in zip(fs, line)]
                sp *= k
                total = sum(widths) + sp * (len(line) - 1)
            lh = max(f.getSize() for f in fs)
            y += lh * 0.78
            x = cx - total / 2
            for f, w, wd in zip(fs, line, widths):
                xs = [f.measureText(w.text[:i]) for i in range(len(w.text))]
                cw = [f.measureText(ch) for ch in w.text]
                self.items.append(dict(w=w, f=f, x=x, y=y, width=wd, xs=xs, cw=cw))
                x += wd + sp
            y += lh * (line_gap - 0.78) + lh * 0.12
        self.bottom = y

    def draw(self, c, t, exit_t=None, exit_kind='up', alpha=1.0):
        for it in self.items:
            draw_word(c, t, it, exit_t, it['w'].exit_kind or exit_kind, alpha)


def _entrance(ent, lt, i, n, seed):
    """Returns (dx, dy, sx, sy, rot, a) for letter i at local time lt."""
    d = i * 0.028
    if ent == 'slam':
        p = clamp((lt - i * 0.012) / 0.22)
        s = lerp(2.8, 1.0, e_back(p, 1.2))
        return 0, 0, s, s, 0, clamp(p * 4)
    if ent == 'drop':
        p = clamp((lt - d) / 0.30)
        return 0, lerp(-240, 0, e_back(p, 2.0)), 1, 1, lerp((rnd(i, seed) - 0.5) * 50, 0, e_out(p)), clamp(p * 3)
    if ent == 'rise':
        p = clamp((lt - d) / 0.28)
        return 0, lerp(150, 0, e_out(p)), 1, lerp(0.0, 1.0, e_back(p, 1.5)), 0, clamp(p * 3)
    if ent == 'flip':
        p = clamp((lt - d * 1.3) / 0.34)
        return 0, 0, 1, math.cos((1 - e_back(p, 1.6)) * math.pi / 2) if p < 1 else 1, 0, clamp(p * 3)
    if ent == 'zoom':
        p = clamp((lt - d * 0.5) / 0.26)
        s = lerp(0.1, 1.0, e_back(p, 1.4))
        return 0, 0, s, s, lerp(-30, 0, e_out(p)), clamp(p * 2.5)
    if ent == 'glitch':
        p = clamp((lt - i * 0.02) / 0.35)
        j = (1 - p) ** 2
        return (rnd(i * 7 + int(lt * 40), seed) - 0.5) * 160 * j, (rnd(i * 3 + int(lt * 40), seed + 1) - 0.5) * 60 * j, \
            1, 1 + j * 0.6, (rnd(i, seed + 2) - 0.5) * 40 * j, (1.0 if p > 0.02 else 0) * (0.4 + 0.6 * (int(lt * 60) % 3 != 0 or p > 0.6))
    if ent == 'snake':
        p = clamp((lt - i * 0.05) / 0.45)
        e = e_out(p)
        return lerp(-700, 0, e), math.sin((1 - e) * 9 + i) * 140 * (1 - e), 1, 1, math.sin((1 - e) * 9 + i) * 25 * (1 - e), clamp(p * 4)
    if ent == 'type':
        p = 1.0 if lt >= i * 0.03 else 0.0
        return 0, 0, 1, 1, 0, p
    return 0, 0, 1, 1, 0, clamp(lt * 5)


def _exit(kind, et, i, n, seed):
    if et <= 0:
        return 0, 0, 1, 1, 0, 1
    d = (i / max(1, n)) * 0.12
    p = clamp((et - d) / 0.3)
    if kind == 'up':
        return 0, -260 * e_in(p), 1, 1, 0, 1 - p
    if kind == 'scatter':
        a = rnd(i, seed + 4) * 6.28
        return math.cos(a) * 500 * e_in(p), math.sin(a) * 500 * e_in(p) - 200 * p, 1 - 0.5 * p, 1 - 0.5 * p, (rnd(i, seed) - 0.5) * 360 * p, 1 - p
    if kind == 'drift':  # slow drift apart (emptiness)
        a = (i - n / 2) / max(1, n)
        return a * 380 * e_out(clamp(et / 1.2)), (rnd(i, seed) - 0.5) * 120 * e_out(clamp(et / 1.2)), 1, 1, (rnd(i, seed + 1) - 0.5) * 30 * clamp(et / 1.2), 1 - 0.6 * clamp(et / 1.4)
    if kind == 'zoom':
        s = 1 + 2.5 * e_in(p)
        return 0, 0, s, s, 0, 1 - p
    return 0, 0, 1, 1, 0, 1 - p


def draw_word(c, t, it, exit_t, exit_kind, alpha):
    w = it['w']
    lt = t - w.t0
    if lt < 0:
        return
    f, x0, y0 = it['f'], it['x'], it['y']
    size = f.getSize()
    n = len(w.text)
    seed = hash(w.text) % 97
    et = (t - exit_t) if exit_t is not None else -1
    if et > 0.9 and exit_kind != 'drift':
        return
    # highlight capsule (drawn behind)
    if w.pill:
        pp = clamp((lt - 0.08) / 0.35)
        pa = alpha * (1 - clamp(et / 0.25) if et > 0 else 1)
        padx, pady = size * 0.22, size * 0.16
        pill(c, x0 - padx, y0 - size * 0.76 - pady, x0 + it['width'] + padx, y0 + size * 0.06 + pady,
             e_out(pp), color='#e2a93b', width=max(4, size * 0.05), alpha=pa)
    glow = w.glow
    for i, ch in enumerate(w.text):
        if ch == ' ':
            continue
        dx, dy, sx, sy, rot, a = _entrance(w.ent, lt, i, n, seed)
        ex = _exit(exit_kind, et, i, n, seed)
        dx += ex[0]; dy += ex[1]; sx *= ex[2]; sy *= ex[3]; rot += ex[4]; a *= ex[5]
        # idle life: tiny beat bounce
        dy += -beat_pulse(t, 9) * size * 0.05 * (1 if (i + int(t * 2)) % 2 else 0.4)
        a *= alpha
        if a <= 0.01 or abs(sy) < 0.01:
            continue
        lx = x0 + it['xs'][i]
        cw = it['cw'][i]
        px, py = lx + cw / 2, y0 - size * 0.36
        c.save()
        c.translate(px + dx, py + dy)
        c.rotate(rot)
        c.scale(sx, sy)
        c.translate(-px, -py)
        if w.ent == 'glitch' and lt < 0.6:
            j = (1 - clamp(lt / 0.6))
            draw_glyphs(c, ch, f, lx - 14 * j, y0, '#ff1a3c', t, depth=0, alpha=a * 0.8 * j, outline=0.01)
            draw_glyphs(c, ch, f, lx + 14 * j, y0, '#19e3ff', t, depth=0, alpha=a * 0.6 * j, outline=0.01)
        draw_glyphs(c, ch, f, lx, y0, w.style, t + i * 0.05, depth=w.depth, alpha=a, glow=glow)
        c.restore()
