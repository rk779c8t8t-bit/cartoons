import sys,glob
from PIL import Image, ImageDraw
fs=sorted(glob.glob(sys.argv[1]+'/*.png')); cols=4; w,h=480,270
rows=(len(fs)+cols-1)//cols; S=Image.new('RGB',(cols*w,rows*h))
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB').resize((w,h)); d=ImageDraw.Draw(im); d.text((6,4),f.split('/')[-1],fill=(0,255,0)); S.paste(im,((i%cols)*w,(i//cols)*h))
S.save(sys.argv[2])
