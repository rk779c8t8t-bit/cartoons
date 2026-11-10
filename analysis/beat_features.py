import numpy as np, subprocess, json, sys
sr=22050
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-f","f32le","-ac","1","-ar",str(sr),"-"],capture_output=True).stdout,np.float32)
hop=256; n=2048
nfr=(len(x)-n)//hop
w=np.hanning(n)
idx=np.arange(n)[None,:]+hop*np.arange(nfr)[:,None]
S=np.abs(np.fft.rfft(x[idx]*w,axis=1)).astype(np.float32)
f=np.fft.rfftfreq(n,1/sr)
fps=sr/hop
L=np.log1p(100*S)
flux=np.maximum(0,np.diff(L,axis=0)).sum(1); flux=np.r_[0,flux]
low=S[:,f<150].sum(1); lowflux=np.maximum(0,np.diff(np.log1p(low)));lowflux=np.r_[0,lowflux]
rms=np.sqrt((S**2).mean(1))
# tempo via autocorr on 40-100s
a,b=int(40*fps),int(116*fps)
o=flux[a:b]-flux[a:b].mean()
ac=np.correlate(o,o,'full')[len(o)-1:]
lags=np.arange(len(ac))/fps
bpms=60/lags[1:]; m=(bpms>60)&(bpms<200)
best=np.argmax(ac[1:][m]); print("tempo",bpms[m][best])
np.savez(sys.argv[2],flux=flux,lowflux=lowflux,low=low,rms=rms,fps=fps)
