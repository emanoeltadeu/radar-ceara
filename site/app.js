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

    // Em Alta no Google (Ceará - 4h vs 24h)
    const listaGoogle = document.getElementById("lista-google-ce");
    const btnTrends4h = document.getElementById("btn-trends-4h");
    const btnTrends24h = document.getElementById("btn-trends-24h");

    function renderItensGoogle(itens) {
      if (!listaGoogle) return;
      listaGoogle.innerHTML = (itens || []).map(item => {
        const clsPonto = item.lado === "nossa" ? "nossa" : (item.lado === "deles" ? "deles" : "disputa");
        return `
          <div class="item-google-ce">
            <div class="item-google-topo">
              <span class="termo-com-ponto">
                <span class="ponto-busca ${clsPonto}"></span>
                ${escapeHtml(item.termo)}
              </span>
              <span class="volume-badge-verde">${escapeHtml(item.volume)}</span>
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
      renderItensGoogle(gt.itens_4h && gt.itens_4h.length > 0 ? gt.itens_4h : gt.itens);

      btnTrends4h?.addEventListener("click", () => {
        btnTrends4h.classList.add("on");
        btnTrends24h?.classList.remove("on");
        renderItensGoogle(gt.itens_4h || gt.itens);
      });

      btnTrends24h?.addEventListener("click", () => {
        btnTrends24h.classList.add("on");
        btnTrends4h?.classList.remove("on");
        renderItensGoogle(gt.itens_24h || gt.itens);
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

      conteudoMacroEl.innerHTML = `
        <p><strong>Pauta:</strong> <span style="font-weight:700;">${escapeHtml(macro.oportunidade || "Pauta Popular")}</span> — ${escapeHtml(macro.detalhe || "")}</p>
        <div class="tatico-acao-linha">
          <strong>➔ Recomendação:</strong>
          <span>${escapeHtml(macro.recomendacao_acao || "")}</span>
        </div>
        ${extrasHtml}
      `;
    }

    // 5. Botão de Exportação de Tarefas para WhatsApp
    btnExportar?.addEventListener("click", () => {
      const alerta = tatico.alerta_imediato || {};
      const macro = tatico.diretriz_estrategica_24h || {};
      const hora = tatico.atualizado_em || "Agora";
      const nomeRede = prefix === "ig" ? "Instagram" : "YouTube";

      let extrasZap = "";
      if (macro.gancho_conteudo) {
        extrasZap += `\n• Gancho: ${macro.gancho_conteudo}`;
      }
      if (macro.segmentacao_trafego) {
        extrasZap += `\n• Tráfego: ${macro.segmentacao_trafego}`;
      }

      const textoZap = `⚡ *RADAR TÁTICO (${hora})*
Rede: ${nomeRede} | Status: *${tatico.status_dominio || "ANALISADO"}*

🚨 *ALERTA URGENTE (ÚLTIMA 1H)*
• Pauta: ${alerta.pauta || "Monitoramento"}
• Contexto: ${alerta.detalhe || tatico.diagnostico_urgente_1h || ""}
➔ *Ação Imediata:* ${alerta.acao_recomendada || "Seguir monitorando"}

🟢 *DIRETRIZ DO DIA (ÚLTIMAS 24H) · OPORTUNIDADE*
• Pauta: ${macro.oportunidade || "Campo Popular"}
• Fôlego: ${macro.detalhe || ""}${extrasZap}
➔ *Recomendação:* ${macro.recomendacao_acao || "Gravar cortes e orientar tráfego"}`;

      navigator.clipboard.writeText(textoZap).then(() => {
        const textoOriginal = btnExportar.innerHTML;
        btnExportar.innerHTML = "<span>✅</span> Tarefas Copiadas!";
        btnExportar.style.background = "#16A34A";
        setTimeout(() => {
          btnExportar.innerHTML = textoOriginal;
          btnExportar.style.background = "";
        }, 3000);
      });
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
