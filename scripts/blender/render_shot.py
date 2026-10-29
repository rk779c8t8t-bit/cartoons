"""Build one shot and render its frames.

blender -b --factory-startup -P render_shot.py -- --shot N --out DIR [--pct 100] [--samples 10]
        [--step 1] [--start 1] [--end N] [--force] [--save-blend PATH]
Existing frames are skipped unless --force (crash-safe resume).
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import common  # noqa: E402
import scenes  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--shot", type=int, required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=10)
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--start", type=int, default=1)
ap.add_argument("--end", type=int, default=0)
ap.add_argument("--force", action="store_true")
ap.add_argument("--save-blend", default="")
ap.add_argument("--frames", default="", help="comma separated explicit frame list")
a = ap.parse_args(argv)

t0 = time.time()
common.reset()
info = scenes.SHOTS[a.shot]() or {}
common.render_settings(res=(1080, 1920), pct=a.pct, samples=a.samples, motion_blur=True, ssr=info.get("ssr", False))
sc = bpy.context.scene
sc.eevee.shadow_cascade_size = "2048"
common.join_static(exclude_prefixes=("drop_proto", "rain_", "tuft_mesh"))
n = scenes.frames_for(a.shot)
sc.frame_start = 1
sc.frame_end = n
end = a.end or n
if a.save_blend:
    bpy.ops.wm.save_as_mainfile(filepath=a.save_blend)
print(f"[shot {a.shot}] built in {time.time() - t0:.1f}s; frames 1..{n}", flush=True)
os.makedirs(a.out, exist_ok=True)
frames = [int(x) for x in a.frames.split(",") if x] if a.frames else list(range(a.start, end + 1, a.step))
for f in frames:
    path = os.path.join(a.out, f"{f:04d}.png")
    if os.path.exists(path) and os.path.getsize(path) > 0 and not a.force:
        continue
    sc.frame_set(f)
    sc.render.filepath = path + ".tmp.png"
    t = time.time()
    bpy.ops.render.render(write_still=True)
    os.replace(path + ".tmp.png", path)
    print(f"[shot {a.shot}] frame {f}/{n} {time.time() - t:.1f}s", flush=True)
print(f"[shot {a.shot}] done in {time.time() - t0:.1f}s", flush=True)
