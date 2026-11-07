"""Characters, environments and graphic elements of the clip."""
import math, pickle
import numpy as np
import skia
from engine import *

# ======================================================================= FIGURES
RIG = {
    'em':   dict(sh=148, shy=-700, hipx=74, hipy=-405, head=(0, -838), hr=(63, 76), ua=165, fa=168,
                 aw=(34, 27), lw=(42, 37), foot=88, shoe=(62, 26)),
    'toly': dict(sh=126, shy=-702, hipx=60, hipy=-415, head=(0, -840), hr=(57, 71), ua=160, fa=168,
                 aw=(23, 18), lw=(28, 23), foot=70, shoe=(46, 18)),
}

POSES = {
    'em': {
        'idle':  dict(lh=(-185, -420), rh=(185, -420)),
        'point': dict(lh=(-120, -560), rh=(450, -770)),
        'rap':   dict(lh=(-215, -440), rh=(40, -650)),
        'raise': dict(lh=(-160, -560), rh=(250, -1120)),
        'wide':  dict(lh=(-420, -690), rh=(420, -690)),
        'chest': dict(lh=(-60, -600), rh=(70, -620)),
        'pointL': dict(lh=(-470, -770), rh=(180, -460)),
        'fistL': dict(lh=(-260, -1110), rh=(170, -560)),
    },
    'toly': {
        'sing':  dict(lh=(-38, -772), rh=(205, -470)),
        'singo': dict(lh=(-38, -772), rh=(390, -800)),
        'singR': dict(lh=(-38, -772), rh=(430, -760)),
        'up':    dict(lh=(-210, -1110), rh=(400, -840)),
    },
}


def pose_mix(kind, a, b, t):
    pa, pb = POSES[kind][a], POSES[kind][b]
    return {k: (lerp(pa[k][0], pb[k][0], t), lerp(pa[k][1], pb[k][1], t)) for k in pa}


