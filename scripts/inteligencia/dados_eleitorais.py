"""
Módulo de Processamento de Dados Eleitorais do Ceará (TSE 2026).

O que faz:
    Processa os Boletins de Urna oficiais do TSE de 2026 via DuckDB para totalizar
    a votação de Léo Suricate por município do interior e por bairro de Fortaleza,
    classificando as estratégias de chão (presencial) vs digital.
"""

import json
import os
import duckdb

from config import BASE_DIR, PAUTAS_CEARA, SAIDA_RADAR_JSON

def extrair_dados_leo_ceara(caminho_bweb=None, caminho_bairros=None):
    """
    Processa os Boletins de Urna oficiais usando DuckDB para totalizar
    a votação do candidato Léo Suricate (50013 / Deputado Estadual).
    """
    if caminho_bweb is None:
        caminho_bweb = os.path.join(BASE_DIR, "2026", "bweb_1t_CE_051020261403.csv")
    if caminho_bairros is None:
        caminho_bairros = os.path.join(BASE_DIR, "2026", "fortaleza_secoes_locais_bairros_2026.csv")

    if not os.path.exists(caminho_bweb) or not os.path.exists(caminho_bairros):
        # Em ambiente CI sem os CSVs pesados, recupera os dados consolidados existentes
        if os.path.exists(SAIDA_RADAR_JSON):
            try:
                with open(SAIDA_RADAR_JSON, "r", encoding="utf-8") as f:
                    return json.load(f).get("mandato_leo", {})
            except Exception:
                pass
        return {}

    con = duckdb.connect()

    # 1. Totalização Estadual e Top Municípios do Léo Suricate
    query_municipios = f"""
        SELECT NM_MUNICIPIO as municipio, SUM(QT_VOTOS) as votos
        FROM read_csv('{caminho_bweb}', delim=';', header=true, encoding='latin-1')
        WHERE DS_CARGO_PERGUNTA = 'Deputado Estadual' 
          AND NR_VOTAVEL = 50013
        GROUP BY NM_MUNICIPIO
        ORDER BY votos DESC
    """
    df_mun = con.execute(query_municipios).df()
    total_ceara = int(df_mun['votos'].sum())
    votos_fortaleza = int(df_mun[df_mun['municipio'] == 'FORTALEZA']['votos'].values[0]) if len(df_mun[df_mun['municipio'] == 'FORTALEZA']) > 0 else 0
    votos_interior = total_ceara - votos_fortaleza

    top_interior = []
    for _, row in df_mun[df_mun['municipio'] != 'FORTALEZA'].head(12).iterrows():
        top_interior.append({
            "municipio": row["municipio"],
            "votos": int(row["votos"]),
            "pct_total_leo": round(float(row["votos"] / total_ceara) * 100, 2),
            "acao_recomendada": "Plenária Regional & Visita Política" if row["votos"] >= 500 else "Articulação de Liderança Local"
        })

    # 2. Votos do Léo por Bairro em Fortaleza
    query_bairros = f"""
        WITH bweb_dep AS (
            SELECT NR_ZONA, NR_SECAO, 
                   SUM(CASE WHEN NR_VOTAVEL = 50013 THEN QT_VOTOS ELSE 0 END) as votos_leo,
                   SUM(QT_VOTOS) as votos_total_dep
            FROM read_csv('{caminho_bweb}', delim=';', header=true, encoding='latin-1')
            WHERE NM_MUNICIPIO = 'FORTALEZA'
              AND DS_CARGO_PERGUNTA = 'Deputado Estadual'
            GROUP BY NR_ZONA, NR_SECAO
        ),
        bairros AS (
            SELECT CAST(NR_ZONA AS INTEGER) as nr_zona, CAST(NR_SECAO AS INTEGER) as nr_secao, NM_BAIRRO as bairro
            FROM read_csv('{caminho_bairros}', delim=';', header=true)
        )
        SELECT b.bairro, 
               SUM(d.votos_leo) as votos_leo,
               SUM(d.votos_total_dep) as votos_validos_dep,
               ROUND(SUM(d.votos_leo) * 100.0 / NULLIF(SUM(d.votos_total_dep), 0), 2) as pct_leo
        FROM bweb_dep d
        JOIN bairros b ON d.NR_ZONA = b.nr_zona AND d.NR_SECAO = b.nr_secao
        GROUP BY b.bairro
        ORDER BY votos_leo DESC
    """
    df_bairros = con.execute(query_bairros).df()

    lista_presencial = []
    lista_digital = []

    for i, row in df_bairros.iterrows():
        bairro_nome = row["bairro"]
        votos = int(row["votos_leo"])
        validos = int(row["votos_validos_dep"])
        pct = float(row["pct_leo"]) if row["pct_leo"] is not None else 0.0

        item = {
            "bairro": bairro_nome,
            "votos_leo": votos,
            "votos_validos_total": validos,
            "pct_leo": pct,
            "posicao_ranking": i + 1
        }

        if i < 15 or pct >= 2.5:
            item["tipo_acao"] = "Ato Presencial / Mobilização de Base"
            item["estrategia"] = "Plenária de Mandato, Roda de Conversa nas Areninhas e Cucas, Prestação de Contas."
            lista_presencial.append(item)
        else:
            item["tipo_acao"] = "Tráfego Pago & Engajamento Digital"
            item["estrategia"] = "Impulsionamento de Reels/TikTok geolocalizado, focado na juventude 18-29 anos."
            lista_digital.append(item)

    return {
        "resumo_eleitoral": {
            "candidato": "Léo Suricate",
            "cargo": "Deputado Estadual (Eleito 2026)",
            "partido": "PSOL / Federação",
            "numero": 50013,
            "votos_totais_ceara": total_ceara,
            "votos_fortaleza": votos_fortaleza,
            "pct_fortaleza": round((votos_fortaleza / total_ceara) * 100, 1) if total_ceara else 0,
            "votos_interior": votos_interior,
            "pct_interior": round((votos_interior / total_ceara) * 100, 1) if total_ceara else 0,
            "total_bairros_com_voto": len(df_bairros)
        },
        "atos_presenciais_bairros": lista_presencial,
        "trafego_digital_bairros": lista_digital[:25],
        "top_interior": top_interior
    }

def carregar_pautas_leo(caminho_pautas=PAUTAS_CEARA):
    """
    Carrega a base de pautas prioritárias armazenadas em 'dados/pautas_ceara.json'.
    """
    if not os.path.exists(caminho_pautas):
        return []

    try:
        with open(caminho_pautas, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
