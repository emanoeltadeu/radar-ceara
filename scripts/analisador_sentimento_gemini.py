"""
Módulo de Coleta e Classificação de Sentimento com Gemini (gemini-3.5-flash-lite).

Objetivo:
Analisar comentários reais extraídos da API do YouTube sobre o debate político
e social no Ceará, classificando cada manifestação sob a perspectiva do mandato
popular de Léo Suricate (50013 / PSOL), com liberdade semântica total para a IA
identificar os temas e gatilhos emergentes nas redes.
"""

import json
import os
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from collections import Counter

# Modelo padrão do Google AI Studio configurado para este projeto
MODELO_GEMINI = "gemini-3.5-flash-lite"

# Termos para ignorar preventivamente na coleta de vídeos (evita gastar cota com fofoca/humor/futebol)
TERMOS_IGNORAR_TITULO = [
    "tiririca", "saf", "futebol", "campeonato", "cearense sub", "clássico-rei",
    "fortaleza ec", "ceará sc", "brasileirão", "gol de", "humor"
]

# Prompt de sistema calibrado para nuances políticas do Ceará com extração livre de temas
SYSTEM_PROMPT_POLITICA_CE = """
Você é um analista sênior de inteligência digital e comunicação política no Ceará.
Sua função é analisar comentários reais de vídeos do YouTube e classificar o sentimento e a pauta sob a ótica do Mandato Popular de LÉO SURICATE (Deputado Estadual do Ceará, PSOL / Campo Popular).

CONTEXTO POLÍTICO E LOCAL DO CEARÁ:
- Campo Popular / Mandato: Léo Suricate, Lula, Elmano de Freitas, Camilo Santana.
- Principais Pautas e Lutas: Fim da escala 6x1, Passe Livre Estudantil, tempo de espera e melhoria dos ônibus/terminais (Messejana, Siqueira, Parangaba, Papicu), juventude periférica, Cucas, Areninhas, Pé-de-Meia, combate à fome, cultura popular.
- Campo Adversário / Oposição: André Fernandes, Capitão Wagner, Carmelo Neto, discursos bolsonaristas, críticas a Elmano/Lula.
- Nuance Linguística: Atenção ao linguajar cearense ("massa", "paia", "arre égua", "botou pra descer", "marmota", "arrochar") e sarcasmos/ironias cotidianas.

REGRA MANDATÓRIA DE CORTE DE RELEVÂNCIA (DESCARTE DE RUÍDO):
Avalie primeiramente se o vídeo (contexto) e o comentário tratam de debate político, serviços públicos ou pautas sociais relevantes para o Ceará.
- CLASSIFIQUE COMO "irrelevante" (DESCARTE):
  * Fofocas, deboches vazios, piadas ou polêmicas de figuras folclóricas/cômicas (ex: Tiririca comentando derrota, gestos com dinheiro, palhaçadas);
  * Memes superficiais sem crítica social ou reivindicação de direitos;
  * Notícias de entretenimento, futebol, celebridades ou bate-bocas puramente pessoais desprovidos de impacto político/social;
  * Comentários genéricos de spam ou emojis sem mensagem.

REGRAS DE CLASSIFICAÇÃO DE SENTIMENTO (APENAS PARA ITENS RELEVANTES):
1. "positivo":
   - Elogio ao Léo ou ao campo popular;
   - Apoio às pautas sociais (ex: comemorar o fim da 6x1 ou passe livre);
   - Crítica legítima à oposição da extrema-direita.

2. "neutro":
   - Dúvidas práticas (ex: "onde vai ser o evento?", "que horas começa?");
   - Relatos informativos sem julgamento de valor;
   - Conteúdo genérico sobre votação sem posição partidária clara.

3. "negativo":
   - Ataques ao Léo, ao PSOL, a Lula ou ao governo estadual;
   - Discurso alinhado à oposição (defesa de pautas da direita);
   - Reclamações duras sobre transporte público, ônibus lotado ou violência.

4. "irrelevante":
   - Qualquer comentário ou vídeo associado aos critérios de corte/ruído definidos acima.

IDENTIFICAÇÃO LIVRE E DINÂMICA DO TEMA / GATILHO ("tema"):
Não use categorias genéricas. Extraia o assunto ou gatilho específico da conversa em 2 a 5 palavras no padrão Título (ex: 'Fim da Escala 6x1', 'Superlotação no Terminal Messejana', 'Mandato Popular Léo Suricate', 'Greve da Educação Infantil', 'Reeleição de Elmano de Freitas', 'Críticas da Oposição ao PT', 'Disputa Lula vs Bolsonaro', 'Passe Livre Estudantil', 'Segurança e Facções', 'Cultura e Areninhas').

FORMATO DE RESPOSTA OBRIGATÓRIO (JSON ARRAY):
Responda APENAS com um array JSON com a seguinte estrutura:
[
  {
    "id": <id_inteiro>,
    "sentimento": "positivo" | "neutro" | "negativo" | "irrelevante",
    "tipo": "apoio" | "cobranca_popular" | "ataque_oposicao" | "neutro" | "ruido_irrelevante",
    "tema": "<Nome descritivo da pauta/gatilho em 2 a 5 palavras>",
    "resumo": "<explicação curta de até 10 palavras>"
  }
]
"""

