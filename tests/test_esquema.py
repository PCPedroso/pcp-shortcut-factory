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


def test_validar_saida_nao_muta_dicionario():
    """Garante que validar_saida não altera o dicionário recebido."""
    dados = carregar_gabarito()
    copia = copy.deepcopy(dados)
    validar_saida(dados)
    assert dados == copia


def test_mutacao_etapa_invalida():
    """Critério 2: etapa inválida deve falhar citando 'etapa'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["etapa"] = "invalida"

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("etapa" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_nota_acima_do_maximo():
    """Critério 2: nota = 11 deve falhar citando 'cortes[0].potencial_viralizacao.nota'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][0]["potencial_viralizacao"]["nota"] = 11

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("cortes[0].potencial_viralizacao.nota" in msg for msg in erros)
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
    assert any("cortes[0].inicio" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_curadoria_com_textos_preenchido():
    """Critério 2: etapa 'curadoria' com textos deve falhar citando regra e 'textos'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["etapa"] = "curadoria"

    erros = validar_saida(dados)
    assert len(erros) >= 1
    assert any("textos" in msg for msg in erros)
    assert any("cortes[0].textos" in msg for msg in erros)
    assert any("deve ser nulo quando a etapa é 'curadoria'" in msg for msg in erros)
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


def test_mutacao_campos_obrigatorios_ausentes_multiplos():
    """Dois campos ausentes no mesmo corte geram duas mensagens separadas."""
    dados = copy.deepcopy(carregar_gabarito())
    del dados["cortes"][0]["gancho"]
    del dados["cortes"][0]["descricao"]

    erros = validar_saida(dados)
    assert any("cortes[0].gancho" in msg for msg in erros)
    assert any("cortes[0].descricao" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_multiplos_erros_em_textos():
    """Múltiplos erros em textos aparecem juntos com seus caminhos completos."""
    dados = copy.deepcopy(carregar_gabarito())
    # 6 hashtags
    dados["cortes"][0]["textos"]["descricao"]["hashtags"].append("#extra")
    # opções inválidas
    dados["cortes"][0]["textos"]["enquete"]["opcoes"] = ["Sim", "Talvez"]
    # título com 101 caracteres
    dados["cortes"][0]["textos"]["titulos"][0]["texto"] = "A" * 101
    dados["cortes"][0]["textos"]["titulos"][0]["caracteres"] = 101

    erros = validar_saida(dados)
    assert any("cortes[0].textos.descricao.hashtags" in msg for msg in erros)
    assert any("cortes[0].textos.enquete.opcoes" in msg for msg in erros)
    assert any("cortes[0].textos.titulos[0].texto" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_erro_corte_indice_1():
    """Erro no corte de índice 1 começa com o prefixo 'cortes[1]'."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][1]["potencial_viralizacao"]["nota"] = 0

    erros = validar_saida(dados)
    assert any(msg.startswith("cortes[1].potencial_viralizacao.nota") for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_mutacao_propriedade_extra():
    """Propriedade extra não permitida cita o nome da propriedade na mensagem."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["cortes"][0]["campo_fantasma"] = "valor"

    erros = validar_saida(dados)
    assert any("campo_fantasma" in msg for msg in erros)
    assert any("cortes[0]: propriedade não permitida: 'campo_fantasma'" in msg for msg in erros)
    assert all(len(msg) < 200 for msg in erros)


def test_ordenacao_estavel_e_sem_duplicatas():
    """Critério 3: as mensagens vêm ordenadas por (caminho, mensagem) e sem duplicatas."""
    dados = copy.deepcopy(carregar_gabarito())
    dados["etapa"] = "invalida"
    dados["cortes"][0]["potencial_viralizacao"]["nota"] = 11
    dados["cortes"][0]["inicio"] = "0:01:49.4"
    del dados["cortes"][0]["gancho"]

    erros = validar_saida(dados)
    assert len(erros) >= 4
    assert len(erros) == len(set(erros))
    caminhos = [msg.split(":")[0] for msg in erros]
    assert caminhos == sorted(caminhos)
    assert all(len(msg) < 200 for msg in erros)
