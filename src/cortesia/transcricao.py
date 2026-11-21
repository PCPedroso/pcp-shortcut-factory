"""Leitor de transcrição e cálculo de tempo efetivo das falas (Tarefa T03)."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class TranscricaoInvalida(Exception):
    """Exceção levantada quando os dados de transcrição são inválidos."""


@dataclass(frozen=True)
class Segmento:
    """Representa um segmento de fala normalizado."""

    inicio: float
    fim: float
    texto: str
    fim_efetivo: float


@dataclass(frozen=True)
class Transcricao:
    """Representa a transcrição completa de um vídeo com falas encadeadas."""

    segmentos: tuple[Segmento, ...]
    idioma: str
    duracao_aproximada: float


def carregar_transcricao(caminho: Path | str) -> Transcricao:
    """Carrega uma transcrição a partir de um arquivo JSON.

    Calcula o fim efetivo de cada fala (o início do segmento seguinte ou o próprio
    fim para o último segmento).

    Valida a presença de campos obrigatórios, integridade temporal e formatação.

    Levanta:
        TranscricaoInvalida: se o arquivo for inválido, faltar campos obrigatórios,
            tiver erro preenchido, lista de segmentos vazia, ou inconsistências
            temporais (start decrescente ou end menor que start).
    """
    caminho_path = Path(caminho)
    try:
        with open(caminho_path, encoding="utf-8") as f:
            dados = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise TranscricaoInvalida(f"Falha ao ler arquivo de transcrição: {exc}") from exc

    if not isinstance(dados, dict):
        raise TranscricaoInvalida("Conteúdo da transcrição deve ser um objeto JSON.")

    if dados.get("error"):
        raise TranscricaoInvalida(f"Transcrição contém erro: {dados['error']}")

    idioma = dados.get("selected_language_code")
    if not idioma or not isinstance(idioma, str):
        raise TranscricaoInvalida(
            "Campo obrigatório 'selected_language_code' ausente ou inválido."
        )

    if "transcript_segments" not in dados:
        raise TranscricaoInvalida("Campo obrigatório 'transcript_segments' ausente.")

    segmentos_brutos: Any = dados["transcript_segments"]
    if not isinstance(segmentos_brutos, list) or len(segmentos_brutos) == 0:
        raise TranscricaoInvalida("Lista de 'transcript_segments' vazia ou inválida.")

    total = len(segmentos_brutos)

    # Primeira passagem: validação estrutural e temporal de cada segmento
    for i, seg in enumerate(segmentos_brutos):
        if not isinstance(seg, dict):
            raise TranscricaoInvalida(f"Segmento no índice {i} deve ser um objeto JSON.")

        if "start" not in seg or "end" not in seg or "text" not in seg:
            raise TranscricaoInvalida(
                f"Segmento no índice {i} não possui os campos obrigatórios ('start', 'end', 'text')."
            )

        inicio_val = seg["start"]
        fim_val = seg["end"]
        texto_val = seg["text"]

        if isinstance(inicio_val, bool) or not isinstance(inicio_val, (int, float)):
            raise TranscricaoInvalida(f"Campo 'start' no segmento {i} deve ser numérico.")
        if isinstance(fim_val, bool) or not isinstance(fim_val, (int, float)):
            raise TranscricaoInvalida(f"Campo 'end' no segmento {i} deve ser numérico.")
        if not isinstance(texto_val, str):
            raise TranscricaoInvalida(f"Campo 'text' no segmento {i} deve ser texto (str).")

        inicio = float(inicio_val)
        fim = float(fim_val)

        if not math.isfinite(inicio):
            raise TranscricaoInvalida(
                f"Segmento no índice {i} possui start não-finito: {inicio}."
            )
        if not math.isfinite(fim):
            raise TranscricaoInvalida(
                f"Segmento no índice {i} possui end não-finito: {fim}."
            )
        if inicio < 0:
            raise TranscricaoInvalida(
                f"Segmento no índice {i} possui start negativo: {inicio}."
            )

        if fim < inicio:
            raise TranscricaoInvalida(
                f"Segmento no índice {i} possui end ({fim}) menor que start ({inicio})."
            )

        if i > 0:
            anterior_inicio = float(segmentos_brutos[i - 1]["start"])
            if inicio < anterior_inicio:
                raise TranscricaoInvalida(
                    f"Segmento no índice {i} possui start ({inicio}) menor que o anterior ({anterior_inicio})."
                )

    # Segunda passagem: construção dos objetos Segmento com fim_efetivo
    lista_segmentos: list[Segmento] = []
    for i, seg in enumerate(segmentos_brutos):
        inicio = float(seg["start"])
        fim = float(seg["end"])
        texto = seg["text"]

        if i < total - 1:
            fim_efetivo = float(segmentos_brutos[i + 1]["start"])
        else:
            fim_efetivo = fim

        lista_segmentos.append(
            Segmento(
                inicio=inicio,
                fim=fim,
                texto=texto,
                fim_efetivo=fim_efetivo,
            )
        )

    duracao_aproximada = float(segmentos_brutos[-1]["end"])

    return Transcricao(
        segmentos=tuple(lista_segmentos),
        idioma=idioma,
        duracao_aproximada=duracao_aproximada,
    )
