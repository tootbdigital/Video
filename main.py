import os
import sys
import math
import datetime
import shutil
from dotenv import load_dotenv
from src.pexels import PexelsAPI
from src.pixabay import PixabayAPI
from src.googleVoice import GoogleVoice
from src.videomaker import VideoMaker
from src.uploadYoutube import YouTubeUploader
from src.uploadTiktok import TikTokUploader
from src.roteiroProcessor import RoteiroProcessor
from src.roteiro import find_value

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
SCRIPT_PATH = os.getenv("SCRIPT_PATH", "scripts")
MUSIC_PATH = os.getenv("MUSIC_PATH", os.path.join("musics", "musica.mp3"))
ENABLE_TIKTOK = os.getenv("ENABLE_TIKTOK", "1").lower() not in ("0", "false", "no")

SCRIPT_BACKUP_PATH = "script_backup"
OUTPUT_BACKUP_PATH = "output_backup"
TIKTOK_PENDING_PATH = "tiktok_pendente"  # vídeos já no YouTube cujo upload no TikTok falhou


def recriar_pasta(path):
    """Apaga e recria a pasta, evitando mídia de roteiros anteriores."""
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"Error: The folder '{SCRIPT_PATH}' was not found.")
        sys.exit(1)

    print("\n🔧 Testing YouTube environment")
    if not YouTubeUploader().testar_ambiente():
        print("\n🆘 YouTube upload test failed in `main.py`.")
        sys.exit(1)
    print("\n🔧✅ YouTube test passed in `main.py`.")

    # TikTok é opcional: se falhar, os vídeos seguem só para o YouTube.
    tiktok_ativo = ENABLE_TIKTOK
    if tiktok_ativo:
        print("\n🔧 Testing TikTok environment\n")
        if TikTokUploader().start_browser_test():
            print("\n🔧✅ TikTok test passed in `main.py`.")
        else:
            print("\n⚠️ TikTok test failed; continuing with YouTube only.")
            tiktok_ativo = False

    print("\n🔧 Testing Google Voice environment")
    if not GoogleVoice().testar_ambiente():
        print("\n🆘 Google Voice test failed in `main.py`.")
        sys.exit(1)
    print("\n🔧✅ Google Voice test passed in `main.py`.")

    print("\n📰 Splitting scripts")
    processor = RoteiroProcessor(os.path.join(SCRIPT_PATH, "roteiro.txt"))
    processor.processar()
    processor.exportar(SCRIPT_PATH)
    print("📰 Scripts processed\n")

    print("📹 Starting video generation\n\n")
    resultados = {}
    for arquivo in sorted(os.listdir(SCRIPT_PATH)):
        roteiro_path = os.path.join(SCRIPT_PATH, arquivo)
        if arquivo == "roteiro.txt" or not arquivo.endswith(".txt") or not os.path.isfile(roteiro_path):
            continue

        print(f"\nGenerating video for {arquivo}")
        try:
            resultados[arquivo] = processar_um_roteiro(arquivo, roteiro_path, tiktok_ativo)
        except Exception as e:
            # Um roteiro com erro não pode derrubar nem contaminar os próximos.
            print(f"\n🆘 Falha em {arquivo}: {type(e).__name__}: {e}")
            print("   O roteiro permanece em 'scripts' para nova tentativa.")
            resultados[arquivo] = "falhou"

    print("\n📋 Resumo:")
    for arquivo, status in resultados.items():
        print(f"  - {arquivo}: {status}")
    return all(s != "falhou" for s in resultados.values())


