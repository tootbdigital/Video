import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
IMG = sys.argv[1]; OUT = sys.argv[2]; TMP = sys.argv[3]
os.makedirs(TMP, exist_ok=True)
W, H = 1280, 720
f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
scenes = [
 ("0:00  GANCHO", "Ovo de dinossauro rachando (1o segundo)", "Theo: \"Olha... está rachando!\""),
 ("0:04  MISSÃO", "Chip abre o portal do tempo", "Chip: \"Missão do dia: fazer um Short incrível.\""),
 ("0:08  CHEGADA", "Vale dos dinossauros, herbívoro ao fundo", "Theo: \"Uau! Olha o tamanho dessas árvores!\""),
 ("0:12  O ERRO", "Theo fala sem parar; o ovo racha atrás dele", "Chip: \"Theo... atrás de você.\""),
 ("0:16  O ACERTO", "Filhote Tri sai do ovo; Theo se vira rindo", "Theo: \"Funciona mesmo! O melhor momento primeiro!\""),
]
src = Image.open(IMG).convert("RGB")
bg = src.resize((W, H)).filter(ImageFilter.GaussianBlur(30))
fg = src.copy(); fg.thumbnail((W, 560))
segs = []
for i, (tag, desc, line) in enumerate(scenes):
    c = bg.copy(); c.paste(fg, ((W - fg.width)//2, 0))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 560, W, H], fill=(10, 14, 30))
    d.text((40, 572), f"ANIMATIC DE TIMING  |  {tag}", font=f_small, fill=(120, 220, 255))
    d.text((40, 612), desc, font=f_big, fill=(255, 255, 255))
    d.text((40, 664), line, font=f_small, fill=(255, 200, 120))
    p = f"{TMP}/s{i}.png"; c.save(p)
    o = f"{TMP}/s{i}.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",p,"-t","4",
      "-vf","scale=1920:1080,zoompan=z='min(zoom+0.0006,1.08)':d=96:s=1280x720:fps=24,format=yuv420p",
      "-r","24","-c:v","libx264",o], check=True)
    segs.append(o)
lst = f"{TMP}/list.txt"
open(lst,"w").write("".join(f"file '{s}'\n" for s in segs))
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",lst,"-c","copy",OUT], check=True)
