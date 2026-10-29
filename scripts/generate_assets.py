#!/usr/bin/env python3
"""Render character reference images (front / 3/4 / side / back / face) into assets/references/
and a combined sheet. Uses exactly the same procedural models as the film, which is what keeps
the characters identical in every shot. Existing images are reused unless --force."""
import argparse
import os
import subprocess
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS = ["ryzhik", "puppy", "rabbit", "fox", "raccoon"]
VIEWS = ["front", "threequarter", "side", "back", "face"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--pct", type=int, default=50)
    a = ap.parse_args()
    out = os.path.join(ROOT, "assets", "references")
    os.makedirs(out, exist_ok=True)
    todo = [c for c in CHARS if a.force or not all(os.path.exists(os.path.join(out, f"{c}_{v}.png")) for v in VIEWS)]
    for c in todo:
        r = subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(ROOT, "scripts", "blender", "ref_lineup.py"),
                            "--", out, str(a.pct), c], capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:])
            return 1
        print("references:", c)
    # combined sheet
    rows = []
    for c in CHARS:
        ims = [Image.open(os.path.join(out, f"{c}_{v}.png")).convert("RGB") for v in VIEWS]
        w, h = ims[0].size
        row = Image.new("RGB", (w * len(ims), h))
        for i, im in enumerate(ims):
            row.paste(im, (i * w, 0))
        rows.append(row.crop((0, int(h * 0.1), row.size[0], int(h * 0.62))))
    W = rows[0].size[0]
    sheet = Image.new("RGB", (W, sum(r.size[1] for r in rows)))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.size[1]
    sheet.thumbnail((2400, 2400))
    sheet.save(os.path.join(out, "character_sheet.jpg"), quality=90)
    print("references: sheet ->", os.path.join(out, "character_sheet.jpg"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
