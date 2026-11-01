// 🚨 Erros das telas — módulo comum da Injex (injex_comum/erros.py). Todo erro de JavaScript vai para o registro do
// servidor com a tela, o arquivo e a linha. No máximo 10 por tela aberta e sem repetir o mesmo; nunca atrapalha a tela.
// Carregar ANTES dos outros scripts:  <script src="/comum/erros.js"></script>
// Outro endereço:  <script src="/comum/erros.js" data-endereco="/api/sistema/erros/tela"></script>
// Erro que o servidor já devolveu e a tela tratou (ex.: "código errado") NÃO é erro do código: quem chama a API marca o
// erro com `status` (ex.: Object.assign(new Error(msg), { status: 400 })) e ele não é mandado.
(function vigiarErrosDaTela() {
  if (window.InjexErros) return;  // já ligado nesta página
  const script = document.currentScript;
  const endereco = (script && script.dataset.endereco) || "/api/erros/tela";
  const vistos = new Set();

  function mandar(mensagem, arquivo, linha, coluna, pilha) {
    const chave = `${mensagem}|${arquivo}|${linha}`;
    if (vistos.has(chave) || vistos.size >= 10) return;
    vistos.add(chave);
    try {
      fetch(endereco, { method: "POST", headers: { "Content-Type": "application/json" }, keepalive: true,
        body: JSON.stringify({ mensagem: String(mensagem || "").slice(0, 500), arquivo: String(arquivo || ""),
          linha: linha || 0, coluna: coluna || 0, pilha: String(pilha || "").slice(0, 3000),
          tela: location.pathname + location.hash }) }).catch(() => {});
    } catch (_) { /* nunca atrapalha */ }
  }

  window.addEventListener("error", (ev) => {
    if (!ev.message) return;  // imagem/arquivo que não carregou: não é erro do código
    mandar(ev.message, ev.filename, ev.lineno, ev.colno, ev.error && ev.error.stack);
  });
  window.addEventListener("unhandledrejection", (ev) => {
    const r = ev.reason;
    if (!r || r.status || (r.message && /fetch|network|Failed to fetch|carregar/i.test(r.message))) return;
    const linha = (r.stack || "").split("\n").find((l) => /\/(static|comum)\//.test(l) || l.includes(location.pathname)) || "";
    const m = linha.match(/(https?:\/\/[^\s)]+):(\d+):(\d+)/);
    mandar(r.message || String(r), m ? m[1] : "", m ? +m[2] : 0, m ? +m[3] : 0, r.stack);
  });

  window.InjexErros = { mandar };  // para mandar um erro "à mão": InjexErros.mandar("texto", "", 0, 0, "")
})();
