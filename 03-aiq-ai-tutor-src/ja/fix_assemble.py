"""Replace clip 14 with a verified take, derive clip 15 from clip 0's brand phrase, and rebuild the track."""
import numpy as np, wave, re, sys
from jtools import *
def load(f):
    with wave.open(f) as w: return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768, w.getframerate()
def store(f,s,sr):
    with wave.open(f,'wb') as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(s,-1,1)*32767).astype(np.int16).tobytes())
tts=make_tts(); rec=make_asr()
for k in range(12):
    s,sr=gen(tts,"問いかけ、学び、積み重ねる。",0,speed=0.95,steps=12)
    nz=np.where(np.abs(s)>0.01)[0]; s=s[max(0,nz[0]-int(.03*sr)):nz[-1]+int(.12*sr)]
    P=np.zeros(sr,np.float32); t=asr(rec,np.concatenate([P,s,P]),sr); a=asr(rec,np.concatenate([P,s[:len(s)//2],P]),sr)
    if t=="問いかけ学び積み重ねる" and a.startswith("問いかけ") and len(s)/sr<=2.7: break
print('clip14', round(len(s)/sr,2), t, '|', a); store('nar_ja/14.wav',s,sr)
# clip 15 from clip 0: brand phrase ends at the longest pause in the first 55%
c0,sr=load('nar_ja/00.wav'); e=np.convolve(np.abs(c0),np.ones(1500)/1500,'same')
lo,hi=int(.8*sr),int(len(c0)*.55); quiet=e[lo:hi]<0.004
best=(0,0); run=0
for i,q in enumerate(quiet):
    run=run+1 if q else 0
    if run>best[0]: best=(run,i)
cut=lo+best[1]-best[0]//2
b=c0[:cut].copy(); f=int(.08*sr); b[-f:]*=np.linspace(1,0,f)
P=np.zeros(sr,np.float32); print('clip15', round(len(b)/sr,2), asr(rec,np.concatenate([P,b,P]),sr)); store('nar_ja/15.wav',b,sr)
starts=[float(m) for m in re.findall(r"^\s+\((\d+\.\d+),", open('narration_ja.py',encoding='utf-8').read(), re.M)]
tr=np.zeros(int(120*sr),np.float32)
for i,st in enumerate(starts):
    c,_=load(f'nar_ja/{i:02d}.wav'); i0=int(st*sr); tr[i0:i0+len(c)]+=c[:len(tr)-i0]
store(sys.argv[1],tr,sr); print('starts',len(starts))
