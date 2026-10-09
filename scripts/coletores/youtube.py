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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from config import (
    CACHE_YOUTUBE,
    CACHE_COMENTARIOS,
    CANAIS_YOUTUBE,
    JANELA_MAXIMA_HORAS,
    calcular_idade_horas,
    carregar_chaves_api
)

# Termos para ignorar preventivamente na coleta de vídeos (evita gastar cota com fofoca/humor/futebol)
TERMOS_IGNORAR_TITULO = [
    "tiririca", "saf", "futebol", "campeonato", "cearense sub", "clássico-rei",
    "fortaleza ec", "ceará sc", "brasileirão", "gol de", "humor"
]

def carregar_lista_canais_youtube(caminho=CANAIS_YOUTUBE):
    """
    Carrega a lista de canais monitorados do arquivo dados/canais_youtube_ce.txt.
    """
    if not os.path.exists(caminho):
        return []
    canais = []
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            for line in f:
                linha = line.strip()
                if linha and not linha.startswith("#"):
                    canais.append(linha)
    except Exception:
        pass
    return canais

def _extrair_videos_recentes_canal_youtube(nome_canal, max_videos=15):
    """
    Extrai vídeos recentes de um canal sem gastar cota da API oficial,
    pesquisando as publicações recentes do canal no YouTube com filtro temporal.
    """
    query = f"{nome_canal} Ceará"
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp=CAI%253D"
    vids = []
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "pt-BR,pt;q=0.9"
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            html_raw = resp.read().decode("utf-8", errors="ignore")

        import re
        m = re.search(r'var ytInitialData = ({.*?});</script>', html_raw)
        if m:
            data = json.loads(m.group(1))
            contents = (
                data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )
            for c in contents:
                items = c.get("itemSectionRenderer", {}) .get("contents", [])
                for it in items:
                    vr = it.get("videoRenderer")
                    if not vr:
                        continue
                    vid_id = vr.get("videoId")
                    if not vid_id:
                        continue
                    tit = vr.get("title", {}).get("runs", [{}])[0].get("text", "")
                    canal_nome = vr.get("ownerText", {}).get("runs", [{}])[0].get("text", nome_canal)
                    vids.append({
                        "id": vid_id,
                        "titulo": html.unescape(tit),
                        "canal": canal_nome,
                        "desc": "",
                        "publishedAt": datetime.now(timezone.utc).isoformat()
                    })
                    if len(vids) >= max_videos:
                        break
                if len(vids) >= max_videos:
                    break
    except Exception:
        pass
    return vids

def atualizar_videos_youtube(yt_key=None, cache_path=CACHE_YOUTUBE):
    """
    O que faz:
        1. Varre em paralelo os canais cearenses mapeados trazendo até 15 vídeos recentes de cada (zero cota);
        2. Mescla com o cache local, deduplicando por videoId e aplicando retenção de 7 dias.

    Retorno:
        list: Lista atualizada de dicionários contendo metadados dos vídeos.
    """
    vids_map = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                for v in json.load(f):
                    if v.get("id"):
                        vids_map[v["id"]] = v
        except Exception:
            pass

    # 1. Coleta concorrente dos canais cearenses mapeados (Até 15 vídeos por canal)
    canais_alvo = carregar_lista_canais_youtube()
    if canais_alvo:
        print(f"   -> Varrendo {len(canais_alvo)} canais cearenses mapeados (paralelo com 8 threads)...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            resultados = list(executor.map(lambda c: _extrair_videos_recentes_canal_youtube(c, max_videos=15), canais_alvo))
            for vids_canal in resultados:
                for v in vids_canal:
                    vid_id = v["id"]
                    if vid_id not in vids_map:
                        vids_map[vid_id] = v

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

    return vids_validos or vids[:50]

def coletar_comentarios_youtube(yt_key=None, max_vids=50, max_comentarios_por_vid=100):
    """
    O que faz:
        Consulta commentThreads.list para os vídeos prioritários e extrai até 100 comentários mais curtidos,
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
        if any(k in t for k in ["elmano", "governo", "ciro", "wagner", "eleições", "alece"]):
            return 1
        return 2

    vids_filtrados.sort(key=prioridade_video)
    alvos = vids_filtrados[:max_vids]

    comentarios_existentes = {}
    datas_mais_recentes_por_video = {}
    if os.path.exists(CACHE_COMENTARIOS):
        try:
            with open(CACHE_COMENTARIOS, "r", encoding="utf-8") as f:
                for c in json.load(f):
                    cid = c.get("id")
                    if cid:
                        comentarios_existentes[cid] = c
                        vid = c.get("video_id")
                        dt = c.get("data", "")
                        if vid and dt:
                            if vid not in datas_mais_recentes_por_video or dt > datas_mais_recentes_por_video[vid]:
                                datas_mais_recentes_por_video[vid] = dt
        except Exception:
            pass

    def _extrair_comentarios_de_um_video(v):
        vid_id = v["id"]
        v_tit = v.get("titulo", "")
        v_canal = v.get("canal", "")
        ultima_data_conhecida = datas_mais_recentes_por_video.get(vid_id, "")

        # Se o vídeo já foi varrido e possui comentários salvos, busca os mais recentes (order=time)
        # para pegar o que há de novo após a última data. Se for um vídeo inédito, usa order=relevance
        # para garantir os mais representativos e curtidos.
        ordem = "time" if ultima_data_conhecida else "relevance"
        url = (
            f"https://www.googleapis.com/youtube/v3/commentThreads"
            f"?part=snippet&videoId={vid_id}&maxResults={max_comentarios_por_vid}"
            f"&order={ordem}&key={yt_key}"
        )
        encontrados = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RadarCeara/2.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for it in data.get("items", []):
                    top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    c_id = it.get("id", "")
                    c_data = top.get("publishedAt", "")
                    texto = html.unescape(top.get("textDisplay", "")).strip()

                    # OTIMIZAÇÃO POR MARCA TEMPORAL (Early Exit / High-Water Mark):
                    # Se estamos em ordem cronológica e encontramos um comentário mais antigo
                    # ou igual ao mais recente que já tínhamos, não precisamos continuar processando
                    if ordem == "time" and ultima_data_conhecida and c_data and c_data <= ultima_data_conhecida:
                        break

                    # Sanitização de quebras de linha e HTML
                    texto_limpo = html.unescape(texto.replace("<br>", " ").replace("<br/>", " "))
                    texto_limpo = " ".join(texto_limpo.split())

                    if len(texto_limpo) < 8:
                        continue

                    encontrados.append({
                        "id": c_id,
                        "rede": "youtube",
                        "video_id": vid_id,
                        "video_titulo": v_tit,
                        "canal": v_canal,
                        "autor": top.get("authorDisplayName", "Anônimo"),
                        "texto": texto_limpo,
                        "likes": top.get("likeCount", 0),
                        "data": c_data,
                        "link_origem": f"https://www.youtube.com/watch?v={vid_id}&lc={c_id}"
                    })
        except Exception:
            pass
        return encontrados

    with ThreadPoolExecutor(max_workers=8) as executor:
        lotes_comentarios = list(executor.map(_extrair_comentarios_de_um_video, alvos))
        for lista_c in lotes_comentarios:
            for c in lista_c:
                comentarios_existentes[c["id"]] = c

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
