"""
Módulo Central de Configurações, Fuso Horário e Credenciais do Radar Ceará.

O que faz:
    Centraliza a definição de caminhos absolutos, timezone oficial do Ceará (UTC-3)
    e o carregamento seguro de chaves de API (lidas do ambiente do GitHub Actions
    ou de arquivos locais em dados/).
"""

import os
from datetime import datetime, timezone, timedelta

# Fuso horário oficial do Estado do Ceará (UTC-3)
FUSO_CE = timezone(timedelta(hours=-3))

# Diretórios base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS_DIR = os.path.join(BASE_DIR, "dados")
SITE_DIR = os.path.join(BASE_DIR, "site")

# Arquivos de dados e caches
CACHE_YOUTUBE = os.path.join(DADOS_DIR, "cache_youtube.json")
CACHE_COMENTARIOS = os.path.join(DADOS_DIR, "cache_comentarios.json")
CACHE_CLASSIFICADOS = os.path.join(DADOS_DIR, "cache_comentarios_classificados.json")
PAUTAS_CEARA = os.path.join(DADOS_DIR, "pautas_ceara.json")
CANAIS_YOUTUBE = os.path.join(DADOS_DIR, "canais_youtube_ce.txt")
SAIDA_RADAR_JSON = os.path.join(SITE_DIR, "radar_ce.json")

# Versão da aplicação
VERSAO_RADAR = "2.1.0-leo-suricate"

# Modelo de IA Generativa padrão
MODELO_GEMINI = "gemini-3.5-flash-lite"

def carregar_chaves_api():
    """
    O que faz:
        Recupera as chaves de API do Google Gemini e YouTube Data API v3.
        Prioriza variáveis de ambiente (injetadas em CI/CD pelo GitHub Secrets).
        Caso não encontre, recorre aos arquivos de texto locais em dados/.

    Retorno:
        dict: Dicionário contendo as chaves 'gemini' e 'youtube'.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    yt_key = os.getenv("YOUTUBE_API_KEY", "").strip()

    gemini_file = os.path.join(DADOS_DIR, "gemini_api_key.txt")
    yt_file = os.path.join(DADOS_DIR, "youtube_api_key.txt")

    if not gemini_key and os.path.exists(gemini_file):
        try:
            with open(gemini_file, "r", encoding="utf-8") as f:
                gemini_key = f.read().strip()
        except Exception:
            pass

    if not yt_key and os.path.exists(yt_file):
        try:
            with open(yt_file, "r", encoding="utf-8") as f:
                yt_key = f.read().strip()
        except Exception:
            pass

    return {
        "gemini": gemini_key,
        "youtube": yt_key
    }

def obter_hora_ce_formatada(formato="%H:%M"):
    """
    O que faz:
        Retorna a hora atual cravada no fuso de Fortaleza (UTC-3).
    """
    return datetime.now(FUSO_CE).strftime(formato)
