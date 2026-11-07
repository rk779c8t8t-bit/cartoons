# Build stylized character portraits (RGBA layers) from source frames.
import mediapipe as mp, numpy as np, cv2, json, sys
from mediapipe.tasks.python import vision, BaseOptions
S=sys.argv[1]
R={r['f'][:4]:r for r in json.load(open(S+'/faces.json')) if r['w']>110}
seg=vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=S+'/models/selfie_multiclass_256x256.tflite'),output_confidence_masks=True))
# palette gradient map: dark -> burgundy -> red -> gold -> cream
STOPS=[(0.0,(8,4,6)),(0.22,(48,8,14)),(0.42,(120,28,26)),(0.62,(196,108,52)),(0.82,(236,180,96)),(1.0,(255,236,190))]
def gmap(L):
    xs=[s[0] for s in STOPS]; out=np.zeros(L.shape+(3,),np.float32)
    for c in range(3): out[...,c]=np.interp(L,xs,[s[1][c] for s in STOPS])
    return out
def xdog(g,s=1.2,k=1.6,p=22,eps=0.0,phi=12):
    a=cv2.GaussianBlur(g,(0,0),s); b=cv2.GaussianBlur(g,(0,0),s*k)
    d=(1+p)*a-p*b
    return np.where(d>=eps,1.0,1+np.tanh(phi*(d-eps)))
def make(key,name,scale=2.4,up=5,yoff=0.12,cloth_mode='dark'):
    r=R[key]; im=cv2.imread(S+'/frames/'+r['f'])
    x0,y0,x1,y1=r['box'];w=r['w'];cx,cy=(x0+x1)/2,(y0+y1)/2+yoff*w;h=w*scale
    P=400;im=cv2.copyMakeBorder(im,P,P,P,P,cv2.BORDER_REPLICATE)
    c=im[int(cy-h/2+P):int(cy+h/2+P),int(cx-h/2+P):int(cx+h/2+P)]
    N=int(h*up)//2*2; c=cv2.resize(c,(N,N),interpolation=cv2.INTER_LANCZOS4)
    rgb=cv2.cvtColor(c,cv2.COLOR_BGR2RGB)
    m=seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,data=np.ascontiguousarray(rgb)))
    cm=[np.squeeze(x.numpy_view()).copy() for x in m.confidence_masks]
    bg=cm[0]; alpha=np.clip(1-bg,0,1); alpha=cv2.GaussianBlur(alpha,(0,0),N/400)
    alpha=np.clip((alpha-0.35)/0.3,0,1)
    nl,lab_,st,_=cv2.connectedComponentsWithStats((alpha>0.5).astype(np.uint8))
    if nl>1:
        big=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); keep=cv2.dilate((lab_==big).astype(np.uint8),np.ones((15,15),np.uint8))
        alpha=alpha*cv2.GaussianBlur(keep.astype(np.float32),(0,0),3)
    hair=cm[1]; skin=np.maximum(cm[2],cm[3]); cloth=np.maximum(cm[4],cm[5])
    # painterly smoothing
    sm=c.copy()
    sm=cv2.GaussianBlur(sm,(0,0),N/700)
    for _ in range(2): sm=cv2.bilateralFilter(sm,9,30,N/150)
    lab0=cv2.cvtColor(sm,cv2.COLOR_BGR2LAB); cl=cv2.createCLAHE(2.0,(4,4)); lab0[...,0]=cl.apply(lab0[...,0]); sm=cv2.cvtColor(lab0,cv2.COLOR_LAB2BGR)
    lab=cv2.cvtColor(sm,cv2.COLOR_BGR2LAB).astype(np.float32)
    L=lab[...,0]/255.
    # local contrast normalize inside person
    msk=alpha>0.5; lo,hi=np.percentile(L[msk],[3,99]); L=np.clip((L-lo)/(hi-lo),0,1)
    cb=cv2.GaussianBlur(cloth.astype(np.float32),(0,0),N/150)
    L=L*(1-0.7*cb)+cv2.GaussianBlur(L.astype(np.float32),(0,0),N/60)*0.7*cb
    # cel bands (soft posterize)
    L=cv2.GaussianBlur(L.astype(np.float32),(0,0),N/500)
    n=5; fr=L*n-np.floor(L*n); q=(np.floor(L*n)+np.clip((fr-0.92)/0.08,0,1))/n
    Lp=0.85*q+0.15*L
    col=gmap(np.clip(Lp,0,1))
    # clothes: push darker / redder
    cbm=np.clip(cv2.GaussianBlur(cloth.astype(np.float32),(0,0),N/300)*1.3,0,1)[...,None]
    if cloth_mode=='light':
        LS=[(0.0,(30,8,12)),(0.35,(110,50,40)),(0.6,(205,170,140)),(0.85,(242,228,206)),(1.0,(255,248,235))]
    else:
        LS=[(0.0,(6,3,5)),(0.4,(26,8,12)),(0.7,(70,16,22)),(1.0,(150,60,40))]
    cc=np.zeros_like(col)
    for c in range(3): cc[...,c]=np.interp(np.clip(Lp,0,1),[a for a,_ in LS],[b[c] for _,b in LS])
    col=col*(1-cbm)+cc*cbm
    # ink lines
    g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY).astype(np.float32)/255.
    e=1-xdog(g,s=N/650,p=30,phi=8)
    e=np.clip(e,0,1)*(alpha>0.5)*(1-cloth*0.5)
    e=cv2.GaussianBlur(e.astype(np.float32),(0,0),N/1200)
    col=col*(1-0.85*e[...,None])+np.array([22,4,8])*0.85*e[...,None]
    out=np.dstack([col,alpha*255]).astype(np.uint8)
    cv2.imwrite(f'{S}/chars/{name}.png',cv2.cvtColor(out,cv2.COLOR_RGBA2BGRA))
    cv2.imwrite(f'{S}/chars/{name}_lines.png',(e*255).astype(np.uint8))
    np.save(f'{S}/chars/{name}_parts.npy',np.stack([hair,skin,cloth]).astype(np.float16))
    # preview
    a=alpha[...,None]; bgc=np.array([20,6,10],np.float32)
    prev=col*a+bgc*(1-a); 
    prev=np.clip(prev,0,255)
    return cv2.resize(cv2.cvtColor(prev.astype(np.uint8),cv2.COLOR_RGB2BGR),(600,600))
tiles=[make('f017','toly_a',cloth_mode='light'),make('f018','toly_b',cloth_mode='light'),make('f022','toly_c',cloth_mode='light'),make('f099','em_a'),make('f041','em_b'),make('f089','em_d')]
cv2.imwrite(S+'/chars/preview.png',np.vstack([np.hstack(tiles[:3]),np.hstack(tiles[3:])]))
