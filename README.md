# 🎯 Radar Léo Suricate · Mandato Popular CE

> Painel de monitoramento digital em tempo real das redes sociais no Ceará (YouTube, Google Trends e Meta Ads) com análise de sentimento e descoberta de pautas via IA Generativa (**Gemini 3.5 Flash-Lite**).

---

## 🌟 Funcionalidades Principais

1. **Monitor de Redes Sociais em Tempo Real (Ceará Hoje):**
   - **Nuvem de Termos do Ceará:** Pesos dinâmicos por campo político baseados no corpus de vídeos cearenses da janela ativa.
   - **Mais Falados nos Vídeos:** Top 10 comparativo (*Pró-Oposição* vs *Campo Popular / Léo Suricate*) com janelas temporais de **12h, 24h e 48h**.
   - **Em Alta no Google Trends CE:** Consultas em alta no Ceará com janelas de **4h** e **24h**, ordenadas por volume real de pesquisas.

2. **Temperatura das Menções & Humor Popular · YouTube (IA Generativa):**
   - Coleta de comentários reais via endpoint oficial `commentThreads.list` do YouTube Data API v3 nos 32 canais cearenses monitorados.
   - Classificação semântica com **`gemini-3.5-flash-lite`** com System Prompt calibrado para o contexto cearense.
   - **Navegação com Link Direto:** Botão `Ver no YouTube ↗` com link profundo (`&lc=`) abrindo o comentário destacado no topo do vídeo.

3. **Temperatura das Menções & Humor Popular · Instagram (Apify & IA):**
   - Coleta de posts e comentários reais via **Apify** dos 24 perfis prioritários (@leosuricate, imprensa e lideranças) e da hashtag `#fimda6x1`.
   - Classificação paralela de sentimento e pautas trabalhistas/populares via Gemini.
   - **Navegação com Link Direto:** Botão `Ver no Instagram ↗` levando diretamente à publicação no Instagram.

4. **Transparência de Anúncios (Meta / Facebook / Instagram):**
   - Monitoramento de gastos declarados com impulsionamento de anúncios no Ceará e distribuição por município.

---

## 📡 Como Funciona a Coleta e Leitura de Dados (YouTube & Instagram)

### 📊 Panorama dos Alvos Monitorados

