"""Validações editoriais (etapa 1 / T04a) sem dependência de transcrição."""

import re
from dataclasses import dataclass
from typing import Any, Literal

from cortesia import esquema, tempo

PADRAO_DOMINIO = re.compile(r"\b[a-z0-9-]+\.(?:com|net|org|br|io|be|ly)\b", re.IGNORECASE)
PADRAO_CANAL_OFICIAL = re.compile(r"youtube\s*oficial", re.IGNORECASE)
PADRAO_DIGITO = re.compile(r"\d")


@dataclass(frozen=True)
class Problema:
    """Representa um problema editorial ou de validação encontrado na saída."""

    gravidade: Literal["erro", "aviso"]
    codigo: str
    caminho: str
    mensagem: str


def _converter_centesimos(tempo_str: str) -> int:
    """Converte tempo no formato hh:mm:ss.cc para centésimos inteiros."""
    return round(tempo.tempo_para_segundos(tempo_str) * 100)


def _contem_link(texto: str) -> bool:
    """Verifica se há http, www. ou domínio conhecido no texto."""
    t_lower = texto.lower()
    if "http" in t_lower or "www." in t_lower:
        return True
    return bool(PADRAO_DOMINIO.search(texto))


def _validar_tempo_e_cortes(
    saida: dict[str, Any], max_cortes: int
) -> list[Problema]:
    """Aplica as regras 1 a 8 sobre tempo, ordenação e limites de cortes."""
    problemas: list[Problema] = []
    cortes = saida.get("cortes", [])
    alertas_gerais = saida.get("alertas_gerais", [])

    if len(cortes) > max_cortes:
        problemas.append(
            Problema(
                gravidade="erro",
                codigo="CORTES_QTD",
                caminho="cortes",
                mensagem=f"Quantidade de cortes ({len(cortes)}) excede o máximo permitido de {max_cortes}.",
            )
        )

    # Duração do vídeo em centésimos
    video_info = saida.get("video", {})
    duracao_video_cent: int | None = None
    if video_info and "duracao_aproximada" in video_info:
        try:
            duracao_video_cent = _converter_centesimos(video_info["duracao_aproximada"])
        except ValueError:
            duracao_video_cent = None

    ids_vistos: set[str] = set()
    inicio_anterior_cent: int | None = None
    fim_anterior_cent: int | None = None
    id_anterior: str | None = None
    maior_fim_cent: int | None = None
    id_maior_fim: str | None = None

    for i, corte in enumerate(cortes):
        c_id = corte.get("id", "")
        caminho_corte = f"cortes[{i}]"

        # Regra 5: CORTES_ID_DUPLICADO
        if c_id in ids_vistos:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="CORTES_ID_DUPLICADO",
                    caminho=f"{caminho_corte}.id",
                    mensagem=f"Identificador de corte duplicado: {c_id}.",
                )
            )
        ids_vistos.add(c_id)

        inicio_str = corte.get("inicio", "")
        fim_str = corte.get("fim", "")
        dur_seg = corte.get("duracao_segundos", 0.0)
        dur_fmt = corte.get("duracao_formatada", "")

        # Regra 1: TEMPO_DURACAO
        if not tempo.duracao_confere(inicio_str, fim_str, dur_seg, dur_fmt):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEMPO_DURACAO",
                    caminho=f"{caminho_corte}.duracao_segundos",
                    mensagem="Duração informada não confere com o intervalo de início e fim.",
                )
            )

        try:
            inicio_cent = _converter_centesimos(inicio_str)
            fim_cent = _converter_centesimos(fim_str)
        except ValueError:
            continue

        # Regra 2: TEMPO_ORDEM
        if fim_cent <= inicio_cent:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEMPO_ORDEM",
                    caminho=f"{caminho_corte}.fim",
                    mensagem=f"Tempo de fim ({fim_str}) deve ser maior que início ({inicio_str}).",
                )
            )

        # Regra 3: TEMPO_FORA_DO_VIDEO (fim > vídeo + 1,0 s = 100 centésimos)
        if duracao_video_cent is not None and fim_cent > duracao_video_cent + 100:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEMPO_FORA_DO_VIDEO",
                    caminho=f"{caminho_corte}.fim",
                    mensagem="Tempo de fim do corte ultrapassa a duração do vídeo em mais de 1,0 s.",
                )
            )

        # Relações com o corte anterior
        # Regra 6: CORTES_ORDEM
        if (
            inicio_anterior_cent is not None
            and id_anterior is not None
            and inicio_cent < inicio_anterior_cent
        ):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="CORTES_ORDEM",
                    caminho=f"{caminho_corte}.inicio",
                    mensagem=f"Corte {c_id} inicia antes do corte anterior ({id_anterior}).",
                )
            )

        # Regra 7: CORTES_SOBREPOSTOS (compara início com o maior fim visto até então)
        if (
            maior_fim_cent is not None
            and inicio_cent < maior_fim_cent
            and id_maior_fim is not None
        ):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="CORTES_SOBREPOSTOS",
                    caminho=f"{caminho_corte}.inicio",
                    mensagem=f"Corte {c_id} sobrepõe o corte {id_maior_fim}.",
                )
            )

        # Regra 8: CORTES_CONSECUTIVOS
        # Intervalo entre 0 e menos de 1,0 s (ou seja, 0 <= intervalo_cent < 100)
        if fim_anterior_cent is not None and id_anterior is not None:
            intervalo_cent = inicio_cent - fim_anterior_cent
            if 0 <= intervalo_cent < 100:
                padrao_ant = rf"\b{re.escape(id_anterior)}\b"
                padrao_atual = rf"\b{re.escape(c_id)}\b"
                justificado = any(
                    re.search(padrao_ant, alerta) and re.search(padrao_atual, alerta)
                    for alerta in alertas_gerais
                )
                if not justificado:
                    problemas.append(
                        Problema(
                            gravidade="erro",
                            codigo="CORTES_CONSECUTIVOS",
                            caminho=caminho_corte,
                            mensagem=(
                                f"Intervalo menor que 1,0 s entre {id_anterior} e {c_id} "
                                "sem justificativa em alertas_gerais."
                            ),
                        )
                    )

        inicio_anterior_cent = inicio_cent
        fim_anterior_cent = fim_cent
        id_anterior = c_id
        if maior_fim_cent is None or fim_cent > maior_fim_cent:
            maior_fim_cent = fim_cent
            id_maior_fim = c_id

    return problemas


