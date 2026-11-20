"""Testes do validador de esquema JSON (Tarefa T01)."""

import copy
from pathlib import Path

from cortesia.esquema import carregar_json, validar_saida

FIXTURES = Path(__file__).parent / "fixtures"
GABARITO_PATH = FIXTURES / "gabarito_textos_c1_c7_c8.json"


def carregar_gabarito() -> dict:
    """Carrega uma nova cópia do gabarito oficial em memória."""
    return carregar_json(GABARITO_PATH)


def test_carregar_json():
    """Verifica se carregar_json carrega corretamente um arquivo JSON em UTF-8."""
    dados = carregar_json(GABARITO_PATH)
    assert isinstance(dados, dict)
    assert dados.get("schema_version") == "1.0"


def test_gabarito_valido_passa():
    """Critério 1: o gabarito oficial passa sem erros."""
    dados = carregar_gabarito()
    erros = validar_saida(dados)
    assert erros == []


def test_mutacao_etapa_invalida():
    """Critério 2: etapa inválida deve falhar citando 'etapa'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["etapa"] = "invalida"

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("etapa" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_nota_acima_do_maximo():
    """Critério 2: nota = 11 deve falhar citando 'nota'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][0]["potencial_viralizacao"]["nota"] = 11

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("nota" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_seis_hashtags():
    """Critério 2: 6 hashtags deve falhar citando 'hashtags' com caminho completo."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][0]["textos"]["descricao"]["hashtags"].append("#extra")

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("hashtags" in msg for msg in erros)
    assert any("cortes[0].textos.descricao.hashtags" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_opcoes_enquete_invalidas():
    """Critério 2: opcoes = ['Sim', 'Talvez'] deve falhar citando 'opcoes'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][0]["textos"]["enquete"]["opcoes"] = ["Sim", "Talvez"]

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("opcoes" in msg for msg in erros)
    assert any("cortes[0].textos.enquete.opcoes" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_tempo_inicio_invalido():
    """Critério 2: inicio = '0:01:49.4' deve falhar citando 'inicio'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][0]["inicio"] = "0:01:49.4"

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("inicio" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_curadoria_com_textos_preenchido():
    """Critério 2: etapa 'curadoria' com textos não nulo deve falhar citando 'textos'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["etapa"] = "curadoria"

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("textos" in msg for msg in erros)
    assert any("cortes[0].textos" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_campo_obrigatorio_ausente_gancho():
    """Critério 2: campo obrigatório 'gancho' ausente deve falhar citando 'gancho'."""
    dados = copy.deepcopy(carregar_gabarito())
    del dados["cortes"][0]["gancho"]

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("gancho" in msg for msg in erros)
    assert any("cortes[0].gancho" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_ordenacao_estavel_e_sem_duplicatas():
    """Critério 3: as mensagens vêm ordenadas por (caminho, mensagem) e sem duplicatas."""
    dados = copy.deepcopy(carregar_gabarito())
    # Injeta múltiplos erros em diferentes campos
    dados["etapa"] = "invalida"
    dados["cortes"][0]["potencial_viralizacao"]["nota"] = 11
    dados["cortes"][0]["inicio"] = "0:01:49.4"
    del dados["cortes"][0]["gancho"]

    erros = validar_saida(dados)
    assert len(erros) >= 4
    # Verifica que não há mensagens duplicadas
    assert len(erros) == len(set(erros))
    # Verifica que a lista está ordenada
    caminhos = [msg.split(":")[0] for msg in erros]
    assert caminhos == sorted(caminhos)
    assert all(len(msg) < 200 for msg in erros)
