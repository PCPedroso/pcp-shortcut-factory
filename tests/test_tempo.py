# /tests/test_tempo.py

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


def test_segundos_para_tempo_carry():
    """Carry nos centésimos arredonda para próximo segundo/minuto/hora."""
    assert segundos_para_tempo(3599.999) == "01:00:00.00"


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
        359999.99,
    ],
)
def test_ida_e_volta(segundos: float):
    """Critério 2: ida e volta preserva o valor com 2 casas decimais."""
    formatado = segundos_para_tempo(segundos)
    recuperado = tempo_para_segundos(formatado)
    assert pytest.approx(recuperado, abs=1e-4) == round(segundos, 2)


def test_segundos_para_tempo_limite_maximo():
    """Limite máximo de 2 dígitos de horas (99:59:59.99)."""
    assert segundos_para_tempo(359999.99) == "99:59:59.99"
    assert tempo_para_segundos("99:59:59.99") == 359999.99


@pytest.mark.parametrize(
    "valor_invalido",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        360000,
        360000.0,
        -0.01,
    ],
)
def test_segundos_para_tempo_valores_invalidos(valor_invalido):
    """Valores não finitos, negativos ou que excedem o limite de 2 dígitos levantam ValueError."""
    with pytest.raises(ValueError):
        segundos_para_tempo(valor_invalido)


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
        "00:01:49.40\n",
        "\n00:01:49.40",
        "00:01:4٩.40",
        None,
        123,
    ],
)
def test_tempo_para_segundos_invalidos(texto_invalido):
    """Critério 3: formatos inválidos, com quebra de linha, dígitos Unicode ou tipos errados levantam ValueError."""
    with pytest.raises(ValueError):
        tempo_para_segundos(texto_invalido)


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
    """Verifica casos de erro em duracao_confere: divergência, invertido e tipos inválidos."""
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
    # Quebra de linha no início ou fim
    assert not duracao_confere("00:00:00.00\n", "00:00:10.00", 10.00, "00:00:10.00")
    assert not duracao_confere("00:00:00.00", "\n00:00:10.00", 10.00, "00:00:10.00")
    assert not duracao_confere("00:00:00.00", "00:00:10.00", 10.00, "00:00:10.00\n")
    # duracao_segundos não número ou NaN
    assert not duracao_confere("00:00:00.00", "00:00:10.00", "10", "00:00:10.00")
    assert not duracao_confere("00:00:00.00", "00:00:10.00", float("nan"), "00:00:10.00")
    assert not duracao_confere("00:00:00.00", "00:00:10.00", float("inf"), "00:00:10.00")
    assert not duracao_confere("00:00:00.00", "00:00:10.00", True, "00:00:10.00")


def test_duracao_confere_bordas_tolerancia():
    """Bordas da tolerância: diferença de 0.01 passa; diferença de 0.02 falha."""
    # Diferença de 0.01 s passa
    assert duracao_confere("00:00:00.00", "00:00:10.00", 10.01, "00:00:10.01")
    assert duracao_confere("00:00:00.00", "00:00:10.00", 9.99, "00:00:09.99")
    assert duracao_confere("00:00:00.00", "00:00:10.00", 10.01, "00:00:10.00")

    # Diferença de 0.02 s falha
    assert not duracao_confere("00:00:00.00", "00:00:10.00", 10.02, "00:00:10.02")
    assert not duracao_confere("00:00:00.00", "00:00:10.00", 9.98, "00:00:09.98")
    assert not duracao_confere("00:00:00.00", "00:00:10.00", 10.02, "00:00:10.00")
