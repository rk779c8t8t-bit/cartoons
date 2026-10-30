#!/usr/bin/env python3
"""Render the 9 scenes as real 3D animation with Blender (bpy, Cycles CPU).

Examples
  python3 scripts/animate_scenes.py --scenes all
  python3 scripts/animate_scenes.py --scenes 3 --force          # re-render one scene
  python3 scripts/animate_scenes.py --scenes 1,2 --width 540 --height 960 --samples 8
  python3 scripts/animate_scenes.py --keyframes 0.5,2,3.5 --width 270 --height 480   # storyboard stills

Frames: assets/generated/frames/scene_NN/f_XXXX.png (existing frames are skipped => resumable)
Clips:  assets/generated/scenes/scene_NN.mp4
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from lbs3d.timeline import FPS, SCENE_LEN, N_SCENES  # noqa: E402


def parse_scenes(s):
    if s == "all":
        return list(range(1, N_SCENES + 1))
    return [int(x) for x in s.split(",") if x.strip()]


def encode_clip(scene, frames_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"scene_{scene:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(frames_dir, "f_%04d.png"),
           "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", default="all")
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=1280)
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--force", action="store_true", help="re-render frames that already exist")
    ap.add_argument("--frames", default=None, help="frame range inside scene, e.g. 0-59")
    ap.add_argument("--step", type=int, default=1, help="render every Nth frame (draft)")
    ap.add_argument("--keyframes", default=None, help="comma list of times (s) to render as stills")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "generated"))
    ap.add_argument("--no-encode", action="store_true")
    a = ap.parse_args()

    import bpy  # noqa: F401  (heavy import only when actually rendering)
    from lbs3d.scenes import Production
    from lbs3d import world

    prod = Production()
    world.render_settings(a.width, a.height, a.samples)
    sc = bpy.context.scene
    n_frames = int(SCENE_LEN * FPS)

    for scene in parse_scenes(a.scenes):
        if a.keyframes:
            d = os.path.join(a.out, "keyframes")
            os.makedirs(d, exist_ok=True)
            for ts in a.keyframes.split(","):
                t = float(ts)
                prod.frame(scene, t)
                sc.render.filepath = os.path.join(d, f"s{scene:02d}_t{t:04.2f}.png")
                bpy.ops.render.render(write_still=True)
                print(f"[keyframe] scene {scene} t={t}", flush=True)
            continue
        fdir = os.path.join(a.out, "frames", f"scene_{scene:02d}")
        os.makedirs(fdir, exist_ok=True)
        lo, hi = 0, n_frames - 1
        if a.frames:
            lo, hi = (int(x) for x in a.frames.split("-"))
        t0 = time.time()
        done = 0
        for f in range(lo, hi + 1, a.step):
            path = os.path.join(fdir, f"f_{f:04d}.png")
            if os.path.exists(path) and not a.force:
                continue
            prod.frame(scene, f / FPS)
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            done += 1
            el = time.time() - t0
            print(f"[scene {scene}] frame {f + 1}/{n_frames}  {el / done:.1f}s/frame", flush=True)
        complete = all(os.path.exists(os.path.join(fdir, f"f_{f:04d}.png")) for f in range(n_frames))
        if complete and not a.no_encode:
            clip = encode_clip(scene, fdir, os.path.join(a.out, "scenes"))
            print(f"[scene {scene}] clip -> {clip}", flush=True)


if __name__ == "__main__":
    main()
