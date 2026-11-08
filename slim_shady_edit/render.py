"""Render the lyric edit.

usage:
  python render.py audio  <song.mp3>          -> build/audio.wav
  python render.py sheet  t1 t2 ...           -> build/sheet.png (preview frames)
  python render.py video  [fps]               -> build/eminem_slim_shady_lyric_edit.mp4
"""
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

from engine import H, W
from scenes import T_AUDIO_END, T_END, T_START, render

OUT = Path(__file__).parent / "build"
OUT.mkdir(exist_ok=True)
SR = 44100

_rng = np.random.default_rng(7)
GRAIN = [cv2.GaussianBlur(_rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8) * 0.022
         for _ in range(6)]


def build_audio(src):
    import librosa
    y, _ = librosa.load(src, sr=SR, mono=False)
    a = y[:, int(T_START * SR):int(T_AUDIO_END * SR)].copy()
    fi = int(0.015 * SR)
    a[:, :fi] *= np.linspace(0, 1, fi)
    fo = int(0.06 * SR)
    a[:, -fo:] *= np.linspace(1, 0, fo) ** 2
    # echo tail of the last word ("Shady") so the edit ends cleanly
    seg = y[:, int(39.66 * SR):int(T_AUDIO_END * SR)].copy()
    seg[:, -fo:] *= np.linspace(1, 0, fo) ** 2
    seg[:, :fi] *= np.linspace(0, 1, fi)
    total = int((T_END - T_START) * SR)
    out = np.zeros((2, total), np.float32)
    out[:, :a.shape[1]] = a
    delay = 0.29
    s0 = int((39.66 - T_START) * SR)
    lp = seg
    for k, g in enumerate((0.42, 0.26, 0.15, 0.08), 1):
        # darker each repeat (one-pole low-pass)
        lp = lp.copy()
        for ch in range(2):
            lp[ch] = np.asarray(
                __import__("scipy.signal", fromlist=["lfilter"]).lfilter([0.45], [1, -0.55], lp[ch]),
                np.float32)
        st = s0 + int(k * delay * SR)
        en = min(total, st + lp.shape[1])
        if st < total:
            out[:, st:en] += g * lp[:, :en - st]
    fade = int(0.35 * SR)
    out[:, -fade:] *= np.linspace(1, 0, fade)
    import soundfile as sf
    sf.write(OUT / "audio.wav", out.T, SR, subtype="PCM_24")
    print("audio", out.shape[1] / SR, "s")


def frame_at(args):
    i, fps = args
    t = T_START + i / fps
    # 2-sample motion blur (~180 degree shutter)
    img = 0.5 * (render(t) + render(t + 0.5 / fps))
    img = img + GRAIN[(i // 2) % len(GRAIN)][..., None]
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()


def video(fps=60):
    n = int(round((T_END - T_START) * fps))
    out = OUT / "eminem_slim_shady_lyric_edit.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-i", str(OUT / "audio.wav"),
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-c:a", "aac", "-b:a", "320k", "-ar", "44100",
           "-movflags", "+faststart", "-shortest", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for k, buf in enumerate(pool.imap(frame_at, [(i, fps) for i in range(n)], chunksize=4)):
            p.stdin.write(buf)
            if k % 120 == 0:
                print(f"{k}/{n}", flush=True)
    p.stdin.close()
    p.wait()
    print("wrote", out)


def sheet(times, cols=6):
    tiles = []
    for t in times:
        img = (np.clip(render(t), 0, 1) * 255).astype(np.uint8)
        img = cv2.resize(img, (270, 480), interpolation=cv2.INTER_AREA)
        cv2.putText(img, f"{t:.2f}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        tiles.append(img)
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(str(OUT / "sheet.png"), cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "audio":
        build_audio(sys.argv[2])
    elif cmd == "sheet":
        sheet([float(x) for x in sys.argv[2:]])
    elif cmd == "video":
        video(int(sys.argv[2]) if len(sys.argv) > 2 else 60)
