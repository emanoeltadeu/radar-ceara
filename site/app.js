document.addEventListener("DOMContentLoaded", () => {
  let DADOS = null;

  // 1. Carregar radar_ce.json
  fetch("radar_ce.json", { cache: "no-store" })
    .then(r => {
      if (!r.ok) throw new Error("Erro na rede");
      return r.json();
    })
    .then(data => {
      DADOS = data;
      renderizarMonitorRedes(data.monitor_redes);

      // Sentimento YouTube (com fallback para sentimento_mencoes)
      const sentYT = data.sentimento_youtube || data.sentimento_mencoes;
      if (sentYT) {
        renderizarBlocoSentimento(sentYT, "yt", {
          tipoRede: "youtube",
          nomeRede: "YouTube",
          rotuloBtn: "Ver no YouTube ↗",
          clsLink: "link-yt-comentario",
          iconeOrigem: "📺"
        });
      }

      // Sentimento Instagram
      if (data.sentimento_instagram) {
        renderizarBlocoSentimento(data.sentimento_instagram, "ig", {
          tipoRede: "instagram",
          nomeRede: "Instagram",
          rotuloBtn: "Ver no Instagram ↗",
          clsLink: "link-ig-comentario",
          iconeOrigem: "📸"
        });
      }

      renderizarMetaAds(data.meta_transparencia);
      const elHora = document.getElementById("hora-atualizacao");
      if (elHora) elHora.textContent = data.gerado_em || "Atualizado";
    })
    .catch(err => {
      console.error("Falha ao carregar radar_ce.json:", err);
    });

  // 3. MONITOR DE REDES AO VIVO (YouTube Nuvem, YouTube Vídeos e Google Trends)
  function renderizarMonitorRedes(monitor) {
    if (!monitor) return;

    let janelaAtualYT = "24h";

    // A. Renderizador da Nuvem de Palavras
    const nuvemBox = document.getElementById("nuvem-termos");
    const horaNuvemBadge = document.getElementById("hora-nuvem");

    function renderNuvem(itensNuvem) {
      if (!nuvemBox || !itensNuvem) return;
      nuvemBox.innerHTML = itensNuvem.map(item => {
        const tam = (11 + (item.peso / 100) * 14).toFixed(1);
        const clsLado = item.lado === "nossa" ? "nossa" : (item.lado === "deles" ? "deles" : "disputa");
        return `<span class="nuvem-tag ${clsLado}" style="font-size: ${tam}px;" title="Alcance: ${item.peso}/100">${escapeHtml(item.t)}</span>`;
      }).join("");
    }

    // B. Renderizador de Mais Falados nos Vídeos
    const listaVideoDeles = document.getElementById("itens-video-deles");
    const listaVideoNossa = document.getElementById("itens-video-nossa");
    const contagemSub = document.getElementById("videos-contagem-sub");
    const painelVideoDetalhe = document.getElementById("painel-videos-detalhe");
    const detalheVideoBadge = document.getElementById("detalhe-video-badge");
    const detalheVideoTema = document.getElementById("detalhe-video-tema");
    const detalheVideoContagem = document.getElementById("detalhe-video-contagem");
    const listaVideosDetalhe = document.getElementById("lista-videos-detalhe");
    const btnFecharDetalheVideos = document.getElementById("btn-fechar-detalhe-videos");

    let temaSelecionadoVideo = null;
    let campoSelecionadoVideo = null;

    btnFecharDetalheVideos?.addEventListener("click", () => {
      fecharDetalheVideos();
    });

    function fecharDetalheVideos() {
      temaSelecionadoVideo = null;
      campoSelecionadoVideo = null;
      if (painelVideoDetalhe) painelVideoDetalhe.style.display = "none";
      document.querySelectorAll(".item-video-linha").forEach(el => el.classList.remove("ativo"));
    }

    function abrirDetalheVideos(item, campo, janelaAtual) {
      if (temaSelecionadoVideo === item.termo && campoSelecionadoVideo === campo) {
        fecharDetalheVideos();
        return;
      }

      temaSelecionadoVideo = item.termo;
      campoSelecionadoVideo = campo;

      document.querySelectorAll(".item-video-linha").forEach(el => el.classList.remove("ativo"));
      const elAtivo = document.querySelector(`.item-video-linha[data-termo="${encodeURIComponent(item.termo)}"][data-campo="${campo}"]`);
      if (elAtivo) elAtivo.classList.add("ativo");

      if (painelVideoDetalhe) {
        painelVideoDetalhe.style.display = "block";
      }
      if (detalheVideoBadge) {
        detalheVideoBadge.textContent = campo === "oposicao" ? "PRÓ-OPOSIÇÃO" : "CAMPO POPULAR / LÉO";
        detalheVideoBadge.className = `detalhe-badge ${campo === "oposicao" ? "deles" : "nossa"}`;
      }
      if (detalheVideoTema) {
        detalheVideoTema.textContent = item.termo;
      }

      const vids = item.videos || [];
      if (detalheVideoContagem) {
        const plural = vids.length === 1 ? "vídeo cearense associado" : "vídeos cearenses associados";
        detalheVideoContagem.textContent = `${vids.length} ${plural} a esta pauta nas últimas ${janelaAtual}.`;
      }

      if (listaVideosDetalhe) {
        if (vids.length === 0) {
          listaVideosDetalhe.innerHTML = `
            <div style="font-size: 11.5px; color: var(--tinta-sub); padding: 8px 0;">
              ℹ️ Nenhum vídeo individualizado diretamente para esta pauta nesta janela.
            </div>
          `;
        } else {
          listaVideosDetalhe.innerHTML = vids.map(v => `
            <a href="${escapeHtml(v.url)}" target="_blank" rel="noopener noreferrer" class="card-video-item" title="Assistir no YouTube">
              <svg class="card-video-icone" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
              </svg>
              <div class="card-video-info">
                <div class="card-video-titulo">${escapeHtml(v.titulo)}</div>
                <div class="card-video-canal">Canal: <span>${escapeHtml(v.canal || 'YouTube')}</span> ↗</div>
              </div>
            </a>
          `).join("");
        }
      }
    }

    function renderVideos(dadosVideos) {
      if (!dadosVideos) return;
      const janelaAtual = dadosVideos.janela || janelaAtualYT;
      if (contagemSub && dadosVideos.total_videos) {
        contagemSub.textContent = `${dadosVideos.total_videos} vídeos cearenses analisados nas últimas ${janelaAtual} · Clique para ver os vídeos`;
      }

      if (listaVideoDeles && dadosVideos.oposicao) {
        const itensDeles = dadosVideos.oposicao.itens || [];
        listaVideoDeles.innerHTML = itensDeles.map(item => {
          const w = Math.min(100, Math.max(8, item.valor * 2.5));
          const estaAtivo = temaSelecionadoVideo === item.termo && campoSelecionadoVideo === "oposicao";
          const qtdLabel = item.qtd_videos ? ` (${item.qtd_videos} ${item.qtd_videos === 1 ? 'vídeo' : 'vídeos'})` : '';
          return `
            <div class="item-video-linha ${estaAtivo ? 'ativo' : ''}" 
                 data-termo="${encodeURIComponent(item.termo)}" 
                 data-campo="oposicao" 
                 title="Clique para ver os vídeos sobre ${escapeHtml(item.termo)}">
              <div class="item-video-dados">
                <span>${escapeHtml(item.termo)}${qtdLabel}</span>
                <span class="item-video-pct">${escapeHtml(item.pct)}</span>
              </div>
              <div class="barra-video-container">
                <div class="barra-video-fill deles" style="width: ${w}%;"></div>
              </div>
            </div>
          `;
        }).join("");

        listaVideoDeles.querySelectorAll(".item-video-linha").forEach((el, idx) => {
          el.addEventListener("click", () => {
            abrirDetalheVideos(itensDeles[idx], "oposicao", janelaAtual);
          });
        });
      }

      if (listaVideoNossa && dadosVideos.popular) {
        const itensNossa = dadosVideos.popular.itens || [];
        listaVideoNossa.innerHTML = itensNossa.map(item => {
          const w = Math.min(100, Math.max(8, item.valor * 2.5));
          const estaAtivo = temaSelecionadoVideo === item.termo && campoSelecionadoVideo === "popular";
          const qtdLabel = item.qtd_videos ? ` (${item.qtd_videos} ${item.qtd_videos === 1 ? 'vídeo' : 'vídeos'})` : '';
          return `
            <div class="item-video-linha ${estaAtivo ? 'ativo' : ''}" 
                 data-termo="${encodeURIComponent(item.termo)}" 
                 data-campo="popular" 
                 title="Clique para ver os vídeos sobre ${escapeHtml(item.termo)}">
              <div class="item-video-dados">
                <span>${escapeHtml(item.termo)}${qtdLabel}</span>
                <span class="item-video-pct">${escapeHtml(item.pct)}</span>
              </div>
              <div class="barra-video-container">
                <div class="barra-video-fill nossa" style="width: ${w}%;"></div>
              </div>
            </div>
          `;
        }).join("");

        listaVideoNossa.querySelectorAll(".item-video-linha").forEach((el, idx) => {
          el.addEventListener("click", () => {
            abrirDetalheVideos(itensNossa[idx], "popular", janelaAtual);
          });
        });
      }
    }

    // Função unificada para alternar janela temporal do YouTube (12h, 24h, 48h)
    function trocarJanelaYouTube(janela) {
      janelaAtualYT = janela;
      
      ["12h", "24h", "48h"].forEach(j => {
        const btn = document.getElementById(`btn-yt-${j}`);
        if (btn) {
          if (j === janela) btn.classList.add("on");
          else btn.classList.remove("on");
        }
      });

      if (horaNuvemBadge) {
        horaNuvemBadge.textContent = `YouTube · ${janela}`;
      }

      const nuvemDados = (monitor.nuvens_por_janela && monitor.nuvens_por_janela[janela]) || monitor.nuvem;
      renderNuvem(nuvemDados);

      const videosDados = (monitor.videos_por_janela && monitor.videos_por_janela[janela]) || monitor.videos_mais_falados_ce;
      renderVideos(videosDados);

      if (temaSelecionadoVideo) {
        const bloco = campoSelecionadoVideo === "oposicao" ? videosDados?.oposicao : videosDados?.popular;
        const itemEncontrado = (bloco?.itens || []).find(it => it.termo === temaSelecionadoVideo);
        if (itemEncontrado) {
          abrirDetalheVideos(itemEncontrado, campoSelecionadoVideo, janela);
        } else {
          fecharDetalheVideos();
        }
      }
    }

    // Inicializar YouTube na janela padrão (24h)
    trocarJanelaYouTube("24h");

    // Event listeners para os botões do YouTube
    document.getElementById("btn-yt-12h")?.addEventListener("click", () => trocarJanelaYouTube("12h"));
    document.getElementById("btn-yt-24h")?.addEventListener("click", () => trocarJanelaYouTube("24h"));
    document.getElementById("btn-yt-48h")?.addEventListener("click", () => trocarJanelaYouTube("48h"));

    // Busca de Palavra
    const formBusca = document.getElementById("form-busca-palavra");
    const inputBusca = document.getElementById("input-busca-palavra");
    const resBusca = document.getElementById("res-busca-palavra");

    formBusca?.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = (inputBusca?.value || "").toLowerCase().trim();
      if (!q) {
        resBusca.textContent = "";
        return;
      }
      const nuvemAtual = (monitor.nuvens_por_janela && monitor.nuvens_por_janela[janelaAtualYT]) || monitor.nuvem || [];
      const achouNuvem = nuvemAtual.find(n => n.t.toLowerCase().includes(q));

      if (achouNuvem) {
        resBusca.innerHTML = `💬 <strong>${escapeHtml(achouNuvem.t)}</strong> está entre os termos mais falados nas últimas ${janelaAtualYT} no YouTube CE (peso ${achouNuvem.peso}/100).`;
      } else {
        resBusca.innerHTML = `ℹ️ <em>"${escapeHtml(q)}"</em> não teve destaque expressivo nas últimas ${janelaAtualYT} no YouTube cearense.`;
      }
    });

    // D. Em Alta no Google (Ceará - 4h vs 24h)
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
    if (totalLabel && sent.total_analisados) {
      totalLabel.textContent = `${sent.total_analisados} comentários analisados`;
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

    const pctApoio = document.getElementById(`pct-apoio-card-${prefix}`);
    const pctOposicao = document.getElementById(`pct-oposicao-card-${prefix}`);
    if (pctApoio) pctApoio.textContent = `${pos.toFixed(1).replace(".", ",")}%`;
    if (pctOposicao) pctOposicao.textContent = `${neg.toFixed(1).replace(".", ",")}%`;

    let temaAtivo = null;
    const todosComentarios = sent.comentarios_todos || sent.todos_comentarios || sent.amostras_destaque || [];
    const titCol = document.getElementById(`tit-col-comentarios-${prefix}`);
    const badgeCol = document.getElementById(`badge-filtro-comentarios-${prefix}`);
    const listaAmostras = document.getElementById(`lista-amostras-comentarios-${prefix}`);
    const listaPos = document.getElementById(`lista-temas-pos-${prefix}`);
    const listaNeg = document.getElementById(`lista-temas-neg-${prefix}`);

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

    function renderItemTema(t, tipoLado) {
      if (!t) return "";
      const nome = typeof t === "object" ? (t.tema || t.rotulo || "") : t;
      const qtd = typeof t === "object" && t.qtd ? `${t.qtd} ${t.qtd === 1 ? 'menção' : 'menções'}` : "";
      return `
        <li class="item-tema-clicavel" data-tema="${escapeHtml(nome)}" data-lado="${tipoLado}" title="Clique para ver os comentários reais sobre este tema">
          <span class="tema-nome">${escapeHtml(nome)}</span>
          ${qtd ? `<span class="tema-qtd-badge">${escapeHtml(qtd)}</span>` : ""}
        </li>
      `;
    }

    if (listaPos && sent.top_temas_positivos) {
      listaPos.innerHTML = sent.top_temas_positivos.map(t => renderItemTema(t, "pos")).join("");
      listaPos.querySelectorAll(".item-tema-clicavel").forEach(el => {
        el.addEventListener("click", () => {
          filtrarPorTema(el.getAttribute("data-tema"), "pos");
        });
      });
    }

    if (listaNeg && sent.top_temas_negativos) {
      listaNeg.innerHTML = sent.top_temas_negativos.map(t => renderItemTema(t, "neg")).join("");
      listaNeg.querySelectorAll(".item-tema-clicavel").forEach(el => {
        el.addEventListener("click", () => {
          filtrarPorTema(el.getAttribute("data-tema"), "neg");
        });
      });
    }

    // Inicializa a 3ª coluna com as amostras gerais de destaque
    renderComentarios(sent.amostras_destaque || todosComentarios.slice(0, 5), null);
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
