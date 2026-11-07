"""Render all frames in parallel and mux with the soundtrack -> output/eminem_toly_animated.mp4"""
import os, sys, subprocess, time
from multiprocessing import Pool
import numpy as np, cv2, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import ROOT, W, H, FPS, DUR

FR = os.path.join(ROOT, 'renders', 'frames')


def work(i):
    import scenes
    out = os.path.join(FR, f'{i:05d}.png')
    if os.path.exists(out):
        return i
    s = scenes.render(i / FPS)
    arr = np.zeros((H, W, 4), np.uint8)
    s.readPixels(skia.ImageInfo.Make(W, H, skia.kBGRA_8888_ColorType, skia.kUnpremul_AlphaType), arr)
    cv2.imwrite(out, arr[..., :3], [cv2.IMWRITE_PNG_COMPRESSION, 1])
    return i


if __name__ == '__main__':
    os.makedirs(FR, exist_ok=True)
    n = int(DUR * FPS)
    t0 = time.time()
    with Pool(os.cpu_count()) as p:
        for k, _ in enumerate(p.imap_unordered(work, range(n), chunksize=4)):
            if k % 50 == 0:
                print(k, '/', n, round(time.time() - t0), 's', flush=True)
    os.makedirs(os.path.join(ROOT, 'output'), exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', os.path.join(FR, '%05d.png'),
                    '-i', os.path.join(ROOT, 'renders', 'soundtrack.wav'),
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                    '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart',
                    os.path.join(ROOT, 'output', 'eminem_toly_animated.mp4')], check=True)
    print('done', round(time.time() - t0), 's')
