"""
Módulo de Inteligência Artificial Generativa (Google Gemini).

O que faz:
    Classifica comentários reais de redes sociais usando IA generativa calibrada
    para o contexto político do Ceará (sentimento, pauta, apoio popular, críticas).
    É agnóstico em relação à rede social de origem (YouTube, Instagram, etc.).
"""

import json
import os
import time
import urllib.request
from collections import Counter
from datetime import datetime

from config import (
    MODELO_GEMINI,
    CACHE_CLASSIFICADOS,
    CACHE_VIDEOS_CLASSIFICADOS,
    JANELA_MAXIMA_HORAS,
    calcular_idade_horas,
    carregar_chaves_api,
    FUSO_CE
)

SYSTEM_PROMPT_POLITICA_CE = """
Você é um analista sênior de inteligência digital e comunicação política no Ceará.
Sua função é analisar comentários reais de redes sociais e classificar o sentimento e a pauta sob a ótica do Mandato Popular de LÉO SURICATE (Deputado Estadual do Ceará, PSOL / Campo Popular).

CONTEXTO POLÍTICO E LOCAL DO CEARÁ:
- Campo Popular / Mandato: Léo Suricate, Lula, Elmano de Freitas, Camilo Santana.
- Principais Pautas e Lutas: Fim da escala 6x1, Passe Livre Estudantil, tempo de espera e melhoria dos ônibus/terminais (Messejana, Siqueira, Parangaba, Papicu), juventude periférica, Cucas, Areninhas, Pé-de-Meia, combate à fome, cultura popular.
- Campo Adversário / Oposição: André Fernandes, Capitão Wagner, Carmelo Neto, discursos bolsonaristas, críticas a Elmano/Lula.
- Nuance Linguística: Atenção ao linguajar cearense ("massa", "paia", "arre égua", "botou pra descer", "marmota", "arrochar") e sarcasmos/ironias cotidianas.

REGRA MANDATÓRIA DE CORTE DE RELEVÂNCIA (DESCARTE DE RUÍDO):
Avalie primeiramente se a publicação (contexto) e o comentário tratam de debate político, serviços públicos ou pautas sociais relevantes para o Ceará.
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
   - Qualquer comentário associado aos critérios de corte/ruído definidos acima.

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

def classificar_lote_comentarios_gemini(lote_comentarios, gemini_key):
    """
    Envia um sublote de até 15 comentários para a API do Gemini.
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_GEMINI}:generateContent?key={gemini_key}"

    linhas_prompt = []
    mapa_ids = {}
    for idx, c in enumerate(lote_comentarios):
        cid_local = idx + 1
        mapa_ids[cid_local] = c
        origem = c.get("video_titulo") or c.get("origem_titulo") or "Vídeo Político CE"
        rede = c.get("rede", "youtube").upper()
        linhas_prompt.append(f"[{cid_local}] ({rede} - {origem}) {c['autor']}: \"{c['texto']}\"")

    prompt_usuario = (
        "Classifique cada um dos comentários abaixo segundo as instruções do sistema.\n\n"
        + "\n".join(linhas_prompt)
        + "\n\nResponda APENAS com o JSON array válido."
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT_POLITICA_CE}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_usuario}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                cands = resp_json.get("candidates", [])
                if not cands:
                    return []
                txt = cands[0]["content"]["parts"][0]["text"].strip()
                analises = json.loads(txt)

                classificados = []
                for a in analises:
                    lid = a.get("id")
                    if lid in mapa_ids:
                        orig = mapa_ids[lid]
                        descartar = (a.get("sentimento") == "irrelevante" or a.get("tipo") == "ruido_irrelevante")
                        classificados.append({
                            **orig,
                            "sentimento": a.get("sentimento", "neutro"),
                            "tipo": a.get("tipo", "neutro"),
                            "tema": a.get("tema", "Geral Ceará"),
                            "resumo_ia": a.get("resumo", ""),
                            "descartado": descartar
                        })
                return classificados
        except urllib.error.HTTPError as e:
            if e.code in [429, 503] and tentativa < 2:
                time.sleep(3 * (tentativa + 1))
                continue
            return []
        except Exception:
            if tentativa < 2:
                time.sleep(2)
                continue
            return []

    return []

