"""
Módulo de Processamento de Linguagem Natural (NLP) e Cálculo de Tendências.

O que faz:
    Analisa o conjunto de publicações de redes sociais (vídeos, títulos, descrições)
    para calcular a Nuvem de Termos Ponderada (12h, 24h, 48h) e o ranking Top 10
    por campo político (Pró-Oposição vs Campo Popular / Léo).
"""

import unicodedata
from datetime import datetime

from config import FUSO_CE, calcular_idade_horas

def normalizar_texto(texto):
    """
    Remove acentos e converte para minúsculas.
    """
    if not texto:
        return ""
    nfd = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

# Termos monitorados para a nuvem de palavras
TERMOS_RADAR_NUVEM = [
    ("Ciro Gomes", "disputa", ["ciro gomes", "ciro"]),
    ("Léo Suricate", "nossa", ["leo suricate", "leosuricate", "suricate"]),
    ("Ônibus e Terminais", "nossa", ["onibus", "terminal", "transporte", "parangaba", "messejana"]),
    ("Lula", "nossa", ["lula"]),
    ("Fim da 6x1", "nossa", ["6x1", "escala 6x1", "trabalhador"]),
    ("André Fernandes", "deles", ["andre fernandes", "andrefernandes"]),
    ("Elmano de Freitas", "nossa", ["elmano"]),
    ("Cid Gomes", "disputa", ["cid gomes", "cid"]),
    ("Assembleia Legislativa", "disputa", ["assembleia legislativa", "alece"]),
    ("Capitão Wagner", "deles", ["capitao wagner", "wagner"]),
    ("Tiririca", "disputa", ["tiririca"]),
    ("Carmelo Neto", "deles", ["carmelo neto", "carmelo"]),
    ("Direita Fortaleza", "deles", ["direita", "bolsonaro", "pl"]),
    ("Pé-de-Meia", "nossa", ["pe-de-meia", "pe de meia"]),
    ("Passe Livre", "nossa", ["passe livre", "tarifa zero"]),
    ("Segurança e Facções", "deles", ["seguranca", "faccao", "crime", "policia"]),
    ("Cultura Periférica", "nossa", ["periferia", "cultura", "cuca"]),
    ("Cláudio Pinho", "disputa", ["claudio pinho"]),
    ("Prefeitura Fortaleza", "disputa", ["prefeitura", "evandro leitao", "sarto"]),
    ("Camilo Santana", "nossa", ["camilo santana", "camilo"]),
    ("Areninhas e Juventude", "nossa", ["areninha", "juventude", "batalha"]),
    ("Críticas a Elmano", "deles", ["critica elmano", "oposicao", "denuncia", "rombo"]),
    ("IPVA e Tributos", "deles", ["ipva", "tributos", "impostos", "taxa"]),
    ("Gastos Públicos", "deles", ["gasto", "gastos", "desperdicio"])
]

TEMAS_OPOSICAO = [
    ("André Fernandes", ["andre fernandes", "andrefernandes"]),
    ("Capitão Wagner", ["capitao wagner", "wagner"]),
    ("Carmelo Neto", ["carmelo neto", "carmelo"]),
    ("Segurança e Facções", ["seguranca", "faccao", "crime", "policia"]),
    ("Críticas a Elmano", ["critica", "rombo", "saude em crise", "denuncia", "oposicao"]),
    ("IPVA e Tributos", ["ipva", "tributo", "imposto", "taxa"]),
    ("Direita Fortaleza", ["direita", "bolsonaro", "pl"]),
    ("Polícia Militar", ["policia militar", "raio", "pm"]),
    ("Tiririca / Crítica", ["tiririca"]),
    ("Gastos Públicos", ["gasto publico", "orcamento", "alece"])
]