def figure_paths(kind, pose, bob=0.0, lean=0.0, tilt=0.0, sway=0.0, t=0.0):
    """Returns (silhouette path, detail path, accent path) in local coords (feet at y=0)."""
    R = RIG[kind]
    up = lambda p: (p[0] + sway * (-p[1] / 900.0), p[1] + bob)  # upper body offset
    sh_y = R['shy']
    # torso
    if kind == 'em':
        S = R['sh']; hy = R['hipy']
        tor = skia.Path()
        pts = [(-S - 16, sh_y + 40), (-S + 2, hy + 30), (-S + 22, hy + 70), (S - 22, hy + 70), (S - 2, hy + 30), (S + 16, sh_y + 40)]
        tor.moveTo(*up(pts[0]))
        for q in pts[1:]:
            tor.lineTo(*up(q))
        tor.quadTo(*up((S + 6, sh_y - 8)), *up((S - 40, sh_y - 14)))
        tor.quadTo(*up((0, sh_y - 52)), *up((-S + 40, sh_y - 14)))
        tor.quadTo(*up((-S - 6, sh_y - 8)), *up(pts[0]))
        tor.close()
        hood = ellipse_path(*up((0, sh_y - 18)), 92, 36)
        tor = union(tor, hood)
    else:
        S = R['sh']; hy = R['hipy']
        tor = skia.Path()
        pts = [(-S - 8, sh_y + 30), (-S + 34, hy + 10), (-S + 40, hy + 40), (S - 40, hy + 40), (S - 34, hy + 10), (S + 8, sh_y + 30)]
        tor.moveTo(*up(pts[0]))
        for q in pts[1:]:
            tor.lineTo(*up(q))
        tor.quadTo(*up((S + 2, sh_y - 6)), *up((S - 40, sh_y - 12)))
        tor.lineTo(*up((-S + 40, sh_y - 12)))
        tor.quadTo(*up((-S - 2, sh_y - 6)), *up(pts[0]))
        tor.close()
    # neck + head
    hx, hyy = R['head']
    neck = capsule(up((0, sh_y - 10)), up((0, hyy + 40)), 27 if kind == 'em' else 23, 26 if kind == 'em' else 22)
    head = skia.Path()
    hc = up((hx, hyy))
    head.addOval(skia.Rect(hc[0] - R['hr'][0], hc[1] - R['hr'][1], hc[0] + R['hr'][0], hc[1] + R['hr'][1]))
    # ears
    head = union(head, ellipse_path(hc[0] - R['hr'][0] + 2, hc[1] + 6, 12, 20), ellipse_path(hc[0] + R['hr'][0] - 2, hc[1] + 6, 12, 20))
    if kind == 'toly':  # swept fringe
        hair = skia.Path()
        hair.moveTo(hc[0] - 62, hc[1] - 10)
        hair.cubicTo(hc[0] - 70, hc[1] - 95, hc[0] + 40, hc[1] - 112, hc[0] + 70, hc[1] - 52)
        hair.cubicTo(hc[0] + 82, hc[1] - 30, hc[0] + 58, hc[1] - 18, hc[0] + 40, hc[1] - 40)
        hair.cubicTo(hc[0] + 10, hc[1] - 62, hc[0] - 30, hc[1] - 40, hc[0] - 62, hc[1] - 10)
        hair.close()
        head = union(head, hair)
    if tilt:
        m = skia.Matrix.RotateDeg(tilt, skia.Point(hc[0], hc[1] + 60))
        head.transform(m)
    # arms (IK)
    parts = [tor, neck, head]
    det = skia.Path()
    acc = skia.Path()
    hands = {}
    for side, key in ((-1, 'lh'), (1, 'rh')):
        Sx = side * R['sh'] * (0.92 if kind == 'em' else 0.95)
        Sp = up((Sx, sh_y + 18))
        T = up(pose[key])
        eA, hand = ik(Sp, T, R['ua'], R['fa'], 1)
        eB, _ = ik(Sp, T, R['ua'], R['fa'], -1)
        # choose the elbow that sits outward / lower
        if kind == 'toly' and key == 'lh' and T[1] > -900:
            sc = lambda e: (e[1] - Sp[1]) - 0.3 * side * (e[0] - Sp[0])
        else:
            sc = lambda e: side * (e[0] - Sp[0]) * 1.0 + (e[1] - Sp[1]) * 0.6
        elbow = eA if sc(eA) > sc(eB) else eB
        parts.append(capsule(Sp, elbow, R['aw'][0], R['aw'][0] * 0.92))
        parts.append(capsule(elbow, hand, R['aw'][0] * 0.9, R['aw'][1]))
        hr_ = R['aw'][1] * (1.25 if kind == 'em' else 1.35)
        hp = skia.Path(); hp.addCircle(hand[0], hand[1], hr_)
        parts.append(hp)
        hands[key] = (hand, elbow)
        if kind == 'em':  # sleeve cuffs
            dx, dy = hand[0] - elbow[0], hand[1] - elbow[1]
            d = math.hypot(dx, dy) or 1
            cx, cy = hand[0] - dx / d * 34, hand[1] - dy / d * 34
            nx, ny = -dy / d, dx / d
            det.moveTo(cx + nx * 26, cy + ny * 26); det.lineTo(cx - nx * 26, cy - ny * 26)
    # legs (IK, knees out)
    for side in (-1, 1):
        Hp = (side * R['hipx'], R['hipy'] + bob + 30)
        F = (side * R['foot'], -24)
        kA, f = ik(Hp, F, 186, 180, 1)
        kB, _ = ik(Hp, F, 186, 180, -1)
        knee = kA if side * kA[0] > side * kB[0] else kB
        parts.append(capsule(Hp, knee, R['lw'][0] + 6, R['lw'][0]))
        parts.append(capsule(knee, f, R['lw'][0], R['lw'][1]))
        sh = skia.Path()
        sh.addOval(skia.Rect(f[0] - R['shoe'][0] + side * 14, -R['shoe'][1] * 1.6, f[0] + R['shoe'][0] + side * 14, 4))
        parts.append(sh)
    # hips block
    hipb = skia.Path()
    hipb.addRoundRect(skia.Rect(-R['hipx'] - R['lw'][0], R['hipy'] + bob - 10, R['hipx'] + R['lw'][0], R['hipy'] + bob + 80), 20, 20)
    parts.append(hipb)
    sil = union(*parts)
    # details
    if kind == 'em':
        # kangaroo pocket
        p0 = up((-82, hy - 30)); p1 = up((82, hy - 30))
        det.moveTo(*up((-104, hy + 54))); det.lineTo(*p0); det.quadTo(*up((0, hy - 58)), *p1); det.lineTo(*up((104, hy + 54)))
        # drawstrings (swing)
        sw = math.sin(t * 7.0) * 10 + sway * 0.3
        for s in (-1, 1):
            a0 = up((s * 24, sh_y + 4))
            det.moveTo(*a0); det.quadTo(a0[0] + s * 4 + sw * 0.5, a0[1] + 60, a0[0] + sw, a0[1] + 128)
        # hood seam
        det.moveTo(*up((-70, sh_y - 30))); det.quadTo(*up((0, sh_y + 30)), *up((70, sh_y - 30)))
    else:
        # collar + placket
        det.moveTo(*up((-44, sh_y - 16))); det.lineTo(*up((0, sh_y + 46))); det.lineTo(*up((44, sh_y - 16)))
        det.moveTo(*up((0, sh_y + 46))); det.lineTo(*up((0, hy + 20)))
        for k in range(4):
            yy = sh_y + 90 + k * 62
            c0 = up((0, yy)); det.addCircle(c0[0] + 9, c0[1], 3.5)
        # microphone in left hand
        hand, elbow = hands['lh']
        dx, dy = hand[0] - elbow[0], hand[1] - elbow[1]
        d = math.hypot(dx, dy) or 1
        ux, uy = dx / d, dy / d
        top = (hand[0] + ux * 58, hand[1] + uy * 58)
        mic = capsule((hand[0] - ux * 30, hand[1] - uy * 30), top, 9, 12)
        mic.addCircle(top[0] + ux * 14, top[1] + uy * 14, 22)
        acc = mic
        sil = union(sil, mic)
    return sil, det, acc


