"""Align lyric screens and words to the vocals, without a speech model.

1. Pull a rough vocal stem out of the mix (REPET-SIM + harmonic/percussive split).
2. Find pauses in the vocal energy -> candidate line boundaries.
3. Per section, pick boundaries with dynamic programming: durations should
   follow syllable counts, and boundaries should sit in real pauses.
4. Snap each word to the nearest vocal onset.

usage: python align.py song.mp3   -> writes timeline.json
"""
import json, os, sys

import librosa
import numpy as np
from scipy.ndimage import uniform_filter1d, minimum_filter1d

from lyrics import SECTIONS, CHORUS
import render as R

HERE = os.path.dirname(os.path.abspath(__file__))
SR, HOP = 22050, 512
FPS = SR / HOP

# Hand-checked anchors (seconds) from the vocal energy plot.
ANCHORS = [
    # (section name, start, end)
    ("title", 0.0, 3.95),
    ("p1", 3.95, 58.0),          # chorus 1 + verse 1
    ("drop", 58.0, 60.25),        # "Династия!" + break
    ("chorus2_head", 60.25, 61.6),  # "Первый миллион" (held note)
    ("p2", 61.6, 120.55),         # chorus 2 lines + verse 2
    ("chorus3_head", 120.55, 121.9),
    ("p3", 121.9, 148.6),         # chorus 3 lines
    ("outro", 148.6, 150.47),
]