TEMAS_CAMPO_POPULAR = [
    ("Léo Suricate", ["leo suricate", "suricate"]),
    ("Ônibus e Terminais", ["onibus", "terminal", "transporte", "parangaba", "messejana"]),
    ("Lula / Mobilização", ["lula", "governo federal"]),
    ("Fim da 6x1", ["6x1", "escala 6x1", "trabalhador"]),
    ("Elmano de Freitas", ["elmano"]),
    ("Camilo Santana", ["camilo santana", "camilo"]),
    ("Passe Livre", ["passe livre", "tarifa zero", "passagem"]),
    ("Cultura Periférica", ["cultura", "periferia", "cuca", "rima"]),
    ("Pé-de-Meia", ["pe-de-meia", "pe de meia", "estudante"]),
    ("Areninhas e Juventude", ["areninha", "juventude", "esporte"])
]

def _extrair_ranking_temas_videos(sub_vids, campo_alvo, temas_fallback, videos_classificados_map=None, sub_comentarios=None):
    """
    Extrai o ranking dinâmico de temas para um campo político ('oposicao' ou 'popular'),
    associando os vídeos correspondentes e ponderando a intensidade a partir dos comentários populares.
    """
    # 1. Agrupar comentários por ID do vídeo
    comentarios_por_vid = {}
    if sub_comentarios:
        for c in sub_comentarios:
            vid = c.get("video_id")
            if vid:
                if vid not in comentarios_por_vid:
                    comentarios_por_vid[vid] = []
                comentarios_por_vid[vid].append(c)

    mapa_temas = {}  # tema -> list de vídeos com estatísticas

    # 2. Agrupamento dinâmico via IA (Google Gemini)
    if videos_classificados_map:
        for v in sub_vids:
            vid = v.get("id")
            c_info = videos_classificados_map.get(vid)
            if c_info and c_info.get("campo") == campo_alvo:
                t_nome = (c_info.get("tema") or "").strip()
                if t_nome and t_nome.lower() not in ["ruido", "irrelevante", "neutro", "política cearense"]:
                    if t_nome not in mapa_temas:
                        mapa_temas[t_nome] = []
                    if not any(item["id"] == vid for item in mapa_temas[t_nome]):
                        comms_v = comentarios_por_vid.get(vid, [])
                        mapa_temas[t_nome].append({
                            "id": vid,
                            "titulo": v.get("titulo", "Vídeo no YouTube"),
                            "canal": v.get("canal", "Canal Cearense"),
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "publishedAt": v.get("publishedAt", ""),
                            "qtd_comentarios": len(comms_v),
                            "amostras_comentarios": [c.get("texto", "") for c in comms_v[:3]]
                        })

    # 3. Complemento / Fallback com verificação por palavras-chave (em títulos E comentários)
    for t_nome, aliases in temas_fallback:
        vids_match = []
        aliases_norm = [normalizar_texto(a) for a in aliases]
        for v in sub_vids:
            vid = v.get("id")
            comms_v = comentarios_por_vid.get(vid, [])
            textos_comms = [c.get("texto", "") for c in comms_v]
            txt_v = normalizar_texto(v.get("titulo", "") + " " + (v.get("desc") or "") + " " + " ".join(textos_comms))

            if any(a in txt_v for a in aliases_norm):
                vids_match.append({
                    "id": vid,
                    "titulo": v.get("titulo", "Vídeo no YouTube"),
                    "canal": v.get("canal", "Canal Cearense"),
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "publishedAt": v.get("publishedAt", ""),
                    "qtd_comentarios": len(comms_v),
                    "amostras_comentarios": [c.get("texto", "") for c in comms_v[:3]]
                })

        if vids_match:
            if t_nome not in mapa_temas:
                mapa_temas[t_nome] = vids_match
            else:
                for vm in vids_match:
                    if not any(item["id"] == vm["id"] for item in mapa_temas[t_nome]):
                        mapa_temas[t_nome].append(vm)

    # 4. Se nenhum tema tiver sido pontuado, carrega temas padrão com lista vazia
    if not mapa_temas:
        for t_nome, _ in temas_fallback[:6]:
            mapa_temas[t_nome] = []

    # 5. Cálculo de pesos relativos e porcentagens considerando presença de vídeos e engajamento popular
    scores = []
    for t_nome, vids_list in mapa_temas.items():
        total_comms = sum(vm.get("qtd_comentarios", 0) for vm in vids_list)
        # Score ponderado: base por vídeo + engajamento dos comentários populares
        score = (len(vids_list) * 2) + total_comms
        if len(vids_list) == 0:
            score = 1
        scores.append((t_nome, score, total_comms, vids_list))

    scores.sort(key=lambda x: (x[1], len(x[3])), reverse=True)
    tot = sum(s for _, s, _, _ in scores) or 1

    itens = []
    for t_nome, s, total_comms, vids_list in scores[:10]:
        pct_val = round((s / tot) * 100, 1)
        itens.append({
            "termo": t_nome,
            "pct": f"{pct_val}%".replace(".", ","),
            "valor": pct_val,
            "qtd_videos": len(vids_list),
            "qtd_comentarios": total_comms,
            "videos": vids_list
        })

    return itens