def draw_figure(ctx, kind, pose, sc, fill_a=1.0, line_p=1.0, line_a=1.0, det_a=0.55, glow=1.0, **kw):
    sil, det, acc = figure_paths(kind, pose, **kw)
    if fill_a > 0.01:
        sh = skia.GradientShader.MakeLinear([skia.Point(0, -950), skia.Point(0, 0)],
                                            [argb(34, 8, 12), argb(14, 4, 6), argb(6, 2, 3)], [0, 0.5, 1])
        ctx.c.drawPath(sil, paint(shader=sh, a=fill_a))
        # inner rim (one-sided light, burgundy)
        ctx.c.save(); ctx.c.clipPath(sil, skia.ClipOp.kIntersect, True)
        rim = skia.Path(sil); rim.offset(-10, 6)
        ctx.c.drawPath(sil, paint((150, 40, 32), 0.55 * fill_a, stroke=9, blur=4))
        ctx.c.restore()
    if line_a > 0.01:
        gold_stroke(ctx, sil, 2.6, a=line_a, glow=glow, prog=line_p, sc=sc)
    if det_a > 0.01 and line_p > 0.5:
        gold_stroke(ctx, det, 1.8, a=det_a * line_a * seg(line_p, 0.5, 1.0), glow=glow * 0.6, sc=sc)
    if kind == 'toly' and fill_a > 0.01:
        gold_stroke(ctx, acc, 2.2, a=0.9 * fill_a, glow=0.8, sc=sc, color=GOLD_L)
    return sil


