"""Animated stickers and effects in the style of the reference edit:
big 3D emoji stickers (pop + wobble), interlude emoji scenes in vocal gaps,
flying stickers with speed lines, bursts with camera shake, falling-emoji rain,
twinkling sparkles, burn transitions between song parts, beat pulses, flash."""
import math, random, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

EMO_DIR = "emoji"
_raw, _sz = {}, {}
def sprite(ch):
    if ch not in _raw:
        _raw[ch] = Image.open(f"{EMO_DIR}/emoji_u{ord(ch):04x}.png").convert("RGBA")
    return _raw[ch]
def sprite_at(ch, size, rot=0.0):
    k = (ch, int(size) // 4 * 4, int(round(rot)))
    if k not in _sz:
        s = max(8, k[1]); im = sprite(ch).resize((s, s), Image.LANCZOS)
        if k[2]: im = im.rotate(k[2], resample=Image.BICUBIC, expand=True)
        if len(_sz) > 4000: _sz.clear()
        _sz[k] = im
    return _sz[k]

def paste(layer, im, cx, cy, alpha=1.0):
    if alpha < 0.999:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2))) if _inside(layer, im, cx, cy) else _safe_paste(layer, im, cx, cy)

def _inside(layer, im, cx, cy):
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    return x >= 0 and y >= 0 and x + im.width <= layer.width and y + im.height <= layer.height
def _safe_paste(layer, im, cx, cy):
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    x0, y0 = max(0, -x), max(0, -y); x1, y1 = min(im.width, layer.width - x), min(im.height, layer.height - y)
    if x1 > x0 and y1 > y0: layer.alpha_composite(im.crop((x0, y0, x1, y1)), (x + x0, y + y0))

def ease_back(x, c=2.2):
    x = min(max(x, 0), 1); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------------------------------------------------------- keyword -> sticker
STICK = [("ковбой", "🤠"), ("сиги", "🚬"), ("рукой", "✋"), ("зеркал", "🪞"), ("москв", "🏙"), ("шалав", "💋"),
         ("красот", "💅"), ("пореж", "🔪"), ("выстрел", "🔫"), ("психопат", "😈"), ("флекс", "💎"), ("умр", "💀"),
         ("дым", "💨"), ("курю", "🚬"), ("отупел", "🤪"), ("прицел", "🎯"), ("сумма", "💸"), ("даун", "🤡"),
         ("думать", "🧠"), ("много", "💯"), ("непонят", "🤷"), ("династ", "👑"), ("миллион", "💰"), ("чемпион", "🏆"),
         ("кожу", "😬"), ("iphone", "📱"), ("samson", "🎙"), ("мама", "👩"), ("микрофон", "🎤"), ("тенью", "👤"),
         ("многоэтаж", "🏙"), ("цитат", "💬"), ("рэпер", "🎤"), ("золо", "🥇"), ("диагноз", "🩺"), ("психолог", "🧠"),
         ("наплевать", "🙄"), ("фотку", "📸"), ("глотку", "👊"), ("футболк", "👕"), ("наработк", "📝"), ("dexey", "🔥"),
         ("стреля", "🔫"), ("ляма", "💸"), ("забавно", "👀"), ("ненормальн", "😵")]
FLY = ("сумма", "миллион", "ляма", "флекс")          # flying winged money
BURST = ("стреля", "выстрел", "прицел", "глотку")     # explosion + shake
FILLERS = list("🔥😎💯🤘👀⚡🤑💥🚀🥶")

def kw(word):
    k = re.sub(r"[^а-яёa-z]", "", word.lower())
    for stem, e in STICK:
        if k.startswith(stem): return stem, e
    return None, None

