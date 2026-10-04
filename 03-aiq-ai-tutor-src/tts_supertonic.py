import sherpa_onnx, numpy as np, wave
D='sherpa-onnx-supertonic-3-tts-int8-2026-05-11'
def make():
    c=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
        duration_predictor=f'{D}/duration_predictor.int8.onnx',text_encoder=f'{D}/text_encoder.int8.onnx',vector_estimator=f'{D}/vector_estimator.int8.onnx',
        vocoder=f'{D}/vocoder.int8.onnx',tts_json=f'{D}/tts.json',unicode_indexer=f'{D}/unicode_indexer.bin',voice_style=f'{D}/voice.bin'),num_threads=4))
    return sherpa_onnx.OfflineTts(c)
def gen(tts,text,sid,speed=1.0,steps=10):
    g=sherpa_onnx.GenerationConfig(); g.sid=sid; g.num_steps=steps; g.speed=speed; g.extra["lang"]="ko"
    a=tts.generate(text,g); return np.array(a.samples,np.float32), a.sample_rate
def save(f,s,sr):
    with wave.open(f,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(s,-1,1)*32767).astype(np.int16).tobytes())
def f0(s,sr):
    fr=int(.04*sr); hop=fr//2; vals=[]
    for i in range(0,len(s)-fr,hop):
        x=s[i:i+fr]; 
        if np.sqrt((x**2).mean())<0.03: continue
        x=x-x.mean(); c=np.correlate(x,x,'full')[fr-1:]
        lo,hi=int(sr/400),int(sr/70); k=lo+np.argmax(c[lo:hi])
        if c[k]>0.3*c[0]: vals.append(sr/k)
    return np.median(vals) if vals else 0