# ======================================================================= PORTRAITS
class Portrait:
    def __init__(self, path_npz, path_pkl):
        d = np.load(path_npz)
        self.rgba = d['rgba']
        self.rev = d['rev'].astype(np.float32)
        self.alpha = self.rgba[..., 3].astype(np.float32) / 255
        self.N = self.rgba.shape[0]
        self.img = skia.Image.fromarray(np.ascontiguousarray(self.rgba), colorType=skia.ColorType.kRGBA_8888_ColorType,
                                        alphaType=skia.AlphaType.kUnpremul_AlphaType)
        self.rim = skia.Image.fromarray(np.ascontiguousarray(d['rim']), colorType=skia.ColorType.kRGBA_8888_ColorType,
                                        alphaType=skia.AlphaType.kUnpremul_AlphaType)
        P = pickle.load(open(path_pkl, 'rb'))
        self.outline = skia.Path(); self.feat = skia.Path()
        for kind, c in P:
            tgt = self.outline if kind == 'outline' else self.feat
            tgt.moveTo(float(c[0][0]), float(c[0][1]))
            for q in c[1:]:
                tgt.lineTo(float(q[0]), float(q[1]))
            tgt.close()
        rng = np.random.default_rng(7)
        nz = rng.random((self.N // 8, self.N // 8)).astype(np.float32)
        import cv2
        self.noise = cv2.resize(nz, (self.N, self.N), interpolation=cv2.INTER_CUBIC)
        self._cache = {}
        self.line_shader = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, self.N)],
                                                          [argb(255, 220, 140), argb(255, 220, 140), argb(255, 220, 140, 0)], [0, 0.66, 0.9])
        self.samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone)

    def reveal_images(self, r):
        key = round(r, 3)
        if key in self._cache:
            return self._cache[key]
        th = 1.08 - r * 1.25
        v = self.rev * 0.85 + self.noise * 0.15
        m = np.clip((v - th) / 0.07, 0, 1)
        rg = self.rgba.copy()
        rg[..., 3] = (self.alpha * m * 255).astype(np.uint8)
        front = np.exp(-((v - th - 0.02) / 0.03) ** 2) * self.alpha
        em = np.zeros_like(self.rgba)
        em[..., 0] = 255; em[..., 1] = 205; em[..., 2] = 120
        em[..., 3] = (np.clip(front, 0, 1) * 255).astype(np.uint8)
        out = (skia.Image.fromarray(rg, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType),
               skia.Image.fromarray(em, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType))
        if len(self._cache) > 40:
            self._cache.clear()
        self._cache[key] = out
        return out

    def draw(self, ctx, size, sc, reveal=1.0, rim=0.8, lines=0.0, line_a=0.0, feat_a=None, a=1.0, cf=None, glow=1.0):
        """Draw centred at local origin, size = local width."""
        if a <= 0.003:
            return
        rect = skia.Rect(-size / 2, -size / 2, size / 2, size / 2)
        if reveal >= 0.999:
            p = paint(None, a, cf=cf); p.setAlphaf(a)
            ctx.c.drawImageRect(self.img, rect, self.samp, p)
        elif reveal > 0.001:
            im, em = self.reveal_images(reveal)
            p = skia.Paint(AntiAlias=True); p.setAlphaf(a)
            if cf is not None: p.setColorFilter(cf)
            ctx.c.drawImageRect(im, rect, self.samp, p)
            pe = skia.Paint(BlendMode=PLUS); pe.setAlphaf(a * 0.9)
            ctx.c.drawImageRect(em, rect, self.samp, pe)
            pg = skia.Paint(); pg.setAlphaf(a * glow)
            ctx.g.drawImageRect(em, rect, self.samp, pg)
        if rim > 0.01 and reveal > 0.3:
            pr = skia.Paint(BlendMode=PLUS); pr.setAlphaf(cl(rim * a * seg(reveal, 0.3, 1.0)))
            ctx.c.drawImageRect(self.rim, rect, self.samp, pr)
            pg = skia.Paint(); pg.setAlphaf(cl(rim * a * 0.8 * glow))
            ctx.g.drawImageRect(self.rim, rect, self.samp, pg)
        if line_a > 0.01 and lines > 0.001:
            k = size / self.N
            ctx.save(); ctx.translate(-size / 2, -size / 2); ctx.scale(k)
            w = 2.3 / max(sc * k, 1e-4)
            eff = trim(0, lines)
            for path, aa in ((self.outline, line_a), (self.feat, line_a * (0.85 if feat_a is None else feat_a))):
                pp = paint(None, aa * a, stroke=w, shader=self.line_shader, effect=eff)
                ctx.c.drawPath(path, pp)
                pg = paint(None, aa * a * glow, stroke=w * 2.6, shader=self.line_shader, effect=eff)
                ctx.g.drawPath(path, pg)
            ctx.restore()


