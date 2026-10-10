"""
Módulo Coletor do Instagram (Apify / Instagram Scraper & Hashtag Scraper).

O que faz:
    1. Lê a lista de perfis de 'dados/perfis_instagram.txt' (@leosuricate, imprensa, etc.);
    2. Lê a lista de hashtags de 'dados/hashtags_instagram.txt' (#fimda6x1);
    3. Coleta posts e comentários dos perfis via 'apify/instagram-scraper';
    4. Coleta posts e comentários da hashtag via 'apify/instagram-hashtag-scraper';
    5. Converte todos os comentários para o Contrato de Comentário Unificado;
    6. Mantém cache persistente e incremental em 'dados/cache_instagram.json'.
"""

import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

from config import (
    CACHE_INSTAGRAM,
    PERFIS_INSTAGRAM,
    HASHTAGS_INSTAGRAM,
    ESTADO_RODIZIO_IG,
    JANELA_MAXIMA_HORAS,
    calcular_idade_horas,
    carregar_chaves_api
)

def carregar_perfis_instagram(tamanho_lote=5, limite_perfis=None):
    if limite_perfis is not None:
        tamanho_lote = limite_perfis
    """
    =============================================================================
    RODÍZIO INTELIGENTE DE PERFIS DO INSTAGRAM (CUSTO ZERO & COBERTURA TOTAL)
    =============================================================================
    POR QUE FOI IMPLEMENTADO ASSIM?
        O arquivo 'dados/perfis_instagram.txt' contém 24 perfis estratégicos no Ceará
        (mandato popular, imprensa, oposição e transporte público).
        Se enviássemos os 24 perfis de uma só vez a cada hora para a nuvem da Apify:
        1. O tempo de execução por rodada aumentaria para ~2 minutos;
        2. O consumo mensal de computação ultrapassaria a cota gratuita de US$ 5.00/mês da Apify.

    COMO FUNCIONA O RODÍZIO INTELIGENTE:
        1. PERFIL DO MANDATO É FIXO (@leosuricate):
           O perfil oficial de Léo Suricate é SEMPRE incluído em 100% das rodadas,
           garantindo que nenhuma postagem ou debate do mandato seja perdido.
        
        2. FILA CIRCULAR DOS DEMAIS 23 PERFIS:
           Os demais 23 perfis são organizados em uma fila circular rotativa.
           A cada execução, o sistema carrega uma fatia de 'tamanho_lote' (padrão: 5 perfis)
           a partir do ponteiro salvo em 'dados/estado_rodizio_ig.json'.
        
        3. AVANÇO AUTOMÁTICO DO PONTEIRO:
           A cada rodada, o ponteiro avança (0 -> 5 -> 10 -> 15 -> 20 -> 0...),
           salvando o estado para a próxima execução.
        
        4. COBERTURA COMPLETA AO LONGO DO DIA:
           Como o GitHub Actions roda 8 vezes por dia (08h, 11h, 13h, 15h, 17h, 20h, 22h, 23h):
           - 8 execuções x 5 perfis rotativos = 40 consultas de perfis por dia.
           - Como temos 23 perfis rotativos, CADA PERFIL É VISITADO CERCA DE 2 VEZES POR DIA.
        
        5. CUSTO ZERO GARANTIDO:
           Com 6 perfis por rodada (1 fixo + 5 rotativos), o consumo mensal da Apify
           fica em aproximadamente US$ 2.40/mês, 100% DENTRO da cota gratuita de US$ 5.00/mês.
    =============================================================================
    """
    perfis = []
    caminho = PERFIS_INSTAGRAM if os.path.exists(PERFIS_INSTAGRAM) else os.path.join("dados", "perfis_instagram.txt")

    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                for line in f:
                    linha = line.strip()
                    if not linha or linha.startswith("#"):
                        continue
                    if linha.startswith("@"):
                        user = linha.lstrip("@").strip()
                        perfis.append(f"https://www.instagram.com/{user}/")
        except Exception:
            pass

    # 1. Garante perfil do Léo Suricate como fixo e prioritário
    leo_url = "https://www.instagram.com/leosuricate/"
    if leo_url not in perfis:
        perfis.insert(0, leo_url)

    outros_perfis = [p for p in perfis if p != leo_url]
    total_outros = len(outros_perfis)

    if total_outros == 0:
        return [leo_url]

    # 2. Recupera o ponteiro da última execução
    caminho_estado = ESTADO_RODIZIO_IG if os.path.exists(os.path.dirname(ESTADO_RODIZIO_IG)) else os.path.join("dados", "estado_rodizio_ig.json")
    indice_atual = 0

    if os.path.exists(caminho_estado):
        try:
            with open(caminho_estado, "r", encoding="utf-8") as f:
                dados_estado = json.load(f)
                indice_atual = dados_estado.get("proximo_indice", 0)
        except Exception:
            indice_atual = 0

    indice_atual = indice_atual % total_outros

    # 3. Seleciona o lote rotativo circular desta rodada
    lote_rotativo = []
    for i in range(tamanho_lote):
        idx = (indice_atual + i) % total_outros
        perfil_escolhido = outros_perfis[idx]
        if perfil_escolhido not in lote_rotativo:
            lote_rotativo.append(perfil_escolhido)

    # 4. Atualiza e persiste o novo ponteiro para a próxima execução
    proximo_indice = (indice_atual + tamanho_lote) % total_outros
    try:
        with open(caminho_estado, "w", encoding="utf-8") as f:
            json.dump({
                "proximo_indice": proximo_indice,
                "indice_rodada_anterior": indice_atual,
                "total_perfis_cadastrados": len(perfis),
                "lote_selecionado": [p.split("/")[-2] for p in lote_rotativo],
                "atualizado_em": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Retorna o perfil de Léo Suricate + o lote rotativo (ex: 1 fixo + 5 rotativos = 6 alvos)
    alvos_finais = [leo_url] + lote_rotativo
    return alvos_finais

def carregar_hashtags_instagram():
    """
    Lê 'dados/hashtags_instagram.txt' e retorna a lista de hashtags válidas (sem espaços).
    """
    tags = []
    caminho = HASHTAGS_INSTAGRAM if os.path.exists(HASHTAGS_INSTAGRAM) else os.path.join("dados", "hashtags_instagram.txt")

    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                for line in f:
                    linha = line.strip()
                    # Ignora comentários explicativos com espaços ou divisores
                    if not linha or linha.startswith("# ") or linha.startswith("##") or linha.startswith("# =") or linha.startswith("# -"):
                        continue
                    if linha.startswith("#"):
                        tag = linha.lstrip("#").strip()
                        # Hashtags válidas não têm espaços
                        if tag and " " not in tag and len(tag) > 1:
                            if tag not in tags:
                                tags.append(tag)
        except Exception:
            pass

    return tags or ["fimda6x1"]

def _disparar_e_aguardar_ator(actor_id, payload, apify_token, max_espera=45):
    """
    Função auxiliar genérica para disparar e aguardar a execução de um ator no Apify.
    Retorna a lista de itens do dataset resultante.
    """
    actor_endpoint = actor_id.replace("/", "~")
    url_run = f"https://api.apify.com/v2/acts/{actor_endpoint}/runs?token={apify_token}"

    req = urllib.request.Request(
        url_run,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            run_id = data.get("data", {}).get("id")
            dataset_id = data.get("data", {}).get("defaultDatasetId")
    except Exception as e:
        print(f"Aviso Apify ao iniciar {actor_id}: {e}")
        return []

    if not run_id:
        return []

    inicio = time.time()
    url_poll = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"

    while time.time() - inicio < max_espera:
        try:
            req_poll = urllib.request.Request(url_poll)
            with urllib.request.urlopen(req_poll, timeout=10) as resp_poll:
                data_poll = json.loads(resp_poll.read().decode("utf-8"))
                status = data_poll.get("data", {}).get("status")
                if status == "SUCCEEDED":
                    dataset_id = data_poll.get("data", {}).get("defaultDatasetId", dataset_id)
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    print(f"Apify {actor_id} terminou com status: {status}")
                    return []
        except Exception:
            pass
        time.sleep(3)

    if not dataset_id:
        return []

    url_items = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}"
    try:
        req_items = urllib.request.Request(url_items)
        with urllib.request.urlopen(req_items, timeout=15) as resp_items:
            return json.loads(resp_items.read().decode("utf-8"))
    except Exception as e:
        print(f"Aviso ao buscar dataset de {actor_id}: {e}")
        return []

def coletar_comentarios_perfis_apify(apify_token, limite_perfis=11, max_posts_por_perfil=5):
    """
    Coleta comentários dos perfis monitorados via 'apify/instagram-scraper'.
    1. Varre os alvos (Léo Suricate fixo + 11 rotativos = 12 perfis no total);
    2. Coleta os últimos posts de cada um (padrão: 5 posts);
    3. Para os posts com debate ativo (especialmente perfil de mandato e posts com alto volume de comentários),
       extrai até 100 comentários em lote focado.
    """
    alvos = carregar_perfis_instagram(limite_perfis=limite_perfis)
    payload = {
        "directUrls": alvos,
        "resultsType": "posts",
        "resultsLimit": max_posts_por_perfil
    }

    posts = _disparar_e_aguardar_ator("apify/instagram-scraper", payload, apify_token, max_espera=60)
    comentarios = []
    posts_para_comentarios_profundos = []

    # 0. Mapeia contagem de comentários e data mais recente já existente por post no cache
    cache_post_stats = {}
    for c in carregar_cache_instagram():
        url = c.get("post_url") or c.get("link_origem")
        if url:
            if url not in cache_post_stats:
                cache_post_stats[url] = {"total_comentarios": 0, "ultima_data": ""}
            cache_post_stats[url]["total_comentarios"] += 1
            dt = c.get("data", "")
            if dt > cache_post_stats[url]["ultima_data"]:
                cache_post_stats[url]["ultima_data"] = dt

    for p in posts:
        post_url = p.get("url", "")
        post_caption = p.get("caption", "").strip()
        post_titulo = (post_caption.split("\n")[0][:90] + "...") if len(post_caption) > 90 else (post_caption or "Post no Instagram")
        comments_count = p.get("commentsCount", 0)

        # Comentários rápidos retornados diretamente no grid de posts
        for comm in p.get("latestComments", []):
            c_id = comm.get("id")
            txt = (comm.get("text") or "").strip()
            if not c_id or len(txt) < 3:
                continue

            autor = comm.get("ownerUsername") or comm.get("owner", {}).get("username") or "usuário"
            autor_formatado = f"@{autor}" if not autor.startswith("@") else autor

            comentarios.append({
                "id": str(c_id),
                "rede": "instagram",
                "origem_tipo": "perfil",
                "autor": autor_formatado,
                "texto": txt,
                "likes": comm.get("likesCount", 0),
                "data": comm.get("timestamp", ""),
                "origem_titulo": post_titulo,
                "post_url": post_url,
                "link_origem": post_url,
                "link_instagram": post_url
            })

        # OTIMIZAÇÃO INCREMENTAL:
        # Só aprofunda se:
        # 1. Post é do mandato @leosuricate OU tem debate ativo (>= 8 comentários);
        # 2. E o post ainda NÃO está no cache OU o número de comentários no Instagram aumentou em relação ao cache.
        eh_leo = "leosuricate" in post_url.lower() or "leosuricate" in (p.get("ownerUsername") or "").lower()
        comentarios_ja_salvos = cache_post_stats.get(post_url, {}).get("total_comentarios", 0)

        # Se já coletamos todos ou quase todos os comentários deste post, não gasta requisição repetida
        tem_novidades = comments_count > (comentarios_ja_salvos + 2) or (comentarios_ja_salvos == 0 and comments_count > 0)

        if post_url and (eh_leo or comments_count >= 8) and tem_novidades:
            posts_para_comentarios_profundos.append((post_url, post_titulo, comments_count))

    # Se identificamos posts de debate ativo, extrai até 100 comentários nos top 3 posts de maior engajamento
    if posts_para_comentarios_profundos:
        # Ordena dando prioridade aos com mais comentários ou Léo Suricate
        posts_ordenados = sorted(
            posts_para_comentarios_profundos,
            key=lambda x: (1 if "leosuricate" in x[0].lower() else 0, x[2]),
            reverse=True
        )[:3]

        urls_debate = [p[0] for p in posts_ordenados]
        mapa_titulos = {p[0]: p[1] for p in posts_ordenados}

        payload_deep_comments = {
            "directUrls": urls_debate,
            "resultsType": "comments",
            "resultsLimit": 100
        }
        comms_deep = _disparar_e_aguardar_ator("apify/instagram-scraper", payload_deep_comments, apify_token, max_espera=45)
        for comm in comms_deep:
            c_id = comm.get("id")
            txt = (comm.get("text") or "").strip()
            if not c_id or len(txt) < 3:
                continue

            autor = comm.get("ownerUsername") or "usuário"
            autor_formatado = f"@{autor}" if not autor.startswith("@") else autor
            p_url = comm.get("postUrl") or comm.get("commentUrl") or urls_debate[0]
            p_titulo = mapa_titulos.get(p_url, "Debate no Instagram")

            comentarios.append({
                "id": str(c_id),
                "rede": "instagram",
                "origem_tipo": "perfil",
                "autor": autor_formatado,
                "texto": txt,
                "likes": comm.get("likesCount", 0),
                "data": comm.get("timestamp", ""),
                "origem_titulo": p_titulo,
                "post_url": p_url,
                "link_origem": p_url,
                "link_instagram": p_url
            })

    return comentarios

def coletar_comentarios_hashtag_apify(apify_token, tags=None, max_posts=2):
    """
    Coleta posts e comentários das hashtags via 'apify/instagram-hashtag-scraper'
    e complementa com 'apify/instagram-scraper' (comments) caso necessário.
    Suporta receber uma tag única (str) ou lista de tags (list).
    """
    if tags is None:
        tags = ["fimda6x1"]
    elif isinstance(tags, str):
        tags = [tags]

    tags_limpas = [t.lstrip("#").strip() for t in tags if t.strip()]
    if not tags_limpas:
        return []

    # O ator apify/instagram-hashtag-scraper aceita múltiplas hashtags numa só execução
    payload_tag = {
        "hashtags": tags_limpas,
        "resultsType": "posts",
        "resultsLimit": max_posts
    }

    posts_tag = _disparar_e_aguardar_ator("apify/instagram-hashtag-scraper", payload_tag, apify_token, max_espera=45)
    comentarios = []
    posts_com_comentarios = []

    # Mapeamento de URLs já vistas no cache para evitar buscar comentários de posts antigos
    cache_post_urls = set()
    for c in carregar_cache_instagram():
        u = c.get("post_url") or c.get("link_origem")
        if u:
            cache_post_urls.add(u)

    for p in posts_tag:
        p_url = p.get("url") or p.get("postUrl") or ""
        p_caption = (p.get("caption") or "").strip()
        p_comments_count = p.get("commentsCount", 0)
        p_hashtag = p.get("inputHashtag") or p.get("hashtag") or tags_limpas[0]
        tag_formatada = f"#{p_hashtag.lstrip('#')}"

        # 1. Verifica se já vieram latestComments
        latest = p.get("latestComments", [])
        if latest:
            for comm in latest:
                c_id = comm.get("id")
                txt = (comm.get("text") or "").strip()
                if not c_id or len(txt) < 3:
                    continue
                autor = comm.get("ownerUsername") or comm.get("owner", {}).get("username") or "usuário"
                autor_formatado = f"@{autor}" if not autor.startswith("@") else autor

                comentarios.append({
                    "id": str(c_id),
                    "rede": "instagram",
                    "origem_tipo": "hashtag",
                    "hashtag": tag_formatada,
                    "autor": autor_formatado,
                    "texto": txt,
                    "likes": comm.get("likesCount", 0),
                    "data": comm.get("timestamp", ""),
                    "origem_titulo": f"{tag_formatada} · {p_caption[:80]}..." if len(p_caption) > 80 else tag_formatada,
                    "post_url": p_url,
                    "link_origem": p_url,
                    "link_instagram": p_url
                })
        elif p_url and p_comments_count > 0 and p_url not in cache_post_urls:
            posts_com_comentarios.append((p_url, tag_formatada))

    # 2. Se houver posts da hashtag com comentários que não vieram no grid, busca direto os comentários
    if posts_com_comentarios:
        urls_para_buscar = [item[0] for item in posts_com_comentarios[:3]]
        mapa_tag_url = {item[0]: item[1] for item in posts_com_comentarios[:3]}
        payload_comm = {
            "directUrls": urls_para_buscar,
            "resultsType": "comments",
            "resultsLimit": 10
        }
        comms_extraidos = _disparar_e_aguardar_ator("apify/instagram-scraper", payload_comm, apify_token, max_espera=35)
        for comm in comms_extraidos:
            c_id = comm.get("id")
            txt = (comm.get("text") or "").strip()
            if not c_id or len(txt) < 3:
                continue

            autor = comm.get("ownerUsername") or "usuário"
            autor_formatado = f"@{autor}" if not autor.startswith("@") else autor
            p_url = comm.get("postUrl") or comm.get("commentUrl") or ""
            tag_fmt = mapa_tag_url.get(p_url, tag_formatada)

            comentarios.append({
                "id": str(c_id),
                "rede": "instagram",
                "origem_tipo": "hashtag",
                "hashtag": tag_fmt,
                "autor": autor_formatado,
                "texto": txt,
                "likes": comm.get("likesCount", 0),
                "data": comm.get("timestamp", ""),
                "origem_titulo": f"{tag_fmt} · Debate Popular",
                "post_url": p_url,
                "link_origem": p_url,
                "link_instagram": p_url
            })

    return comentarios

def coletar_comentarios_instagram_apify(apify_token=None, max_posts_por_perfil=5, max_espera_segundos=60):
    """
    Orquestra a coleta de comentários no Instagram:
    - Perfis oficiais e locais (apify/instagram-scraper) com 12 perfis e 5 posts por perfil
    - Hashtags prioritárias e de mobilização (apify/instagram-hashtag-scraper)
    - Mesclagem com o cache existente sem duplicação
    """
    if apify_token is None:
        apify_token = carregar_chaves_api()["apify"]

    # Se não houver token configurado, retorna os dados em cache
    if not apify_token:
        return carregar_cache_instagram()

    comentarios_existentes = {}
    for c in carregar_cache_instagram():
        if c.get("id"):
            comentarios_existentes[c["id"]] = c

    # 1. Coleta dos Perfis (1 fixo + 11 rotativos = 12 perfis)
    try:
        novos_perfis = coletar_comentarios_perfis_apify(apify_token, limite_perfis=11, max_posts_por_perfil=max_posts_por_perfil)
        for c in novos_perfis:
            comentarios_existentes[c["id"]] = c
    except Exception as e:
        print(f"Aviso na coleta de perfis do Instagram: {e}")

    # 2. Coleta das Hashtags (ex: #fimda6x1, #boralula, #lula13, etc.)
    tags = carregar_hashtags_instagram()
    if tags:
        try:
            # Envia as hashtags cadastradas em uma única chamada agregada ao ator
            novos_tag = coletar_comentarios_hashtag_apify(apify_token, tags=tags, max_posts=2)
            for c in novos_tag:
                comentarios_existentes[c["id"]] = c
        except Exception as e:
            print(f"Aviso na coleta de hashtags do Instagram: {e}")

    # Política de retenção de 7 dias: descarta comentários mais antigos
    lista_final = [
        c for c in comentarios_existentes.values()
        if calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS
    ]
    if lista_final:
        try:
            with open(CACHE_INSTAGRAM, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return lista_final

def carregar_cache_instagram():
    """
    Carrega os comentários do cache local 'dados/cache_instagram.json'
    filtrados pela janela máxima de 7 dias.
    """
    if os.path.exists(CACHE_INSTAGRAM):
        try:
            with open(CACHE_INSTAGRAM, "r", encoding="utf-8") as f:
                dados = json.load(f)
                return [c for c in dados if calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS]
        except Exception:
            pass
    return []
