#!/usr/bin/env python3
"""Create the film's original soundtrack by pure synthesis (numpy/scipy, no samples,
no voices):

  assets/audio/music.wav     36 s orchestral-cartoon score (xylophone, marimba, pizzicato,
                             piano, light strings, brass, glockenspiel, soft drums)
  assets/audio/foley.wav     sound effects placed on the cue list in lbs3d/timeline.py
  assets/audio/ambience.wav  kitchen room tone, fridge hum, distant window birds (synthetic)
  assets/audio/mix.wav       balanced stereo mix (peak-limited)

Everything is generated from code => fully original, no licensing issues.
"""
import os
import sys

import numpy as np
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lbs3d.timeline import DURATION, SFX_CUES  # noqa: E402

SR = 48000
N = int(DURATION * SR)
RNG = np.random.default_rng(2024)
BEAT = 0.5  # 120 BPM: one scene = 8 beats = 2 bars


# ----------------------------------------------------------------------------- utils

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def n(name):
    """'C#5' -> midi"""
    pitch, octv = name[:-1], int(name[-1])
    return 12 * (octv + 1) + NOTE[pitch]


def tvec(dur):
    return np.arange(int(dur * SR)) / SR


def env_adsr(length, a=0.005, d=0.1, s=0.6, r=0.1):
    L = length
    e = np.ones(L) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = max(A, 1)
    e[:A] = np.linspace(0, 1, A)
    if A + D < L:
        e[A:A + D] = np.linspace(1, s, D)
    else:
        e[A:] = 1
    if R < L:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), "low")
    return signal.lfilter(b, a, x)


def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def noise(dur):
    return RNG.standard_normal(int(dur * SR))


class Track:
    def __init__(self):
        self.L = np.zeros(N + SR * 3)
        self.R = np.zeros(N + SR * 3)

    def add(self, x, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i < 0:
            x = x[-i:]
            i = 0
        j = min(i + len(x), len(self.L))
        x = x[: j - i]
        gl = gain * np.sqrt(0.5 * (1 - pan))
        gr = gain * np.sqrt(0.5 * (1 + pan))
        self.L[i:j] += x * gl
        self.R[i:j] += x * gr

    def stereo(self):
        return np.stack([self.L[:N], self.R[:N]], axis=1)


# ----------------------------------------------------------------------------- instruments

def xylo(m, dur=0.6, vel=1.0):
    f = mtof(m)
    t = tvec(dur)
    x = (np.sin(2 * np.pi * f * t) * np.exp(-t * 9) + 0.45 * np.sin(2 * np.pi * f * 3.0 * t) * np.exp(-t * 22)
         + 0.2 * np.sin(2 * np.pi * f * 6.1 * t) * np.exp(-t * 40))
    click = noise(0.006) * np.linspace(1, 0, int(0.006 * SR)) * 0.25
    x[: len(click)] += click
    return x * vel * 0.5


def marimba(m, dur=0.9, vel=1.0):
    f = mtof(m)
    t = tvec(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 5) + 0.25 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 18)
    x *= np.minimum(1, t / 0.002)
    return x * vel * 0.55


def glock(m, dur=1.4, vel=1.0):
    f = mtof(m)
    t = tvec(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 3) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6) \
        + 0.15 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 10)
    return x * vel * 0.3


def pizz(m, dur=0.45, vel=1.0):
    """Karplus-Strong plucked string"""
    f = mtof(m)
    L = int(dur * SR)
    period = int(SR / f)
    buf = RNG.uniform(-1, 1, period)
    buf = lowpass(buf, 3000, 1)
    out = np.zeros(L)
    for i in range(L):
        out[i] = buf[i % period]
        buf[i % period] = 0.5 * (buf[i % period] + buf[(i + 1) % period]) * 0.996
    out = lowpass(out, 2500)
    return out * vel * 0.9 * np.exp(-np.arange(L) / SR * 3)


def piano(m, dur=0.5, vel=1.0):
    f = mtof(m)
    t = tvec(dur + 0.3)
    x = np.zeros_like(t)
    for k, a in enumerate((1.0, 0.5, 0.28, 0.15, 0.08, 0.05), start=1):
        x += a * np.sin(2 * np.pi * f * k * 1.0005 ** k * t) * np.exp(-t * (2.5 + 1.2 * k))
    e = np.ones_like(t)
    r = int(0.3 * SR)
    e[-r:] = np.linspace(1, 0, r)
    return x * e * np.minimum(1, t / 0.003) * vel * 0.32


