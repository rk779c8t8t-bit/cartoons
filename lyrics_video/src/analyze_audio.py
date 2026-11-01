"""Audio analysis: tempo grid, kicks, energy envelopes -> analysis/analysis.json.

Usage:  python3 src/analyze_audio.py [--audio audio/fragment.m4a] [--fps 60]

The word timings themselves live in config/timeline.json (they were found with
vocal separation + ASR + onset analysis, then checked by hand). This script
produces the beat grid and the per-frame envelopes that drive the
music-reactive effects (pulses, glow, embers).
"""
import argparse, json, os, subprocess, tempfile
import numpy as np
import librosa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path, sr=22050):
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", str(sr), wav], check=True)
        y, _ = librosa.load(wav, sr=sr, mono=True)
    return y, sr


def env_at_fps(x, src_rate, fps, n):
    t = np.arange(n) / fps
    src_t = np.arange(len(x)) / src_rate
    return np.interp(t, src_t, x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", default=os.path.join(ROOT, "audio", "fragment.m4a"))
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--out", default=os.path.join(ROOT, "analysis", "analysis.json"))
    a = ap.parse_args()

    y, sr = load(a.audio)
    dur = len(y) / sr
    hop = 256
    rate = sr / hop
    H, P = librosa.effects.hpss(y, margin=2)

    # --- percussive onsets (kick band + full) ---
    S = np.abs(librosa.stft(P, n_fft=1024, hop_length=hop))
    f = librosa.fft_frequencies(sr=sr, n_fft=1024)
    def band_flux(lo, hi):
        e = np.log1p(S[(f >= lo) & (f < hi)].sum(0) * 10)
        d = np.maximum(0, np.diff(e, prepend=e[0]))
        return d / (d.max() + 1e-9)
    kick = band_flux(20, 130)
    hats = band_flux(3000, 9000)
    times = librosa.frames_to_time(np.arange(len(kick)), sr=sr, hop_length=hop)
    pk = librosa.util.peak_pick(kick, pre_max=8, post_max=8, pre_avg=20, post_avg=20, delta=0.12, wait=30)
    kick_times = times[pk]

    # --- tempo grid: librosa beat track, then least-squares fit of a straight grid ---
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time", start_bpm=158)
    idx = np.arange(len(beats))
    period, phase = np.polyfit(idx, beats, 1)
    bpm = 60.0 / period
    grid = phase + period * np.arange(-2, int(dur / period) + 3)
    grid = grid[(grid >= 0) & (grid <= dur)]

    # --- energy envelopes ---
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms /= rms.max()
    v = librosa.feature.rms(y=H, hop_length=hop)[0]
    v /= v.max()
    n = int(round(dur * a.fps))
    def smooth_attack_release(x, att=0.5, rel=0.12):
        out = np.zeros_like(x); s = 0.0
        for i, xi in enumerate(x):
            s = s + (xi - s) * (att if xi > s else rel); out[i] = s
        return out
    kick_env = smooth_attack_release(kick, 0.9, 0.08)

    data = {
        "audio": os.path.relpath(a.audio, ROOT),
        "duration": dur,
        "fps": a.fps,
        "frames": n,
        "bpm": round(float(bpm), 3),
        "beat_period": float(period),
        "beat_phase": float(phase),
        "beats": [round(float(b), 4) for b in grid],
        "kicks": [round(float(k), 4) for k in kick_times],
        "env": {
            "rms": np.round(env_at_fps(rms, rate, a.fps, n), 4).tolist(),
            "harmonic": np.round(env_at_fps(v, rate, a.fps, n), 4).tolist(),
            "kick": np.round(env_at_fps(kick_env, rate, a.fps, n), 4).tolist(),
            "hats": np.round(env_at_fps(smooth_attack_release(hats, 0.9, 0.15), rate, a.fps, n), 4).tolist(),
        },
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(data, fh)
    print(f"duration {dur:.3f}s  bpm {bpm:.2f}  beats {len(grid)}  kicks {len(kick_times)}")
    print("kicks:", " ".join(f"{k:.2f}" for k in kick_times))


if __name__ == "__main__":
    main()
