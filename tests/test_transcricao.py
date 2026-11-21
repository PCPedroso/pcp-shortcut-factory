"""Testes para o módulo de transcrição e cálculo de tempo efetivo (Tarefa T03)."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cortesia.transcricao import Segmento, Transcricao, TranscricaoInvalida, carregar_transcricao

FIXTURES = Path(__file__).parent / "fixtures"
TRANSCRIPT_PATH = FIXTURES / "transcript_tuVNNEO-NKc_pt.json"


def test_carregar_transcricao_fixture_completa():
    """Critérios 1, 2, 3 e 5 com a fixture oficial tuVNNEO-NKc."""
    transcricao = carregar_transcricao(TRANSCRIPT_PATH)

    assert isinstance(transcricao, Transcricao)
    # Critério 1: 685 segmentos, primeiro inicio = 0.08, duracao_aproximada = 1424.88
    assert len(transcricao.segmentos) == 685
    assert transcricao.segmentos[0].inicio == 0.08
    assert transcricao.duracao_aproximada == 1424.88
    assert transcricao.idioma == "pt"

    # Critério 2: fim_efetivo de cada segmento (exceto o último) = inicio do seguinte;
    # do último = seu fim.
    for i in range(len(transcricao.segmentos) - 1):
        assert transcricao.segmentos[i].fim_efetivo == transcricao.segmentos[i + 1].inicio

    ultimo = transcricao.segmentos[-1]
    assert ultimo.fim_efetivo == ultimo.fim == 1424.88

    # Critério 3: source e selected_language NÃO são tratados como canal nem viram atributos
    assert not hasattr(transcricao, "source")
    assert not hasattr(transcricao, "selected_language")
    assert not hasattr(transcricao, "canal")

    # Critério 5: textos preservam acentos (UTF-8)
    assert transcricao.segmentos[0].texto == "Nesse vídeo aqui, então, a gente vai"
    assert transcricao.segmentos[-1].texto == "Vila Nova, gente, eu patrocínio."


def test_erro_preenchido_levanta_transcricao_invalida(tmp_path: Path):
    """Critério 4: JSON com error preenchido levanta TranscricaoInvalida."""
    arquivo = tmp_path / "erro.json"
    dados = {
        "selected_language_code": "pt",
        "error": "Legendas desativadas pelo autor do vídeo.",
        "transcript_segments": [{"start": 0.0, "end": 1.0, "text": "olá"}],
    }
    arquivo.write_text(json.dumps(dados), encoding="utf-8")

    with pytest.raises(TranscricaoInvalida, match="Transcrição contém erro"):
        carregar_transcricao(arquivo)


def test_segmentos_vazios_levanta_transcricao_invalida(tmp_path: Path):
    """Critério 4: JSON com lista de segmentos vazia levanta TranscricaoInvalida."""
    arquivo = tmp_path / "vazio.json"
    dados = {
        "selected_language_code": "pt",
        "error": None,
        "transcript_segments": [],
    }
    arquivo.write_text(json.dumps(dados), encoding="utf-8")

    with pytest.raises(TranscricaoInvalida, match="vazia ou inválida"):
        carregar_transcricao(arquivo)


@pytest.mark.parametrize(
    "dados_invalidos,mensagem_esperada",
    [
        (
            {"transcript_segments": [{"start": 0.0, "end": 1.0, "text": "teste"}]},
            "selected_language_code",
        ),
        (
            {"selected_language_code": "pt"},
            "transcript_segments",
        ),
        (
            {
                "selected_language_code": "pt",
                "transcript_segments": [{"end": 1.0, "text": "sem start"}],
            },
            "campos obrigatórios",
        ),
        (
            {
                "selected_language_code": "pt",
                "transcript_segments": [{"start": 0.0, "text": "sem end"}],
            },
            "campos obrigatórios",
        ),
        (
            {
                "selected_language_code": "pt",
                "transcript_segments": [{"start": 0.0, "end": 1.0}],
            },
            "campos obrigatórios",
        ),
        (
            {
                "selected_language_code": "pt",
                "transcript_segments": [{"start": "zero", "end": 1.0, "text": "tipo errado"}],
            },
            "deve ser numérico",
        ),
        (
            {
                "selected_language_code": "pt",
                "transcript_segments": [{"start": 0.0, "end": "um", "text": "tipo errado"}],
            },
            "deve ser numérico",
        ),
        (
            {
                "selected_language_code": "pt",
                "transcript_segments": [{"start": 0.0, "end": 1.0, "text": 123}],
            },
            "deve ser texto",
        ),
    ],
)
def test_campos_ausentes_ou_invalidos_levantam_transcricao_invalida(
    tmp_path: Path, dados_invalidos: dict, mensagem_esperada: str
):
    """Critério 4: campos ausentes ou tipos inválidos levantam TranscricaoInvalida."""
    arquivo = tmp_path / "invalido.json"
    arquivo.write_text(json.dumps(dados_invalidos), encoding="utf-8")

    with pytest.raises(TranscricaoInvalida, match=mensagem_esperada):
        carregar_transcricao(arquivo)


def test_start_decrescente_levanta_transcricao_invalida(tmp_path: Path):
    """Critério adicional 6: start não-decrescente levanta erro indicando o índice."""
    arquivo = tmp_path / "start_decrescente.json"
    dados = {
        "selected_language_code": "pt",
        "error": None,
        "transcript_segments": [
            {"start": 1.0, "end": 3.0, "text": "primeiro"},
            {"start": 4.0, "end": 6.0, "text": "segundo"},
            {"start": 3.5, "end": 7.0, "text": "terceiro com start menor que o segundo"},
        ],
    }
    arquivo.write_text(json.dumps(dados), encoding="utf-8")

    with pytest.raises(TranscricaoInvalida) as exc_info:
        carregar_transcricao(arquivo)

    mensagem = str(exc_info.value)
    assert "índice 2" in mensagem
    assert "start" in mensagem


def test_end_menor_que_start_levanta_transcricao_invalida(tmp_path: Path):
    """Critério adicional 6: end menor que start levanta TranscricaoInvalida."""
    arquivo = tmp_path / "end_menor_que_start.json"
    dados = {
        "selected_language_code": "pt",
        "error": None,
        "transcript_segments": [
            {"start": 0.0, "end": 2.0, "text": "normal"},
            {"start": 2.5, "end": 1.8, "text": "fim antes do inicio"},
        ],
    }
    arquivo.write_text(json.dumps(dados), encoding="utf-8")

    with pytest.raises(TranscricaoInvalida) as exc_info:
        carregar_transcricao(arquivo)

    mensagem = str(exc_info.value)
    assert "índice 1" in mensagem
    assert "end" in mensagem
    assert "menor que start" in mensagem


def test_arquivo_inexistente_ou_malformado(tmp_path: Path):
    """Arquivo inexistente ou JSON inválido levanta TranscricaoInvalida."""
    with pytest.raises(TranscricaoInvalida, match="Falha ao ler arquivo"):
        carregar_transcricao(tmp_path / "inexistente.json")

    arquivo_corrompido = tmp_path / "corrompido.json"
    arquivo_corrompido.write_text("{conteudo quebrado", encoding="utf-8")
    with pytest.raises(TranscricaoInvalida, match="Falha ao ler arquivo"):
        carregar_transcricao(arquivo_corrompido)


def test_imutabilidade_das_dataclasses():
    """Garante que Segmento e Transcricao são imutáveis e segmentos é uma tupla."""
    seg = Segmento(inicio=1.0, fim=2.0, texto="fala", fim_efetivo=2.0)
    with pytest.raises(FrozenInstanceError):
        seg.inicio = 5.0  # type: ignore[misc]

    transcricao = Transcricao(segmentos=(seg,), idioma="pt", duracao_aproximada=2.0)
    with pytest.raises(FrozenInstanceError):
        transcricao.idioma = "en"  # type: ignore[misc]

    assert isinstance(transcricao.segmentos, tuple)