def _validar_faixa_duracao(
    saida: dict[str, Any], duracao_min_s: float, duracao_max_s: float
) -> list[Problema]:
    """Aplica as regras 9 e 10 sobre duração do corte usando fim - inicio em centésimos."""
    problemas: list[Problema] = []
    min_cent = round(duracao_min_s * 100)
    max_cent = round(duracao_max_s * 100)
    margem_cent = max_cent - 500  # max - 5 s

    cortes = saida.get("cortes", [])
    for i, corte in enumerate(cortes):
        caminho_duracao = f"cortes[{i}].duracao_segundos"
        try:
            inicio_cent = _converter_centesimos(corte.get("inicio", ""))
            fim_cent = _converter_centesimos(corte.get("fim", ""))
        except ValueError:
            continue

        duracao_cent = fim_cent - inicio_cent
        tem_obs_edicao = any(
            obs.get("tipo") == "edicao" for obs in corte.get("observacoes", [])
        )

        if tem_obs_edicao:
            continue

        # Regra 9: DURACAO_FAIXA (fora de [min, max])
        if duracao_cent < min_cent or duracao_cent > max_cent:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="DURACAO_FAIXA",
                    caminho=caminho_duracao,
                    mensagem=(
                        f"Duração ({duracao_cent / 100:.2f} s) fora da faixa de "
                        f"{duracao_min_s:.1f} a {duracao_max_s:.1f} s sem observação de edição."
                    ),
                )
            )
        # Regra 10: DURACAO_MARGEM (duração > max - 5 s e <= max)
        elif duracao_cent > margem_cent:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="DURACAO_MARGEM",
                    caminho=caminho_duracao,
                    mensagem=(
                        f"Duração ({duracao_cent / 100:.2f} s) a menos de 5 s do limite máximo "
                        f"({duracao_max_s:.1f} s) sem observação de edição."
                    ),
                )
            )

    return problemas