# ======================================================================= SHATTER
class Shards:
    def __init__(self, portrait, n=70, seed=3):
        from scipy.spatial import Delaunay
        rng = np.random.default_rng(seed)
        N = portrait.N
        g = []
        for i in range(8):
            for j in range(8):
                g.append(((i + rng.uniform(0.15, 0.85)) / 8 * N, (j + rng.uniform(0.15, 0.85)) / 8 * N))
        g += [(0, 0), (N, 0), (N, N), (0, N), (N / 2, 0), (0, N / 2), (N, N / 2), (N / 2, N)]
        pts = np.array(g)
        tri = Delaunay(pts)
        self.tris = []
        for s in tri.simplices:
            P = pts[s]
            c = P.mean(0)
            # keep only shards that contain some of the character
            ys, xs = int(np.clip(c[1], 0, N - 1)), int(np.clip(c[0], 0, N - 1))
            if portrait.alpha[ys, xs] < 0.15:
                continue
            self.tris.append(dict(P=P, c=c, rot=rng.uniform(-260, 260), spd=rng.uniform(0.7, 1.4),
                                  ang=math.atan2(c[1] - N * 0.45, c[0] - N / 2), rad=np.hypot(c[0] - N / 2, c[1] - N * 0.45),
                                  ring=rng.integers(0, 3), jit=rng.uniform(-0.25, 0.25)))
        self.p = portrait
        order = np.argsort([t['ang'] for t in self.tris])
        for k, i in enumerate(order):
            self.tris[i]['slot'] = k / len(order) * 2 * math.pi

    def draw(self, ctx, size, sc, t_exp, t_ring, ring_r=520.0, spin=0.0):
        """t_exp: 0..1 explode; t_ring: 0..1 settle into rings."""
        p = self.p; N = p.N; k = size / N
        for tr in self.tris:
            P = tr['P']; c = tr['c']
            e = eoe(t_exp * tr['spd'])
            # explode position (local px of portrait image)
            ex = c[0] + math.cos(tr['ang']) * (180 + tr['rad']) * e * 0.9
            ey = c[1] + math.sin(tr['ang']) * (180 + tr['rad']) * e * 0.9
            # ring slot
            rr = (ring_r * (1 + 0.16 * tr['ring'])) / k
            sa = tr['slot'] + spin + tr['jit'] * 0.2
            rx = N / 2 + math.cos(sa) * rr
            ry = N * 0.45 + math.sin(sa) * rr
            q = eio(t_ring)
            x = lerp(ex, rx, q); y = lerp(ey, ry, q)
            s = lerp(1.0 + 0.25 * e, 0.28, q)
            rot = tr['rot'] * e + q * 90
            path = poly([tuple(v) for v in P])
            ctx.save()
            ctx.translate(-size / 2, -size / 2); ctx.scale(k)
            ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s); ctx.translate(-c[0], -c[1])
            ctx.c.save(); ctx.c.clipPath(path, skia.ClipOp.kIntersect, True)
            tint = cl(e * 0.8 + q)
            pp = skia.Paint(); pp.setColorFilter(tint_cf(tint)); pp.setAlphaf(1.0)
            ctx.c.drawImageRect(p.img, skia.Rect(0, 0, N, N), p.samp, pp)
            if tint > 0.5:
                ctx.c.drawPath(path, paint(GOLD, (tint - 0.5) * 1.2 * cl(1 - q * 0.2)))
            ctx.c.restore()
            w = 2.2 / max(sc * k * s, 1e-3)
            ctx.c.drawPath(path, paint(GOLD_L, 0.9 * cl(e * 3), stroke=w))
            ctx.g.drawPath(path, paint(GOLD, 0.8 * cl(e * 3), stroke=w * 3))
            ctx.restore()


