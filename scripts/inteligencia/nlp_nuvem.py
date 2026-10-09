"""
Módulo de Processamento de Linguagem Natural (NLP) e Cálculo de Tendências.

O que faz:
    Analisa o conjunto de publicações de redes sociais (vídeos, títulos, descrições)
    para calcular a Nuvem de Termos Ponderada (12h, 24h, 48h) e o ranking Top 10
    por campo político (Pró-Oposição vs Campo Popular / Léo).
"""

import unicodedata
from datetime import datetime

from config import FUSO_CE

def normalizar_texto(texto):
    """
    Remove acentos e converte para minúsculas.
    """
    if not texto:
        return ""
    nfd = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

# Termos monitorados para a nuvem de palavras
TERMOS_RADAR_NUVEM = [
    ("Ciro Gomes", "disputa", ["ciro gomes", "ciro"]),
    ("Léo Suricate", "nossa", ["leo suricate", "leosuricate", "suricate"]),
    ("Ônibus e Terminais", "nossa", ["onibus", "terminal", "transporte", "parangaba", "messejana"]),
    ("Lula", "nossa", ["lula"]),
    ("Fim da 6x1", "nossa", ["6x1", "escala 6x1", "trabalhador"]),
    ("André Fernandes", "deles", ["andre fernandes", "andrefernandes"]),
    ("Elmano de Freitas", "nossa", ["elmano"]),
    ("Cid Gomes", "disputa", ["cid gomes", "cid"]),
    ("Assembleia Legislativa", "disputa", ["assembleia legislativa", "alece"]),
    ("Capitão Wagner", "deles", ["capitao wagner", "wagner"]),
    ("Tiririca", "disputa", ["tiririca"]),
    ("Carmelo Neto", "deles", ["carmelo neto", "carmelo"]),
    ("Direita Fortaleza", "deles", ["direita", "bolsonaro", "pl"]),
    ("Pé-de-Meia", "nossa", ["pe-de-meia", "pe de meia"]),
    ("Passe Livre", "nossa", ["passe livre", "tarifa zero"]),
    ("Segurança e Facções", "deles", ["seguranca", "faccao", "crime", "policia"]),
    ("Cultura Periférica", "nossa", ["periferia", "cultura", "cuca"]),
    ("Cláudio Pinho", "disputa", ["claudio pinho"]),
    ("Prefeitura Fortaleza", "disputa", ["prefeitura", "evandro leitao", "sarto"]),
    ("Camilo Santana", "nossa", ["camilo santana", "camilo"]),
    ("Areninhas e Juventude", "nossa", ["areninha", "juventude", "batalha"]),
    ("Críticas a Elmano", "deles", ["critica elmano", "oposicao", "denuncia", "rombo"]),
    ("IPVA e Tributos", "deles", ["ipva", "tributos", "impostos", "taxa"]),
    ("Gastos Públicos", "deles", ["gasto", "gastos", "desperdicio"])
]

TEMAS_OPOSICAO = [
    ("André Fernandes", ["andre fernandes", "andrefernandes"]),
    ("Capitão Wagner", ["capitao wagner", "wagner"]),
    ("Carmelo Neto", ["carmelo neto", "carmelo"]),
    ("Segurança e Facções", ["seguranca", "faccao", "crime", "policia"]),
    ("Críticas a Elmano", ["critica", "rombo", "saude em crise", "denuncia", "oposicao"]),
    ("IPVA e Tributos", ["ipva", "tributo", "imposto", "taxa"]),
    ("Direita Fortaleza", ["direita", "bolsonaro", "pl"]),
    ("Polícia Militar", ["policia militar", "raio", "pm"]),
    ("Tiririca / Crítica", ["tiririca"]),
    ("Gastos Públicos", ["gasto publico", "orcamento", "alece"])
]

TEMAS_CAMPO_POPULAR = [
    ("Léo Suricate", ["leo suricate", "suricate"]),
    ("Ônibus e Terminais", ["onibus", "terminal", "transporte", "parangaba", "messejana"]),
    ("Lula / Mobilização", ["lula", "governo federal"]),
    ("Fim da 6x1", ["6x1", "escala 6x1", "trabalhador"]),
    ("Elmano de Freitas", ["elmano"]),
    ("Camilo Santana", ["camilo santana", "camilo"]),
    ("Passe Livre", ["passe livre", "tarifa zero", "passagem"]),
    ("Cultura Periférica", ["cultura", "periferia", "cuca", "rima"]),
    ("Pé-de-Meia", ["pe-de-meia", "pe de meia", "estudante"]),
    ("Areninhas e Juventude", ["areninha", "juventude", "esporte"])
]

