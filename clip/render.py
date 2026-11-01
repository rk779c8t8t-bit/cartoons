"""Kinetic-typography renderer in the style of the reference clip.

Usage:
  python3 render.py AUDIO OUT.mp4            full render
  python3 render.py AUDIO OUT.png --at 12.3  single still (for checks)
"""
import json, math, os, random, re, shutil, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920          # full-screen 9:16
BY, BW, BH = 0, 1080, 1920  # picture fills the whole frame
FPS = 30
FONT = "fonts/fonts_Rubik.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
BG = "bg.mp4"
MAXW = 900  # safe text width (room for zoom, tilt and letter overshoot)

SMALL = set("и в во на но а я ты мы не так то что же как это мне тебя со из за по до у о ведь чё а ли бы был было".split())
EMOJI = {"ковбой": "🤠", "зеркало": "🪞", "москву": "🏙", "красота": "💅", "порежу": "🔪", "выстрелишь": "🔫",
         "дым": "💨", "прицел": "🎯", "сумма": "💰", "династия": "👑", "миллион": "💰", "чемпион": "🏆",
         "iphone": "📱", "микрофон": "🎤", "многоэтажек": "🏙", "фотку": "📸", "футболку": "👕",
         "психопаты": "😈", "умрём": "💀", "samson": "🎙"}
EMOJI = {}  # inline emoji replaced by animated stickers (fx.py)

_fc = {}
def font(sz):
    sz = max(4, int(round(sz)))
    if sz not in _fc: _fc[sz] = ImageFont.truetype(FONT, sz)
    return _fc[sz]
_EF = ImageFont.truetype(EMOJI_FONT, 109)
_ec = {}
def emoji_img(ch):
    if ch not in _ec:
        im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((10, 10), ch, font=_EF, embedded_color=True)
        _ec[ch] = im.crop(im.getbbox())
    return _ec[ch]

def clean_word(w):
    w = w.strip("«»\"',.:;!?()…").replace("«", "").replace("»", "")
    return w.upper() if w not in ("-", "—") else ""
def key(w): return re.sub(r"[^а-яёa-z]", "", w.lower())

def ease_back(x):  # 0..1 -> overshoot then settle
    x = min(max(x, 0), 1); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

# ---------------------------------------------------------------- cards
def build_cards(timing, song_len):
    words, lines = timing["words"], timing["lines"]
    cards = []
    for li in range(len(lines)):
        ws = [dict(w) for w in words if w["line"] == li]
        ws = [w for w in ws if clean_word(w["w"])]
        # split long lines into two cards (at a comma near the middle if possible)
        chunks = [ws]
        if sum(len(w["w"]) + 1 for w in ws) > 34 and len(ws) > 3:
            mid = len(ws) // 2
            cands = [i for i in range(2, len(ws) - 1) if ws[i - 1]["w"][-1] in ",?!-"]
            cut = min(cands, key=lambda i: abs(i - mid)) if cands and min(abs(i - mid) for i in cands) <= 2 else mid
            chunks = [ws[:cut], ws[cut:]]
        for ch in chunks: cards.append({"words": ch})
    allw = [w for c in cards for w in c["words"]]
    for i, w in enumerate(allw):
        nxt = allw[i + 1]["t"] if i + 1 < len(allw) else song_len
        w["d"] = max(0.08, min(0.06 * len(clean_word(w["w"])) + 0.05, nxt - w["t"]))
    rnd = random.Random(7)
    for i, c in enumerate(cards):
        c["start"] = c["words"][0]["t"] - 0.03
        last = c["words"][-1]; lim = last["t"] + last["d"] + 1.1
        c["end"] = min(lim, cards[i + 1]["words"][0]["t"] - 0.03) if i + 1 < len(cards) else min(lim + 1, song_len)
        c["align"] = rnd.choice(["c", "c", "l"])
        c["rot0"] = rnd.uniform(-3, 3); c["rot1"] = c["rot0"] + rnd.uniform(-2, 2)
        c["dy"] = rnd.uniform(-120, 120)
        layout(c)
    return cards

def word_scale(w, card):
    k = key(w["w"])
    if k in SMALL or len(k) <= 2: return 0.58
    if w is card["hero"]: return 1.3
    return 1.0

