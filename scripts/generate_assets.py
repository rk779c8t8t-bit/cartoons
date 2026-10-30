#!/usr/bin/env python3
"""Character reference sheets (design bible renders) from the SAME 3D models used in the film.

Because no AI image generator is available in this environment (see docs/technical_audit.md),
the references are rendered from the procedural 3D character rigs. This guarantees that the
references and every scene share identical character designs.

Outputs (assets/references/):
  milo_front.png, milo_side.png, milo_three_quarter.png, mom_portrait.png,
  noodle_reference.png, lineup.png, character_sheet.png (montage)

If an AI image API key becomes available, prompts/characters/*.md contain ready-made
prompts; pass these PNGs as reference images for character consistency.
"""
import argparse
import math
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=1280)
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = os.path.join(ROOT, "assets", "references")
    os.makedirs(out, exist_ok=True)
    names = ["milo_front", "milo_side", "milo_three_quarter", "mom_portrait", "noodle_reference", "lineup"]
    if not a.force and all(os.path.exists(os.path.join(out, f"{n}.png")) for n in names):
        print("[refs] references exist (use --force to re-render)")
        return

    import bpy
    from mathutils import Vector
    from lbs3d.scenes import Production
    from lbs3d import world
    from lbs3d.world import FLOOR_Z, aim

    prod = Production()
    world.render_settings(a.width, a.height, a.samples)
    sc = bpy.context.scene
    m, mom, nd = prod.milo, prod.mom, prod.nd

    def shot(name):
        sc.render.filepath = os.path.join(out, f"{name}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[refs] {name}.png", flush=True)

    def base():
        prod.reset_frame()

    # Milo turnaround on the countertop
    for name, ang in (("milo_front", 0.0), ("milo_three_quarter", 0.7), ("milo_side", math.pi / 2)):
        base()
        m.pose(loc=(0, 0, 0), rz=ang, smile=0.8, look=(0, 0), tail_wag=1.0)
        aim(prod.cam, (0.0, -1.25, 0.32), (0, 0, 0.25), lens=40, fstop=5.6)
        shot(name)
    # Mom portrait (full body, in front of the island)
    base()
    prod.show_mom(True)
    mom.pose(loc=(0, -1.3, FLOOR_Z), rz=0.0, smile=0.8, eye_big=1.0, tail_up=0.5, arm_l=(-0.1, 0.2, 0), arm_r=(-0.1, -0.2, 0))
    aim(prod.cam, (0.2, -3.9, -0.05), (0, -1.3, -0.12), lens=32, fstop=6)
    shot("mom_portrait")
    # Noodle creature
    base()
    world._set_hide(m.root, True)
    nd.visible(True)
    pts = [Vector((0.75 - 0.065 * i, 0.15 + 0.06 * math.sin(i * 1.1), 0.055 + 0.02 * max(0, i - 6) ** 1.5)) for i in range(12)]
    nd.set(pts, t=0.4, face_dir=(0.2, -1, 0), eyes_scale=1.3)
    aim(prod.cam, (0.3, -1.1, 0.5), (0.18, 0.12, 0.16), lens=28, fstop=5.6)
    shot("noodle_reference")
    # Lineup / scale comparison
    base()
    prod.show_mom(True)
    mom.pose(loc=(0.45, -1.3, FLOOR_Z), rz=-0.25, smile=0.8)
    m.pose(loc=(-0.35, -1.3, FLOOR_Z), rz=0.25, smile=0.9)
    nd.visible(True)
    pts = [Vector((0.05 - 0.05 * math.cos(i * 0.9) * 0.6, -1.3 + 0.05 * math.sin(i * 0.9), FLOOR_Z + 0.055 + 0.03 * i)) for i in range(12)]
    nd.set(pts, t=0.4, face_dir=(0, -1, 0), eyes_scale=1.2)
    aim(prod.cam, (0.0, -4.4, -0.2), (0.05, -1.3, -0.3), lens=30, fstop=8)
    shot("lineup")
    subprocess.run(["montage", *[os.path.join(out, f"{n}.png") for n in names], "-tile", "6x1", "-geometry", "360x640+4+4",
                    "-background", "white", os.path.join(out, "character_sheet.png")], check=False)
    print("[refs] character_sheet.png")


if __name__ == "__main__":
    main()