def strings(ms, dur, vel=1.0, trem=0.0, attack=0.15):
    t = tvec(dur)
    x = np.zeros_like(t)
    for m in ms:
        f = mtof(m)
        for det in (-0.12, 0.0, 0.13):
            ph = 2 * np.pi * f * 2 ** (det / 12) * t + RNG.uniform(0, 6.28)
            x += signal.sawtooth(ph) * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * t))
    x = lowpass(x, 2800, 2)
    e = env_adsr(len(t), a=attack, d=0.1, s=1.0, r=min(0.25, dur * 0.4))
    if trem:
        e *= 0.65 + 0.35 * np.sin(2 * np.pi * trem * t)
    return x * e * vel * 0.06 / max(1, len(ms)) ** 0.5


def brass(ms, dur, vel=1.0):
    t = tvec(dur)
    x = np.zeros_like(t)
    for m in ms:
        f = mtof(m)
        x += signal.sawtooth(2 * np.pi * f * t) + 0.5 * signal.sawtooth(2 * np.pi * f * 1.003 * t)
    # filter-envelope "blat"
    env_f = 600 + 2600 * np.exp(-t * 6)
    y = np.zeros_like(x)
    # block-wise time varying lowpass
    blk = 512
    zi = None
    for i in range(0, len(x), blk):
        b, a = signal.butter(2, min(env_f[i], SR / 2 - 200) / (SR / 2), "low")
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y[i:i + blk], zi = signal.lfilter(b, a, x[i:i + blk], zi=zi)
    return y * env_adsr(len(t), a=0.03, d=0.15, s=0.75, r=0.12) * vel * 0.09 / max(1, len(ms)) ** 0.5


def kick(vel=1.0):
    t = tvec(0.35)
    f = 50 + 90 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * vel * 0.9


def snare(vel=1.0):
    t = tvec(0.22)
    x = bandpass(noise(0.22), 1200, 8000) * np.exp(-t * 22) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4
    return x * vel * 0.5


def hat(vel=1.0, dur=0.05):
    t = tvec(dur)
    return highpass(noise(dur), 7000) * np.exp(-t * 70) * vel * 0.25


def woodblock(freq=900, vel=1.0):
    t = tvec(0.12)
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t * 45) + 0.4 * np.sin(2 * np.pi * freq * 2.3 * t) * np.exp(-t * 60)
    return x * vel * 0.45


def crash(vel=1.0, dur=1.6):
    t = tvec(dur)
    x = highpass(noise(dur), 3500) * np.exp(-t * 2.8)
    return x * vel * 0.18


def shaker(vel=1.0):
    t = tvec(0.08)
    return bandpass(noise(0.08), 5000, 12000) * np.sin(np.pi * t / 0.08) * vel * 0.15


