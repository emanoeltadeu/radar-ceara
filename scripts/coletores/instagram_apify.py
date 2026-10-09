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
        novos_perfis = coletar_comentarios_perfis_apify(apify_token, limite_perfis=5, max_posts_por_perfil=max_posts_por_perfil)
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
