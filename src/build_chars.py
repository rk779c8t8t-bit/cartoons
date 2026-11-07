"""Build stylized character head sprites from the reference photos.

Pipeline: polygon + GrabCut cutout -> edge-preserving smoothing -> cel-shaded
luminance bands -> warm palette grade -> XDoG ink lines.  Output: RGBA head
sprites plus a JSON rig (eye / mouth / brow / pivot positions in sprite space).
"""
import json, os, cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'src')
OUT = os.path.join(ROOT, 'assets', 'chars')

# Hand-placed landmarks (source photo pixel coords).
CHARS = {
    'eminem': dict(
        file='eminem.png', scale=2.0,
        crop=(60, 0, 430, 505),
        poly=[(240, 8), (300, 18), (350, 50), (378, 100), (388, 160), (386, 205),
              (400, 212), (408, 245), (398, 300), (378, 330), (360, 338),
              (345, 380), (318, 420), (280, 445), (238, 452), (198, 446), (160, 425),
              (135, 385), (120, 340), (100, 330), (82, 300), (78, 245), (88, 212),
              (100, 208), (98, 160), (105, 105), (135, 50), (185, 18)],
        neck=[(180, 420), (318, 420), (322, 500), (176, 500)],
        eyes=[(172, 221, 26, 9), (300, 219, 26, 9)],
        brows=[(172, 192), (300, 190)],
        mouth=(238, 357, 34), chin=446, pivot=(240, 532),
        skin=(214, 172, 150),
    ),
    'toly': dict(
        file='toly.png', scale=2.0,
        crop=(310, 20, 690, 545),
        poly=[(470, 32), (540, 38), (600, 80), (635, 140), (640, 210), (648, 240),
              (668, 250), (672, 300), (655, 350), (630, 365), (615, 410),
              (585, 450), (540, 478), (490, 490), (450, 484), (405, 455), (372, 420),
              (352, 380), (345, 320), (342, 260), (330, 200), (328, 140), (360, 80),
              (410, 45)],
        neck=[(445, 450), (575, 440), (572, 540), (450, 540)],
        eyes=[(401, 286, 24, 9), (519, 269, 24, 9)],
        brows=[(398, 252), (520, 236)],
        mouth=(474, 409, 38), chin=488, pivot=(485, 572),
        skin=(226, 176, 146),
    ),
}


def cutout(img, c):
    h, w = img.shape[:2]
    poly = np.array(c['poly'], np.int32)
    neck = np.array(c['neck'], np.int32)
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [poly], 1); cv2.fillPoly(m, [neck], 1)
    fg = cv2.erode(m, np.ones((25, 25), np.uint8))
    pr = cv2.dilate(m, np.ones((13, 13), np.uint8))
    gc = np.where(pr > 0, cv2.GC_PR_BGD, cv2.GC_BGD).astype(np.uint8)
    gc[m > 0] = cv2.GC_PR_FGD
    gc[fg > 0] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(img, gc, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    mask = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # keep inside polygon band, smooth edge
    mask = cv2.bitwise_and(mask, pr * 255)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab = cv2.connectedComponents(mask)
    if n > 2:
        sizes = [(lab == i).sum() for i in range(1, n)]
        mask = np.where(lab == 1 + int(np.argmax(sizes)), 255, 0).astype(np.uint8)
    # fade neck bottom so it tucks into the drawn collar
    mask = cv2.GaussianBlur(mask, (0, 0), 1.6)
    return mask


def xdog(gray, sigma=1.0, k=1.6, p=22, eps=-0.05, phi=12):
    g = gray.astype(np.float32) / 255.0
    a = cv2.GaussianBlur(g, (0, 0), sigma)
    b = cv2.GaussianBlur(g, (0, 0), sigma * k)
    d = (1 + p) * a - p * b
    e = np.where(d >= eps, 1.0, 1.0 + np.tanh(phi * (d - eps)))
    return np.clip(e, 0, 1)


def stylize(img, mask, c):
    s = c['scale']
    if s != 1:
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        mask = cv2.resize(mask, None, fx=s, fy=s, interpolation=cv2.INTER_LINEAR)
    sm = img.copy()
    for _ in range(3):
        sm = cv2.bilateralFilter(sm, 7, 22, 5)
    lab = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB).astype(np.float32)
    L = lab[..., 0] / 255.0
    # soft cel bands
    levels = np.array([0.16, 0.30, 0.44, 0.57, 0.70, 0.82, 0.92])
    vals = np.array([0.08, 0.22, 0.36, 0.50, 0.63, 0.76, 0.87, 0.96])
    out = np.full_like(L, vals[0])
    for t, lo, hi in zip(levels, vals[:-1], vals[1:]):
        w = np.clip((L - t) / 0.018 + 0.5, 0, 1)
        w = w * w * (3 - 2 * w)
        out = out + w * (hi - lo)
    Lq = 0.7 * out + 0.3 * L
    lab[..., 0] = Lq * 255
    # warm grade: push a/b toward warm, shadows toward burgundy
    lab[..., 1] = (lab[..., 1] - 128) * 1.05 + 128 + (1 - Lq) * 8
    lab[..., 2] = (lab[..., 2] - 128) * 1.1 + 128 + 4
    col = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    gray = cv2.cvtColor(cv2.bilateralFilter(img, 7, 40, 7), cv2.COLOR_BGR2GRAY)
    ink = xdog(gray, sigma=0.75 * s, p=28, eps=-0.015, phi=25)
    ink = cv2.GaussianBlur(ink, (0, 0), 0.5 * s)
    inkcol = np.array([40, 20, 52], np.float32)  # BGR dark burgundy
    colf = col.astype(np.float32)
    colf = colf * ink[..., None] + inkcol * (1 - ink[..., None])
    # outline along the cutout edge
    edge = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32) / 255
    edge = cv2.GaussianBlur(edge, (0, 0), 1.0 * s)
    edge = np.clip(edge * 2.2, 0, 1)
    colf = colf * (1 - edge[..., None]) + inkcol * edge[..., None]
    rgba = np.dstack([np.clip(colf, 0, 255).astype(np.uint8), mask])
    return rgba


def main():
    os.makedirs(OUT, exist_ok=True)
    rig = {}
    for name, c in CHARS.items():
        img = cv2.imread(os.path.join(SRC, c['file']))
        mask = cutout(img, c)
        x0, y0, x1, y1 = c['crop']
        img_c, mask_c = img[y0:y1, x0:x1], mask[y0:y1, x0:x1]
        rgba = stylize(img_c, mask_c, c)
        cv2.imwrite(os.path.join(OUT, f'{name}_head.png'), rgba)
        s = c['scale']
        tr = lambda p: [(p[0] - x0) * s, (p[1] - y0) * s]
        rig[name] = dict(
            size=[rgba.shape[1], rgba.shape[0]],
            eyes=[tr(e[:2]) + [e[2] * s, e[3] * s] for e in c['eyes']],
            brows=[tr(b) for b in c['brows']],
            mouth=tr(c['mouth'][:2]) + [c['mouth'][2] * s],
            chin=(c['chin'] - y0) * s, pivot=tr(c['pivot']),
            skin=list(c['skin']),
        )
        print(name, rgba.shape)
    json.dump(rig, open(os.path.join(OUT, 'rig.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