def layout(card):
    ws = card["words"]
    content = [w for w in ws if key(w["w"]) not in SMALL and len(key(w["w"])) > 3]
    card["hero"] = max(content, key=lambda w: len(key(w["w"]))) if content else None
    for base in range(170, 40, -3):
        rows, row, rw = [], [], 0
        sp = base * 0.22
        for w in ws:
            s = base * word_scale(w, card); txt = clean_word(w["w"])
            wd = font(s).getlength(txt) + (s * 1.05 if EMOJI.get(key(w["w"])) else 0)
            if row and rw + sp + wd > MAXW: rows.append(row); row, rw = [], 0
            row.append((w, s, txt, wd)); rw += (sp if len(row) > 1 else 0) + wd
        rows.append(row)
        hts = [max(s for _, s, _, _ in r) * 0.80 for r in rows]
        widths = [sum(x[3] for x in r) + sp * (len(r) - 1) for r in rows]
        if len(rows) <= 4 and max(widths) <= MAXW and sum(hts) + base * 0.12 * (len(rows) - 1) <= 1000: break
    # absolute positions (band coords), letters with their own anchor
    total_h = sum(hts) + base * 0.12 * (len(rows) - 1)
    y = BH / 2 - total_h / 2 + card["dy"]
    y = min(max(y, 160), BH - 160 - total_h)
    glyphs = []
    for r, h in zip(rows, hts):
        y += h; width = sum(wd for _, _, _, wd in r) + base * 0.22 * (len(r) - 1)
        x = (BW - width) / 2 if card["align"] == "c" else 90
        for w, s, txt, wd in r:
            f = font(s); n = len(txt)
            for i, ch in enumerate(txt):
                cx = x + f.getlength(txt[:i]); cw = f.getlength(ch)
                glyphs.append({"ch": ch, "x": cx + cw / 2, "y": y, "s": s,
                               "t": w["t"] + w["d"] * i / max(n, 1)})
            e = EMOJI.get(key(w["w"]))
            if e:
                glyphs.append({"emoji": e, "x": x + f.getlength(txt) + s * 0.6, "y": y, "s": s * 0.95,
                               "t": w["t"] + w["d"]})
            x += wd + base * 0.22
        y += base * 0.12
    card["glyphs"] = glyphs
    card["ytop"] = min(g["y"] - g["s"] * 0.8 for g in glyphs); card["ybot"] = max(g["y"] for g in glyphs)

