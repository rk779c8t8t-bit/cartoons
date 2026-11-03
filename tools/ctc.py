import os
import kaldi_native_fbank as knf, numpy as np, onnxruntime as ort, soundfile as sf, sys
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","models")+"/"
D=D+"sherpa-onnx-nemo-ctc-giga-am-v2-russian-2025-04-19/"
def feats(a):
    o=knf.FbankOptions(); fo=o.frame_opts; fo.dither=0; fo.remove_dc_offset=False; fo.preemph_coeff=0; fo.window_type="hann"; fo.round_to_power_of_two=False
    o.mel_opts.low_freq=0; o.mel_opts.high_freq=8000; o.mel_opts.num_bins=64
    f=knf.OnlineFbank(o); f.accept_waveform(16000,a); f.input_finished()
    return np.stack([f.get_frame(i) for i in range(f.num_frames_ready)]).astype(np.float32)
tok={}
for l in open(D+"tokens.txt",encoding="utf-8"):
    p=l.rstrip("\n").split(" ")
    if len(p)==2 and p[0]=="" : tok[" "]=int(p[1])
    elif len(p)==2: tok[p[0]]=int(p[1])
    else: tok[" "]=int(p[-1])
BLK=tok["<blk>"]
sess=ort.InferenceSession(D+"model.int8.onnx",providers=["CPUExecutionProvider"])
def logprobs(path):
    a,sr=sf.read(path,dtype="float32"); x=feats(a)
    lp=sess.run(None,{"features":x.T[None],"feature_lengths":np.array([x.shape[0]],dtype=np.int64)})[0][0]
    return lp, len(a)/sr/lp.shape[0]
def norm(t): return "".join(c for c in t.lower().replace("ё","е") if c in tok and c!=" ")
def viterbi(lp,text):
    ids=[tok[c] for c in text]; S=[BLK]
    for i in ids: S+= [i,BLK]
    T,N=lp.shape[0],len(S); NEG=-1e9
    dp=np.full((T,N),NEG); bp=np.zeros((T,N),int)
    dp[0,0]=lp[0,S[0]]; dp[0,1]=lp[0,S[1]]
    for t in range(1,T):
        for s in range(N):
            c=[(dp[t-1,s],s)]
            if s>0: c.append((dp[t-1,s-1],s-1))
            if s>1 and S[s]!=BLK and S[s]!=S[s-2]: c.append((dp[t-1,s-2],s-2))
            v,b=max(c); dp[t,s]=v+lp[t,S[s]]; bp[t,s]=b
    end=N-1 if dp[-1,N-1]>dp[-1,N-2] else N-2
    score=dp[-1,end]; path=[end]
    for t in range(T-1,0,-1): path.append(bp[t,path[-1]])
    path=path[::-1]
    # char start/end frames
    st={};en={}
    for t,s in enumerate(path):
        if s%2==1:
            k=s//2; st.setdefault(k,t); en[k]=t
    return score,[(st[k],en[k]) for k in range(len(ids))]
