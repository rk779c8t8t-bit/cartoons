"""Frame compositor + multi-process MP4 export.

Usage:
  python3 src/render.py                       # full 1080x1920 60fps render -> output/
  python3 src/render.py --stills 0.3 2.1 3.7  # PNG stills to previews/
  python3 src/render.py --start 3 --end 5 --scale 0.5 --out previews/part.mp4   # quick preview
"""
import argparse, math, os, subprocess, sys, time, json
import numpy as np
import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import (Textures, FontBank, TextLayer, Embers, draw_burst, draw_bubbles, glitch, chroma, radial_distort,
                    lerp_item, lut, FIRE_LUT, clamp, ROOT)
import scenes

W, H = 1080, 1920


class Renderer:
    def __init__(self, scale=1.0):
        self.s = scale
        self.W, self.H = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
        self.tex = Textures()
        self.fonts = FontBank()
        self.text = TextLayer(W, H, self.fonts, self.tex)
        self.embers = Embers()
        self.qW, self.qH = W // 4, H // 4
        gy, gx = np.mgrid[0:self.qH, 0:self.qW].astype(np.float32)
        self.qx, self.qy = gx * 4, gy * 4
        cx, cy = W / 2, H * 0.55
        r = np.sqrt(((self.qx - cx) / W) ** 2 + ((self.qy - cy) / H * 0.75) ** 2)
        self.radial = np.clip(1 - r * 1.6, 0, 1) ** 1.6
        self.bottom = np.clip((self.qy / H - 0.55) / 0.45, 0, 1) ** 1.7
        vy, vx = np.mgrid[0:H, 0:W].astype(np.float32)
        vr = np.sqrt(((vx - W / 2) / (W * 0.62)) ** 2 + ((vy - H / 2) / (H * 0.62)) ** 2)
        self.vignette = np.clip(1.15 - vr ** 2.2 * 0.75, 0.22, 1).astype(np.float32)[..., None]
        self.GY, self.GX = vy, vx

    # ---------------------------------------------------------- background
    def background(self, t, bg, puffs):
        T = self.tex
        qx, qy = self.qx, self.qy
        sp = bg.get("smoke_speed", 1.0)
        s1 = T.sample(T.smoke1, qx * 0.32 + t * 18 * sp, qy * 0.32 + t * 55 * sp)
        s2 = T.sample(T.smoke2, qx * 0.21 - t * 26 * sp, qy * 0.21 + t * 34 * sp)
        dens = np.clip((s1 * 0.6 + s2 * 0.55 - 0.42) * 1.9, 0, 1) ** 1.4 * bg.get("smoke", 0.6)
        for p in puffs:
            a = t - p["t0"]
            if a < 0 or a > p["life"]: continue
            R = p["r0"] + p["grow"] * math.sqrt(a)
            d2 = ((qx - p["x"]) ** 2 + ((qy - p["y"] + a * 120) ) ** 2) / (R * R)
            fade = (1 - a / p["life"]) ** 1.5
            n = T.sample(T.smoke1, qx * 0.6 + a * 40, qy * 0.6 + a * 90)
            dens = dens + np.exp(-d2 * 2.2) * (0.5 + 0.8 * n) * fade * p["amt"]
        red = bg.get("red", 0.5)
        base = np.zeros((self.qH, self.qW, 3), np.float32)
        base += self.radial[..., None] * np.array([0.30, 0.02, 0.01], np.float32) * red
        under = self.bottom * bg.get("underlight", 0.6)
        smoke_col = np.array([0.075, 0.05, 0.05], np.float32)[None, None] + \
            under[..., None] * np.array([0.55, 0.12, 0.02], np.float32) + \
            self.radial[..., None] * np.array([0.25, 0.04, 0.02], np.float32) * red
        base = base * (1 - dens[..., None] * 0.6) + dens[..., None] * smoke_col
        fl = bg.get("flames", 0.0)
        if fl > 0.01:
            f1 = T.sample(T.fire, qx * 0.9, qy * 0.55 + t * 330)
            f2 = T.sample(T.fine, qx * 1.6, qy * 1.0 + t * 520)
            g = np.clip((qy / H - (1 - 0.42 * fl)) / (0.42 * fl + 1e-3), 0, 1)
            v = np.clip((f1 * 0.75 + f2 * 0.35) * g * 1.6 - 0.25, 0, 1)
            base += lut(FIRE_LUT, v) * (0.9 * fl)
        base *= bg.get("bright", 1.0)
        return cv2.resize(base, (W, H), interpolation=cv2.INTER_LINEAR)

    # ---------------------------------------------------------- frame
    def frame(self, t):
        spec = scenes.frame(t)
        prev = scenes.frame(t - 1.0 / 120.0)
        bg = self.background(t, spec["bg"], spec.get("puffs", []))

        # --- text with motion blur
        self.text.clear()
        prev_map = {it["key"]: it for it in prev["items"] if "key" in it}
        items = sorted(spec["items"], key=lambda d: d.get("z", 0))
        for it in items:
            if it.get("kind") == "rect":
                self.text.draw_rect(it); continue
            p = prev_map.get(it.get("key"))
            variants = [it]
            if p is not None:
                disp = abs(it["x"] - p["x"]) + abs(it["y"] - p["y"]) + \
                    abs(it["size"] * it["sx"] - p["size"] * p["sx"]) * 2.5 + \
                    abs(it["rot"] - p["rot"]) * it["size"] * 0.02
                if it.get("letters") and p.get("letters") and len(it["letters"]) == len(p["letters"]):
                    for la, lb in zip(it["letters"], p["letters"]):
                        disp = max(disp, (abs(la.get("dx", 0) - lb.get("dx", 0)) + abs(la.get("dy", 0) - lb.get("dy", 0))
                                          + abs(la.get("s", 1) - lb.get("s", 1))) * it["size"])
                k = int(min(9, math.ceil(disp / 5.0)))
                if k > 1 and it.get("mblur", True):
                    variants = [lerp_item(p, it, (j + 1) / k) for j in range(k)]
            self.text.draw(variants, t)
        TL = self.text
        # --- particles (half res): back layer (behind text) and front layer
        hs = 0.5
        em = spec.get("embers", {})
        layers = []
        for front in (False, True):
            hot = np.zeros((H // 2, W // 2), np.float32)
            pcol = np.zeros((H // 2, W // 2, 3), np.float32)
            if not front:
                self.embers.draw(t, hot, hs, em.get("amount", 0.6), em.get("speed", 1.0), em.get("count", 0.6))
            for b in scenes.BURSTS:
                if b.front == front:
                    draw_burst(b, t, hot, pcol, hs)
            for bs in spec.get("bubbles", []):
                if bs.get("front", False) == front:
                    draw_bubbles(pcol, hs, t, bs)
            layers.append(self._particles(hot, pcol, spec if front else None, hs))
        img = (bg + layers[0]) * (1 - TL.a[..., None]) + TL.rgb + TL.add + layers[1]
        # --- glow (quarter res)
        gq = cv2.resize(TL.glow, (self.qW, self.qH), interpolation=cv2.INTER_AREA)
        gsum = cv2.GaussianBlur(gq, (0, 0), 3) * 0.55 + cv2.GaussianBlur(gq, (0, 0), 12) * 0.6 + \
            cv2.GaussianBlur(gq, (0, 0), 32) * 0.45
        img += cv2.resize(gsum, (W, H), interpolation=cv2.INTER_LINEAR)

        # --- heat haze
        hz = spec.get("heat")
        if hz and hz["amt"] > 0.01:
            img = self.heat_haze(img, t, hz)
        # --- shockwave refraction
        for r in spec.get("rings", []):
            if len(r) > 5 and r[5] > 0.5:
                img = radial_distort(img, r[0], r[1], r[2], 50 + r[3] * 2, r[5])

        # --- flash
        fl = spec.get("flash")
        if fl is not None and max(fl) > 0.003:
            img += np.array(fl, np.float32)

        # --- camera
        img = self.camera(img, spec["cam"])

        # --- bloom
        q = cv2.resize(img, (self.qW, self.qH), interpolation=cv2.INTER_AREA)
        br = np.maximum(q - 0.85, 0)
        bl = cv2.GaussianBlur(br, (0, 0), 6) * 0.35 + cv2.GaussianBlur(br, (0, 0), 22) * 0.35
        img += cv2.resize(bl, (W, H), interpolation=cv2.INTER_LINEAR) * spec.get("bloom", 1.0)

        img = glitch(img, spec.get("glitch", 0), t)
        img = chroma(img, 0.0025 + spec.get("chroma", 0))
        img *= self.vignette
        img *= spec.get("fade", 1.0)
        # tone curve with soft shoulder
        img = np.where(img < 0.8, img, 0.8 + (1 - np.exp(-(img - 0.8) * 5)) * 0.2)
        g = self.tex.grain[int(t * 60) % len(self.tex.grain)]
        img += cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * 0.012
        out = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
        if self.s != 1.0:
            out = cv2.resize(out, (self.W, self.H), interpolation=cv2.INTER_AREA)
        return out

    def _particles(self, hot, pcol, spec, hs):
        rb = None
        for r in (spec.get("rings", []) if spec else []):
            cx, cy, R, th, br = r[:5]
            if br > 0.01 and R > 1:
                if rb is None: rb = np.zeros_like(hot)
                cv2.circle(rb, (int(cx * hs * 16), int(cy * hs * 16)), int(R * hs * 16), float(min(1, br)),
                           max(1, int(th * hs)), cv2.LINE_AA, 4)
        if rb is not None:
            hot += cv2.GaussianBlur(rb, (0, 0), 3.5) * 0.55
        if not hot.any() and not pcol.any():
            return 0.0
        g1 = cv2.GaussianBlur(hot, (0, 0), 2.5); g2 = cv2.GaussianBlur(hot, (0, 0), 9)
        heatv = np.clip(hot * 1.1 + g1 * 1.3 + g2 * 1.6, 0, 1)
        pc = lut(FIRE_LUT, heatv) * np.clip(heatv * 3, 0, 1)[..., None]
        pc += pcol + cv2.GaussianBlur(pcol, (0, 0), 4) * 0.8
        return cv2.resize(pc, (W, H), interpolation=cv2.INTER_LINEAR)

    def heat_haze(self, img, t, hz):
        s = 0.25
        qh, qw = int(H * s), int(W * s)
        gy, gx = np.mgrid[0:qh, 0:qw].astype(np.float32) / s
        n1 = self.tex.sample(self.tex.smoke2, gx * 0.45, gy * 0.45 + t * 420) - 0.5
        n2 = self.tex.sample(self.tex.smoke1, gx * 0.5 + 50, gy * 0.5 + t * 520) - 0.5
        m = np.zeros((qh, qw), np.float32)
        x0, y0, x1, y1 = [int(v * s) for v in hz["box"]]
        m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1
        m = cv2.GaussianBlur(m, (0, 0), 14)
        dx = cv2.resize(n1 * m * hz["amt"] * 7, (W, H)); dy = cv2.resize(n2 * m * hz["amt"] * 10, (W, H))
        return cv2.remap(img, self.GX + dx, self.GY + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    def camera(self, img, cam):
        z, rot, x, y = cam.get("zoom", 1.0), cam.get("rot", 0.0), cam.get("x", 0.0), cam.get("y", 0.0)
        zb = cam.get("zoom_blur", 0.0)
        cx, cy = W / 2 + cam.get("cx", 0.0), H / 2 + cam.get("cy", 0.0)
        def M(zz):
            m = cv2.getRotationMatrix2D((cx, cy), rot, zz)
            m[0, 2] += x; m[1, 2] += y
            return m
        if abs(z - 1) < 1e-4 and abs(rot) < 1e-3 and abs(x) < 0.05 and abs(y) < 0.05 and zb < 0.002:
            return img
        if zb >= 0.002:
            n = int(min(10, 3 + zb * 60))
            acc = np.zeros_like(img)
            for i in range(n):
                acc += cv2.warpAffine(img, M(z * (1 + zb * i / (n - 1))), (W, H), flags=cv2.INTER_LINEAR,
                                      borderMode=cv2.BORDER_REFLECT)
            return acc / n
        return cv2.warpAffine(img, M(z), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ export
_R = None
def _init(scale):
    global _R
    cv2.setNumThreads(1)
    _R = Renderer(scale)

def _render_chunk(args):
    i0, i1, fps, path, scale, crf = args
    r = _R
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{r.W}x{r.H}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-x264-params", "keyint=60", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        fr = r.frame(i / fps)
        p.stdin.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR).tobytes())
    p.stdin.close(); p.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--out", default=os.path.join(ROOT, "output", "slava_marlow_toly_summer_lyrics_1080x1920_60fps.mp4"))
    ap.add_argument("--stills", type=float, nargs="*")
    ap.add_argument("--no-audio", action="store_true")
    a = ap.parse_args()
    tl = scenes.TL
    end = a.end if a.end is not None else tl["video"]["end"]

    if a.stills:
        _init(a.scale)
        os.makedirs(os.path.join(ROOT, "previews"), exist_ok=True)
        for t in a.stills:
            t0 = time.time(); fr = _R.frame(t)
            p = os.path.join(ROOT, "previews", f"still_{t:06.3f}.png")
            cv2.imwrite(p, cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            print(p, f"{time.time() - t0:.2f}s")
        return

    fps = a.fps
    i0, i1 = int(round(a.start * fps)), int(round(end * fps))
    n = i1 - i0
    tmp = os.path.join(ROOT, "output", ".chunks"); os.makedirs(tmp, exist_ok=True)
    nchunks = max(1, min(n, a.workers * 4))
    bounds = np.linspace(i0, i1, nchunks + 1).astype(int)
    jobs = [(int(bounds[k]), int(bounds[k + 1]), fps, os.path.join(tmp, f"c{k:03d}.mp4"), a.scale, a.crf)
            for k in range(nchunks) if bounds[k + 1] > bounds[k]]
    t0 = time.time()
    import multiprocessing as mp
    with mp.get_context("fork").Pool(a.workers, initializer=_init, initargs=(a.scale,)) as pool:
        for j, _ in enumerate(pool.imap(_render_chunk, jobs)):
            print(f"\rchunks {j + 1}/{len(jobs)}  {time.time() - t0:.0f}s", end="", flush=True)
    print()
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as fh:
        for j in jobs: fh.write(f"file '{os.path.basename(j[3])}'\n")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    audio = os.path.join(ROOT, tl["audio"])
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst]
    if not a.no_audio:
        # original AAC stream is copied bit-exact (no re-encode, no speed/pitch change)
        cmd += ["-ss", f"{a.start}", "-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "copy" if a.start == 0 else "aac",
                "-shortest"]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    for j in jobs: os.remove(j[3])
    os.remove(lst)
    print("wrote", a.out, f"({n} frames, {time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
