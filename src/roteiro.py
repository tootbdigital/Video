"""Parser único do formato de roteiro (usado por TTS e pelo montador de vídeo).

Formato das narrações: linhas começando com "N. texto" (N = inteiro, seguido de
ponto e espaço). Linhas como "3.5 mil pessoas" NÃO são narração.
"""
import re

_NARRACAO = re.compile(r"^\s*\d+[.)]\s+(\S.*)$")
# Divide em vírgulas, exceto entre dígitos ("1,5 milhão", "R$ 1,000").
_VIRGULA = re.compile(r"(?<!\d),|,(?!\d)")


def dividir_partes(texto):
    return [p.strip() for p in _VIRGULA.split(texto) if p.strip()]


def parse_narracoes(script_path):
    """Retorna {id_sequencial: [partes]} a partir do arquivo de roteiro.

    Levanta FileNotFoundError se o arquivo não existir e ValueError se não
    houver nenhuma narração (evita gerar vídeo vazio em silêncio).
    """
    narracoes = {}
    with open(script_path, "r", encoding="utf-8") as f:
        for linha in f:
            m = _NARRACAO.match(linha.rstrip("\n"))
            if not m:
                continue
            partes = dividir_partes(m.group(1))
            if partes:
                narracoes[len(narracoes) + 1] = partes
    if not narracoes:
        raise ValueError(f"Nenhuma narração encontrada em {script_path}")
    return narracoes


def find_value(script_path, termo):
    """Valor da primeira linha que começa com `termo` (ex.: 'TÍTULO:') ou None."""
    with open(script_path, "r", encoding="utf-8") as f:
        for linha in f:
            if linha.startswith(termo):
                valor = linha.split(termo, 1)[1].strip()
                return valor or None
    return None
