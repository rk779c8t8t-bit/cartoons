"""Step 1: prepare assets for the edit.

- extracts the original audio (lossless WAV) from the reference video
- upscales both portraits (Real-ESRGAN x4plus on CPU if torch + weights are
  available, otherwise Lanczos + detail sharpening)
- cuts the people out of the background (rembg / isnet-general-use)
- builds clean background plates (person removed + inpainted) for parallax

Usage:  python3 prep.py [--esrgan path/to/RealESRGAN_x4plus.pth]
Outputs go to assets/build/.
"""
import argparse
import os
import subprocess

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "assets", "src")
OUT = os.path.join(HERE, "assets", "build")


# --------------------------------------------------------------------------
# Real-ESRGAN (RRDBNet) - minimal re-implementation so we don't need basicsr
# --------------------------------------------------------------------------
def esrgan_upscale(img_bgr, weights):
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class RDB(nn.Module):
        def __init__(s, nf=64, gc=32):
            super().__init__()
            s.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
            s.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
            s.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
            s.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
            s.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
            s.l = nn.LeakyReLU(0.2, True)

        def forward(s, x):
            x1 = s.l(s.conv1(x))
            x2 = s.l(s.conv2(torch.cat((x, x1), 1)))
            x3 = s.l(s.conv3(torch.cat((x, x1, x2), 1)))
            x4 = s.l(s.conv4(torch.cat((x, x1, x2, x3), 1)))
            x5 = s.conv5(torch.cat((x, x1, x2, x3, x4), 1))
            return x5 * 0.2 + x

    class RRDB(nn.Module):
        def __init__(s, nf=64):
            super().__init__()
            s.rdb1, s.rdb2, s.rdb3 = RDB(nf), RDB(nf), RDB(nf)

        def forward(s, x):
            return s.rdb3(s.rdb2(s.rdb1(x))) * 0.2 + x

    class RRDBNet(nn.Module):
        def __init__(s, nf=64, nb=23):
            super().__init__()
            s.conv_first = nn.Conv2d(3, nf, 3, 1, 1)
            s.body = nn.Sequential(*[RRDB(nf) for _ in range(nb)])
            s.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
            s.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
            s.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
            s.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
            s.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
            s.l = nn.LeakyReLU(0.2, True)

        def forward(s, x):
            f = s.conv_first(x)
            f = f + s.conv_body(s.body(f))
            f = s.l(s.conv_up1(F.interpolate(f, scale_factor=2, mode="nearest")))
            f = s.l(s.conv_up2(F.interpolate(f, scale_factor=2, mode="nearest")))
            return s.conv_last(s.l(s.conv_hr(f)))

    net = RRDBNet()
    sd = torch.load(weights, map_location="cpu")
    sd = sd.get("params_ema", sd.get("params", sd))
    net.load_state_dict(sd, strict=True)
    net.eval()
    torch.set_num_threads(os.cpu_count() or 4)

    rgb = img_bgr[:, :, ::-1].astype(np.float32) / 255.0
    h, w = rgb.shape[:2]
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    tile, pad = 192, 12
    with torch.no_grad():
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                y0, x0 = max(0, y - pad), max(0, x - pad)
                y1, x1 = min(h, y + tile + pad), min(w, x + tile + pad)
                t = torch.from_numpy(rgb[y0:y1, x0:x1].transpose(2, 0, 1).copy())[None]
                r = net(t)[0].clamp(0, 1).numpy().transpose(1, 2, 0)
                ty, tx = (y - y0) * 4, (x - x0) * 4
                th, tw = min(tile, h - y) * 4, min(tile, w - x) * 4
                out[y * 4:y * 4 + th, x * 4:x * 4 + tw] = r[ty:ty + th, tx:tx + tw]
                print(f"  esrgan tile {y},{x}", flush=True)
    return (out[:, :, ::-1] * 255 + 0.5).astype(np.uint8)


def classic_upscale(img, f):
    up = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_LANCZOS4)
    blur = cv2.GaussianBlur(up, (0, 0), 1.6)
    return cv2.addWeighted(up, 1.6, blur, -0.6, 0)


def upscale(img, target_long, weights):
    """Upscale to roughly target_long px on the long side."""
    if weights and os.path.exists(weights):
        try:
            up = esrgan_upscale(img, weights)
            # blend a little of the classic version back in to avoid a
            # plastic "AI" look on skin
            classic = cv2.resize(img, (up.shape[1], up.shape[0]), interpolation=cv2.INTER_LANCZOS4)
            up = cv2.addWeighted(up, 0.85, classic, 0.15, 0)
        except Exception as e:  # torch missing etc.
            print("ESRGAN unavailable, falling back:", e)
            up = classic_upscale(img, 4)
    else:
        up = classic_upscale(img, 4)
    s = target_long / max(up.shape[:2])
    return cv2.resize(up, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)


def matte(img_bgr):
    from rembg import new_session, remove
    from PIL import Image

    sess = new_session("isnet-general-use")
    pil = Image.fromarray(img_bgr[:, :, ::-1])
    rgba = np.array(remove(pil, session=sess, post_process_mask=True))
    a = rgba[:, :, 3]
    # gentle edge refinement
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    return a


def plate(img, alpha, grow):
    """Remove the person and inpaint the hole -> background plate."""
    m = (alpha > 20).astype(np.uint8) * 255
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
    small_s = 0.25
    sm = cv2.resize(img, None, fx=small_s, fy=small_s, interpolation=cv2.INTER_AREA)
    mm = cv2.resize(m, (sm.shape[1], sm.shape[0]), interpolation=cv2.INTER_NEAREST)
    inp = cv2.inpaint(sm, mm, 9, cv2.INPAINT_TELEA)
    inp = cv2.GaussianBlur(inp, (0, 0), 3)
    inp = cv2.resize(inp, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    mf = cv2.GaussianBlur(m, (0, 0), grow / 3).astype(np.float32)[..., None] / 255
    return (img * (1 - mf) + inp * mf).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esrgan", default=os.path.join(HERE, "models", "RealESRGAN_x4plus.pth"))
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(SRC, "reference.mp4"),
                    "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
                    os.path.join(OUT, "original_audio.wav")], check=True)

    for name, long_side in (("toly", 2400), ("eminem", 2400)):
        print("processing", name)
        img = cv2.imread(os.path.join(SRC, name + ".png"))
        hr = upscale(img, long_side, args.esrgan)
        cv2.imwrite(os.path.join(OUT, name + "_hr.png"), hr)
        a = matte(hr)
        cv2.imwrite(os.path.join(OUT, name + "_alpha.png"), a)
        cv2.imwrite(os.path.join(OUT, name + "_plate.png"), plate(hr, a, 61))
    print("done")


if __name__ == "__main__":
    main()
