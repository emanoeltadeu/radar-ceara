#!/usr/bin/env python3
"""
Script para expurgar comentários de alvos de oposição/inimigos dos caches e do radar_ce.json,
recalculando todas as métricas analíticas e o Radar Tático com IA sobre a base limpa.
"""
import json
import os
import shutil
from datetime import datetime
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from config import (
    SAIDA_RADAR_JSON,
    CACHE_COMENTARIOS,
    CACHE_CLASSIFICADOS,
    CACHE_INSTAGRAM,
    CACHE_CLASSIFICADOS_IG,
    FUSO_CE,
    carregar_chaves_api
)
from inteligencia.radar_tatico import (
    gerar_insights_radar_tatico_yt,
    gerar_insights_radar_tatico_ig
)

def extrair_alvos_oposicao():
    raiz = Path(__file__).resolve().parent.parent

    # Canais YouTube comentados nas seções de oposição ou missão
    yt_op = []
    caminho_yt = raiz / "dados" / "canais_youtube_ce.txt"
    if caminho_yt.exists():
        with open(caminho_yt, "r", encoding="utf-8") as f:
            in_op = False
            for linha in f:
                if "OPOSIÇÃO" in linha or "MISSÃO" in linha:
                    in_op = True
                elif linha.startswith("# ---"):
                    in_op = False
                elif in_op and linha.strip().startswith("#"):
                    nome = linha.strip().lstrip("#").strip().lower()
                    if nome:
                        yt_op.append(nome)

    # Perfis Instagram comentados nas seções de oposição ou missão
    ig_op = []
    caminho_ig = raiz / "dados" / "perfis_instagram.txt"
    if caminho_ig.exists():
        with open(caminho_ig, "r", encoding="utf-8") as f:
            in_op = False
            for linha in f:
                if "OPOSIÇÃO" in linha or "MISSÃO" in linha:
                    in_op = True
                elif linha.startswith("# ---"):
                    in_op = False
                elif in_op and linha.strip().startswith("#"):
                    nome = linha.strip().lstrip("#").strip().lstrip("@").lower()
                    if nome:
                        ig_op.append(nome)

    return yt_op, ig_op

def identificar_ids_oposicao(yt_op_names, ig_op_names):
    # 1. YouTube via canal no cache
    yt_ids_op = set()
    if os.path.exists(CACHE_CLASSIFICADOS):
        with open(CACHE_CLASSIFICADOS, "r", encoding="utf-8") as f:
            cache_yt = json.load(f)
        for c in cache_yt:
            canal = (c.get("canal") or "").strip().lower()
            for op in yt_op_names:
                if op == canal or (len(op) > 4 and op in canal):
                    yt_ids_op.add(c.get("id"))
                    break

    # 2. Instagram via perfil/título/url no cache
    ig_ids_op = set()
    if os.path.exists(CACHE_CLASSIFICADOS_IG):
        with open(CACHE_CLASSIFICADOS_IG, "r", encoding="utf-8") as f:
            cache_ig = json.load(f)
        for c in cache_ig:
            tit = (c.get("origem_titulo") or "").lower()
            url = (c.get("link_origem") or c.get("post_url") or "").lower()
            eh_op = False
            for op in ig_op_names:
                if f"@{op}" in tit or f"/{op}/" in url or f"siga @{op}" in tit or f"via @{op}" in tit:
                    eh_op = True
                    break
            if not eh_op:
                if any(termo in tit for termo in ["missão", "#mbl", "renan santos", "carmelo neto"]):
                    eh_op = True
            if eh_op:
                ig_ids_op.add(c.get("id"))

    return yt_ids_op, ig_ids_op

def limpar_arquivo_json(caminho, ids_remover):
    if not os.path.exists(caminho):
        return 0, 0
    with open(caminho, "r", encoding="utf-8") as f:
        itens = json.load(f)
    if not isinstance(itens, list):
        return 0, 0
    original_len = len(itens)
    filtrados = [item for item in itens if item.get("id") not in ids_remover]
    removidos = original_len - len(filtrados)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(filtrados, f, ensure_ascii=False, indent=2)
    return removidos, len(filtrados)

