import requests

class PexelsAPI:
    def __init__(self, api_key):
        self.base_url = "https://api.pexels.com/v1"
        self.headers = {"Authorization": api_key}
    
    def buscar_imagens(self, query, num=5):
        response = requests.get(f"{self.base_url}/search", headers=self.headers,
                                params={"query": query, "per_page": num}, timeout=30)
        if response.status_code == 200:
            return response.json()['photos']
        else:
            print("Erro ao buscar imagens:", response.status_code, response.text)
            return []

    def buscar_videos(self, query, num=5, orientation="portrait"):
        response = requests.get(f"{self.base_url}/videos/search", headers=self.headers,
                                params={"query": query, "per_page": num, "orientation": orientation}, timeout=30)
        if response.status_code == 200:
            videos = response.json()['videos']
            for video in videos:
                # Pega a versão com maior qualidade disponível (maior width)
                video['video_files'].sort(key=lambda x: x['width'], reverse=True)
                video['best_quality_url'] = video['video_files'][0]['link']  # Maior resolução disponível
            return videos
        else:
            print("Erro ao buscar vídeos:", response.status_code, response.text)
            return []

    def baixar_arquivo(self, url, destino):
        try:
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code == 200:
                with open(destino, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"Arquivo baixado: {destino}")
                return True
            else:
                print(f"Erro ao baixar arquivo: {url}")
                return False
        except Exception as e:
            print(f"Erro durante o download: {e}")
            return False