def _validar_ranking(saida: dict[str, Any]) -> list[Problema]:
    """Aplica as regras 11 e 12 sobre a estrutura do ranking e consistência."""
    problemas: list[Problema] = []
    ranking = saida.get("ranking", [])
    etapa = saida.get("etapa")
    cortes = saida.get("cortes", [])
    ids_cortes = {c.get("id") for c in cortes}
    prioridade = saida.get("prioridade_sugerida")

    # Regra 11: RANKING_ESTRUTURA
    if len(ranking) > 3:
        problemas.append(
            Problema(
                gravidade="erro",
                codigo="RANKING_ESTRUTURA",
                caminho="ranking",
                mensagem=f"Ranking contém {len(ranking)} itens (máximo permitido é 3).",
            )
        )

    posicoes = [item.get("posicao") for item in ranking]
    esperado = list(range(1, len(ranking) + 1))
    if posicoes != esperado:
        problemas.append(
            Problema(
                gravidade="erro",
                codigo="RANKING_ESTRUTURA",
                caminho="ranking",
                mensagem=f"Posições do ranking inválidas: {posicoes}. Esperado: {esperado}.",
            )
        )

    ids_ranking = [item.get("id") for item in ranking]
    if len(ids_ranking) != len(set(ids_ranking)):
        problemas.append(
            Problema(
                gravidade="erro",
                codigo="RANKING_ESTRUTURA",
                caminho="ranking",
                mensagem="Identificadores repetidos no ranking.",
            )
        )

    if etapa == "curadoria":
        for r_id in ids_ranking:
            if r_id not in ids_cortes:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="RANKING_ESTRUTURA",
                        caminho="ranking",
                        mensagem=f"Corte {r_id} do ranking não existe na lista de cortes da curadoria.",
                    )
                )
        if prioridade not in ids_cortes:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="RANKING_ESTRUTURA",
                    caminho="prioridade_sugerida",
                    mensagem=f"Prioridade sugerida ({prioridade}) não existe nos cortes da curadoria.",
                )
            )

        # Regra 12: RANKING_TOPO (aviso, só na curadoria)
        notas_ranking: list[int] = []
        mapa_notas = {
            c.get("id"): c.get("potencial_viralizacao", {}).get("nota")
            for c in cortes
            if isinstance(c.get("potencial_viralizacao"), dict)
        }

        for r_id in ids_ranking:
            nota = mapa_notas.get(r_id)
            if isinstance(nota, int):
                notas_ranking.append(nota)

        if notas_ranking:
            menor_nota_ranking = min(notas_ranking)
            ids_ranking_set = set(ids_ranking)
            for c in cortes:
                cid = c.get("id")
                if cid not in ids_ranking_set:
                    c_nota = mapa_notas.get(cid)
                    if isinstance(c_nota, int) and c_nota > menor_nota_ranking:
                        problemas.append(
                            Problema(
                                gravidade="aviso",
                                codigo="RANKING_TOPO",
                                caminho="ranking",
                                mensagem=(
                                    f"Corte {cid} tem nota {c_nota}, maior que a menor nota "
                                    f"do ranking ({menor_nota_ranking})."
                                ),
                            )
                        )

    return problemas


