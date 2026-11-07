import mediapipe as mp, numpy as np, cv2, glob, json, sys
S=sys.argv[1]
from mediapipe.tasks.python import vision, BaseOptions
lm=vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=S+'/models/face_landmarker.task'),num_faces=2,output_facial_transformation_matrixes=True))
res=[]
for f in sorted(glob.glob(S+'/frames/f*.png')):
    im=cv2.imread(f); rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
    r=lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb))
    for i,l in enumerate(r.face_landmarks):
        p=np.array([[q.x*576,q.y*576] for q in l])
        x0,y0=p.min(0);x1,y1=p.max(0)
        M=np.array(r.facial_transformation_matrixes[i]); yaw=np.degrees(np.arctan2(M[0,2],M[2,2]))
        g=cv2.cvtColor(im[int(max(0,y0)):int(y1),int(max(0,x0)):int(x1)],cv2.COLOR_BGR2GRAY)
        sharp=cv2.Laplacian(g,cv2.CV_64F).var() if g.size else 0
        res.append(dict(f=f.split('/')[-1],box=[float(x0),float(y0),float(x1),float(y1)],w=float(x1-x0),yaw=float(yaw),sharp=float(sharp)))
json.dump(res,open(S+'/faces.json','w'))
for r in res: print(r['f'],int(r['w']),round(r['yaw']),int(r['sharp']),[int(v) for v in r['box']])
