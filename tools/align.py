#!/usr/bin/env python3
"""Forced alignment of lyrics/lyrics.txt against the vocal track with the GigaAM v2 CTC model.
Writes lyrics/timing.json (word-level timings; can be edited by hand) and lyrics/lyrics.lrc / .srt."""
import os, sys, json, re
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ctc import logprobs, viterbi, norm
VOC=os.path.join(ROOT,"work","voc16k.wav")
lines=[l.strip() for l in open(os.path.join(ROOT,"lyrics","lyrics.txt"),encoding="utf-8") if l.strip() and not l.startswith("#")]
END=float(sys.argv[1]) if len(sys.argv)>1 else 18.8   # vocals end before this time
lp,fr=logprobs(VOC); lp=lp[:int(END/fr)]
words=[]; chars=""
for li,l in enumerate(lines):
    for w in l.split():
        acc=w.startswith("*") or w.endswith("*")
        txt=w.replace("*","")
        n=norm(txt)
        if not n:  # punctuation like "—" sticks to previous word
            if words: words[-1]["text"]+=" "+txt
            continue
        words.append(dict(line=li,text=txt,accent=acc,i0=len(chars),i1=len(chars)+len(n))); chars+=n
score,al=viterbi(lp,chars)
for w in words:
    w["start"]=round(al[w["i0"]][0]*fr,3); w["end"]=round((al[w["i1"]-1][1]+1)*fr,3)
    # per-character onsets (for syllable highlighting)
    w["chars"]=[round(al[i][0]*fr-w["start"],3) for i in range(w["i0"],w["i1"])]
    del w["i0"],w["i1"]
out=[]
for li,l in enumerate(lines):
    ws=[{k:v for k,v in w.items() if k!="line"} for w in words if w["line"]==li]
    out.append(dict(text=l.replace("*",""),start=ws[0]["start"],end=ws[-1]["end"],words=ws))
json.dump(dict(score=round(float(score),1),lines=out),open(os.path.join(ROOT,"lyrics","timing.json"),"w"),ensure_ascii=False,indent=1)
def ts(t,sep): m,s=divmod(t,60); return f"{int(m):02d}:{s:06.3f}".replace(".",sep) if sep else f"{int(m):02d}:{s:05.2f}"
with open(os.path.join(ROOT,"lyrics","lyrics.lrc"),"w",encoding="utf-8") as f:
    for L in out: f.write(f"[{ts(L['start'],'')}]"+" ".join(f"<{ts(w['start'],'')}>{w['text']}" for w in L["words"])+"\n")
with open(os.path.join(ROOT,"lyrics","lyrics.srt"),"w",encoding="utf-8") as f:
    for i,L in enumerate(out,1): f.write(f"{i}\n00:{ts(L['start'],',')} --> 00:{ts(L['end']+0.3,',')}\n{L['text']}\n\n")
print("alignment score",score)
for L in out: print(f"{L['start']:6.2f}-{L['end']:6.2f}  {L['text']}")
