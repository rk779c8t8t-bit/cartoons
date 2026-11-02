import json, sys
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2] if len(sys.argv) > 2 else "small", device="cpu", compute_type="int8", cpu_threads=4)
import librosa
audio, _ = librosa.load(sys.argv[1], sr=16000, mono=True)
segs, info = m.transcribe(audio, language="ru", word_timestamps=True, vad_filter=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
    pass
json.dump(out, open("transcript.json","w"), ensure_ascii=False, indent=1)
