"""Build the soundtrack and the timing data the animation is synced to.

Soundtrack = 2.05 s synthesized intro (reverse swell + riser + sub)
           + mashup music 0 .. 10.6 s (TikTok outro jingle cut off)
           + outro: impact + reverb wash of the last bar.
"""
import json, os, sys
import numpy as np, librosa, scipy.signal as ss, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
PRE = 2.05          # music starts here on the video timeline (one bar @ ~117 BPM)
MUSIC_END = 10.62   # cut before the TikTok jingle
DUR = 15.0

# Syllable schedule in *music* time: (word, [syllable starts]).  Times were read
# from pitch/energy analysis and the bar grid (downbeats 2.62, 4.55, 6.62, 8.52).
LYRICS = {
    'toly': [
        [('ГОРИ,', [0.92, 1.20]), ('Я', [1.55]), ('ГОРЮ', [1.78, 1.93]), ('ТОЖЕ', [2.17, 2.30])],
    ],
    'eminem': [
        [('NOW,', [2.50]), ('THIS', [2.74]), ('LOOKS', [2.98]), ('LIKE', [3.20]), ('A', [3.38]),
         ('JOB', [3.55]), ('FOR', [3.84]), ('ME', [4.06])],
        [('SO', [4.55]), ('EVERYBODY,', [4.80, 4.94, 5.08, 5.22]), ('JUST', [5.58]),
         ('FOLLOW', [5.84, 6.02]), ('ME', [6.20])],
        [('’CAUSE', [6.60]), ('WE', [6.80]), ('NEED', [7.00]), ('A', [7.18]), ('LITTLE', [7.33, 7.48]),
         ('CONTROVERSY', [7.68, 7.88, 8.06, 8.26])],
        [('’CAUSE', [8.55]), ('IT', [8.74]), ('FEELS', [8.94]), ('SO', [9.18]), ('EMPTY', [9.42, 9.66]),
         ('WITHOUT', [9.92, 10.12]), ('ME', [10.30])],
    ],
}
# Beat grid from librosa beat tracking on the full mashup (~117.5 BPM).
BEATS = [0.07, 0.6, 1.11, 1.63, 2.14, 2.62, 3.09, 3.58, 4.06, 4.55, 5.06, 5.57, 6.11,
         6.62, 7.17, 7.66, 8.08, 8.52, 8.99, 9.52, 10.03, 10.47]
LINE_END = {'toly': [2.45], 'eminem': [4.45, 6.50, 8.48, 10.55]}


def load_music():
    src = [f for f in os.listdir(os.path.join(ROOT, 'assets', 'src')) if f == 'mashup_audio.wav'][0]
    y, sr = librosa.load(os.path.join(ROOT, 'assets', 'src', src), sr=SR, mono=False)
    return y  # (2, n)


def reverb_ir(seconds, decay, seed=0):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((2, n)) * np.exp(-t / decay)
    b, a = ss.butter(2, 6000 / (SR / 2))
    return ss.lfilter(b, a, ir) * 0.03


