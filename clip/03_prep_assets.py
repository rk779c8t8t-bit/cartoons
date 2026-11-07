"""Turn stylized character portraits into render-ready assets:
RGBA (with soft fade into darkness), luminance map (for the 'emerge from darkness'
reveal), golden rim-light layer and vector contour paths (for the gold line-drawing)."""
import numpy as np, cv2, pickle, sys
S = sys.argv[1]; OUT = sys.argv[2]
SZ = 1024
def prep(name, fade_bottom=(0.70, 0.98), side=0.0, face_cy=0.45):
    im = cv2.imread(f'{S}/chars/{name}.png', cv2.IMREAD_UNCHANGED)
    im = cv2.resize(im, (SZ, SZ), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB).astype(np.float32)
    a = im[..., 3].astype(np.float32) / 255
    yy, xx = np.mgrid[0:SZ, 0:SZ] / SZ
    fade = 1 - np.clip((yy - fade_bottom[0]) / (fade_bottom[1] - fade_bottom[0]), 0, 1) ** 1.5
    # soft side falloff so stray shoulders melt into darkness
    fade *= np.clip(1 - (np.abs(xx - 0.5) - 0.36) / 0.14, 0, 1)
    a2 = a * fade
    lum = (rgb @ np.array([0.3, 0.55, 0.15])) / 255
    lum = np.clip(lum / max(lum[a > 0.5].max(), 1e-3), 0, 1)
    # luminance used for reveal: favour face area (centre) so faces appear first
    d = np.sqrt((xx - 0.5) ** 2 + ((yy - face_cy) * 1.1) ** 2)
    rev = np.clip(0.6 * lum + 0.4 * (1 - d / 0.6), 0, 1)
    rev = cv2.GaussianBlur(rev.astype(np.float32), (0, 0), 3)
    # rim light (gold edge emission), stronger on upper-left
    er = cv2.erode((a > 0.5).astype(np.float32), np.ones((9, 9), np.uint8))
    edge = np.clip((a > 0.5).astype(np.float32) - er, 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 4)
    shift = np.roll(np.roll(a, 14, 1), 10, 0)
    rimside = np.clip(a - shift, 0, 1)
    rimside = cv2.GaussianBlur(rimside, (0, 0), 6)
    rim = np.clip(edge * 0.7 + rimside * 1.1, 0, 1) * fade
    gold = np.array([255, 196, 110], np.float32)
    rim_rgba = np.dstack([np.tile(gold, (SZ, SZ, 1)), rim[..., None] * 255]).astype(np.uint8)
    # contours: silhouette outline
    paths = []
    bm = ((a2 > 0.35) * 255).astype(np.uint8)
    cs, _ = cv2.findContours(bm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cs = sorted(cs, key=lambda c: -cv2.arcLength(c, True))[:2]
    for c in cs:
        c = cv2.approxPolyDP(c, 1.2, True)[:, 0, :].astype(np.float32)
        # drop points in faded zone
        paths.append(('outline', c))
    # feature lines from ink map
    # tonal band boundaries -> engraving-like line drawing
    ls = cv2.GaussianBlur(lum.astype(np.float32), (0, 0), 2.5)
    cs = []
    for th in (0.28, 0.5, 0.72):
        lb = ((ls > th) & (a2 > 0.5)).astype(np.uint8) * 255
        cc, _ = cv2.findContours(lb, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        cs += [c for c in cc if cv2.arcLength(c, True) > 60]
    # prefer lines near the face
    def score(c):
        m = c[:, 0, :].mean(0) / SZ
        return cv2.arcLength(c, True) * np.exp(-((m[0] - .5) ** 2 + (m[1] - face_cy) ** 2) / 0.06)
    cs = sorted(cs, key=lambda c: -score(c))[:90]
    # order top->bottom so the drawing 'flows' down the face
    cs = sorted(cs, key=lambda c: c[:, 0, 1].mean())
    for c in cs:
        c = cv2.approxPolyDP(c, 1.0, True)[:, 0, :].astype(np.float32)
        if len(c) > 3: paths.append(('feature', c))
    rgba = np.dstack([rgb, a2[..., None] * 255]).astype(np.uint8)
    np.savez_compressed(f'{OUT}/{name}.npz', rgba=rgba, rev=rev.astype(np.float16), rim=rim_rgba)
    pickle.dump(paths, open(f'{OUT}/{name}_paths.pkl', 'wb'))
    print(name, len(paths))
for n in ['toly_a', 'toly_c', 'em_a', 'em_b', 'em_d']:
    prep(n)
