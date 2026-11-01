"""Clean background plate from the reference: keep its colours, gradients, cuts and
transitions, but remove the old baked-in text/stickers (masked normalized blur) and
the TikTok watermark. Output: bg.mp4 (576x324, 30 fps, 72 s)."""
import cv2, numpy as np, subprocess, sys
Y0,Y1=349,673; END=2160  # band rows, frames before the TikTok end card
def clean(f):
    b=f[Y0:Y1].astype(np.float32)/255
    small=cv2.resize(b,(288,162),interpolation=cv2.INTER_AREA)
    hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
    h=hsv[...,0]  # the reference backgrounds are never green/cyan -> those pixels are stickers
    m=((hsv[...,1]>0.42)&(hsv[...,2]>0.35)&((h<70)|(h>200))).astype(np.float32)
    m=cv2.erode(m,np.ones((5,5),np.uint8))
    k=(0,0); s=18
    num=cv2.GaussianBlur(small*m[...,None],k,s); den=cv2.GaussianBlur(m,k,s)[...,None]
    wide=cv2.GaussianBlur(small,k,40)
    out=np.where(den>0.02, num/np.maximum(den,1e-4), wide)
    out=cv2.GaussianBlur(out,k,4)
    return cv2.resize(out,(576,324),interpolation=cv2.INTER_CUBIC)
if __name__=="__main__":
    SRC=sys.argv[1]; OUT=sys.argv[2] if len(sys.argv)>2 else "bg.mp4"
    c=cv2.VideoCapture(SRC)
    p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s","576x324","-r","30","-i","-",
        "-c:v","libx264","-crf","12","-preset","medium","-pix_fmt","yuv420p",OUT],stdin=subprocess.PIPE)
    for i in range(END):
        ok,f=c.read()
        if not ok: break
        p.stdin.write((np.clip(clean(f),0,1)*255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
