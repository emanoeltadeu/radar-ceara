"""
Módulo Coletor do YouTube (YouTube Data API v3).

O que faz:
    1. Pesquisa e mantém atualizado o acervo de vídeos cearenses relevantes (search.list);
    2. Coleta comentários reais mais curtidos/relevantes nos vídeos (commentThreads.list);
    3. Padroniza os comentários no Contrato de Dados Unificado de Redes Sociais.
"""

import json
import os
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone

from config import (
    CACHE_YOUTUBE,
    CACHE_COMENTARIOS,
    JANELA_MAXIMA_HORAS,
    calcular_idade_horas,
    carregar_chaves_api
)

# Termos para ignorar preventivamente na coleta de vídeos (evita gastar cota com fofoca/humor/futebol)
TERMOS_IGNORAR_TITULO = [
    "tiririca", "saf", "futebol", "campeonato", "cearense sub", "clássico-rei",
    "fortaleza ec", "ceará sc", "brasileirão", "gol de", "humor"
]

CONSULTAS_PADRAO_CEARA = [
    "Ceará política",
    "Fortaleza política",
    "Léo Suricate",
    "Assembleia Legislativa Ceará",
    "Elmano de Freitas Ceará",
    "ônibus Fortaleza",
    "escala 6x1 Fortaleza"
]

def atualizar_videos_youtube(yt_key=None, cache_path=CACHE_YOUTUBE, queries=None):
    """
    O que faz:
        Executa buscas temáticas na YouTube Data API v3 (search.list) e mescla
        com os vídeos já existentes no cache local, deduplicando por videoId.

    Retorno:
        list: Lista atualizada de dicionários contendo metadados dos vídeos.
    """
    if yt_key is None:
        yt_key = carregar_chaves_api()["youtube"]

    if queries is None:
        queries = CONSULTAS_PADRAO_CEARA

    vids_map = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                for v in json.load(f):
                    if v.get("id"):
                        vids_map[v["id"]] = v
        except Exception:
            pass

    if yt_key:
        for q in queries:
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(q)}&type=video&order=date&maxResults=8&key={yt_key}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "RadarCeara/2.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for item in data.get("items", []):
                        vid_id = item.get("id", {}).get("videoId")
                        if not vid_id:
                            continue
                        snip = item.get("snippet", {})
                        vids_map[vid_id] = {
                            "id": vid_id,
                            "titulo": html.unescape(snip.get("title", "")),
                            "canal": snip.get("channelTitle", ""),
                            "desc": html.unescape(snip.get("description", "")),
                            "publishedAt": snip.get("publishedAt", "")
                        }
            except Exception:
                continue

    # Política de retenção de 7 dias: descarta vídeos fora da janela máxima
    lista_ordenada = [
        v for v in vids_map.values()
        if calcular_idade_horas(v.get("publishedAt")) <= JANELA_MAXIMA_HORAS
    ]
    lista_ordenada.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)

    if lista_ordenada:
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(lista_ordenada, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return lista_ordenada

def carregar_corpus_videos(cache_path=CACHE_YOUTUBE):
    """
    O que faz:
        Carrega os vídeos do cache, calcula a idade em horas de cada publicação
        e filtra estritamente pela janela máxima de 7 dias.
    """
    if not os.path.exists(cache_path):
        return []

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            vids = json.load(f)
    except Exception:
        return []

    vids_validos = []
    for v in vids:
        idade = calcular_idade_horas(v.get("publishedAt"))
        v["idade_horas"] = idade
        if idade <= JANELA_MAXIMA_HORAS:
            vids_validos.append(v)

    return vids_validos or vids[:30]

def coletar_comentarios_youtube(yt_key=None, max_vids=35, max_comentarios_por_vid=10):
    """
    O que faz:
        Consulta commentThreads.list para os vídeos prioritários e extrai os comentários,
        formatando-os no Contrato Unificado de Comentários de Redes Sociais.

    Retorno:
        list: Lista de comentários unificados.
    """
    if yt_key is None:
        yt_key = carregar_chaves_api()["youtube"]

    if not yt_key:
        return []

    vids = carregar_corpus_videos()
    if not vids:
        vids = atualizar_videos_youtube(yt_key)

    # Filtrar títulos de futebol/ruído
    vids_filtrados = [
        v for v in vids
        if v.get("id") and not any(ign in v.get("titulo", "").lower() for ign in TERMOS_IGNORAR_TITULO)
    ]

    # Prioriza vídeos que citam o mandato ou temas centrais
    def prioridade_video(v):
        t = v.get("titulo", "").lower()
        if any(k in t for k in ["leo suricate", "suricate", "lula", "6x1", "onibus", "tarifa"]):
            return 0
        if any(k in t for k in ["elmano", "governo", "ciro", "wagner", "eleições"]):
            return 1
        return 2

    vids_filtrados.sort(key=prioridade_video)
    alvos = vids_filtrados[:max_vids]

    comentarios_existentes = {}
    if os.path.exists(CACHE_COMENTARIOS):
        try:
            with open(CACHE_COMENTARIOS, "r", encoding="utf-8") as f:
                for c in json.load(f):
                    if c.get("id"):
                        comentarios_existentes[c["id"]] = c
        except Exception:
            pass

    novos_adicionados = 0
    for v in alvos:
        vid_id = v["id"]
        v_tit = v.get("titulo", "")
        v_canal = v.get("canal", "")

        url = (
            f"https://www.googleapis.com/youtube/v3/commentThreads"
            f"?part=snippet&videoId={vid_id}&maxResults={max_comentarios_por_vid}"
            f"&order=relevance&key={yt_key}"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RadarCeara/2.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for it in data.get("items", []):
                    top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    c_id = it.get("id", "")
                    texto = html.unescape(top.get("textDisplay", "")).strip()

                    # Sanitização de quebras de linha e HTML
                    texto_limpo = html.unescape(texto.replace("<br>", " ").replace("<br/>", " "))
                    texto_limpo = " ".join(texto_limpo.split())

                    # Ignora comentários curtos demais ou sem conteúdo textual
                    if len(texto_limpo) < 8:
                        continue

                    comentarios_existentes[c_id] = {
                        "id": c_id,
                        "rede": "youtube",
                        "video_id": vid_id,
                        "video_titulo": v_tit,
                        "canal": v_canal,
                        "autor": top.get("authorDisplayName", "Anônimo"),
                        "texto": texto_limpo,
                        "likes": top.get("likeCount", 0),
                        "data": top.get("publishedAt", ""),
                        "link_origem": f"https://www.youtube.com/watch?v={vid_id}&lc={c_id}"
                    }
                    novos_adicionados += 1
        except Exception:
            continue

    # Política de retenção de 7 dias: descarta comentários mais antigos
    lista_final = [
        c for c in comentarios_existentes.values()
        if calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS
    ]
    if lista_final:
        try:
            with open(CACHE_COMENTARIOS, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return lista_final
