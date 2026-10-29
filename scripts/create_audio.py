#!/usr/bin/env python3
"""Original music, foley and ambience for the short. No voices, no samples.

music.wav    – MIDI composed in code below, rendered with FluidSynth + FluidR3_GM soundfont (MIT licence)
foley.wav    – procedurally synthesised effects, placed on the shot timeline
ambience.wav – procedurally synthesised birds, breeze, rain, wind
Run: python3 scripts/create_audio.py [--force]
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from common_cfg import load_config, shot_starts  # noqa: E402

SR = 44100
DUR = 36.0
N = int(SR * DUR)
SOUNDFONTS = ["/usr/share/sounds/sf2/FluidR3_GM.sf2", "/usr/share/sounds/sf2/default-GM.sf2"]
rng = np.random.default_rng(2026)


# ============================================================== MIDI writer
class Midi:
    TPB = 480
    BPM = 80.0

    def __init__(self):
        self.tracks = {}

    def ticks(self, sec):
        return int(round(sec * self.BPM / 60.0 * self.TPB))

    def program(self, ch, prog, name=None):
        self.tracks.setdefault(ch, {"prog": prog, "ev": []})["prog"] = prog

    def note(self, ch, start, dur, pitch, vel=70):
        tr = self.tracks.setdefault(ch, {"prog": 0, "ev": []})
        tr["ev"].append((self.ticks(start), 1, 0x90 | ch, pitch, vel))
        tr["ev"].append((self.ticks(start + dur), 0, 0x80 | ch, pitch, 0))

    def cc(self, ch, t, num, val):
        tr = self.tracks.setdefault(ch, {"prog": 0, "ev": []})
        tr["ev"].append((self.ticks(t), 0, 0xB0 | ch, num, int(max(0, min(127, val)))))

    def chord(self, ch, start, dur, pitches, vel=60):
        for p in pitches:
            self.note(ch, start, dur, p, vel)

    @staticmethod
    def _vlq(v):
        out = [v & 0x7F]
        v >>= 7
        while v:
            out.append((v & 0x7F) | 0x80)
            v >>= 7
        return bytes(reversed(out))

    def save(self, path):
        chunks = []
        tempo = int(60_000_000 / self.BPM)
        t0 = b"\x00\xFF\x51\x03" + tempo.to_bytes(3, "big") + b"\x00\xFF\x2F\x00"
        chunks.append(b"MTrk" + struct.pack(">I", len(t0)) + t0)
        for ch, tr in sorted(self.tracks.items()):
            data = bytearray()
            if ch != 9:
                data += b"\x00" + bytes([0xC0 | ch, tr["prog"]])
            evs = sorted(tr["ev"], key=lambda e: (e[0], e[1]))
            last = 0
            for t, _, st, a, b in evs:
                data += self._vlq(t - last) + bytes([st, a, b])
                last = t
            data += b"\x00\xFF\x2F\x00"
            chunks.append(b"MTrk" + struct.pack(">I", len(data)) + bytes(data))
        hdr = b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), self.TPB)
        with open(path, "wb") as f:
            f.write(hdr + b"".join(chunks))


def n(name):
    """note name -> midi number, e.g. C4=60, F#3, Bb2"""
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    p = names[name[0]]
    i = 1
    if name[1] in "#b":
        p += 1 if name[1] == "#" else -1
        i = 2
    return 12 * (int(name[i:]) + 1) + p


