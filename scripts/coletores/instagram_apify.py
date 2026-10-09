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
    carregar_chaves_api
)

def carregar_perfis_instagram(limite_perfis=4):
    """
    Lê 'dados/perfis_instagram.txt' e seleciona os perfis prioritários (@).
    Prioriza sempre o perfil oficial do Léo Suricate e veículos da imprensa cearense.
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

    # Garante perfil do Léo Suricate em primeiro lugar
    leo_url = "https://www.instagram.com/leosuricate/"
    alvos_selecionados = [leo_url] if leo_url in perfis else []

    for p in perfis:
        if p not in alvos_selecionados and len(alvos_selecionados) < limite_perfis:
            alvos_selecionados.append(p)

    return alvos_selecionados or [leo_url]

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

def coletar_comentarios_perfis_apify(apify_token, limite_perfis=3, max_posts_por_perfil=3):
    """
    Coleta comentários dos perfis monitorados via 'apify/instagram-scraper'.
    """
    alvos = carregar_perfis_instagram(limite_perfis=limite_perfis)
    payload = {
        "directUrls": alvos,
        "resultsType": "posts",
        "resultsLimit": max_posts_por_perfil
    }

    posts = _disparar_e_aguardar_ator("apify/instagram-scraper", payload, apify_token, max_espera=45)
    comentarios = []

    for p in posts:
        post_url = p.get("url", "")
        post_caption = p.get("caption", "").strip()
        post_titulo = (post_caption.split("\n")[0][:90] + "...") if len(post_caption) > 90 else (post_caption or "Post no Instagram")

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

    return comentarios

def coletar_comentarios_hashtag_apify(apify_token, tag="fimda6x1", max_posts=2):
    """
    Coleta posts e comentários da hashtag via 'apify/instagram-hashtag-scraper'
    e complementa com 'apify/instagram-scraper' (comments) caso necessário.
    """
    payload_tag = {
        "hashtags": [tag.lstrip("#").strip()],
        "resultsType": "posts",
        "resultsLimit": max_posts
    }

    posts_tag = _disparar_e_aguardar_ator("apify/instagram-hashtag-scraper", payload_tag, apify_token, max_espera=35)
    comentarios = []
    posts_com_comentarios = []

    for p in posts_tag:
        p_url = p.get("url") or p.get("postUrl") or ""
        p_caption = (p.get("caption") or "").strip()
        p_comments_count = p.get("commentsCount", 0)

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
                    "hashtag": f"#{tag}",
                    "autor": autor_formatado,
                    "texto": txt,
                    "likes": comm.get("likesCount", 0),
                    "data": comm.get("timestamp", ""),
                    "origem_titulo": f"#{tag} · {p_caption[:80]}..." if len(p_caption) > 80 else f"#{tag}",
                    "post_url": p_url,
                    "link_origem": p_url,
                    "link_instagram": p_url
                })
        elif p_url and p_comments_count > 0:
            posts_com_comentarios.append(p_url)

    # 2. Se houver posts da hashtag com comentários que não vieram no grid, busca direto os comentários
    if posts_com_comentarios:
        payload_comm = {
            "directUrls": posts_com_comentarios[:2],
            "resultsType": "comments",
            "resultsLimit": 5
        }
        comms_extraidos = _disparar_e_aguardar_ator("apify/instagram-scraper", payload_comm, apify_token, max_espera=30)
        for comm in comms_extraidos:
            c_id = comm.get("id")
            txt = (comm.get("text") or "").strip()
            if not c_id or len(txt) < 3:
                continue

            autor = comm.get("ownerUsername") or "usuário"
            autor_formatado = f"@{autor}" if not autor.startswith("@") else autor
            p_url = comm.get("postUrl") or comm.get("commentUrl") or ""

            comentarios.append({
                "id": str(c_id),
                "rede": "instagram",
                "origem_tipo": "hashtag",
                "hashtag": f"#{tag}",
                "autor": autor_formatado,
                "texto": txt,
                "likes": comm.get("likesCount", 0),
                "data": comm.get("timestamp", ""),
                "origem_titulo": f"#{tag} · Debate Popular",
                "post_url": p_url,
                "link_origem": p_url,
                "link_instagram": p_url
            })

    return comentarios

def coletar_comentarios_instagram_apify(apify_token=None, max_posts_por_perfil=3, max_espera_segundos=45):
    """
    Orquestra a coleta de comentários no Instagram:
    - Perfis oficiais e locais (apify/instagram-scraper)
    - Hashtags prioritárias como #fimda6x1 (apify/instagram-hashtag-scraper)
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

    # 1. Coleta dos Perfis
    try:
        novos_perfis = coletar_comentarios_perfis_apify(apify_token, limite_perfis=3, max_posts_por_perfil=max_posts_por_perfil)
        for c in novos_perfis:
            comentarios_existentes[c["id"]] = c
    except Exception as e:
        print(f"Aviso na coleta de perfis do Instagram: {e}")

    # 2. Coleta das Hashtags (ex: #fimda6x1)
    tags = carregar_hashtags_instagram()
    for tag in tags[:1]:  # Focado inicialmente na hashtag prioritária
        try:
            novos_tag = coletar_comentarios_hashtag_apify(apify_token, tag=tag, max_posts=2)
            for c in novos_tag:
                comentarios_existentes[c["id"]] = c
        except Exception as e:
            print(f"Aviso na coleta da hashtag #{tag}: {e}")

    lista_final = list(comentarios_existentes.values())
    if lista_final:
        try:
            with open(CACHE_INSTAGRAM, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return lista_final

def carregar_cache_instagram():
    """
    Carrega os comentários do cache local 'dados/cache_instagram.json'.
    """
    if os.path.exists(CACHE_INSTAGRAM):
        try:
            with open(CACHE_INSTAGRAM, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []
