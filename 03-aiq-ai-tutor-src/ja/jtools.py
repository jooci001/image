import sherpa_onnx, numpy as np, wave
TD='/tmp/claude-0/-home-user-image/488c813d-a7f5-5e16-a04d-8330f48fef73/scratchpad/sherpa-onnx-supertonic-3-tts-int8-2026-05-11'
AD='/tmp/claude-0/-home-user-image/488c813d-a7f5-5e16-a04d-8330f48fef73/scratchpad/dl_ja/sherpa-onnx-zipformer-ja-reazonspeech-2024-08-01'
def make_tts():
    c=sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
        duration_predictor=f'{TD}/duration_predictor.int8.onnx',text_encoder=f'{TD}/text_encoder.int8.onnx',vector_estimator=f'{TD}/vector_estimator.int8.onnx',
        vocoder=f'{TD}/vocoder.int8.onnx',tts_json=f'{TD}/tts.json',unicode_indexer=f'{TD}/unicode_indexer.bin',voice_style=f'{TD}/voice.bin'),num_threads=4))
    return sherpa_onnx.OfflineTts(c)
def gen(tts,text,sid,speed=1.0,steps=12):
    g=sherpa_onnx.GenerationConfig(); g.sid=sid; g.num_steps=steps; g.speed=speed; g.extra["lang"]="ja"
    a=tts.generate(text,g); return np.array(a.samples,np.float32), a.sample_rate
def make_asr():
    return sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{AD}/encoder-epoch-99-avg-1.int8.onnx',decoder=f'{AD}/decoder-epoch-99-avg-1.onnx',joiner=f'{AD}/joiner-epoch-99-avg-1.int8.onnx',tokens=f'{AD}/tokens.txt',num_threads=4)
def asr(rec,s,sr):
    st=rec.create_stream(); st.accept_waveform(sr,s); rec.decode_stream(st); return st.result.text
def save(f,s,sr):
    with wave.open(f,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(s,-1,1)*32767).astype(np.int16).tobytes())
def f0(s,sr):
    fr=int(.04*sr); hop=fr//2; v=[]
    for i in range(0,len(s)-fr,hop):
        x=s[i:i+fr]
        if np.sqrt((x**2).mean())<0.03: continue
        x=x-x.mean(); c=np.correlate(x,x,'full')[fr-1:]; lo,hi=int(sr/400),int(sr/70); k=lo+np.argmax(c[lo:hi])
        if c[k]>0.3*c[0]: v.append(sr/k)
    return np.median(v) if v else 0