def compose(path):
    m = Midi()
    PNO, CEL, STR, TREM, PIZZ, TIMP, HORN, FLUTE, XYL, BASS, DR = 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 9
    m.program(PNO, 0)      # acoustic grand piano
    m.program(CEL, 8)      # celesta (bells)
    m.program(STR, 48)     # string ensemble
    m.program(TREM, 44)    # tremolo strings
    m.program(PIZZ, 45)    # pizzicato
    m.program(TIMP, 47)    # timpani
    m.program(HORN, 60)    # french horn
    m.program(FLUTE, 73)   # flute
    m.program(XYL, 13)     # xylophone (playful 'giggle' figure instead of any voice)
    m.program(BASS, 42)    # cello
    E = 0.375  # eighth note at 80 bpm
    for ch, vol in ((PNO, 100), (CEL, 85), (STR, 80), (TREM, 70), (PIZZ, 80), (TIMP, 90), (HORN, 78), (FLUTE, 72), (XYL, 70), (BASS, 80)):
        m.cc(ch, 0, 7, vol)
        m.cc(ch, 0, 91, 70)  # reverb send

    def arp(t0, t1, notes, vel=48, ch=PNO):
        t, i = t0, 0
        while t < t1 - 1e-6:
            m.note(ch, t, E * 1.6, notes[i % len(notes)], vel)
            t += E
            i += 1

    def mel(seq, ch=PNO, vel=72):
        for t, d, p in seq:
            m.note(ch, t, d, n(p), vel)

    # --- 0–8 s: tender piano, a worried turn when the kids laugh
    arp(0.0, 3.0, [n("C3"), n("G3"), n("E4"), n("G3")])
    arp(3.0, 5.25, [n("A2"), n("E3"), n("C4"), n("E3")])
    mel([(0.0, 0.7, "E5"), (0.75, 0.7, "G5"), (1.5, 0.35, "A5"), (1.875, 0.35, "G5"), (2.25, 0.7, "E5"),
         (3.0, 0.7, "C5"), (3.75, 0.35, "D5"), (4.125, 0.35, "E5"), (4.5, 0.8, "D5")])
    m.chord(STR, 0.0, 3.0, [n("C3"), n("G3"), n("E4")], 38)
    m.chord(STR, 3.0, 2.3, [n("A2"), n("E3"), n("C4")], 38)
    # giggle figure (xylophone, staccato) – thoughtless laughter
    t = 5.3
    for p in ["G5", "E5", "G5", "E5", "A5", "F#5", "G5", "E5", "G5", "D#5"]:
        m.note(XYL, t, 0.08, n(p), 58)
        t += 0.15
    # anxious note: soft minor-second cluster + low F#
    m.chord(PNO, 5.3, 1.2, [n("B4"), n("C5")], 40)
    m.note(BASS, 5.3, 2.6, n("F#2"), 50)
    # sadness 6–8: iv minor
    m.chord(STR, 5.5, 2.5, [n("F3"), n("Ab3"), n("C4")], 46)
    mel([(6.0, 0.7, "Ab4"), (6.75, 0.7, "G4"), (7.5, 0.6, "F4")], vel=60)
    arp(6.0, 7.9, [n("F2"), n("C3"), n("Ab3"), n("C3")], vel=40)

    # --- 8–12 s: warm chords and bells (the umbrella)
    m.chord(STR, 8.0, 1.6, [n("F2"), n("A3"), n("C4"), n("F4")], 52)
    m.chord(STR, 9.6, 1.5, [n("E2"), n("G3"), n("C4"), n("E4")], 56)
    m.chord(STR, 11.1, 1.0, [n("G2"), n("B3"), n("D4"), n("G4")], 54)
    arp(8.0, 9.6, [n("F2"), n("C3"), n("A3"), n("C3")], vel=44)
    arp(9.6, 12.0, [n("C3"), n("G3"), n("E4"), n("G3")], vel=46)
    t = 9.83
    for p in ["C6", "E6", "G6", "C7", "G6", "E6"]:
        m.note(CEL, t, 0.6, n(p), 70)
        t += 0.12
    mel([(10.2, 0.4, "E5"), (10.6, 0.4, "D5"), (11.0, 0.4, "C5"), (11.4, 0.4, "D5"), (11.8, 0.5, "E5")], vel=70)
    mel([(10.2, 0.4, "E6"), (11.8, 0.5, "G6")], ch=CEL, vel=50)

    # --- 12–16 s: tension (wind, creak, crack, fall)
    m.chord(TREM, 12.0, 4.0, [n("A2"), n("E3")], 45)
    m.cc(TREM, 12.0, 11, 40)
    for i in range(24):
        m.cc(TREM, 12.0 + i * 0.065, 11, 40 + i * 3.5)  # crescendo to the crack
    t = 12.0
    while t < 13.5:
        m.note(PIZZ, t, 0.15, n("A2"), 62)
        m.note(PIZZ, t + E, 0.15, n("E3") if int((t - 12) / E) % 4 else n("A2"), 55)
        t += 2 * E
    for i in range(10):  # timpani roll into the impact
        m.note(TIMP, 13.55 + i * 0.045, 0.1, n("A2"), 40 + i * 6)
    m.note(TIMP, 14.03, 1.2, n("A2"), 112)
    m.chord(STR, 14.03, 0.5, [n("Bb3"), n("B3"), n("C4"), n("E4")], 85)
    m.note(BASS, 14.03, 1.8, n("A1"), 90)
    m.cc(TREM, 14.2, 11, 60)
    m.chord(TREM, 14.3, 1.7, [n("D3"), n("A3"), n("E4")], 40)
    for t in (14.9, 15.5):  # heartbeat
        m.note(TIMP, t, 0.2, n("D2"), 60)
        m.note(TIMP, t + 0.2, 0.2, n("D2"), 45)

    # --- 16–20 s: decision; pulse grows, ostinato starts when he runs
    for i, t in enumerate(np.arange(16.0, 18.4, 0.75)):
        m.note(TIMP, t, 0.2, n("A2"), 55 + i * 4)
    m.chord(STR, 16.0, 2.0, [n("A2"), n("E3"), n("C4")], 50)
    m.chord(STR, 18.0, 1.0, [n("F2"), n("C3"), n("A3")], 60)
    m.chord(STR, 19.0, 1.0, [n("G2"), n("D3"), n("B3")], 66)
    mel([(16.6, 0.5, "A4"), (17.2, 0.5, "C5"), (17.8, 0.9, "E5")], vel=62)
    t = 18.4
    k = 0
    while t < 20.0:
        root = n("F3") if t < 19.0 else n("G3")
        m.note(PIZZ, t, 0.12, root, 70)
        m.note(PIZZ, t + E / 2, 0.1, root + 7, 60)
        t += E
        k += 1

    # --- 20–24 s: rescue; driving eighths, heroic horn, emotional rise
    prog = [(20.0, ["A2", "E3", "A3", "C4"]), (21.0, ["F2", "C3", "F3", "A3"]), (22.0, ["C3", "G3", "C4", "E4"]), (23.0, ["G2", "D3", "G3", "B3"])]
    for i, (t0, ch_) in enumerate(prog):
        notes = [n(x) for x in ch_]
        m.chord(STR, t0, 1.0, notes, 62 + i * 6)
        arp(t0, t0 + 1.0, [notes[0], notes[2], notes[3], notes[2]], vel=56 + i * 5)
        m.note(BASS, t0, 1.0, notes[0] - 12, 70 + i * 5)
        for j in range(4):
            m.note(PIZZ, t0 + j * 0.25, 0.1, notes[1], 60 + i * 5)
    mel([(21.6, 0.35, "E4"), (22.0, 0.35, "G4"), (22.4, 0.35, "A4"), (22.8, 1.0, "C5"), (23.5, 0.5, "B4")], ch=HORN, vel=88)
    m.note(DR, 22.95, 1.0, 49, 52)  # soft crash when the rabbit is free (drum channel)
    m.note(TIMP, 22.95, 0.6, n("C3"), 80)

    # --- 24–32 s: light strings and soft piano (gratitude, reconciliation)
    prog2 = [(24.0, ["C3", "G3", "C4", "E4"]), (26.0, ["B2", "G3", "D4", "G4"]), (28.0, ["A2", "E3", "C4", "E4"]), (30.0, ["F2", "C3", "A3", "C4"])]
    for t0, ch_ in prog2:
        notes = [n(x) for x in ch_]
        m.chord(STR, t0, 2.0, notes[1:], 55)
        m.note(BASS, t0, 2.0, notes[0], 55)
        arp(t0, t0 + 2.0, [notes[0], notes[1], notes[3], notes[1]], vel=44)
    mel([(24.4, 0.7, "E5"), (25.1, 0.35, "D5"), (25.45, 0.35, "C5"), (25.8, 0.7, "D5"), (26.5, 1.2, "G5"),
         (28.0, 0.7, "E5"), (28.75, 0.35, "D5"), (29.1, 0.35, "C5"), (29.45, 0.7, "A4"), (30.2, 0.7, "C5"), (30.9, 1.0, "D5")], vel=66)
    mel([(28.0, 0.7, "E6"), (28.75, 0.35, "D6"), (29.1, 0.35, "C6"), (29.45, 0.7, "A5"), (30.2, 0.7, "C6"), (30.9, 1.0, "D6")], ch=FLUTE, vel=52)

    # --- 32–36 s: final memorable phrase (main motif resolved)
    m.chord(STR, 32.0, 1.0, [n("F3"), n("A3"), n("C4"), n("E4")], 56)
    m.chord(STR, 33.0, 1.0, [n("G3"), n("B3"), n("D4"), n("F4")], 58)
    m.chord(STR, 34.0, 1.9, [n("C3"), n("G3"), n("C4"), n("E4"), n("G4")], 60)
    m.note(BASS, 32.0, 1.0, n("F2"), 60)
    m.note(BASS, 33.0, 1.0, n("G2"), 60)
    m.note(BASS, 34.0, 1.9, n("C2"), 62)
    arp(32.0, 34.0, [n("F2"), n("C3"), n("A3"), n("C3")], vel=44)
    mel([(32.0, 0.35, "E5"), (32.375, 0.35, "D5"), (32.75, 0.35, "C5"), (33.125, 0.35, "D5"),
         (33.5, 0.45, "E5"), (33.95, 0.45, "G5"), (34.4, 1.5, "C6")], vel=74)
    t = 34.4
    for p in ["C6", "G6", "E6", "C7"]:
        m.note(CEL, t, 1.2, n(p), 55)
        t += 0.2
    m.save(path)


