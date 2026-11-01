"""Kinetic-typography lyric video for "ДИНАСТИЯ" (VILLIAN, madk1d).

Vertical 9:16 frame with a colourful 16:9 band in the middle; lyrics pop in
word by word with emojis, sparkles and a beat pulse.

usage: python render.py song.mp3 out.mp4 [--preview SECONDS] [--start SECONDS]
"""
import json, math, os, random, re, subprocess, sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from lyrics import SECTIONS, CHORUS, EMOJI

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Rubik[wght].ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS = 720, 1280, 30
BW, BH = 720, 1280
BY = (H - BH) // 2
SIZES = {"big": 96, "mid": 66, "small": 42}
MAXW, MAXH = 640, 900

PALETTES = [
    ((255, 214, 40), (255, 150, 25)),   # yellow
    ((255, 160, 150), (240, 105, 110)),  # salmon
    ((245, 90, 225), (255, 130, 205)),   # magenta
    ((150, 115, 255), (105, 95, 245)),   # purple
    ((255, 175, 45), (255, 100, 35)),    # orange
    ((255, 70, 150), (190, 40, 150)),    # hot pink
    ((95, 145, 255), (150, 105, 255)),   # blue
]

SMALL_WORDS = {"я", "в", "на", "и", "ты", "а", "но", "не", "мы", "то", "из", "со",
               "мне", "мой", "моя", "так", "же", "что", "чё", "как", "ведь", "уже",
               "все", "всё", "это", "до", "по", "дам", "там", "тут", "в", "за", "с",
               "бы", "мои", "свой", "ещё", "тебе", "тебя", "меня", "была", "было"}


def syl(s):
    return max(1, len(re.findall(r"[аеёиоуыэюяaeiouy]", s.lower())))


# ---------------------------------------------------------------- timeline
def load_beats(song):
    cache = os.path.join(HERE, "beats.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    import librosa
    y, sr = librosa.load(song, sr=22050)
    _, b = librosa.beat.beat_track(y=y, sr=sr)
    beats = librosa.frames_to_time(b, sr=sr).round(3).tolist()
    json.dump(beats, open(cache, "w"))
    return beats


def parse_tokens(text):
    toks = []
    for raw in text.split():
        kind = "mid"
        w = raw
        if w.startswith("*") or w.endswith("*") or "*" in w:
            kind = "big"
            w = w.replace("*", "")
        elif w.startswith("_") and w.endswith("_"):
            kind = "small"
            w = w.strip("_")
        bare = re.sub(r"[^\w«»\-]", "", w.lower())
        if kind == "mid" and (bare in SMALL_WORDS or len(bare) <= 2):
            kind = "small"
        toks.append({"text": w.upper(), "kind": kind, "bare": bare, "syl": syl(w)})
    return toks


def emoji_for(bare):
    b = bare.strip("«»-")
    for stem, e in EMOJI.items():
        if b.startswith(stem.strip("«»")) or bare == stem:
            return e
    return None


def load_timeline():
    """Use aligned timings from align.py when available."""
    p = os.path.join(HERE, "timeline.json")
    if not os.path.exists(p):
        return None
    screens = json.load(open(p))
    if not screens or "word_times" not in screens[0]:
        return None
    for sc in screens:
        toks = parse_tokens(sc["text"])
        for t, at in zip(toks, sc["word_times"]):
            t["at"] = at
            t["emoji"] = emoji_for(t["bare"])
        sc["toks"] = toks
    return screens


def build_screens(beats):
    beats = np.array(beats)

    def snap(t):
        i = np.abs(beats - t).argmin()
        return float(beats[i]) if abs(beats[i] - t) < 0.25 else t

    screens = []
    pal_i = 0
    for name, s0, s1, mode, lines in SECTIONS:
        if mode == "chorus":
            lines = CHORUS
            first = 1.75
            rest = (s1 - s0 - first) / (len(lines) - 1)
            starts = [s0, s0 + first] + [s0 + first + rest * k for k in range(1, len(lines) - 1)]
        elif mode == "even":
            d = (s1 - s0) / len(lines)
            starts = [s0 + d * k for k in range(len(lines))]
        else:
            wts = [syl(l) + 3 for l in lines]
            tot = sum(wts)
            acc, starts = 0, []
            for w in wts:
                starts.append(s0 + (s1 - s0) * acc / tot)
                acc += w
        starts = [starts[0]] + [snap(t) for t in starts[1:]]
        ends = starts[1:] + [s1]
        for li, (line, a, b) in enumerate(zip(lines, starts, ends)):
            parts = [p.strip() for p in line.split("||")]
            pw = [sum(t["syl"] for t in parse_tokens(p)) + 2 for p in parts]
            t = a
            for p, w in zip(parts, pw):
                d = (b - a) * w / sum(pw)
                special = name in ("title", "drop") or (name == "outro" and "DEXEY" in p)
                if special:
                    pal = {"title": 4, "drop": 5, "outro": 2}[name]
                else:
                    pal = pal_i % len(PALETTES)
                    pal_i += 1
                screens.append({"start": t, "end": t + d, "text": p, "section": name,
                                "pal": pal, "special": special})
                t += d
    # word reveal times
    for sc in screens:
        toks = parse_tokens(sc["text"])
        d = sc["end"] - sc["start"]
        span = min(d * 0.72, 0.28 * sum(t["syl"] for t in toks) + 0.1)
        tot = sum(t["syl"] for t in toks)
        acc = 0
        for t in toks:
            t["at"] = sc["start"] + span * acc / tot
            acc += t["syl"]
            t["emoji"] = emoji_for(t["bare"])
        sc["toks"] = toks
    return screens


# ---------------------------------------------------------------- drawing
@lru_cache(maxsize=None)
def font(size):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([900])
    except Exception:
        pass
    return f


@lru_cache(maxsize=None)
def emoji_img(e, size):
    e = e.replace("️", "").replace("‍", "")
    e = e[0]
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), e, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox() or (0, 0, 1, 1))
    r = size / max(im.size)
    im = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return im


