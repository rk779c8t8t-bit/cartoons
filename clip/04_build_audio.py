"""Build the soundtrack from the source video's music only.
- music: 0 .. 10.78 s of the source (the TikTok logo sting after it is dropped)
- pre-roll: 1.0 s reverse-reverb swell made from the first beat of the same track
- tail: natural reverb decay of the last phrase, so the final image can breathe
No external sounds are added."""
import sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfilt

src, out = sys.argv[1], sys.argv[2]
PRE, MUSIC_END, A_END = 1.0, 10.78, 12.8
sr, y = wavfile.read(src)
y = y.astype(np.float32) / 32768.0
if y.ndim == 1:
    y = np.stack([y, y], 1)
music = y[: int(MUSIC_END * sr)].copy()
fo = int(0.012 * sr)
music[-fo:] *= np.linspace(1, 0, fo)[:, None]

rng = np.random.default_rng(0)
def ir(dur, decay):
    n = int(dur * sr)
    t = np.arange(n) / sr
    e = np.exp(-t / decay)
    l = rng.standard_normal(n) * e; r = rng.standard_normal(n) * e
    sos = butter(2, 5500, 'low', fs=sr, output='sos')
    l, r = sosfilt(sos, l), sosfilt(sos, r)
    pre = int(0.012 * sr)
    l[:pre] *= np.linspace(0, 1, pre); r[:pre] *= np.linspace(0, 1, pre)
    return np.stack([l, r], 1) / np.sqrt((l ** 2).sum())

# reverse-reverb swell
seg = music[: int(0.55 * sr)]
R = ir(2.2, 0.55)
rev = seg[::-1]
wet = np.stack([fftconvolve(rev[:, c], R[:, c]) for c in range(2)], 1)
wet = wet[::-1]                      # swell, then the original content at the end
swell = wet[: len(wet) - len(seg)]   # only the build-up before the first note
swell = swell[-int(PRE * sr):]
swell *= np.linspace(0, 1, len(swell))[:, None] ** 2.2
swell *= 0.55 / (np.abs(swell).max() + 1e-6)

# reverb tail from the last phrase
last = music[int(10.30 * sr):]
R2 = ir(2.8, 0.75)
wet2 = np.stack([fftconvolve(last[:, c], R2[:, c]) for c in range(2)], 1)
tail = wet2[len(last):]
tail_len = int((A_END - MUSIC_END) * sr)
tail = tail[:tail_len]
tail *= 0.35 / (np.abs(tail[: int(0.05 * sr)]).max() + 1e-6) * np.abs(music[-int(0.4 * sr):]).max()
env = np.linspace(1, 0, len(tail)) ** 1.6
tail *= env[:, None]
# also let the music itself ring into the tail (wet signal during the last phrase)
mix = np.concatenate([swell, music, tail])
mix_wet_start = int(PRE * sr) + int(10.30 * sr)
wet_overlap = wet2[: len(last)] * 0.18
mix[mix_wet_start: mix_wet_start + len(wet_overlap)] += wet_overlap
total = int((PRE + A_END) * sr)
mix = mix[:total]
if len(mix) < total:
    mix = np.concatenate([mix, np.zeros((total - len(mix), 2), np.float32)])
mix *= 0.89 / np.abs(mix).max()
wavfile.write(out, sr, (mix * 32767).astype(np.int16))
print('audio', len(mix) / sr, 's')
