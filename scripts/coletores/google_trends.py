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

        pauta = f"Busca associada: {detalhes[0]}" if detalhes else "Tendência de pesquisa registrada no Ceará."

        t_low = (termo + " " + pauta).lower()
        if any(k in t_low for k in ["lula", "nordestino", "6x1", "suricate", "passe livre", "cuca", "pe-de-meia"]):
            lado = "nossa"
        elif any(k in t_low for k in ["bolsonaro", "direita", "faccao", "crime", "ipva"]):
            lado = "deles"
        else:
            lado = "disputa"

        items.append({
            "termo": termo,
            "volume": vol,
            "lado": lado,
            "pauta": pauta
        })

    items.sort(key=lambda x: parse_volume_buscas(x["volume"]), reverse=True)
    return items[:10]

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
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            html_content = resp.read().decode("utf-8")
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html_content)
    except Exception:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            except Exception:
                pass

    if not html_content:
        return []

    return extrair_itens_trends_html(html_content)
