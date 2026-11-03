#!/usr/bin/env python3
"""Audio analysis (tempo, beats, energy envelopes) + bundle with lyrics/timing.json into src/data.js."""
import os, json, numpy as np, librosa, subprocess
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
W=os.path.join(ROOT,"work"); os.makedirs(W,exist_ok=True)
SRC=os.path.join(ROOT,"src","audio","song.m4a")
wav=os.path.join(W,"song44.wav")
subprocess.run(["ffmpeg","-v","error","-y","-i",SRC,"-ar","44100",wav],check=True)
y,sr=librosa.load(wav,sr=22050,mono=True)
dur=len(y)/sr
tempo,beats=librosa.beat.beat_track(y=y,sr=sr,units="time")
FPS=30; hop=sr//FPS
rms=librosa.feature.rms(y=y,frame_length=2048,hop_length=hop)[0]
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=hop)); f=librosa.fft_frequencies(sr=sr,n_fft=2048)
low=S[f<160].sum(0); high=S[(f>4000)].sum(0)
onset=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop)
def nz(a): a=np.asarray(a,float); return np.round(a/(a.max()+1e-9),3).tolist()
timing=json.load(open(os.path.join(ROOT,"lyrics","timing.json"),encoding="utf-8"))
data=dict(duration=dur,fps=FPS,tempo=float(np.atleast_1d(tempo)[0]),beats=np.round(beats,3).tolist(),
          rms=nz(rms),low=nz(low),high=nz(high),onset=nz(onset),lines=timing["lines"])
open(os.path.join(ROOT,"src","data.js"),"w",encoding="utf-8").write("window.DATA="+json.dumps(data,ensure_ascii=False)+";\n")
print(f"duration {dur:.3f}s tempo {data['tempo']:.1f} BPM, {len(beats)} beats")
