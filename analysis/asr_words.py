import sys, json
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[2], device="cpu", compute_type="int8", cpu_threads=4)
import numpy as np, subprocess
audio=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-f","f32le","-ac","1","-ar","16000","-"],capture_output=True).stdout,np.float32)
segs, info = m.transcribe(audio, language="ru", word_timestamps=True, vad_filter=False, beam_size=5,
    initial_prompt="Ты слушаешь хуйню. Детка, да, дай мне подключиться на Bluetooth. Ги-ги-ги-ги-гикаю, да.")
out=[]
for s in segs:
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end,"p":w.probability} for w in s.words]})
json.dump(out, open(sys.argv[3],"w"), ensure_ascii=False, indent=1)