@lru_cache(maxsize=None)
def word_img(text, size):
    """White word with a soft drop shadow. Returns (img, baseline_y, pad)."""
    f = font(size)
    l, t, r, b = f.getbbox(text, anchor="ls")
    pad = 14
    w, h = r - l + pad * 2, b - t + pad * 2
    base = -t + pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sh).text((pad - l + 2, base + 5), text, font=f, fill=95, anchor="ls")
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    im.putalpha(sh)
    d = ImageDraw.Draw(im)
    d.text((pad - l, base), text, font=f, fill=(255, 255, 255, 255), anchor="ls",
           stroke_width=max(1, size // 30), stroke_fill=(255, 255, 255, 255))
    return im, base, pad


@lru_cache(maxsize=None)
def bg_img(pal):
    c1, c2 = (np.array(c, float) for c in PALETTES[pal])
    bw, bh = int(BW * 1.12), int(BH * 1.12)
    yy, xx = np.mgrid[0:bh, 0:bw]
    g = ((xx / bw) * 0.6 + (yy / bh) * 0.4)[..., None]
    img = c1 * (1 - g) + c2 * g
    r = np.sqrt(((xx - bw / 2) / (bw / 2)) ** 2 + ((yy - bh / 2) / (bh / 2)) ** 2)[..., None]
    img = img + (1 - np.clip(r, 0, 1)) * 28          # soft centre glow
    img = img * (1 - np.clip(r - 0.75, 0, 1) * 0.25)  # light vignette
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def ease_back(x):
    x = min(max(x, 0), 1)
    c1, c3 = 1.9, 2.9
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def layout(sc):
    """Place tokens (and inline emojis) into centred rows inside the band."""
    items = []
    for t in sc["toks"]:
        size = SIZES[t["kind"]] * (1.45 if sc["special"] else 1)
        items.append({"type": "w", "text": t["text"], "size": int(size), "at": t["at"]})
        if t["emoji"] and not (sc["special"] and t["emoji"] == "👑"):
            items.append({"type": "e", "e": t["emoji"], "size": int(size * 1.05), "at": t["at"] + 0.06})
    gap = 16
    for it in items:
        if it["type"] == "w":
            im, base, pad = word_img(it["text"], it["size"])
            it["w"], it["h"] = im.width - 2 * pad, int(it["size"] * 0.78)
        else:
            im = emoji_img(it["e"], it["size"])
            it["w"], it["h"] = im.width, im.height * 0.8
    rows, cur, cw = [], [], 0
    for it in items:
        if cur and cw + gap + it["w"] > MAXW * 0.92 and it["type"] == "w":
            rows.append(cur); cur, cw = [], 0
        cur.append(it); cw += it["w"] + (gap if cur[:-1] else 0)
    if cur:
        rows.append(cur)
    # merge a lone small leftover into the previous row
    rw = [sum(i["w"] for i in r) + gap * (len(r) - 1) for r in rows]
    rh = [max(i["h"] for i in r) for r in rows]
    lg = 16
    tw, th = max(rw), sum(rh) + lg * (len(rows) - 1)
    scale = min(1, MAXW / tw, MAXH / th)
    y = BH / 2 - th * scale / 2
    for ri, (r, w, h) in enumerate(zip(rows, rw, rh)):
        jog = (ri % 2 * 2 - 1) * 18 * (len(rows) > 1)
        x = BW / 2 - w * scale / 2 + jog * scale
        baseline = y + h * scale
        for it in r:
            it["x"], it["base"], it["scale"] = x, baseline, scale
            x += (it["w"] + gap) * scale
        y += (h + lg) * scale
    return items


def draw_items(band, items, t, out_k):
    for it in items:
        dt = t - it["at"]
        if dt < 0:
            continue
        k = ease_back(dt / 0.2) * out_k
        a = min(1, dt / 0.07)
        s = it["scale"] * max(k, 0.05)
        if it["type"] == "w":
            im, base, pad = word_img(it["text"], it["size"])
            cx = it["x"] + it["w"] * it["scale"] / 2
            cy = it["base"] - it["h"] * it["scale"] / 2
            nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
            im2 = im.resize((nw, nh), Image.BILINEAR)
            # map word centre
            px = cx - (pad + it["w"] / 2) * s
            py = cy - (base - it["h"] / 2) * s + (1 - min(1, dt / 0.15)) * 14
        else:
            im = emoji_img(it["e"], it["size"])
            wob = math.sin(dt * 6) * 0.06
            nw, nh = max(1, int(im.width * s * (1 + wob))), max(1, int(im.height * s * (1 - wob)))
            im2 = im.resize((nw, nh), Image.BILINEAR)
            px = it["x"] + it["w"] * it["scale"] / 2 - nw / 2
            py = it["base"] - it["h"] * it["scale"] / 2 - nh / 2
        if a < 1:
            im2 = im2.copy()
            im2.putalpha(im2.getchannel("A").point(lambda v: int(v * a)))
        band.paste(im2, (int(px), int(py)), im2)


def star(d, x, y, r, col):
    p = []
    for i in range(8):
        ang = i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.28
        p.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    d.polygon(p, fill=col)


def draw_rays(band, t, pal):
    c = tuple(min(255, v + 40) for v in PALETTES[pal][0]) + (90,)
    lay = Image.new("RGBA", band.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy, R = BW / 2, BH / 2, 1600
    for i in range(16):
        a0 = t * 0.6 + i * math.pi / 8
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a0 + 0.22), cy + R * math.sin(a0 + 0.22))], fill=c)
    band.alpha_composite(lay)