def analisar_corpus_videos(sub_vids, horas_label, videos_classificados_map=None, sub_comentarios=None):
    """
    Calcula as frequências de menções aos temas do Ceará para a janela temporal,
    unindo o texto dos títulos com o vocabulário real dos comentários populares.
    """
    textos = [v.get("titulo", "") + " " + v.get("desc", "") for v in sub_vids]
    if sub_comentarios:
        textos.extend([c.get("texto", "") for c in sub_comentarios])

    full_text = normalizar_texto(" ".join(textos))
    hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")

    # 1. Nuvem de Palavras
    ocorrencias = []
    for nome, lado, aliases in TERMOS_RADAR_NUVEM:
        cnt = sum(full_text.count(normalizar_texto(a)) for a in aliases)
        if cnt > 0:
            ocorrencias.append((nome, lado, cnt))

    ocorrencias.sort(key=lambda x: x[2], reverse=True)
    max_c = ocorrencias[0][2] if ocorrencias else 1
    nuvem_out = []
    for n, l, c in ocorrencias[:18]:
        peso = int(40 + round((c / max_c) * 58))
        peso = max(38, min(98, peso))
        nuvem_out.append({"t": n, "peso": peso, "lado": l})

    # Rankings com vídeos e comentários associados
    itens_deles = _extrair_ranking_temas_videos(sub_vids, "oposicao", TEMAS_OPOSICAO, videos_classificados_map, sub_comentarios)
    itens_nossa = _extrair_ranking_temas_videos(sub_vids, "popular", TEMAS_CAMPO_POPULAR, videos_classificados_map, sub_comentarios)

    return {
        "total_videos": len(sub_vids),
        "total_comentarios": len(sub_comentarios) if sub_comentarios else 0,
        "janela": horas_label,
        "nuvem": nuvem_out,
        "videos_mais_falados": {
            "hora": hora_ce,
            "janela": horas_label,
            "total_videos": len(sub_vids),
            "total_comentarios": len(sub_comentarios) if sub_comentarios else 0,
            "oposicao": {"titulo": "PRÓ-OPOSIÇÃO", "itens": itens_deles},
            "popular": {"titulo": "CAMPO POPULAR / LÉO", "itens": itens_nossa}
        }
    }