def render_music(mid, wav):
    sf = next((s for s in SOUNDFONTS if os.path.exists(s)), None)
    if not sf or not shutil.which("fluidsynth"):
        raise RuntimeError("fluidsynth / GM soundfont missing (sudo apt-get install fluidsynth fluid-soundfont-gm)")
    tmp = wav + ".raw.wav"
    subprocess.run(["fluidsynth", "-ni", "-g", "0.8", "-r", str(SR), "-F", tmp, sf, mid], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sr, x = wavfile.read(tmp)
    os.remove(tmp)
    x = x.astype(np.float32) / 32768.0
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    out = np.zeros((N, 2), np.float32)
    k = min(N, len(x))
    out[:k] = x[:k]
    # short fade-in, gentle fade-out of the last 0.6 s (no click)
    fi = int(0.05 * SR)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(0.6 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    return out


# ============================================================== DSP helpers
def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def noise(sec):
    return rng.standard_normal(int(sec * SR)).astype(np.float32)


def env(nsamp, a=0.005, d=0.1, shape=4.0):
    t = np.arange(nsamp) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-shape * np.maximum(0, t - a) / max(d, 1e-4))
    return e.astype(np.float32)


def place(buf, snd, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    snd = snd[: len(buf) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(snd), 0] += snd * gain * l * 1.41
    buf[i:i + len(snd), 1] += snd * gain * r * 1.41


# -------------------------------------------------------------- effects
def footstep(soft=0.5, wet=False, boot=True):
    L = int(0.12 * SR)
    x = noise(0.12)
    s = lp(x, 900 if boot else 1400) * env(L, 0.002, 0.03, 5)
    t = np.arange(L) / SR
    s += 0.6 * np.sin(2 * np.pi * (110 + rng.uniform(-15, 15)) * t) * env(L, 0.002, 0.025, 6)
    if wet:
        s += 0.35 * bp(noise(0.12), 1500, 6000) * env(L, 0.01, 0.05, 4)
    return s * soft


def creak(sec=0.5, f0=150):
    L = int(sec * SR)
    t = np.arange(L) / SR
    f = f0 * (1 + 0.12 * np.sin(2 * np.pi * 3 * t) + 0.04 * rng.standard_normal(L).cumsum() / np.sqrt(L))
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = (ph / (2 * np.pi)) % 1.0 * 2 - 1
    pulses = (np.sin(2 * np.pi * 18 * t) > 0.3).astype(np.float32)
    s = bp(saw * (0.4 + 0.6 * pulses), 400, 2400) * np.hanning(L)
    return s.astype(np.float32)


def crack():
    # dry wood snapping: a dense burst of tiny clicks + a mid 'snap', no harsh peak
    L = int(0.45 * SR)
    s = np.zeros(L, np.float32)
    for k in range(26):
        t = 0.004 * k ** 1.25 + rng.uniform(0, 0.004)
        i = int(t * SR)
        c = bp(noise(0.02), 900, 5000) * env(int(0.02 * SR), 0.0005, 0.004, 6) * (1 - k / 30)
        s[i:i + len(c)] += c[: max(0, L - i)]
    sn = bp(noise(0.12), 300, 2500) * env(int(0.12 * SR), 0.001, 0.03, 5)
    s[:len(sn)] += 0.8 * sn
    return s


def whoosh(sec, f0, f1, q=0.6):
    """Noise sweep: crossfade between fixed band-passes (continuous, click-free)."""
    L = int(sec * SR)
    x = noise(sec)
    bands = np.geomspace(f0, f1, 5)
    pos = np.linspace(0, len(bands) - 1, L)
    out = np.zeros(L, np.float32)
    for k, fc in enumerate(bands):
        w = np.clip(1 - np.abs(pos - k), 0, 1)
        out += bp(x, fc * (1 - q / 2), fc * (1 + q / 2)) * w
    return out * np.hanning(L).astype(np.float32)


def thud(sec=0.5, f=55, g=1.0):
    L = int(sec * SR)
    t = np.arange(L) / SR
    s = np.sin(2 * np.pi * f * t * (1 - 0.3 * t)) * env(L, 0.003, sec * 0.3, 4)
    s += 0.5 * lp(noise(sec), 400) * env(L, 0.002, 0.06, 5)
    return (s * g).astype(np.float32)


def twig_rattle(sec=0.6, density=60):
    L = int(sec * SR)
    s = np.zeros(L, np.float32)
    for _ in range(int(density * sec)):
        i = rng.integers(0, L - 800)
        c = bp(noise(0.015), 1500, 7000) * env(int(0.015 * SR), 0.0005, 0.003, 6)
        s[i:i + len(c)] += c * rng.uniform(0.2, 1) * (1 - i / L)
    return s


def knock(f1=320, f2=760, sec=0.12):
    L = int(sec * SR)
    t = np.arange(L) / SR
    return ((np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f2 * t)) * env(L, 0.001, 0.03, 5)).astype(np.float32)


def rustle(sec=0.4, lo=1500, hi=6000):
    L = int(sec * SR)
    x = bp(noise(sec), lo, hi)
    am = lp(np.abs(noise(sec)), 30)
    am /= am.max() + 1e-9
    return (x * am * np.hanning(L)).astype(np.float32)


def scrape(sec=0.9):
    L = int(sec * SR)
    x = bp(noise(sec), 700, 3200)
    t = np.arange(L) / SR
    jitter = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 11 * t + rng.uniform(0, 3)))
    return (x * jitter * np.hanning(L)).astype(np.float32)