def carregar_chaves():
    """
    O que faz:
        Lê e retorna as credenciais da API do Gemini e da API do YouTube salvas em arquivos locais.

    Por que faz:
        Evita expor chaves de API diretamente no código-fonte versionado e permite
        que voluntários e desenvolvedores usem suas próprias chaves de forma isolada e segura.

    Retorno:
        tuple (gemini_key: str, youtube_key: str)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    yt_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    gemini_file = os.path.join(base_dir, "dados", "gemini_api_key.txt")
    yt_file = os.path.join(base_dir, "dados", "youtube_api_key.txt")
    
    if not gemini_key and os.path.exists(gemini_file):
        with open(gemini_file, "r", encoding="utf-8") as f:
            gemini_key = f.read().strip()
    if not yt_key and os.path.exists(yt_file):
        with open(yt_file, "r", encoding="utf-8") as f:
            yt_key = f.read().strip()
            
    return gemini_key, yt_key

def coletar_comentarios_youtube(max_vids=92, max_comentarios_por_vid=15):
    """
    O que faz:
        Consulta o endpoint oficial 'commentThreads.list' do YouTube Data API v3 para extrair
        os comentários mais relevantes (relevance) em todos os vídeos políticos cearenses disponíveis,
        filtrando preventivamente vídeos de entretenimento, futebol ou palhaçadas irrelevantes.

    Por que faz:
        Processa até 92 vídeos do acervo com consumo ínfimo de cota (1 unidade por requisição),
        garantindo uma base amostral robusta de 80 a 100+ comentários reais para alimentar a IA.

    Parâmetros:
        max_vids (int): Quantidade máxima de vídeos a inspecionar por ciclo de coleta (até 92).
        max_comentarios_por_vid (int): Quantidade de comentários mais curtidos por vídeo.

    Retorno:
        list: Lista de dicionários com comentários reais deduplicados por ID.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _, yt_key = carregar_chaves()
    if not yt_key:
        return []

    cache_vids_path = os.path.join(base_dir, "dados", "cache_youtube.json")
    if not os.path.exists(cache_vids_path):
        return []

    with open(cache_vids_path, "r", encoding="utf-8") as f:
        vids = json.load(f)

    cache_comentarios_path = os.path.join(base_dir, "dados", "cache_comentarios.json")
    comentarios_existentes = {}
    if os.path.exists(cache_comentarios_path):
        try:
            with open(cache_comentarios_path, "r", encoding="utf-8") as f:
                lista = json.load(f)
                for c in lista:
                    tit = c.get("video_titulo", "").lower()
                    if not any(ign in tit for ign in TERMOS_IGNORAR_TITULO):
                        comentarios_existentes[c["id"]] = c
        except Exception:
            pass

    # Filtrar vídeos eliminando títulos irrelevantes
    vids_filtrados = []
    for v in vids:
        if not v.get("id"):
            continue
        tit = v.get("titulo", "").lower()
        if any(ign in tit for ign in TERMOS_IGNORAR_TITULO):
            continue
        vids_filtrados.append(v)

    # Prioriza vídeos que citam o mandato, Léo Suricate, Lula ou temas centrais
    def prioridade_video(v):
        t = v.get("titulo", "").lower()
        if any(k in t for k in ["leo suricate", "suricate", "lula", "6x1", "onibus", "tarifa"]):
            return 0
        if any(k in t for k in ["elmano", "governo", "ciro", "wagner", "eleições"]):
            return 1
        return 2

    vids_filtrados.sort(key=prioridade_video)
    vids_selecionados = vids_filtrados[:max_vids]

    for v in vids_selecionados:
        vid_id = v["id"]
        url = (
            f"https://www.googleapis.com/youtube/v3/commentThreads"
            f"?part=snippet&videoId={vid_id}&maxResults={max_comentarios_por_vid}"
            f"&order=relevance&key={yt_key}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RadarCeara/2.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read().decode("utf-8"))
                for it in data.get("items", []):
                    c_id = it.get("id")
                    top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                    texto = html.unescape(top.get("textOriginal", "")).strip()
                    if not texto or len(texto) < 4:
                        continue
                    comentarios_existentes[c_id] = {
                        "id": c_id,
                        "video_id": vid_id,
                        "video_titulo": v.get("titulo", ""),
                        "canal": v.get("canal", ""),
                        "autor": top.get("authorDisplayName", "Anônimo"),
                        "texto": texto,
                        "likes": top.get("likeCount", 0),
                        "data": top.get("publishedAt", "")
                    }
        except Exception:
            # Vídeos com comentários desativados são ignorados com segurança
            pass

    todos_comentarios = list(comentarios_existentes.values())
    with open(cache_comentarios_path, "w", encoding="utf-8") as f:
        json.dump(todos_comentarios, f, ensure_ascii=False, indent=2)

    return todos_comentarios

def classificar_comentarios_gemini(comentarios, limite=120):
    """
    O que faz:
        Envia lotes de comentários não classificados ao modelo Gemini 3.5 Flash-Lite via API,
        fracionando em sublotes de até 30 comentários para garantir respostas precisas,
        aplicando o System Prompt político e extraindo temas de forma livre e orgânica.

    Por que faz:
        O fracionamento em sublotes previne timeouts de rede e respostas truncadas,
        enquanto a IA generativa descobre autonomamente as pautas quentes do momento
        sem depender de palavras-chave rígidas pré-definidas.

    Parâmetros:
        comentarios (list): Lista de comentários candidatos a classificação.
        limite (int): Limite máximo total de novos comentários a analisar.

    Retorno:
        list: Lista completa de comentários classificados persistidos no cache.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gemini_key, _ = carregar_chaves()
    if not gemini_key or not comentarios:
        return []

    cache_classificados_path = os.path.join(base_dir, "dados", "cache_comentarios_classificados.json")
    ja_classificados = {}
    if os.path.exists(cache_classificados_path):
        try:
            with open(cache_classificados_path, "r", encoding="utf-8") as f:
                ja_classificados = {c["id"]: c for c in json.load(f)}
        except Exception:
            pass

    para_classificar = [c for c in comentarios if c["id"] not in ja_classificados][:limite]
    if not para_classificar:
        return list(ja_classificados.values())

    tamanho_sublote = 15
    sublotes = [para_classificar[i:i + tamanho_sublote] for i in range(0, len(para_classificar), tamanho_sublote)]

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_GEMINI}:generateContent?key={gemini_key}"

    for num_sub, sublote in enumerate(sublotes):
        lote_prompt = []
        mapa_id = {}
        for i, c in enumerate(sublote):
            idx = i + 1
            mapa_id[idx] = c
            lote_prompt.append({
                "id": idx,
                "video_contexto": c.get("video_titulo", "")[:70],
                "texto": c.get("texto", "")[:300]
            })

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT_POLITICA_CE}]
            },
            "contents": [{
                "parts": [{"text": f"Classifique os seguintes comentários em JSON:\n{json.dumps(lote_prompt, ensure_ascii=False)}"}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        sucesso = False
        for tentativa in range(3):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=35) as r:
                    res_raw = json.loads(r.read().decode("utf-8"))
                    cand = res_raw.get("candidates", [])[0]
                    texto_saida = cand["content"]["parts"][0]["text"]
                    analises = json.loads(texto_saida)
                    
                    for a in analises:
                        idx = a.get("id")
                        if idx in mapa_id:
                            orig = dict(mapa_id[idx])
                            sent = a.get("sentimento", "neutro")
                            orig["sentimento"] = sent
                            orig["tipo"] = a.get("tipo", "neutro")
                            orig["tema"] = a.get("tema", "Debate Político").strip()
                            orig["resumo_ia"] = a.get("resumo", "")
                            orig["descartado"] = (sent == "irrelevante" or orig["tipo"] == "ruido_irrelevante")
                            ja_classificados[orig["id"]] = orig
                    sucesso = True
                    break
            except Exception as e:
                import time
                time.sleep(2 * (tentativa + 1))
                if tentativa == 2:
                    print(f"Aviso ao classificar sublote {num_sub+1}/{len(sublotes)} com Gemini: {e}")

    lista_final = list(ja_classificados.values())
    with open(cache_classificados_path, "w", encoding="utf-8") as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=2)

    return lista_final

def gerar_painel_sentimento():
    """
    O que faz:
        Consolida os comentários classificados da base real, descarta itens irrelevantes,
        agrega os temas mais frequentes de forma dinâmica e calcula as métricas proporcionais.

    Por que faz:
        Alimenta a chave 'sentimento_mencoes' em 'radar_ce.json' com dados qualificados e
        uma lista rica de temas livres descobertos pela IA, preenchendo as colunas de apoio
        e de ataques com múltiplos assuntos relevantes.

    Retorno:
        dict: Estrutura consolidada pronta para serialização no painel da aplicação.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_path = os.path.join(base_dir, "dados", "cache_comentarios_classificados.json")

    classificados = []
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                classificados = json.load(f)
        except Exception:
            pass

    gemini_key, yt_key = carregar_chaves()
    hora_ce = datetime.now(timezone(timedelta(hours=-3))).strftime("%H:%M")

    # Coleta incremental de novos comentários se chaves disponíveis
    if yt_key and gemini_key:
        try:
            novos_brutos = coletar_comentarios_youtube(max_vids=25, max_comentarios_por_vid=5)
            ja_ids = {c.get("id") for c in classificados if c.get("id")}
            pendentes = [c for c in novos_brutos if c.get("id") and c["id"] not in ja_ids]
            if pendentes:
                novos_classificados = classificar_comentarios_gemini(pendentes, limite=15)
                if novos_classificados:
                    classificados.extend(novos_classificados)
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(classificados, f, ensure_ascii=False, indent=2)
                    except Exception:
                        pass
        except Exception:
            pass
    elif len(classificados) < 80:
        comentarios = coletar_comentarios_youtube(max_vids=92)
        if comentarios:
            classificados = classificar_comentarios_gemini(comentarios, limite=80)

    # FILTRO MANDATÓRIO DE DESCARTE: ignora itens marcados como irrelevantes
    validos = [
        c for c in classificados 
        if c.get("sentimento") in ["positivo", "neutro", "negativo"] and not c.get("descartado")
    ]

    if not validos:
        return {
            "disponivel": False,
            "modelo": MODELO_GEMINI,
            "hora": hora_ce,
            "total_analisados": 0,
            "positivo_pct": 0.0,
            "neutro_pct": 0.0,
            "negativo_pct": 0.0,
            "divisao_tipos": {
                "apoio_popular": 0.0,
                "cobranca_servicos": 0.0,
                "ataque_oposicao": 0.0,
                "neutro_informativo": 0.0
            },
            "top_temas_positivos": [],
            "top_temas_negativos": [],
            "amostras_destaque": []
        }

    total = len(validos)
    pos_lista = [c for c in validos if c.get("sentimento") == "positivo"]
    neu_lista = [c for c in validos if c.get("sentimento") == "neutro"]
    neg_lista = [c for c in validos if c.get("sentimento") == "negativo"]

    pos = len(pos_lista)
    neu = len(neu_lista)
    neg = len(neg_lista)

    apoio = sum(1 for c in validos if c.get("tipo") == "apoio")
    cobranca = sum(1 for c in validos if c.get("tipo") == "cobranca_popular")
    ataque = sum(1 for c in validos if c.get("tipo") == "ataque_oposicao")

    # Contagem dinâmica das pautas extraídas livremente pela IA
    temas_pos_cnt = Counter(c.get("tema", "").strip() for c in pos_lista if c.get("tema") and c.get("tema") != "irrelevante")
    temas_neg_cnt = Counter(c.get("tema", "").strip() for c in neg_lista if c.get("tema") and c.get("tema") != "irrelevante")

    # Formatação rica com contagem de menções para preenchimento dos painéis
    top_pos = [
        {"tema": t, "qtd": cnt, "rotulo": f"{t} ({cnt} {('menção' if cnt == 1 else 'menções')})"}
        for t, cnt in temas_pos_cnt.most_common(6)
    ]
    top_neg = [
        {"tema": t, "qtd": cnt, "rotulo": f"{t} ({cnt} {('menção' if cnt == 1 else 'menções')})"}
        for t, cnt in temas_neg_cnt.most_common(6)
    ]

    # Lista completa de comentários válidos estruturados com link direto do YouTube
    lista_comentarios_payload = []
    for c in validos:
        vid_id = c.get("video_id", "")
        c_id = c.get("id", "")
        link_yt = f"https://www.youtube.com/watch?v={vid_id}&lc={c_id}" if vid_id and c_id else ""
        lista_comentarios_payload.append({
            "id": c_id,
            "video_id": vid_id,
            "video_titulo": c.get("video_titulo", ""),
            "canal": c.get("canal", ""),
            "autor": c.get("autor", "Internauta CE"),
            "texto": c.get("texto", "").strip(),
            "likes": c.get("likes", 0),
            "sentimento": c.get("sentimento", "neutro"),
            "tipo": c.get("tipo", "neutro"),
            "tema": c.get("tema", "").strip(),
            "resumo_ia": c.get("resumo_ia", ""),
            "link_yt": link_yt
        })

    # Amostras de destaque (comentários mais curtidos)
    amostras = sorted(lista_comentarios_payload, key=lambda x: x.get("likes", 0), reverse=True)[:5]

    return {
        "disponivel": True,
        "modelo": MODELO_GEMINI,
        "hora": hora_ce,
        "total_analisados": total,
        "positivo_pct": round((pos / total) * 100, 1),
        "neutro_pct": round((neu / total) * 100, 1),
        "negativo_pct": round((neg / total) * 100, 1),
        "divisao_tipos": {
            "apoio_popular": round((apoio / total) * 100, 1),
            "cobranca_servicos": round((cobranca / total) * 100, 1),
            "ataque_oposicao": round((ataque / total) * 100, 1),
            "neutro_informativo": round((neu / total) * 100, 1)
        },
        "top_temas_positivos": top_pos,
        "top_temas_negativos": top_neg,
        "amostras_destaque": amostras,
        "comentarios_todos": lista_comentarios_payload
    }

if __name__ == "__main__":
    painel = gerar_painel_sentimento()
    print("Métricas Reais de Sentimento Filtradas (Gemini):")
    print(f" - Total Válidos Analisados: {painel['total_analisados']}")
    print(f" - Positivo: {painel['positivo_pct']}% | Neutro: {painel['neutro_pct']}% | Negativo: {painel['negativo_pct']}%")
    print(" - Top Pautas Positivas:", [t["tema"] for t in painel["top_temas_positivos"]])
    print(" - Top Pautas Negativas:", [t["tema"] for t in painel["top_temas_negativos"]])
