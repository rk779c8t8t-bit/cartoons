"""Align user-provided lyrics to ASR token timestamps -> timing.json"""
import json, re, numpy as np
OFFSET = 61.94  # chorus 2 starts 61.94 s after chorus 1 (measured by audio similarity)
TRANS = str.maketrans({"ё":"е","i":"а","p":"п","h":"х","o":"о","n":"н","e":"е","s":"с","a":"а","m":"м"})
def norm(s): return re.sub(r"[^а-я]", "", s.lower().translate(TRANS))

# --- lyrics -> words
lines=[]; sect=None
for raw in open("lyrics.txt", encoding="utf-8"):
    raw=raw.strip()
    if raw.startswith("#C"): sect=raw[1:]; ci=0; continue
    if raw=="#END": sect=None; continue
    if raw: lines.append({"text":raw,"sect":sect,"ci":(ci if sect else None)}); ci = ci+1 if sect else 0
words=[]
for li,L in enumerate(lines):
    for w in L["text"].split():
        if norm(w): words.append({"w":w,"line":li,"n":norm(w)})
lyr=""; owner=[]
for wi,w in enumerate(words): lyr+=w["n"]; owner+=[wi]*len(w["n"])

def align(asr_chars):
    a=lyr; b="".join(c for c,_ in asr_chars); n,m=len(a),len(b)
    G=-0.6  # gap
    S=np.full((n+1,m+1),-1e9,np.float32); S[0,:]=0; S[:,0]=np.arange(n+1)*G  # free leading asr gaps
    B=np.zeros((n+1,m+1),np.int8)
    bb=np.frombuffer(b.encode("utf-32-le"),np.uint32)
    for i in range(1,n+1):
        sub=np.where(bb==ord(a[i-1]),1.0,-0.8).astype(np.float32)
        diag=S[i-1,:-1]+sub; up=S[i-1,1:]+G
        row=np.maximum(diag,up); Bi=np.where(diag>=up,0,1).astype(np.int8)
        # left moves (skip asr chars) sequential: cheap gap for ASR insertions
        Srow=np.empty(m+1,np.float32); Srow[0]=S[i,0]; Brow=np.zeros(m+1,np.int8)
        for j in range(1,m+1):
            l=Srow[j-1]-0.3
            if row[j-1]>=l: Srow[j]=row[j-1]; Brow[j]=Bi[j-1]
            else: Srow[j]=l; Brow[j]=2
        S[i]=Srow; B[i]=Brow
    i,j=n,int(np.argmax(S[n])); match={}
    while i>0 and j>0:
        k=B[i,j]
        if k==0:
            if a[i-1]==b[j-1]: match[i-1]=asr_chars[j-1][1]
            i-=1;j-=1
        elif k==1: i-=1
        else: j-=1
    return match

anch={}
for f in ["toks.json","toks_voc.json","toks_6.json"]:
    chars=[]
    for ts,tk in json.load(open(f)):
        t=norm(tk); first=True
        for c in t: chars.append((c, ts if first else ts+0.04)); first=False
    for ci,t in align(chars).items():
        wi=owner[ci]
        # word start = first matched char of the word (adjust for chars before it)
        off=ci-owner.index(wi)
        anch.setdefault(wi,[]).append(t-off*0.05)
starts={wi:float(np.median(v)) for wi,v in anch.items() if len(v)>=2 or len(anch)<5}
# monotonic clean-up (longest increasing subsequence)
ks=sorted(starts); vals=[starts[k] for k in ks]
best=[1]*len(ks); prev=[-1]*len(ks)
for i in range(len(ks)):
    for j in range(i):
        if vals[j]<vals[i] and best[j]+1>best[i]: best[i]=best[j]+1; prev[i]=j
i=int(np.argmax(best)); keep=set()
while i>=0: keep.add(ks[i]); i=prev[i]
starts={k:starts[k] for k in keep}
# drop anchors inconsistent with their neighbours (local robust line fit)
pos0=np.cumsum([0]+[len(w["n"])+1 for w in words])
def clean(st):
    for _ in range(3):
        ks=sorted(st); bad=set()
        for i,k in enumerate(ks):
            nb=[j for j in ks[max(0,i-6):i+7] if j!=k]
            if len(nb)<4: continue
            sl=[(st[a]-st[b])/(pos0[a]-pos0[b]) for a in nb for b in nb if pos0[a]>pos0[b]]
            sl=float(np.median(sl)); ic=float(np.median([st[j]-sl*pos0[j] for j in nb]))
            if abs(st[k]-(sl*pos0[k]+ic))>0.9: bad.add(k)
        for k in bad: st.pop(k)
    # minimum speech rate: at most ~25 chars per second between anchors
    ks=sorted(st); keep=[ks[0]]
    for k in ks[1:]:
        p=keep[-1]
        if (st[k]-st[p]) >= 0.04*(pos0[k]-pos0[p]) - 0.05: keep.append(k)
    return {k:st[k] for k in keep}
starts=clean(starts)
# transfer between choruses
c1=[wi for wi,w in enumerate(words) if lines[w["line"]]["sect"]=="C1"]
c2=[wi for wi,w in enumerate(words) if lines[w["line"]]["sect"]=="C2"]
for a,b in zip(c1,c2):
    if a in starts and b not in starts: starts[b]=starts[a]+OFFSET
    elif b in starts and a not in starts: starts[a]=starts[b]-OFFSET
# inside each chorus lines 1-4 repeat the flow of lines 5-8 exactly 12.38 s earlier (measured)
REP=12.38
for base in (0.0, OFFSET):
    sect="C1" if base==0 else "C2"
    for k in range(1,5):
        src=[wi for wi,w in enumerate(words) if lines[w["line"]]["sect"]==sect and lines[w["line"]]["ci"]==k+4]
        dst=[wi for wi,w in enumerate(words) if lines[w["line"]]["sect"]==sect and lines[w["line"]]["ci"]==k]
        for d in dst: starts.pop(d,None)
        for a,b in zip(src,dst):
            if a in starts: starts[b]=starts[a]-REP
    first=[wi for wi,w in enumerate(words) if lines[w["line"]]["sect"]==sect and lines[w["line"]]["ci"]==0]
    starts[first[0]]=60.25+base; starts[first[1]]=60.85+base
# interpolate the rest by character position
known=sorted(starts); pos=np.cumsum([0]+[len(w["n"])+1 for w in words])
kp=[pos[k] for k in known]; kt=[starts[k] for k in known]
for wi,w in enumerate(words):
    t=starts.get(wi, np.interp(pos[wi],kp,kt))
    if wi<known[0]: t=kt[0]-0.07*(kp[0]-pos[wi])   # extrapolate words before first anchor
    w["t"]=round(float(t),3); w["anchored"]=wi in starts
json.dump({"lines":lines,"words":words},open("timing.json","w"),ensure_ascii=False,indent=1)
print("anchored",sum(w["anchored"] for w in words),"/",len(words))
for li,L in enumerate(lines):
    ws=[w for w in words if w["line"]==li]
    print(f"{ws[0]['t']:7.2f} {''.join('*' if w['anchored'] else '.' for w in ws)}")
