"""Cut Dora's verse from the full song and build a soft outro.

The original audio stops at CUT (just before the next vocalist comes in);
after that only a reverb/echo tail of the last bar plays, fading to silence.
Usage: python3 -I scripts/make_audio.py znak_full.mp3 public/verse.wav
"""
import sys
import numpy as np
import librosa
import soundfile as sf
from scipy.signal import fftconvolve

SR = 48000
START = 139.16     # clip start in the song (s)
TOTAL = 38.73      # clip length (s)
CUT = 36.24        # original audio ends here (clip time) = 175.40 s in the song
TAIL_SRC = 1.2     # seconds of music before CUT that feed the reverb tail

y, _ = librosa.load(sys.argv[1], sr=SR, mono=False, offset=START, duration=CUT + 0.1)
y = y[:, : int(CUT * SR)]
n_total = int(TOTAL * SR)
out = np.zeros((2, n_total), dtype=np.float32)

# dry signal with 30 ms fade-in and 60 ms fade-out at the cut
dry = y.copy()
fi = int(0.03 * SR); fo = int(0.06 * SR)
dry[:, :fi] *= np.linspace(0, 1, fi)
dry[:, -fo:] *= np.linspace(1, 0, fo)
out[:, : dry.shape[1]] += dry

# synthetic stereo hall impulse (decorrelated decaying noise, RT60 ≈ 3.6 s) + a few discrete echoes
rng = np.random.default_rng(7)
ir_len = int(3.2 * SR)
t = np.arange(ir_len) / SR
env = np.exp(-6.9 * t / 3.6)
ir = rng.standard_normal((2, ir_len)) * env
for d, g in [(0.11, 0.5), (0.23, 0.4), (0.37, 0.3), (0.54, 0.22)]:
    ir[:, int(d * SR)] += g * 40
# darker tail: one-pole lowpass on the impulse
ir = np.array([np.convolve(ch, np.ones(8) / 8, mode='same') for ch in ir])

src = y[:, -int(TAIL_SRC * SR):]
wet = np.array([fftconvolve(src[c], ir[c]) for c in range(2)])
wet_start = int((CUT - TAIL_SRC) * SR)
cut_i = int(CUT * SR)
wet_full = np.zeros((2, n_total), dtype=np.float32)
end = min(n_total, wet_start + wet.shape[1])
wet_full[:, wet_start:end] = wet[:, : end - wet_start]
# only the part after the cut is used, with a 60 ms fade-in so it takes over from the dry signal
wet_full[:, :cut_i] = 0
wet_full[:, cut_i : cut_i + fo] *= np.linspace(0, 1, fo)
# match level: tail starts about as loud as the music it continues
ref = np.sqrt(np.mean(src ** 2))
seg = wet_full[:, cut_i : cut_i + int(0.3 * SR)]
wet_full *= (ref * 0.8) / (np.sqrt(np.mean(seg ** 2)) + 1e-9)
# gentle overall fade to exact silence by the last 0.3 s
fade_end = n_total - int(0.3 * SR)
fade = np.ones(n_total, dtype=np.float32)
fade[cut_i:fade_end] = np.linspace(1, 0, fade_end - cut_i) ** 1.1
fade[fade_end:] = 0
out += wet_full * fade

# keep the original loudness (same as a plain ffmpeg cut); only clip stray inter-sample peaks
out = np.clip(out, -1.0, 1.0)
sf.write(sys.argv[2], out.T, SR, subtype='PCM_16')
print('written', sys.argv[2], out.shape[1] / SR, 's')
