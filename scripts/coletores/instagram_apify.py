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

def carregar_perfis_instagram(tamanho_lote=8, limite_perfis=None):
    if limite_perfis is not None:
        tamanho_lote = limite_perfis
    """
    =============================================================================
    RODÍZIO CIRCULAR DE PERFIS DO INSTAGRAM (CUSTO ZERO & COBERTURA HOMOGÊNEA)
    =============================================================================
    COMO FUNCIONA O RODÍZIO:
        1. FILA CIRCULAR COMPLETA (SEM PERFIL FIXO):
           Todos os perfis cadastrados em 'dados/perfis_instagram.txt' (incluindo
           @leosuricate, lideranças e imprensa) participam igualmente da rotação circular.
        
        2. LOTE ROTATIVO POR RODADA:
           A cada execução, o sistema carrega uma fatia de 'tamanho_lote' (padrão: 8 perfis)
           a partir do ponteiro salvo em 'dados/estado_rodizio_ig.json'.
        
        3. AVANÇO AUTOMÁTICO DO PONTEIRO:
           A cada rodada, o ponteiro avança, salvando o estado para a próxima execução.
        
        4. COBERTURA COMPLETA AO LONGO DO DIA:
           Na grade de 4 rodadas diárias em Fortaleza/CE (07:30, 12:30, 17:30 e 21:30):
           4 rodadas x 8 perfis = 32 consultas de perfis por dia.
           Como temos 21 perfis ativos, cada perfil é visitado ~1,5 a 2 vezes ao dia.
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
                        url = f"https://www.instagram.com/{user}/"
                        if url not in perfis:
                            perfis.append(url)
        except Exception:
            pass

    total_perfis = len(perfis)
    if total_perfis == 0:
        return ["https://www.instagram.com/leosuricate/"]

    # 1. Recupera o ponteiro da última execução
    caminho_estado = ESTADO_RODIZIO_IG if os.path.exists(os.path.dirname(ESTADO_RODIZIO_IG)) else os.path.join("dados", "estado_rodizio_ig.json")
    indice_atual = 0

    if os.path.exists(caminho_estado):
        try:
            with open(caminho_estado, "r", encoding="utf-8") as f:
                dados_estado = json.load(f)
                indice_atual = dados_estado.get("proximo_indice", 0)
        except Exception:
            indice_atual = 0

    indice_atual = indice_atual % total_perfis

    # 2. Seleciona o lote rotativo circular desta rodada
    lote_rotativo = []
    for i in range(min(tamanho_lote, total_perfis)):
        idx = (indice_atual + i) % total_perfis
        perfil_escolhido = perfis[idx]
        if perfil_escolhido not in lote_rotativo:
            lote_rotativo.append(perfil_escolhido)

    # 3. Atualiza e persiste o novo ponteiro para a próxima execução
    proximo_indice = (indice_atual + len(lote_rotativo)) % total_perfis
    try:
        with open(caminho_estado, "w", encoding="utf-8") as f:
            json.dump({
                "proximo_indice": proximo_indice,
                "indice_rodada_anterior": indice_atual,
                "total_perfis_cadastrados": total_perfis,
                "lote_selecionado": [p.split("/")[-2] for p in lote_rotativo],
                "atualizado_em": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return lote_rotativo

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

    return tags

def _disparar_e_aguardar_ator(actor_id, payload, apify_token, max_espera=45):
    """
    Função auxiliar genérica para disparar e aguardar a execução de um ator no Apify.
    Retorna a lista de itens do dataset resultante.
    """
    actor_endpoint = actor_id.replace("/", "~")
    # Força alocação leve de memória (1024 MB) e timeout estrito (45s) para blindar a cota gratuita contra consumo de 4GB
    url_run = f"https://api.apify.com/v2/acts/{actor_endpoint}/runs?token={apify_token}&memory=1024&timeout=45"

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

def coletar_comentarios_perfis_apify(apify_token, limite_perfis=8, max_posts_por_perfil=5):
    """
    Coleta comentários dos perfis monitorados via 'apify/instagram-scraper' de forma ultraenxuta:
    1. Varre os alvos em rodízio circular homogêneo (lote de 8 perfis por rodada);
    2. Coleta os últimos posts de cada um (padrão: até 5 posts);
    3. Extrai estritamente os comentários retornados nativamente no nó 'latestComments' (1 única chamada ao ator).
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

        # Comentários rápidos retornados diretamente no grid de posts (sem Deep Scan)
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

def coletar_comentarios_hashtag_apify(apify_token, tags=None, max_posts=2):
    """
    Coleta posts e comentários das hashtags via 'apify/instagram-hashtag-scraper'.
    Aproveita exclusivamente os comentários retornados nativamente no nó 'latestComments' (1 única chamada ao ator).
    """
    if tags is None:
        tags = ["fimda6x1"]
    elif isinstance(tags, str):
        tags = [tags]

    tags_limpas = [t.lstrip("#").strip() for t in tags if t.strip()]
    if not tags_limpas:
        return []

    # O ator apify/instagram-hashtag-scraper aceita múltiplas hashtags numa só execução
    limite_total_posts = max(10, max_posts * len(tags_limpas))
    payload_tag = {
        "hashtags": tags_limpas,
        "resultsType": "posts",
        "resultsLimit": limite_total_posts
    }

    posts_tag = _disparar_e_aguardar_ator("apify/instagram-hashtag-scraper", payload_tag, apify_token, max_espera=35)
    comentarios = []

    for p in posts_tag:
        p_url = p.get("url") or p.get("postUrl") or ""
        p_caption = (p.get("caption") or "").strip()
        p_hashtag = p.get("inputHashtag") or p.get("hashtag") or tags_limpas[0]
        tag_formatada = f"#{p_hashtag.lstrip('#')}"

        # Extrai exclusivamente os comentários que já vierem no retorno da hashtag
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

    return comentarios

def coletar_comentarios_instagram_apify(apify_token=None, limite_perfis=8, max_posts_por_perfil=5, max_espera_segundos=45):
    """
    Orquestra a coleta de comentários no Instagram de forma ultraenxuta:
    - Perfis oficiais e locais (apify/instagram-scraper): rotação circular homogênea de 8 alvos por rodada
    - Coleta de até 5 posts por perfil
    - Hashtags prioritárias e de mobilização (apify/instagram-hashtag-scraper): 1 chamada direta
    - Extração estritamente via 'latestComments' nativo (zero Deep Scan)
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

    # 1. Coleta dos Perfis (1 fixo + 8 rotativos = 9 perfis)
    try:
        novos_perfis = coletar_comentarios_perfis_apify(apify_token, limite_perfis=limite_perfis, max_posts_por_perfil=max_posts_por_perfil)
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
