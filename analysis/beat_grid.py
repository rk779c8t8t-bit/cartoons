import numpy as np,sys
d=np.load(sys.argv[1]); fl=d['flux']; lf=d['lowflux']; fps=float(d['fps']); rms=d['rms']
t=np.arange(len(fl))/fps
def interp(sig,ts): return np.interp(ts*fps,np.arange(len(sig)),sig)
best=None
for bpm in np.arange(144,152,0.01):
  P=60/bpm
  for ph in np.arange(0,P,0.005):
    ts=np.arange(ph+40,116,P)
    s=interp(fl,ts).mean()
    if best is None or s>best[0]: best=(s,bpm,ph)
print(best)
s,bpm,ph=best;P=60/bpm
# report bars 48..92
ts=np.arange(ph,129,P)
k=np.argmin(abs(ts-48))
fln=fl/np.percentile(fl,99); lfn=lf/np.percentile(lf,99); r=rms/np.percentile(rms,99)
for i in range(k,k+120):
  T=ts[i]; j=int(T*fps)
  sl=slice(max(0,j-3),j+4)
  print(f"{i:4d} {T:7.3f} flux{fln[sl].max():5.2f} low{lfn[sl].max():5.2f} rms{r[j]:5.2f}", "#"*int(10*lfn[sl].max()))