def analisar_corpus_videos(sub_vids, horas_label):
    """
    Calcula as frequências de menções aos temas do Ceará para a janela temporal.
    """
    textos = [v.get("titulo", "") + " " + v.get("desc", "") for v in sub_vids]
    full_text = normalizar_texto(" ".join(textos))
    hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")

    # 1. Nuvem de Palavras
    ocorrencias = []
    for nome, lado, aliases in TERMOS_RADAR_NUVEM:
        cnt = sum(full_text.count(normalizar_texto(a)) for a in aliases)
        if cnt > 0:
            ocorrencias.append((nome, lado, cnt))

    ocorrencias.sort(key=lambda x: x[2], reverse=True)
    max_c = ocorrencias[0][2] if ocorrencias else 1
    nuvem_out = []
    for n, l, c in ocorrencias[:18]:
        peso = int(40 + round((c / max_c) * 58))
        peso = max(38, min(98, peso))
        nuvem_out.append({"t": n, "peso": peso, "lado": l})

    # 2. Ranking Top 10 Oposição
    scores_deles = []
    for t_nome, aliases in TEMAS_OPOSICAO:
        s = sum(full_text.count(normalizar_texto(a)) for a in aliases)
        scores_deles.append((t_nome, s + 1))
    tot_d = sum(s for _, s in scores_deles)
    itens_deles = []
    for t_nome, s in sorted(scores_deles, key=lambda x: x[1], reverse=True)[:10]:
        pct_val = round((s / tot_d) * 100, 1)
        itens_deles.append({"termo": t_nome, "pct": f"{pct_val}%".replace(".", ","), "valor": pct_val})

    # 3. Ranking Top 10 Campo Popular
    scores_nossa = []
    for t_nome, aliases in TEMAS_CAMPO_POPULAR:
        s = sum(full_text.count(normalizar_texto(a)) for a in aliases)
        scores_nossa.append((t_nome, s + 1))
    tot_n = sum(s for _, s in scores_nossa)
    itens_nossa = []
    for t_nome, s in sorted(scores_nossa, key=lambda x: x[1], reverse=True)[:10]:
        pct_val = round((s / tot_n) * 100, 1)
        itens_nossa.append({"termo": t_nome, "pct": f"{pct_val}%".replace(".", ","), "valor": pct_val})

    return {
        "total_videos": len(sub_vids),
        "janela": horas_label,
        "nuvem": nuvem_out,
        "videos_mais_falados": {
            "hora": hora_ce,
            "janela": horas_label,
            "total_videos": len(sub_vids),
            "oposicao": {"titulo": "PRÓ-OPOSIÇÃO", "itens": itens_deles},
            "popular": {"titulo": "CAMPO POPULAR / LÉO", "itens": itens_nossa}
        }
    }

def construir_monitor_redes(corpus_videos, itens_google_4h, itens_google_24h):
    """
    Consolida as 3 janelas temporais de vídeos (12h, 24h, 48h) com o Google Trends CE.
    """
    vids_12h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 12] or corpus_videos[:15]
    vids_24h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 24] or corpus_videos[:30]
    vids_48h = [v for v in corpus_videos if v.get("idade_horas", 999) <= 48] or corpus_videos

    res_12h = analisar_corpus_videos(vids_12h, "12h")
    res_24h = analisar_corpus_videos(vids_24h, "24h")
    res_48h = analisar_corpus_videos(vids_48h, "48h")

    if not itens_google_4h:
        itens_google_4h = itens_google_24h

    hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")
    google_trends_ce = {
        "hora": hora_ce,
        "janela": "4h",
        "itens": itens_google_4h,
        "itens_4h": itens_google_4h,
        "itens_24h": itens_google_24h
    }

    return {
        "nuvem": res_24h["nuvem"],
        "nuvens_por_janela": {
            "12h": res_12h["nuvem"],
            "24h": res_24h["nuvem"],
            "48h": res_48h["nuvem"]
        },
        "videos_mais_falados_ce": res_24h["videos_mais_falados"],
        "videos_por_janela": {
            "12h": res_12h["videos_mais_falados"],
            "24h": res_24h["videos_mais_falados"],
            "48h": res_48h["videos_mais_falados"]
        },
        "google_trends_ce": google_trends_ce
    }
