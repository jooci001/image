import sherpa_onnx, wave, numpy as np, sys
D='sherpa-onnx-zipformer-korean-2024-06-24'
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=f'{D}/encoder-epoch-99-avg-1.int8.onnx',decoder=f'{D}/decoder-epoch-99-avg-1.onnx',joiner=f'{D}/joiner-epoch-99-avg-1.int8.onnx',tokens=f'{D}/tokens.txt',num_threads=4)
for f in sys.argv[1:]:
    with wave.open(f) as w:
        sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
        if w.getnchannels()==2: x=x.reshape(-1,2).mean(1)
    s=rec.create_stream(); s.accept_waveform(sr,x); rec.decode_stream(s); print(f,'=>',s.result.text)
