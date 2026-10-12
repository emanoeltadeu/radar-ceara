"""
Módulo Coletor do Google Trends Ceará (geo='BR-CE').

O que faz:
    Consulta e extrai os termos em alta no Ceará nas janelas de 4 horas e 24 horas,
    classificando as pautas associadas e volumes de busca.
"""

import os
import re
import html
import urllib.request
import unicodedata

from config import DADOS_DIR

def normalizar_texto(texto):
    """
    Remove acentos e converte para minúsculas.
    """
    if not texto:
        return ""
    nfd = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

def parse_volume_buscas(vol_str):
    """
    Converte volumes textuais (ex: '500 mil+') em inteiros para ordenação matemática.
    """
    if not vol_str:
        return 0
    v = vol_str.lower().replace("+", "").replace("pesquisas", "").replace("\xa0", " ").strip()
    if any(m in v for m in ["milhao", "milhão", "milhoes", "milhões"]):
        num = float(re.sub(r"[^\d,\.]", "", v).replace(",", "."))
        return int(num * 1000000)
    if "mil" in v or "k" in v:
        num = float(re.sub(r"[^\d,\.]", "", v).replace(",", "."))
        return int(num * 1000)
    try:
        return int(re.sub(r"[^\d]", "", v))
    except Exception:
        return 0

def extrair_itens_trends_html(html_content):
    """
    Extrai as linhas de tendências do HTML do Google Trends Ceará.
    """
    rows = re.findall(r'<tr[^>]*class=\"[^\"]*enOdEe[^\"]*\"[^>]*>(.*?)</tr>', html_content, re.DOTALL)
    items = []

    for r in rows:
        termo_m = re.search(r'<div class=\"mZ3RIc\">([^<]+)</div>', r)
        if not termo_m:
            continue
        termo = html.unescape(termo_m.group(1)).strip()

        vol_m = re.search(r'<div class=\"qNpYPd\">([^<]+)</div>', r)
        vol = vol_m.group(1).replace(" pesquisas", "").strip() if vol_m else ""

        detalhes_raw = re.findall(r"ssk='[0-9]+:([^']+)'", r)
        detalhes = [html.unescape(d).strip() for d in detalhes_raw if len(d) > 6 and not re.match(r'^[A-Za-z0-9]{6}$', d)]

        detalhes_str = " ".join(detalhes) if detalhes else ""
        pauta = f"Busca associada: {detalhes[0]}" if detalhes else "Tendência de pesquisa registrada no Ceará."

        t_low = (termo + " " + detalhes_str).lower()
        t_norm = normalizar_texto(t_low)

        # Classificação de alinhamento político tradicional
        if any(k in t_low for k in ["lula", "nordestino", "6x1", "suricate", "passe livre", "cuca", "pe-de-meia"]):
            lado = "nossa"
        elif any(k in t_low for k in ["bolsonaro", "direita", "faccao", "crime", "ipva"]):
            lado = "deles"
        else:
            lado = "disputa"

        # 1. Termos Cívico-Sociais e Políticos
        termos_civicos_sociais = [
            # Lideranças e Figuras Políticas
            "lula", "bolsonaro", "elmano", "camilo", "evandro", "sarto", "wagner",
            "leosuricate", "suricate", "janaina paschoal", "tarcisio", "haddad", "marcal",
            "moraes", "dino", "barroso", "zanin",
            # Eleições & Pesquisas
            "politica", "eleicao", "eleicoes", "voto", "pesquisa", "datafolha", "quaest",
            "ipolitica", "parana pesquisas", "presidente", "presidencial", "governador",
            "prefeito", "senador", "deputado", "segundo turno", "primeiro turno",
            "candidato", "candidatura", "urna", "urnas", "horario eleitoral",
            # Instituições & Poderes
            "alece", "prefeitura", "governo", "stf", "tse", "camara", "senado", "congresso",
            "justica", "anistia", "enel", "cagece", "ministerio",
            # Direitos, Trabalho & Economia
            "transporte", "passagem", "onibus", "frota", "metrofor", "vlt",
            "concurso", "escala 6x1", "6x1", "inflacao", "salario", "auxilio", "emprego",
            "desemprego", "trabalhador", "trabalho", "greve", "sindicato", "previdencia",
            "reforma", "imposto", "ipva", "iptu", "icms", "fgts", "pib", "renda",
            # Serviços Públicos e Cidadania
            "saude", "seguranca", "faccao", "faccoes", "policia", "hospitais", "upa",
            "escola", "educacao", "enem", "professor", "professores", "pe-de-meia",
            "cuca", "passe livre", "tarifa zero", "moradia", "saneamento"
        ]

        # 2. Termos Específicos de Esporte / Futebol
        termos_esporte = [
            "futebol", "goleada", "jogo", "jogos", "partida", "campeonato", "copa", "libertadores",
            "brasileirao", "champions", "serie a", "serie b", "rodada", "tabela", "classificacao",
            "escalacao", "gol", "gols", "estadio", "arena", "castelao", "placar", "resultado",
            "ceara sc", "fortaleza ec", "ferroviario", "flamengo", "palmeiras", "corinthians",
            "sao paulo", "vasco", "gremio", "internacional", "botafogo", "fluminense", "bahia",
            "sport", "nautico", "vitoria", "atletico", "cruzeiro", "mirassol", "vila nova",
            "avai", "cuiaba", "liverpool", "city", "real madrid", "barcelona", "seedorf",
            "alcaraz", "tenis", "cleland", "surf", "ufc", "boxe", "nba", "basquete", "volei",
            "treinador", "tecnico", "abel ferreira", "dorival", "neymar", "messi", "cr7", "ronaldo"
        ]

        if any(k in t_norm for k in termos_civicos_sociais):
            categoria = "politica_social"
        elif any(k in t_norm for k in termos_esporte) or " x " in t_norm:
            categoria = "esporte"
        else:
            categoria = "cotidiano_cultura"

        items.append({
            "termo": termo,
            "volume": vol,
            "lado": lado,
            "categoria": categoria,
            "pauta": pauta
        })

    items.sort(key=lambda x: parse_volume_buscas(x["volume"]), reverse=True)
    return items[:10]

def extrair_termos_socioeconomicos(itens_trends):
    """
    Filtra os termos classificados como 'politica_social' para injeção de contexto na IA.
    Retorna uma lista resumida de dicionários ou strings.
    """
    destaques = []
    for it in itens_trends or []:
        if it.get("categoria") == "politica_social":
            destaques.append({
                "termo": it.get("termo"),
                "volume": it.get("volume"),
                "pauta": it.get("pauta")
            })
    return destaques

def coletar_trends_ceara(hours=4):
    """
    Coleta os termos em alta do Google Trends para o Ceará.
    """
    cache_file = f"trends_ce_{hours}h.html" if hours == 4 else "trends_ce.html"
    cache_path = os.path.join(DADOS_DIR, cache_file)

    html_content = ""
    param_hours = f"&hours={hours}" if hours == 4 else ""
    url = f"https://trends.google.com.br/trending?geo=BR-CE{param_hours}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html_content = resp.read().decode("utf-8")
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html_content)
    except Exception as e:
        print(f"   [Trends {hours}h] Falha na requisição ao vivo ({e}). Tentando carregar cache local...")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            except Exception:
                pass

    if not html_content:
        return []

    return extrair_itens_trends_html(html_content)