def reverb(st, mix=0.18, rt=1.1):
    L = int(rt * SR)
    t = np.arange(L) / SR
    out = st.copy()
    for ch in range(2):
        ir = RNG.standard_normal(L) * np.exp(-t * 6.9 / rt)
        ir = lowpass(ir, 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        wet = signal.fftconvolve(st[:, ch], ir)[: len(st)]
        out[:, ch] = st[:, ch] * (1 - mix) + wet * mix
    return out


# ----------------------------------------------------------------------------- score

def music():
    tr = Track()
    b = lambda beats: beats * BEAT  # noqa: E731

    def mel(inst, notes, offset_beats, transpose=0, vel=1.0, pan=0.0):
        for (bt, dur, nm) in notes:
            if nm is None:
                continue
            tr.add(inst(n(nm) + transpose, dur=max(0.25, dur * BEAT * 1.4), vel=vel), b(offset_beats + bt), pan=pan)

    def drums(b0, b1, kicks=(0, 2), snares=(1, 3), hats=0.5, vel=1.0):
        bt = b0
        while bt < b1 - 1e-6:
            rel = (bt - b0) % 4
            if any(abs(rel - k) < 1e-6 for k in kicks):
                tr.add(kick(0.7 * vel), b(bt))
            if any(abs(rel - k) < 1e-6 for k in snares):
                tr.add(snare(0.55 * vel), b(bt), pan=0.1)
            tr.add(hat(0.6 * vel), b(bt), pan=0.3)
            bt += hats

    theme = [(0, .5, "G4"), (.5, .5, "C5"), (1, .5, "E5"), (1.5, .5, "G5"), (2, 1, "E5"), (3, .5, "C5"), (3.5, .5, "D5"),
             (4, .5, "E5"), (4.5, .5, "F5"), (5, .5, "G5"), (5.5, .5, "A5"), (6, 1.5, "G5"), (7.5, .5, "G4")]
    bass_A = [(0, 1, "C3"), (1, 1, "G2"), (2, 1, "C3"), (3, 1, "G2"), (4, 1, "F2"), (5, 1, "C3"), (6, 1, "G2"), (7, 1, "B2")]

    # ---- 0-4 s  (beats 0-8): confident little chef
    mel(xylo, theme, 0, vel=1.0, pan=-0.2)
    mel(pizz, bass_A, 0, vel=0.9, pan=0.15)
    for bt, ch in ((1, ["C4", "E4", "G4"]), (3, ["C4", "E4", "G4"]), (5, ["F4", "A4", "C5"]), (7, ["G4", "B4", "D5"])):
        for nm in ch:
            tr.add(piano(n(nm), 0.25, 0.6), b(bt), pan=0.25)
    drums(0, 8, vel=0.8)
    tr.add(glock(n("C6"), vel=0.6), 1.9)  # catch
    tr.add(glock(n("G6"), vel=0.5), 2.45)  # wink

    # ---- 4-8 s (beats 8-16): cooking ... flour POOF at 6.35 s
    themeB = [(0, .5, "C5"), (.5, .5, "E5"), (1, .5, "G5"), (1.5, .5, "E5"), (2, .5, "F5"), (2.5, .5, "D5"),
              (3, .5, "B4"), (3.5, .5, "G4"), (4, .5, "C5"), (4.5, .2, "D5")]
    mel(xylo, themeB, 8, vel=0.95, pan=-0.2)
    mel(pizz, [(0, 1, "C3"), (1, 1, "E3"), (2, 1, "F2"), (3, 1, "G2"), (4, .5, "C3")], 8, vel=0.9, pan=0.15)
    drums(8, 12.5, vel=0.75)
    for k in range(5):  # stirring tick-tock
        tr.add(woodblock(1100 if k % 2 else 850, 0.5), 4.15 + k * 0.25, pan=0.4)
    poof = 6.35
    tr.add(brass([n("C3"), n("F#3")], 0.7, 1.0), poof)        # comic "bwaaah"
    tr.add(crash(0.9, 1.4), poof)
    tr.add(kick(1.0), poof)
    for k, nm in enumerate(["C6", "B5", "Bb5", "A5", "Ab5", "G5"]):   # sliding down (dumbfounded)
        tr.add(xylo(n(nm), 0.3, 0.45), poof + 0.08 + k * 0.07, pan=0.3)
    tr.add(xylo(n("E6"), 0.4, 0.5), 7.1)
    tr.add(xylo(n("C6"), 0.4, 0.5), 7.25)
    for k in range(8):  # shake flutter
        tr.add(woodblock(1400 + 120 * (k % 2), 0.35), 7.45 + k * 0.06, pan=-0.3 + 0.08 * k)

    # ---- 8-12 s (beats 16-24): funny tension (A minor)
    for k, nm in enumerate(["A2", "C3", "E3", "D#3", "A2", "C3", "E3", "F3"]):
        tr.add(pizz(n(nm), 0.4, 0.8), 8.0 + k * 0.5, pan=0.15)
    tr.add(strings([n("A3"), n("C4"), n("E4")], 2.3, 0.9, trem=12, attack=1.0), 8.7)
    for k, nm in enumerate(["A4", "C5", "E5", "A5", "C6", "E6"]):   # noodle rising run
        tr.add(marimba(n(nm), 0.6, 0.7), 8.85 + k * 0.09, pan=-0.2)
    tr.add(xylo(n("G#5"), 0.4, 0.6), 10.3)
    tr.add(xylo(n("A5"), 0.4, 0.6), 10.45)
    hit = 11.0  # crash-zoom stab
    tr.add(brass([n("A2"), n("E3"), n("A3"), n("C4")], 0.5, 1.2), hit)
    tr.add(strings([n("A4"), n("C5"), n("E5")], 0.4, 1.0, attack=0.01), hit)
    tr.add(kick(1.0), hit)
    tr.add(crash(0.6, 1.0), hit)
    tr.add(strings([n("E5"), n("F5")], 0.9, 0.7, trem=16, attack=0.05), hit + 0.12)
    tr.add(kick(0.5), 11.5)
    tr.add(kick(0.4), 11.75)

    # ---- 12-20 s (beats 24-40): chaos & chase (fast)
    chase_bass = ["A2", "A2", "C3", "A2", "D3", "A2", "E3", "D#3"]
    for bt in np.arange(24, 40, 0.5):
        tt = b(bt)
        if 15.0 <= tt < 16.0 or 17.7 <= tt < 20.0:
            continue
        tr.add(pizz(n(chase_bass[int((bt * 2) % 8)]), 0.3, 0.85), tt, pan=0.15)
    run = ["A4", "B4", "C5", "D5", "E5", "D5", "C5", "B4", "A4", "C5", "E5", "A5", "G#5", "E5", "D5", "B4"]
    for k, bt in enumerate(np.arange(24, 40, 0.25)):
        tt = b(bt)
        if 14.0 <= tt < 14.75 or 15.0 <= tt < 16.0 or 17.7 <= tt < 20.0:
            continue
        tr.add(xylo(n(run[k % 16]), 0.25, 0.55), tt, pan=-0.25)
    drums(24, 30, kicks=(0, 1.5, 2), snares=(1, 3), hats=0.25, vel=0.85)
    drums(32, 35.4, kicks=(0, 1.5, 2), snares=(1, 3), hats=0.25, vel=0.85)
    for k in range(8):  # slip: rising squeal on strings
        tr.add(xylo(n("C5") + 2 * k, 0.2, 0.45), 14.0 + k * 0.05, pan=0.3)
    tr.add(crash(0.9, 1.2), 14.7)
    tr.add(kick(1.0), 14.7)
    for k, nm in enumerate(["E4", "E4", "F4", "F#4"]):   # tiptoe peek
        tr.add(pizz(n(nm), 0.25, 0.6), 15.05 + k * 0.22, pan=0.2)
    # hiding behind the jar: tiptoe + tremolo suspense
    tr.add(strings([n("E4"), n("A4")], 1.6, 0.6, trem=10, attack=0.4), 17.75)
    for k, nm in enumerate(["A3", "C4", "A3", "D#4"]):
        tr.add(pizz(n(nm), 0.25, 0.55), 17.8 + k * 0.25, pan=0.2)
    tr.add(xylo(n("E5"), 0.3, 0.6), 18.7)
    tr.add(xylo(n("E5"), 0.3, 0.6), 18.8)
    for k in range(6):   # double-take gliss up
        tr.add(xylo(n("C5") + 3 * k, 0.2, 0.55), 19.2 + k * 0.035, pan=-0.1)
    tr.add(kick(0.8), 19.2)

    # ---- 20-24 s (beats 40-48): discovery -> joy (to F major)
    tr.add(strings([n("A3"), n("E4")], 1.2, 0.55, trem=8, attack=0.2), 20.0)
    tr.add(glock(n("C6"), vel=0.7), 21.2)
    tr.add(glock(n("F6"), vel=0.7), 21.32)
    tr.add(glock(n("A6"), vel=0.6), 21.44)
    arp = ["F4", "A4", "C5", "F5", "C5", "A4"]
    for k, bt in enumerate(np.arange(42.5, 48, 0.25)):
        tr.add(piano(n(arp[k % 6]), 0.3, 0.55), b(bt), pan=0.2)
    mel(pizz, [(0, 1, "F2"), (1, 1, "C3"), (2, 1, "F2"), (3, 1, "C3")], 44, vel=0.8)
    for bt in np.arange(44, 48, 0.5):
        tr.add(shaker(0.8), b(bt), pan=-0.3)
    tr.add(strings([n("F4"), n("A4"), n("C5")], 2.0, 0.5, attack=0.6), 22.0)

    # ---- 24-28 s (beats 48-56): triumphant creation (F major fanfare)
    fan = [(0, 1, "F4"), (1, .5, "A4"), (1.5, .5, "C5"), (2, 1.5, "F5"), (3.5, .5, "E5"), (4, 1, "D5"), (5, .5, "Bb4"),
           (5.5, .5, "D5"), (6, 2, "C5")]
    for (bt, dur, nm) in fan:
        tr.add(brass([n(nm)], dur * BEAT * 1.05, 0.9), b(48 + bt), pan=-0.1)
        tr.add(glock(n(nm) + 12, vel=0.4), b(48 + bt), pan=0.3)
    for bt, ch in ((48, ["F3", "A3", "C4"]), (50, ["F3", "A3", "C4"]), (52, ["Bb3", "D4", "F4"]), (54, ["C4", "E4", "G4"])):
        tr.add(strings([n(x) for x in ch], 1.0, 0.8, attack=0.08), b(bt))
    mel(pizz, [(0, 1, "F2"), (1, 1, "C3"), (2, 1, "F2"), (3, 1, "A2"), (4, 1, "Bb2"), (5, 1, "F2"), (6, 1, "C3"), (7, 1, "E2")], 48)
    drums(48, 56, kicks=(0, 2, 2.5), snares=(1, 3), hats=0.5, vel=0.7)
    tr.add(woodblock(700, 0.7), 25.6)
    for k, nm in enumerate(["C6", "F6", "A6", "C7"]):
        tr.add(glock(n(nm), vel=0.45), 27.4 + k * 0.06)

    # ---- 28-32 s (beats 56-64): mom arrives, surprise, tasting, delight
    for k, nm in enumerate(["F3", "A3", "C4", "A3"]):
        tr.add(pizz(n(nm), 0.3, 0.55), 28.3 + k * 0.3, pan=0.15)
    tr.add(brass([n("B2"), n("D3"), n("F3"), n("G#3")], 0.45, 1.0), 29.5)   # diminished stinger
    tr.add(strings([n("B4"), n("D5"), n("F5")], 0.35, 0.9, attack=0.01), 29.5)
    tr.add(crash(0.5, 0.8), 29.5)
    tr.add(strings([n("C6")], 1.3, 0.35, trem=14, attack=0.3), 30.2)
    for k in range(5):
        tr.add(woodblock(1000 if k % 2 else 800, 0.3), 30.4 + k * 0.25, pan=0.3)
    tr.add(strings([n("F4"), n("A4"), n("C5"), n("F5")], 0.5, 0.9, attack=0.25), 31.3)
    tr.add(crash(0.6, 1.5), 31.55)
    for k, nm in enumerate(["F5", "A5", "C6", "F6", "A6"]):
        tr.add(glock(n(nm), vel=0.55), 31.55 + k * 0.05)

    # ---- 32-36 s (beats 64-72): joyful finale (theme reprise in F) + ta-da
    themeF = [(0, .5, "G4"), (.5, .5, "C5"), (1, .5, "E5"), (1.5, .5, "G5"), (2, 1, "E5"), (3, .5, "C5"), (3.5, .5, "D5"),
              (4, .5, "E5"), (4.5, .5, "G5"), (5, 0.6, "C6")]
    mel(xylo, themeF, 64, transpose=5, vel=1.0, pan=-0.2)
    mel(marimba, themeF, 64, transpose=-7, vel=0.5, pan=0.2)
    mel(pizz, [(0, 1, "F2"), (1, 1, "C3"), (2, 1, "F2"), (3, 1, "C3"), (4, 1, "Bb2"), (5, 1, "C3")], 64)
    for bt, ch in ((65, ["F4", "A4", "C5"]), (67, ["F4", "A4", "C5"]), (68.5, ["Bb4", "D5", "F5"])):
        for nm in ch:
            tr.add(piano(n(nm), 0.25, 0.6), b(bt), pan=0.25)
    for k in range(4):   # tap-tap "more!"
        tr.add(woodblock(1200, 0.45), 32.1 + k * 0.18, pan=0.35)
    drums(64, 69.5, vel=0.8)
    tada = 34.8
    for k, nm in enumerate(["C5", "E5"]):   # pickup
        tr.add(xylo(n(nm), 0.25, 0.7), tada - 0.25 + k * 0.12)
    tr.add(brass([n("F3"), n("A3"), n("C4"), n("F4")], 1.1, 1.2), tada)
    tr.add(strings([n("F4"), n("A4"), n("C5"), n("F5")], 1.2, 1.0, attack=0.02), tada)
    tr.add(kick(1.0), tada)
    tr.add(crash(0.8, 1.2), tada)
    for k, nm in enumerate(["F5", "A5", "C6", "F6"]):
        tr.add(glock(n(nm), vel=0.55), tada + k * 0.04)
        tr.add(xylo(n(nm), 0.5, 0.5), tada + k * 0.04)

    st = tr.stereo()
    st = reverb(st, mix=0.16, rt=1.2)
    return st


# ----------------------------------------------------------------------------- sound effects

def sweep(f0, f1, dur, shape="exp"):
    t = tvec(dur)
    if shape == "exp":
        f = f0 * (f1 / f0) ** (t / dur)
    else:
        f = f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR), t


