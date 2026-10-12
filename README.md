# 🎯 Radar Léo Suricate · Mandato Popular CE

> Central de inteligência de guerra digital e monitoramento em tempo real das redes sociais no Ceará (YouTube, Instagram, Google Trends e Meta Ads) com análise de sentimento, Balanço de Disputa Narrativa e Radar Tático operacional acionável via IA Generativa (**Google Gemini**).

---

## 🌟 Funcionalidades Principais

1. **Panorama Geral das Redes (Hero Banner):**
   - Síntese executiva unificada no topo da página destacando o status de domínio em cada rede (*DOMINANDO*, *EQUILIBRADO* ou *SOB PRESSÃO*), a pauta principal em foco e a diretriz estratégica recomendada para o dia.

2. **Radar Tático IA (Ordens Operacionais Sem Clichês):**
   - **Alerta Imediato / Urgência (1h):** Detecção de calor recente e ataques da oposição. Em calmaria, libera a equipe para avanço ofensivo de pauta; em crise, aciona contenção imediata com contra-fatos.
   - **Diretriz Estratégica Consolidada (24h):** 
     - **Hook de 3 Segundos:** Gancho popular cearense pronto para o Léo falar na abertura do Reels/Shorts.
     - **Segmentação Territorial de Tráfego:** Recomendações de público e municípios/bairros de Fortaleza e RMF para impulsionamento no Meta Ads.
     - **Comando por Setor:** Tarefas tangíveis para roteiristas, editores e assessoria.
   - **📋 Exportação Direta para WhatsApp:** Botão que formata e envia o briefing tático completo direto para o WhatsApp da equipe e da militância de base com 1 clique.

3. **Cruzamento Estratégico com Google Trends Ceará:**
   - **Classificação Temática em 3 Vias:** Separação automática e precisa entre pautas de interesse público (`🏛️ Cívico`), futebol/esportes (`⚽ Esporte`) e cultura pop/feriados/datas comemorativas (`🎉 Cotidiano`), com botão de filtro rápido no painel.
   - **Selo de Validação Popular com Blindagem Anti-Alucinação:** Injeção do contexto real do Google Trends no prompt da IA, gerando o badge `🔥 Tração Validada nas Buscas do Google` no Hero Banner estritamente quando comprovada a correspondência com pesquisas reais capturadas no Ceará.
   - **Links Oficiais:** Cada termo possui link direto `↗` para a busca oficial correspondente no Google Trends.

4. **Balanço de Disputa Narrativa (Saldo Líquido):**
   - Termômetro dinâmico por tema que agrupa comentários e calcula o **Saldo Líquido** (% Pró vs % Contra).
   - Classificação estratégica em 5 faixas:
     - 🟢 **Terreno Seguro** (+70% a +100%)
     - 🟢 **Favorecido** (+21% a +69%)
     - 🟡 **Em Disputa** (-20% a +20%)
     - 🔴 **Campo Minado** (-21% a -69%)
     - 🔴 **Crítica / Contenção** (-70% a -100%)
   - Ordenação dinâmica por **Volume de Menções** ou por **Criticidade / Crise** (menor saldo primeiro).

5. **Janelas Temporais Sincronizadas (1h, 2h, 12h, 24h e 7d):**
   - Controles independentes para **YouTube** e **Instagram** com alternância instantânea entre 5 horizontes de tempo.
   - Recálculo dinâmico do termômetro de humor popular, do balanço de disputa e da lista de comentários da janela selecionada.

6. **Auditoria de Comentários Reais com Deep Link:**
   - Lista interativa de comentários reais classificados por sentimento (*Positivo*, *Neutro*, *Crítica / Oposição*).
   - Filtro interativo por tema e botão direto `Ver no YouTube ↗` (com link profundo `&lc=`) ou `Ver no Instagram ↗`.

7. **Modal de Fontes Monitoradas Transparente:**
   - Modal dinâmico no cabeçalho das redes exibindo a lista completa de perfis e canais monitorados com links externos `↗`, sem expor infraestrutura de coleta.

8. **Transparência Meta Ads:**
   - Monitoramento de gastos declarados com impulsionamento de anúncios políticos no Ceará e distribuição percentual por município.

---

## 📡 Alvos Monitorados (YouTube & Instagram)

