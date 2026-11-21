"""Testes para o módulo de validação editorial (Tarefa T04a)."""

import copy
from pathlib import Path

from cortesia import esquema, tempo
from cortesia.validacao import validar_editorial, verificar_saida

FIXTURES = Path(__file__).parent / "fixtures"
GABARITO_PATH = FIXTURES / "gabarito_textos_c1_c7_c8.json"


def carregar_gabarito() -> dict:
    """Carrega uma nova cópia do gabarito oficial em memória."""
    return esquema.carregar_json(GABARITO_PATH)


def montar_corte_sintetico(
    corte_base: dict,
    inicio_s: float,
    fim_s: float,
    c_id: str | None = None,
    com_edicao: bool = False,
) -> dict:
    """Gera um corte sintetico com tempos coerentes a partir de um corte existente."""
    novo = copy.deepcopy(corte_base)
    if c_id:
        novo["id"] = c_id
    novo["inicio"] = tempo.segundos_para_tempo(inicio_s)
    novo["fim"] = tempo.segundos_para_tempo(fim_s)
    duracao = round(fim_s - inicio_s, 2)
    novo["duracao_segundos"] = duracao
    novo["duracao_formatada"] = tempo.segundos_para_tempo(duracao)
    if com_edicao:
        novo["observacoes"].append(
            {"tipo": "edicao", "texto": "Trecho longo requer cortes rápidos."}
        )
    return novo


# --- Critérios de Aceite 1 e 2: Gabarito e Curadoria ---


def test_gabarito_oficial_sem_problemas():
    """Critério 1: verificar_saida(gabarito) devolve lista vazia."""
    dados = carregar_gabarito()
    problemas = verificar_saida(dados)
    assert problemas == []


def test_gabarito_curadoria_sem_problemas():
    """Critério 2: variante curadoria sem textos devolve lista vazia."""
    dados = carregar_gabarito()
    dados["etapa"] = "curadoria"
    for c in dados["cortes"]:
        c["textos"] = None
    problemas = verificar_saida(dados)
    assert problemas == []


# --- Critério 3: Testes de mutação para cada uma das 25 regras ---


def test_regra_01_tempo_duracao():
    """Regra 1: TEMPO_DURACAO erro quando duracao_confere é falso."""
    dados = carregar_gabarito()
    dados["cortes"][0]["duracao_segundos"] = 999.99
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEMPO_DURACAO"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].duracao_segundos"


def test_regra_02_tempo_ordem():
    """Regra 2: TEMPO_ORDEM erro quando fim <= inicio."""
    dados = carregar_gabarito()
    dados["cortes"][0]["fim"] = dados["cortes"][0]["inicio"]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEMPO_ORDEM"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].fim"


def test_regra_03_tempo_fora_do_video():
    """Regra 3: TEMPO_FORA_DO_VIDEO erro quando fim > video + 1.0 s."""
    dados = carregar_gabarito()
    # vídeo tem 00:23:44.88 -> 1424.88 s. Definimos fim para 1425.89 s (ultrapassa 1.0 s)
    dados["cortes"][0]["fim"] = tempo.segundos_para_tempo(1425.89)
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEMPO_FORA_DO_VIDEO"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].fim"