def fx(name):
    if name in ("whoosh_up", "slide_hide", "zoom_hit"):
        d = 0.45
        t = tvec(d)
        x = noise(d)
        out = np.zeros_like(x)
        for i in range(0, len(x), 512):  # moving band
            fc = 400 + 3000 * (i / len(x)) if name != "slide_hide" else 3000 - 2500 * (i / len(x))
            out[i:i + 512] = bandpass(x[i:i + 512 + 2048], fc * 0.7, fc * 1.4)[: len(out[i:i + 512])]
        out *= np.sin(np.pi * t / d) ** 2
        if name == "zoom_hit":
            out = np.concatenate([out, np.zeros(SR // 3)])
            out[int(0.3 * SR):int(0.3 * SR) + int(0.35 * SR)] += kick(0.9)[: int(0.35 * SR)]
        return out * 0.5
    if name == "tomato_toss":
        x, t = sweep(300, 900, 0.18)
        return x * np.exp(-t * 12) * 0.3
    if name in ("catch_pop", "peek_pop"):
        x, t = sweep(900, 300, 0.08)
        return x * np.exp(-t * 40) * 0.6
    if name in ("wink_ting", "plate_ting", "idea_ding"):
        f = {"wink_ting": 2600, "plate_ting": 3200, "idea_ding": 1760}[name]
        t = tvec(1.0)
        x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4)
        return x * np.exp(-t * 4.5) * 0.3
    if name in ("tiny_steps", "running_steps", "mom_steps"):
        k, gap, f = {"tiny_steps": (4, 0.17, 2200), "running_steps": (10, 0.09, 2600), "mom_steps": (4, 0.3, 900)}[name]
        out = np.zeros(int((k * gap + 0.2) * SR))
        for i in range(k):
            t = tvec(0.05)
            s = bandpass(noise(0.05), f * 0.5, f * 1.5) * np.exp(-t * 90) * (0.8 + 0.2 * (i % 2))
            j = int(i * gap * SR)
            out[j:j + len(s)] += s
        return out * 0.45
    if name in ("stir", "twirl"):
        d = 0.45 if name == "stir" else 1.0
        t = tvec(d)
        x = noise(d)
        mod = 1500 + 900 * np.sin(2 * np.pi * (3 if name == "stir" else 5) * t)
        out = np.zeros_like(x)
        for i in range(0, len(x), 256):
            fc = mod[i]
            out[i:i + 256] = bandpass(x[i:i + 256 + 1024], fc * 0.7, fc * 1.3)[: len(out[i:i + 256])]
        out *= np.sin(np.pi * t / d)
        if name == "twirl":
            sp, _ = sweep(600, 1800, d)
            out += 0.15 * sp * np.sin(np.pi * t / d)
        return out * 0.35
    if name in ("bag_rustle", "hat_adjust", "basil_flutter"):
        d = {"bag_rustle": 0.5, "hat_adjust": 0.4, "basil_flutter": 0.5}[name]
        x = highpass(noise(d), 2500) * (RNG.random(int(d * SR)) > 0.985) * 3 + highpass(noise(d), 4000) * 0.15
        return lowpass(x, 9000) * np.sin(np.pi * tvec(d) / d) * 0.4
    if name == "bag_slip":
        x, t = sweep(1200, 400, 0.3, "lin")
        return x * 0.25 * np.sin(np.pi * t / 0.3)
    if name == "flour_poof":
        d = 1.3
        t = tvec(d)
        x = lowpass(noise(d), 1400) * np.exp(-t * 3.5) * np.minimum(1, t / 0.02)
        th, _ = sweep(110, 45, d)
        return (x * 1.6 + th * np.exp(-t * 6) * 0.9) * 0.6
    if name == "blink":
        out = np.zeros(int(0.3 * SR))
        for k in range(2):
            s, t = sweep(2000, 2600, 0.03)
            out[int(k * 0.14 * SR):int(k * 0.14 * SR) + len(s)] += s * np.exp(-t * 80)
        return out * 0.3
    if name == "shake":
        d = 0.5
        t = tvec(d)
        x = bandpass(noise(d), 800, 5000) * (0.5 + 0.5 * np.sin(2 * np.pi * 26 * t)) * np.sin(np.pi * t / d)
        return x * 0.4
    if name in ("lid_open", "fork_pick", "fork_plate", "spoon_clatter"):
        partials = {"lid_open": (520, 1310, 2470, 3900), "fork_pick": (2900, 4700, 6900), "fork_plate": (2500, 4100, 6300),
                    "spoon_clatter": (380, 950, 1600)}[name]
        dec = {"lid_open": 3.5, "fork_pick": 12, "fork_plate": 10, "spoon_clatter": 30}[name]
        t = tvec(0.9)
        x = sum(np.sin(2 * np.pi * f * t) / (i + 1) for i, f in enumerate(partials)) * np.exp(-t * dec)
        if name == "spoon_clatter":
            out = np.zeros(int(0.6 * SR))
            for k, g in enumerate((1, 0.6, 0.4)):
                j = int(k * 0.11 * SR)
                out[j:j + len(x)] += x[: len(out) - j] * g
            return out * 0.4
        return x * 0.3
    if name in ("noodle_rise", "noodle_boing", "gasp_boing", "delight_boing"):
        f0, f1, d = {"noodle_rise": (200, 700, 1.0), "noodle_boing": (180, 420, 0.4), "gasp_boing": (600, 250, 0.45),
                     "delight_boing": (400, 1400, 0.6)}[name]
        t = tvec(d)
        f = f0 * (f1 / f0) ** (t / d) * (1 + 0.06 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 3))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        return x * np.sin(np.pi * t / d) ** 0.5 * np.exp(-t * 1.5) * 0.35
    if name in ("noodle_squish", "noodle_slither", "chew"):
        d = {"noodle_squish": 0.4, "noodle_slither": 1.0, "chew": 0.55}[name]
        t = tvec(d)
        x = lowpass(noise(d), 900)
        am = (0.5 + 0.5 * np.sin(2 * np.pi * (9 if name != "chew" else 7) * t)) ** 3
        bub = np.sin(2 * np.pi * np.cumsum(300 + 200 * np.sin(2 * np.pi * 11 * t)) / SR) * 0.2
        return (x * 1.5 + bub) * am * np.sin(np.pi * t / d) * 0.5
    if name == "tomato_fall":
        x, t = sweep(260, 120, 0.15)
        return (x * np.exp(-t * 25) + lowpass(noise(0.15), 600) * np.exp(-t * 40) * 0.5) * 0.6
    if name == "slip_squeak":
        x, t = sweep(700, 1800, 0.35)
        return (x + 0.4 * np.sin(2 * np.pi * np.cumsum(np.full(len(t), 1.0)) / SR)) * np.sin(np.pi * t / 0.35) * 0.35
    if name == "pot_bong":
        t = tvec(1.6)
        x = sum(np.sin(2 * np.pi * f * t) * a * np.exp(-t * dcy) for f, a, dcy in
                ((185, 1.0, 2.0), (452, 0.5, 2.6), (781, 0.35, 3.4), (1210, 0.2, 4.5)))
        return x * np.minimum(1, t / 0.002) * 0.45
    if name == "double_take":
        out = np.zeros(int(0.4 * SR))
        for k in range(2):
            s, t = sweep(1500, 2200, 0.05)
            out[int(k * 0.1 * SR):int(k * 0.1 * SR) + len(s)] += s * np.exp(-t * 50)
        s, t = sweep(300, 1200, 0.15)
        out[int(0.2 * SR):int(0.2 * SR) + len(s)] += s * np.exp(-t * 10)
        return out * 0.35
    if name in ("sauce_plop",):
        x, t = sweep(500, 140, 0.25)
        return x * np.exp(-t * 14) * 0.6 + lowpass(noise(0.25), 500) * np.exp(-t * 30) * 0.3
    if name in ("cheese_sprinkle", "sparkle", "bow_ta_da"):
        d = 1.0
        out = np.zeros(int(d * SR))
        k = 14 if name != "cheese_sprinkle" else 20
        for i in range(k):
            f = RNG.uniform(3000, 7000) if name != "cheese_sprinkle" else RNG.uniform(5000, 9000)
            t = tvec(0.25)
            s = np.sin(2 * np.pi * f * t) * np.exp(-t * 25)
            j = int(RNG.uniform(0, 0.7) * SR)
            out[j:j + len(s)] += s
        return out * 0.12
    if name == "door_open":
        d = 0.8
        t = tvec(d)
        f = 300 + 120 * np.sin(2 * np.pi * 2 * t) + RNG.normal(0, 30, len(t))
        x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * (RNG.random(len(t)) > 0.5))
        x = bandpass(x, 400, 2500) * np.sin(np.pi * t / d) * 0.25
        click = woodblock(600, 0.6)
        x[: len(click)] += click
        return x
    if name == "surprise_sting":
        return crash(0.4, 0.8) * 0.8
    if name == "more_taps":
        out = np.zeros(int(0.8 * SR))
        s = fx("fork_plate")
        for k in range(4):
            j = int(k * 0.18 * SR)
            out[j:j + len(s)] += s[: len(out) - j] * 0.7
        return out
    return np.zeros(100)


