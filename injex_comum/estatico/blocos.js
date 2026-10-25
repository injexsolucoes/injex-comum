// 🧱 Blocos livres do injex-comum: carrossel, vídeo (só carrega no toque) e galeria que amplia.
// Roda sozinho ao abrir a página; quem monta a página depois (ex.: cardápio digital) chama InjexBlocos.iniciar(caixa).
(function () {
  'use strict';
  var ampliada = null;
  function abrir(src) {
    if (!ampliada) {
      ampliada = document.createElement('div');
      ampliada.className = 'ib-ampliada'; ampliada.setAttribute('role', 'dialog'); ampliada.setAttribute('aria-label', 'Foto ampliada');
      ampliada.innerHTML = '<button type="button" aria-label="Fechar">✕</button><img alt="">';
      ampliada.addEventListener('click', function () { ampliada.classList.remove('aberta'); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') ampliada.classList.remove('aberta'); });
      document.body.appendChild(ampliada);
    }
    ampliada.querySelector('img').src = src; ampliada.classList.add('aberta');
  }
  function iniciar(raiz) {
    raiz = raiz || document;
    raiz.querySelectorAll('.bloco-livre [data-carrossel]').forEach(function (c) {
      if (c.dataset.pronto) return; c.dataset.pronto = '1';
      var t = c.querySelector('.trilho');
      c.querySelectorAll('.seta').forEach(function (s) {
        s.addEventListener('click', function () {
          var fim = t.scrollLeft + t.clientWidth >= t.scrollWidth - 4, inicio = t.scrollLeft <= 4;
          var prox = s.classList.contains('prox');
          t.scrollLeft = prox ? (fim ? 0 : t.scrollLeft + t.clientWidth) : (inicio ? t.scrollWidth : t.scrollLeft - t.clientWidth);
        });
      });
    });
    // 🍪 vídeo do YouTube: o player (com os cookies dele) só carrega no toque
    raiz.querySelectorAll('.bloco-livre [data-video]').forEach(function (v) {
      var b = v.querySelector('button'); if (!b || v.dataset.pronto) return; v.dataset.pronto = '1';
      b.addEventListener('click', function () {
        var f = document.createElement('iframe');
        f.src = 'https://www.youtube-nocookie.com/embed/' + v.dataset.video + '?autoplay=1&rel=0';
        f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen = true; f.title = 'Vídeo';
        v.replaceChildren(f);
      });
    });
    raiz.querySelectorAll('.bloco-livre .galeria-livre button').forEach(function (b) {
      if (b.dataset.pronto) return; b.dataset.pronto = '1';
      b.addEventListener('click', function () { abrir(b.dataset.grande); });
    });
  }
  window.InjexBlocos = window.InjexBlocos || {};
  window.InjexBlocos.iniciar = iniciar;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { iniciar(); });
  else iniciar();
})();
