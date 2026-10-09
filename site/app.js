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
      renderizarSentimentoIA(data.sentimento_mencoes);
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

    function renderVideos(dadosVideos) {
      if (!dadosVideos) return;
      if (contagemSub && dadosVideos.total_videos) {
        contagemSub.textContent = `${dadosVideos.total_videos} vídeos cearenses analisados nas últimas ${dadosVideos.janela || janelaAtualYT}`;
      }
      if (listaVideoDeles && dadosVideos.oposicao) {
        listaVideoDeles.innerHTML = (dadosVideos.oposicao.itens || []).map(item => {
          const w = Math.min(100, Math.max(8, item.valor * 2.5));
          return `
            <div class="item-video-linha">
              <div class="item-video-dados">
                <span>${escapeHtml(item.termo)}</span>
                <span class="item-video-pct">${escapeHtml(item.pct)}</span>
              </div>
              <div class="barra-video-container">
                <div class="barra-video-fill deles" style="width: ${w}%;"></div>
              </div>
            </div>
          `;
        }).join("");
      }
      if (listaVideoNossa && dadosVideos.popular) {
        listaVideoNossa.innerHTML = (dadosVideos.popular.itens || []).map(item => {
          const w = Math.min(100, Math.max(8, item.valor * 2.5));
          return `
            <div class="item-video-linha">
              <div class="item-video-dados">
                <span>${escapeHtml(item.termo)}</span>
                <span class="item-video-pct">${escapeHtml(item.pct)}</span>
              </div>
              <div class="barra-video-container">
                <div class="barra-video-fill nossa" style="width: ${w}%;"></div>
              </div>
            </div>
          `;
        }).join("");
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

  // 3.1. RENDERIZADOR DE SENTIMENTO & HUMOR POPULAR COM GEMINI
  function renderizarSentimentoIA(sent) {
    if (!sent) return;

    const totalLabel = document.getElementById("sentimento-total-label");
    if (totalLabel && sent.total_analisados) {
      totalLabel.textContent = `${sent.total_analisados} comentários analisados com ${sent.modelo || "IA"}`;
    }

    const pos = sent.positivo_pct || 0;
    const neu = sent.neutro_pct || 0;
    const neg = sent.negativo_pct || 0;

    const barPos = document.getElementById("barra-sent-pos");
    const barNeu = document.getElementById("barra-sent-neu");
    const barNeg = document.getElementById("barra-sent-neg");

    const rotPos = document.getElementById("rotulo-sent-pos");
    const rotNeu = document.getElementById("rotulo-sent-neu");
    const rotNeg = document.getElementById("rotulo-sent-neg");

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

    const pctApoio = document.getElementById("pct-apoio-card");
    const pctOposicao = document.getElementById("pct-oposicao-card");
    if (pctApoio) pctApoio.textContent = `${pos.toFixed(1).replace(".", ",")}%`;
    if (pctOposicao) pctOposicao.textContent = `${neg.toFixed(1).replace(".", ",")}%`;

    let temaAtivo = null;
    const todosComentarios = sent.comentarios_todos || sent.amostras_destaque || [];
    const titCol = document.getElementById("tit-col-comentarios");
    const badgeCol = document.getElementById("badge-filtro-comentarios");
    const listaAmostras = document.getElementById("lista-amostras-comentarios");

    function renderComentarios(lista, temaFiltro = null) {
      if (!listaAmostras) return;

      if (titCol) {
        titCol.textContent = temaFiltro ? `Comentários: "${temaFiltro}"` : "Comentários Reais (Amostras da IA)";
      }

      if (badgeCol) {
        if (temaFiltro) {
          badgeCol.innerHTML = `${lista.length} ${lista.length === 1 ? 'comentário' : 'comentários'} <button id="btn-limpar-filtro" class="btn-limpar-filtro" title="Limpar filtro e ver amostras">✕ Ver todos</button>`;
          document.getElementById("btn-limpar-filtro")?.addEventListener("click", () => {
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
        const videoOrigem = a.video_titulo ? `<div class="amostra-video-origem" title="${escapeHtml(a.video_titulo)}">📺 ${escapeHtml(a.video_titulo)}</div>` : "";
        const linkYt = a.link_yt ? `<a href="${escapeHtml(a.link_yt)}" target="_blank" rel="noopener noreferrer" class="link-yt-comentario" title="Abrir este comentário destacado no YouTube">Ver no YouTube ↗</a>` : "";
        return `
          <div class="item-amostra-comentario">
            <div class="amostra-topo">
              <span class="amostra-autor">${escapeHtml(a.autor)}</span>
              <span class="amostra-tag ${clsTag}">${escapeHtml(a.sentimento)}</span>
            </div>
            ${videoOrigem}
            <div class="amostra-texto">"${escapeHtml(a.texto)}"</div>
            ${linkYt ? `<div class="amostra-rodape">${linkYt}</div>` : ""}
          </div>
        `;
      }).join("");
    }

    function filtrarPorTema(tema, tipoLado) {
      if (temaAtivo === tema || !tema) {
        temaAtivo = null;
        document.querySelectorAll(".item-tema-clicavel").forEach(el => el.classList.remove("ativo-pos", "ativo-neg"));
        renderComentarios(sent.amostras_destaque || todosComentarios.slice(0, 5), null);
        return;
      }

      temaAtivo = tema;
      document.querySelectorAll(".item-tema-clicavel").forEach(el => {
        el.classList.remove("ativo-pos", "ativo-neg");
        if (el.getAttribute("data-tema") === tema) {
          el.classList.add(tipoLado === "pos" ? "ativo-pos" : "ativo-neg");
        }
      });

      const filtrados = todosComentarios.filter(c => {
        const cTema = (c.tema || "").toLowerCase().trim();
        const tBusca = tema.toLowerCase().trim();
        return cTema === tBusca || cTema.includes(tBusca) || tBusca.includes(cTema);
      });

      renderComentarios(filtrados, tema);

      // Scroll suave até a coluna de comentários se estiver em tela mobile
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

    const listaPos = document.getElementById("lista-temas-pos");
    if (listaPos && sent.top_temas_positivos) {
      listaPos.innerHTML = sent.top_temas_positivos.map(t => renderItemTema(t, "pos")).join("");
      listaPos.querySelectorAll(".item-tema-clicavel").forEach(el => {
        el.addEventListener("click", () => {
          filtrarPorTema(el.getAttribute("data-tema"), "pos");
        });
      });
    }

    const listaNeg = document.getElementById("lista-temas-neg");
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
