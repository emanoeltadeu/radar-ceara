# 📦 Diretório de Códigos Legados (Arquivo Morto)

Este diretório contém módulos e utilitários que fizeram parte das etapas iniciais de construção e migração do **Radar Ceará**, mas que foram descontinuados e não fazem mais parte do pipeline de produção contínuo.

Os arquivos foram preservados aqui para histórico e referência de implementações anteriores.

---

## 📄 Arquivos Arquivados & Motivos

### 1. `dados_eleitorais.py`
- **O que fazia:** Processava boletins de urna oficiais do TSE (2026) via DuckDB para totalizar votos de chão por município e bairros de Fortaleza.
- **Motivo da inativação:** O escopo do projeto evoluiu para uma central de inteligência de guerra digital e monitoramento em tempo real das redes (YouTube, Instagram, Google Trends e Meta Ads). Os arquivos brutos de votação não estão versionados no Git nem alimentam a SPA estática em produção.

### 2. `nlp_nuvem.py`
- **O que fazia:** Processador de linguagem natural (NLP) baseado em expressões regulares, contagem de frequência de palavras e listas manuais de termos para gerar nuvem de termos e rankings de oposição.
- **Motivo da inativação:** Foi 100% substituído pela inteligência semântica com **Google Gemini** (`scripts/inteligencia/gemini.py` e `scripts/inteligencia/radar_tatico.py`), que compreende contexto cearense, sarcasmo e sentimento com acurácia superior e sem dependência de regras rígidas de regex.

### 3. `migrar_radar_ce.py`
- **O que fazia:** Script de migração one-off para desduplicar e compactar a estrutura antiga do payload `site/radar_ce.json` de ~12,6 MB para ~2,8 MB, adotando ponteiros de IDs por janela temporal.
- **Motivo da inativação:** A migração já foi concluída e o orquestrador oficial (`scripts/gerar_radar_ce.py`) já gera nativamente o JSON na estrutura otimizada.

### 4. `remover_alvos_oposicao.py`
- **O que fazia:** Utilitário pontual executado manualmente para expurgar comentários de figuras de oposição que haviam entrado em caches antigos.
- **Motivo da inativação:** A filtragem de relevância e alvos agora ocorre dinamicamente nas chamadas de extração e no system prompt do Gemini, tornando o expurgo estático desnecessário na rotina de CI/CD.