def vocal_stem(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    S, ph = librosa.magphase(librosa.stft(y, n_fft=2048, hop_length=HOP))
    F = librosa.decompose.nn_filter(S, aggregate=np.median, metric="cosine",
                                    width=int(librosa.time_to_frames(2, sr=SR)))
    F = np.minimum(S, F)
    V = librosa.util.softmask(S - F, 10 * F, power=2) * S
    Hm, _ = librosa.decompose.hpss(V, margin=(1.0, 3.0))
    f = librosa.fft_frequencies(sr=SR, n_fft=2048)
    band = (f > 250) & (f < 4000)
    env = np.log10((Hm[band] ** 2).sum(0) + 1e-6)
    v = librosa.istft(Hm * ph, hop_length=HOP)
    on = librosa.onset.onset_detect(y=v, sr=SR, hop_length=HOP, units="time", backtrack=True)
    return env, on


def local_norm(env):
    w = int(3 * FPS)
    lo = minimum_filter1d(env, w)
    hi = -minimum_filter1d(-env, w)
    return np.clip((env - lo) / (hi - lo + 1e-6), 0, 1)


def gap_candidates(n, a, b):
    """Vocal pauses in [a,b]: (time where singing resumes, depth 0..1)."""
    s = uniform_filter1d(n, 5)
    out = []
    i0, i1 = int(a * FPS), int(b * FPS)
    i = i0
    while i < i1:
        if s[i] < 0.42:
            j = i
            while j < i1 and s[j] < 0.42:
                j += 1
            seg = s[i:j]
            depth = 1 - seg.min()
            length = (j - i) / FPS
            out.append((j / FPS - 0.02, min(1, depth * (0.5 + length * 4))))
            i = j
        i += 1
    return out


def dp_boundaries(units, a, b, cands):
    """Choose len(units)-1 boundaries among cands (or free points)."""
    k = len(units)
    w = np.array([u + 1.5 for u in units], float)
    rate = (b - a) / w.sum()
    pts = [(a, 1.0)] + [c for c in cands if a + 0.4 < c[0] < b - 0.4] + [(b, 1.0)]
    times = np.array([p[0] for p in pts])
    depth = np.array([p[1] for p in pts])
    m = len(pts)
    INF = 1e18
    cost = np.full((k + 1, m), INF)
    back = np.zeros((k + 1, m), int)
    cost[0, 0] = 0
    for u in range(1, k + 1):
        exp = w[u - 1] * rate
        for j in range(1, m):
            if u < k and j == m - 1:
                continue
            if u == k and j != m - 1:
                continue
            d = times[j] - times[:j]
            c = cost[u - 1, :j] + ((d - exp) / (0.45 * exp + 0.35)) ** 2 + 2.2 * (1 - depth[j]) * (u < k)
            c[d < 0.45] = INF
            bi = int(np.argmin(c))
            cost[u, j], back[u, j] = c[bi], bi
    seq, j = [], m - 1
    for u in range(k, 0, -1):
        seq.append(times[j]); j = back[u, j]
    seq.append(times[j])
    return seq[::-1]


def units_for(lines):
    out = []
    for line in lines:
        for p in line.split("||"):
            p = p.strip()
            out.append((p, sum(t["syl"] for t in R.parse_tokens(p))))
    return out


STEP = 1.549  # one half-line (2 beats at ~155 BPM); measured from the chorus repeat
PLAN = [
    # (name, start, half-steps per unit or "fit", total half-steps)
    ("title", 0.0, None, None),
    ("chorus1", 3.95, 2, 8),
    ("verse1", 3.95 + 8 * STEP, "fit", 27),
    ("drop", None, None, None),
    ("chorus_head", None, None, None),
    ("chorus2", 61.75, 2, 16),
    ("verse2", 61.75 + 16 * STEP, "fit", 23),
    ("chorus_head", None, None, None),
    ("chorus3", 61.75 + 61.95, 2, 16),
    ("outro", None, None, None),
]


def dip(n, t):
    """How much the vocal energy dips right before t (0..1)."""
    i = int(t * FPS)
    s = uniform_filter1d(n, 4)
    return float(1 - s[max(0, i - 7):i + 3].min())


def fit_steps(lines, total, t0, n):
    """Give each line 1..3 half-steps (sum = total), matching syllables and pauses."""
    syl = [sum(t["syl"] for t in R.parse_tokens(l.replace("||", ""))) for l in lines]
    rate = sum(syl) / total
    k = len(lines)
    best = {(0, 0): (0.0, [])}
    for i in range(k):
        nxt = {}
        for (li, used), (c, path) in best.items():
            for st in (1, 2, 3):
                u = used + st
                if u > total:
                    continue
                cc = c + ((syl[i] - rate * st) / (rate * 0.6)) ** 2
                if i < k - 1:
                    cc += 1.5 * (1 - dip(n, t0 + u * STEP))
                key = (i + 1, u)
                if key not in nxt or nxt[key][0] > cc:
                    nxt[key] = (cc, path + [st])
        best = nxt
    return best[(k, total)][1]


def split_parts(line, a, b, n):
    parts = [p.strip() for p in line.split("||")]
    if len(parts) == 1:
        return [(parts[0], a, b)]
    w = [sum(t["syl"] for t in R.parse_tokens(p)) for p in parts]
    m = a + (b - a) * w[0] / sum(w)
    # nudge the split into a nearby vocal pause
    cands = np.arange(m - 0.3, m + 0.3, 0.02)
    m = float(cands[np.argmax([dip(n, c) for c in cands])])
    return [(parts[0], a, m), (parts[1], m, b)]


def main():
    song = sys.argv[1]
    env, onsets = vocal_stem(song)
    n = local_norm(env)
    sec = {s[0]: s[4] for s in SECTIONS}
    units = []  # (text, start, end, section)
    c1_lines, c2_lines = sec["chorus1"], CHORUS[1:]
    units.append(("*ДИНАСТИЯ*", 0.0, 3.95, "title"))
    t = 3.95
    for l in c1_lines:
        units += [(p, a, b, "chorus") for p, a, b in split_parts(l, t, t + 2 * STEP, n)]
        t += 2 * STEP
    steps = fit_steps(sec["verse1"], 27, t, n)
    for l, st in zip(sec["verse1"], steps):
        units += [(p, a, b, "verse1") for p, a, b in split_parts(l, t, t + st * STEP, n)]
        t += st * STEP
    c2 = 61.75
    units.append(("*ДИНАСТИЯ!*", t, c2 - 2 * STEP + 1.6, "drop"))
    units.append((CHORUS[0], c2 - 2 * STEP + 1.6, c2, "chorus"))

    def chorus_at(t):
        for l in c2_lines:
            yield from ((p, a, b, "chorus") for p, a, b in split_parts(l, t, t + 2 * STEP, n))
            t += 2 * STEP
    units += list(chorus_at(c2))
    t = c2 + 16 * STEP
    steps = fit_steps(sec["verse2"], 23, t, n)
    for l, st in zip(sec["verse2"], steps):
        units += [(p, a, b, "verse2") for p, a, b in split_parts(l, t, t + st * STEP, n)]
        t += st * STEP
    c3 = c2 + 61.95
    units.append((CHORUS[0], t, c3, "chorus"))
    units += list(chorus_at(c3))
    end = c3 + 16 * STEP
    units.append(("tainiy-tainiy", end, end + 0.9, "outro"))
    units.append(("*DEXEY!*", end + 0.9, 150.47, "outro"))

    screens, pal_i = [], 0
    for text, a, b, section in units:
        special = section in ("title", "drop") or "DEXEY" in text
        if special:
            pal = {"title": 4, "drop": 5}.get(section, 2)
        else:
            pal = pal_i % len(R.PALETTES); pal_i += 1
        screens.append({"start": round(a, 3), "end": round(b, 3), "text": text,
                        "section": section, "pal": pal, "special": special})
    # word timings snapped to vocal onsets
    on = np.array(onsets)
    for sc in screens:
        toks = R.parse_tokens(sc["text"])
        a, b = sc["start"], sc["end"]
        syl = np.array([t["syl"] for t in toks], float)
        span = min((b - a) * 0.85, 0.17 * syl.sum() + 0.1)
        est = a + span * np.concatenate([[0], np.cumsum(syl)[:-1]]) / syl.sum()
        times, last = [], a
        for k, t0 in enumerate(est):
            if k == 0:
                tt = a
            else:
                cand = on[(on > last + 0.08) & (on < b - 0.15) & (np.abs(on - t0) < 0.18)]
                tt = float(cand[np.abs(cand - t0).argmin()]) if len(cand) else max(t0, last + 0.08)
            times.append(round(tt, 3)); last = tt
        sc["word_times"] = times
    json.dump(screens, open(os.path.join(HERE, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    for s in screens:
        print(f'{s["start"]:7.2f} {s["end"]:7.2f}  {s["text"]}')


CH_TEXT = set(p.strip() for l in CHORUS for p in l.split("||"))


def _in_chorus(text):
    return text in CH_TEXT


if __name__ == "__main__":
    main()
