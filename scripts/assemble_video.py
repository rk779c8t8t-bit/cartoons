#!/usr/bin/env python3
"""Assemble the 9 scene clips + the audio mix into the final Short with FFmpeg.

  output/final_short.mp4  1080x1920, 30 fps, H.264 High (yuv420p), AAC 48 kHz stereo,
                          loudness-normalised to -14 LUFS / -1.5 dBTP (YouTube standard)
  output/preview.mp4      540x960 light preview

Scenes are joined with hard cuts on action (each scene is exactly 120 frames = 4 s),
so there are no black frames, no pauses and the music stays frame-accurate.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lbs3d.timeline import N_SCENES, DURATION, FPS  # noqa: E402


def ff(args):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    print("[ffmpeg]", " ".join(cmd[4:])[:200], flush=True)
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default=os.path.join(ROOT, "assets", "generated", "scenes"))
    ap.add_argument("--audio", default=os.path.join(ROOT, "assets", "audio", "mix.wav"))
    ap.add_argument("--out", default=os.path.join(ROOT, "output"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    clips = [os.path.join(a.clips, f"scene_{i:02d}.mp4") for i in range(1, N_SCENES + 1)]
    missing = [c for c in clips if not os.path.exists(c)]
    if missing:
        sys.exit(f"[assemble] missing scene clips: {missing}\n  -> run: python3 run.py --only render")
    if not os.path.exists(a.audio):
        sys.exit("[assemble] missing audio mix -> run: python3 scripts/create_audio.py")
    lst = os.path.join(a.out, "concat_list.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    final = os.path.join(a.out, "final_short.mp4")
    vf = (f"fps={FPS},scale=1080:1920:flags=lanczos,unsharp=5:5:0.55:5:5:0.0,"
          "eq=saturation=1.2:contrast=1.04:gamma=0.98,format=yuv420p")
    ff(["-f", "concat", "-safe", "0", "-i", lst, "-i", a.audio,
        "-filter_complex", f"[0:v]{vf}[v];[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{DURATION:.3f}",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "17", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", final])
    ff(["-i", final, "-vf", "scale=540:960:flags=lanczos", "-c:v", "libx264", "-crf", "26", "-preset", "medium",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", os.path.join(a.out, "preview.mp4")])
    os.remove(lst)
    print(f"[assemble] {final}")


if __name__ == "__main__":
    main()
