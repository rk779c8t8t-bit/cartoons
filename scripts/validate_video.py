#!/usr/bin/env python3
"""Technical validation of output/final_short.mp4. Exit code 0 = all mandatory checks passed.
Writes logs/validation.json and output/validation.md.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from common_cfg import load_config, shot_starts  # noqa: E402


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def grab(path, t, w=270, h=480):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-s", f"{w}x{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(out) != w * h * 3:
        return None
    return np.frombuffer(out, np.uint8).reshape(h, w, 3).astype(np.float32)


def main():
    cfg = load_config()
    V = cfg["video"]
    path = os.path.join(ROOT, cfg["paths"]["final"])
    R = []

    def check(name, ok, detail="", mandatory=True):
        R.append({"check": name, "ok": bool(ok), "detail": str(detail), "mandatory": mandatory})
        print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))

    exists = os.path.exists(path)
    check("file exists", exists, path)
    if not exists:
        return finish(R)
    check("file size > 0", os.path.getsize(path) > 0, f"{os.path.getsize(path) / 1e6:.2f} MB")
    pr = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path])
    check("ffprobe can read metadata", pr.returncode == 0, pr.stderr.strip()[:200])
    if pr.returncode != 0:
        return finish(R)
    info = json.loads(pr.stdout)
    vs = [s for s in info["streams"] if s["codec_type"] == "video"]
    as_ = [s for s in info["streams"] if s["codec_type"] == "audio"]
    check("video stream present", len(vs) == 1)
    check("audio stream present", len(as_) == 1)
    v = vs[0]
    a = as_[0] if as_ else {}
    check("resolution 1080x1920 (9:16)", (v["width"], v["height"]) == (V["width"], V["height"]), f'{v["width"]}x{v["height"]}')
    num, den = map(int, v["r_frame_rate"].split("/"))
    fps = num / den
    check("frame rate 30 fps", abs(fps - V["fps"]) < 0.01, f"{fps:.3f}")
    dur = float(info["format"]["duration"])
    check("duration within 30–40 s", V["min_duration_s"] <= dur <= V["max_duration_s"], f"{dur:.3f} s")
    check("container MP4", "mp4" in info["format"]["format_name"], info["format"]["format_name"])
    check("video codec H.264", v["codec_name"] == "h264", f'{v["codec_name"]} {v.get("profile", "")} {v.get("pix_fmt", "")}')
    check("pixel format yuv420p", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt"))
    check("audio codec AAC", a.get("codec_name") == "aac", f'{a.get("codec_name")} {a.get("sample_rate")} Hz {a.get("channels")} ch')
    vd = float(v.get("duration", dur))
    ad = float(a.get("duration", 0))
    check("audio does not end before video", ad >= vd - 0.05, f"video {vd:.3f} s, audio {ad:.3f} s")
    nf = int(v.get("nb_frames", 0))
    check("frame count", abs(nf - round(V["duration_s"] * V["fps"])) <= 1, f"{nf} frames")
    # decode whole file, look for errors
    dec = run(["ffmpeg", "-v", "error", "-i", path, "-f", "null", "-"])
    check("full decode without errors", dec.returncode == 0 and not dec.stderr.strip(), dec.stderr.strip()[:200])
    # black frames / silence
    bd = run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "blackdetect=d=0.1:pix_th=0.08", "-an", "-f", "null", "-"])
    blacks = [l for l in bd.stderr.splitlines() if "black_start" in l]
    check("no black frames (start/end/inside)", not blacks, "; ".join(blacks)[:200])
    sd = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=n=-55dB:d=0.7", "-vn", "-f", "null", "-"])
    sil = [l for l in sd.stderr.splitlines() if "silence_start" in l]
    check("no audio dropouts (silence > 0.7 s)", not sil, "; ".join(sil)[:200])
    vol = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-vn", "-f", "null", "-"])
    mx = [l.split(":")[-1].strip() for l in vol.stderr.splitlines() if "max_volume" in l]
    mean = [l.split(":")[-1].strip() for l in vol.stderr.splitlines() if "mean_volume" in l]
    try:
        mxv = float(mx[0].split()[0])
    except Exception:
        mxv = 0.0
    check("no clipping (peak < 0 dBFS)", mxv < -0.1, f"max {mx[0] if mx else '?'}, mean {mean[0] if mean else '?'}")
    # every shot present, in order, not empty: compare video frame at each shot's middle with its source render
    starts, _ = shot_starts(cfg)
    order_ok, empty = True, []
    details = []
    for i, s in enumerate(cfg["shots"]):
        mid_local = 60
        t = (starts[i] + mid_local - 1 + 0.5) / V["fps"]
        fr = grab(path, t)
        src = os.path.join(ROOT, cfg["paths"]["frames"], f"shot_{s['id']:02d}", f"{mid_local:04d}.png")
        if fr is None or not os.path.exists(src):
            order_ok = False
            details.append(f"shot {s['id']}: missing")
            continue
        ref = np.asarray(Image.open(src).convert("RGB").resize((270, 480)), np.float32)
        own = float(np.mean(np.abs(fr - ref)))
        others = []
        for j, s2 in enumerate(cfg["shots"]):
            if j == i:
                continue
            p2 = os.path.join(ROOT, cfg["paths"]["frames"], f"shot_{s2['id']:02d}", f"{mid_local:04d}.png")
            if os.path.exists(p2):
                others.append(float(np.mean(np.abs(fr - np.asarray(Image.open(p2).convert("RGB").resize((270, 480)), np.float32)))))
        best_other = min(others) if others else 999
        ok = own < 0.6 * best_other  # must match its own render far better than any other shot
        order_ok &= ok
        if fr.std() < 8:
            empty.append(s["id"])
        details.append(f"shot {s['id']}: diff {own:.1f} vs nearest other {best_other:.1f}")
    check("all 9 shots present in the right order", order_ok, "; ".join(details))
    check("no empty/flat shots", not empty, f"flat: {empty}" if empty else "")
    return finish(R)


def finish(R):
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", "validation.json"), "w") as f:
        json.dump(R, f, indent=2, ensure_ascii=False)
    lines = ["# Автоматическая проверка final_short.mp4", "", "| Проверка | Результат | Детали |", "|---|---|---|"]
    for r in R:
        lines.append(f"| {r['check']} | {'✅' if r['ok'] else '❌'} | {r['detail'].replace('|', '/')} |")
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    with open(os.path.join(ROOT, "output", "validation.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    bad = [r for r in R if r["mandatory"] and not r["ok"]]
    print(f"\n{len(R) - len(bad)}/{len(R)} checks passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