def test_regra_04_cortes_qtd():
    """Regra 4: CORTES_QTD erro quando cortes > max_cortes."""
    dados = carregar_gabarito()
    problemas = validar_editorial(dados, max_cortes=2)
    alvos = [p for p in problemas if p.codigo == "CORTES_QTD"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes"


def test_regra_05_cortes_id_duplicado():
    """Regra 5: CORTES_ID_DUPLICADO erro com ids repetidos."""
    dados = carregar_gabarito()
    dados["cortes"][1]["id"] = dados["cortes"][0]["id"]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CORTES_ID_DUPLICADO"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[1].id"


def test_regra_06_cortes_ordem():
    """Regra 6: CORTES_ORDEM erro quando inicio do corte atual < inicio do anterior."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]
    # c0: 10 a 75; c1: 5 a 70 (inicia antes de c0)
    c0 = montar_corte_sintetico(base, 10.0, 75.0, "C1")
    c1 = montar_corte_sintetico(base, 5.0, 70.0, "C2")
    dados["cortes"] = [c0, c1]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CORTES_ORDEM"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[1].inicio"


def test_regra_07_cortes_sobrepostos():
    """Regra 7: CORTES_SOBREPOSTOS erro quando inicio do corte atual < fim do anterior."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]
    # c0: 10 a 80; c1: 75 a 140 (75 < 80 sobrepõe)
    c0 = montar_corte_sintetico(base, 10.0, 80.0, "C1")
    c1 = montar_corte_sintetico(base, 75.0, 140.0, "C2")
    dados["cortes"] = [c0, c1]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CORTES_SOBREPOSTOS"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[1].inicio"


def test_regra_08_cortes_consecutivos():
    """Regra 8: CORTES_CONSECUTIVOS erro quando intervalo < 1.0 s sem alerta conjunto."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]
    c0 = montar_corte_sintetico(base, 10.0, 80.0, "C1")
    c1 = montar_corte_sintetico(base, 80.5, 150.0, "C2")
    dados["cortes"] = [c0, c1]
    dados["alertas_gerais"] = ["Cortes C1 e C10 são próximos"]  # C10 não é C2
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CORTES_CONSECUTIVOS"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[1]"

    # Com alerta citando \bC1\b e \bC2\b, o problema desaparece
    dados["alertas_gerais"] = ["Cortes C1 e C2 são consecutivos e deliberados."]
    assert not any(p.codigo == "CORTES_CONSECUTIVOS" for p in validar_editorial(dados))


def test_regra_09_duracao_faixa():
    """Regra 9: DURACAO_FAIXA erro para duração fora de [min, max] sem edição."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]
    c0 = montar_corte_sintetico(base, 10.0, 50.0, "C1")  # 40 s < 60 s
    dados["cortes"] = [c0]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "DURACAO_FAIXA"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].duracao_segundos"

    # Com observação de edição o erro não ocorre
    c0_ed = montar_corte_sintetico(base, 10.0, 50.0, "C1", com_edicao=True)
    dados["cortes"] = [c0_ed]
    assert not any(p.codigo == "DURACAO_FAIXA" for p in validar_editorial(dados))


