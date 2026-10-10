#!/usr/bin/env python3
"""
Script pontual de migração e saneamento do radar_ce.json.
Remove chaves mortas, unifica campos e desduplica comentários entre janelas temporais.
"""
import json
import shutil
from pathlib import Path

ARQUIVO_RADAR = Path(__file__).resolve().parent.parent / "site" / "radar_ce.json"
ARQUIVO_BACKUP = ARQUIVO_RADAR.with_suffix(".json.bak")

def compactar_comentario(c, rede_padrao="youtube"):
    vid_id = c.get("video_id", "")
    c_id = c.get("id", "")
    link = (
        c.get("link_origem")
        or c.get("link_instagram")
        or c.get("link_youtube")
        or (f"https://www.youtube.com/watch?v={vid_id}&lc={c_id}" if vid_id and c_id else "")
    )
    origem_tit = c.get("origem_titulo") or c.get("video_titulo", "")
    return {
        "id": c_id,
        "rede": c.get("rede", rede_padrao),
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
    }

def limpar_sentimento(sent_obj, rede_padrao="youtube"):
    if not sent_obj:
        return {}
    todos = sent_obj.get("todos_comentarios") or sent_obj.get("comentarios_todos") or []
    compactos = [compactar_comentario(c, rede_padrao) for c in todos]
    amostras = sorted(compactos, key=lambda x: x.get("likes", 0), reverse=True)[:5]

    por_janela_limpo = {}
    orig_pj = sent_obj.get("por_janela", {})
    for j_nome, j_dados in orig_pj.items():
        j_comms = j_dados.get("todos_comentarios") or j_dados.get("comentarios_todos") or []
        ids = [c.get("id") for c in j_comms if c.get("id")]
        por_janela_limpo[j_nome] = {
            "disponivel": j_dados.get("disponivel", True),
            "janela": j_dados.get("janela", j_nome),
            "modelo": j_dados.get("modelo", ""),
            "hora": j_dados.get("hora", ""),
            "total_analisados": j_dados.get("total_analisados", len(ids)),
            "positivo_pct": j_dados.get("positivo_pct", 0.0),
            "neutro_pct": j_dados.get("neutro_pct", 0.0),
            "negativo_pct": j_dados.get("negativo_pct", 0.0),
            "ids_comentarios": ids
        }

    return {
        "disponivel": sent_obj.get("disponivel", True),
        "janela": sent_obj.get("janela", "7d"),
        "modelo": sent_obj.get("modelo", ""),
        "hora": sent_obj.get("hora", ""),
        "total_analisados": sent_obj.get("total_analisados", len(compactos)),
        "positivo_pct": sent_obj.get("positivo_pct", 0.0),
        "neutro_pct": sent_obj.get("neutro_pct", 0.0),
        "negativo_pct": sent_obj.get("negativo_pct", 0.0),
        "amostras_destaque": amostras,
        "todos_comentarios": compactos,
        "por_janela": por_janela_limpo
    }

def migrar():
    print(f"Lendo {ARQUIVO_RADAR}...")
    with open(ARQUIVO_RADAR, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Backup de segurança
    print(f"Criando backup em {ARQUIVO_BACKUP}...")
    shutil.copy2(ARQUIVO_RADAR, ARQUIVO_BACKUP)

    # 2. Limpeza do payload
    cleaned_monitor = {
        "google_trends_ce": data.get("monitor_redes", {}).get("google_trends_ce", {})
    }

    novo_payload = {
        "titulo": data.get("titulo", ""),
        "subtitulo": data.get("subtitulo", ""),
        "gerado_em": data.get("gerado_em", ""),
        "versao": data.get("versao", ""),
        "radar_tatico_youtube": data.get("radar_tatico_youtube", {}),
        "radar_tatico_instagram": data.get("radar_tatico_instagram", {}),
        "monitor_redes": cleaned_monitor,
        "sentimento_youtube": limpar_sentimento(data.get("sentimento_youtube", {}), "youtube"),
        "sentimento_instagram": limpar_sentimento(data.get("sentimento_instagram", {}), "instagram"),
        "meta_transparencia": data.get("meta_transparencia", {})
    }

    # 3. Gravação atômica
    temp_file = ARQUIVO_RADAR.with_suffix(".json.tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(novo_payload, f, ensure_ascii=False, indent=2)

    temp_file.replace(ARQUIVO_RADAR)

    tam_antes = ARQUIVO_BACKUP.stat().st_size
    tam_depois = ARQUIVO_RADAR.stat().st_size
    print(f"Sucesso!")
    print(f"Tamanho anterior: {tam_antes / 1024 / 1024:.2f} MB")
    print(f"Tamanho otimizado: {tam_depois / 1024 / 1024:.2f} MB")
    print(f"Economia de payload: {(1 - tam_depois / tam_antes) * 100:.1f}%")

if __name__ == "__main__":
    migrar()
