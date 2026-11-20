import soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
lines = [
 "Quando você chegou, o mundo inteiro coube na sua mão.",
 "Aprendi a soltar... sem nunca deixar de te segurar.",
 "Você aprendeu a voar.",
 "E nas noites de medo, eu sou o seu abrigo.",
 "Cada passo seu me leva junto.",
 "Te amo, minha filha.",
]
for i,t in enumerate(lines,1):
    s,sr = k.create(t, voice="pf_dora", speed=0.88, lang="pt-br")
    sf.write(f"v{i}.wav", s, sr)
    print(i, round(len(s)/sr,2), "s", sr)