| Rede Social | Arquivo de Alvos | Total de Alvos Ativos | Status da Coleta |
| :--- | :--- | :--- | :--- |
| **YouTube** | [`dados/canais_youtube_ce.txt`](dados/canais_youtube_ce.txt) | **28 canais cearenses** | **Ativo contínuo** (Vídeos recentes e comentários via YouTube Data API v3) |
| **Instagram (Perfis)** | [`dados/perfis_instagram.txt`](dados/perfis_instagram.txt) | **21 perfis prioritários (@)** | **Ativo em rotação FIFO** (8 perfis por ciclo, 5 posts mais recentes via Apify) |
| **Instagram (Hashtags)** | [`dados/hashtags_instagram.txt`](dados/hashtags_instagram.txt) | *17 hashtags mapeadas (#)* | **⏸️ Pausado temporariamente** (Economia de cota Apify; ativável sob demanda) |
| **Total Combinado** | — | **49 alvos monitorados no CE** | **Milhares de comentários processados e classificados** |

---

### ▶ Coleta no YouTube (YouTube Data API v3)
- **Imprensa & Notícias (12 canais):** *O POVO Online, Diário do Nordeste, GCMAIS / TV Cidade, Jornal Jangadeiro, TV Ceará, ALECE Notícias, Focus Poder, UrbNews, etc.*
- **Mandato & Campo Popular (6 canais):** *Léo Suricate / Suricate Seboso, Mídia NINJA, Elmano de Freitas, Governo do Ceará, Prefeitura de Fortaleza, Coletivo Cuca / Batalha do Cuca.*
- **Debate Político & Oposição (8 canais):** *André Fernandes, Capitão Wagner, Carmelo Neto, Rubão TV, Direita Já, etc.*
- **Cotidiano Urbano & Transporte (2 canais):** *Central do Ônibus Fortaleza, No Ponto Fortaleza.*

### 📸 Coleta no Instagram (Apify Cloud)
- **Perfis Monitorados (21 perfis):** Mandato popular e aliados (`@leosuricate`, `@suricateseboso`, `@midianinja`), imprensa cearense (`@opovoonline`, `@diariodonordeste`, `@gcmais`, `@portalgcm`, etc.), oposição (`@andrefernandes`, `@capitaowagnersousa`, `@carmeloneto`) e veículos de mobilização urbana/comunitária.
- **Estratégia de Cota e Rotação Circular (FIFO):**
  - Cada execução coleta em lote circular de 8 perfis (`batch_size=8`), extraindo os 5 posts mais recentes de cada um (`resultsLimit=5`).
  - O cursor de rotação é persistido em `dados/cursor_perfis_ig.json`, garantindo cobertura equitativa de todos os 21 perfis ao longo dos ciclos.
  - Memória do container Apify limitada a 1024 MB com timeout de 45s, garantindo custo previsível (~US\$ 0,08 por ciclo).
- **Hashtags de Mobilização:**
  - A varredura de hashtags via Apify está **temporariamente em pausa** para preservação de cota mensal da plataforma. O arquivo de alvos (`dados/hashtags_instagram.txt`) permanece pronto para reativação estratégica em períodos eleitorais ou mobilizações pontuais.

---

## 🧠 Inteligência & Classificação com IA (Google Gemini)

1. Os comentários do YouTube e do Instagram são classificados semanticamente via `scripts/inteligencia/gemini.py` com o modelo **Google Gemini**.
2. Para cada comentário, o modelo identifica:
   - **Sentimento:** Positivo (apoio), Crítica / Oposição (cobrança/ataque) ou Neutro.
   - **Pauta / Tema específico:** (ex.: *"Escala 6x1"*, *"Segurança Pública"*, *"Transporte / Tarifa Zero"*, *"Lula vs Bolsonaro"*, etc.).
   - **Resumo IA:** Síntese em uma frase da mensagem central do comentário.
3. O módulo `scripts/inteligencia/radar_tatico.py` cruza o calor das redes com as buscas reais do Google Trends Ceará e gera ordens operacionais sem jargões para comunicação rápida do mandato (hooks, segmentação de tráfego e comandos para a equipe).

---

## ⚡ Arquitetura de Dados & Payload Otimizado

O payload central [`site/radar_ce.json`](site/radar_ce.json) foi projetado para alta performance:
- **Redução de ~78% de peso (de ~12,6 MB para ~2,8 MB)**.
- **Desduplicação Mestra:** Os comentários completos ficam armazenados apenas uma vez por rede (`sentimento_youtube.todos_comentarios` e `sentimento_instagram.todos_comentarios`).
- **Ponteiros de ID por Janela:** Cada uma das 5 janelas temporais (`1h`, `2h`, `12h`, `24h`, `7d`) armazena apenas métricas percentuais consolidadas e um array de IDs (`ids_comentarios`), resolvido instantaneamente em memória pelo frontend.

---

## 📁 Estrutura do Repositório

```text
├── .github/
│   └── workflows/
│       ├── deploy-pages.yml         # Pipeline completo diário/manual no GitHub Actions
│       └── atualizar-trends.yml     # Micro-workflow rápido (a cada 4h) para o Google Trends
├── dados/
│   ├── canais_youtube_ce.txt        # 28 canais prioritários monitorados no Ceará
│   ├── perfis_instagram.txt         # 21 perfis do Instagram (@) em rotação circular
│   ├── hashtags_instagram.txt       # Hashtags mapeadas (pausadas temporariamente)
│   ├── cursor_perfis_ig.json        # Ponteiro persistente do lote circular de perfis
│   ├── cache_youtube.json           # Acervo persistente de vídeos políticos cearenses
│   ├── cache_comentarios.json       # Base bruta de comentários do YouTube
│   ├── cache_instagram.json         # Base bruta de comentários do Instagram
│   ├── cache_comentarios_classificados.json    # Comentários do YouTube classificados
│   └── cache_comentarios_classificados_ig.json # Comentários do Instagram classificados
├── scripts/
│   ├── config.py                    # Configurações de caminhos, fuso horário e chaves
│   ├── coletores/                   # Camada de Coleta (Extract)
│   │   ├── youtube.py               # Extração de vídeos e comentários na YouTube API v3
│   │   ├── instagram_apify.py       # Extração de perfis via Apify (rotação FIFO)
│   │   ├── google_trends.py         # Coleta e categorização do Google Trends CE (4h e 24h)
│   │   └── meta_ads.py              # Análise de gastos e distribuição Meta Ads
│   ├── inteligencia/                # Camada de IA & Análise (Transform)
│   │   ├── gemini.py                # Classificação de sentimento, temas e resumo
│   │   └── radar_tatico.py          # Radar Tático IA com cruzamento de Trends e ordens
│   ├── atualizar_trends_isolado.py  # Script de atualização rápida apenas do Google Trends
│   ├── migrar_radar_ce.py           # Utilitário de migração e compactação do payload
│   └── gerar_radar_ce.py            # Orquestrador do pipeline completo (Load)
├── site/
│   ├── index.html                   # Interface do painel de inteligência de guerra digital
│   ├── style.css                    # Folha de estilos moderna com tema escuro e responsiva
│   ├── app.js                       # Lógica de filtros, janelas temporais e modal de fontes
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