def test_regra_10_duracao_margem():
    """Regra 10: DURACAO_MARGEM erro para duração > max - 5 s e <= max sem edição."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]
    c0 = montar_corte_sintetico(base, 10.0, 187.0, "C1")  # 177 s (> 175 s e <= 180 s)
    dados["cortes"] = [c0]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "DURACAO_MARGEM"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].duracao_segundos"

    # Com observação de edição o erro não ocorre
    c0_ed = montar_corte_sintetico(base, 10.0, 187.0, "C1", com_edicao=True)
    dados["cortes"] = [c0_ed]
    assert not any(p.codigo == "DURACAO_MARGEM" for p in validar_editorial(dados))


def test_regra_11_ranking_estrutura():
    """Regra 11: RANKING_ESTRUTURA para ranking > 3, posições fora de ordem ou ids repetidos."""
    dados = carregar_gabarito()
    dados["ranking"].append({"posicao": 4, "id": "C7", "ponderacao": "Extra"})
    problemas = validar_editorial(dados)
    assert any(p.codigo == "RANKING_ESTRUTURA" for p in problemas)


def test_regra_12_ranking_topo():
    """Regra 12: RANKING_TOPO aviso na curadoria se corte fora tem nota maior que menor do ranking."""
    dados = carregar_gabarito()
    dados["etapa"] = "curadoria"
    for c in dados["cortes"]:
        c["textos"] = None
    # Corte C7 tem nota 8. Criamos corte C99 fora do ranking com nota 10
    base = dados["cortes"][0]
    c_extra = montar_corte_sintetico(base, 600.0, 670.0, "C99")
    c_extra["potencial_viralizacao"]["nota"] = 10
    c_extra["textos"] = None
    dados["cortes"].append(c_extra)

    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "RANKING_TOPO"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "aviso"
    assert alvos[0].caminho == "ranking"


def test_regra_13_credito():
    """Regra 13: CREDITO erro se crédito divergir de 'Fonte: <canal>' ou 'Fonte: [confirmar canal]'."""
    dados = carregar_gabarito()
    dados["cortes"][0]["textos"]["descricao"]["credito"] = "Fonte: Outro Canal"
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CREDITO"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].textos.descricao.credito"

    # Canal original nulo exige 'Fonte: [confirmar canal]'
    dados["video"]["canal_original"] = None
    dados["alertas_gerais"] = ["confirmar canal original"]
    dados["cortes"][0]["textos"]["descricao"]["credito"] = "Fonte: Incorreto"
    problemas = validar_editorial(dados)
    assert any(p.codigo == "CREDITO" for p in problemas)


def test_regra_14_canal_youtube_oficial():
    """Regra 14: CANAL_YOUTUBE_OFICIAL erro quando canal parece genérico oficial do YouTube."""
    dados = carregar_gabarito()
    dados["video"]["canal_original"] = "YouTube Oficial"
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CANAL_YOUTUBE_OFICIAL"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "video.canal_original"


def test_regra_15_canal_nulo_sem_alerta():
    """Regra 15: CANAL_NULO_SEM_ALERTA erro quando canal é nulo e nenhum alerta cita canal."""
    dados = carregar_gabarito()
    dados["video"]["canal_original"] = None
    dados["alertas_gerais"] = ["Alerta qualquer sobre áudio"]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "CANAL_NULO_SEM_ALERTA"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "video.canal_original"


def test_regra_16_textos_itens():
    """Regra 16: TEXTOS_ITENS erro para duplicata ou bloco nulo."""
    dados = carregar_gabarito()
    dados["cortes"][0]["textos"]["itens_gerados"].append("titulo")
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEXTOS_ITENS"]
    assert len(alvos) >= 1
    assert alvos[0].caminho == "cortes[0].textos.itens_gerados"


def test_regra_17_texto_titulos():
    """Regra 17: TEXTO_TITULOS erro quando contagem != 3, tamanho > 100 ou caracteres difere."""
    dados = carregar_gabarito()
    dados["cortes"][0]["textos"]["titulos"].pop()  # ficam 2
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEXTO_TITULOS"]
    assert len(alvos) >= 1
    assert alvos[0].caminho == "cortes[0].textos.titulos"


def test_regra_18_texto_descricao():
    """Regra 18: TEXTO_DESCRICAO erro com '#', caracteres difere ou hashtag repetida."""
    dados = carregar_gabarito()
    desc = dados["cortes"][0]["textos"]["descricao"]
    desc["texto"] += " #"
    desc["caracteres_texto"] = len(desc["texto"])
    desc["hashtags"].append(desc["hashtags"][0])
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEXTO_DESCRICAO"]
    assert len(alvos) >= 1
    assert alvos[0].caminho == "cortes[0].textos.descricao"


def test_regra_19_texto_ancora():
    """Regra 19: TEXTO_ANCORA erro para tamanho fora dos limites ou tipos incorretos."""
    dados = carregar_gabarito()
    ancora = dados["cortes"][0]["textos"]["textos_ancora"]
    # Curto acima de 60 caracteres
    ancora[1]["texto"] = "A" * 65
    ancora[1]["caracteres"] = 65
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEXTO_ANCORA"]
    assert len(alvos) >= 1
    assert alvos[0].caminho == "cortes[0].textos.textos_ancora"


def test_regra_20_texto_enquete_e_pergunta():
    """Regra 20: TEXTO_ENQUETE erro (>100) e TEXTO_ENQUETE_PERGUNTA aviso (sem '?')."""
    dados = carregar_gabarito()
    enquete = dados["cortes"][0]["textos"]["enquete"]
    enquete["texto"] = "Você investiria no Banco do Brasil agora"  # sem ?
    enquete["caracteres"] = len(enquete["texto"])
    problemas = validar_editorial(dados)
    avisos = [p for p in problemas if p.codigo == "TEXTO_ENQUETE_PERGUNTA"]
    assert len(avisos) == 1
    assert avisos[0].gravidade == "aviso"
    assert avisos[0].caminho == "cortes[0].textos.enquete"


def test_regra_21_texto_link():
    """Regra 21: TEXTO_LINK erro ao conter URL ou domínio."""
    dados = carregar_gabarito()
    dados["cortes"][0]["gancho"] = "Veja no site example.com os detalhes."
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "TEXTO_LINK"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].gancho"


def test_regra_22_obs_dados():
    """Regra 22: OBS_DADOS erro se houver dígitos sem observação do tipo dados."""
    dados = carregar_gabarito()
    # Remove observação de tipo dados
    dados["cortes"][0]["observacoes"] = [
        obs for obs in dados["cortes"][0]["observacoes"] if obs["tipo"] != "dados"
    ]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "OBS_DADOS"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].observacoes"


def test_regra_23_obs_visual():
    """Regra 23: OBS_VISUAL erro se depende_visual=True sem observação visual."""
    dados = carregar_gabarito()
    dados["cortes"][0]["observacoes"] = [
        obs for obs in dados["cortes"][0]["observacoes"] if obs["tipo"] != "visual"
    ]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "OBS_VISUAL"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].observacoes"


def test_regra_24_obs_risco():
    """Regra 24: OBS_RISCO erro se risco_contexto='alto' sem contexto ou tema_sensivel."""
    dados = carregar_gabarito()
    dados["cortes"][0]["risco_contexto"] = "alto"
    dados["cortes"][0]["observacoes"] = [
        obs
        for obs in dados["cortes"][0]["observacoes"]
        if obs["tipo"] not in ("contexto", "tema_sensivel")
    ]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "OBS_RISCO"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].observacoes"


def test_regra_25_frase_vazia():
    """Regra 25: FRASE_VAZIA erro se frase_inicio ou frase_fim tiver menos de 3 caracteres úteis."""
    dados = carregar_gabarito()
    dados["cortes"][0]["frase_inicio"] = "  oi  "  # apenas 2 caracteres úteis
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "FRASE_VAZIA"]
    assert len(alvos) == 1
    assert alvos[0].gravidade == "erro"
    assert alvos[0].caminho == "cortes[0].frase_inicio"


# --- Critério 4: Múltiplos problemas no mesmo corte ---


def test_multiplos_erros_mesmo_corte():
    """Critério 4: link + caracteres errado + hashtags repetidas + dígito sem observação dados."""
    dados = carregar_gabarito()
    corte = dados["cortes"][0]
    corte["gancho"] = "Confira em bit.ly/promo lucro de 87%."
    corte["observacoes"] = [o for o in corte["observacoes"] if o["tipo"] != "dados"]
    desc = corte["textos"]["descricao"]
    desc["caracteres_texto"] = 1
    desc["hashtags"].append(desc["hashtags"][0])

    problemas = validar_editorial(dados)
    codigos = {p.codigo for p in problemas}
    assert "TEXTO_LINK" in codigos
    assert "TEXTO_DESCRICAO" in codigos
    assert "OBS_DADOS" in codigos


# --- Critérios 5, 6 e 7: Ordenação, Deduplicação, Esquema e Imutabilidade ---


def test_ordenacao_e_deduplicacao():
    """Critério 5 e ajuste 3: lista sai ordenada por (caminho, codigo, mensagem) sem duplicatas."""
    dados = carregar_gabarito()
    # Provoca múltiplos erros em caminhos diferentes
    dados["cortes"][0]["gancho"] = "Link http://a.com"
    dados["cortes"][1]["gancho"] = "Link http://b.com"

    problemas = validar_editorial(dados)
    tuplas = [(p.caminho, p.codigo, p.mensagem) for p in problemas]
    assert tuplas == sorted(tuplas)
    assert len(problemas) == len(set(problemas))


def test_verificar_saida_esquema_invalido():
    """Critério 6: verificar_saida com erro de esquema devolve apenas ESQUEMA."""
    dados = carregar_gabarito()
    dados["etapa"] = "invalida"
    problemas = verificar_saida(dados)
    assert len(problemas) >= 1
    assert all(p.codigo == "ESQUEMA" for p in problemas)
    assert any("etapa" in p.caminho for p in problemas)


def test_validar_editorial_nao_muta_e_mensagens_curtas():
    """Critério 7: não muta o dict original e todas as mensagens têm <= 200 caracteres."""
    dados = carregar_gabarito()
    copia = copy.deepcopy(dados)
    problemas = validar_editorial(dados)
    assert dados == copia
    assert all(len(p.mensagem) <= 200 for p in problemas)


# --- Critério 8 e Ajuste 4: Testes de Borda Obrigatórios ---


def test_bordas_duracao_e_edicao():
    """Ajuste 4: testes de borda com centésimos exatos e observação de edição."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]

    # 60.00 s: sem problema
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 60.00, "C1")]
    assert not any(p.codigo in ("DURACAO_FAIXA", "DURACAO_MARGEM") for p in validar_editorial(dados))

    # 59.99 s: DURACAO_FAIXA
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 59.99, "C1")]
    problemas = validar_editorial(dados)
    assert any(p.codigo == "DURACAO_FAIXA" for p in problemas)
    # Com edicao: sem problema
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 59.99, "C1", com_edicao=True)]
    assert not any(p.codigo in ("DURACAO_FAIXA", "DURACAO_MARGEM") for p in validar_editorial(dados))

    # 175.00 s: sem problema
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 175.00, "C1")]
    assert not any(p.codigo in ("DURACAO_FAIXA", "DURACAO_MARGEM") for p in validar_editorial(dados))

    # 175.01 s: DURACAO_MARGEM
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 175.01, "C1")]
    problemas = validar_editorial(dados)
    assert any(p.codigo == "DURACAO_MARGEM" for p in problemas)
    # Com edicao: sem problema
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 175.01, "C1", com_edicao=True)]
    assert not any(p.codigo in ("DURACAO_FAIXA", "DURACAO_MARGEM") for p in validar_editorial(dados))

    # 180.00 s: DURACAO_MARGEM
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 180.00, "C1")]
    problemas = validar_editorial(dados)
    assert any(p.codigo == "DURACAO_MARGEM" for p in problemas)
    # Com edicao: sem problema
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 180.00, "C1", com_edicao=True)]
    assert not any(p.codigo in ("DURACAO_FAIXA", "DURACAO_MARGEM") for p in validar_editorial(dados))

    # 180.01 s: DURACAO_FAIXA
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 180.01, "C1")]
    problemas = validar_editorial(dados)
    assert any(p.codigo == "DURACAO_FAIXA" for p in problemas)
    # Com edicao: sem problema
    dados["cortes"] = [montar_corte_sintetico(base, 0.0, 180.01, "C1", com_edicao=True)]
    assert not any(p.codigo in ("DURACAO_FAIXA", "DURACAO_MARGEM") for p in validar_editorial(dados))


