"""
Micro-script de atualização isolada do Google Trends Ceará (geo='BR-CE').

Finalidade:
    - Coleta os termos em alta nas janelas de 4 horas e 24 horas.
    - Atualiza cirurgicamente apenas o bloco monitor_redes["google_trends_ce"] no 'site/radar_ce.json'.
    - Zero consumo de Apify, zero tokens de IA (Gemini) e zero API do YouTube.
    - Fallback resiliente: preserva os dados existentes se houver bloqueio temporário ou erro de rede.
"""

import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
if DIRETORIO_ATUAL not in sys.path:
    sys.path.insert(0, DIRETORIO_ATUAL)

from coletores.google_trends import coletar_trends_ceara

CAMINHO_RADAR_JSON = os.path.join(os.path.dirname(DIRETORIO_ATUAL), "site", "radar_ce.json")

def atualizar_trends_isolado():
    print("📈 Iniciando micro-atualização do Google Trends Ceará...")

    if not os.path.exists(CAMINHO_RADAR_JSON):
        print(f"❌ Erro: Arquivo {CAMINHO_RADAR_JSON} não encontrado.")
        sys.exit(1)

    try:
        with open(CAMINHO_RADAR_JSON, "r", encoding="utf-8") as f:
            radar_dados = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler {CAMINHO_RADAR_JSON}: {e}")
        sys.exit(1)

    # Coleta isolada (4h e 24h)
    print("   -> Consultando Google Trends (4h)...")
    trends_4h = coletar_trends_ceara(hours=4)

    print("   -> Consultando Google Trends (24h)...")
    trends_24h = coletar_trends_ceara(hours=24)

    # Obter bloco anterior para fallback silencioso
    monitor_redes = radar_dados.setdefault("monitor_redes", {})
    trends_anterior = monitor_redes.get("google_trends_ce", {})

    itens_4h_final = trends_4h if trends_4h else trends_anterior.get("itens_4h", [])
    itens_24h_final = trends_24h if trends_24h else trends_anterior.get("itens_24h", [])

    if not trends_4h and not trends_24h:
        print("⚠️ Aviso: Google Trends não retornou novos dados (possível rate-limit). Mantendo dados anteriores.")
    else:
        print(f"✅ Coletados: {len(itens_4h_final)} termos (4h) | {len(itens_24h_final)} termos (24h)")

    # Data/Hora no fuso de Fortaleza/CE (UTC-3)
    agora_ce = datetime.now(ZoneInfo("America/Fortaleza"))
    timestamp_formatado = agora_ce.strftime("%d/%m/%Y às %H:%M")

    # Atualiza estritamente o bloco google_trends_ce
    monitor_redes["google_trends_ce"] = {
        "atualizado_em": timestamp_formatado,
        "frequencia_atualizacao": "A cada 4 horas",
        "itens_4h": itens_4h_final,
        "itens_24h": itens_24h_final,
        "itens": itens_4h_final if itens_4h_final else itens_24h_final
    }

    # Grava de volta no radar_ce.json de forma atômica
    try:
        with open(CAMINHO_RADAR_JSON, "w", encoding="utf-8") as f:
            json.dump(radar_dados, f, ensure_ascii=False, indent=2)
        print(f"🎯 'site/radar_ce.json' atualizado com sucesso em {timestamp_formatado}!")
    except Exception as e:
        print(f"❌ Erro ao salvar 'site/radar_ce.json': {e}")
        sys.exit(1)

if __name__ == "__main__":
    atualizar_trends_isolado()
