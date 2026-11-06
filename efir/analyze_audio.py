import numpy as np, wave, json
w=wave.open('audio.wav'); sr=w.getframerate(); n=w.getnframes(); ch=w.getnchannels()
x=np.frombuffer(w.readframes(n),dtype=np.int16).reshape(-1,ch).mean(1)/32768
hop=512; win=2048
frames=1+(len(x)-win)//hop
idx=np.arange(win)[None,:]+hop*np.arange(frames)[:,None]
S=np.abs(np.fft.rfft(x[idx]*np.hanning(win),axis=1))
f=np.fft.rfftfreq(win,1/sr)
t=np.arange(frames)*hop/sr
rms=np.sqrt((x[idx]**2).mean(1))
bass=S[:,(f>30)&(f<150)].sum(1)
L=np.log1p(S*10); flux=np.maximum(0,np.diff(L,axis=0)).sum(1); flux=np.r_[0,flux]
bflux=np.maximum(0,np.diff(np.log1p(bass)));bflux=np.r_[0,bflux]
# per 0.5s RMS
for s in np.arange(0,15,0.5):
    m=(t>=s)&(t<s+0.5); print(f"{s:4.1f} rms={rms[m].mean():.3f} bass={bass[m].mean():8.1f} flux={flux[m].mean():6.1f}")
# tempo via autocorr of flux in 0-10.3s
m=t<10.3; o=flux[m]-flux[m].mean(); ac=np.correlate(o,o,'full')[len(o)-1:]
fps=sr/hop; lags=np.arange(len(ac))/fps
best=[(60/lags[i],ac[i]) for i in range(1,len(ac)) if 60/lags[i]>60 and 60/lags[i]<200]
best.sort(key=lambda z:-z[1]); print('tempo cands',[ (round(a,1),round(b,1)) for a,b in best[:8]])
# onset peaks
pk=[i for i in range(2,len(flux)-2) if flux[i]==flux[i-2:i+3].max() and flux[i]>np.percentile(flux,85)]
print('onsets',[round(t[i],2) for i in pk])
json.dump({'t':t.tolist(),'rms':rms.tolist(),'bass':bass.tolist(),'flux':flux.tolist()},open('env.json','w'))