def construir_monitor_redes(corpus_videos, itens_google_4h, itens_google_24h, videos_classificados_map=None, corpus_comentarios=None):
    """
    Consolida as janelas temporais de vídeos e comentários (1h, 2h, 12h, 24h e 7d) com o Google Trends CE.
    """
    if corpus_comentarios is None:
        corpus_comentarios = []

    vids_1h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 1] or corpus_videos[:5]
    vids_2h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 2] or corpus_videos[:8]
    vids_12h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 12] or corpus_videos[:15]
    vids_24h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 24] or corpus_videos[:30]
    vids_7d = [v for v in corpus_videos if v.get("idade_horas", 999) <= 168] or corpus_videos

    comms_1h = [c for c in corpus_comentarios if calcular_idade_horas(c.get("data")) <= 1] or corpus_comentarios[:20]
    comms_2h = [c for c in corpus_comentarios if calcular_idade_horas(c.get("data")) <= 2] or corpus_comentarios[:40]
    comms_12h = [c for c in corpus_comentarios if calcular_idade_horas(c.get("data")) <= 12] or corpus_comentarios[:80]
    comms_24h = [c for c in corpus_comentarios if calcular_idade_horas(c.get("data")) <= 24] or corpus_comentarios[:150]
    comms_7d = [c for c in corpus_comentarios if calcular_idade_horas(c.get("data")) <= 168] or corpus_comentarios

    res_1h = analisar_corpus_videos(vids_1h, "1h", videos_classificados_map, comms_1h)
    res_2h = analisar_corpus_videos(vids_2h, "2h", videos_classificados_map, comms_2h)
    res_12h = analisar_corpus_videos(vids_12h, "12h", videos_classificados_map, comms_12h)
    res_24h = analisar_corpus_videos(vids_24h, "24h", videos_classificados_map, comms_24h)
    res_7d = analisar_corpus_videos(vids_7d, "7d", videos_classificados_map, comms_7d)

    if not itens_google_4h:
        itens_google_4h = itens_google_24h

    hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")
    google_trends_ce = {
        "hora": hora_ce,
        "janela": "4h",
        "itens": itens_google_4h,
        "itens_4h": itens_google_4h,
        "itens_24h": itens_google_24h
    }

    return {
        "nuvem": res_24h["nuvem"],
        "nuvens_por_janela": {
            "1h": res_1h["nuvem"],
            "2h": res_2h["nuvem"],
            "12h": res_12h["nuvem"],
            "24h": res_24h["nuvem"],
            "7d": res_7d["nuvem"]
        },
        "videos_mais_falados_ce": res_24h["videos_mais_falados"],
        "videos_por_janela": {
            "1h": res_1h["videos_mais_falados"],
            "2h": res_2h["videos_mais_falados"],
            "12h": res_12h["videos_mais_falados"],
            "24h": res_24h["videos_mais_falados"],
            "7d": res_7d["videos_mais_falados"]
        },
        "google_trends_ce": google_trends_ce
    }

def gerar_nuvem_instagram(comentarios_ig):
    """
    Gera a nuvem de palavras ponderada específica do Instagram a partir dos comentários
    e legendas de posts monitorados de lideranças e veículos cearenses.
    """
    if not comentarios_ig:
        return []

    textos = [c.get("texto", "") + " " + c.get("origem_titulo", "") for c in comentarios_ig]
    full_text = normalizar_texto(" ".join(textos))

    ocorrencias = []
    for nome, lado, aliases in TERMOS_RADAR_NUVEM:
        cnt = sum(full_text.count(normalizar_texto(a)) for a in aliases)
        if cnt > 0:
            ocorrencias.append((nome, lado, cnt))

    ocorrencias.sort(key=lambda x: x[2], reverse=True)
    max_c = ocorrencias[0][2] if ocorrencias else 1
    nuvem_out = []
    for n, l, c in ocorrencias[:18]:
        peso = int(40 + round((c / max_c) * 58))
        peso = max(38, min(98, peso))
        nuvem_out.append({"t": n, "peso": peso, "lado": l, "contagem": c})

    return nuvem_out

