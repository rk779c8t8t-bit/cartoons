"""Анализ аудио + выравнивание текста песни по вокалу -> build/data.js

Использование:
  python3 prepare.py song.mp3 asr.json [lyrics.txt]

asr.json  — пословные тайминги из faster-whisper (transcribe.py).
lyrics.txt — настоящий текст песни (одна строка = одна фраза на экране).
Если lyrics.txt не задан, используется распознанный текст (только для черновика).
"""
import json, re, sys, difflib
import numpy as np
import librosa

FPS = 30
song, asr_path = sys.argv[1], sys.argv[2]
lyrics_path = sys.argv[3] if len(sys.argv) > 3 else None

# ---------- аудио ----------
y, sr = librosa.load(song, sr=22050, mono=True)
dur = len(y) / sr
hop = 512
S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
f = librosa.fft_frequencies(sr=sr)
ft = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

def band(lo, hi):
    v = S[(f >= lo) & (f < hi)].mean(0)
    v = np.log1p(v * 10)
    return v / (np.percentile(v, 99) + 1e-9)

bands = {"low": band(20, 150), "mid": band(300, 3000), "high": band(5000, 11000)}
rms = librosa.feature.rms(y=y, hop_length=hop)[0]
bands["rms"] = rms / (np.percentile(rms, 99) + 1e-9)

n = int(np.ceil(dur * FPS))
tt = np.arange(n) / FPS
env = {}
for k, v in bands.items():
    v = np.interp(tt, ft, v)
    # быстрая атака, медленный спад
    o = np.zeros_like(v)
    a = 0.0
    for i, x in enumerate(v):
        a = x if x > a else a * 0.86 + x * 0.14
        o[i] = a
    env[k] = np.clip(o, 0, 1.2).round(3).tolist()

tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
beats = librosa.frames_to_time(beats, sr=sr).round(3).tolist()
# удары бочки: онсеты в низах с сильной амплитудой
lo_db = librosa.amplitude_to_db(S[f < 150])
oenv = librosa.onset.onset_strength(S=lo_db, sr=sr)
kf = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, units="frames")
thr = np.percentile(oenv[kf], 45)
kicks = librosa.frames_to_time([k for k in kf if oenv[k] > thr], sr=sr).round(3).tolist()

# ---------- текст ----------
asr_all = [json.load(open(p)) for p in asr_path.split(",")]
asr = asr_all[0]
aw = [w for s in asr for w in s["words"]]

def norm(s):
    return re.sub(r"[^a-zа-яё0-9]", "", s.lower().replace("ё", "е"))

