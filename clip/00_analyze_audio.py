import librosa, numpy as np, sys
y,sr=librosa.load(sys.argv[1],sr=22050)
print('dur',len(y)/sr)
tempo,beats=librosa.beat.beat_track(y=y,sr=sr)
print('tempo',tempo,'beats',np.round(librosa.frames_to_time(beats,sr=sr),2))
on=librosa.onset.onset_detect(y=y,sr=sr,units='time',backtrack=False)
print('onsets',np.round(on,2))
rms=librosa.feature.rms(y=y,hop_length=2205)[0]
print('rms/0.1s',' '.join(f'{v:.2f}' for v in rms))
cent=librosa.feature.spectral_centroid(y=y,sr=sr,hop_length=11025)[0]
print('centroid/0.5s',np.round(cent).astype(int))
