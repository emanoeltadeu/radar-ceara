# 🎯 Radar Léo Suricate · Mandato Popular CE

> Painel de inteligência estratégica e monitoramento digital em tempo real das redes sociais no Ceará (YouTube, Instagram, Google Trends e Meta Ads) com análise de sentimento, Balanço de Disputa Narrativa e Radar Tático acionável via IA Generativa (**Google Gemini**).

---

## 🌟 Funcionalidades Principais

1. **Radar Tático IA (YouTube & Instagram):**
   - **Alerta Imediato / Urgência (1h):** Detecção precoce de crises emergentes, pautas em ascensão rápida e ataques coordenados na última hora.
   - **Diretriz Estratégica Consolidada (24h):** Síntese aprofundada das narrativas dominantes, pautas favorecidas e recomendações de comunicação e posicionamento tático formuladas pelo Gemini.

2. **Balanço de Disputa Narrativa (Saldo Líquido):**
   - Termômetro dinâmico por tema que agrupa comentários e calcula o **Saldo Líquido** (% Pró vs % Contra).
   - Classificação estratégica em 5 faixas:
     - 🟢 **Terreno Seguro** (+70% a +100%)
     - 🟢 **Favorecido** (+21% a +69%)
     - 🟡 **Em Disputa** (-20% a +20%)
     - 🔴 **Campo Minado** (-21% a -69%)
     - 🔴 **Crítica / Contenção** (-70% a -100%)
   - Ordenação dinâmica por **Volume de Menções** ou por **Criticidade / Crise** (menor saldo primeiro).

3. **Janelas Temporais Sincronizadas (1h, 2h, 12h, 24h e 7d):**
   - Controles independentes para **YouTube** e **Instagram** com alternância instantânea entre 5 horizontes de tempo.
   - Recálculo dinâmico do termômetro de humor popular, do balanço de disputa e da lista de comentários da janela selecionada.

4. **Auditoria de Comentários Reais com Deep Link:**
   - Lista interativa de comentários reais classificados por sentimento (*Positivo*, *Neutro*, *Crítica / Oposição*).
   - Filtro interativo: clique em qualquer pauta do balanço para auditar estritamente os comentários daquele tema.
   - **Link Direto:** Botão `Ver no YouTube ↗` com link profundo (`&lc=`) abrindo o comentário fixado no topo do vídeo, e `Ver no Instagram ↗` levando diretamente à publicação original.

5. **Em Alta no Google Trends (Ceará):**
   - Monitor de buscas com janelas de **4h** e **24h**, destacando termos relacionados ao campo popular, oposição ou pautas de disputa geral no estado.

6. **Transparência Meta Ads:**
   - Monitoramento de gastos declarados com impulsionamento de anúncios políticos no Ceará e distribuição percentual por município.

---

## 📡 Alvos Monitorados (YouTube & Instagram)