def gerar_ranking_posts_instagram(comentarios_ig):
    """
    Gera o ranking 'Mais Falados no Instagram' por campo político (Pró-Oposição vs Campo Popular / Léo),
    avaliando tanto os comentários quanto as legendas e textos dos posts monitorados,
    associando os posts correspondentes a cada tema para viabilizar gaveta interativa no frontend.
    """
    if not comentarios_ig:
        return {
            "total_posts": 0,
            "oposicao": {"titulo": "PRÓ-OPOSIÇÃO", "itens": []},
            "popular": {"titulo": "CAMPO POPULAR / LÉO", "itens": []}
        }

    # 1. Agrupar comentários por publicação (post_url)
    posts_map = {}
    for c in comentarios_ig:
        url = c.get("post_url") or c.get("link_origem") or c.get("link_instagram")
        if not url:
            continue
        if url not in posts_map:
            posts_map[url] = {
                "id": str(c.get("id", "")),
                "url": url,
                "titulo": c.get("origem_titulo", "Publicação no Instagram"),
                "autor": c.get("autor", "@usuario"),
                "data": c.get("data", ""),
                "textos": [c.get("origem_titulo", "")]
            }
        posts_map[url]["textos"].append(c.get("texto", ""))

    posts_list = list(posts_map.values())
    total_posts = len(posts_list)

    def _rankear_por_temas(temas_alvo):
        ranking = []
        for t_nome, aliases in temas_alvo:
            posts_match = []
            for p in posts_list:
                texto_completo = normalizar_texto(" ".join(p["textos"]))
                if any(normalizar_texto(a) in texto_completo for a in aliases):
                    posts_match.append({
                        "id": p["id"],
                        "titulo": p["titulo"],
                        "autor": p["autor"],
                        "url": p["url"],
                        "qtd_comentarios": max(0, len(p["textos"]) - 1),
                        "data": p["data"]
                    })
            if posts_match:
                ranking.append((t_nome, len(posts_match), posts_match))

        ranking.sort(key=lambda x: (x[1], sum(pm["qtd_comentarios"] for pm in x[2])), reverse=True)
        tot = sum(r[1] for r in ranking) or 1
        out = []
        for t_nome, score, p_list in ranking[:10]:
            pct = round((score / tot) * 100, 1)
            out.append({
                "termo": t_nome,
                "pct": f"{pct}%".replace(".", ","),
                "valor": pct,
                "qtd_posts": len(p_list),
                "posts": p_list
            })
        return out

    itens_oposicao = _rankear_por_temas(TEMAS_OPOSICAO)
    itens_popular = _rankear_por_temas(TEMAS_CAMPO_POPULAR)

    hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")

    return {
        "hora": hora_ce,
        "total_posts": total_posts,
        "oposicao": {"titulo": "PRÓ-OPOSIÇÃO", "itens": itens_oposicao},
        "popular": {"titulo": "CAMPO POPULAR / LÉO", "itens": itens_popular}
    }

def construir_metricas_instagram_janelas(comentarios_ig):
    """
    Gera as nuvens de palavras e os rankings de posts fatiados pelas 5 janelas temporais:
    1h, 2h, 12h, 24h e 7d. Possui fallbacks progressivos para janelas ultracurtas.
    """
    if not comentarios_ig:
        comentarios_ig = []

    c_1h = [c for c in comentarios_ig if calcular_idade_horas(c.get("data")) <= 1] or comentarios_ig[:15]
    c_2h = [c for c in comentarios_ig if calcular_idade_horas(c.get("data")) <= 2] or comentarios_ig[:35]
    c_12h = [c for c in comentarios_ig if calcular_idade_horas(c.get("data")) <= 12] or comentarios_ig[:80]
    c_24h = [c for c in comentarios_ig if calcular_idade_horas(c.get("data")) <= 24] or comentarios_ig[:160]
    c_7d = comentarios_ig

    nuvem_1h = gerar_nuvem_instagram(c_1h)
    nuvem_2h = gerar_nuvem_instagram(c_2h)
    nuvem_12h = gerar_nuvem_instagram(c_12h)
    nuvem_24h = gerar_nuvem_instagram(c_24h)
    nuvem_7d = gerar_nuvem_instagram(c_7d)

    posts_1h = gerar_ranking_posts_instagram(c_1h)
    posts_2h = gerar_ranking_posts_instagram(c_2h)
    posts_12h = gerar_ranking_posts_instagram(c_12h)
    posts_24h = gerar_ranking_posts_instagram(c_24h)
    posts_7d = gerar_ranking_posts_instagram(c_7d)

    return {
        "nuvem": nuvem_24h or nuvem_7d,
        "nuvens_por_janela": {
            "1h": nuvem_1h,
            "2h": nuvem_2h,
            "12h": nuvem_12h,
            "24h": nuvem_24h,
            "7d": nuvem_7d
        },
        "posts_mais_falados": posts_24h or posts_7d,
        "posts_por_janela": {
            "1h": posts_1h,
            "2h": posts_2h,
            "12h": posts_12h,
            "24h": posts_24h,
            "7d": posts_7d
        }
    }