def umbrella_open():
    w = whoosh(0.28, 600, 3000, 0.8) * 0.7
    pop = lp(noise(0.06), 900) * env(int(0.06 * SR), 0.001, 0.015, 5) * 1.2
    out = np.zeros(int(0.4 * SR), np.float32)
    out[:len(w)] += w
    i = int(0.24 * SR)
    out[i:i + len(pop)] += pop
    return out


def chirp_bird():
    sec = rng.uniform(0.06, 0.16)
    L = int(sec * SR)
    t = np.arange(L) / SR
    f0, f1 = rng.uniform(2800, 4200), rng.uniform(3500, 6000)
    f = f0 + (f1 - f0) * (t / sec) ** rng.uniform(0.5, 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + 0.2 * np.sin(2 * ph)) * np.sin(np.pi * t / sec) ** 2
    return s.astype(np.float32)


def bird_phrase():
    out = []
    for _ in range(rng.integers(2, 6)):
        out.append(chirp_bird())
        out.append(np.zeros(int(rng.uniform(0.03, 0.09) * SR), np.float32))
    return np.concatenate(out)


# ============================================================== builders
def shot_t(starts, shot, frame):
    return starts[shot - 1] / 30.0 + (frame - 1) / 30.0


def build_foley(cfg):
    st, _ = shot_starts(cfg)
    T = lambda s, f: shot_t(st, s, f)  # noqa: E731
    F = np.zeros((N, 2), np.float32)
    # S1 kitten's light steps (contacts every ~9 frames while walking 1..90)
    for f in range(1, 90, 9):
        place(F, footstep(0.35), T(1, f), 0.5, -0.2)
    # S2 crouch / clothes rustle
    place(F, rustle(0.5, 1200, 5000), T(2, 64), 0.25, -0.2)
    # S3 puppy's wet steps + umbrella
    for f in range(1, 38, 9):
        place(F, footstep(0.3, wet=True), T(3, f), 0.5, -0.4)
    place(F, umbrella_open(), T(3, 53), 0.9, -0.1)
    # S4 kids' steps, creak, crack, fall, thud, bounce, twigs, stepping back
    for f in range(1, 46, 9):
        for d, pan in ((0, -0.2), (3, 0.2), (5, -0.4), (7, 0.4)):
            place(F, footstep(0.25, wet=True), T(4, f + d), 0.35, pan)
    place(F, creak(0.35, 140), T(4, 33), 0.55, -0.5)
    place(F, creak(0.3, 170), T(4, 40), 0.6, -0.5)
    place(F, crack(), T(4, 46), 0.75, -0.4)
    place(F, whoosh(0.4, 300, 1200, 1.0), T(4, 50), 0.6, -0.2)
    place(F, twig_rattle(0.5, 50), T(4, 52), 0.35, -0.2)
    place(F, thud(0.6, 52, 1.0), T(4, 61), 0.9, 0.0)
    place(F, twig_rattle(0.8, 90), T(4, 61), 0.55, 0.1)
    place(F, thud(0.3, 70, 0.5), T(4, 65), 0.6, 0.0)
    for f in range(63, 80, 5):
        place(F, footstep(0.3, wet=True), T(4, f), 0.4, rng.uniform(-0.5, 0.5))
    # S5 backpack drop, running steps
    place(F, thud(0.25, 90, 0.5), T(5, 72), 0.6, -0.2)
    place(F, rustle(0.25), T(5, 70), 0.25, -0.2)
    for f in range(72, 105, 6):
        place(F, footstep(0.45, wet=True), T(5, f), 0.55, 0.2)
    # S6 board scrape, knock on rock, lever creaks, branch rustle, rabbit scurry, branch settles
    place(F, scrape(0.85), T(6, 4), 0.45, 0.2)
    place(F, knock(300, 720), T(6, 44), 0.7, 0.2)
    place(F, creak(0.7, 120), T(6, 56), 0.55, 0.25)
    place(F, creak(0.6, 135), T(6, 76), 0.5, 0.25)
    place(F, twig_rattle(1.0, 40), T(6, 60), 0.3, 0.3)
    for f in range(76, 112, 4):
        place(F, footstep(0.18, wet=False, boot=False), T(6, f), 0.35, 0.3)
    place(F, thud(0.4, 60, 0.6), T(6, 104), 0.7, 0.2)
    place(F, knock(260, 600), T(6, 105), 0.5, 0.2)
    # S7 rabbit runs up and hugs (cloth & fur), steps
    for f in range(4, 19, 5):
        place(F, footstep(0.25, boot=False), T(7, f), 0.4, 0.3)
    place(F, rustle(0.5, 800, 4000), T(7, 18), 0.4, 0.1)
    place(F, rustle(0.4, 600, 3000), T(7, 28), 0.3, 0.0)
    # S8 steps, cloth wiping, paw shake
    for f in range(2, 20, 8):
        place(F, footstep(0.3, wet=True), T(8, f), 0.4, -0.3)
        place(F, footstep(0.3, wet=True), T(8, f + 3), 0.4, 0.3)
    for f in range(28, 92, 6):
        place(F, rustle(0.13, 2000, 7000), T(8, f), 0.22, 0.25)
    place(F, thud(0.15, 120, 0.25), T(8, 62), 0.4, -0.1)
    # S9 group footsteps
    for f in range(1, 94, 10):
        for d, pan in ((0, 0.0), (2, -0.3), (4, 0.3), (6, -0.6), (8, 0.6)):
            place(F, footstep(0.2), T(9, f + d), 0.3, pan)
    return F