# ======================================================================= CITY
def make_city(seed, L, hmin, hmax, wmin, wmax, body, win_col, win_p, win_a, edge_a=0.0, k=1.0):
    rng = np.random.default_rng(seed)
    rec = skia.PictureRecorder(); c = rec.beginRecording(skia.Rect(-L - 500, -hmax * 1.6, L + 500, 10))
    recf = skia.PictureRecorder(); cf = recf.beginRecording(skia.Rect(-L - 500, -hmax * 1.6, L + 500, 10))
    x = -L
    bp = paint(body)
    edges = skia.Path()
    while x < L:
        w = rng.uniform(wmin, wmax); h = rng.uniform(hmin, hmax)
        c.drawRect(skia.Rect(x, -h, x + w, 0), bp)
        top = -h
        edges.moveTo(x, -h * 0.5); edges.lineTo(x, -h); edges.lineTo(x + w, -h)
        if rng.random() < 0.45:
            w2 = w * rng.uniform(0.4, 0.7); h2 = rng.uniform(40, 180) * k
            x2 = x + (w - w2) / 2
            c.drawRect(skia.Rect(x2, -h - h2, x2 + w2, -h), bp)
            edges.moveTo(x2, -h); edges.lineTo(x2, -h - h2); edges.lineTo(x2 + w2, -h - h2); edges.lineTo(x2 + w2, -h)
            top = -h - h2
            if rng.random() < 0.5:
                c.drawRect(skia.Rect(x2 + w2 / 2 - 2 * k, top - 120 * k, x2 + w2 / 2 + 2 * k, top), bp)
        if rng.random() < 0.25:
            c.drawRect(skia.Rect(x + w * 0.2, -h - 60 * k, x + w * 0.2 + 34 * k, -h), bp)
        # windows
        cw, ch = 26 * k, 36 * k
        nx = int((w - 16 * k) // cw); ny = int((h - 30 * k) // ch)
        for i in range(nx):
            for j in range(ny):
                if rng.random() < win_p:
                    wx = x + 10 * k + i * cw; wy = -h + 20 * k + j * ch
                    a = win_a * rng.uniform(0.35, 1.0)
                    tgt = cf if rng.random() < 0.25 else c
                    tgt.drawRect(skia.Rect(wx, wy, wx + 12 * k, wy + 18 * k), paint(win_col, a))
        x += w + rng.uniform(-8, 30) * k
    if edge_a > 0:
        c.drawPath(edges, paint(GOLD, edge_a, stroke=2.2 * k))
    return rec.finishRecordingAsPicture(), recf.finishRecordingAsPicture()


class City:
    def __init__(self):
        self.layers = []
        # (z, pic, flicker, scale)
        specs = [
            (5200, 11, 3.2, (60, 3, 10), (255, 140, 60), 0.18, 0.35, 0.0),
            (2600, 12, 2.0, (34, 6, 10), (255, 176, 80), 0.22, 0.55, 0.0),
            (1100, 13, 1.35, (15, 4, 7), (255, 196, 110), 0.14, 0.8, 0.35),
        ]
        for z, seed, k, body, wc, wp, wa, ea in specs:
            pic, fl = make_city(seed, 4200 * k / 2, 380 * k, 1500 * k, 150 * k, 420 * k, body, wc, wp, wa, ea, k)
            self.layers.append((z, pic, fl))

    def draw(self, ctx, cam, flick=0.0, a=1.0, xclip=None, ground=0.0):
        for z, pic, fl in self.layers:
            def fn(cx, sc, pic=pic, fl=fl):
                if xclip is not None:
                    cx.c.save(); cx.c.clipRect(skia.Rect(xclip[0], -1e5, xclip[1], 1e5))
                cx.c.drawPicture(pic)
                p = skia.Paint(); p.setAlphaf(cl(0.4 + 0.6 * flick))
                cx.c.saveLayer(None, p); cx.c.drawPicture(fl); cx.c.restore()
                if xclip is not None:
                    cx.c.restore()
            draw_plane(ctx, cam, (0, ground, z), fn, ext=600)


# ======================================================================= PARTICLES
class Particles:
    def __init__(self, n=700, seed=1):
        rng = np.random.default_rng(seed)
        self.P = rng.uniform([-3400, -6000, 0], [3400, 6000, 6000], (n, 3))
        self.size = rng.uniform(1.2, 4.5, n) ** 1.35
        self.ph = rng.uniform(0, 2 * np.pi, n)
        self.sp = rng.uniform(15, 80, n)
        self.tw = rng.uniform(1.5, 5.0, n)
        cols = np.array([GOLD_L, GOLD, (255, 150, 70), (230, 80, 50)], np.float32)
        self.c = cols[rng.choice(4, n, p=[0.35, 0.4, 0.15, 0.1])]
        self.n = n

    def draw(self, ctx, cam, t, bright=1.0, focus=1200.0, vortex=0.0, vc=(W / 2, H / 2), rise=1.0, burst=0.0):
        rel = np.empty_like(self.P)
        rel[:, 0] = (self.P[:, 0] + np.sin(t * 0.5 + self.ph) * 60 - cam.x + 3400) % 6800 - 3400
        rel[:, 1] = (self.P[:, 1] - self.sp * t * rise - cam.y + 6000) % 12000 - 6000
        rel[:, 2] = (self.P[:, 2] - cam.z) % 6000 + 40
        X, Y, Z = cam.proj_np(rel + np.array([cam.x, cam.y, cam.z]))
        if vortex > 0 or burst > 0:
            dx, dy = X - vc[0], Y - vc[1]
            ang = vortex * 2.2 + burst * 0.6
            ca, sa = np.cos(ang), np.sin(ang)
            s = (1 - 0.92 * vortex) * (1 + burst * 1.4)
            X = vc[0] + (dx * ca - dy * sa) * s
            Y = vc[1] + (dx * sa + dy * ca) * s
        r = self.size * cam.f / np.maximum(Z, 1)
        fade = np.clip((Z - 40) / 300, 0, 1) * np.clip((6000 - Z) / 2000, 0, 1)
        twk = 0.55 + 0.45 * np.sin(t * self.tw + self.ph)
        A = fade * twk * bright
        blur = np.clip(np.abs(Z - focus) / focus * 5.0, 0, 14)
        vis = (Z > 40) & (X > -60) & (X < W + 60) & (Y > -60) & (Y < H + 60) & (A > 0.02)
        idx = np.nonzero(vis)[0]
        buckets = {}
        for i in idx:
            b = 0 if blur[i] < 1 else 1 if blur[i] < 3.5 else 2 if blur[i] < 7 else 3
            buckets.setdefault(b, []).append(i)
        sig = [0.0, 2.0, 5.0, 10.0]
        for b, ids in buckets.items():
            for i in ids:
                rr = min(r[i], 40.0)
                a = float(A[i]) * (1.0 if b < 2 else 0.55)
                cc = self.c[i]
                p = paint((int(cc[0]), int(cc[1]), int(cc[2])), a, blur=sig[b] + rr * 0.3, blend=PLUS)
                ctx.c.drawCircle(float(X[i]), float(Y[i]), max(rr, 0.8), p)
                if b < 2 and a > 0.3:
                    ctx.g.drawCircle(float(X[i]), float(Y[i]), max(rr, 0.8) * 1.8, paint((int(cc[0]), int(cc[1]), int(cc[2])), a * 0.7))


# ======================================================================= SMOKE / TEXTURES
def make_noise(n=512, beta=2.6, seed=0):
    rng = np.random.default_rng(seed)
    wn = rng.standard_normal((n, n))
    fx = np.fft.fftfreq(n)[:, None]; fy = np.fft.fftfreq(n)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2); f[0, 0] = 1
    spec = np.fft.fft2(wn) / f ** (beta / 2)
    spec[0, 0] = 0
    v = np.real(np.fft.ifft2(spec))
    v = (v - v.min()) / (v.max() - v.min())
    return v


