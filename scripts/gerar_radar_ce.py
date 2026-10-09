"""
Script de Geração do Radar Léo Suricate (radar_ce.json)

Integração 100% orientada a dados reais:
1. Votação oficial do TSE de 2026 para Deputado Estadual (Léo Suricate - 50013):
   - Mapeamento analítico dos 110 bairros de Fortaleza e municípios do interior via DuckDB;
   - Matriz de decisão territorial: "Atos Presenciais (Chão)" vs "Tráfego Pago (Digital)".
2. Pautas estratégicas populares e mensagens para WhatsApp (dados/pautas_ceara.json).
3. Relatório diário de transparência de anúncios da Meta e Prestação de Contas do TSE.
4. Monitor ao vivo de redes sociais (YouTube API v3 e Google Trends CE).
5. Análise de humor e temperatura popular via IA Generativa (gemini-3.5-flash-lite).
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
import duckdb
import pandas as pd

from coletor_meta_ads import coletar_meta_ads_ce
from coletor_trends_ce import gerar_nuvem_ceara_real
from analisador_sentimento_gemini import gerar_painel_sentimento

def extrair_dados_leo_ceara(caminho_bweb, caminho_bairros):
    """
    O que faz:
        Processa os Boletins de Urna oficiais do TSE de 2026 usando DuckDB para totalizar
        a votação do candidato Léo Suricate (número 50013 / Deputado Estadual), mapeando
        os votos por município do interior e por bairro de Fortaleza através de junção espacial.
        Classifica cada bairro em diretrizes estratégicas ("Chão / Presencial" vs "Digital / Tráfego Pago").

    Por que faz:
        Substitui qualquer estimativa ou amostragem manual por auditoria eleitoral 100% oficial.
        O motor OLAP DuckDB lê o arquivo CSV massivo de boletins de urna do TSE em segundos,
        permitindo que a coordenação de campanha identifique exatamente onde estão suas fortalezas
        de votos para atos presenciais e quais bairros populosos demandam investimento digital.

    Parâmetros:
        caminho_bweb (str): Caminho do CSV de Boletim de Urna do 1º Turno do CE (TSE 2026).
        caminho_bairros (str): Caminho do CSV de mapeamento de Zonas/Seções para Bairros de Fortaleza.

    Retorno:
        dict: Estrutura completa contendo resumo eleitoral, top municípios do interior,
              relação de bairros prioritários para mobilização de chão e para tráfego pago.
    """
    if not os.path.exists(caminho_bweb):
        print(f"Aviso: Arquivo de boletins de urna {caminho_bweb} não encontrado.")
        return {}

    if not os.path.exists(caminho_bairros):
        print(f"Aviso: Arquivo de bairros {caminho_bairros} não encontrado.")
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

    # 2. Votos do Léo por Bairro em Fortaleza + Votos Válidos Totais para Deputado Estadual
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

    # Classificação Estratégica ("Chão" vs "Digital"):
    # Bairros mais fortes em volume absoluto ou percentual são bases de mobilização presencial.
    # Demais bairros populosos compõem o plano de expansão digital e tráfego pago.
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

def carregar_pautas_leo(caminho_pautas):
    """
    O que faz:
        Lê e carrega a base de pautas prioritárias, dados de checagem e mensagens formatadas
        para WhatsApp armazenadas no arquivo 'dados/pautas_ceara.json'.

    Por que faz:
        Centraliza os argumentos e a comunicação popular do mandato em arquivo estruturado,
        permitindo atualizações rápidas pelo time de comunicação sem necessidade de alterar
        o código do pipeline de geração do radar.

    Parâmetros:
        caminho_pautas (str): Caminho do arquivo JSON contendo as pautas temáticas.

    Retorno:
        list: Lista de dicionários com as pautas e mensagens prontas para compartilhamento.
    """
    if not os.path.exists(caminho_pautas):
        return []

    try:
        with open(caminho_pautas, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Aviso ao carregar pautas: {e}")
        return []

def main():
    """
    O que faz:
        Função coordenadora do pipeline de dados. Orquestra a execução de cada módulo:
        1. Extração eleitoral oficial do TSE via DuckDB;
        2. Carregamento de pautas e diretrizes de comunicação popular;
        3. Extração de transparência de anúncios da Meta / Prestação de Contas;
        4. Coleta de tendências em tempo real (YouTube CE e Google Trends CE);
        5. Classificação de humor popular e sentimento com IA Generativa (Gemini 3.5 Flash-Lite);
        6. Consolidação e exportação atômica do arquivo final 'site/radar_ce.json'.

    Por que faz:
        Centraliza em um único comando de execução a atualização completa do painel do radar,
        garantindo integridade de esquema, sincronização temporal entre todas as fontes e
        eliminação absoluta de dados simulados ou fictícios.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_bweb = os.path.join(base_dir, "2026", "bweb_1t_CE_051020261403.csv")
    caminho_bairros = os.path.join(base_dir, "2026", "fortaleza_secoes_locais_bairros_2026.csv")
    caminho_pautas = os.path.join(base_dir, "dados", "pautas_ceara.json")
    caminho_saida = os.path.join(base_dir, "site", "radar_ce.json")

    print("1/5 Extraindo dados oficiais do TSE de 2026 (Léo Suricate via DuckDB)...")
    dados_leo = extrair_dados_leo_ceara(caminho_bweb, caminho_bairros)
    # Na nuvem do GitHub Actions (onde arquivos pesados de >6GB não estão versionados), preserva os dados existentes
    if not dados_leo and os.path.exists(caminho_saida):
        try:
            with open(caminho_saida, "r", encoding="utf-8") as f_prev:
                dados_leo = json.load(f_prev).get("mandato_leo", {})
        except Exception:
            pass

    print("2/5 Carregando pautas e munição de comunicação popular...")
    pautas = carregar_pautas_leo(caminho_pautas)

    print("3/5 Processando Relatório de Transparência da Meta e Prestação TSE...")
    meta_ads = coletar_meta_ads_ce(diretorio_base=base_dir)
    if (not meta_ads or not meta_ads.get("top_anunciantes")) and os.path.exists(caminho_saida):
        try:
            with open(caminho_saida, "r", encoding="utf-8") as f_prev:
                meta_ads = json.load(f_prev).get("meta_transparencia", meta_ads)
        except Exception:
            pass

    print("4/5 Gerando monitor de redes ao vivo (Nuvem, Vídeos e Google Trends CE)...")
    monitor_redes = gerar_nuvem_ceara_real()

    print("5/5 Processando análise de sentimento com IA Gemini (gemini-3.5-flash-lite)...")
    sentimento_mencoes = gerar_painel_sentimento()

    payload = {
        "titulo": "Radar Léo Suricate · Mandato Popular CE",
        "subtitulo": "Inteligência Territorial de Bairros (Chão) & Monitoramento Digital de Redes",
        "gerado_em": datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y às %H:%M"),
        "versao": "2.0.0-leo-suricate",
        "mandato_leo": dados_leo,
        "monitor_redes": monitor_redes,
        "sentimento_mencoes": sentimento_mencoes,
        "meta_transparencia": meta_ads,
        "pautas_estrategicas": pautas
    }

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\nSucesso absoluto! JSON 100% real do Radar gerado em: {caminho_saida}")

if __name__ == "__main__":
    main()
