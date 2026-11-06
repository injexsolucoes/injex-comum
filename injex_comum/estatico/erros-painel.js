// 🚨 Quadro "Erros do sistema" — módulo comum da Injex (injex_comum/erros.py). Mostra os erros em aberto (ou os
// resolvidos), com onde, quem, a origem no código e o caminho, "📋 Copiar para o responsável" e "✔ Resolvido".
// Uso (página só do administrador):  <div id="erros"></div>
//   <script src="/comum/erros-painel.js"></script>
//   <script>InjexErrosPainel.montar(document.getElementById("erros"))</script>
// Opções: { endereco: "/api/erros" }. Sem dependência de nenhum outro script.
(function () {
  if (window.InjexErrosPainel) return;

  function el(tag, attrs, ...filhos) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === "style") e.style.cssText = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const f of filhos.flat()) if (f !== null && f !== undefined) e.append(f);
    return e;
  }

  async function pedir(endereco, opcoes) {
    const r = await fetch(endereco, Object.assign({ credentials: "same-origin" }, opcoes || {}));
    let d = null;
    try { d = await r.json(); } catch (_) { /* sem corpo */ }
    if (!r.ok) throw Object.assign(new Error((d && typeof d.detail === "string" && d.detail) || "Não consegui carregar."),
      { status: r.status });
    return d;
  }

  const hora = (iso) => new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

  function cartao(e, recarregar, endereco, recado) {
    const codigo = e.chave.slice(0, 6).toUpperCase();
    const texto = `🚨 Erro ${codigo} (${e.onde})\n${e.tipo}: ${e.mensagem}\nOnde: ${e.rota || e.tela}\nOrigem: ${e.origem}\n` +
      `Quem: ${e.usuario || "(ninguém logado)"} · ${e.navegador}\n${e.vezes} vez(es), 1ª ${hora(e.primeira)}, última ${hora(e.ultima)}` +
      (e.pilha ? `\n\n${e.pilha}` : "");
    const botao = (rotulo, fn, principal) => el("button", { type: "button", style: "padding:6px 12px;border-radius:8px;" +
      "font:inherit;cursor:pointer;border:2px solid #2e7d32;" + (principal ? "background:#2e7d32;color:#fff" : "background:#fff;color:#2e7d32"),
      onclick: fn }, rotulo);
    return el("div", { style: `margin:8px 0;padding:12px;border:1px solid #ddd;border-radius:10px;background:#fff;` +
        `border-left:5px solid ${e.resolvido ? "#7a7" : "#c62828"}` },
      el("div", { style: "display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap" },
        el("strong", {}, `${e.onde === "tela" ? "🖥️ Tela" : "🗄️ Servidor"} · ${e.tipo}: ${e.mensagem.slice(0, 160)}`),
        el("span", { style: "color:#666" }, `${e.vezes}× · última ${hora(e.ultima)}`)),
      el("div", { style: "color:#555;margin:4px 0;font-size:.92em" }, `📍 ${e.rota || e.tela} · 🧩 origem: `,
        el("code", {}, e.origem), ` · 👤 ${e.usuario || "ninguém logado"}${e.navegador ? " · " + e.navegador : ""} · 1ª vez ${hora(e.primeira)}`),
      e.pilha ? el("details", {}, el("summary", { style: "color:#555;cursor:pointer" }, "Caminho no código"),
        el("pre", { style: "white-space:pre-wrap;font-size:12px" }, e.pilha)) : null,
      el("div", { style: "display:flex;gap:8px;margin-top:6px;flex-wrap:wrap" },
        botao("📋 Copiar para o responsável", async () => {
          try { await navigator.clipboard.writeText(texto); recado("Copiado: mande para o responsável."); }
          catch (_) { recado("Não consegui copiar.", true); }
        }),
        botao(e.resolvido ? "↩ Voltar para em aberto" : "✔ Resolvido", async () => {
          try {
            await pedir(`${endereco}/${e.chave}/resolvido`, { method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ resolvido: !e.resolvido }) });
            recarregar();
          } catch (err) { recado(err.message, true); }
        }, true)));
  }

  function montar(alvo, opcoes) {
    const endereco = (opcoes && opcoes.endereco) || "/api/erros";
    const recado = (opcoes && opcoes.aviso) || ((t) => alert(t));
    const resolvidos = el("input", { type: "checkbox" });
    const lista = el("div", {}, "Consultando…");
    async function carregar() {
      let d;
      try { d = await pedir(`${endereco}?resolvidos=${resolvidos.checked}`); }
      catch (e) { lista.replaceChildren(el("p", { style: "color:#c62828" }, e.message)); return; }
      lista.replaceChildren(...(d.erros.length ? d.erros.map((e) => cartao(e, carregar, endereco, recado))
        : [el("p", { style: "color:#555" }, resolvidos.checked ? "Nenhum erro resolvido guardado." : "Nenhum erro em aberto. 👍")]));
    }
    resolvidos.addEventListener("change", carregar);
    alvo.replaceChildren(
      el("p", { style: "color:#555;margin:0 0 8px" }, "Todo erro inesperado (no servidor ou numa tela) fica aqui com onde ",
        "aconteceu, quem estava usando e a origem (arquivo e linha do código). Erro novo manda um e-mail e aparece no Início. ",
        "Para corrigir: \"📋 Copiar para o responsável\". Corrigido e no ar → \"✔ Resolvido\" (se acontecer de novo, ele volta e avisa)."),
      el("div", { style: "display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:6px" },
        el("button", { type: "button", style: "padding:6px 12px;border-radius:8px;font:inherit;cursor:pointer", onclick: carregar }, "🔄 Atualizar"),
        el("label", { style: "color:#555" }, resolvidos, " Ver os já resolvidos")),
      lista);
    carregar();
    return { carregar };
  }

  window.InjexErrosPainel = { montar };
})();