def _validar_canal_e_credito(saida: dict[str, Any]) -> list[Problema]:
    """Aplica as regras 13, 14 e 15 sobre canal_original e crédito."""
    problemas: list[Problema] = []
    video_info = saida.get("video", {})
    canal = video_info.get("canal_original")
    alertas_gerais = saida.get("alertas_gerais", [])
    cortes = saida.get("cortes", [])

    # Regra 14: CANAL_YOUTUBE_OFICIAL
    if canal is not None and PADRAO_CANAL_OFICIAL.search(canal):
        problemas.append(
            Problema(
                gravidade="erro",
                codigo="CANAL_YOUTUBE_OFICIAL",
                caminho="video.canal_original",
                mensagem=f"Nome de canal '{canal}' parece genérico/oficial do YouTube.",
            )
        )

    # Regra 15: CANAL_NULO_SEM_ALERTA
    if canal is None:
        tem_alerta_canal = any("canal" in str(alerta).lower() for alerta in alertas_gerais)
        if not tem_alerta_canal:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="CANAL_NULO_SEM_ALERTA",
                    caminho="video.canal_original",
                    mensagem="Canal original é nulo mas nenhum alerta geral menciona 'canal'.",
                )
            )

    # Regra 13: CREDITO
    credito_esperado = f"Fonte: {canal}" if canal is not None else "Fonte: [confirmar canal]"
    for i, corte in enumerate(cortes):
        textos = corte.get("textos")
        if not textos or not isinstance(textos, dict):
            continue
        descricao = textos.get("descricao")
        if not descricao or not isinstance(descricao, dict):
            continue
        credito_informado = descricao.get("credito")
        if credito_informado != credito_esperado:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="CREDITO",
                    caminho=f"cortes[{i}].textos.descricao.credito",
                    mensagem=f"Crédito '{credito_informado}' diverge do esperado ('{credito_esperado}').",
                )
            )

    return problemas