# ---------------------------------------------------------------- drawing
def draw_card(card, t, pulse=0.0):
    """RGBA band-size layer with the card at time t (or None)."""
    if not (card["start"] <= t < card["end"]): return None
    life = (t - card["start"]) / max(card["end"] - card["start"], 0.01)
    layer = Image.new("RGBA", (BW, BH)); d = ImageDraw.Draw(layer)
    for g in card["glyphs"]:
        a = (t - g["t"]) / 0.13
        if a <= 0: continue
        sc = 0.25 + 0.75 * ease_back(a); al = int(255 * min(1, a * 1.6))
        if "emoji" in g:
            im = emoji_img(g["emoji"]); hh = g["s"] * 0.95 * sc
            ww = im.width * hh / im.height
            im = im.resize((max(1, int(ww)), max(1, int(hh))), Image.LANCZOS)
            if al < 255: im.putalpha(im.getchannel("A").point(lambda v: v * al // 255))
            layer.alpha_composite(im, (int(g["x"] - ww / 2), int(g["y"] - hh * 0.92)))
            continue
        f = font(g["s"] * sc)
        d.text((g["x"], g["y"] + (1 - min(a, 1)) * g["s"] * 0.15), g["ch"], font=f, anchor="ms", fill=(255, 255, 255, al))
    # whole-card motion: slow push-in + drift rotation, squash-out exit
    zoom = (1.0 + 0.05 * life) * (1 + 0.035 * pulse)
    rot = card["rot0"] + (card["rot1"] - card["rot0"]) * life
    sx = sy = zoom; alpha = 1.0
    ex = (card["end"] - t) / 0.16
    if ex < 1:
        e = 1 - ex; sy *= 1 - 0.85 * e; sx *= 1 + 0.15 * e; alpha = ex
    cx, cy = BW / 2, BH / 2
    M = cv2.getRotationMatrix2D((cx, cy), rot, 1.0)
    M[:, :2] = M[:, :2] @ np.diag([sx, sy]); M[:, 2] = [cx, cy] - M[:, :2] @ [cx, cy]
    arr = cv2.warpAffine(np.asarray(layer), M, (BW, BH), flags=cv2.INTER_LINEAR)
    if alpha < 1: arr[..., 3] = (arr[..., 3] * alpha).astype(np.uint8)
    return arr

def composite(bg, layer):
    """bg: HxWx3 uint8 RGB band. layer: RGBA uint8. Adds the soft drop shadow."""
    out = bg.astype(np.float32)
    if layer is not None:
        a = layer[..., 3].astype(np.float32) / 255
        sh = cv2.GaussianBlur(np.roll(np.roll(a, 8, 0), 6, 1), (0, 0), 6.0) * 0.35
        out *= (1 - sh[..., None])
        out = out * (1 - a[..., None]) + layer[..., :3].astype(np.float32) * a[..., None]
    return out

import fx
from multiprocessing import Pool

class Background:
    """Clean plate held in memory; each song part starts at its own scene, kicks punch the zoom,
    part changes use the burn transition."""
    def __init__(self, path, sections, kicks):
        cap = cv2.VideoCapture(path); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        self.fr = np.stack(fr); self.n = len(fr); self.sec = sections; self.kicks = np.array(kicks)
        rng = np.random.default_rng(3)
        self.grain = [cv2.resize(rng.normal(0, 5, (BH // 2, BW // 2)).astype(np.float32), (BW, BH))[..., None] for _ in range(6)]
    def plate(self, si, t, zoom):
        s = self.sec[si]; idx = int(round((t - s["t"]) * FPS + s["bgoff"])) % self.n
        f = self.fr[idx]; h, w = f.shape[:2]
        ch = h / zoom; cw = ch * W / H; x0 = (w - cw) / 2; y0 = (h - ch) / 2
        M = np.float32([[W / cw, 0, -x0 * W / cw], [0, H / ch, -y0 * H / ch]])
        return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    def frame(self, t):
        i = np.searchsorted(self.kicks, t) - 1
        zoom = 1.0 + (0.045 * math.exp(-(t - self.kicks[i]) / 0.11) if i >= 0 else 0)
        si = max(k for k, s in enumerate(self.sec) if s["t"] <= t) if t >= self.sec[0]["t"] else 0
        cur = self.plate(si, t, zoom)
        u = (t - self.sec[si]["t"]) / 0.55
        if si > 0 and u < 1 and self.sec[si].get("burn"):
            cur = fx.burn_mix(self.plate(si - 1, t, zoom), cur, u, seed=si)
        return cur

def alpha_over(dst, src):
    a = src[..., 3:4].astype(np.float32) / 255
    out = dst.astype(np.float32); out[..., :3] = out[..., :3] * (1 - a) + src[..., :3] * a
    out[..., 3:4] = 255 * (a + dst[..., 3:4] / 255 * (1 - a)); return out.astype(np.uint8)

G = {}
def render_frame(t, fi):
    cards, ev, bg = G["cards"], G["ev"], G["bg"]
    band = bg.frame(t)
    pulse = fx.beat_pulse(ev, t)
    stick = Image.new("RGBA", (W, H)); fx.draw_stickers(stick, ev, t, W, H)
    layer = np.asarray(stick)
    for c in cards:
        l = draw_card(c, t, pulse)
        if l is not None: layer = alpha_over(layer, l)
    out = composite(band, layer)
    sp = Image.new("RGBA", (W, H)); fx.draw_sparkles(sp, ev, t); sp = np.asarray(sp)
    a = sp[..., 3:4] / 255.0; out = out * (1 - a) + sp[..., :3] * a
    fl = fx.flash_amount(ev, t)
    if fl > 0.01: out = out * (1 - fl) + 255 * fl
    out += bg.grain[fi % 6]
    dx, dy = fx.shake_offset(ev, t)
    out = np.clip(out, 0, 255).astype(np.uint8)
    if abs(dx) + abs(dy) > 0.5:
        out = cv2.warpAffine(out, np.float32([[1.03, 0, dx - W * 0.015], [0, 1.03, dy - H * 0.015]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return out

def sections_from(timing, song):
    L = timing["lines"]; Wd = timing["words"]
    t = lambda li: min(w["t"] for w in Wd if w["line"] == li)
    c1 = next(i for i, l in enumerate(L) if l["sect"] == "C1"); c2 = next(i for i, l in enumerate(L) if l["sect"] == "C2")
    v2 = next(i for i in range(c1, len(L)) if L[i]["sect"] is None)
    S = [dict(t=0.0, bgoff=0), dict(t=t(4) - 0.05, bgoff=600, burn=1),
         dict(t=t(c1 - 1) - 0.05, bgoff=1250, burn=1, flash=1, spark=1),
         dict(t=t(c1) - 0.05, bgoff=1290, rain=1, spark=1),
         dict(t=t(v2) - 0.05, bgoff=300, burn=1),
         dict(t=t(c2) - 0.05, bgoff=1250, burn=1, rain=1, spark=1, flash=1),
         dict(t=t(len(L) - 1) - 0.05, bgoff=1800, burn=1, flash=1)]
    for a, b in zip(S, S[1:] + [dict(t=song)]): a["t1"] = b["t"]
    return S

def setup(audio):
    song = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]))
    timing = json.load(open("timing.json", encoding="utf-8")); beats = json.load(open("beats.json"))
    cards = build_cards(timing, song); secs = sections_from(timing, song)
    G.update(cards=cards, song=song, ev=fx.build(cards, beats["beats"], song, W, H, secs), bg=Background(BG, secs, beats["kicks"]))
    return song

def work(args):
    a, b, path = args
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "26", "-preset", "medium", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(render_frame(fi / FPS, fi).tobytes())
    p.stdin.close(); p.wait(); return path

def main():
    audio, out = sys.argv[1], sys.argv[2]
    song = setup(audio)
    if "--at" in sys.argv:
        for i, t in enumerate(map(float, sys.argv[sys.argv.index("--at") + 1].split(","))):
            Image.fromarray(render_frame(t, int(t * FPS))).save(out.replace(".png", f"_{i}.png"))
        return
    n = int(math.ceil(song * FPS)); P = 4; step = math.ceil(n / P)
    tmp = out + ".parts"; os.makedirs(tmp, exist_ok=True)
    jobs = [(k * step, min(n, (k + 1) * step), f"{tmp}/p{k}.mp4") for k in range(P)]
    with Pool(P) as pool: parts = pool.map(work, jobs)
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-i", audio,
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-t", f"{song:.3f}",
                           "-movflags", "+faststart", out])
    shutil.rmtree(tmp)

if __name__ == "__main__":
    main()