def processar_sentimento_comentarios(comentarios_unificados=None, cache_path=CACHE_CLASSIFICADOS):
    """
    O que faz:
        Processa comentários de redes sociais, aproveitando o histórico classificado
        e enviando novos comentários pendentes para o Gemini de forma incremental.

    Retorno:
        dict: Estrutura pronta para a chave 'sentimento_mencoes' do radar.
    """
    chaves = carregar_chaves_api()
    gemini_key = chaves["gemini"]
    hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")

    classificados = []
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                dados_brutos = json.load(f)
                vistos = set()
                classificados = []
                for c in dados_brutos:
                    cid = c.get("id")
                    if cid and cid not in vistos:
                        vistos.add(cid)
                        if calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS:
                            classificados.append(c)
                    elif not cid and calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS:
                        classificados.append(c)
        except Exception:
            pass

    # Se recebemos comentários unificados novos, filtra para a janela de 7 dias antes de enviar ao Gemini
    if comentarios_unificados and gemini_key:
        comentarios_recentes = [
            c for c in comentarios_unificados
            if calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS
        ]
        ja_classificados_ids = {c.get("id") for c in classificados if c.get("id")}
        pendentes = [c for c in comentarios_recentes if c.get("id") and c["id"] not in ja_classificados_ids]

        if pendentes:
            tamanho_sublote = 25
            limite_novos = 150
            pendentes_para_rodar = pendentes[:limite_novos]

            for i in range(0, len(pendentes_para_rodar), tamanho_sublote):
                sublote = pendentes_para_rodar[i:i + tamanho_sublote]
                novos_classificados = classificar_lote_comentarios_gemini(sublote, gemini_key)
                if novos_classificados:
                    for nv in novos_classificados:
                        nid = nv.get("id")
                        if nid and nid not in ja_classificados_ids:
                            ja_classificados_ids.add(nid)
                            classificados.append(nv)
                        elif not nid:
                            classificados.append(nv)
                time.sleep(1)

            if classificados:
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(classificados, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

    # Filtrar válidos (não descartados, únicos por ID e estritamente dentro da janela de 7 dias)
    vistos_validos = set()
    validos = []
    for c in classificados:
        cid = c.get("id")
        if (
            c.get("sentimento") in ["positivo", "neutro", "negativo"]
            and not c.get("descartado")
            and calcular_idade_horas(c.get("data")) <= JANELA_MAXIMA_HORAS
        ):
            if cid:
                if cid not in vistos_validos:
                    vistos_validos.add(cid)
                    validos.append(c)
            else:
                validos.append(c)

    # Janelas Temporais de Sentimento (1h, 2h, 12h, 24h e 7d)
    v_1h = [c for c in validos if calcular_idade_horas(c.get("data")) <= 1]
    v_2h = [c for c in validos if calcular_idade_horas(c.get("data")) <= 2]
    v_12h = [c for c in validos if calcular_idade_horas(c.get("data")) <= 12]
    v_24h = [c for c in validos if calcular_idade_horas(c.get("data")) <= 24]
    v_7d = validos

    res_1h = _calcular_metricas_sentimento(v_1h or validos[:15], "1h", hora_ce)
    res_2h = _calcular_metricas_sentimento(v_2h or validos[:35], "2h", hora_ce)
    res_12h = _calcular_metricas_sentimento(v_12h or validos[:80], "12h", hora_ce)
    res_24h = _calcular_metricas_sentimento(v_24h or validos[:150], "24h", hora_ce)
    res_7d = _calcular_metricas_sentimento(v_7d, "7d", hora_ce)

    res_final = dict(res_7d)
    res_final["por_janela"] = {
        "1h": res_1h,
        "2h": res_2h,
        "12h": res_12h,
        "24h": res_24h,
        "7d": dict(res_7d)
    }

    return res_final

def _calcular_metricas_sentimento(sub_validos, janela_label="7d", hora_ce=""):
    """
    Calcula as métricas proporcionais de sentimento, temas e amostras para um subconjunto de comentários.
    """
    if not hora_ce:
        hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")

    if not sub_validos:
        return {
            "disponivel": False,
            "janela": janela_label,
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
            "amostras_destaque": [],
            "todos_comentarios": [],
            "comentarios_todos": []
        }

    total = len(sub_validos)
    pos_lista = [c for c in sub_validos if c.get("sentimento") == "positivo"]
    neu_lista = [c for c in sub_validos if c.get("sentimento") == "neutro"]
    neg_lista = [c for c in sub_validos if c.get("sentimento") == "negativo"]

    pos = len(pos_lista)
    neu = len(neu_lista)
    neg = len(neg_lista)

    apoio = sum(1 for c in sub_validos if c.get("tipo") == "apoio")
    cobranca = sum(1 for c in sub_validos if c.get("tipo") == "cobranca_popular")
    ataque = sum(1 for c in sub_validos if c.get("tipo") == "ataque_oposicao")

    temas_pos_cnt = Counter(c.get("tema", "").strip() for c in pos_lista if c.get("tema") and c.get("tema") != "irrelevante")
    temas_neg_cnt = Counter(c.get("tema", "").strip() for c in neg_lista if c.get("tema") and c.get("tema") != "irrelevante")

    top_pos = [
        {"tema": t, "qtd": cnt, "rotulo": f"{t} ({cnt} {('menção' if cnt == 1 else 'menções')})"}
        for t, cnt in temas_pos_cnt.most_common(6)
    ]
    top_neg = [
        {"tema": t, "qtd": cnt, "rotulo": f"{t} ({cnt} {('menção' if cnt == 1 else 'menções')})"}
        for t, cnt in temas_neg_cnt.most_common(6)
    ]

    payload_comentarios = []
    for c in sub_validos:
        vid_id = c.get("video_id", "")
        c_id = c.get("id", "")
        link = (
            c.get("link_instagram")
            or c.get("link_youtube")
            or c.get("link_origem")
            or (f"https://www.youtube.com/watch?v={vid_id}&lc={c_id}" if vid_id and c_id else "")
        )

        payload_comentarios.append({
            "id": c_id,
            "rede": c.get("rede", "youtube"),
            "video_id": vid_id,
            "video_titulo": c.get("video_titulo") or c.get("origem_titulo", ""),
            "origem_titulo": c.get("origem_titulo") or c.get("video_titulo", ""),
            "canal": c.get("canal", ""),
            "autor": c.get("autor", "Anônimo"),
            "texto": c.get("texto", ""),
            "likes": c.get("likes", 0),
            "data": c.get("data", ""),
            "sentimento": c.get("sentimento", "neutro"),
            "tipo": c.get("tipo", "neutro"),
            "tema": c.get("tema", ""),
            "resumo_ia": c.get("resumo_ia", ""),
            "link_yt": link,
            "link_youtube": link,
            "link_instagram": link,
            "link_origem": link
        })

    amostras = sorted(payload_comentarios, key=lambda x: x.get("likes", 0), reverse=True)[:5]

    return {
        "disponivel": True,
        "janela": janela_label,
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
            "neutro_informativo": round(((total - apoio - cobranca - ataque) / total) * 100, 1)
        },
        "top_temas_positivos": top_pos,
        "top_temas_negativos": top_neg,
        "amostras_destaque": amostras,
        "todos_comentarios": payload_comentarios,
        "comentarios_todos": payload_comentarios
    }