| Rede Social | Arquivo de Alvos | Total de Alvos Ativos | Volume Atual em Base |
| :--- | :--- | :--- | :--- |
| **YouTube** | [`dados/canais_youtube_ce.txt`](dados/canais_youtube_ce.txt) | **32 canais cearenses** | **122 vídeos** / **507 comentários reais** |
| **Instagram (Perfis)** | [`dados/perfis_instagram.txt`](dados/perfis_instagram.txt) | **24 perfis (@)** | **46 comentários reais** de posts |
| **Instagram (Hashtags)** | [`dados/hashtags_instagram.txt`](dados/hashtags_instagram.txt) | **1 hashtag (#)** (`#fimda6x1`) | **Comentários de debate popular** |
| **Total Combinado** | — | **57 alvos no Ceará** | **550+ comentários reais** |

---

### ▶ Coleta no YouTube (YouTube Data API v3)

#### **1. Os 32 Canais Mapeados (`dados/canais_youtube_ce.txt`):**
- **Imprensa & Notícias (14 canais):** *O POVO Online, Rádio O POVO CBN, Diário do Nordeste, GCMAIS / TV Cidade, Jornal Jangadeiro, TV Ceará, ALECE Notícias, Focus Poder, UrbNews, Ceará Acontece, Radar do Ceará, etc.*
- **Mandato & Campo Popular (7 canais):** *Léo Suricate / Suricate Seboso, Mídia NINJA, Elmano de Freitas, Governo do Ceará, Prefeitura de Fortaleza, Coletivo Cuca, Batalha do Cuca.*
- **Debate Político & Oposição (7 canais):** *André Fernandes, Capitão Wagner, Carmelo Neto, Rubão TV, Direita Já, etc.*
- **Cotidiano Urbano & Transporte (2 canais):** *Central do Ônibus Fortaleza, No Ponto Fortaleza.*

#### **2. Fluxo de Execução (`scripts/coletores/youtube.py`):**
1. **Busca de Vídeos (`search.list`):** Cruza os canais cearenses com termos de interesse político (*"Léo Suricate", "Ceará política", "Fortaleza política", "escala 6x1 Fortaleza", "ônibus Fortaleza"*), descartando automaticamente conteúdos irrelevantes (futebol, fofoca).
2. **Extração de Comentários (`commentThreads.list`):** Nos vídeos mais recentes, captura até 10 comentários mais curtidos/relevantes de cada vídeo.
3. **Deep Link:** Gera a URL profunda `https://www.youtube.com/watch?v={id}&lc={commentId}`, abrindo o vídeo com o comentário destacado no topo.
4. **Cache Persistente:** Salva incrementalmente em `dados/cache_youtube.json` e `dados/cache_comentarios.json`.

---

### 📸 Coleta no Instagram (Apify Cloud)

#### **1. Os 24 Perfis Mapeados (`dados/perfis_instagram.txt`):**
- **Mandato & Base:** `@leosuricate`, `@suricateseboso`, `@elmanodefreitas`, `@camilosantanaoficial`, `@governodoceara`, `@prefeituradefortaleza`, `@rede_cuca`, `@midianinja`.
- **Imprensa Cearense:** `@opovoonline`, `@opovocbn`, `@diariodonordeste`, `@gcmais`, `@jornaljangadeiro`, `@tvceara`, `@assembleiace`, `@focuspoder`, `@urbnews`, `@radardoceara`, `@cearanoticias`.
- **Oposição:** `@andrefernandes`, `@capitaowagnersousa`, `@carmeloneto`.
- **Cotidiano & Transporte:** `@etufortaleza`, `@centraldoonibusfortaleza`.

#### **2. A Hashtag Ativa (`dados/hashtags_instagram.txt`):**
- **`#fimda6x1`**: Pauta prioritária de mobilização popular e direitos trabalhistas.

#### **3. Fluxo de Execução (`scripts/coletores/instagram_apify.py`):**
1. **Perfis (`apify/instagram-scraper`):** Extrai os posts mais recentes dos perfis prioritários (garantindo `@leosuricate` em primeiro lugar) com os comentários reais de seguidores.
2. **Hashtags (`apify/instagram-hashtag-scraper`):** Ator dedicado que extrai postagens recentes marcadas com `#fimda6x1` e busca os comentários de debate entre trabalhadores e defensores da pauta.
3. **Deep Link:** Gera links diretos para cada postagem (`https://www.instagram.com/p/{shortCode}/`).
4. **Cache Persistente:** Unifica perfis e hashtags em `dados/cache_instagram.json`.

---

### 🧠 Inteligência & Classificação com IA (Google Gemini)

1. Os comentários do YouTube e do Instagram são processados em pipelines paralelos e independentes via `scripts/inteligencia/gemini.py`.
2. Para cada comentário, o modelo:
   - Identifica o sentimento: **Positivo** (apoio ao mandato/Lula/pauta), **Crítica** (oposição/cobrança de serviços) ou **Neutro**.
   - Identifica o **tema específico** (ex.: *"Fim da Escala 6x1"*, *"Disputa Lula vs Bolsonaro"*, *"Reeleição de Lula"*).
3. Alimenta os dois painéis independentes no dashboard com barras percentuais e filtros clicáveis em tempo real.

---

## 📁 Estrutura do Repositório

```text
├── .github/
│   └── workflows/
│       └── deploy-pages.yml         # Automação agendada nos 8 horários do Ceará
├── dados/
│   ├── canais_youtube_ce.txt        # 32 canais prioritários monitorados no Ceará
│   ├── perfis_instagram.txt         # 24 perfis do Instagram (@)
│   ├── hashtags_instagram.txt       # Hashtags prioritárias (#fimda6x1)
│   ├── cache_youtube.json           # Acervo persistente de vídeos políticos cearenses
│   ├── cache_comentarios.json       # Base de comentários do YouTube
│   ├── cache_instagram.json         # Base de comentários do Instagram
│   ├── cache_comentarios_classificados.json    # Comentários do YouTube classificados
│   ├── cache_comentarios_classificados_ig.json # Comentários do Instagram classificados
│   └── pautas_ceara.json            # Pautas estratégicas e munição de comunicação
├── scripts/
│   ├── config.py                    # Central de caminhos, fuso de Fortaleza e chaves
│   ├── coletores/                   # CAMADA EXTRACT (Coleta pura de dados brutos)
│   │   ├── youtube.py               # Busca de vídeos e comentários na YouTube API v3
│   │   ├── instagram_apify.py       # Extração de perfis e hashtags no Apify
│   │   ├── google_trends.py         # Coleta e parsing do Google Trends CE (4h e 24h)
│   │   └── meta_ads.py              # Processamento de prestação de contas TSE / Meta
│   ├── inteligencia/                # CAMADA TRANSFORM (Processamento, NLP e IA)
│   │   ├── gemini.py                # IA Generativa: Análise de sentimento e temas
│   │   ├── nlp_nuvem.py             # Limpeza, stopwords e ponderação da nuvem/vídeos
│   │   └── dados_eleitorais.py      # Extração DuckDB de votos do Léo por bairro (TSE 2026)
│   └── gerar_radar_ce.py            # CAMADA LOAD (Orquestrador concorrente em paralelo)
├── site/
│   ├── index.html                   # Interface do painel de monitoramento
│   ├── style.css                    # Folha de estilos responsiva
│   ├── app.js                       # Lógica de renderização e interatividade
│   └── radar_ce.json                # JSON gerado pelo pipeline de dados
├── .env.example                     # Modelo de variáveis de ambiente
├── .gitignore                       # Proteção de credenciais e exclusão de arquivos pesados
├── requirements.txt                 # Dependências Python
└── README.md                        # Documentação do projeto
```

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório e criar o ambiente virtual
```bash
git clone https://github.com/seu-usuario/eleicoes.git
cd eleicoes

python3 -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar as Chaves de API (Opcional para novos ciclos)
Você pode configurar as chaves via variáveis de ambiente ou arquivos na pasta `dados/`:

```bash
cp .env.example .env
# Edite o arquivo .env com suas chaves:
# GEMINI_API_KEY="sua_chave"
# YOUTUBE_API_KEY="sua_chave"
# APIFY_API_TOKEN="seu_token_apify"
```

*Alternativamente, salve diretamente em:*
* `dados/gemini_api_key.txt`
* `dados/youtube_api_key.txt`
* `dados/apify_token.txt`

### 3. Gerar os dados atualizados do Radar
```bash
python scripts/gerar_radar_ce.py
```
O comando atualizará o arquivo `site/radar_ce.json` com os dados mais recentes.

### 4. Visualizar o Painel no Navegador
Como o site é uma SPA estática:
```bash
python -m http.server 8080 --directory site
```
Acesse no seu navegador: `http://localhost:8080`

---

## 🌐 Publicação Gratuita no GitHub Pages

Este repositório já vem com o workflow do **GitHub Actions** configurado para publicação automática:

1. Suba o código para o seu repositório no GitHub:
   ```bash
   git add .
   git commit -m "feat: radar leo suricate com monitoramento de redes e IA gemini"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git
   git push -u origin main
   ```
2. No repositório do GitHub, vá em **Settings** > **Pages**.
3. Em **Build and deployment** > **Source**, selecione: **`GitHub Actions`**.
4. Em menos de 1 minuto, o site estará no ar na URL:  
   `https://SEU_USUARIO.github.io/NOME_DO_REPO/`

---

## 🔒 Segurança e Melhores Práticas

* **Credenciais Protegidas:** O arquivo `.gitignore` bloqueia qualquer arquivo de chave (`*api_key.txt`, `.env`) de ser enviado ao GitHub.
* **Repositório Leve:** Arquivos pesados locais e caches são ignorados no Git para manter o repositório leve (menos de 1,5 MB).
* **Documentação das Funções:** Todas as funções Python possuem docstrings detalhadas explicando **"O que faz"** e **"Por que faz"**.
