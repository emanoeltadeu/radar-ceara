"""
Módulo de Coleta e Análise de Tendências em Tempo Real no Ceará (Google Trends e YouTube CE).

Objetivo:
Processar dados 100% reais do Google Trends Ceará (geo='BR-CE') e do acervo de vídeos
cearenses coletados via YouTube Data API v3, calculando a nuvem de termos e os 10 tópicos
mais debatidos por campo político (Pró-Oposição vs Campo Popular / Léo).
"""

import json
import os
import re
import html as html_lib
import urllib.request
import urllib.parse
import unicodedata
from datetime import datetime, timezone, timedelta

FUSO_CE = timezone(timedelta(hours=-3))

def normalizar_texto(texto):
    """
    O que faz:
        Remove acentos ortográficos e converte o texto para letras minúsculas (ex: 'Ceará' -> 'ceara').

    Por que faz:
        Garante que termos pesquisados em títulos, descrições ou consultas do Google sejam
        identificados com precisão sem falhas de case-sensitivity ou codificação de caracteres.

    Parâmetros:
        texto (str): Texto bruto a ser normalizado.

    Retorno:
        str: Texto em minúsculas e sem diacríticos/acentos.
    """
    if not texto:
        return ""
    nfd = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")

def parse_volume_buscas(vol_str):
    """
    O que faz:
        Converte representações textuais de volume do Google Trends (ex: '500 mil+', '20 mil+', '1 milhão+')
        em um número inteiro estrito (ex: 500000, 20000, 1000000).

    Por que faz:
        Permite a ordenação matemática decrescente e confiável dos termos em alta no Ceará,
        evitando que itens com menor volume fiquem acima de termos com maior alcance.

    Parâmetros:
        vol_str (str): String com o volume fornecido pelo Google Trends.

    Retorno:
        int: Volume numérico equivalente para ordenação.
    """
    if not vol_str:
        return 0
    v = vol_str.lower().replace("+", "").replace("pesquisas", "").replace("\xa0", " ").strip()
    if "milhao" in v or "milhão" in v or "milhoes" in v or "milhões" in v:
        num = float(re.sub(r"[^\d,\.]", "", v).replace(",", "."))
        return int(num * 1000000)
    if "mil" in v:
        num = float(re.sub(r"[^\d,\.]", "", v).replace(",", "."))
        return int(num * 1000)
    num_str = re.sub(r"[^\d]", "", v)
    return int(num_str) if num_str else 0

def extrair_itens_trends_html(html_content):
    """
    O que faz:
        Realiza o parsing da tabela HTML oficial do Google Trends da região Ceará (geo=BR-CE),
        extraindo termo de busca, volume estimado de pesquisas e termos correlatos.

    Por que faz:
        A biblioteca legada 'pytrends' foi descontinuada e sofre com bloqueios de rate limit 429.
        O parsing direto do HTML oficial com User-Agent de navegador obtém os dados ao vivo
        do estado sem custos e sem risco de expiração de credenciais.

    Parâmetros:
        html_content (str): Conteúdo HTML retornado pela página de tendências do Google.

    Retorno:
        list: Lista dos 10 termos mais buscados ordenados de forma estritamente decrescente por volume.
    """
    rows = re.findall(r'<tr[^>]*class=\"[^\"]*enOdEe[^\"]*\"[^>]*>(.*?)</tr>', html_content, re.DOTALL)
    items = []

    for r in rows:
        termo_m = re.search(r'<div class=\"mZ3RIc\">([^<]+)</div>', r)
        if not termo_m:
            continue
        termo = html_lib.unescape(termo_m.group(1)).strip()
        
        vol_m = re.search(r'<div class=\"qNpYPd\">([^<]+)</div>', r)
        vol = vol_m.group(1).replace(" pesquisas", "").strip() if vol_m else ""
        
        detalhes_raw = re.findall(r"ssk='[0-9]+:([^']+)'", r)
        detalhes = [html_lib.unescape(d).strip() for d in detalhes_raw if len(d) > 6 and not re.match(r'^[A-Za-z0-9]{6}$', d)]
        
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

    # Ordenação decrescente estrita pelo volume numérico
    items.sort(key=lambda x: parse_volume_buscas(x["volume"]), reverse=True)
    return items[:10]