def processar_um_roteiro(arquivo, roteiro_path, tiktok_ativo):
    """Gera e publica um roteiro. Levanta exceção em qualquer falha de geração.

    O roteiro só vai para o backup se o upload no YouTube der certo.
    """
    titulo = find_value(roteiro_path, "TÍTULO:")
    hashtags = find_value(roteiro_path, "HASHTAGS:") or ""
    query = find_value(roteiro_path, "SEARCH:")
    if not titulo:
        raise ValueError("linha 'TÍTULO:' ausente ou vazia")
    if not query:
        raise ValueError("linha 'SEARCH:' ausente ou vazia")

    # Estado limpo: nada de áudio, clipes ou vídeo base do roteiro anterior.
    recriar_pasta(DOWNLOAD_DIR)
    recriar_pasta(os.path.join("output", "audio"))
    base_video = os.path.join("output", "final_video.mp4")
    if os.path.exists(base_video):
        os.remove(base_video)

    print(f"\n=== 🔊 Generating audio for file: {arquivo} ===")
    tempo_total = GoogleVoice().processar_roteiro(roteiro_path)  # levanta se falhar
    print(f"\n=== 🔊 Total audio generated: {tempo_total:.2f} seconds ===")

    tempo_total_desejado = math.ceil(tempo_total / 10) * 10
    tempo_maximo_por_video = 10

    print(f"\n=== 📼 Searching videos on Pexels: '{query}' ===")
    contador_videos = pexels(query, False, tempo_total_desejado, tempo_maximo_por_video)
    if contador_videos == 0:
        raise RuntimeError(f"Nenhum vídeo baixado do Pexels para '{query}'")
    print("\n=== 📼 Pexels video search completed! ===")

    print("\n=== 📼 Generating base video ===")
    videomaker = VideoMaker()
    videomaker.criar_video(DOWNLOAD_DIR, MUSIC_PATH, tempo_total_desejado=tempo_total_desejado)

    print("\n=== 📼 Generating video with voice and text ===")
    video_path = os.path.join("output", f"{arquivo}.mp4")
    if os.path.exists(video_path):
        os.remove(video_path)
    videomaker.adicionar_texto_e_audio(base_video, output_file=f"{arquivo}.mp4", script_file=roteiro_path)
    if not os.path.exists(video_path):
        raise RuntimeError(f"Vídeo final não foi gerado: {video_path}")
    print("\n=== 📼 Video with voice and text generated ===")

    print("\n=== 🟦 Authenticating YouTube ===")
    youtube = YouTubeUploader()
    youtube.authenticate()

    last_date = youtube.get_last_scheduled_video_date()
    base_time = last_date + datetime.timedelta(seconds=1) if last_date else None
    next_schedule = youtube.generate_schedule(1, start_time=base_time)[0]

    print("\n=== ⬆️ Starting YouTube upload ===")
    if not youtube.upload_single_video(video_path, titulo, hashtags, scheduled_time=next_schedule):
        raise RuntimeError("upload no YouTube falhou")
    print("⬆️✅ Upload successful on YouTube!")
    status = "youtube ok"

    tiktok_ok = True
    if tiktok_ativo:
        print("\n=== ⬆️ Starting TikTok upload ===")
        description_tiktok = f"{titulo}\n{hashtags}".strip()
        tiktok_ok = TikTokUploader().upload_video_to_tiktok(
            video_file=video_path, description=description_tiktok, scheduled_time=next_schedule)
        if tiktok_ok:
            print("⬆️✅ Upload scheduled successfully on TikTok!")
            status += " + tiktok ok"
        else:
            print("⬆️🆘 TikTok upload failed (YouTube já publicado).")
            status += f" / tiktok FALHOU (vídeo em '{TIKTOK_PENDING_PATH}')"

    # YouTube ok => o roteiro está consumido e o vídeo é arquivado.
    destino_video = OUTPUT_BACKUP_PATH if tiktok_ok else TIKTOK_PENDING_PATH
    os.makedirs(destino_video, exist_ok=True)
    os.makedirs(SCRIPT_BACKUP_PATH, exist_ok=True)
    shutil.move(video_path, os.path.join(destino_video, os.path.basename(video_path)))
    shutil.move(roteiro_path, os.path.join(SCRIPT_BACKUP_PATH, arquivo))
    return status


