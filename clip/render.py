"""Kinetic-typography renderer in the style of the reference clip.

Usage:
  python3 render.py AUDIO OUT.mp4            full render
  python3 render.py AUDIO OUT.png --at 12.3  single still (for checks)
"""
import json, math, random, re, subprocess, sys
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

# ---------------------------------------------------------------- drawing
def draw_card(card, t):
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
    zoom = 1.0 + 0.05 * life
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

class Background:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path); self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)); self.pos = -1
        rng = np.random.default_rng(3); self.grain = [cv2.resize(rng.normal(0, 5, (BH // 2, BW // 2)).astype(np.float32), (BW, BH))[..., None] for _ in range(6)]
    def frame(self, idx):
        idx %= self.n
        if idx != self.pos + 1: self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, f = self.cap.read(); self.pos = idx
        h, w = f.shape[:2]; cw = int(round(h * W / H)); x0 = (w - cw) // 2   # 9:16 cover crop of the 16:9 plate
        f = cv2.resize(f[:, x0:x0 + cw], (W, H), interpolation=cv2.INTER_CUBIC)
        return cv2.cvtColor(f, cv2.COLOR_BGR2RGB)

def render_frame(bg, cards, t, fi):
    band = bg.frame(fi)
    layer = None
    for c in cards:
        l = draw_card(c, t)
        if l is not None:
            if layer is None: layer = l
            else:  # overlap during handover: alpha-over
                a = l[..., 3:4] / 255.0
                layer = (layer * (1 - a) + l * a).astype(np.uint8)
    out = composite(band, layer) + bg.grain[fi % 6]
    return np.clip(out, 0, 255).astype(np.uint8)

def main():
    audio, out = sys.argv[1], sys.argv[2]
    song = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]))
    cards = build_cards(json.load(open("timing.json", encoding="utf-8")), song)
    json.dump([{"start": round(c["start"], 2), "end": round(c["end"], 2), "text": " ".join(clean_word(w["w"]) for w in c["words"])} for c in cards],
              open("cards.json", "w"), ensure_ascii=False, indent=1)
    bg = Background(BG)
    if "--at" in sys.argv:
        for i, t in enumerate(map(float, sys.argv[sys.argv.index("--at") + 1].split(","))):
            Image.fromarray(render_frame(bg, cards, t, int(t * FPS))).save(out.replace(".png", f"_{i}.png"))
        return
    n = int(math.ceil(song * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", audio, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-tune", "grain",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", f"{song:.3f}", out],
                         stdin=subprocess.PIPE)
    for fi in range(n):
        p.stdin.write(render_frame(bg, cards, fi / FPS, fi).tobytes())
        if fi % 900 == 0: print(f"{fi}/{n}", flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