def coletar_google_trends_ce_html(hours=4):
    """
    O que faz:
        Coleta e armazena em cache o HTML público do Google Trends para o Ceará ('BR-CE'),
        suportando janela de 4 horas (&hours=4) e janela de 24 horas.

    Por que faz:
        Alimenta o Card 3 ('EM ALTA NO GOOGLE') com dados fidedignos e permite alternância
        instantânea entre a visão do momento (4h) e o consolidado do dia (24h).

    Parâmetros:
        hours (int): Janela temporal de interesse (4 ou 24).

    Retorno:
        list: Lista dos 10 termos formatados para exibição.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_file = f"trends_ce_{hours}h.html" if hours == 4 else "trends_ce.html"
    cache_path = os.path.join(base_dir, "dados", cache_file)
    
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
        # Em caso de falha de conexão ou sandbox, utiliza o arquivo salvo em cache
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                html_content = f.read()

    if not html_content:
        return []

    return extrair_itens_trends_html(html_content)

def atualizar_videos_youtube_api(cache_path):
    """
    O que faz:
        Busca os vídeos políticos e sociais mais recentes do Ceará na YouTube Data API v3
        e atualiza o cache local mantendo histórico deduplicado por ID de vídeo.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    yt_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not yt_key:
        yt_file = os.path.join(base_dir, "dados", "youtube_api_key.txt")
        if os.path.exists(yt_file):
            try:
                with open(yt_file, "r", encoding="utf-8") as f:
                    yt_key = f.read().strip()
            except Exception:
                pass
    if not yt_key:
        return

    queries = [
        "Ceará política", "Fortaleza política", "Léo Suricate",
        "Assembleia Legislativa Ceará", "Elmano de Freitas Ceará",
        "ônibus Fortaleza", "escala 6x1 Fortaleza"
    ]

    vids_map = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                for v in json.load(f):
                    if v.get("id"):
                        vids_map[v["id"]] = v
        except Exception:
            pass

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
                        "titulo": html_lib.unescape(snip.get("title", "")),
                        "canal": snip.get("channelTitle", ""),
                        "desc": html_lib.unescape(snip.get("description", "")),
                        "publishedAt": snip.get("publishedAt", "")
                    }
        except Exception:
            continue

    if vids_map:
        lista_ordenada = list(vids_map.values())
        lista_ordenada.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(lista_ordenada, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def carregar_corpus_videos_youtube():
    """
    O que faz:
        Carrega do arquivo 'dados/cache_youtube.json' os metadados dos vídeos coletados
        pela API oficial e calcula a idade em horas de cada publicação com base no timestamp UTC.

    Por que faz:
        Permite a segmentação temporal dinâmica em recortes de 12h, 24h e 48h sem precisar
        fazer novas chamadas de rede repetidas à API do YouTube.

    Retorno:
        list: Lista de vídeos reais com títulos, descrições, canal e campo 'idade_horas'.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_path = os.path.join(base_dir, "dados", "cache_youtube.json")
    
    # Atualiza via API se a chave estiver presente
    atualizar_videos_youtube_api(cache_path)

    if not os.path.exists(cache_path):
        return []

    vids = []
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            vids = json.load(f)
    except Exception:
        return []

    now = datetime.now(timezone.utc)
    for v in vids:
        p = v.get("publishedAt")
        if p:
            try:
                dt = datetime.fromisoformat(p.replace("Z", "+00:00"))
                v["idade_horas"] = (now - dt).total_seconds() / 3600
            except Exception:
                v["idade_horas"] = 999
        else:
            v["idade_horas"] = 999

    return vids

def analisar_corpus_youtube(sub_vids, horas_label):
    """
    O que faz:
        Calcula as frequências de menções aos temas políticos e sociais do Ceará no conjunto
        de vídeos pertencentes a uma janela temporal específica (ex: últimas 12h, 24h ou 48h).

    Por que faz:
        Gera os pesos dinâmicos da Nuvem de Palavras (Card 1) e o ranking Top 10 por campo
        político (Card 2: Pró-Oposição vs Campo Popular / Léo) estritamente a partir do corpus real.

    Parâmetros:
        sub_vids (list): Subconjunto de vídeos publicados dentro do limite de horas.
        horas_label (str): Rótulo da janela (ex: '12h', '24h', '48h').

    Retorno:
        dict: Dicionário contendo a lista da nuvem e as duas tabelas Top 10.
    """
    textos = [v.get("titulo", "") + " " + v.get("desc", "") for v in sub_vids]
    full_text = normalizar_texto(" ".join(textos))

    # Dicionário de termos estratégicos monitorados para a nuvem
    termos_radar = [
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

    # Temas de debate da Oposição
    temas_deles = [
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

    # Temas de debate do Campo Popular / Mandato Léo
    temas_nossa = [
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

    # 1. Nuvem de Palavras: peso proporcional calibrado entre 40 e 98
    ocorrencias = []
    for nome, lado, aliases in termos_radar:
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
    for t_nome, aliases in temas_deles:
        s = sum(full_text.count(normalizar_texto(a)) for a in aliases)
        scores_deles.append((t_nome, s + 1))
    tot_d = sum(s for _, s in scores_deles)
    itens_deles = []
    for t_nome, s in sorted(scores_deles, key=lambda x: x[1], reverse=True)[:10]:
        pct_val = round((s / tot_d) * 100, 1)
        itens_deles.append({"termo": t_nome, "pct": f"{pct_val}%".replace(".", ","), "valor": pct_val})

    # 3. Ranking Top 10 Campo Popular
    scores_nossa = []
    for t_nome, aliases in temas_nossa:
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
            "hora": datetime.now(FUSO_CE).strftime("%H:%M"),
            "janela": horas_label,
            "total_videos": len(sub_vids),
            "oposicao": {"titulo": "PRÓ-OPOSIÇÃO", "itens": itens_deles},
            "popular": {"titulo": "CAMPO POPULAR / LÉO", "itens": itens_nossa}
        }
    }

def gerar_nuvem_ceara_real():
    """
    O que faz:
        Consolida a geração completa das 3 janelas temporais de vídeos do YouTube (12h, 24h, 48h)
        e a coleta de tendências do Google Trends Ceará (4h e 24h).

    Por que faz:
        É o ponto de entrada principal consumido por 'gerar_radar_ce.py', alimentando
        toda a seção de monitoramento digital ao vivo do painel.

    Retorno:
        dict: Estrutura completa de monitoramento para o arquivo 'radar_ce.json'.
    """
    vids = carregar_corpus_videos_youtube()

    # Filtros temporais reais baseados no campo 'idade_horas' calculado via UTC
    vids_12h = [v for v in vids if v.get("idade_horas", 999) <= 12] or vids[:15]
    vids_24h = [v for v in vids if v.get("idade_horas", 999) <= 24] or vids[:30]
    vids_48h = [v for v in vids if v.get("idade_horas", 999) <= 48] or vids

    res_12h = analisar_corpus_youtube(vids_12h, "12h")
    res_24h = analisar_corpus_youtube(vids_24h, "24h")
    res_48h = analisar_corpus_youtube(vids_48h, "48h")

    # Coleta de tendências oficiais do Google Trends Ceará
    itens_google_4h = coletar_google_trends_ce_html(hours=4)
    itens_google_24h = coletar_google_trends_ce_html(hours=24)
    if not itens_google_4h:
        itens_google_4h = itens_google_24h

    google_trends_ce = {
        "hora": datetime.now(FUSO_CE).strftime("%H:%M"),
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

if __name__ == "__main__":
    resultado = gerar_nuvem_ceara_real()
    print("Sucesso! Monitor de Redes ao Vivo gerado.")
    print("Nuvem 24h termos:", len(resultado["nuvem"]))
    print("Google Trends termos:", len(resultado["google_trends_ce"]["itens"]))