def pixabay(query, buscar_imagens, tempo_total_desejado, tempo_maximo_por_video, contador_videos=0):
    pixabay = PixabayAPI(PIXABAY_API_KEY)

    # Search for images if necessary
    if buscar_imagens:
        imagens = pixabay.buscar_imagens(query, num=3, orientation="vertical")
        print("Images Found on Pixabay:")
        for img in imagens:
            print(f"URL: {img['pageURL']}, Tags: {img['tags']}")

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        print("\nDownloading found images:")
        for i, img in enumerate(imagens):
            url = img['largeImageURL']
            destino = os.path.join(DOWNLOAD_DIR, f"imagem_{i+1}.jpg")
            pixabay.baixar_arquivo(url, destino)

    videos = pixabay.buscar_videos(query, num=50)
    print("\nVideos Found on Pixabay:")
    tempo_acumulado = 0

    for vid in videos:
        if tempo_acumulado >= tempo_total_desejado:
            print("Desired total time reached for Pixabay.")
            break

        duracao = vid['duration']
        if duracao > 200:
            continue

        if duracao > tempo_maximo_por_video:
            duracao = tempo_maximo_por_video

        tempo_acumulado += duracao
        contador_videos += 1
        print(f"URL: {vid['pageURL']}, Duration: {vid['duration']} seconds, Considered: {duracao} seconds")

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        print("\nDownloading found video:")
        url = vid['videos']['medium']['url']
        destino = os.path.join(DOWNLOAD_DIR, f"video_{contador_videos}.mp4")
        pixabay.baixar_arquivo(url, destino)

    return contador_videos


def escolher_arquivo_pexels(video_files, largura_max=1080):
    """Maior mp4 com largura <= largura_max (a tela final é 1080 de largura);
    se nenhum couber, o menor disponível. Evita baixar 4K à toa."""
    mp4 = [f for f in video_files if f.get("file_type", "video/mp4") == "video/mp4"] or video_files
    cabem = [f for f in mp4 if 0 < (f.get("width") or 0) <= largura_max]
    if cabem:
        return max(cabem, key=lambda f: f["width"])
    return min(mp4, key=lambda f: f.get("width") or 0)


def pexels(query, buscar_imagens, tempo_total_desejado, tempo_maximo_por_video, contador_videos=0):
    pexels = PexelsAPI(PEXELS_API_KEY)

    if buscar_imagens:
        imagens = pexels.buscar_imagens(query, num=3)
        print("Images Found on Pexels:")
        for img in imagens:
            print(f"URL: {img['url']}, Photographer: {img['photographer']}")

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        print("\nDownloading found images:")
        for i, img in enumerate(imagens):
            url = img['src']['original']
            destino = os.path.join(DOWNLOAD_DIR, f"imagem_{i+1}.jpg")
            pexels.baixar_arquivo(url, destino)

    videos = pexels.buscar_videos(query, num=50, orientation="portrait")
    tempo_acumulado = 0

    for vid in videos:
        if tempo_acumulado >= tempo_total_desejado:
            print("Desired total time reached for Pexels.")
            break

        duracao = vid['duration']
        if duracao > 200:
            continue

        if duracao > tempo_maximo_por_video:
            duracao = tempo_maximo_por_video

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        print("\nDownloading found video:")
        url = escolher_arquivo_pexels(vid['video_files'])['link']
        destino = os.path.join(DOWNLOAD_DIR, f"video_{contador_videos + 1}.mp4")
        # Só conta o clipe se o download realmente deu certo.
        if not pexels.baixar_arquivo(url, destino):
            continue
        contador_videos += 1
        tempo_acumulado += duracao
        print(f"URL: {vid['url']}, Duration: {vid['duration']} seconds, Considered: {duracao} seconds")

    return contador_videos


if __name__ == "__main__":
    ok = main()
    print("\n🔚 Finished!\n")
    sys.exit(0 if ok else 1)