# ---------------------------------------------------------------- sparkle sprite
def _make_sparkle(n=256):
    im = Image.new("RGBA", (n, n)); d = ImageDraw.Draw(im); c = n / 2
    def star(r, w, col):
        pts = []
        for i in range(8):
            a = i * math.pi / 4; rr = r if i % 2 == 0 else w
            pts.append((c + rr * math.cos(a - math.pi / 2), c + rr * math.sin(a - math.pi / 2)))
        d.polygon(pts, fill=col)
    star(n * 0.46, n * 0.07, (255, 205, 60, 255)); star(n * 0.26, n * 0.04, (255, 250, 210, 255))
    glow = Image.new("RGBA", (n, n)); ImageDraw.Draw(glow).ellipse((c - n * .22, c - n * .22, c + n * .22, c + n * .22), fill=(255, 190, 60, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(n * 0.08))
    glow.alpha_composite(im); return glow
SPARK = _make_sparkle()
_spk = {}
def sparkle_at(size):
    k = max(8, int(size) // 6 * 6)
    if k not in _spk: _spk[k] = SPARK.resize((k, k), Image.LANCZOS)
    return _spk[k]

# ---------------------------------------------------------------- build events
def build(cards, beats, song_len, W, H, sections):
    rnd = random.Random(11)
    ev = {"stick": [], "fly": [], "burst": [], "rain": [], "flash": [], "shake": []}
    last_e = None
    for i, c in enumerate(cards):
        used = 0
        for w in c["words"]:
            stem, e = kw(w["w"])
            if not e or used >= 1 or e == last_e: continue
            used += 1; last_e = e
            above = c["ytop"] > 760
            cy = c["ytop"] - 270 if above else c["ybot"] + 280
            cy = min(max(cy, 260), H - 260)
            ev["stick"].append({"e": e, "t0": w["t"], "t1": c["end"], "x": rnd.uniform(300, W - 300), "y": cy,
                                "s": rnd.uniform(380, 460), "ph": rnd.uniform(0, 6)})
            if stem in FLY:
                ev["fly"].append({"e": "💸", "t0": w["t"] + 0.1, "dur": 1.2, "y": rnd.uniform(500, 1400), "s": 300, "dir": rnd.choice([1, -1])})
            if stem in BURST:
                ev["burst"].append({"t0": w["t"], "x": rnd.uniform(250, W - 250), "y": rnd.uniform(400, H - 400)})
                ev["shake"].append(w["t"])
        # vocal gap -> interlude emoji scene
        nxt = cards[i + 1]["start"] if i + 1 < len(cards) else song_len
        if nxt - c["end"] >= 0.45:
            e = rnd.choice([f for f in FILLERS if f != last_e]); last_e = e
            ev["stick"].append({"e": e, "t0": c["end"], "t1": nxt, "x": W / 2, "y": H / 2, "s": 640, "ph": 0, "solo": 1})
    if cards and cards[0]["start"] > 0.8:   # intro
        ev["stick"].append({"e": "👑", "t0": 0.15, "t1": cards[0]["start"], "x": W / 2, "y": H / 2, "s": 640, "ph": 0, "solo": 1})
    for s in sections:
        if s.get("rain"):
            for k in range(18):
                ev["rain"].append({"e": rnd.choice("💰💸🤑"), "t0": s["t"] + rnd.uniform(0, 1.6), "x": rnd.uniform(60, W - 60),
                                   "v": rnd.uniform(1300, 2100), "s": rnd.uniform(150, 250), "r0": rnd.uniform(-30, 30), "vr": rnd.uniform(-120, 120)})
        if s.get("flash"): ev["flash"].append(s["t"])
    # sparkle field for choruses
    ev["spark"] = [{"x": rnd.uniform(40, W - 40), "y": rnd.uniform(60, H - 60), "s": rnd.uniform(50, 130),
                    "ph": rnd.uniform(0, 6.28), "sp": rnd.uniform(3, 6)} for _ in range(26)]
    ev["spark_on"] = [(s["t"], s["t1"]) for s in sections if s.get("spark")]
    ev["beats"] = np.array(beats)
    return ev

# ---------------------------------------------------------------- per-frame drawing
def beat_pulse(ev, t, tau=0.09):
    b = ev["beats"]; i = np.searchsorted(b, t) - 1
    return 0.0 if i < 0 else math.exp(-(t - b[i]) / tau)

def draw_stickers(layer, ev, t, W, H):
    """stickers, flyers, bursts, rain -> PIL RGBA layer (they get the drop shadow)."""
    for s in ev["stick"]:
        if not (s["t0"] <= t < s["t1"]): continue
        a = (t - s["t0"]) / 0.22; ex = (s["t1"] - t) / 0.14
        sc = ease_back(a) * (min(1, ex) if ex < 1 else 1)
        if sc <= 0.02: continue
        wob = math.sin((t - s["t0"]) * 2 * math.pi * 1.3 + s["ph"]) * 9
        bob = math.sin((t - s["t0"]) * 2 * math.pi * 0.9 + s["ph"]) * 16
        size = s["s"] * sc * (1 + 0.05 * beat_pulse(ev, t))
        paste(layer, sprite_at(s["e"], size, wob), s["x"], s["y"] + bob)
    d = ImageDraw.Draw(layer)
    for f in ev["fly"]:
        u = (t - f["t0"]) / f["dur"]
        if not 0 <= u < 1: continue
        x0, x1 = (-250, W + 250) if f["dir"] > 0 else (W + 250, -250)
        x = x0 + (x1 - x0) * u; y = f["y"] - 450 * u + math.sin(u * 12) * 30
        for k in range(4):   # speed lines
            yy = y - 60 + k * 40; ln = 160 + 40 * (k % 2)
            d.line([(x - f["dir"] * (170), yy), (x - f["dir"] * (170 + ln), yy + 450 / W * ln * f["dir"] * 0.5)], fill=(255, 255, 255, 200), width=9)
        paste(layer, sprite_at(f["e"], f["s"], -15 * f["dir"]), x, y)
    for b in ev["burst"]:
        u = (t - b["t0"]) / 0.45
        if not 0 <= u < 1: continue
        paste(layer, sprite_at("💥", 420 * ease_back(min(1, u * 3.5))), b["x"], b["y"], alpha=1 - max(0, (u - 0.5) * 2))
    for r in ev["rain"]:
        dt = t - r["t0"]
        if dt < 0: continue
        y = -150 + r["v"] * dt
        if y > H + 200: continue
        paste(layer, sprite_at(r["e"], r["s"], r["r0"] + r["vr"] * dt), r["x"] + math.sin(dt * 3 + r["x"]) * 25, y)

def draw_sparkles(layer, ev, t):
    on = any(a <= t < b for a, b in ev["spark_on"])
    if not on: return
    for s in ev["spark"]:
        v = math.sin(s["ph"] + t * s["sp"])
        if v <= 0.05: continue
        paste(layer, sparkle_at(s["s"] * v), s["x"], s["y"])

def shake_offset(ev, t):
    dx = dy = 0.0
    for t0 in ev["shake"]:
        u = t - t0
        if 0 <= u < 0.25:
            a = 22 * (1 - u / 0.25); dx += a * math.sin(u * 95); dy += a * math.cos(u * 77)
    return dx, dy

def flash_amount(ev, t):
    return max([0.0] + [0.75 * math.exp(-(t - f) / 0.07) for f in ev["flash"] if t >= f])

# ---------------------------------------------------------------- burn transition
_noise = None
def burn_mix(a, b, u, seed=0):
    """a -> b with a ragged burning hole growing from the middle; u in 0..1."""
    global _noise
    H, W = a.shape[:2]; h, w = H // 4, W // 4
    if _noise is None:
        rng = np.random.default_rng(5)
        n = sum(cv2.resize(rng.random((h // s + 2, w // s + 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC) / k
                for s, k in ((40, 1), (16, 2), (6, 4)))
        _noise = (n - n.min()) / (n.max() - n.min())
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * (0.35 + 0.3 * ((seed * 37) % 10) / 10), h * (0.4 + 0.2 * ((seed * 53) % 10) / 10)
    dist = np.hypot((xx - cx) / w, (yy - cy) / w) / 1.1
    field = dist * 0.75 + _noise * 0.25
    p = u * 1.15
    m = np.clip((p - field) / 0.012, 0, 1)
    edge = np.clip(1 - np.abs(p - field) / 0.03, 0, 1) * (u < 0.98)
    m = cv2.resize(m, (W, H))[..., None]; edge = cv2.resize(cv2.GaussianBlur(edge, (0, 0), 1.5), (W, H))[..., None]
    out = a * (1 - m) + b * m
    fire = np.array([255, 170, 30], np.float32)
    return out * (1 - edge) + fire * edge
