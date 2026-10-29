"""Render character reference sheets into assets/references/.
Usage: blender -b -P ref_lineup.py -- <outdir> [pct] [only_id]"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import common, geo, mats
from mats import hexc
from characters import Actor, CHARACTERS

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else "/tmp/refs"
pct = int(argv[1]) if len(argv) > 1 else 50
only = argv[2] if len(argv) > 2 else None
os.makedirs(out, exist_ok=True)

common.reset()
common.render_settings(res=(1080, 1920), pct=pct, samples=24, motion_blur=False)
common.world_sky("#cfe0ee", "#f4ece0", 1.0, "#d8d2c6")
common.sun("Sun", (55, 0, 35), 3.2)
common.area("Fill", (-3, -4, 2.5), (0, 0, 0.6), 250, 4, "#dfe9ff")
common.area("Rim", (2, 3, 3), (0, 0, 0.8), 300, 3, "#fff0d8")
floor = geo.cylinder("floor", (0, 0, -0.01), 6, 0.02, mats.basic("floorm", hexc("#e9e3d8"), rough=0.7))
cam, tgt = common.camera("Cam", lens=55, fstop=8)
bpy.context.scene.camera = cam

ids = [only] if only else list(CHARACTERS)
for cid in ids:
    for o in [o for o in bpy.data.objects if o.name.startswith(cid + "_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    a = Actor(cid)
    a.key(1, smile=0.6)
    h = CHARACTERS[cid]["height"]
    views = {"front": (0, -4.2, 0.9), "threequarter": (2.6, -3.3, 1.0), "side": (4.2, 0, 0.9), "back": (0, 4.2, 0.9)}
    for vname, loc in views.items():
        cam.location = loc
        tgt.location = (0, 0, 0.62 * h)
        cam.data.lens = 55
        bpy.context.scene.render.filepath = os.path.join(out, f"{cid}_{vname}.png")
        bpy.ops.render.render(write_still=True)
    # face close-up
    cam.location = (0.5, -2.2, 0.95 * h + 0.05)
    tgt.location = (0, 0, 0.9 * h)
    cam.data.lens = 85
    bpy.context.scene.render.filepath = os.path.join(out, f"{cid}_face.png")
    bpy.ops.render.render(write_still=True)
    # hide for next char
    for o in bpy.data.objects:
        if o.name.startswith(cid + "_"):
            o.hide_render = True
