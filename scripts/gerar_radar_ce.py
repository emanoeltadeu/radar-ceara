"""
Pipeline Master · Radar Léo Suricate (Mandato Popular CE).

O que faz:
    Orquestrador único do pipeline de dados (ETL).
    1. Extract: Coleta concorrente do YouTube, Google Trends e Meta/TSE;
    2. Transform: Processamento de NLP, nuvem de termos e IA Generativa (Gemini);
    3. Load: Consolidação e geração atômica de 'site/radar_ce.json' para o Cloudflare Pages.
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Adiciona o diretório de scripts ao path de importação do Python
DIRETORIO_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if DIRETORIO_SCRIPTS not in sys.path:
    sys.path.insert(0, DIRETORIO_SCRIPTS)

from config import (
    SAIDA_RADAR_JSON,
    FUSO_CE,
    VERSAO_RADAR,
    CACHE_CLASSIFICADOS_IG,
    carregar_chaves_api
)
from coletores.youtube import (
    atualizar_videos_youtube,
    carregar_corpus_videos,
    coletar_comentarios_youtube
)
from coletores.google_trends import coletar_trends_ceara
from coletores.meta_ads import coletar_meta_ads_ce
from coletores.instagram_apify import coletar_comentarios_instagram_apify
from inteligencia.gemini import processar_sentimento_comentarios
from inteligencia.radar_tatico import (
    gerar_insights_radar_tatico_yt,
    gerar_insights_radar_tatico_ig
)

def executar_coleta_paralela():
    """
    O que faz:
        Dispara as coletas de rede de forma concorrente em threads paralelas
        (YouTube, Instagram, Google Trends e Meta/TSE).

    Retorno:
        tuple: (corpus_videos, comentarios_youtube, comentarios_instagram, trends_4h, trends_24h, meta_ads)
    """
    def tarefa_youtube():
        chaves = carregar_chaves_api()
        vids = atualizar_videos_youtube(chaves["youtube"])
        if not vids:
            vids = carregar_corpus_videos()
        comentarios = coletar_comentarios_youtube(chaves["youtube"])
        return vids, comentarios

    def tarefa_instagram():
        return coletar_comentarios_instagram_apify(max_posts_por_perfil=3, max_espera_segundos=35)

    def tarefa_trends():
        t4 = coletar_trends_ceara(hours=4)
        t24 = coletar_trends_ceara(hours=24)
        return t4, t24

    def tarefa_meta():
        return coletar_meta_ads_ce()

    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_yt = executor.submit(tarefa_youtube)
        fut_ig = executor.submit(tarefa_instagram)
        fut_trends = executor.submit(tarefa_trends)
        fut_meta = executor.submit(tarefa_meta)

        vids, comentarios_yt = fut_yt.result()
        comentarios_ig = fut_ig.result()
        trends_4h, trends_24h = fut_trends.result()
        meta_ads = fut_meta.result()

    return vids, comentarios_yt, comentarios_ig, trends_4h, trends_24h, meta_ads

def main():
    print("🚀 Iniciando Pipeline Modular do Radar Ceará (ETL)...")
    hora_inicio = datetime.now()

    # 1. Coleta Concorrente de Redes (YouTube, Instagram, Google Trends e Meta)
    print("1/4 Executando coleta paralela de redes (YouTube, Instagram, Trends e Meta)...")
    vids, comentarios_yt, comentarios_ig, trends_4h, trends_24h, meta_ads = executar_coleta_paralela()
    print(f"   -> YouTube: {len(vids)} vídeos no acervo | {len(comentarios_yt)} comentários")
    print(f"   -> Instagram: {len(comentarios_ig)} comentários coletados via Apify")

    # 2. Inteligência Territorial e Monitor de Tendências Transversais
    print("2/4 Consolidando tendências de busca no Ceará (Google Trends)...")
    chaves = carregar_chaves_api()
    monitor_redes = {
        "google_trends_ce": {
            "itens_4h": trends_4h,
            "itens_24h": trends_24h,
            "itens": trends_4h if trends_4h else trends_24h
        }
    }

    # 3. Inteligência Generativa (Google Gemini para YouTube e Instagram)
    print("3/4 Processando inteligência de sentimento no YouTube com Google Gemini...")
    sentimento_youtube = processar_sentimento_comentarios(comentarios_yt)
    print(f"   -> YouTube analisado: {sentimento_youtube.get('total_analisados', 0)} comentários")

    print("4/4 Processando inteligência de sentimento no Instagram com Google Gemini...")
    sentimento_instagram = processar_sentimento_comentarios(
        comentarios_ig,
        cache_path=CACHE_CLASSIFICADOS_IG
    )
    print(f"   -> Instagram analisado: {sentimento_instagram.get('total_analisados', 0)} comentários")

    # 4.1 Radar Tático IA (Diagnóstico Urgente Recente vs Diretriz Estratégica 24h)
    print("   -> Gerando Radar Tático IA (YouTube: Alerta Imediato + Consolidado 24h)...")
    comentarios_classificados_yt = sentimento_youtube.get("todos_comentarios") or sentimento_youtube.get("comentarios_todos") or []
    radar_tatico_yt = gerar_insights_radar_tatico_yt(comentarios_classificados_yt, chaves.get("gemini", ""))

    print("   -> Gerando Radar Tático IA (Instagram: Alerta Imediato + Consolidado 24h)...")
    comentarios_classificados_ig = sentimento_instagram.get("todos_comentarios") or sentimento_instagram.get("comentarios_todos") or []
    radar_tatico_ig = gerar_insights_radar_tatico_ig(comentarios_classificados_ig, chaves.get("gemini", ""))

    # 5. Consolidação e Gravação do Arquivo Final
    hora_ce = datetime.now(FUSO_CE).strftime("%d/%m/%Y às %H:%M")
    payload = {
        "titulo": "Radar Léo Suricate · Mandato Popular CE",
        "subtitulo": "Inteligência Territorial de Bairros (Chão) & Monitoramento Digital de Redes",
        "gerado_em": hora_ce,
        "versao": VERSAO_RADAR,
        "radar_tatico_youtube": radar_tatico_yt,
        "radar_tatico_instagram": radar_tatico_ig,
        "monitor_redes": monitor_redes,
        "sentimento_youtube": sentimento_youtube,
        "sentimento_instagram": sentimento_instagram,
        "meta_transparencia": meta_ads
    }

    os.makedirs(os.path.dirname(SAIDA_RADAR_JSON), exist_ok=True)
    with open(SAIDA_RADAR_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    tempo_decorrido = (datetime.now() - hora_inicio).total_seconds()
    print(f"\n✅ Sucesso! Radar gerado em {tempo_decorrido:.1f}s em: {SAIDA_RADAR_JSON}")

if __name__ == "__main__":
    main()