SYSTEM_PROMPT_VIDEOS_CE = """
Você é um analista sênior de inteligência digital e comunicação política no Ceará.
Analise a lista de vídeos cearenses do YouTube (título, canal e descrição) e classifique cada um:

1. "campo":
   - "oposicao": pautas críticas a Lula/Elmano/PT/PSOL, alinhadas à oposição/direita cearense (André Fernandes, Capitão Wagner, Carmelo Neto, denúncias contra governo, rombo, cobrança pesada em segurança pública, críticas duras à gestão estadual/municipal).
   - "popular": pautas do campo popular e progressista (Léo Suricate, Lula, Elmano de Freitas, Camilo Santana, Passe Livre Estudantil, Fim da 6x1, transporte público coletivo, Areninhas, Pé-de-Meia, cultura periférica, movimentos sociais).
   - "neutro": pauta jornalística neutra, institucional, cobertura geral sem viés partidário nítido.
   - "ruido": entretenimento sem política, simulação de jogos, fofoca ou futebol sem impacto social.

2. "tema":
   - Extraia o assunto/pauta específica em 2 a 4 palavras no padrão Título (ex: 'Fim da Escala 6x1', 'Superlotação e Greve de Ônibus', 'Críticas à Gestão Elmano', 'Campanha André Fernandes', 'Segurança e Facções', 'Passe Livre Estudantil', 'Programa Pé-de-Meia', 'Atos da Juventude e Lula', 'Debates na Assembleia ALECE').
   - Seja conciso e use títulos consistentes para vídeos que tratam do mesmo assunto.

3. "resumo":
   - Resumo em até 10 palavras do tema do vídeo.

FORMATO DE RESPOSTA OBRIGATÓRIO (JSON ARRAY):
[
  {
    "id": <id_inteiro>,
    "campo": "oposicao" | "popular" | "neutro" | "ruido",
    "tema": "<Nome do Tema>",
    "resumo": "<Resumo curto>"
  }
]
"""

