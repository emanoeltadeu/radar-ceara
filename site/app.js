document.addEventListener("DOMContentLoaded", () => {
  let DADOS = null;
  let SENTIMENTO_YOUTUBE = null;
  let SENTIMENTO_INSTAGRAM = null;

  // 1. Carregar radar_ce.json (com timestamp dinâmico para anular cache de CDN)
  fetch(`radar_ce.json?t=${Date.now()}`, { cache: "no-store" })
    .then(r => {
      if (!r.ok) throw new Error("Erro na rede");
      return r.json();
    })
    .then(data => {
      DADOS = data;
      SENTIMENTO_YOUTUBE = data.sentimento_youtube || data.sentimento_mencoes;
      SENTIMENTO_INSTAGRAM = data.sentimento_instagram;

      // 0. Hero Banner (Panorama Geral das Redes)
      renderizarPanoramaGeral(data);

      // Hub YouTube (janelas temporais 1h, 2h, 12h, 24h, 7d)
      if (SENTIMENTO_YOUTUBE) {
        inicializarHubYouTube(SENTIMENTO_YOUTUBE);
      }

      // Hub Instagram (janelas temporais 1h, 2h, 12h, 24h, 7d)
      if (SENTIMENTO_INSTAGRAM) {
        inicializarHubInstagram(SENTIMENTO_INSTAGRAM);
      }

      // Monitor de Redes (Google Trends Ceará)
      renderizarMonitorRedes(data.monitor_redes);

      // Radar Tático IA (YouTube & Instagram)
      if (data.radar_tatico_youtube) {
        renderizarRadarTatico(data.radar_tatico_youtube, "yt");
      }
      if (data.radar_tatico_instagram) {
        renderizarRadarTatico(data.radar_tatico_instagram, "ig");
      }

      renderizarMetaAds(data.meta_transparencia);
      const elHora = document.getElementById("hora-atualizacao");
      if (elHora) elHora.textContent = data.gerado_em || "Atualizado";
    })
    .catch(err => {
      console.error("Falha ao carregar radar_ce.json:", err);
    });

  // 1. RENDERIZADOR DO HERO BANNER (PANORAMA GERAL DAS REDES · CEARÁ HOJE)
  function renderizarPanoramaGeral(data) {
    if (!data) return;

    const elHora = document.getElementById("panorama-hora-atualizacao");
    if (elHora && data.gerado_em) {
      elHora.textContent = data.gerado_em;
    }

    // --- YOUTUBE ---
    const yt = data.radar_tatico_youtube || {};
    const badgeYT = document.getElementById("hero-badge-yt");
    const rotuloPautaYT = document.getElementById("hero-rotulo-pauta-yt");
    const pautaYT = document.getElementById("hero-pauta-yt");
    const diretrizYT = document.getElementById("hero-diretriz-yt");

    const statusYT = (yt.status_dominio || "ANALISANDO").toUpperCase();
    if (badgeYT) {
      badgeYT.textContent = statusYT;
      badgeYT.className = "badge-status-hero";
      if (statusYT === "DOMINANDO") badgeYT.classList.add("dominando");
      else if (statusYT === "SOB_PRESSAO" || statusYT === "SOB PRESSÃO") badgeYT.classList.add("sob-pressao");
      else badgeYT.classList.add("equilibrado");
    }

    const alertaYT = yt.alerta_imediato || {};
    const macroYT = yt.diretriz_estrategica_24h || {};

    let textoPautaYT = "";
    if (alertaYT.pauta && alertaYT.pauta !== "Nenhum Ataque Crítico Detectado") {
      textoPautaYT = alertaYT.pauta;
    } else if (macroYT.pautas_favoraveis && macroYT.pautas_favoraveis.length > 0) {
      textoPautaYT = macroYT.pautas_favoraveis[0];
    } else {
      textoPautaYT = "Consolidação de Pautas Populares & Mandato";
    }

    if (rotuloPautaYT) {
      rotuloPautaYT.textContent = statusYT === "DOMINANDO" ? "Pauta Positiva:" : "Pauta em Foco:";
    }
    if (pautaYT) {
      let extraBadgeYT = "";
      if (macroYT.validado_no_google_trends) {
        extraBadgeYT = ` <span class="badge-hero-trends-inline" title="Tração confirmada nas buscas do Ceará: '${escapeHtml(macroYT.termo_trends_relacionado || '')}'">🔥 Validada no Google Trends</span>`;
      }
      pautaYT.innerHTML = `${escapeHtml(textoPautaYT)}${extraBadgeYT}`;
    }
    if (diretrizYT) {
      diretrizYT.textContent = alertaYT.acao_recomendada || macroYT.orientacao_geral || "Manter monitoramento preventivo da base.";
    }

    // --- INSTAGRAM ---
    const ig = data.radar_tatico_instagram || {};
    const badgeIG = document.getElementById("hero-badge-ig");
    const rotuloPautaIG = document.getElementById("hero-rotulo-pauta-ig");
    const pautaIG = document.getElementById("hero-pauta-ig");
    const diretrizIG = document.getElementById("hero-diretriz-ig");

    const statusIG = (ig.status_dominio || "ANALISANDO").toUpperCase();
    if (badgeIG) {
      badgeIG.textContent = statusIG;
      badgeIG.className = "badge-status-hero";
      if (statusIG === "DOMINANDO") badgeIG.classList.add("dominando");
      else if (statusIG === "SOB_PRESSAO" || statusIG === "SOB PRESSÃO") badgeIG.classList.add("sob-pressao");
      else badgeIG.classList.add("equilibrado");
    }

    const alertaIG = ig.alerta_imediato || {};
    const macroIG = ig.diretriz_estrategica_24h || {};

    let textoPautaIG = "";
    if (alertaIG.pauta && alertaIG.pauta !== "Nenhum Ataque Crítico Detectado") {
      textoPautaIG = alertaIG.pauta;
    } else if (macroIG.pautas_favoraveis && macroIG.pautas_favoraveis.length > 0) {
      textoPautaIG = macroIG.pautas_favoraveis[0];
    } else {
      textoPautaIG = "Debate Popular & Mandato";
    }

    if (rotuloPautaIG) {
      rotuloPautaIG.textContent = "Pauta em Foco:";
    }
    if (pautaIG) {
      let extraBadgeIG = "";
      if (macroIG.validado_no_google_trends) {
        extraBadgeIG = ` <span class="badge-hero-trends-inline" title="Tração confirmada nas buscas do Ceará: '${escapeHtml(macroIG.termo_trends_relacionado || '')}'">🔥 Validada no Google Trends</span>`;
      }
      pautaIG.innerHTML = `${escapeHtml(textoPautaIG)}${extraBadgeIG}`;
    }
    if (diretrizIG) {
      diretrizIG.textContent = alertaIG.acao_recomendada || macroIG.orientacao_geral || "Acompanhar repercussão das publicações e debate.";
    }

    // --- LEGENDA DE AMOSTRA NOS CABEÇALHOS DO ACORDEÃO ---
    const amostraYT = document.getElementById("amostra-header-yt");
    if (amostraYT && data.sentimento_youtube) {
      const totYT = formatarNum(data.sentimento_youtube.total_analisados || 0);
      amostraYT.textContent = `${totYT} comentários`;
    }

    const amostraIG = document.getElementById("amostra-header-ig");
    if (amostraIG && data.sentimento_instagram) {
      const totIG = formatarNum(data.sentimento_instagram.total_analisados || 0);
      amostraIG.textContent = `${totIG} comentários`;
    }
  }

  // 2. HELPER PARA FILTRAGEM EFICIENTE DE COMENTÁRIOS POR JANELA
  function obterComentariosJanela(todosBase, sentJanela, janela) {
    if (!todosBase || !todosBase.length) return [];
    if (sentJanela && Array.isArray(sentJanela.ids_comentarios) && sentJanela.ids_comentarios.length > 0) {
      const idSet = new Set(sentJanela.ids_comentarios);
      return todosBase.filter(c => idSet.has(c.id));
    }
    if (sentJanela && Array.isArray(sentJanela.todos_comentarios) && sentJanela.todos_comentarios.length > 0) {
      return sentJanela.todos_comentarios;
    }
    if (sentJanela && Array.isArray(sentJanela.comentarios_todos) && sentJanela.comentarios_todos.length > 0) {
      return sentJanela.comentarios_todos;
    }
    if (janela === "7d") return todosBase;
    const horasMax = { "1h": 1.0, "2h": 2.0, "12h": 12.0, "24h": 24.0 }[janela] || 168.0;
    const agora = Date.now();
    return todosBase.filter(c => {
      if (!c.data) return false;
      const t = new Date(c.data).getTime();
      return !isNaN(t) && (agora - t) / 3600000 <= horasMax;
    });
  }

  // 3.A HUB DO YOUTUBE (JANELAS TEMPORAIS: 1h, 2h, 12h, 24h, 7d)
  function inicializarHubYouTube(dadosYouTube) {
    if (!dadosYouTube) return;

    let janelaAtualYT = "1h";

    function trocarJanelaYouTube(janela) {
      janelaAtualYT = janela;

      ["1h", "2h", "12h", "24h", "7d"].forEach(j => {
        const btn = document.getElementById(`btn-yt-${j}`);
        if (btn) {
          if (j === janela) btn.classList.add("on");
          else btn.classList.remove("on");
        }
      });

      const sentJanela = (dadosYouTube.por_janela && dadosYouTube.por_janela[janela]) || dadosYouTube;
      const todosBase = dadosYouTube.todos_comentarios || dadosYouTube.comentarios_todos || [];
      const comentariosJanela = obterComentariosJanela(todosBase, sentJanela, janela);
      const sentYTAtual = { ...sentJanela, todos_comentarios: comentariosJanela };

      renderizarBlocoSentimento(sentYTAtual, "yt", {
        tipoRede: "youtube",
        nomeRede: "YouTube",
        rotuloBtn: "Ver no YouTube ↗",
        clsLink: "link-yt-comentario",
        iconeOrigem: "📺",
        janela: janela
      });
    }

    ["1h", "2h", "12h", "24h", "7d"].forEach(j => {
      document.getElementById(`btn-yt-${j}`)?.addEventListener("click", () => {
        trocarJanelaYouTube(j);
      });
    });

    trocarJanelaYouTube("1h");
  }

  // 3.B MONITOR DE TENDÊNCIAS (Google Trends Ceará)
  function renderizarMonitorRedes(monitor) {
    if (!monitor) return;

    // Em Alta no Google (Ceará - 4h vs 24h & Filtro Cívico/Social)
    const listaGoogle = document.getElementById("lista-google-ce");
    const btnTrends4h = document.getElementById("btn-trends-4h");
    const btnTrends24h = document.getElementById("btn-trends-24h");
    const btnCatTodas = document.getElementById("btn-trends-cat-todas");
    const btnCatCivica = document.getElementById("btn-trends-cat-civica");

    let janelaTrendsAtual = "4h";
    let filtroCatAtual = "todas";

    function renderItensGoogle(itens) {
      if (!listaGoogle) return;
      
      const filtrados = (itens || []).filter(item => {
        if (filtroCatAtual === "civica") {
          return item.categoria === "politica_social";
        }
        return true;
      });

      if (filtrados.length === 0) {
        listaGoogle.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 20px; text-align: center; color: var(--tx-2); font-size: 13px;">
            Nenhuma busca de relevância cívico-social identificada nesta janela. As buscas estão concentradas em esportes e entretenimento.
          </div>
        `;
        return;
      }

      listaGoogle.innerHTML = filtrados.map(item => {
        const clsPonto = item.lado === "nossa" ? "nossa" : (item.lado === "deles" ? "deles" : "disputa");
        const isCivico = item.categoria === "politica_social";
        const badgeCatHtml = isCivico
          ? `<span class="badge-cat-trends civica" title="Pauta de relevância cívica, política ou de serviços públicos">🏛️ Cívico</span>`
          : `<span class="badge-cat-trends esporte" title="Busca relacionada a entretenimento, cultura pop ou esporte">⚽ Esporte</span>`;

        const urlBusca = `https://trends.google.com.br/trending?geo=BR-CE&q=${encodeURIComponent(item.termo)}`;

        return `
          <div class="item-google-ce ${isCivico ? 'item-civico-destaque' : ''}">
            <div class="item-google-topo">
              <span class="termo-com-ponto">
                <span class="ponto-busca ${clsPonto}"></span>
                <a href="${urlBusca}" target="_blank" rel="noopener noreferrer" class="link-termo-trends" title="Ver busca no Google Trends ↗">
                  ${escapeHtml(item.termo)}
                </a>
              </span>
              <div style="display:flex; align-items:center; gap:6px;">
                ${badgeCatHtml}
                <span class="volume-badge-verde">${escapeHtml(item.volume)}</span>
              </div>
            </div>
            <div class="item-google-pauta">
              <strong>Pauta:</strong> ${escapeHtml(item.pauta)}
            </div>
          </div>
        `;
      }).join("");
    }

    if (monitor.google_trends_ce) {
      const gt = monitor.google_trends_ce;
      
      // Atualiza o badge de auditoria temporal
      const badgeAuditoria = document.getElementById("trends-auditoria-badge");
      if (badgeAuditoria) {
        const hora = gt.atualizado_em ? (gt.atualizado_em.split("às")[1]?.trim() || gt.atualizado_em) : "recente";
        const freq = gt.frequencia_atualizacao || "A cada 4h";
        badgeAuditoria.textContent = `Atualizado às ${hora} • Renovação ${freq.toLowerCase()}`;
      }

      function atualizarLista() {
        const baseItens = (janelaTrendsAtual === "4h")
          ? (gt.itens_4h && gt.itens_4h.length > 0 ? gt.itens_4h : gt.itens)
          : (gt.itens_24h && gt.itens_24h.length > 0 ? gt.itens_24h : gt.itens);
        renderItensGoogle(baseItens);
      }

      atualizarLista();

      btnTrends4h?.addEventListener("click", () => {
        janelaTrendsAtual = "4h";
        btnTrends4h.classList.add("on");
        btnTrends24h?.classList.remove("on");
        atualizarLista();
      });

      btnTrends24h?.addEventListener("click", () => {
        janelaTrendsAtual = "24h";
        btnTrends24h.classList.add("on");
        btnTrends4h?.classList.remove("on");
        atualizarLista();
      });

      btnCatTodas?.addEventListener("click", () => {
        filtroCatAtual = "todas";
        btnCatTodas.classList.add("on");
        btnCatCivica?.classList.remove("on");
        atualizarLista();
      });

      btnCatCivica?.addEventListener("click", () => {
        filtroCatAtual = "civica";
        btnCatCivica.classList.add("on");
        btnCatTodas?.classList.remove("on");
        atualizarLista();
      });
    }
  }

  // 3.1. RENDERIZADOR MODULAR DE SENTIMENTO & HUMOR POPULAR (GEMINI)
  function renderizarBlocoSentimento(sent, prefix, config = {}) {
    if (!sent) return;

    const tipoRede = config.tipoRede || "youtube";
    const rotuloBtn = config.rotuloBtn || (tipoRede === "instagram" ? "Ver no Instagram ↗" : "Ver no YouTube ↗");
    const clsLink = config.clsLink || (tipoRede === "instagram" ? "link-ig-comentario" : "link-yt-comentario");
    const iconeOrigem = config.iconeOrigem || (tipoRede === "instagram" ? "📸" : "📺");

    const totalLabel = document.getElementById(`sentimento-${prefix}-total-label`);
    if (totalLabel && sent.total_analisados !== undefined) {
      const rotuloJanela = config.janela ? ` (${config.janela})` : '';
      totalLabel.textContent = `${sent.total_analisados} comentários analisados${rotuloJanela}`;
    }

    const pos = sent.positivo_pct || 0;
    const neu = sent.neutro_pct || 0;
    const neg = sent.negativo_pct || 0;

    const barPos = document.getElementById(`barra-sent-${prefix}-pos`);
    const barNeu = document.getElementById(`barra-sent-${prefix}-neu`);
    const barNeg = document.getElementById(`barra-sent-${prefix}-neg`);

    const rotPos = document.getElementById(`rotulo-sent-${prefix}-pos`);
    const rotNeu = document.getElementById(`rotulo-sent-${prefix}-neu`);
    const rotNeg = document.getElementById(`rotulo-sent-${prefix}-neg`);

    if (barPos) {
      barPos.style.width = `${pos}%`;
      if (rotPos) rotPos.textContent = `${pos.toFixed(1).replace(".", ",")}% Positivo`;
    }
    if (barNeu) {
      barNeu.style.width = `${neu}%`;
      if (rotNeu) rotNeu.textContent = `${neu.toFixed(1).replace(".", ",")}% Neutro`;
    }
    if (barNeg) {
      barNeg.style.width = `${neg}%`;
      if (rotNeg) rotNeg.textContent = `${neg.toFixed(1).replace(".", ",")}% Crítica / Oposição`;
    }


    let temaAtivo = null;
    const todosComentarios = sent.comentarios_todos || sent.todos_comentarios || sent.amostras_destaque || [];
    const titCol = document.getElementById(`tit-col-comentarios-${prefix}`);
    const badgeCol = document.getElementById(`badge-filtro-comentarios-${prefix}`);
    const listaAmostras = document.getElementById(`lista-amostras-comentarios-${prefix}`);

    function renderComentarios(lista, temaFiltro = null) {
      if (!listaAmostras) return;

      if (titCol) {
        titCol.textContent = temaFiltro ? `Comentários: "${temaFiltro}"` : "Comentários Reais em Destaque";
      }

      if (badgeCol) {
        if (temaFiltro) {
          badgeCol.innerHTML = `${lista.length} ${lista.length === 1 ? 'comentário' : 'comentários'} <button id="btn-limpar-filtro-${prefix}" class="btn-limpar-filtro" title="Limpar filtro e ver amostras">✕ Ver todos</button>`;
          document.getElementById(`btn-limpar-filtro-${prefix}`)?.addEventListener("click", () => {
            filtrarPorTema(null, null);
          });
        } else {
          badgeCol.textContent = "Auditoria em tempo real";
        }
      }

      if (lista.length === 0) {
        listaAmostras.innerHTML = `<div class="item-amostra-vazio">Nenhum comentário específico encontrado para este tema no lote atual.</div>`;
        return;
      }

      listaAmostras.innerHTML = lista.map(a => {
        const clsTag = a.sentimento === "positivo" ? "positivo" : (a.sentimento === "negativo" ? "negativo" : "neutro");

        // Destino inteligente para link
        let urlDestino = a.link_origem || a.link_instagram || a.link_yt || a.link_youtube;
        if (!urlDestino) {
          if (a.rede === "instagram" && a.post_url) {
            urlDestino = a.post_url;
          } else if (a.video_id && a.id) {
            urlDestino = `https://www.youtube.com/watch?v=${encodeURIComponent(a.video_id)}&lc=${encodeURIComponent(a.id)}`;
          }
        }

        const linkBotao = urlDestino ? `<a href="${escapeHtml(urlDestino)}" target="_blank" rel="noopener noreferrer" class="${clsLink}" title="Abrir publicação/comentário original">${escapeHtml(rotuloBtn)}</a>` : "";

        const tituloOrigem = a.origem_titulo || a.video_titulo || "";
        const htmlOrigem = tituloOrigem ? `<div class="amostra-video-origem" title="${escapeHtml(tituloOrigem)}">${iconeOrigem} ${escapeHtml(tituloOrigem)}</div>` : "";

        return `
          <div class="item-amostra-comentario">
            <div class="amostra-topo">
              <span class="amostra-autor">${escapeHtml(a.autor || "@anonimo")}</span>
              <span class="amostra-tag ${clsTag}">${escapeHtml(a.sentimento || "neutro")}</span>
            </div>
            ${htmlOrigem}
            <div class="amostra-texto">"${escapeHtml(a.texto || "")}"</div>
            ${linkBotao ? `<div class="amostra-rodape">${linkBotao}</div>` : ""}
          </div>
        `;
      }).join("");
    }

    function filtrarPorTema(tema, tipoLado) {
      const containerGeral = document.getElementById(`painel-sentimento-${prefix}`);
      const itensClicaveis = containerGeral ? containerGeral.querySelectorAll(".item-tema-clicavel") : [];

      if (temaAtivo === tema || !tema) {
        temaAtivo = null;
        itensClicaveis.forEach(el => el.classList.remove("ativo-pos", "ativo-neg"));
        document.querySelectorAll(`#tabela-balanco-${prefix}-corpo .linha-pauta-balanco`).forEach(el => el.classList.remove("ativo"));
        renderComentarios(sent.amostras_destaque || todosComentarios.slice(0, 5), null);
        return;
      }

      temaAtivo = tema;
      itensClicaveis.forEach(el => {
        el.classList.remove("ativo-pos", "ativo-neg");
        if (el.getAttribute("data-tema") === tema) {
          el.classList.add(tipoLado === "pos" ? "ativo-pos" : "ativo-neg");
        }
      });

      const filtradosPorLado = todosComentarios.filter(c => {
        const cTema = (c.tema || "").toLowerCase().trim();
        const tBusca = tema.toLowerCase().trim();
        if (cTema !== tBusca) return false;
        if (tipoLado === "pos") return c.sentimento === "positivo" || c.tipo === "apoio";
        if (tipoLado === "neg") return c.sentimento === "negativo" || c.tipo === "ataque_oposicao" || c.tipo === "cobranca_popular" || c.tipo === "cobranca_servicos";
        return true;
      });

      const filtrados = filtradosPorLado.length > 0 ? filtradosPorLado : todosComentarios.filter(c => {
        const cTema = (c.tema || "").toLowerCase().trim();
        const tBusca = tema.toLowerCase().trim();
        return cTema === tBusca;
      });

      renderComentarios(filtrados, tema);

      // Scroll suave se estiver no mobile
      if (window.innerWidth <= 900) {
        listaAmostras?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }


    // =========================================================================
    // BALANÇO DE DISPUTA NARRATIVA (SALDO LÍQUIDO) - YOUTUBE
    // =========================================================================
    const tabelaBalancoCorpo = document.getElementById(`tabela-balanco-${prefix}-corpo`);
    const subBalancoEl = document.getElementById(`sub-balanco-${prefix}`);
    if (subBalancoEl && config.janela) {
      subBalancoEl.textContent = `Saldo líquido de menções nas últimas ${config.janela}`;
    }

    if (tabelaBalancoCorpo) {
      // 1. Agrupa comentários de todos os temas disponíveis
      const temasAgrupados = {};
      todosComentarios.forEach(c => {
        const t = (c.tema || "Geral").trim();
        const s = c.sentimento;
        if (!temasAgrupados[t]) {
          temasAgrupados[t] = { tema: t, positivo: 0, negativo: 0, neutro: 0, total: 0 };
        }
        if (s === "positivo") temasAgrupados[t].positivo++;
        else if (s === "negativo") temasAgrupados[t].negativo++;
        else if (s === "neutro") temasAgrupados[t].neutro++;
        temasAgrupados[t].total++;
      });

      // 2. Calcula Saldo Líquido e Percentuais Proporcionais
      const listaPautas = Object.values(temasAgrupados).map(item => {
        const somaPróContra = item.positivo + item.negativo;
        let saldo = 0;
        let posPct = 0;
        let negPct = 0;

        if (somaPróContra > 0) {
          saldo = Math.round(((item.positivo - item.negativo) / somaPróContra) * 100);
          posPct = Math.round((item.positivo / somaPróContra) * 100);
          negPct = Math.round((item.negativo / somaPróContra) * 100);
        } else if (item.total > 0) {
          posPct = 50;
          negPct = 50;
        }

        let statusClass = "disputa";
        let statusLabel = "EM DISPUTA";

        if (saldo > 20) {
          statusClass = "favorecido";
          statusLabel = saldo >= 70 ? "TERRENO SEGURO" : "FAVORECIDO";
        } else if (saldo < -20) {
          statusClass = "minado";
          statusLabel = saldo <= -70 ? "CRÍTICA / CONTENÇÃO" : "CAMPO MINADO";
        }

        return {
          ...item,
          somaPróContra,
          saldo,
          posPct,
          negPct,
          statusClass,
          statusLabel
        };
      });

      let modoOrdBalanco = 'volume';

      function renderLinhasBalanco() {
        let ordenadas = [...listaPautas];
        if (modoOrdBalanco === 'volume') {
          ordenadas.sort((a, b) => b.total - a.total);
        } else {
          // Criticidade: menor saldo primeiro (prioriza crises e campo minado)
          ordenadas.sort((a, b) => a.saldo - b.saldo);
        }

        // Filtra para mostrar pautas com relevância (mínimo de volume)
        const relevantes = ordenadas.filter(p => p.total >= 3);
        const exibidas = relevantes.length >= 4 ? relevantes : ordenadas.slice(0, 8);

        tabelaBalancoCorpo.innerHTML = exibidas.map(p => {
          const saldoCls = p.saldo > 20 ? 'pos' : (p.saldo < -20 ? 'neg' : 'neu');
          const sufixoSaldo = p.saldo > 20 ? 'Pró' : (p.saldo < -20 ? (p.tema.toLowerCase().includes('oposição') ? 'Contra' : 'Oposição') : 'Equilibrado');
          const saldoFormatado = `${p.saldo > 0 ? '+' : ''}${p.saldo}% ${sufixoSaldo}`;
          const estaAtivo = temaAtivo && temaAtivo.toLowerCase().trim() === p.tema.toLowerCase().trim();
          const ehCritico = p.saldo < -20;

          return `
            <div class="card-pauta-item ${ehCritico ? 'pauta-critica' : ''} ${estaAtivo ? 'ativo' : ''}" data-tema="${escapeHtml(p.tema)}" title="Clique para auditar comentários de '${escapeHtml(p.tema)}'">
              <div class="card-pauta-topo">
                <span class="card-pauta-titulo">${escapeHtml(p.tema)}</span>
                <div class="card-pauta-badges">
                  <span class="badge-vol-pauta">${p.total} menções</span>
                  <span class="badge-saldo-pauta ${saldoCls}">${saldoFormatado}</span>
                </div>
              </div>

              <div class="card-pauta-barra-wrap">
                <div class="barra-pauta-dupla">
                  <div style="width: ${p.posPct}%;" class="seg-pauta-verde" title="${p.positivo} comentários pró (${p.posPct}%)"></div>
                  <div style="width: ${p.negPct}%;" class="seg-pauta-vermelho" title="${p.negativo} comentários contra (${p.negPct}%)"></div>
                </div>
                <div class="card-pauta-labels">
                  <span class="lbl-verde">${p.posPct}%</span>
                  <span class="lbl-vermelho">${p.negPct}%</span>
                </div>
              </div>
            </div>
          `;
        }).join("");

        // Adiciona evento de clique nos cards para filtrar comentários reais
        tabelaBalancoCorpo.querySelectorAll(".card-pauta-item").forEach(card => {
          card.addEventListener("click", () => {
            const temaClicado = card.getAttribute("data-tema");
            tabelaBalancoCorpo.querySelectorAll(".card-pauta-item").forEach(el => el.classList.remove("ativo"));
            if (temaAtivo === temaClicado) {
              filtrarPorTema(null, null);
            } else {
              card.classList.add("ativo");
              filtrarPorTema(temaClicado, "balanco");
            }
          });
        });
      }

      // Configura os botões de ordenação do Balanço
      const btnVolYt = document.getElementById(`btn-ord-vol-${prefix}`);
      const btnSaldoYt = document.getElementById(`btn-ord-saldo-${prefix}`);

      btnVolYt?.addEventListener("click", () => {
        modoOrdBalanco = 'volume';
        btnVolYt.classList.add("on");
        btnSaldoYt?.classList.remove("on");
        renderLinhasBalanco();
      });

      btnSaldoYt?.addEventListener("click", () => {
        modoOrdBalanco = 'saldo';
        btnSaldoYt.classList.add("on");
        btnVolYt?.classList.remove("on");
        renderLinhasBalanco();
      });

      renderLinhasBalanco();
    }


    // Inicializa a 3ª coluna com as amostras gerais de destaque
    renderComentarios(sent.amostras_destaque || todosComentarios.slice(0, 5), null);
  }

  // =========================================================================
  // 3.A.2 RENDERIZADOR DO RADAR TÁTICO IA (BRIEFING EM DUAS CAMADAS: 1H & 24H)
  // =========================================================================
  function renderizarRadarTatico(tatico, prefix = "yt") {
    if (!tatico) return;

    const badgeStatus = document.getElementById(`badge-status-dominio-${prefix}`);
    const tempoEl = document.getElementById(`tempo-tatico-${prefix}`);
    const diag1hEl = document.getElementById(`diagnostico-urgente-1h-${prefix}`);
    const conteudoUrgenteEl = document.getElementById(`conteudo-alerta-urgente-${prefix}`);
    const conteudoMacroEl = document.getElementById(`conteudo-diretriz-macro-${prefix}`);
    const blocoUrgente = document.getElementById(`bloco-urgente-${prefix}`);
    const btnExportar = document.getElementById(`btn-exportar-tarefas-${prefix}`);

    // 1. Status de Domínio
    if (badgeStatus && tatico.status_dominio) {
      const st = tatico.status_dominio.toLowerCase();
      badgeStatus.className = `badge-status-tatico ${st}`;
      const labels = {
        dominando: "🟢 DOMINANDO O DEBATE",
        equilibrado: "🟡 DEBATE EQUILIBRADO",
        sob_pressao: "🔴 SOB PRESSÃO"
      };
      badgeStatus.textContent = labels[st] || tatico.status_dominio;
    }

    if (tempoEl && tatico.atualizado_em) {
      tempoEl.textContent = `Atualizado às ${tatico.atualizado_em}`;
    }

    // 2. Diagnóstico 1h
    if (diag1hEl && tatico.diagnostico_urgente_1h) {
      diag1hEl.textContent = tatico.diagnostico_urgente_1h;
    }

    // 3. Alerta Imediato / Crise
    if (conteudoUrgenteEl && tatico.alerta_imediato) {
      const alerta = tatico.alerta_imediato;
      const tagUrgente = document.getElementById(`tag-urgente-${prefix}`);
      if (blocoUrgente) {
        if (!alerta.existe_crise) {
          blocoUrgente.classList.add("calmo");
          if (tagUrgente) tagUrgente.textContent = "🟢 SEM CRISE IMEDIATA (ÚLTIMA 1H)";
        } else {
          blocoUrgente.classList.remove("calmo");
          if (tagUrgente) tagUrgente.textContent = "🚨 URGENTE (ÚLTIMA 1H)";
        }
      }

      const rotuloPauta = alerta.existe_crise ? "Pauta sob ataque:" : "Status da pauta:";
      const rotuloAcao = alerta.existe_crise ? "➔ Ação Imediata:" : "➔ Ação Recomendada:";

      conteudoUrgenteEl.innerHTML = `
        <p><strong>${rotuloPauta}</strong> <span style="font-weight:700;">${escapeHtml(alerta.pauta || "Nenhum Ataque Crítico Detectado")}</span> — ${escapeHtml(alerta.detalhe || "")}</p>
        <div class="tatico-acao-linha">
          <strong>${rotuloAcao}</strong>
          <span>${escapeHtml(alerta.acao_recomendada || "Manter monitoramento preventivo.")}</span>
        </div>
      `;
    }

    // 4. Diretriz Estratégica 24h
    if (conteudoMacroEl && tatico.diretriz_estrategica_24h) {
      const macro = tatico.diretriz_estrategica_24h;
      let extrasHtml = "";
      if (macro.gancho_conteudo) {
        extrasHtml += `
          <div class="tatico-acao-linha" style="margin-top:6px;">
            <strong>🎬 Gancho / Ângulo:</strong>
            <span>${escapeHtml(macro.gancho_conteudo)}</span>
          </div>
        `;
      }
      if (macro.segmentacao_trafego) {
        extrasHtml += `
          <div class="tatico-acao-linha" style="margin-top:6px;">
            <strong>🎯 Tráfego & Segmentação:</strong>
            <span>${escapeHtml(macro.segmentacao_trafego)}</span>
          </div>
        `;
      }

      let badgeTrendsHtml = "";
      if (macro.validado_no_google_trends) {
        const termoValidado = escapeHtml(macro.termo_trends_relacionado || "Pautas Populares em Alta");
        badgeTrendsHtml = `
          <div class="badge-trends-validado" title="Esta pauta corresponde ao interesse ativo de busca da população cearense no Google">
            🔥 <strong>Tração Validada nas Buscas do Google</strong> (Ceará: "${termoValidado}")
          </div>
        `;
      }

      conteudoMacroEl.innerHTML = `
        ${badgeTrendsHtml}
        <p><strong>Pauta:</strong> <span style="font-weight:700;">${escapeHtml(macro.oportunidade || "Pauta Popular")}</span> — ${escapeHtml(macro.detalhe || "")}</p>
        <div class="tatico-acao-linha">
          <strong>➔ Recomendação:</strong>
          <span>${escapeHtml(macro.recomendacao_acao || "")}</span>
        </div>
        ${extrasHtml}
      `;
    }

    // 5. Botão de Exportação de Tarefas para WhatsApp (Disparo Imediato via API)
    btnExportar?.addEventListener("click", () => {
      const alerta = tatico.alerta_imediato || {};
      const macro = tatico.diretriz_estrategica_24h || {};
      const hora = tatico.atualizado_em || (DADOS && DADOS.gerado_em ? DADOS.gerado_em.split("às")[1]?.trim() : "Agora");
      const nomeRede = prefix === "ig" ? "Instagram" : "YouTube";
      const statusDominio = (tatico.status_dominio || "ANALISADO").toUpperCase();

      // Bloco 1: Alerta Urgente (Condicional Sem Crise vs Com Crise)
      let blocoUrgenteZap = "";
      if (alerta.existe_crise) {
        blocoUrgenteZap = `----------------------------------------
🚨 *ALERTA URGENTE (Janela 1h)*
• *Pauta:* ${alerta.pauta || "Ataque Crítico Detectado"}
• *Contexto:* ${alerta.detalhe || tatico.diagnostico_urgente_1h || "Volume elevado de negatividade na última hora."}
👉 *Ação Imediata:* ${alerta.acao_recomendada || "Intervir com contenção imediata nos comentários."}
----------------------------------------`;
      } else {
        blocoUrgenteZap = `----------------------------------------
🚨 *ALERTA URGENTE (Janela 1h)*
• *Pauta:* Nenhum Ataque Crítico Detectado
• *Contexto:* ${alerta.detalhe || "Cenário estável na última hora sem novos ataques coordenados."}
👉 *Ação Imediata:* ${alerta.acao_recomendada || "Monitoramento preventivo ativo; foco total na produção da diretriz do dia."}
----------------------------------------`;
      }

      // Bloco 2: Equipe de Vídeo & Tráfego Pago
      let blocoVideoZap = "";
      if (macro.gancho_conteudo) {
        blocoVideoZap = `\n🎬 *EQUIPE DE VÍDEO (Gancho/Ângulo):*\n"${macro.gancho_conteudo}"\n`;
      }

      let blocoTrafegoZap = "";
      if (macro.segmentacao_trafego) {
        blocoTrafegoZap = `\n🎯 *GESTÃO DE TRÁFEGO:*\n• Público & Território: ${macro.segmentacao_trafego}\n`;
      }

      // Bloco Validação Google Trends (se houver correspondência)
      let linhaTrendsZap = "";
      if (macro.validado_no_google_trends && macro.termo_trends_relacionado) {
        linhaTrendsZap = `\n🔍 *Google Trends CE:* Em alta com o termo "${macro.termo_trends_relacionado}"`;
      }

      const textoZap = `⚡ *RADAR TÁTICO MANDATO LÉO SURICATE*
📅 *Atualizado às:* ${hora} | *Rede:* ${nomeRede}
🎯 *Status:* *${statusDominio}*

${blocoUrgenteZap}

🟢 *DIRETRIZ DO DIA (Janela 24h)*
• *Pauta com Tração:* ${macro.oportunidade || "Pauta Popular & Mandato"}
• *Métrica/Respaldo:* ${macro.detalhe || "Alto saldo líquido favorável consolidado nas últimas 24h."}${linhaTrendsZap}
${blocoVideoZap}${blocoTrafegoZap}
👉 *Diretriz Operacional:* ${macro.recomendacao_acao || "Gravar cortes prioritários e amplificar narrativa nas redes."}

----------------------------------------
🔗 *Painel em Tempo Real:* https://radar-ceara.pages.dev`;

      // 1. Tentar copiar para a área de transferência como backup
      try {
        navigator.clipboard?.writeText(textoZap);
      } catch (e) {}

      // 2. Feedback visual no botão
      const textoOriginal = btnExportar.innerHTML;
      btnExportar.innerHTML = "<span>🚀</span> Abrindo WhatsApp...";
      btnExportar.style.background = "#16A34A";
      setTimeout(() => {
        btnExportar.innerHTML = textoOriginal;
        btnExportar.style.background = "";
      }, 3000);

      // 3. Disparo imediato da API do WhatsApp
      const urlZap = `https://api.whatsapp.com/send?text=${encodeURIComponent(textoZap)}`;
      window.open(urlZap, "_blank");
    });
  }

  // 3.D INICIALIZAÇÃO E CONTROLE DAS 5 JANELAS DO INSTAGRAM (1h, 2h, 12h, 24h, 7d)
  function inicializarHubInstagram(dadosInstagram) {
    if (!dadosInstagram) return;

    let janelaAtualIG = "1h";

    function trocarJanelaInstagram(janela) {
      janelaAtualIG = janela;

      ["1h", "2h", "12h", "24h", "7d"].forEach(j => {
        const btn = document.getElementById(`btn-ig-${j}`);
        if (btn) {
          if (j === janela) btn.classList.add("on");
          else btn.classList.remove("on");
        }
      });

      const sentJanela = (dadosInstagram.por_janela && dadosInstagram.por_janela[janela]) || dadosInstagram;
      const todosBase = dadosInstagram.todos_comentarios || dadosInstagram.comentarios_todos || [];
      const comentariosJanela = obterComentariosJanela(todosBase, sentJanela, janela);
      const sentAtual = { ...sentJanela, todos_comentarios: comentariosJanela };

      renderizarBlocoSentimento(sentAtual, "ig", {
        tipoRede: "instagram",
        nomeRede: "Instagram",
        rotuloBtn: "Ver no Instagram ↗",
        clsLink: "link-ig-comentario",
        iconeOrigem: "📸",
        janela: janela
      });
    }

    // Configura os ouvintes de clique nos 5 botões de tempo do Instagram
    ["1h", "2h", "12h", "24h", "7d"].forEach(j => {
      document.getElementById(`btn-ig-${j}`)?.addEventListener("click", () => {
        trocarJanelaInstagram(j);
      });
    });

    // Renderização inicial na janela padrão de 1h
    trocarJanelaInstagram("1h");
  }

  // 4. Painel Meta Ads
  function renderizarMetaAds(meta) {
    const container = document.getElementById("painel-meta");
    if (!container || !meta) return;

    const anunciantesHtml = (meta.top_anunciantes || []).map(a => `
      <div class="meta-anunciante">
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
          <span class="anunciante-nome">${escapeHtml(a.pagina)}</span>
          <span class="anunciante-gasto">${escapeHtml(a.gasto_estimado)}</span>
        </div>
        <div class="anunciante-foco">
          <strong>Pautas:</strong> ${(a.foco_pautas || []).join(", ")}<br>
          <small>Alvo: ${escapeHtml(a.publico_alvo)}</small>
        </div>
      </div>
    `).join("");

    const regioesHtml = (meta.distribuicao_geografica_anuncios || []).map(r => `
      <div style="display:flex; justify-content:space-between; padding: 6px 0; border-bottom: 1px dashed var(--linha);">
        <span>${escapeHtml(r.municipio)}</span>
        <div>
          <strong style="color:var(--azul-claro)">${r.percentual}%</strong>
          <small style="color:var(--tx-3); margin-left:6px;">(${escapeHtml(r.estrategia)})</small>
        </div>
      </div>
    `).join("");

    container.innerHTML = `
      <div class="card-meta">
        <h3>
          <span>Maiores Gastos com Anúncios (CE)</span>
          <small style="font-size:11px; font-weight:normal; color:var(--tx-3)">${escapeHtml(meta.fonte)}</small>
        </h3>
        <p style="font-size: 13px; color: var(--tx-2); margin-bottom: 10px;">
          Investimento total declarado no Ceará: <strong>${meta.investimento_estimado_ce_7d}</strong> (${meta.total_anuncios_ativos} anúncios ativos).
        </p>
        ${anunciantesHtml}
      </div>

      <div class="card-meta">
        <h3>Concentração de Alcance no Ceará</h3>
        <p style="font-size: 13px; color: var(--tx-2); margin-bottom: 10px;">
          Distribuição dos anúncios por cidade e diretriz recomendada para o mandato.
        </p>
        ${regioesHtml}
      </div>
    `;
  }

  // 7. Botão geral compartilhar no rodapé
  document.getElementById("btn-compartilhar-site")?.addEventListener("click", () => {
    const texto = "Confira o Radar Léo Suricate · Inteligência de dados eleitorais, chão e redes no Ceará:\n" + window.location.href;
    window.open("https://wa.me/?text=" + encodeURIComponent(texto), "_blank");
  });

  // 8. CONTROLE DOS HUBS DE PLATAFORMAS (MINIMIZAR / EXPANDIR / FOCO)
  const hubYtSec = document.getElementById("monitor-sec");
  const hubIgSec = document.getElementById("hub-instagram-sec");
  const cardTrends = document.querySelector(".card-transversal-google");
  const btnToggleYt = document.getElementById("btn-toggle-hub-yt");
  const btnToggleIg = document.getElementById("btn-toggle-hub-ig");
  const btnToggleTrends = document.getElementById("btn-toggle-hub-trends");
  const btnFocoTodos = document.getElementById("btn-foco-todos");
  const btnFocoYt = document.getElementById("btn-foco-yt");
  const btnFocoIg = document.getElementById("btn-foco-ig");

  function atualizarRotuloToggle(btn, sec) {
    if (!btn || !sec) return;
    const rotulo = btn.querySelector(".rotulo-toggle");
    const estaRecolhido = sec.classList.contains("recolhido");
    if (rotulo) {
      rotulo.textContent = estaRecolhido ? "Expandir" : "Minimizar";
    }
  }

  // Inicializa rótulos com base no estado inicial
  atualizarRotuloToggle(btnToggleYt, hubYtSec);
  atualizarRotuloToggle(btnToggleIg, hubIgSec);
  atualizarRotuloToggle(btnToggleTrends, cardTrends);

  function setFocoAtivo(btnAtivo) {
    [btnFocoTodos, btnFocoYt, btnFocoIg].forEach(b => {
      if (b) b.classList.remove("on");
    });
    if (btnAtivo) btnAtivo.classList.add("on");
  }

  if (btnToggleTrends && cardTrends) {
    btnToggleTrends.addEventListener("click", () => {
      cardTrends.classList.toggle("recolhido");
      atualizarRotuloToggle(btnToggleTrends, cardTrends);
    });
  }

  if (btnToggleYt && hubYtSec) {
    btnToggleYt.addEventListener("click", () => {
      hubYtSec.classList.toggle("recolhido");
      atualizarRotuloToggle(btnToggleYt, hubYtSec);
    });
  }

  if (btnToggleIg && hubIgSec) {
    btnToggleIg.addEventListener("click", () => {
      hubIgSec.classList.toggle("recolhido");
      atualizarRotuloToggle(btnToggleIg, hubIgSec);
    });
  }

  document.getElementById("cab-hub-yt")?.addEventListener("click", (e) => {
    if (e.target.closest("button") === btnToggleYt) return;
    if (hubYtSec) {
      hubYtSec.classList.toggle("recolhido");
      atualizarRotuloToggle(btnToggleYt, hubYtSec);
    }
  });

  document.getElementById("cab-hub-ig")?.addEventListener("click", (e) => {
    if (e.target.closest("button") === btnToggleIg) return;
    if (hubIgSec) {
      hubIgSec.classList.toggle("recolhido");
      atualizarRotuloToggle(btnToggleIg, hubIgSec);
    }
  });

  if (btnFocoTodos) {
    btnFocoTodos.addEventListener("click", () => {
      if (hubYtSec) {
        hubYtSec.classList.remove("recolhido");
        atualizarRotuloToggle(btnToggleYt, hubYtSec);
      }
      if (hubIgSec) {
        hubIgSec.classList.remove("recolhido");
        atualizarRotuloToggle(btnToggleIg, hubIgSec);
      }
      setFocoAtivo(btnFocoTodos);
    });
  }

  if (btnFocoYt) {
    btnFocoYt.addEventListener("click", () => {
      if (hubYtSec) {
        hubYtSec.classList.remove("recolhido");
        atualizarRotuloToggle(btnToggleYt, hubYtSec);
      }
      if (hubIgSec) {
        hubIgSec.classList.add("recolhido");
        atualizarRotuloToggle(btnToggleIg, hubIgSec);
      }
      setFocoAtivo(btnFocoYt);
      hubYtSec?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (btnFocoIg) {
    btnFocoIg.addEventListener("click", () => {
      if (hubIgSec) {
        hubIgSec.classList.remove("recolhido");
        atualizarRotuloToggle(btnToggleIg, hubIgSec);
      }
      if (hubYtSec) {
        hubYtSec.classList.add("recolhido");
        atualizarRotuloToggle(btnToggleYt, hubYtSec);
      }
      setFocoAtivo(btnFocoIg);
      hubIgSec?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  // =========================================================================
  // MODAL DE FONTES MONITORADAS (CANAIS E PERFIS)
  // =========================================================================
  const modalOverlay = document.getElementById("modal-fontes-overlay");
  const modalTitulo = document.getElementById("modal-fontes-titulo");
  const modalSubtitulo = document.getElementById("modal-fontes-subtitulo");
  const modalIcone = document.getElementById("modal-fontes-icone");
  const modalCorpo = document.getElementById("modal-fontes-corpo");
  const modalContagem = document.getElementById("modal-contagem-total");
  const btnFecharModalX = document.getElementById("btn-fechar-modal-x");
  const btnFecharModalBase = document.getElementById("btn-fechar-modal-base");
  const btnFontesIg = document.getElementById("btn-fontes-ig");
  const btnFontesYt = document.getElementById("btn-fontes-yt");

  function abrirModalFontes(tipo) {
    if (!modalOverlay || !modalCorpo) return;

    const fontes = (DADOS && DADOS.fontes_monitoradas) || {};

    if (tipo === "instagram") {
      const ig = fontes.instagram || {};
      const perfis = ig.perfis || [];
      const hashtags = ig.hashtags || [];
      const total = perfis.length + hashtags.length;

      if (modalIcone) modalIcone.textContent = "📸";
      if (hashtags.length > 0) {
        if (modalTitulo) modalTitulo.textContent = "Perfis & Hashtags Monitorados · Instagram";
        if (modalSubtitulo) modalSubtitulo.textContent = "Relação de perfis do campo popular, imprensa cearense e hashtags ativas";
        if (modalContagem) modalContagem.textContent = `${perfis.length} perfis e ${hashtags.length} hashtags em monitoramento`;
      } else {
        if (modalTitulo) modalTitulo.textContent = "Perfis Monitorados · Instagram";
        if (modalSubtitulo) modalSubtitulo.textContent = "Relação de perfis do campo popular e imprensa cearense";
        if (modalContagem) modalContagem.textContent = `${perfis.length} perfis cearenses em monitoramento`;
      }

      let html = "";

      if (perfis.length > 0) {
        html += `
          <div class="modal-secao-grupo">
            <span class="modal-grupo-titulo">Perfis Monitorados (${perfis.length})</span>
            <div class="modal-chips-grid">
              ${perfis.map(p => {
                const username = p.replace(/^@/, "");
                return `
                  <a href="https://www.instagram.com/${encodeURIComponent(username)}/" target="_blank" rel="noopener noreferrer" class="chip-fonte" title="Abrir perfil @${escapeHtml(username)} no Instagram">
                    <span>${escapeHtml(p)}</span>
                    <span class="chip-icone">↗</span>
                  </a>
                `;
              }).join("")}
            </div>
          </div>
        `;
      }

      if (hashtags.length > 0) {
        html += `
          <div class="modal-secao-grupo">
            <span class="modal-grupo-titulo">Hashtags Prioritárias (${hashtags.length})</span>
            <div class="modal-chips-grid">
              ${hashtags.map(h => {
                const tag = h.replace(/^#/, "");
                return `
                  <a href="https://www.instagram.com/explore/tags/${encodeURIComponent(tag)}/" target="_blank" rel="noopener noreferrer" class="chip-fonte" title="Ver hashtag ${escapeHtml(h)} no Instagram">
                    <span>${escapeHtml(h)}</span>
                    <span class="chip-icone">↗</span>
                  </a>
                `;
              }).join("")}
            </div>
          </div>
        `;
      }

      if (!html) {
        html = `<p style="color: var(--tx-2); font-size: 13px;">Nenhuma fonte cadastrada no momento.</p>`;
      }

      modalCorpo.innerHTML = html;

    } else if (tipo === "youtube") {
      const yt = fontes.youtube || {};
      const canais = yt.canais || [];

      if (modalIcone) modalIcone.textContent = "▶";
      if (modalTitulo) modalTitulo.textContent = "Canais Monitorados · YouTube";
      if (modalSubtitulo) modalSubtitulo.textContent = "Emissoras, portais jornalísticos e comunicadores políticos do Ceará";
      if (modalContagem) modalContagem.textContent = `${canais.length} canais cearenses em monitoramento`;

      let html = "";

      if (canais.length > 0) {
        html += `
          <div class="modal-secao-grupo">
            <span class="modal-grupo-titulo">Canais Ativos (${canais.length})</span>
            <div class="modal-chips-grid">
              ${canais.map(c => {
                return `
                  <a href="https://www.youtube.com/results?search_query=${encodeURIComponent(c)}" target="_blank" rel="noopener noreferrer" class="chip-fonte" title="Pesquisar canal '${escapeHtml(c)}' no YouTube">
                    <span>${escapeHtml(c)}</span>
                    <span class="chip-icone">↗</span>
                  </a>
                `;
              }).join("")}
            </div>
          </div>
        `;
      } else {
        html = `<p style="color: var(--tx-2); font-size: 13px;">Nenhum canal cadastrado no momento.</p>`;
      }

      modalCorpo.innerHTML = html;
    }

    modalOverlay.style.display = "flex";
    // Forçar reflow para ativar a animação de opacidade/transform
    void modalOverlay.offsetWidth;
    modalOverlay.classList.add("aberto");
    modalOverlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function fecharModalFontes() {
    if (!modalOverlay) return;
    modalOverlay.classList.remove("aberto");
    modalOverlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    setTimeout(() => {
      if (!modalOverlay.classList.contains("aberto")) {
        modalOverlay.style.display = "none";
      }
    }, 200);
  }

  btnFontesIg?.addEventListener("click", (e) => {
    e.stopPropagation();
    abrirModalFontes("instagram");
  });

  btnFontesYt?.addEventListener("click", (e) => {
    e.stopPropagation();
    abrirModalFontes("youtube");
  });

  btnFecharModalX?.addEventListener("click", fecharModalFontes);
  btnFecharModalBase?.addEventListener("click", fecharModalFontes);

  modalOverlay?.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
      fecharModalFontes();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalOverlay?.classList.contains("aberto")) {
      fecharModalFontes();
    }
  });

  // Utilitários
  function formatarNum(n) {
    return Number(n || 0).toLocaleString("pt-BR");
  }

  function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }
});
