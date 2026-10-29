#!/usr/bin/env python3
"""Edit the rendered shots into the final vertical short and mix the audio.

- cuts / cross-dissolves according to config/project.yaml (dissolves use the rendered tail frames)
- audio: music + foley + ambience mixed in numpy, peak-limited to -1 dBFS
- output/final_short.mp4 : 1080x1920, 30 fps, H.264 High (yuv420p) + AAC 48 kHz stereo
- output/preview.mp4     : 540x960 light-weight preview
- output/contact_sheet.jpg : one frame per second for visual QA
"""
import argparse
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from common_cfg import load_config, shot_frames  # noqa: E402

MIX = {"music": 0.95, "foley": 0.85, "ambience": 0.75}


def frame_path(cfg, shot, f):
    return os.path.join(ROOT, cfg["paths"]["frames"], f"shot_{shot:02d}", f"{f:04d}.png")


def timeline(cfg):
    """List of (shot, local_frame, prev_shot, prev_frame, alpha) for every output frame."""
    out = []
    shots = cfg["shots"]
    for i, s in enumerate(shots):
        prev_tail = shots[i - 1].get("tail", 0) if i > 0 else 0
        for k in range(s["frames"]):
            if k < prev_tail:
                a = (k + 1) / (prev_tail + 1)
                out.append((s["id"], k + 1, shots[i - 1]["id"], shots[i - 1]["frames"] + k + 1, a))
            else:
                out.append((s["id"], k + 1, None, None, 1.0))
    return out


def check_frames(cfg):
    missing = []
    for s in cfg["shots"]:
        for f in range(1, shot_frames(cfg, s["id"]) + 1):
            p = frame_path(cfg, s["id"], f)
            if not os.path.exists(p):
                missing.append(p)
    return missing


def mix_audio(cfg, out_wav):
    adir = os.path.join(ROOT, cfg["paths"]["audio"])
    total = None
    sr = 44100
    for name, g in MIX.items():
        sr, x = wavfile.read(os.path.join(adir, name + ".wav"))
        x = x.astype(np.float32) / 32768.0
        total = x * g if total is None else total + x * g
    n = int(sr * cfg["video"]["duration_s"])
    total = total[:n]
    peak = np.max(np.abs(total))
    total *= 0.89 / peak  # -1 dBFS
    fade = int(0.01 * sr)
    total[:fade] *= np.linspace(0, 1, fade)[:, None]
    wavfile.write(out_wav, sr, (total * 32767).astype(np.int16))
    return out_wav


def encode(cfg, wav, out_mp4, scale=1.0, crf=17, preset="slow"):
    W, H, fps = cfg["video"]["width"], cfg["video"]["height"], cfg["video"]["fps"]
    w, h = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    tmp = out_mp4 + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
           "-i", wav,
           "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-t", str(cfg["video"]["duration_s"]), "-movflags", "+faststart", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sheet = []

    def load(shot, f):
        im = Image.open(frame_path(cfg, shot, f)).convert("RGB")
        if im.size != (w, h):
            im = im.resize((w, h), Image.LANCZOS)
        return np.asarray(im, dtype=np.float32)

    for i, (shot, f, ps, pf, a) in enumerate(timeline(cfg)):
        cur = load(shot, f)
        if ps is not None:
            prev = load(ps, pf)
            # smoothstep dissolve
            s = a * a * (3 - 2 * a)
            cur = prev * (1 - s) + cur * s
        fr = np.clip(cur + 0.5, 0, 255).astype(np.uint8)
        p.stdin.write(fr.tobytes())
        if scale == 1.0 and i % fps == fps // 2:
            sheet.append(Image.fromarray(fr).resize((216, 384)))
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    os.replace(tmp, out_mp4)
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-preview", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found")
        return 2
    missing = check_frames(cfg)
    if missing:
        print(f"ERROR: {len(missing)} rendered frames missing, e.g. {missing[0]} - run scripts/animate_scenes.py")
        return 1
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    wav = os.path.join(ROOT, "output", "mix.wav")
    mix_audio(cfg, wav)
    final = os.path.join(ROOT, cfg["paths"]["final"])
    sheet = encode(cfg, wav, final)
    print("wrote", final)
    if sheet:
        cols = 6
        rows = (len(sheet) + cols - 1) // cols
        cs = Image.new("RGB", (216 * cols, 384 * rows))
        for i, im in enumerate(sheet):
            cs.paste(im, ((i % cols) * 216, (i // cols) * 384))
        cs.save(os.path.join(ROOT, "output", "contact_sheet.jpg"), quality=88)
    if not a.no_preview:
        prev = os.path.join(ROOT, cfg["paths"]["preview"])
        encode(cfg, wav, prev, scale=0.5, crf=23, preset="medium")
        print("wrote", prev)
    return 0


if __name__ == "__main__":
    sys.exit(main())