def test_bordas_intervalo_cortes_consecutivos():
    """Ajuste 4: intervalo de 1.00 s vs 0.99 s entre cortes."""
    dados = carregar_gabarito()
    base = dados["cortes"][0]
    dados["alertas_gerais"] = []

    # Intervalo de 1.00 s (ex.: 80.00 a 81.00): sem CORTES_CONSECUTIVOS
    c0 = montar_corte_sintetico(base, 10.0, 80.0, "C1")
    c1 = montar_corte_sintetico(base, 81.0, 150.0, "C2")
    dados["cortes"] = [c0, c1]
    assert not any(p.codigo == "CORTES_CONSECUTIVOS" for p in validar_editorial(dados))

    # Intervalo de 0.99 s (ex.: 80.00 a 80.99): CORTES_CONSECUTIVOS
    c1_consec = montar_corte_sintetico(base, 80.99, 150.0, "C2")
    dados["cortes"] = [c0, c1_consec]
    problemas = validar_editorial(dados)
    assert any(p.codigo == "CORTES_CONSECUTIVOS" for p in problemas)


# --- Testes adicionais obrigatórios solicitados pelo usuário ---


def test_ranking_etapa_textos_cita_id_inexistente():
    """Etapa 'textos' com ranking citando um id que não está em 'cortes': sem problema."""
    dados = carregar_gabarito()
    assert dados["etapa"] == "textos"
    # C8 está no ranking do gabarito. Vamos remover C8 de cortes, deixando só C1 e C7
    dados["cortes"] = [c for c in dados["cortes"] if c["id"] != "C8"]
    problemas = validar_editorial(dados)
    assert not any(p.codigo == "RANKING_ESTRUTURA" for p in problemas)


