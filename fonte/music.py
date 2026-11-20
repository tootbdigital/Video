import numpy as np, soundfile as sf
sr=44100; dur=30.0; n=int(sr*dur); out=np.zeros(n)
bpm=72; beat=60/bpm
midi=lambda m:440*2**((m-69)/12)
chords=[[48,52,55,60],[43,47,50,55],[45,48,52,57],[41,45,48,53]]  # C G Am F
def note(f,start,length,amp):
    i0=int(start*sr); L=int(length*sr); t=np.arange(L)/sr
    env=np.exp(-t*2.2)*np.minimum(1,t/0.01)
    w=np.sin(2*np.pi*f*t)+0.35*np.sin(4*np.pi*f*t)*np.exp(-t*4)+0.12*np.sin(6*np.pi*f*t)*np.exp(-t*6)
    seg=amp*env*w; e=min(n,i0+L); out[i0:e]+=seg[:e-i0]
bar=4*beat
for b in range(int(dur/bar)+1):
    ch=chords[b%4]; t0=b*bar
    for k in range(8):                       # arpejo em colcheias
        m=ch[[0,1,2,3,2,1,2,3][k]]+12
        if t0+k*beat/2<dur: note(midi(m),t0+k*beat/2,1.6,0.16)
    if t0<dur: note(midi(ch[0]-12),t0,bar,0.22)   # baixo
    if t0<dur:
        for m in ch[1:]: note(midi(m),t0,bar*0.9,0.05)  # pad
# final suave em C
t=np.arange(n)/sr
fade=np.minimum(1,t/1.5)*np.minimum(1,(dur-t)/2.0)
out*=fade; out/=np.max(np.abs(out))*1.0
sf.write('vid/music.wav',out*0.9,sr)
print('music ok')
