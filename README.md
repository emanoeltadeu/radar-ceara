# 🎯 Radar Léo Suricate · Mandato Popular CE

> Painel de inteligência de dados eleitorais (voto de chão em Fortaleza e interior) e monitoramento ao vivo de redes sociais (YouTube, Google Trends e Meta Ads) com análise de sentimento via IA Generativa (**Gemini 3.5 Flash-Lite**).

---

## 🌟 Funcionalidades Principais

1. **Inteligência Territorial de Bairros (Chão vs Digital):**
   - Processamento de alta velocidade com **DuckDB** sobre os Boletins de Urna oficiais do TSE 2026.
   - Mapeamento detalhado dos **110 bairros de Fortaleza** e municípios do interior do Ceará.
   - Matriz estratégica automática: Bairros prioritários para *Mobilização de Chão (Plenárias e Ruas)* vs *Tráfego Pago (Reels/TikTok)*.

2. **Monitor de Redes Sociais em Tempo Real (Ceará Hoje):**
   - **Nuvem de Termos do Ceará:** Pesos dinâmicos por campo político baseados no corpus de vídeos cearenses da janela ativa.
   - **Mais Falados nos Vídeos:** Top 10 comparativo (*Pró-Oposição* vs *Campo Popular / Léo Suricate*) com janelas temporais de **12h, 24h e 48h**.
   - **Em Alta no Google Trends CE:** Consultas em alta no Ceará com janelas de **4h** e **24h**, ordenadas por volume real de pesquisas.

3. **Temperatura das Menções & Humor Popular (IA Generativa):**
   - Coleta de comentários reais via endpoint oficial `commentThreads.list` do YouTube Data API v3.
   - Classificação semântica com **`gemini-3.5-flash-lite`** com System Prompt calibrado para o vocabulário e a política cearense.
   - **Filtro de Descarte de Ruído:** Elimina automaticamente fofocas vazias, memes de figuras folclóricas (ex: Tiririca) e notícias de futebol.
   - **Descoberta Dinâmica de Pautas:** A IA extrai livremente os gatilhos e assuntos reais da conversa popular (sem categorias rígidas).
   - **Navegação Interativa com Link Direto:** Clique em qualquer tema para filtrar os comentários na 3ª coluna e abrir o link profundo do YouTube (`&lc=`) com o comentário destacado no topo.

4. **Transparência de Anúncios (Meta / Facebook / Instagram):**
   - Extração oficial dos gastos declarados com impulsionamento no Ceará via Prestação de Contas do TSE 2026 e Relatório da Meta Ad Library.

---

## 📁 Estrutura do Repositório

```text
├── .github/
│   └── workflows/
│       └── deploy-pages.yml         # Deploy contínuo no GitHub Pages
├── dados/
│   ├── canais_youtube_ce.txt        # 32 canais prioritários monitorados no Ceará
│   └── pautas_ceara.json            # Pautas estratégicas e munição de comunicação
├── scripts/
│   ├── analisador_sentimento_gemini.py # Coleta e classificação de sentimento com Gemini
│   ├── coletor_meta_ads.py          # Processamento de transparência de anúncios Meta/TSE
│   ├── coletor_trends_ce.py         # Coleta do Google Trends CE e corpus do YouTube
│   └── gerar_radar_ce.py            # Orquestrador do pipeline e gerador do radar_ce.json
├── site/
│   ├── index.html                   # Interface do painel de monitoramento
│   ├── style.css                    # Folha de estilos responsiva
│   ├── app.js                       # Lógica de renderização e interatividade
│   └── radar_ce.json                # JSON gerado pelo pipeline de dados
├── .env.example                     # Modelo de variáveis de ambiente
├── .gitignore                       # Proteção de credenciais e exclusão de dados >6GB
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
```

*Alternativamente, salve diretamente em:*
* `dados/gemini_api_key.txt`
* `dados/youtube_api_key.txt`

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
* **Dados Massivos:** Os arquivos brutos de votação do TSE somam mais de 6 GB e estão ignorados no Git para manter o repositório leve (menos de 2 MB).
* **Documentação das Funções:** Todas as funções Python possuem docstrings detalhadas explicando **"O que faz"** e **"Por que faz"**.
