#!/usr/bin/env python3
"""Little Big Stories — "The Kitten Who Opened a Restaurant": one-command production pipeline.

  python3 run.py                     # full pipeline, resumes where it stopped
  python3 run.py --dry-run           # audit + plan only: no rendering, no paid requests
  python3 run.py --scene 4           # re-render ONLY scene 4 (others untouched), re-assemble, validate
  python3 run.py --scene 4,7 --draft # quick low-res re-render of scenes 4 and 7 (look check)
  python3 run.py --only audio        # run one step: audit|deps|refs|render|audio|assemble|validate|report
  python3 run.py --force             # re-render everything from scratch

Steps: audit -> deps -> refs -> render -> audio -> assemble -> validate -> report
All results are saved on disk; finished frames are skipped, so a crashed run can simply be restarted.
"""
import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
LOG = os.path.join(ROOT, "logs", "run.log")
STATE = os.path.join(ROOT, "logs", "run_state.json")
STEPS = ["audit", "deps", "refs", "render", "audio", "assemble", "validate", "report"]

FINAL = dict(width=540, height=960, samples=8)      # rendered, then Lanczos-upscaled to 1080x1920
DRAFT = dict(width=270, height=480, samples=4)


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def save_state(st):
    with open(STATE, "w") as f:
        json.dump(st, f, indent=2)


def sh(args, step):
    log(f"$ {' '.join(args)}")
    with open(LOG, "a") as f:
        p = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            f.write(line)
            if line.startswith(("[", "PASS", "FAIL")) and "render  " not in line:
                print("   " + line.rstrip(), flush=True)
        p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"step '{step}' failed (exit {p.returncode}); see logs/run.log")


def check_deps():
    missing = []
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            missing.append(tool)
    for mod in ("numpy", "scipy", "PIL", "bpy"):
        try:
            importlib.import_module(mod)
        except Exception:  # noqa: BLE001
            missing.append(mod)
    if missing:
        raise RuntimeError(f"missing dependencies: {missing} -> pip install -r requirements.txt ; apt install ffmpeg")
    log("dependencies OK (ffmpeg, ffprobe, numpy, scipy, Pillow, bpy)")


def plan(a, scenes):
    q = DRAFT if a.draft else FINAL
    frames = len(scenes) * 120
    sec = frames * (1.3 if a.draft else 7.5)
    log("PLAN")
    log(f"  scenes to render : {scenes} ({frames} frames @ {q['width']}x{q['height']}, {q['samples']} spp, Cycles CPU)")
    log(f"  estimated render : ~{sec / 60:.0f} min on 4 CPU cores (existing frames are skipped)")
    log("  audio            : synthesized locally (music, foley, ambience) ~10 s")
    log("  assembly         : FFmpeg -> output/final_short.mp4 (1080x1920, 30 fps, H.264/AAC, -14 LUFS)")
    log("  paid API calls   : NONE (no generator keys configured; see docs/technical_audit.md)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--scene", default=None, help="comma list of scenes to (re)render, e.g. 3 or 2,5")
    ap.add_argument("--only", choices=STEPS, default=None)
    ap.add_argument("--draft", action="store_true", help="fast low-res render")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    st = load_state()
    scenes = [int(x) for x in a.scene.split(",")] if a.scene else list(range(1, 10))
    log("=" * 70)
    log(f"run.py start  args={vars(a)}")

    if a.dry_run:
        sh([PY, "scripts/audit_environment.py"], "audit")
        try:
            check_deps()
        except RuntimeError as e:
            log(f"WARNING: {e}")
        plan(a, scenes)
        log("dry-run finished: nothing rendered, no paid requests made")
        return

    steps = [a.only] if a.only else STEPS
    q = DRAFT if a.draft else FINAL
    for step in steps:
        t0 = time.time()
        log(f"--- step: {step}")
        try:
            if step == "audit":
                sh([PY, "scripts/audit_environment.py"], step)
            elif step == "deps":
                check_deps()
            elif step == "refs":
                sh([PY, "scripts/generate_assets.py"] + (["--force"] if a.force else []), step)
            elif step == "render":
                args = [PY, "scripts/animate_scenes.py", "--scenes", ",".join(map(str, scenes)),
                        "--width", str(q["width"]), "--height", str(q["height"]), "--samples", str(q["samples"])]
                if a.force or a.scene:
                    args.append("--force")
                if a.draft:  # drafts never overwrite final frames
                    args += ["--out", os.path.join(ROOT, "assets", "generated", "draft")]
                sh(args, step)
            elif step == "audio":
                sh([PY, "scripts/create_audio.py"], step)
            elif step in ("assemble", "validate") and a.draft:
                log(f"draft mode: skipping {step} (draft clips are in assets/generated/draft/scenes)")
            elif step == "assemble":
                sh([PY, "scripts/assemble_video.py"], step)
            elif step == "validate":
                sh([PY, "scripts/validate_video.py"], step)
            elif step == "report":
                v = os.path.join(ROOT, "logs", "validation.json")
                if os.path.exists(v):
                    with open(v) as f:
                        R = json.load(f)
                    ok = sum(c["ok"] for c in R["checks"])
                    log(f"validation: {ok}/{len(R['checks'])} checks passed -> docs/validation_report.md")
                log("final video: output/final_short.mp4   preview: output/preview.mp4")
            st[step] = {"done": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": round(time.time() - t0, 1)}
            save_state(st)
        except Exception as e:  # noqa: BLE001
            log(f"ERROR in step '{step}': {e}")
            log("fix the problem and run the same command again: finished work is reused")
            sys.exit(1)
    log("pipeline finished")


if __name__ == "__main__":
    main()
