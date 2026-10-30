#!/usr/bin/env python3
"""Validate output/final_short.mp4: technical parameters + automatic visual/audio checks.

Writes logs/validation.json, docs/validation_report.md and output/contact_sheet.png
(3 frames per scene) for manual visual review. Exit code 1 if a hard check fails.

Only things that are actually measured are reported as checked.
"""
import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lbs3d.timeline import N_SCENES, SCENE_LEN, FPS, SCENES  # noqa: E402


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def probe(path):
    code, out, err = sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if code != 0:
        return None
    return json.loads(out)


def frame_at(path, t, w=270, h=480):
    buf = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    if len(buf) < w * h * 3:
        return None
    return np.frombuffer(buf[: w * h * 3], np.uint8).reshape(h, w, 3)


def validate(path):
    R = {"file": path, "checks": [], "info": {}}

    def check(name, ok, detail="", hard=True):
        R["checks"].append({"name": name, "ok": bool(ok), "detail": detail, "hard": hard})

    exists = os.path.exists(path)
    check("MP4 exists", exists, path)
    if not exists:
        return R
    size = os.path.getsize(path)
    check("file not empty", size > 100_000, f"{size / 1e6:.2f} MB")
    P = probe(path)
    check("ffprobe reads file", P is not None)
    if P is None:
        return R
    v = [s for s in P["streams"] if s["codec_type"] == "video"]
    a = [s for s in P["streams"] if s["codec_type"] == "audio"]
    check("video stream present", len(v) == 1)
    check("audio stream present", len(a) == 1)
    if not v or not a:
        return R
    v, a = v[0], a[0]
    W, H = int(v["width"]), int(v["height"])
    check("resolution 1080x1920", (W, H) == (1080, 1920), f"{W}x{H}")
    check("aspect 9:16", abs(W / H - 9 / 16) < 1e-3, f"{W / H:.4f}")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    fps = num / den
    check("FPS 30", abs(fps - 30) < 0.01, f"{fps:.3f}")
    dur = float(P["format"]["duration"])
    check("duration 30-40 s", 30 <= dur <= 40, f"{dur:.3f} s")
    check("video codec H.264", v["codec_name"] == "h264", f'{v["codec_name"]} {v.get("profile", "")} {v.get("pix_fmt", "")}')
    check("audio codec AAC", a["codec_name"] == "aac", f'{a["codec_name"]} {a.get("sample_rate")} Hz {a.get("channels")} ch')
    vd, ad = float(v.get("duration", dur)), float(a.get("duration", dur))
    check("audio/video durations match (sync)", abs(vd - ad) < 0.06, f"video {vd:.3f}s / audio {ad:.3f}s")
    nb = int(v.get("nb_frames", 0))
    check("frame count = 1080", nb == int(N_SCENES * SCENE_LEN * FPS), f"{nb} frames", hard=False)
    # black frames
    _, _, err = sh(["ffmpeg", "-hide_banner", "-i", path, "-vf", "blackdetect=d=0.03:pix_th=0.08", "-an", "-f", "null", "-"])
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)
    check("no black frames", not blacks, f"{len(blacks)} black segments")
    # frozen segments (long holds would look like a pause)
    _, _, err = sh(["ffmpeg", "-hide_banner", "-i", path, "-vf", "freezedetect=n=0.0008:d=0.8", "-an", "-f", "null", "-"])
    freezes = re.findall(r"freeze_start: ([\d.]+)", err)
    check("no frozen/paused segments >0.8 s", not freezes, f"{len(freezes)} found {freezes}", hard=False)
    # audio loudness / peak / silence
    _, _, err = sh(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"])
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    lufs = float(I[-1]) if I else None
    tp = float(TP[-1]) if TP else None
    check("loudness ~ -14 LUFS (YouTube)", lufs is not None and -16.5 <= lufs <= -12, f"{lufs} LUFS")
    check("no clipping (true peak <= -1 dBTP)", tp is not None and tp <= -0.9, f"{tp} dBTP")
    _, _, err = sh(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=n=-45dB:d=0.7", "-vn", "-f", "null", "-"])
    sil = re.findall(r"silence_start: ([\d.]+)", err)
    check("no silent gaps > 0.7 s", not sil, f"{sil}", hard=False)
    # scene boundaries: every 4 s there must be a cut (large frame difference) => 9 scenes present
    cuts = []
    for k in range(1, N_SCENES):
        t = k * SCENE_LEN
        f0, f1 = frame_at(path, t - 1.5 / FPS), frame_at(path, t + 0.5 / FPS)
        if f0 is not None and f1 is not None:
            cuts.append(float(np.mean(np.abs(f0.astype(int) - f1.astype(int)))))
    # inside-scene motion: consecutive frames should differ (something happens in every scene)
    motion = []
    for k in range(N_SCENES):
        diffs = []
        for t in np.linspace(0.3, SCENE_LEN - 0.3, 6):
            g0, g1 = frame_at(path, k * SCENE_LEN + t), frame_at(path, k * SCENE_LEN + t + 0.2)
            if g0 is not None and g1 is not None:
                diffs.append(float(np.mean(np.abs(g0.astype(int) - g1.astype(int)))))
        motion.append(round(float(np.mean(diffs)), 2) if diffs else 0)
    R["info"]["boundary_diffs"] = [round(c, 1) for c in cuts]
    R["info"]["motion_per_scene"] = motion
    check("all 9 scenes present (8 cuts detected at 4 s marks)", len(cuts) == 8 and all(c > 6 for c in cuts),
          f"diffs {[round(c, 1) for c in cuts]}", hard=False)
    check("visible action in every scene", all(m > 1.0 for m in motion), f"mean frame diff/0.2s {motion}")
    # flicker: luminance jumps between consecutive frames inside scenes
    lum = []
    for k in range(N_SCENES):
        for t in np.arange(0.2, SCENE_LEN - 0.1, 0.5):
            f = frame_at(path, k * SCENE_LEN + t, 64, 112)
            g = frame_at(path, k * SCENE_LEN + t + 1 / FPS, 64, 112)
            if f is not None and g is not None:
                lum.append(abs(float(f.mean()) - float(g.mean())))
    check("no flicker (adjacent-frame luminance jump < 12)", max(lum) < 12 if lum else False,
          f"max {max(lum):.2f}" if lum else "n/a", hard=False)
    # contact sheet
    sheet_path = os.path.join(ROOT, "output", "contact_sheet.png")
    tiles = []
    for k in range(N_SCENES):
        row = []
        for t in (0.4, 2.0, 3.6):
            f = frame_at(path, k * SCENE_LEN + t, 216, 384)
            row.append(f if f is not None else np.zeros((384, 216, 3), np.uint8))
        tiles.append(np.concatenate(row, axis=1))
    rows = [np.concatenate(tiles[i:i + 3], axis=1) for i in range(0, 9, 3)]
    Image.fromarray(np.concatenate(rows, axis=0)).save(sheet_path)
    R["info"]["contact_sheet"] = sheet_path
    return R


def write_report(R, md_path):
    lines = ["# Automatic validation report", "", f"File: `{os.path.relpath(R['file'], ROOT)}`", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    for c in R["checks"]:
        res = "PASS" if c["ok"] else ("FAIL" if c["hard"] else "WARN")
        lines.append(f"| {c['name']} | {res} | {c['detail']} |")
    lines += ["", f"Frame difference at the 8 scene boundaries: {R['info'].get('boundary_diffs')}",
              f"Mean motion per scene (frame diff over 0.2 s): {R['info'].get('motion_per_scene')}", "",
              "Contact sheet (3 frames per scene, 3 scenes per row): `output/contact_sheet.png`", "",
              "Visual criteria (character consistency, no extra limbs, no text/watermarks, story readability) "
              "are reviewed manually from the contact sheet and the video: see docs/quality_report.md."]
    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?", default=os.path.join(ROOT, "output", "final_short.mp4"))
    a = ap.parse_args()
    R = validate(a.video)
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", "validation.json"), "w") as f:
        json.dump(R, f, indent=2)
    write_report(R, os.path.join(ROOT, "docs", "validation_report.md"))
    hard_fail = False
    for c in R["checks"]:
        tag = "PASS" if c["ok"] else ("FAIL" if c["hard"] else "WARN")
        hard_fail |= (not c["ok"] and c["hard"])
        print(f"[{tag}] {c['name']:55s} {c['detail']}")
    print("contact sheet:", R["info"].get("contact_sheet"))
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()
