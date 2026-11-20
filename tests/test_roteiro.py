import pytest
from src.roteiro import dividir_partes, parse_narracoes, find_value


def test_virgula_entre_digitos_nao_divide():
    assert dividir_partes("custou R$ 1,5 milhão, e subiu") == ["custou R$ 1,5 milhão", "e subiu"]
    assert dividir_partes("em 2023, 2024 e 2025") == ["em 2023", "2024 e 2025"]


def _write(tmp_path, txt):
    p = tmp_path / "r.txt"
    p.write_text(txt, encoding="utf-8")
    return str(p)


def test_parse_ignora_linha_que_comeca_com_numero_decimal(tmp_path):
    p = _write(tmp_path, "TEMA: x\nNARRACAO:\n1. Olá, mundo\n3.5 mil pessoas foram\n2. Fim\n")
    assert parse_narracoes(p) == {1: ["Olá", "mundo"], 2: ["Fim"]}


def test_parse_sem_narracao_levanta(tmp_path):
    with pytest.raises(ValueError):
        parse_narracoes(_write(tmp_path, "TEMA: x\nsó texto\n"))


def test_parse_arquivo_inexistente_levanta(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_narracoes(str(tmp_path / "nao.txt"))


def test_find_value(tmp_path):
    p = _write(tmp_path, "TÍTULO: Meu título \nHASHTAGS:\nSEARCH: mar\n")
    assert find_value(p, "TÍTULO:") == "Meu título"
    assert find_value(p, "HASHTAGS:") is None
    assert find_value(p, "SEARCH:") == "mar"
    assert find_value(p, "XYZ:") is None