def recalcular_janelas(bloco_sentimento, ids_remover):
    todos = bloco_sentimento.get("todos_comentarios", [])
    todos_limpos = [c for c in todos if c.get("id") not in ids_remover]
    bloco_sentimento["todos_comentarios"] = todos_limpos
    bloco_sentimento["amostras_destaque"] = sorted(
        todos_limpos, key=lambda x: x.get("likes", 0), reverse=True
    )[:5]

    # Recalcula raiz (7d)
    tot_raiz = len(todos_limpos)
    if tot_raiz > 0:
        pos_r = sum(1 for c in todos_limpos if c.get("sentimento") == "positivo")
        neu_r = sum(1 for c in todos_limpos if c.get("sentimento") == "neutro")
        neg_r = sum(1 for c in todos_limpos if c.get("sentimento") == "negativo")
        bloco_sentimento["total_analisados"] = tot_raiz
        bloco_sentimento["positivo_pct"] = round((pos_r / tot_raiz) * 100, 1)
        bloco_sentimento["neutro_pct"] = round((neu_r / tot_raiz) * 100, 1)
        bloco_sentimento["negativo_pct"] = round((neg_r / tot_raiz) * 100, 1)

    mapa_comms = {c.get("id"): c for c in todos_limpos}
    pj = bloco_sentimento.get("por_janela", {})

    for j_nome, j_dados in pj.items():
        ids_orig = j_dados.get("ids_comentarios", [])
        ids_filtrados = [cid for cid in ids_orig if cid not in ids_remover]
        j_dados["ids_comentarios"] = ids_filtrados

        comms_j = [mapa_comms[cid] for cid in ids_filtrados if cid in mapa_comms]
        tot_j = len(comms_j)
        j_dados["total_analisados"] = tot_j

        if tot_j > 0:
            pos_j = sum(1 for c in comms_j if c.get("sentimento") == "positivo")
            neu_j = sum(1 for c in comms_j if c.get("sentimento") == "neutro")
            neg_j = sum(1 for c in comms_j if c.get("sentimento") == "negativo")
            j_dados["positivo_pct"] = round((pos_j / tot_j) * 100, 1)
            j_dados["neutro_pct"] = round((neu_j / tot_j) * 100, 1)
            j_dados["negativo_pct"] = round((neg_j / tot_j) * 100, 1)
        else:
            j_dados["positivo_pct"] = 0.0
            j_dados["neutro_pct"] = 0.0
            j_dados["negativo_pct"] = 0.0

def main():
    print("🧹 Iniciando Expurgador de Comentários de Oposição...")

    yt_op_names, ig_op_names = extrair_alvos_oposicao()
    print(f"   -> Alvos de oposição YT mapeados: {len(yt_op_names)}")
    print(f"   -> Alvos de oposição IG mapeados: {len(ig_op_names)}")

    yt_ids_op, ig_ids_op = identificar_ids_oposicao(yt_op_names, ig_op_names)
    print(f"   -> IDs de oposição para expurgar no YouTube: {len(yt_ids_op)}")
    print(f"   -> IDs de oposição para expurgar no Instagram: {len(ig_ids_op)}")

    # 1. Limpeza dos Caches Locais
    print("\n📦 Atualizando arquivos de cache local...")
    rem_yt_b, rest_yt_b = limpar_arquivo_json(CACHE_COMENTARIOS, yt_ids_op)
    rem_yt_c, rest_yt_c = limpar_arquivo_json(CACHE_CLASSIFICADOS, yt_ids_op)
    print(f"   -> Cache YT bruto: -{rem_yt_b} | restante: {rest_yt_b}")
    print(f"   -> Cache YT classificado: -{rem_yt_c} | restante: {rest_yt_c}")

    rem_ig_b, rest_ig_b = limpar_arquivo_json(CACHE_INSTAGRAM, ig_ids_op)
    rem_ig_c, rest_ig_c = limpar_arquivo_json(CACHE_CLASSIFICADOS_IG, ig_ids_op)
    print(f"   -> Cache IG bruto: -{rem_ig_b} | restante: {rest_ig_b}")
    print(f"   -> Cache IG classificado: -{rem_ig_c} | restante: {rest_ig_c}")

    # 2. Limpeza e Recálculo no radar_ce.json
    print(f"\n⚡ Atualizando e recalculando {SAIDA_RADAR_JSON}...")
    with open(SAIDA_RADAR_JSON, "r", encoding="utf-8") as f:
        radar_data = json.load(f)

    recalcular_janelas(radar_data.get("sentimento_youtube", {}), yt_ids_op)
    recalcular_janelas(radar_data.get("sentimento_instagram", {}), ig_ids_op)

    # 3. Regeneração do Radar Tático IA sobre a base limpa
    print("\n🧠 Regenerando Radar Tático IA com Google Gemini (base limpa)...")
    chaves = carregar_chaves_api()
    gemini_key = chaves.get("gemini", "")

    comms_yt_limpos = radar_data.get("sentimento_youtube", {}).get("todos_comentarios", [])
    comms_ig_limpos = radar_data.get("sentimento_instagram", {}).get("todos_comentarios", [])

    print("   -> Gerando Radar Tático YouTube...")
    radar_data["radar_tatico_youtube"] = gerar_insights_radar_tatico_yt(comms_yt_limpos, gemini_key)

    print("   -> Gerando Radar Tático Instagram...")
    radar_data["radar_tatico_instagram"] = gerar_insights_radar_tatico_ig(comms_ig_limpos, gemini_key)

    hora_ce = datetime.now(FUSO_CE).strftime("%d/%m/%Y às %H:%M")
    radar_data["gerado_em"] = hora_ce

    # 4. Gravação Atômica
    temp_json = SAIDA_RADAR_JSON + ".tmp"
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump(radar_data, f, ensure_ascii=False, indent=2)
    os.replace(temp_json, SAIDA_RADAR_JSON)

    print(f"\n✅ Concluído com sucesso! Payload atualizado em {SAIDA_RADAR_JSON}")

if __name__ == "__main__":
    main()