def align(flat, aw):
    a_chars, a_time = [], []
    for w in aw:
        c = norm(w["w"])
        for i, ch in enumerate(c):
            a_chars.append(ch)
            a_time.append(w["s"] + (w["e"] - w["s"]) * i / max(1, len(c)))
    l_chars, l_owner = [], []
    for k, w in enumerate(flat):
        for ch in norm(w):
            l_chars.append(ch)
            l_owner.append(k)
    sm = difflib.SequenceMatcher(None, "".join(l_chars), "".join(a_chars), autojunk=False)
    times = [[] for _ in flat]
    for b in sm.get_matching_blocks():
        for j in range(b.size):
            times[l_owner[b.a + j]].append(a_time[b.b + j])
    # слово считаем найденным, если совпала хотя бы половина букв
    return [min(t) if t and len(t) >= max(1, (len(norm(flat[i])) + 1) // 2) else None for i, t in enumerate(times)]

if lyrics_path:
    lines, sections = [], []
    for l in open(lyrics_path, encoding="utf-8"):
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        m = re.match(r"^\[([^|\]]+)\|?([^\]]*)\]$", l)
        if m:
            sections.append({"line": len(lines), "type": m.group(1).strip(), "artist": m.group(2).strip()})
            continue
        # бэк-вокал в скобках отделяем от основной партии
        main, adl, depth, buf = [], [], 0, ""
        for tok in re.findall(r"\(|\)|[^\s()]+", l):
            if tok == "(":
                depth += 1; buf = ""; continue
            if tok == ")":
                depth -= 1; adl.append({"w": buf.strip(), "after": len(main) - 1}); continue
            if depth:
                buf += " " + tok
            elif re.search(r"[\w]", tok):
                main.append(tok)
            elif main:
                main[-1] += tok  # тире/многоточие приклеиваем к слову
        lines.append({"main": main, "adlibs": adl})
    flat = [w for L in lines for w in L["main"]]
    passes = [align(flat, [w for seg in A for w in seg["words"]]) for A in asr_all]
    st = []
    for i in range(len(flat)):
        c = [p[i] for p in passes if p[i] is not None]
        if not c:
            st.append(None)
        elif len(c) == 1 or max(c) - min(c) < 0.6:
            st.append(min(c))  # лучше на долю секунды раньше, чем позже
        else:
            # конфликт: берём вариант, согласованный с соседями
            prev = next((x for x in reversed(st) if x is not None), 0)
            ok = [x for x in c if x >= prev]
            st.append(min(ok) if ok else max(c))
    known = [i for i, v in enumerate(st) if v is not None]
    for i in range(len(st)):
        if st[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            if prev is None:
                st[i] = st[nxt] - 0.25 * (nxt - i)
            elif nxt is None:
                st[i] = st[prev] + 0.3 * (i - prev)
            else:
                st[i] = st[prev] + (st[nxt] - st[prev]) * (i - prev) / (nxt - prev)
    for i in range(1, len(st)):
        st[i] = max(st[i], st[i - 1] + 0.06)
    # ручные правки таймингов там, где распознавание не услышало слова
    import os
    fx = json.load(open("timing_fixes.json")) if os.path.exists("timing_fixes.json") else []
    k = 0; seen = {}
    for L in lines:
        txt = " ".join(L["main"]); occ = seen.get(txt, 0); seen[txt] = occ + 1
        for f in fx:
            if f["line"].replace(" ", "") == txt.replace(" ", "") and f["occ"] == occ:
                for j, tv in enumerate(f["times"][:len(L["main"])]):
                    st[k + j] = tv
        k += len(L["main"])
    out_lines, k = [], 0
    for L in lines:
        words = []
        for w in L["main"]:
            words.append({"w": w, "s": round(st[k], 3)}); k += 1
        out_lines.append({"words": words, "adlibs": L["adlibs"]})
else:
    sections = []
    out_lines = [{"words": [{"w": w["w"].strip(), "s": round(w["s"], 3)} for w in s["words"]], "adlibs": []}
                 for s in asr]

# конец каждой строки: начало следующей (но не дольше 2.2с после последнего слова)
for i, l in enumerate(out_lines):
    nxt = out_lines[i + 1]["words"][0]["s"] if i + 1 < len(out_lines) else dur - 3.5
    last = l["words"][-1]["s"]
    l["s"] = l["words"][0]["s"]
    l["e"] = round(min(nxt - 0.05, last + 2.2), 3)
    for j, w in enumerate(l["words"]):
        w["e"] = l["words"][j + 1]["s"] if j + 1 < len(l["words"]) else round(min(l["e"], w["s"] + 0.6), 3)
    for ad in l["adlibs"]:
        base = l["words"][ad["after"]] if ad["after"] >= 0 else l["words"][0]
        ad["s"] = round(min(base["s"] + 0.45, l["e"] - 0.3), 3) if ad["after"] < len(l["words"]) - 1 else round(min(last + 0.55, l["e"] - 0.25), 3)

data = {"fps": FPS, "dur": round(dur, 3), "tempo": float(np.atleast_1d(tempo)[0]),
        "beats": beats, "kicks": kicks, "env": env, "lines": out_lines,
        "sections": [dict(sec, s=out_lines[sec["line"]]["words"][0]["s"]) for sec in sections]}
open("build/data.js", "w").write("window.DATA=" + json.dumps(data, ensure_ascii=False) + ";")
print(f"dur={dur:.2f}s frames={n} tempo={data['tempo']:.1f} beats={len(beats)} kicks={len(kicks)} lines={len(out_lines)}")
