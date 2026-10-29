#!/usr/bin/env python3
"""Render all shots (frame sequences) with Blender/EEVEE.

Re-runnable: frames that already exist are skipped, so after a crash simply run again.
  python3 scripts/animate_scenes.py                 # all shots, final quality
  python3 scripts/animate_scenes.py --shots 3 5     # only some shots
  python3 scripts/animate_scenes.py --force-shot 4  # wipe & re-render shot 4
  python3 scripts/animate_scenes.py --preview       # 25% resolution, every 15th frame
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from common_cfg import load_config, shot_frames  # noqa: E402

BLENDER_SCRIPT = os.path.join(ROOT, "scripts", "blender", "render_shot.py")


def frames_dir(cfg, shot, preview=False):
    base = os.path.join(ROOT, cfg["paths"]["frames"] if not preview else cfg["paths"]["preview_frames"])
    return os.path.join(base, f"shot_{shot:02d}")


def shot_complete(cfg, shot, preview=False):
    d = frames_dir(cfg, shot, preview)
    n = shot_frames(cfg, shot)
    if not os.path.isdir(d):
        return False
    have = {f for f in os.listdir(d) if f.endswith(".png") and not f.endswith(".tmp.png")}
    need = {f"{i:04d}.png" for i in range(1, n + 1, 15 if preview else 1)}
    return need <= have


def render_chunk(cfg, shot, frames, preview, log_path):
    d = frames_dir(cfg, shot, preview)
    r = cfg["render"]
    cmd = ["blender", "-b", "--factory-startup", "-P", BLENDER_SCRIPT, "--",
           "--shot", str(shot), "--out", d,
           "--pct", str(25 if preview else r["resolution_percent"]),
           "--samples", str(4 if preview else r["samples"]),
           "--frames", ",".join(str(f) for f in frames)]
    with open(log_path, "a") as lf:
        lf.write(f"\n=== {time.ctime()} {' '.join(cmd[:8])} ... ({len(frames)} frames)\n")
        lf.flush()
        p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", type=int, nargs="*")
    ap.add_argument("--force-shot", type=int, nargs="*", default=[])
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    shots = a.shots or list(range(1, 10))
    workers = a.workers or cfg["render"]["workers"]
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    status_path = os.path.join(ROOT, "logs", "render_status.json")
    for s in a.force_shot:
        shutil.rmtree(frames_dir(cfg, s, a.preview), ignore_errors=True)
    if shutil.which("blender") is None:
        print("ERROR: blender not found (sudo apt-get install blender)")
        return 2
    jobs = []
    for s in shots:
        n = shot_frames(cfg, s)
        d = frames_dir(cfg, s, a.preview)
        os.makedirs(d, exist_ok=True)
        todo = [f for f in range(1, n + 1, 15 if a.preview else 1)
                if not os.path.exists(os.path.join(d, f"{f:04d}.png"))]
        if not todo:
            print(f"shot {s}: complete, reusing")
            continue
        # split shot into `workers` interleaved chunks so all processes stay busy
        k = max(1, min(workers, len(todo) // 8 or 1))
        for w in range(k):
            jobs.append((s, todo[w::k]))
        print(f"shot {s}: {len(todo)} frames to render in {k} chunk(s)")
    if a.dry_run or not jobs:
        print("dry-run: nothing rendered" if a.dry_run else "all shots complete")
        return 0
    t0 = time.time()
    log = os.path.join(ROOT, "logs", "render.log")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(render_chunk, cfg, s, fr, a.preview, log) for s, fr in jobs]
        rcs = [f.result() for f in futs]
    status = {f"shot_{s}": shot_complete(cfg, s, a.preview) for s in shots}
    with open(status_path, "w") as f:
        json.dump({"time": time.ctime(), "seconds": round(time.time() - t0), "complete": status, "return_codes": rcs}, f, indent=2)
    print(json.dumps(status))
    return 0 if all(status.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
