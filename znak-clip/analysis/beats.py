import librosa, numpy as np, json, sys
y, sr = librosa.load(sys.argv[1], sr=22050, mono=True)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='time')
rms = librosa.feature.rms(y=y)[0]; t = librosa.times_like(rms, sr=sr)
json.dump({"tempo":float(np.atleast_1d(tempo)[0]),"beats":[float(b) for b in beats],"onsets":[float(o) for o in onsets],
  "rms_t":[float(x) for x in t[::4]],"rms":[float(x) for x in rms[::4]]}, open("beats.json","w"))
print("tempo", tempo, "nbeats", len(beats))