def _validar_textos(saida: dict[str, Any]) -> list[Problema]:
    """Aplica as regras 16 a 21 sobre textos, limites, hashtags, enquetes e links."""
    problemas: list[Problema] = []
    cortes = saida.get("cortes", [])

    for i, corte in enumerate(cortes):
        caminho_corte = f"cortes[{i}]"
        textos = corte.get("textos")
        if textos is None:
            continue

        caminho_textos = f"{caminho_corte}.textos"
        itens_gerados = textos.get("itens_gerados", [])

        # Mapeamento do item gerado ao nome da chave do bloco no esquema
        mapa_blocos = {
            "titulo": "titulos",
            "descricao": "descricao",
            "texto_ancora": "textos_ancora",
            "enquete": "enquete",
        }

        # Regra 16: TEXTOS_ITENS
        if len(itens_gerados) != len(set(itens_gerados)):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEXTOS_ITENS",
                    caminho=f"{caminho_textos}.itens_gerados",
                    mensagem="Lista de itens_gerados contém duplicatas.",
                )
            )

        for item_nome, chave_bloco in mapa_blocos.items():
            bloco_presente = textos.get(chave_bloco) is not None
            item_listado = item_nome in itens_gerados
            if item_listado and not bloco_presente:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTOS_ITENS",
                        caminho=f"{caminho_textos}.itens_gerados",
                        mensagem=f"Item '{item_nome}' está em itens_gerados mas o bloco '{chave_bloco}' é nulo.",
                    )
                )
            elif bloco_presente and not item_listado:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTOS_ITENS",
                        caminho=f"{caminho_textos}.itens_gerados",
                        mensagem=f"Bloco '{chave_bloco}' está preenchido mas '{item_nome}' não está em itens_gerados.",
                    )
                )

        # Regra 17: TEXTO_TITULOS
        titulos = textos.get("titulos")
        if titulos is not None:
            caminho_titulos = f"{caminho_textos}.titulos"
            if len(titulos) != 3:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_TITULOS",
                        caminho=caminho_titulos,
                        mensagem=f"Esperado exatamente 3 títulos, recebido {len(titulos)}.",
                    )
                )
            for j, t in enumerate(titulos):
                caminho_t = f"{caminho_titulos}[{j}]"
                texto_t = t.get("texto", "")
                tam_real = len(texto_t)
                caracteres = t.get("caracteres")
                if tam_real > 100:
                    problemas.append(
                        Problema(
                            gravidade="erro",
                            codigo="TEXTO_TITULOS",
                            caminho=caminho_t,
                            mensagem=f"Título excede 100 caracteres ({tam_real} caracteres).",
                        )
                    )
                if caracteres != tam_real:
                    problemas.append(
                        Problema(
                            gravidade="erro",
                            codigo="TEXTO_TITULOS",
                            caminho=caminho_t,
                            mensagem=f"Campo caracteres ({caracteres}) diverge do tamanho real ({tam_real}).",
                        )
                    )

        # Regra 18: TEXTO_DESCRICAO
        descricao = textos.get("descricao")
        if descricao is not None:
            caminho_desc = f"{caminho_textos}.descricao"
            texto_d = descricao.get("texto", "")
            tam_real_d = len(texto_d)
            caracteres_texto = descricao.get("caracteres_texto")

            if caracteres_texto != tam_real_d:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_DESCRICAO",
                        caminho=caminho_desc,
                        mensagem=f"Campo caracteres_texto ({caracteres_texto}) diverge do tamanho real ({tam_real_d}).",
                    )
                )
            if tam_real_d == 0:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_DESCRICAO",
                        caminho=caminho_desc,
                        mensagem="Texto da descrição está vazio.",
                    )
                )
            if "#" in texto_d:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_DESCRICAO",
                        caminho=caminho_desc,
                        mensagem="Texto da descrição contém caractere '#' indevido.",
                    )
                )

            hashtags = descricao.get("hashtags", [])
            hashtags_normalizadas = [
                h.casefold() for h in hashtags if isinstance(h, str)
            ]
            if len(hashtags_normalizadas) != len(set(hashtags_normalizadas)):
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_DESCRICAO",
                        caminho=caminho_desc,
                        mensagem="Lista de hashtags contém termos repetidos.",
                    )
                )

        # Regra 19: TEXTO_ANCORA
        textos_ancora = textos.get("textos_ancora")
        if textos_ancora is not None:
            caminho_ancora = f"{caminho_textos}.textos_ancora"
            tipos = [item.get("tipo") for item in textos_ancora if isinstance(item, dict)]
            if tipos.count("padrao") != 1 or tipos.count("curto") != 1 or len(textos_ancora) != 2:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_ANCORA",
                        caminho=caminho_ancora,
                        mensagem="Deve haver exatamente um texto âncora 'padrao' e um 'curto'.",
                    )
                )

            for item in textos_ancora:
                if not isinstance(item, dict):
                    continue
                tipo = item.get("tipo")
                texto_a = item.get("texto", "")
                tam_a = len(texto_a)
                caracteres_a = item.get("caracteres")

                if caracteres_a != tam_a:
                    problemas.append(
                        Problema(
                            gravidade="erro",
                            codigo="TEXTO_ANCORA",
                            caminho=caminho_ancora,
                            mensagem=f"Âncora '{tipo}': campo caracteres ({caracteres_a}) diverge do real ({tam_a}).",
                        )
                    )
                if tipo == "padrao" and (tam_a < 100 or tam_a > 120):
                    problemas.append(
                        Problema(
                            gravidade="erro",
                            codigo="TEXTO_ANCORA",
                            caminho=caminho_ancora,
                            mensagem=f"Âncora 'padrao' com {tam_a} caracteres (permitido: 100 a 120).",
                        )
                    )
                if tipo == "curto" and tam_a > 60:
                    problemas.append(
                        Problema(
                            gravidade="erro",
                            codigo="TEXTO_ANCORA",
                            caminho=caminho_ancora,
                            mensagem=f"Âncora 'curto' com {tam_a} caracteres (máximo: 60).",
                        )
                    )

        # Regra 20: TEXTO_ENQUETE e TEXTO_ENQUETE_PERGUNTA
        enquete = textos.get("enquete")
        if enquete is not None:
            caminho_enquete = f"{caminho_textos}.enquete"
            texto_e = enquete.get("texto", "")
            tam_e = len(texto_e)
            caracteres_e = enquete.get("caracteres")

            if tam_e > 100:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_ENQUETE",
                        caminho=caminho_enquete,
                        mensagem=f"Texto da enquete excede 100 caracteres ({tam_e} caracteres).",
                    )
                )
            if caracteres_e != tam_e:
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_ENQUETE",
                        caminho=caminho_enquete,
                        mensagem=f"Enquete: campo caracteres ({caracteres_e}) diverge do real ({tam_e}).",
                    )
                )
            if not texto_e.rstrip().endswith("?"):
                problemas.append(
                    Problema(
                        gravidade="aviso",
                        codigo="TEXTO_ENQUETE_PERGUNTA",
                        caminho=caminho_enquete,
                        mensagem="Texto da enquete não termina com ponto de interrogação '?'.",
                    )
                )

    return problemas