def build_ambience(cfg):
    A = np.zeros((N, 2), np.float32)
    t = np.arange(N) / SR

    def curve(points):
        xs, ys = zip(*points)
        return np.interp(t, xs, ys).astype(np.float32)

    # breeze bed (stereo decorrelated)
    for c in range(2):
        A[:, c] += lp(noise(DUR), 700)[:N] * 0.05
    # birds: morning, quieter in overcast, absent in rain/wind, return at the end
    bird_g = curve([(0, 1), (3.5, 1), (5, 0.4), (7.6, 0.25), (8.5, 0), (24, 0), (26, 0.6), (31, 1), (36, 1)])
    tt = 0.2
    while tt < DUR:
        g = bird_g[min(N - 1, int(tt * SR))]
        if g > 0.05:
            place(A, bird_phrase(), tt, 0.05 * g, rng.uniform(-0.8, 0.8))
        tt += rng.uniform(0.5, 1.6)
    # rain 7.6–12.4 s with drops; patter on the umbrella after it opens
    rain_g = curve([(0, 0), (7.6, 0), (8.2, 1), (11.6, 1), (12.4, 0), (36, 0)])
    for c in range(2):
        r = (0.6 * hp(noise(DUR), 3000)[:N] + 0.4 * bp(noise(DUR), 400, 2500)[:N]) * 0.16
        A[:, c] += r * rain_g
    tt = 7.7
    while tt < 12.3:
        d = bp(noise(0.02), 2500, 8000) * env(int(0.02 * SR), 0.0005, 0.005, 6)
        place(A, d, tt, 0.15 * rng.uniform(0.3, 1), rng.uniform(-1, 1))
        tt += rng.uniform(0.01, 0.05)
    tt = 9.9
    while tt < 12.3:  # drops on the umbrella canvas (softer, tonal)
        d = bp(noise(0.03), 900, 2200) * env(int(0.03 * SR), 0.001, 0.01, 6)
        place(A, d, tt, 0.18 * rng.uniform(0.3, 1), rng.uniform(-0.3, 0.2))
        tt += rng.uniform(0.03, 0.09)
    # wind 12–24 s with a strong gust at the branch break
    wind_g = curve([(0, 0), (11.8, 0), (12.6, 0.5), (13.4, 1.0), (14.5, 0.8), (16, 0.45), (20, 0.35), (24, 0.25), (26, 0.1), (36, 0.08)])
    for c in range(2):
        x = noise(DUR)[:N]
        lo, mid, hi = bp(x, 150, 450), bp(x, 300, 800), bp(x, 500, 1400)
        mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t + c)
        w = lo * (1 - mod) * (1 - wind_g) + mid * mod + hi * wind_g * 0.8
        A[:, c] += w * wind_g * 0.22
        A[:, c] += hp(noise(DUR), 2500)[:N] * wind_g * 0.035  # leaves
    # occasional drips after the rain
    tt = 12.5
    while tt < 24:
        place(A, knock(1800, 3200, 0.04) * 0.4, tt, 0.15, rng.uniform(-0.8, 0.8))
        tt += rng.uniform(0.4, 1.2)
    return A


def save(path, x):
    peak = float(np.max(np.abs(x))) or 1.0
    if peak > 0.89:
        x = x * (0.89 / peak)
    wavfile.write(path, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    return peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    out = os.path.join(ROOT, cfg["paths"]["audio"])
    os.makedirs(out, exist_ok=True)
    paths = {k: os.path.join(out, k + ".wav") for k in ("music", "foley", "ambience")}
    if not a.force and all(os.path.exists(p) for p in paths.values()):
        print("audio: all stems exist, reusing (use --force to rebuild)")
        return 0
    mid = os.path.join(out, "music.mid")
    compose(mid)
    music = render_music(mid, paths["music"])
    for name, x in (("music", music), ("foley", build_foley(cfg)), ("ambience", build_ambience(cfg))):
        pk = save(paths[name], x)
        print(f"audio: wrote {paths[name]} (raw peak {pk:.2f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