class Smoke:
    def __init__(self):
        self.imgs = []
        for s, (r, g, b) in ((5, (150, 24, 30)), (9, (110, 30, 20))):
            v = make_noise(512, 2.8, s)
            a = np.clip((v - 0.45) / 0.4, 0, 1) ** 1.6
            arr = np.zeros((512, 512, 4), np.uint8)
            arr[..., 0], arr[..., 1], arr[..., 2] = r, g, b
            arr[..., 3] = (a * 255).astype(np.uint8)
            self.imgs.append(skia.Image.fromarray(arr, colorType=skia.ColorType.kRGBA_8888_ColorType, alphaType=skia.AlphaType.kUnpremul_AlphaType))

    def draw(self, canvas, t, a=0.5, rect=(0, 0, W, H), drift=(40, -12), scale=3.2, which=(0, 1)):
        for i in which:
            im = self.imgs[i]
            m = skia.Matrix()
            sc = scale * (1 + 0.3 * i)
            m.setScaleTranslate(sc, sc * 1.2, t * drift[0] * (1 + i * 0.6) + i * 300, t * drift[1] * (1 + i * 0.4) + i * 500)
            sh = im.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions(skia.FilterMode.kLinear), m)
            p = skia.Paint(Shader=sh, BlendMode=SCREEN); p.setAlphaf(cl(a * (0.8 if i else 1.0)))
            canvas.drawRect(skia.Rect(*rect), p)


# ======================================================================= RAYS
def rays_path(n=24, r=3000, w=0.5):
    p = skia.Path()
    for i in range(n):
        a0 = i / n * 2 * math.pi; a1 = a0 + w * 2 * math.pi / n
        p.moveTo(0, 0); p.lineTo(r * math.cos(a0), r * math.sin(a0)); p.lineTo(r * math.cos(a1), r * math.sin(a1)); p.close()
    return p

RAYS = rays_path(28, 3200, 0.5)


def draw_rays(canvas, cx, cy, rot, a, color=(120, 16, 24), r=1800):
    sh = skia.GradientShader.MakeRadial(skia.Point(0, 0), r, [col(color, 1.0), col(color, 0.35), col(color, 0.0)], [0, 0.5, 1])
    canvas.save(); canvas.translate(cx, cy); canvas.rotate(rot)
    p = skia.Paint(AntiAlias=True, Shader=sh, BlendMode=SCREEN); p.setAlphaf(cl(a))
    canvas.drawPath(RAYS, p)
    canvas.restore()


