import sherpa_onnx, soundfile as sf, numpy as np, json, sys
M=sys.argv[1]
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M+"/encoder.int8.onnx",decoder=M+"/decoder.int8.onnx",joiner=M+"/joiner.int8.onnx",tokens=M+"/tokens.txt",num_threads=4,decoding_method="modified_beam_search")
x,sr=sf.read(sys.argv[2]); W,STEP=float(sys.argv[4]),float(sys.argv[4])/2; toks=[]; t=0.0; dur=len(x)/sr
while t<dur:
    a=x[int(t*sr):int((t+W)*sr)].astype(np.float32)
    s=rec.create_stream(); s.accept_waveform(sr,a); rec.decode_stream(s); r=s.result
    lo=0 if t==0 else STEP/2; hi=STEP/2+STEP
    for tk,ts in zip(r.tokens,r.timestamps):
        if lo<=ts<hi: toks.append([round(t+ts,2),tk])
    t+=STEP
json.dump(toks,open(sys.argv[3],"w"),ensure_ascii=False)
line="";last=0
for ts,tk in toks:
    if ts-last>4 or len(line)>90: print(f"{last:6.1f} {line}"); line=f"[{ts:.1f}]"
    line+=tk; last=ts
print(line)
