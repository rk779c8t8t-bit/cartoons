#!/usr/bin/env python3
"""One-command pipeline for «Над котёнком все смеялись».

  python3 run.py                    # full run, reuses everything that is already done
  python3 run.py --dry-run          # checks + plan only, renders nothing (no paid services are used anyway)
  python3 run.py --force-shot 4 6   # re-render only these shots, then re-edit
  python3 run.py --force-all        # re-render everything (frames, audio, references)
  python3 run.py --preview          # quick low-res render of every 15th frame (no final video)
Exit code != 0 if a mandatory stage fails or the final file does not pass validation.
"""
import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(ROOT, "scripts")


def stage(name, cmd):
    print(f"\n==> [{time.strftime('%H:%M:%S')}] {name}: {' '.join(cmd[1:])}", flush=True)
    t = time.time()
    r = subprocess.run(cmd, cwd=ROOT)
    print(f"<== {name}: {'OK' if r.returncode == 0 else 'FAILED (%d)' % r.returncode} in {time.time() - t:.0f}s", flush=True)
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force-shot", type=int, nargs="*", default=[])
    ap.add_argument("--force-all", action="store_true")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    py = sys.executable
    for d in ("logs", "output", "assets/references", "assets/audio", "assets/generated/frames"):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    if not os.path.exists(os.path.join(ROOT, "config", "project.yaml")):
        print("config/project.yaml missing")
        return 2
    if stage("audit", [py, os.path.join(S, "audit_environment.py")]) != 0:
        return 2
    if a.dry_run:
        rc = stage("render plan (dry-run)", [py, os.path.join(S, "animate_scenes.py"), "--dry-run"])
        print("\nDry run finished: nothing was rendered, no network or paid services were used.")
        return rc
    force = ["--force"] if a.force_all else []
    if stage("character references", [py, os.path.join(S, "generate_assets.py")] + force) != 0:
        return 3
    if stage("audio", [py, os.path.join(S, "create_audio.py")] + force) != 0:
        return 4
    anim = [py, os.path.join(S, "animate_scenes.py")]
    if a.preview:
        anim.append("--preview")
    if a.force_all:
        anim += ["--force-shot"] + [str(i) for i in range(1, 10)]
    elif a.force_shot:
        anim += ["--force-shot"] + [str(i) for i in a.force_shot]
    if a.workers:
        anim += ["--workers", str(a.workers)]
    if stage("render shots", anim) != 0:
        return 5
    if a.preview:
        print("Preview frames are in output/preview_frames/")
        return 0
    if stage("edit + mix", [py, os.path.join(S, "assemble_video.py")]) != 0:
        return 6
    if stage("validate", [py, os.path.join(S, "validate_video.py")]) != 0:
        return 7
    print("\nDONE ->", os.path.join(ROOT, "output", "final_short.mp4"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