| Rede Social | Arquivo de Alvos | Total de Alvos Ativos | Volume na Base (7d) |
| :--- | :--- | :--- | :--- |
| **YouTube** | [`dados/canais_youtube_ce.txt`](dados/canais_youtube_ce.txt) | **32 canais cearenses** | **2.000+ comentários reais** |
| **Instagram (Perfis)** | [`dados/perfis_instagram.txt`](dados/perfis_instagram.txt) | **24 perfis prioritários (@)** | **Comentários de debate e seguidores** |
| **Instagram (Hashtags)** | [`dados/hashtags_instagram.txt`](dados/hashtags_instagram.txt) | **Hashtags de mobilização (#)** | **Debate popular e mobilização** |
| **Total Combinado** | — | **56+ alvos no Ceará** | **~3.700 comentários analisados** |

---

### ▶ Coleta no YouTube (YouTube Data API v3)
- **Imprensa & Notícias (14 canais):** *O POVO Online, Diário do Nordeste, GCMAIS / TV Cidade, Jornal Jangadeiro, TV Ceará, ALECE Notícias, Focus Poder, UrbNews, etc.*
- **Mandato & Campo Popular (7 canais):** *Léo Suricate / Suricate Seboso, Mídia NINJA, Elmano de Freitas, Governo do Ceará, Prefeitura de Fortaleza, Coletivo Cuca, Batalha do Cuca.*
- **Debate Político & Oposição (7 canais):** *André Fernandes, Capitão Wagner, Carmelo Neto, Rubão TV, Direita Já, etc.*
- **Cotidiano Urbano & Transporte (2 canais):** *Central do Ônibus Fortaleza, No Ponto Fortaleza.*

### 📸 Coleta no Instagram (Apify Cloud)
- **Perfis Monitorados:** `@leosuricate`, `@suricateseboso`, `@midianinja`, imprensa cearense (`@opovoonline`, `@diariodonordeste`, `@gcmais`), oposição (`@andrefernandes`, `@capitaowagnersousa`, `@carmeloneto`) e perfis de mobilização urbana.
- **Hashtags de Mobilização:** `#fimda6x1`, `#boralula`, `#eleicoes2026`, entre outras.
- **Estrutura:** Extração via atores Apify com rotação inteligente para otimização de custo e limite de chamadas.

---

## 🧠 Inteligência & Classificação com IA (Google Gemini)

1. Os comentários do YouTube e do Instagram são classificados semanticamente via `scripts/inteligencia/gemini.py`.
2. Para cada comentário, o modelo identifica:
   - **Sentimento:** Positivo (apoio), Crítica / Oposição (cobrança/ataque) ou Neutro.
   - **Pauta / Tema específico:** (ex.: *"Escala 6x1"*, *"Segurança Pública"*, *"Transporte / Tarifa Zero"*, *"Lula vs Bolsonaro"*, etc.).
   - **Resumo IA:** Síntese em uma frase da mensagem central do comentário.
3. O módulo `scripts/inteligencia/radar_tatico.py` sintetiza as métricas da última hora vs últimas 24h e gera o relatório tático executivo com recomendações de blindagem e contra-ataque.

---

## ⚡ Arquitetura de Dados & Payload Otimizado

O payload central [`site/radar_ce.json`](site/radar_ce.json) foi projetado para alta performance:
- **Redução de ~78% de peso (de ~12,6 MB para 2,8 MB)**.
- **Desduplicação Mestra:** Os comentários completos ficam armazenados apenas uma vez por rede (`sentimento_youtube.todos_comentarios` e `sentimento_instagram.todos_comentarios`).
- **Ponteiros de ID por Janela:** Cada uma das 5 janelas temporais (`1h`, `2h`, `12h`, `24h`, `7d`) armazena apenas métricas percentuais consolidadas e um array de IDs (`ids_comentarios`), resolvido instantaneamente em memória pelo frontend.

---

## 📁 Estrutura do Repositório

```text
├── .github/
│   └── workflows/
│       └── deploy-pages.yml         # Automação agendada diária no GitHub Actions
├── dados/
│   ├── canais_youtube_ce.txt        # 32 canais prioritários monitorados no Ceará
│   ├── perfis_instagram.txt         # 24 perfis do Instagram (@)
│   ├── hashtags_instagram.txt       # Hashtags prioritárias (#fimda6x1, etc.)
│   ├── cache_youtube.json           # Acervo persistente de vídeos políticos cearenses
│   ├── cache_comentarios.json       # Base bruta de comentários do YouTube
│   ├── cache_instagram.json         # Base bruta de comentários do Instagram
│   ├── cache_comentarios_classificados.json    # Comentários do YouTube classificados
│   └── cache_comentarios_classificados_ig.json # Comentários do Instagram classificados
├── scripts/
│   ├── config.py                    # Configurações de caminhos, fuso horário e chaves
│   ├── coletores/                   # Camada de Coleta (Extract)
│   │   ├── youtube.py               # Extração de vídeos e comentários na YouTube API v3
│   │   ├── instagram_apify.py       # Extração de perfis e hashtags via Apify
│   │   ├── google_trends.py         # Coleta e parsing do Google Trends CE (4h e 24h)
│   │   └── meta_ads.py              # Análise de gastos e distribuição Meta Ads
│   ├── inteligencia/                # Camada de IA & Análise (Transform)
│   │   ├── gemini.py                # Classificação de sentimento, temas e resumo
│   │   └── radar_tatico.py          # Geração do Radar Tático IA (1h urgente vs 24h)
│   ├── migrar_radar_ce.py           # Utilitário de migração e compactação do payload
│   └── gerar_radar_ce.py            # Orquestrador do pipeline de dados (Load)
├── site/
│   ├── index.html                   # Interface do painel de monitoramento (SPA)
│   ├── style.css                    # Folha de estilos responsiva
│   ├── app.js                       # Lógica de interação, filtros e janelas temporais
│   └── radar_ce.json                # Payload consolidado consumido pelo frontend
├── .env.example                     # Modelo de variáveis de ambiente
├── .gitignore                       # Proteção de credenciais e caches
├── requirements.txt                 # Dependências Python
└── README.md                        # Documentação do projeto
```

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório e ativar o ambiente virtual
```bash
git clone https://github.com/SEU_USUARIO/eleicoes.git
cd eleicoes

python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Chaves de API (para novas coletas)
Configure via arquivo `.env` ou salvando diretamente em `dados/`:
```bash
cp .env.example .env
# Preencha:
# GEMINI_API_KEY="sua_chave"
# YOUTUBE_API_KEY="sua_chave"
# APIFY_API_TOKEN="seu_token"
```

### 3. Gerar o Radar
```bash
python scripts/gerar_radar_ce.py
```

### 4. Visualizar o Painel
```bash
python -m http.server 8080 --directory site
```
Acesse no navegador: `http://localhost:8080`

---

## 🌐 Publicação Contínua (CI/CD)

- O projeto é servido como uma SPA estática via **Cloudflare Pages** conectada à branch `main`.
- O workflow [`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml) executa a rotina agendada ou manual via `workflow_dispatch`, atualizando `site/radar_ce.json` automaticamente no repositório.

---

## 🔒 Segurança

- **Credenciais Protegidas:** O `.gitignore` impede o versionamento de qualquer chave de API (`.env`, `*api_key.txt`, `*token.txt`).
- **Caches Locais Ignorados:** Bases pesadas de dados brutos são mantidas fora do versionamento Git para garantir deploy leve e ágil.
