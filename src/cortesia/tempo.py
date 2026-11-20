"""Utilitários de conversão e validação de tempo no formato hh:mm:ss.cc."""

import re

PADRAO_TEMPO = re.compile(r"^(\d{2}):([0-5]\d):([0-5]\d)\.(\d{2})$")


def segundos_para_tempo(segundos: float) -> str:
    """Converte segundos em formato hh:mm:ss.cc usando aritmética inteira nos centésimos.

    Exemplo: 59.999 vira '00:01:00.00'.
    Levanta ValueError se segundos for negativo.
    """
    if segundos < 0:
        raise ValueError(f"Tempo em segundos não pode ser negativo: {segundos}")

    total_centesimos = round(segundos * 100)
    centesimos = total_centesimos % 100
    total_segundos = total_centesimos // 100
    seg = total_segundos % 60
    total_minutos = total_segundos // 60
    minutos = total_minutos % 60
    horas = total_minutos // 60

    return f"{horas:02d}:{minutos:02d}:{seg:02d}.{centesimos:02d}"


def tempo_para_segundos(texto: str) -> float:
    """Converte string no formato hh:mm:ss.cc para segundos como float.

    Aceita apenas o formato exato hh:mm:ss.cc com minutos e segundos entre 00 e 59.
    Levanta ValueError para qualquer formato inválido.
    """
    try:
        match = PADRAO_TEMPO.match(texto)
    except TypeError as exc:
        raise ValueError(
            f"Esperado string, recebido {type(texto).__name__}"
        ) from exc
    if not match:
        raise ValueError(
            f"Formato de tempo inválido: {texto!r}. Esperado padrão 'hh:mm:ss.cc'."
        )

    horas, minutos, segundos, centesimos = (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        int(match.group(4)),
    )

    total_centesimos = (horas * 3600 + minutos * 60 + segundos) * 100 + centesimos
    return total_centesimos / 100.0


def duracao_confere(
    inicio: str, fim: str, duracao_segundos: float, duracao_formatada: str
) -> bool:
    """Verifica se a duração fim - inicio bate com duracao_segundos e duracao_formatada.

    Usa tolerância de 0,01 s. Retorna False se algum formato for inválido
    ou se os valores divergirem além da tolerância.
    """
    try:
        t_inicio = tempo_para_segundos(inicio)
        t_fim = tempo_para_segundos(fim)
        t_formatada = tempo_para_segundos(duracao_formatada)
    except ValueError:
        return False

    if t_fim < t_inicio or duracao_segundos < 0:
        return False

    delta = t_fim - t_inicio
    tolerancia = 0.01 + 1e-6

    bate_segundos = abs(delta - duracao_segundos) <= tolerancia
    bate_formatada = abs(delta - t_formatada) <= tolerancia
    consistencia_interna = abs(duracao_segundos - t_formatada) <= tolerancia

    return bate_segundos and bate_formatada and consistencia_interna