def foley():
    tr = Track()
    pans = {"tomato_toss": 0.2, "catch_pop": 0.2, "noodle_rise": 0.25, "pot_bong": -0.4, "door_open": -0.5,
            "mom_steps": -0.4, "running_steps": -0.2}
    for (t, name, gain) in SFX_CUES:
        tr.add(fx(name), t, gain=gain, pan=pans.get(name, 0.0))
    return reverb(tr.stereo(), mix=0.1, rt=0.6)


def ambience():
    d = DURATION
    t = tvec(d)
    room = lowpass(noise(d), 500) * 0.02 + lowpass(noise(d), 3000) * 0.004
    hum = (np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)) * 0.003
    birds = np.zeros_like(t)
    for k in range(9):  # distant window birds (synthetic chirps, not voices)
        t0 = RNG.uniform(0.5, d - 1)
        for c in range(RNG.integers(2, 4)):
            s, tt = sweep(RNG.uniform(2500, 3500), RNG.uniform(4000, 5500), 0.06)
            j = int((t0 + c * 0.1) * SR)
            birds[j:j + len(s)] += s * np.sin(np.pi * tt / 0.06) * 0.012
    L = room + hum + birds
    R = np.roll(room, 2400) + hum + np.roll(birds, 480)
    return np.stack([L, R], axis=1)


