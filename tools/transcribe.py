#!/usr/bin/env python3
"""Черновое распознавание текста: Whisper turbo + GigaAM v2 (оффлайн, sherpa-onnx).
Результат — для сверки; итоговый текст правится вручную в lyrics/lyrics.txt."""
import os, sherpa_onnx, soundfile as sf
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
M=os.path.join(R,"models"); a,sr=sf.read(os.path.join(R,"work","voc16k.wav"),dtype="float32")
w=M+"/sherpa-onnx-whisper-turbo/"; g=M+"/sherpa-onnx-nemo-transducer-giga-am-v2-russian-2025-04-19/"
recs={"whisper":sherpa_onnx.OfflineRecognizer.from_whisper(encoder=w+"turbo-encoder.int8.onnx",decoder=w+"turbo-decoder.int8.onnx",tokens=w+"turbo-tokens.txt",language="",num_threads=4),
      "gigaam":sherpa_onnx.OfflineRecognizer.from_transducer(encoder=g+"encoder.int8.onnx",decoder=g+"decoder.onnx",joiner=g+"joiner.onnx",tokens=g+"tokens.txt",model_type="nemo_transducer",num_threads=4)}
for k,r in recs.items():
    s=r.create_stream(); s.accept_waveform(sr,a); r.decode_stream(s); print(k+":",s.result.text)
