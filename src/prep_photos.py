"""Prepare the ORIGINAL photos for the edit (no stylization, faces untouched).

- crop (Toly: drop the fairy on the right edge), upscale 2x with Lanczos
- subject mask via GrabCut -> *_cut.png (same pixels, alpha = person) used only
  for layering ("text behind the person").
"""
import os, cv2, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = os.path.join(ROOT, 'assets', 'src'), os.path.join(ROOT, 'assets', 'photos')

P = {
    'eminem': dict(file='eminem.png', crop=(0, 0, 500, 591),
                   fg=[[(240, 8), (300, 18), (350, 50), (378, 100), (388, 160), (386, 205), (400, 212), (408, 245),
                        (398, 300), (378, 330), (360, 338), (345, 380), (318, 420), (280, 445), (238, 452),
                        (198, 446), (160, 425), (135, 385), (120, 340), (100, 330), (82, 300), (78, 245), (88, 212),
                        (100, 208), (98, 160), (105, 105), (135, 50), (185, 18)],
                       [(140, 400), (350, 400), (500, 450), (500, 591), (0, 591), (0, 455)]]),
    'toly': dict(file='toly.png', crop=(170, 0, 750, 760),
                 fg=[[(470, 32), (540, 38), (600, 80), (635, 140), (640, 210), (648, 240), (668, 250), (672, 300),
                      (655, 350), (630, 365), (615, 410), (585, 450), (540, 478), (490, 490), (450, 484), (405, 455),
                      (372, 420), (352, 380), (345, 320), (342, 260), (330, 200), (328, 140), (360, 80), (410, 45)],
                     [(430, 420), (650, 400), (870, 590), (900, 1000), (130, 1000), (150, 820), (280, 545)]]),
}


def mask_for(img, polys):
    h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.array(p, np.int32)], 1)
    sure = cv2.erode(m, np.ones((21, 21), np.uint8))
    near = cv2.dilate(m, np.ones((15, 15), np.uint8))
    gc = np.where(near > 0, cv2.GC_PR_BGD, cv2.GC_BGD).astype(np.uint8)
    gc[m > 0] = cv2.GC_PR_FGD
    gc[sure > 0] = cv2.GC_FGD
    cv2.grabCut(img, gc, None, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_MASK)
    out = np.where((gc == 1) | (gc == 3), 255, 0).astype(np.uint8)
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, c in P.items():
        img = cv2.imread(os.path.join(SRC, c['file']))
        m = mask_for(img, c['fg'])
        x0, y0, x1, y1 = c['crop']
        img, m = img[y0:y1, x0:x1], m[y0:y1, x0:x1]
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        m = cv2.resize(m, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        m = cv2.GaussianBlur(m, (0, 0), 1.5)
        cv2.imwrite(os.path.join(OUT, f'{name}.png'), img)
        cv2.imwrite(os.path.join(OUT, f'{name}_cut.png'), np.dstack([img, m]))
        print(name, img.shape)


if __name__ == '__main__':
    main()


# ---- v3: face-only stickers (head + a bit of neck, transparent background) ----
FACE = {
    'eminem': [P['eminem']['fg'][0], [(170, 400), (320, 400), (330, 500), (165, 500)]],
    'toly': [P['toly']['fg'][0], [(440, 440), (580, 430), (585, 520), (445, 525)]],
}


def faces():
    for name, polys in FACE.items():
        img = cv2.imread(os.path.join(SRC, P[name]['file']))
        m = mask_for(img, polys)
        # keep only within the head polygons (+ margin): no shoulders, no background
        lim = np.zeros_like(m)
        for p in polys:
            cv2.fillPoly(lim, [np.array(p, np.int32)], 255)
        lim = cv2.dilate(lim, np.ones((11, 11), np.uint8))
        m = cv2.bitwise_and(m, lim)
        # fade the neck out at the bottom
        ys = np.where(m.max(1) > 0)[0]
        y1 = ys.max()
        fade = np.clip((y1 - np.arange(m.shape[0])) / 40.0, 0, 1)
        m = (m * fade[:, None]).astype(np.uint8)
        xs = np.where(m.max(0) > 0)[0]
        x0, x1, y0 = max(0, xs.min() - 6), xs.max() + 6, max(0, ys.min() - 6)
        img, m = img[y0:y1 + 1, x0:x1 + 1], m[y0:y1 + 1, x0:x1 + 1]
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        m = cv2.GaussianBlur(cv2.resize(m, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR), (0, 0), 1.2)
        cv2.imwrite(os.path.join(OUT, f'{name}_face.png'), np.dstack([img, m]))
        print(name, 'face', img.shape)


if __name__ == '__main__':
    faces()