def write_wav(path, st):
    from scipy.io import wavfile
    st = np.clip(st, -1, 1)
    wavfile.write(path, SR, (st * 32767).astype(np.int16))


def main():
    out = os.path.join(ROOT, "assets", "audio")
    os.makedirs(out, exist_ok=True)
    print("[audio] composing music ...", flush=True)
    mu = music()
    print("[audio] synthesizing foley ...", flush=True)
    fo = foley()
    print("[audio] ambience ...", flush=True)
    am = ambience()

    def norm(x, peak):
        return x * (peak / max(1e-9, np.max(np.abs(x))))

    mu = norm(mu, 0.6)
    fo = norm(fo, 0.75)
    am = norm(am, 0.08)
    # gentle fade in/out
    fade = np.ones(N)
    fade[: int(0.02 * SR)] = np.linspace(0, 1, int(0.02 * SR))
    fade[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR)) ** 0.5
    mix = (mu * 0.85 + fo * 0.75 + am) * fade[:, None]
    # soft-knee limiter
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix * 1.2) / np.tanh(1.2) if peak > 0.9 else mix
    mix = norm(mix, 0.89)
    write_wav(os.path.join(out, "music.wav"), mu)
    write_wav(os.path.join(out, "foley.wav"), fo)
    write_wav(os.path.join(out, "ambience.wav"), am)
    write_wav(os.path.join(out, "mix.wav"), mix)
    print(f"[audio] wrote music/foley/ambience/mix ({DURATION:.1f}s, {SR} Hz, peak {np.max(np.abs(mix)):.2f})")


if __name__ == "__main__":
    main()