def build():
    music = load_music()
    n_total = int(DUR * SR)
    out = np.zeros((2, n_total))
    mstart, mlen = int(PRE * SR), int(MUSIC_END * SR)
    seg = music[:, :mlen].copy()
    fade = int(0.04 * SR)
    seg[:, -fade:] *= np.linspace(1, 0, fade)
    out[:, mstart:mstart + mlen] += seg

    t = np.arange(mstart) / SR
    rng = np.random.default_rng(3)
    # reverse swell: reverb of the first beat, reversed into the downbeat
    wet = np.stack([ss.fftconvolve(music[c, :int(0.6 * SR)], reverb_ir(2.2, 0.6, 1)[c]) for c in range(2)])
    wet = wet[:, :mstart][:, ::-1]
    wet *= 0.9 / (np.abs(wet).max() + 1e-9)
    env = (t / t[-1]) ** 2.2
    out[:, :mstart] += wet * env * 0.55
    # noise riser with rising band-pass
    noise = rng.standard_normal(mstart)
    sweep = np.zeros(mstart)
    blk = 2048
    for i in range(0, mstart, blk):
        f = 300 + 7000 * (i / mstart) ** 2
        b, a = ss.butter(2, [f / (SR / 2), min(0.99, f * 1.6 / (SR / 2))], 'band')
        sweep[i:i + blk] = ss.lfilter(b, a, noise[i:i + blk])
    out[:, :mstart] += sweep * (t / t[-1]) ** 3 * 0.10
    # sub drone + heartbeat pulses on the bar grid
    sub = np.sin(2 * np.pi * 41 * t) * 0.18 * np.clip(t / 0.6, 0, 1)
    out[:, :mstart] += sub
    for pt in (0.0, 1.03):
        k = (t >= pt)
        tt = t[k] - pt
        out[:, :mstart][:, k] += 0.35 * np.sin(2 * np.pi * (55 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 7)

    # outro: impact + reverb wash of the last bar
    o0 = mstart + mlen
    tail = music[:, int((MUSIC_END - 2.0) * SR):mlen]
    wash = np.stack([ss.fftconvolve(tail[c], reverb_ir(4.5, 1.3, 2)[c]) for c in range(2)])
    wash = wash[:, int(2.0 * SR) - int(0.05 * SR):]
    wash *= 0.5 / (np.abs(wash).max() + 1e-9)
    n = min(wash.shape[1], n_total - o0)
    out[:, o0:o0 + n] += wash[:, :n]
    tt = np.arange(n_total - o0) / SR
    boom = 0.55 * np.sin(2 * np.pi * (38 + 80 * np.exp(-tt * 18)) * tt) * np.exp(-tt * 2.2)
    crack = rng.standard_normal(len(tt)) * np.exp(-tt * 25) * 0.25
    out[:, o0:] += boom + crack
    # master fade + limiter
    fo = int(0.8 * SR)
    out[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    os.makedirs(os.path.join(ROOT, 'renders'), exist_ok=True)
    sf.write(os.path.join(ROOT, 'renders', 'soundtrack.wav'), out.T.astype(np.float32), SR)

    # ---- analysis for sync ----
    mono = librosa.to_mono(music[:, :mlen])
    sr2 = 22050
    mono = librosa.resample(mono, orig_sr=SR, target_sr=sr2)
    b, a = ss.butter(4, [300 / (sr2 / 2), 3400 / (sr2 / 2)], 'band')
    voc = ss.filtfilt(b, a, mono)
    hop = sr2 // 60
    env = librosa.feature.rms(y=voc, hop_length=hop, frame_length=1024)[0]
    env = env / np.percentile(env, 98)
    tempo, beats = librosa.beat.beat_track(y=mono, sr=sr2)
    beats = librosa.frames_to_time(beats, sr=sr2)
    lo = ss.filtfilt(*ss.butter(4, 150 / (sr2 / 2)), mono)
    kick = librosa.onset.onset_strength(y=lo, sr=sr2, hop_length=hop)
    kick = kick / (kick.max() + 1e-9)
    data = dict(pre=PRE, music_end=MUSIC_END, dur=DUR, tempo=float(np.atleast_1d(tempo)[0]),
                beats=[b + PRE for b in BEATS],
                env_rate=sr2 / hop, voc_env=[float(x) for x in env], kick=[float(x) for x in kick],
                lyrics={k: [[(w, [s + PRE for s in syl]) for w, syl in line] for line in v]
                        for k, v in LYRICS.items()},
                line_end={k: [x + PRE for x in v] for k, v in LINE_END.items()})
    json.dump(data, open(os.path.join(ROOT, 'assets', 'timing.json'), 'w'), ensure_ascii=False)
    print('tempo', data['tempo'], 'beats', len(beats))


if __name__ == '__main__':
    build()