# ======================================================================= TYPE
class Type:
    def __init__(self, font_path, size):
        self.tf = skia.Typeface.MakeFromFile(font_path)
        self.font = skia.Font(self.tf, size)
        self.size = size

    def layout(self, text, tracking=0.0):
        gl = self.font.textToGlyphs(text)
        ws = self.font.getWidths(gl)
        xs = []; x = 0
        for w in ws:
            xs.append(x); x += w + tracking * self.size
        total = x - tracking * self.size
        return gl, xs, ws, total

    def draw(self, ctx, text, cx, base, prog, tracking=0.0, depth=7, fill='gold', a=1.0, glow=0.35,
             rise=0.55, slam=0.0, stagger=None, outline=0.0, scale=1.0, color=None):
        """prog: callable(i)->0..1 per letter or float."""
        gl, xs, ws, total = self.layout(text, tracking)
        x0 = cx - total * scale / 2
        sh = gold_shader(base - self.size * 0.78 * scale, base + self.size * 0.05 * scale)
        for i, g in enumerate(gl):
            t = prog(i) if callable(prog) else prog
            if t <= 0.001:
                continue
            e = eoe(t)
            path = self.font.getPath(g)
            if path is None or path.countPoints() == 0:
                continue
            s = scale * (1 + slam * (1 - eob(t, 2.2)))
            dy = (1 - e) * self.size * rise
            la = a * cl(t * 2.5)
            gx = x0 + xs[i] * scale + ws[i] * scale / 2
            ctx.save(); ctx.translate(gx, base + dy); ctx.scale(s); ctx.translate(-ws[i] / 2, 0)
            for k in range(depth, 0, -1):
                q = skia.Path(path); q.offset(0, k * 1.6)
                ctx.c.drawPath(q, paint((38 + k * 4, 6, 10), la))
            if fill == 'gold':
                p = skia.Paint(AntiAlias=True)
                # shader in glyph-local coords
                lsh = gold_shader(-self.size * 0.78, self.size * 0.05)
                p.setShader(lsh); p.setAlphaf(cl(la))
                ctx.c.drawPath(path, p)
            else:
                ctx.c.drawPath(path, paint(color or GOLD_L, la))
            if outline > 0:
                ctx.c.drawPath(path, paint((60, 10, 14), la * outline, stroke=2.0))
            if glow > 0:
                ctx.g.drawPath(path, paint(GOLD, la * glow))
            ctx.restore()
        return total * scale


def swoosh(ctx, cx, cy, rx, ry, rot, prog, a=1.0, w=3.0, start=0.0):
    if prog <= 0.001 or a < 0.01:
        return
    p = skia.Path(); p.addArc(skia.Rect(-rx, -ry, rx, ry), 200, 330)
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot)
    eff = trim(start, prog)
    ctx.c.drawPath(p, paint(GOLD, a, stroke=w, effect=eff))
    ctx.g.drawPath(p, paint(GOLD, a, stroke=w * 3, effect=eff))
    ctx.restore()


# ======================================================================= ORNATE FRAME
def oval_frame(ctx, rx, ry, sc, prog=1.0, a=1.0, beads=True, t=0.0):
    o = skia.Path(); o.addArc(skia.Rect(-rx, -ry, rx, ry), -90, 359.9)
    i = skia.Path(); i.addArc(skia.Rect(-rx + 16, -ry + 16, rx - 16, ry - 16), 90, 359.9)
    gold_stroke(ctx, o, 6.0, a=a, glow=0.9, prog=prog, sc=sc, color=GOLD)
    gold_stroke(ctx, i, 2.0, a=a * 0.9, glow=0.6, prog=prog, sc=sc, color=GOLD_L)
    if beads and prog > 0.6:
        n = 36
        for k in range(n):
            ang = k / n * 2 * math.pi
            bx, by = math.cos(ang) * (rx - 8), math.sin(ang) * (ry - 8)
            ba = a * seg(prog, 0.6 + 0.4 * k / n, 0.65 + 0.4 * k / n)
            ctx.c.drawCircle(bx, by, 2.6 / max(sc, 1e-3) * 1.0, paint(GOLD_L, ba))
    if prog > 0.9:
        for k in range(4):
            ang = k * math.pi / 2
            sx, sy = math.cos(ang) * rx, math.sin(ang) * ry
            draw_star(ctx, sx, sy, 22 * seg(prog, 0.9, 1.0) * (1 + 0.15 * math.sin(t * 5 + k)), a, 0)