def _validar_links(saida: dict[str, Any]) -> list[Problema]:
    """Aplica a regra 21 (TEXTO_LINK) verificando URLs e domínios em todos os campos de texto."""
    problemas: list[Problema] = []
    cortes = saida.get("cortes", [])

    for i, corte in enumerate(cortes):
        caminho_corte = f"cortes[{i}]"

        gancho = corte.get("gancho", "")
        if _contem_link(gancho):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEXTO_LINK",
                    caminho=f"{caminho_corte}.gancho",
                    mensagem="Gancho contém link, URL ou domínio não permitido.",
                )
            )

        descricao = corte.get("descricao", "")
        if _contem_link(descricao):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEXTO_LINK",
                    caminho=f"{caminho_corte}.descricao",
                    mensagem="Descrição do corte contém link, URL ou domínio não permitido.",
                )
            )

        textos = corte.get("textos")
        if not textos or not isinstance(textos, dict):
            continue

        caminho_textos = f"{caminho_corte}.textos"
        titulos = textos.get("titulos") or []
        for j, t in enumerate(titulos):
            if _contem_link(t.get("texto", "")):
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_LINK",
                        caminho=f"{caminho_textos}.titulos[{j}].texto",
                        mensagem="Título contém link, URL ou domínio não permitido.",
                    )
                )

        desc_texto = (textos.get("descricao") or {}).get("texto", "")
        if _contem_link(desc_texto):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEXTO_LINK",
                    caminho=f"{caminho_textos}.descricao.texto",
                    mensagem="Texto da descrição contém link, URL ou domínio não permitido.",
                )
            )

        textos_ancora = textos.get("textos_ancora") or []
        for j, item in enumerate(textos_ancora):
            if _contem_link(item.get("texto", "")):
                problemas.append(
                    Problema(
                        gravidade="erro",
                        codigo="TEXTO_LINK",
                        caminho=f"{caminho_textos}.textos_ancora[{j}].texto",
                        mensagem="Texto âncora contém link, URL ou domínio não permitido.",
                    )
                )

        enq_texto = (textos.get("enquete") or {}).get("texto", "")
        if _contem_link(enq_texto):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="TEXTO_LINK",
                    caminho=f"{caminho_textos}.enquete.texto",
                    mensagem="Texto da enquete contém link, URL ou domínio não permitido.",
                )
            )

    return problemas


def _validar_observacoes_e_frases(saida: dict[str, Any]) -> list[Problema]:
    """Aplica as regras 22 a 25 sobre observações obrigatórias e integridade de frases."""
    problemas: list[Problema] = []
    cortes = saida.get("cortes", [])

    for i, corte in enumerate(cortes):
        caminho_corte = f"cortes[{i}]"
        caminho_obs = f"{caminho_corte}.observacoes"
        observacoes = corte.get("observacoes", [])
        tipos_obs = {obs.get("tipo") for obs in observacoes if isinstance(obs, dict)}

        # Coleta de todos os textos editoriais do corte para a regra 22 (OBS_DADOS)
        textos_corte = [corte.get("gancho", ""), corte.get("descricao", "")]
        textos = corte.get("textos")
        if textos and isinstance(textos, dict):
            for t in textos.get("titulos") or []:
                textos_corte.append(t.get("texto", ""))
            desc = textos.get("descricao")
            if desc and isinstance(desc, dict):
                textos_corte.append(desc.get("texto", ""))
            for a in textos.get("textos_ancora") or []:
                textos_corte.append(a.get("texto", ""))
            enq = textos.get("enquete")
            if enq and isinstance(enq, dict):
                textos_corte.append(enq.get("texto", ""))

        tem_digito = any(PADRAO_DIGITO.search(txt) for txt in textos_corte)
        if tem_digito and "dados" not in tipos_obs:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="OBS_DADOS",
                    caminho=caminho_obs,
                    mensagem="Corte contém dígitos numéricos em seus textos mas não possui observação de 'dados'.",
                )
            )

        # Regra 23: OBS_VISUAL
        if corte.get("depende_visual") is True and "visual" not in tipos_obs:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="OBS_VISUAL",
                    caminho=caminho_obs,
                    mensagem="Corte depende de elementos visuais mas não possui observação do tipo 'visual'.",
                )
            )

        # Regra 24: OBS_RISCO
        if corte.get("risco_contexto") == "alto" and not (
            "contexto" in tipos_obs or "tema_sensivel" in tipos_obs
        ):
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="OBS_RISCO",
                    caminho=caminho_obs,
                    mensagem=(
                        "Risco de contexto é alto mas não há observação de 'contexto' ou 'tema_sensivel'."
                    ),
                )
            )

        # Regra 25: FRASE_VAZIA
        frase_inicio = corte.get("frase_inicio", "")
        if len(frase_inicio.strip()) < 3:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="FRASE_VAZIA",
                    caminho=f"{caminho_corte}.frase_inicio",
                    mensagem="Frase de início vazia ou com menos de 3 caracteres úteis.",
                )
            )

        frase_fim = corte.get("frase_fim", "")
        if len(frase_fim.strip()) < 3:
            problemas.append(
                Problema(
                    gravidade="erro",
                    codigo="FRASE_VAZIA",
                    caminho=f"{caminho_corte}.frase_fim",
                    mensagem="Frase de fim vazia ou com menos de 3 caracteres úteis.",
                )
            )

    return problemas


