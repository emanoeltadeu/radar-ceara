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
    res_7d_janela = {k: v for k, v in res_7d.items() if k not in ("todos_comentarios", "amostras_destaque")}
    res_final["por_janela"] = {
        "1h": res_1h,
        "2h": res_2h,
        "12h": res_12h,
        "24h": res_24h,
        "7d": res_7d_janela
    }

    return res_final

def _calcular_metricas_sentimento(sub_validos, janela_label="7d", hora_ce=""):
    """
    Calcula as métricas proporcionais de sentimento para uma janela temporal.
    Armazena 'todos_comentarios' apenas na janela raiz ('7d') e 'ids_comentarios' nas janelas filhas.
    """
    if not hora_ce:
        hora_ce = datetime.now(FUSO_CE).strftime("%H:%M")

    if not sub_validos:
        res = {
            "disponivel": False,
            "janela": janela_label,
            "modelo": MODELO_GEMINI,
            "hora": hora_ce,
            "total_analisados": 0,
            "positivo_pct": 0.0,
            "neutro_pct": 0.0,
            "negativo_pct": 0.0,
            "ids_comentarios": []
        }
        if janela_label == "7d":
            res["amostras_destaque"] = []
            res["todos_comentarios"] = []
        return res

    total = len(sub_validos)
    pos_lista = [c for c in sub_validos if c.get("sentimento") == "positivo"]
    neu_lista = [c for c in sub_validos if c.get("sentimento") == "neutro"]
    neg_lista = [c for c in sub_validos if c.get("sentimento") == "negativo"]

    pos = len(pos_lista)
    neu = len(neu_lista)
    neg = len(neg_lista)

    ids_comentarios = [c.get("id", "") for c in sub_validos if c.get("id")]

    resultado = {
        "disponivel": True,
        "janela": janela_label,
        "modelo": MODELO_GEMINI,
        "hora": hora_ce,
        "total_analisados": total,
        "positivo_pct": round((pos / total) * 100, 1),
        "neutro_pct": round((neu / total) * 100, 1),
        "negativo_pct": round((neg / total) * 100, 1),
        "ids_comentarios": ids_comentarios
    }

    if janela_label == "7d":
        payload_comentarios = []
        for c in sub_validos:
            vid_id = c.get("video_id", "")
            c_id = c.get("id", "")
            link = (
                c.get("link_origem")
                or c.get("link_instagram")
                or c.get("link_youtube")
                or (f"https://www.youtube.com/watch?v={vid_id}&lc={c_id}" if vid_id and c_id else "")
            )
            origem_tit = c.get("origem_titulo") or c.get("video_titulo", "")

            payload_comentarios.append({
                "id": c_id,
                "rede": c.get("rede", "youtube"),
                "origem_titulo": origem_tit,
                "autor": c.get("autor", "Anônimo"),
                "texto": c.get("texto", ""),
                "likes": c.get("likes", 0),
                "data": c.get("data", ""),
                "sentimento": c.get("sentimento", "neutro"),
                "tipo": c.get("tipo", "neutro"),
                "tema": c.get("tema", ""),
                "resumo_ia": c.get("resumo_ia", ""),
                "origem_tipo": c.get("origem_tipo") or ("hashtag" if str(origem_tit).startswith("#") else "perfil"),
                "hashtag": c.get("hashtag") or (origem_tit.split()[0] if str(origem_tit).startswith("#") else ""),
                "link_origem": link
            })

        amostras = sorted(payload_comentarios, key=lambda x: x.get("likes", 0), reverse=True)[:5]
        resultado["amostras_destaque"] = amostras
        resultado["todos_comentarios"] = payload_comentarios

    return resultado