class Renderer:
    def __init__(self, screens, beats):
        self.screens = screens
        self.beats = np.array(beats)
        self.layouts = {}
        rnd = random.Random(7)
        self.stars = [(rnd.random() * BW, rnd.random() * BH, rnd.random() * 6, 8 + rnd.random() * 14)
                      for _ in range(34)]
        self.floaters = [(rnd.random(), rnd.random(), 0.5 + rnd.random()) for _ in range(12)]

    def screen_at(self, t):
        for i, sc in enumerate(self.screens):
            if sc["start"] <= t < sc["end"]:
                return i, sc
        return len(self.screens) - 1, self.screens[-1]

    def frame(self, n):
        t = n / FPS
        i, sc = self.screen_at(t)
        if i not in self.layouts:
            self.layouts[i] = layout(sc)
        items = self.layouts[i]
        # beat pulse (every other beat = half-time kick)
        prev = self.beats[self.beats <= t]
        pulse = 0
        if len(prev):
            bi = len(prev) - 1
            pulse = math.exp(-(t - prev[-1]) * 9) * (0.03 if bi % 2 == 0 else 0.012)
        since = t - sc["start"]
        intro = math.exp(-since * 14) * 0.06
        z = 1 + pulse + intro
        bg = bg_img(sc["pal"])
        cw, ch = BW / z, BH / z
        ox, oy = (bg.width - cw) / 2, (bg.height - ch) / 2
        band = bg.crop((int(ox), int(oy), int(ox + cw), int(oy + ch))).resize((BW, BH), Image.BILINEAR).convert("RGBA")

        chorus = sc["section"].startswith("chorus") or sc["special"]
        if sc["special"]:
            draw_rays(band, t, sc["pal"])
        if chorus:
            d = ImageDraw.Draw(band)
            for (x, y, ph, r) in self.stars:
                k = (math.sin(t * 4 + ph) + 1) / 2
                star(d, x, y, r * (0.4 + 0.8 * k), (255, 250, 200, 255))
        # floating emoji behind the text
        emo = next((it["e"] for it in items if it["type"] == "e"), None)
        if emo and not sc["special"]:
            for fx, fy, sp in self.floaters:
                yy = (fy * BH * 1.4 - since * 60 * sp) % (BH * 1.4) - BH * 0.2
                im = emoji_img(emo, 48)
                im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: v * 55 // 100))
                band.paste(im, (int(fx * (BW - 40)), int(yy)), im)
        if sc["special"] and sc["section"] in ("title", "drop"):
            crown = emoji_img("👑", 150)
            bob = math.sin(t * 7) * 6
            k = ease_back(since / 0.3)
            c2 = crown.resize((max(1, int(crown.width * k)), max(1, int(crown.height * k))))
            band.paste(c2, (int(BW / 2 - c2.width / 2), int(BH / 2 - 300 + bob)), c2)
        # text, with a quick pop-out at the end of the screen
        left = sc["end"] - t
        out_k = 1 + max(0, 0.1 - left) * 1.5
        draw_items(band, items, t, out_k)
        if sc["section"] == "drop" and since < 0.15:
            band = Image.blend(band, Image.new("RGBA", band.size, (255, 255, 255, 255)), 0.7 * (1 - since / 0.15))
        frame = Image.new("RGB", (W, H), (0, 0, 0))
        frame.paste(band.convert("RGB"), (0, BY))
        return frame.tobytes()


R = None


def _init(screens, beats):
    global R
    R = Renderer(screens, beats)


def _render(n):
    return R.frame(n)


def main():
    song, out = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    start = float(args[args.index("--start") + 1]) if "--start" in args else 0.0
    dur_total = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", song]))
    dur = float(args[args.index("--preview") + 1]) if "--preview" in args else dur_total - start
    beats = load_beats(song)
    screens = load_timeline() or build_screens(beats)
    frames = range(int(start * FPS), int((start + dur) * FPS))
    ff = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-ss", str(start), "-t", str(dur), "-i", song,
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out,
    ], stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init, initargs=(screens, beats)) as pool:
        for k, buf in enumerate(pool.imap(_render, frames, chunksize=6)):
            ff.stdin.write(buf)
            if k % 300 == 0:
                print(f"frame {k}/{len(frames)}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done", out)


if __name__ == "__main__":
    main()
