"""Validação de dados de saída conforme schemas/saida_v1.schema.json."""

import json
import re
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError, best_match


def _caminho_esquema_padrao() -> Path:
    """Retorna o caminho padrão do esquema JSON."""
    return Path(__file__).resolve().parents[2] / "schemas" / "saida_v1.schema.json"


def carregar_json(caminho: Path) -> dict[str, Any]:
    """Carrega um arquivo JSON em UTF-8 e retorna o dicionário correspondente."""
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _obter_validador(caminho_esquema: Path | None = None) -> Draft202012Validator:
    """Carrega o esquema uma única vez e retorna o validador Draft 2020-12 em cache."""
    caminho = caminho_esquema or _caminho_esquema_padrao()
    esquema = carregar_json(caminho)
    return Draft202012Validator(esquema)


def _formatar_caminho(elementos_caminho: Iterable[Any]) -> str:
    """Formata os elementos de caminho no padrão cortes[0].potencial_viralizacao.nota."""
    resultado = ""
    for elem in elementos_caminho:
        if isinstance(elem, int):
            resultado += f"[{elem}]"
        else:
            if resultado:
                resultado += f".{elem}"
            else:
                resultado = str(elem)
    return resultado


def _descer_erro(err: ValidationError) -> list[ValidationError]:
    """Extrai erros específicos de estruturas oneOf/anyOf ignorando ramos nulos."""
    if err.validator in ("oneOf", "anyOf") and err.context:
        # Filtra o ramo que apenas exige null quando o valor não é nulo
        relevantes = [
            c
            for c in err.context
            if not (c.validator == "type" and c.validator_value == "null")
        ]
        if not relevantes:
            relevantes = list(err.context)

        if len(relevantes) > 1:
            melhor = best_match(relevantes)
            if melhor is not None:
                return _descer_erro(melhor)

        erros_desdobrados: list[ValidationError] = []
        for c in relevantes:
            erros_desdobrados.extend(_descer_erro(c))
        return erros_desdobrados

    return [err]


def _traduzir_problema(err: ValidationError, caminho: str) -> str:
    """Traduz e formata o problema para português com base no validador do jsonschema."""
    val = err.validator
    val_val = err.validator_value
    inst = err.instance

    if val == "maximum":
        return f"{inst} é maior que o máximo {val_val}"
    if val == "minimum":
        return f"{inst} é menor que o mínimo {val_val}"
    if val == "exclusiveMaximum":
        return f"{inst} deve ser menor que {val_val}"
    if val == "exclusiveMinimum":
        return f"{inst} deve ser maior que {val_val}"
    if val == "enum":
        opcoes = ", ".join(repr(o) for o in val_val)
        return f"valor {repr(inst)[:30]} inválido (esperado um de: {opcoes})"
    if val == "const":
        return f"valor {repr(inst)[:30]} é inválido (esperado {val_val!r})"
    if val == "maxItems":
        qtd = len(inst) if isinstance(inst, (list, tuple, dict, set)) else "?"
        return f"máximo de {val_val} itens (recebeu {qtd})"
    if val == "minItems":
        qtd = len(inst) if isinstance(inst, (list, tuple, dict, set)) else "?"
        return f"mínimo de {val_val} itens (recebeu {qtd})"
    if val == "pattern":
        return f"valor {repr(inst)[:30]} não corresponde ao padrão esperado"
    if val == "required":
        return "campo obrigatório ausente"
    if val == "type":
        if val_val == "null" and caminho.endswith("textos"):
            return "deve ser nulo quando a etapa é 'curadoria'"
        return f"tipo inválido (esperado {val_val})"
    if val == "additionalProperties":
        return "propriedade não permitida"
    if val == "minLength":
        return f"tamanho mínimo de {val_val} caracteres"
    if val == "maxLength":
        return f"tamanho máximo de {val_val} caracteres"

    return f"falha na validação ({val})"


def _processar_erro(err: ValidationError) -> tuple[str, str]:
    """Processa um ValidationError e retorna (caminho, mensagem) formatada."""
    caminho = _formatar_caminho(err.absolute_path)

    if err.validator == "required":
        faltante: str | None = None
        if isinstance(err.instance, dict) and isinstance(err.validator_value, list):
            for campo in err.validator_value:
                if campo not in err.instance:
                    faltante = campo
                    break
        if not faltante:
            match = re.search(r"'([^']+)' is a required property", err.message)
            if match:
                faltante = match.group(1)

        if faltante:
            caminho = f"{caminho}.{faltante}" if caminho else faltante

    problema = _traduzir_problema(err, caminho)
    mensagem = f"{caminho}: {problema}" if caminho else problema

    if len(mensagem) > 200:
        mensagem = mensagem[:197] + "..."

    return caminho, mensagem


def validar_saida(dados: dict[str, Any]) -> list[str]:
    """Valida um dicionário contra o esquema JSON.

    Retorna lista vazia se válido; senão uma lista ordenada de mensagens
    de erro no formato '<caminho>: <problema>', sem duplicatas.
    """
    validador = _obter_validador()
    erros_brutos = list(validador.iter_errors(dados))

    if not erros_brutos:
        return []

    erros_formatados: list[tuple[str, str]] = []
    for err in erros_brutos:
        for sub_err in _descer_erro(err):
            erros_formatados.append(_processar_erro(sub_err))

    # Ordena por (caminho, mensagem) e remove duplicatas
    erros_ordenados = sorted(set(erros_formatados), key=lambda x: (x[0], x[1]))
    return [msg for _, msg in erros_ordenados]