def test_ranking_etapa_curadoria_cita_id_inexistente():
    """Etapa 'curadoria' com ranking citando id inexistente: RANKING_ESTRUTURA."""
    dados = carregar_gabarito()
    dados["etapa"] = "curadoria"
    for c in dados["cortes"]:
        c["textos"] = None
    # Remove C8 de cortes
    dados["cortes"] = [c for c in dados["cortes"] if c["id"] != "C8"]
    problemas = validar_editorial(dados)
    alvos = [p for p in problemas if p.codigo == "RANKING_ESTRUTURA"]
    assert len(alvos) >= 1
    assert alvos[0].caminho == "ranking"


def test_textos_itens_dois_sentidos():
    """TEXTOS_ITENS nos dois sentidos: item listado com bloco nulo e bloco preenchido não listado."""
    dados = carregar_gabarito()

    # Sentido 1: item listado em itens_gerados mas bloco é nulo
    d1 = copy.deepcopy(dados)
    d1["cortes"][0]["textos"]["enquete"] = None
    assert "enquete" in d1["cortes"][0]["textos"]["itens_gerados"]
    p1 = validar_editorial(d1)
    alvos1 = [p for p in p1 if p.codigo == "TEXTOS_ITENS"]
    assert len(alvos1) == 1
    assert "bloco 'enquete' é nulo" in alvos1[0].mensagem

    # Sentido 2: bloco preenchido não listado em itens_gerados
    d2 = copy.deepcopy(dados)
    d2["cortes"][0]["textos"]["itens_gerados"].remove("enquete")
    assert d2["cortes"][0]["textos"]["enquete"] is not None
    p2 = validar_editorial(d2)
    alvos2 = [p for p in p2 if p.codigo == "TEXTOS_ITENS"]
    assert len(alvos2) == 1
    assert "não está em itens_gerados" in alvos2[0].mensagem


def test_dois_problemas_mesmo_caminho_e_codigo():
    """Dois problemas diferentes no mesmo caminho e código aparecem como dois itens."""
    dados = carregar_gabarito()
    # Título com 101 caracteres E campo caracteres divergente (ex.: 50 != 101)
    titulo_obj = dados["cortes"][0]["textos"]["titulos"][0]
    titulo_obj["texto"] = "A" * 101
    titulo_obj["caracteres"] = 50

    problemas = validar_editorial(dados)
    alvos = [
        p
        for p in problemas
        if p.caminho == "cortes[0].textos.titulos[0]" and p.codigo == "TEXTO_TITULOS"
    ]
    assert len(alvos) == 2
    mensagens = {p.mensagem for p in alvos}
    assert any("excede 100 caracteres" in m for m in mensagens)
    assert any("diverge do tamanho real" in m for m in mensagens)
