"""Testes dos utilitários de tempo hh:mm:ss.cc (Tarefa T02)."""

import json
from pathlib import Path

import pytest

from cortesia.tempo import duracao_confere, segundos_para_tempo, tempo_para_segundos

FIXTURES = Path(__file__).parent / "fixtures"
GABARITO_PATH = FIXTURES / "gabarito_textos_c1_c7_c8.json"


def test_segundos_para_tempo_exemplos():
    """Critério 1: conversão de segundos para formato hh:mm:ss.cc com exemplos fixos."""
    assert segundos_para_tempo(0.08) == "00:00:00.08"
    assert segundos_para_tempo(109.40) == "00:01:49.40"
    assert segundos_para_tempo(1424.88) == "00:23:44.88"
    assert segundos_para_tempo(3600.0) == "01:00:00.00"
    assert segundos_para_tempo(59.999) == "00:01:00.00"


@pytest.mark.parametrize(
    "segundos",
    [
        0.0,
        0.08,
        1.25,
        59.0,
        59.99,
        60.0,
        109.40,
        1424.88,
        3600.0,
        7384.56,
    ],
)
def test_ida_e_volta(segundos: float):
    """Critério 2: ida e volta preserva o valor com 2 casas decimais."""
    formatado = segundos_para_tempo(segundos)
    recuperado = tempo_para_segundos(formatado)
    assert pytest.approx(recuperado, abs=1e-4) == round(segundos, 2)


@pytest.mark.parametrize(
    "texto_invalido",
    [
        "1:02",
        "00:01:49",
        "00:60:00.00",
        "00:00:60.00",
        "-00:01:00.00",
        "00:01:00.0",
        "00:01:00.000",
        "texto",
        "",
    ],
)
def test_tempo_para_segundos_invalidos(texto_invalido: str):
    """Critério 3: formatos inválidos levantam ValueError."""
    with pytest.raises(ValueError):
        tempo_para_segundos(texto_invalido)


def test_segundos_negativos_levantam_erro():
    """Critério 3: segundos negativos levantam ValueError."""
    with pytest.raises(ValueError):
        segundos_para_tempo(-0.01)


def test_todos_cortes_gabarito_passam_duracao_confere():
    """Critério 4: todos os cortes do gabarito passam em duracao_confere."""
    with open(GABARITO_PATH, encoding="utf-8") as f:
        dados = json.load(f)

    cortes = dados["cortes"]
    assert len(cortes) > 0
    for corte in cortes:
        assert duracao_confere(
            inicio=corte["inicio"],
            fim=corte["fim"],
            duracao_segundos=corte["duracao_segundos"],
            duracao_formatada=corte["duracao_formatada"],
        )


def test_duracao_confere_divergencias_e_invalidos():
    """Verifica casos de erro em duracao_confere: divergência, invertido e inválidos."""
    # Divergência de 0.05 s
    assert not duracao_confere("00:00:00.00", "00:00:10.00", 10.05, "00:00:10.00")
    # Divergência na string formatada
    assert not duracao_confere("00:00:00.00", "00:00:10.00", 10.00, "00:00:10.05")
    # Fim anterior ao início
    assert not duracao_confere("00:00:10.00", "00:00:05.00", 5.00, "00:00:05.00")
    # Duração segundos negativa
    assert not duracao_confere("00:00:00.00", "00:00:10.00", -10.00, "00:00:10.00")
    # Formato inválido
    assert not duracao_confere("invalido", "00:00:10.00", 10.00, "00:00:10.00")