def validar_editorial(
    saida: dict[str, Any],
    *,
    duracao_min_s: float = 60.0,
    duracao_max_s: float = 180.0,
    max_cortes: int = 8,
) -> list[Problema]:
    """Aplica todas as regras editoriais independentes da transcrição.

    Assume que o esquema básico já é válido. Não altera o dicionário recebido.
    Retorna lista ordenada por (caminho, codigo, mensagem) sem duplicatas.
    """
    problemas: list[Problema] = []

    problemas.extend(_validar_tempo_e_cortes(saida, max_cortes))
    problemas.extend(_validar_faixa_duracao(saida, duracao_min_s, duracao_max_s))
    problemas.extend(_validar_ranking(saida))
    problemas.extend(_validar_canal_e_credito(saida))
    problemas.extend(_validar_textos(saida))
    problemas.extend(_validar_links(saida))
    problemas.extend(_validar_observacoes_e_frases(saida))

    # Garante tamanho máximo de 200 caracteres para todas as mensagens
    problemas_ajustados: list[Problema] = []
    for p in problemas:
        msg = p.mensagem
        if len(msg) > 200:
            msg = msg[:197] + "..."
        problemas_ajustados.append(
            Problema(
                gravidade=p.gravidade,
                codigo=p.codigo,
                caminho=p.caminho,
                mensagem=msg,
            )
        )

    # Ordenação por (caminho, codigo, mensagem) e remoção de duplicatas exatas
    return sorted(
        set(problemas_ajustados),
        key=lambda p: (p.caminho, p.codigo, p.mensagem),
    )


def verificar_saida(saida: dict[str, Any], **parametros: Any) -> list[Problema]:
    """Valida a saída contra o esquema e, se válida, aplica as regras editoriais.

    Se houver falha de esquema, retorna apenas problemas com código 'ESQUEMA'.
    """
    erros_esquema = esquema.validar_saida(saida)
    if erros_esquema:
        problemas_esquema: list[Problema] = []
        for erro_msg in erros_esquema:
            if ":" in erro_msg:
                caminho, _, _ = erro_msg.partition(":")
                caminho = caminho.strip()
            else:
                caminho = ""
            msg = erro_msg
            if len(msg) > 200:
                msg = msg[:197] + "..."
            problemas_esquema.append(
                Problema(
                    gravidade="erro",
                    codigo="ESQUEMA",
                    caminho=caminho,
                    mensagem=msg,
                )
            )
        return sorted(
            set(problemas_esquema),
            key=lambda p: (p.caminho, p.codigo, p.mensagem),
        )

    return validar_editorial(saida, **parametros)
