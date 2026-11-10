import numpy as np, subprocess, sys
sr=22050
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-ss","54","-t","38","-f","f32le","-ac","2","-ar",str(sr),"-"],capture_output=True).stdout,np.float32).reshape(-1,2)
mid=x[:,0]+x[:,1]; side=x[:,0]-x[:,1]
hop=128;n=1024;w=np.hanning(n)
def spec(s):
  nfr=(len(s)-n)//hop; idx=np.arange(n)[None,:]+hop*np.arange(nfr)[:,None]
  return np.abs(np.fft.rfft(s[idx]*w,axis=1))
M=spec(mid); f=np.fft.rfftfreq(n,1/sr); band=(f>250)&(f<3500)
L=np.log1p(50*M[:,band]); fl=np.r_[0,np.maximum(0,np.diff(L,axis=0)).sum(1)]
fps=sr/hop; fl=np.convolve(fl,np.ones(3)/3,'same'); fl/=np.percentile(fl,99.5)
P=60/148; ph=0.07
for i in range(2,len(fl)-2):
  t=54+i/fps
  if fl[i]>0.35 and fl[i]==fl[i-2:i+3].max() and float(sys.argv[2])<t<float(sys.argv[3]):
    g=(t-ph)/(P/4); print(f"{t:7.3f} {fl[i]:.2f} 16th:{g-round(g):+.2f} ", "#"*int(20*fl[i]))
