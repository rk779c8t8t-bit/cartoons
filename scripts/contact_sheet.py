"""Make a contact sheet from a folder of frames: python3 contact_sheet.py DIR OUT [cols] [width]"""
import sys, os
from PIL import Image, ImageDraw

def sheet(d, out, cols=4, w=270):
    fs = sorted(f for f in os.listdir(d) if f.endswith(".png") and not f.endswith(".tmp.png"))
    ims = []
    for f in fs:
        im = Image.open(os.path.join(d, f)).convert("RGB")
        h = int(im.size[1] * w / im.size[0])
        im = im.resize((w, h))
        ImageDraw.Draw(im).text((4, 4), f[:-4], fill=(255, 255, 0))
        ims.append(im)
    if not ims:
        return
    rows = (len(ims) + cols - 1) // cols
    W, H = ims[0].size
    s = Image.new("RGB", (W * cols, H * rows))
    for i, im in enumerate(ims):
        s.paste(im, ((i % cols) * W, (i // cols) * H))
    s.save(out)

if __name__ == "__main__":
    sheet(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 4, int(sys.argv[4]) if len(sys.argv) > 4 else 270)
