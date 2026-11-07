import sys, time
sys.path.insert(0, 'src')
import skia, importlib, os
scenes = importlib.import_module(os.environ.get("MOD", "scenes"))
from PIL import Image
import numpy as np
S = '/tmp/claude-0/-home-user-cartoons/e3564bd2-6e7b-5487-9175-5649ed9eb08c/scratchpad/'
def to_np(surf):
    arr = np.zeros((1920, 1080, 4), np.uint8)
    surf.readPixels(skia.ImageInfo.Make(1080, 1920, skia.kRGBA_8888_ColorType, skia.kUnpremul_AlphaType), arr)
    return arr[..., :3]
if __name__ == '__main__':
    ts = [float(x) for x in sys.argv[1:]]
    ims = []
    for t in ts:
        t0 = time.time(); s = scenes.render(t); print(t, round(time.time() - t0, 2), 's')
        ims.append(Image.fromarray(to_np(s)).resize((360, 640)))
    sheet = Image.new('RGB', (360 * len(ims), 640))
    for i, im in enumerate(ims): sheet.paste(im, (360 * i, 0))
    sheet.save(S + 'frames.png')