def classificar_lote_videos_gemini(lote_videos, gemini_key):
    """
    Envia um lote de vídeos cearenses para a API do Gemini.
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_GEMINI}:generateContent?key={gemini_key}"

    linhas_prompt = []
    mapa_ids = {}
    for idx, v in enumerate(lote_videos):
        vid_local = idx + 1
        mapa_ids[vid_local] = v
        titulo = v.get("titulo", "")
        canal = v.get("canal", "")
        desc = (v.get("desc") or "")[:120]
        linhas_prompt.append(f"[{vid_local}] Canal: {canal} | Título: \"{titulo}\" | Desc: \"{desc}\"")

    prompt_usuario = (
        "Classifique cada um dos vídeos cearenses abaixo segundo as instruções do sistema.\n\n"
        + "\n".join(linhas_prompt)
        + "\n\nResponda APENAS com o JSON array válido."
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT_VIDEOS_CE}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_usuario}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                cands = resp_json.get("candidates", [])
                if not cands:
                    return []
                txt = cands[0]["content"]["parts"][0]["text"].strip()
                analises = json.loads(txt)

                classificados = []
                for a in analises:
                    lid = a.get("id")
                    if lid in mapa_ids:
                        orig = mapa_ids[lid]
                        classificados.append({
                            "id": orig.get("id"),
                            "titulo": orig.get("titulo"),
                            "canal": orig.get("canal"),
                            "desc": orig.get("desc", ""),
                            "campo": a.get("campo", "neutro"),
                            "tema": a.get("tema", "Política Cearense").strip(),
                            "resumo": a.get("resumo", "").strip(),
                            "classificado_em": datetime.now().isoformat()
                        })
                return classificados
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3 * (tentativa + 1))
            else:
                break
        except Exception:
            time.sleep(2)

    return []

def _classificar_video_heuristico(v):
    """
    Classificador heurístico de fallback caso o Gemini esteja inacessível.
    """
    txt = (v.get("titulo", "") + " " + (v.get("desc") or "")).lower()

    # Campo Oposição
    if any(k in txt for k in ["andre fernandes", "andrefernandes"]):
        return "oposicao", "André Fernandes"
    if any(k in txt for k in ["capitao wagner", "wagner"]):
        return "oposicao", "Capitão Wagner"
    if any(k in txt for k in ["carmelo neto", "carmelo"]):
        return "oposicao", "Carmelo Neto"
    if any(k in txt for k in ["faccao", "faccoes", "crime", "chacina", "violencia"]):
        return "oposicao", "Segurança e Facções"
    if any(k in txt for k in ["rombo", "denuncia elmano", "saude em crise", "critica elmano"]):
        return "oposicao", "Críticas a Elmano"
    if any(k in txt for k in ["ipva", "tributo", "imposto", "taxa"]):
        return "oposicao", "IPVA e Tributos"
    if any(k in txt for k in ["direita", "bolsonaro", "pl ceara"]):
        return "oposicao", "Direita Fortaleza"

    # Campo Popular
    if any(k in txt for k in ["leo suricate", "leosuricate", "suricate"]):
        return "popular", "Léo Suricate"
    if any(k in txt for k in ["6x1", "escala 6x1"]):
        return "popular", "Fim da Escala 6x1"
    if any(k in txt for k in ["onibus", "terminal", "transporte", "siqueira", "messejana"]):
        return "popular", "Ônibus e Terminais"
    if any(k in txt for k in ["passe livre", "tarifa zero"]):
        return "popular", "Passe Livre"
    if any(k in txt for k in ["lula", "governo federal", "visita lula"]):
        return "popular", "Lula / Mobilização"
    if any(k in txt for k in ["elmano", "governo do ceara"]):
        return "popular", "Elmano de Freitas"
    if any(k in txt for k in ["camilo", "mec"]):
        return "popular", "Camilo Santana"
    if any(k in txt for k in ["pe-de-meia", "pe de meia"]):
        return "popular", "Programa Pé-de-Meia"
    if any(k in txt for k in ["areninha", "cuca", "juventude", "periferia"]):
        return "popular", "Areninhas e Juventude"

    return "neutro", "Política Cearense"

def classificar_videos_youtube_gemini(videos, gemini_key=None, cache_path=CACHE_VIDEOS_CLASSIFICADOS):
    """
    Classifica vídeos cearenses por campo político e tema dinâmico,
    mantendo cache incremental em dados/cache_videos_classificados.json.
    """
    if gemini_key is None:
        gemini_key = carregar_chaves_api().get("gemini", "")

    cache_map = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    if item.get("id"):
                        cache_map[item["id"]] = item
        except Exception:
            pass

    pendentes = [v for v in videos if v.get("id") and v["id"] not in cache_map]

    if pendentes:
        if gemini_key:
            tamanho_lote = 15
            for i in range(0, len(pendentes), tamanho_lote):
                sublote = pendentes[i:i + tamanho_lote]
                novos = classificar_lote_videos_gemini(sublote, gemini_key)
                for nv in novos:
                    cache_map[nv["id"]] = nv
                time.sleep(1)

        # Fallback heurístico para vídeos que ainda ficaram sem classificação
        for v in pendentes:
            if v["id"] not in cache_map:
                campo, tema = _classificar_video_heuristico(v)
                cache_map[v["id"]] = {
                    "id": v["id"],
                    "titulo": v.get("titulo", ""),
                    "canal": v.get("canal", ""),
                    "desc": v.get("desc", ""),
                    "campo": campo,
                    "tema": tema,
                    "resumo": "Análise contextual heurística",
                    "classificado_em": datetime.now().isoformat()
                }

        # Salva cache atualizado com expurgo de itens com mais de 7 dias
        cache_filtrado = [
            item for item in cache_map.values()
            if calcular_idade_horas(item.get("publishedAt") or item.get("classificado_em")) <= JANELA_MAXIMA_HORAS
        ]
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_filtrado, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {item["id"]: item for item in cache_filtrado}

    return cache_map

