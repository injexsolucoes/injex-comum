// 🧱 Editor de blocos do injex-comum (o mesmo em todos os sistemas: Agenda, Lojas, Lanchonete).
// O sistema guarda a lista e diz o que é dele (seções prontas, ações do botão, fotos); este arquivo só desenha e
// mexe na lista. As regras de verdade (limites, links, fotos que existem) são do servidor: blocos.py › validar.
//
//   var ed = InjexBlocos.editor(caixa, {
//     blocos: [...],                      // a lista (o editor mexe nela mesma)
//     secoes: { banners: { nome: 'Banners', dica: 'Vêm de …', icone: 'image', extra: function (b, card) {} } },
//     acoes: ['whatsapp', 'link'],        // ações do botão que valem (a 1ª é a padrão)
//     fotos: function () { return ['chave', …]; },  fotoUrl: function (chave) { return '/…'; },
//     subirFoto: function (arquivo) { return Promise com a chave (o sistema já põe a chave na lista de fotos) },
//     icones: function () { return Promise com a galeria [{nome, rotulo, linha, preenchido, emoji}] },
//     estilo: function () { return 'linha' },   // estilo dos ícones do site (o elemento Ícone mostra nele)
//     aoMudar: function (estrutura) {},   // false = digitou (salvar daqui a pouco); true = mudou a estrutura
//     aviso: function (texto) {}, onde: 'do site'
//   });
//   ed.redesenhar();  ed.blocos();
// Telas internas: ícones de linha da galeria (sem emoji). Visual em editor-blocos.css (classes ibe-).
(function () {
  'use strict';
  var ACOES = { agendar: 'Agendar', whatsapp: 'WhatsApp', cardapio: 'Ver o cardápio', produtos: 'Ver os produtos', link: 'Um link' };
  var ELEMENTOS = [
    ['icone', 'star', 'Ícone', 'Um desenho da galeria, na cor do site'],
    ['titulo', 'text-t', 'Título', 'Frase grande, com um rótulo pequeno em cima'],
    ['texto', 'text-align-left', 'Texto', 'Parágrafos de explicação'],
    ['foto', 'image', 'Foto', 'Uma foto no formato do bloco'],
    ['botao', 'cursor-click', 'Botão', 'WhatsApp, um link e o que o sistema tiver'],
    ['carrossel', 'slideshow', 'Carrossel de fotos', 'Várias fotos que passam com as setas'],
    ['galeria', 'squares-four', 'Galeria', 'Grade de fotos que ampliam no toque'],
    ['lista', 'list-checks', 'Lista com ✓', 'Diferenciais, o que está incluso'],
    ['faq', 'question', 'Perguntas frequentes', 'Pergunta que abre a resposta'],
    ['video', 'play', 'Vídeo do YouTube', 'Cola o link do vídeo'],
    ['citacao', 'quotes', 'Frase em destaque', 'Depoimento ou frase marcante'],
    ['divisor', 'minus', 'Linha divisória', 'Separa partes da coluna'],
    ['espaco', 'arrows-vertical', 'Espaço', 'Um respiro entre os elementos']];
  var NOMES = {}, ICONE_EL = {};
  ELEMENTOS.forEach(function (x) { NOMES[x[0]] = x[2]; ICONE_EL[x[0]] = x[1]; });
  var FUNDOS = { auto: 'Fundo automático', claro: 'Fundo claro', cor: 'Fundo na cor da marca' };
  var PROPORCOES = { deitada: 'Fotos deitadas (4:3)', quadrada: 'Fotos quadradas', larga: 'Fotos largas (16:9)', em_pe: 'Fotos em pé (3:4)' };
  var RAZAO = { deitada: '4/3', quadrada: '1/1', larga: '16/9', em_pe: '3/4' };
  var TAMANHOS = { p: 'Pequeno', m: 'Médio', g: 'Grande' };
  var MAX_BLOCOS = 30, MAX_EL = 12, MAX_FOTOS = 12, MAX_ITENS = 15;

  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function semAcento(t) { return String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function opcoes(mapa, atual) {
    return Object.keys(mapa).map(function (k) { return '<option value="' + k + '"' + (String(k) === String(atual) ? ' selected' : '') + '>' + esc(mapa[k]) + '</option>'; }).join('');
  }
  function mexer(lista, i, passo) { var j = i + passo; if (j < 0 || j >= lista.length) return; lista.splice(j, 0, lista.splice(i, 1)[0]); }
  function novoId() { return 'b' + Math.random().toString(36).slice(2, 9); }

  function editor(caixa, op) {
    var lista = op.blocos || [];
    var galeria = null, aberto = null, painel = null, escolhendo = null, busca = '';
    var acoes = (op.acoes && op.acoes.length ? op.acoes : ['whatsapp', 'link']).filter(function (a) { return ACOES[a]; });
    var secoes = op.secoes || {}, onde = op.onde || 'da página';
    var aviso = op.aviso || function (t) { alert(t); };
    var aoMudar = op.aoMudar || function () {};
    caixa.classList.add('ibe');

    function desenho(nome, estilo) {
      var x = galeria && galeria.filter(function (g) { return g.nome === nome; })[0];
      if (!x) return '';
      if (estilo === 'emoji') return '<span class="ibe-emoji" aria-hidden="true">' + x.emoji + '</span>';
      return '<svg class="ibe-ic" viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">' + x[estilo === 'preenchido' ? 'preenchido' : 'linha'] + '</svg>';
    }
    function ic(nome) { return desenho(nome, 'linha'); }   // telas internas: sempre de linha
    function noSite(nome) { return desenho(nome, op.estilo ? op.estilo() : 'linha'); }
    if (op.icones) op.icones().then(function (g) { galeria = g.icones || g; redesenhar(); }).catch(function () { galeria = []; redesenhar(); });

    function botao(html, rotulo, aoClicar, classe) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'ibe-bt' + (classe ? ' ' + classe : '');
      b.innerHTML = html; if (rotulo) { b.setAttribute('aria-label', rotulo); b.title = rotulo; }
      b.onclick = aoClicar; return b;
    }
    function mudou() { redesenhar(); aoMudar(true); }
    function ordem(lst, i, nome) {
      var c = document.createElement('span'); c.className = 'ibe-ordem';
      var sobe = botao(ic('arrow-up') || '↑', 'Subir', function () { mexer(lst, i, -1); mudou(); });
      var desce = botao(ic('arrow-down') || '↓', 'Descer', function () { mexer(lst, i, 1); mudou(); });
      var tira = botao(ic('trash') || '✕', 'Apagar', function () { if (confirm('Tirar ' + nome + ' ' + onde + '?')) { lst.splice(i, 1); mudou(); } });
      sobe.disabled = i === 0; desce.disabled = i === lst.length - 1;
      c.append(sobe, desce, tira); return c;
    }
    function campo(rotulo, html, aoMudarCampo) {
      var l = document.createElement('label'); l.className = 'ibe-campo'; l.innerHTML = '<span>' + esc(rotulo) + '</span>' + html;
      var c = l.querySelector('input, textarea, select');
      c.addEventListener(c.tagName === 'SELECT' ? 'change' : 'input', function () { aoMudarCampo(c.value); aoMudar(false); });
      return l;
    }
    function dica(texto) { var p = document.createElement('p'); p.className = 'ibe-dica'; p.textContent = texto; return p; }
    function novoElemento(tipo) {
      if (tipo === 'botao') return { tipo: tipo, acao: acoes[0], texto: '', link: '' };
      if (tipo === 'espaco') return { tipo: tipo, tamanho: 'm' };
      if (tipo === 'foto') return { tipo: tipo, foto: '' };
      if (tipo === 'carrossel' || tipo === 'galeria') return { tipo: tipo, fotos: [] };
      if (tipo === 'lista') return { tipo: tipo, itens: ['', '', ''] };
      if (tipo === 'faq') return { tipo: tipo, itens: [{ pergunta: '', resposta: '' }] };
      if (tipo === 'video') return { tipo: tipo, video: '' };
      if (tipo === 'citacao') return { tipo: tipo, texto: '', autor: '' };
      if (tipo === 'divisor') return { tipo: tipo };
      if (tipo === 'icone') return { tipo: tipo, icone: '', tamanho: 'm' };
      return { tipo: tipo, texto: '', rotulo: '' };
    }
    function enviar(arquivos, depois, elCaixa) {
      elCaixa.classList.add('ibe-carregando');
      Array.prototype.slice.call(arquivos).reduce(function (p, arq) {
        return p.then(function () { return op.subirFoto(arq).then(depois); });
      }, Promise.resolve()).catch(function (e) { aviso(e.message || String(e)); }).then(function () { mudou(); });
    }
    function escolherFotos(el, varias) {
      var g = document.createElement('div'); g.className = 'ibe-escolher';
      var todas = op.fotos ? op.fotos() : [];
      if (!todas.length) { g.appendChild(dica('Nenhuma foto enviada ainda: use "Enviar".')); return g; }
      todas.forEach(function (chave) {
        var marcada = varias ? el.fotos.indexOf(chave) >= 0 : el.foto === chave;
        var b = botao('<img src="' + esc(op.fotoUrl(chave)) + '" alt="">', marcada ? 'Foto escolhida' : 'Escolher esta foto', function () {
          if (!varias) { el.foto = chave; escolhendo = null; }
          else {
            var i = el.fotos.indexOf(chave);
            if (i >= 0) el.fotos.splice(i, 1); else if (el.fotos.length < MAX_FOTOS) el.fotos.push(chave); else aviso('Até ' + MAX_FOTOS + ' fotos.');
          }
          mudou();
        }, marcada ? 'atual' : '');
        g.appendChild(b);
      });
      return g;
    }
    function editorFoto(el, b) {
      var c = document.createElement('div'); c.className = 'ibe-foto';
      c.innerHTML = el.foto ? '<img src="' + esc(op.fotoUrl(el.foto)) + '" alt="" style="aspect-ratio:' + RAZAO[b.proporcao] + '">' : '<span class="ibe-dica">Nenhuma foto escolhida</span>';
      var acoesF = document.createElement('div'); acoesF.className = 'ibe-acoes';
      acoesF.appendChild(botao(ic('image') + 'Escolher foto', '', function () { escolhendo = escolhendo === el ? null : el; redesenhar(); }));
      var envia = document.createElement('label'); envia.className = 'ibe-bt';
      envia.innerHTML = ic('upload-simple') + 'Enviar nova<input type="file" accept="image/*" hidden>';
      envia.querySelector('input').onchange = function () { var arqs = this.files; enviar(arqs, function (ch) { el.foto = ch; escolhendo = null; }, c); };
      acoesF.appendChild(envia); c.appendChild(acoesF);
      if (escolhendo === el) c.appendChild(escolherFotos(el, false));
      c.appendChild(dica('A foto se ajusta sozinha ao formato do bloco (' + PROPORCOES[b.proporcao].toLowerCase() + ').'));
      return c;
    }
    function editorFotos(el, b) {
      var c = document.createElement('div'); c.className = 'ibe-fotos';
      var lst = document.createElement('div'); lst.className = 'ibe-escolhidas';
      el.fotos.forEach(function (chave, k) {
        var f = document.createElement('div'); f.className = 'ibe-mini';
        f.innerHTML = '<img src="' + esc(op.fotoUrl(chave)) + '" alt="">';
        var m = document.createElement('div'); m.className = 'ibe-mini-bts';
        m.append(botao('←', 'Para trás', function () { mexer(el.fotos, k, -1); mudou(); }),
          botao('✕', 'Tirar', function () { el.fotos.splice(k, 1); mudou(); }),
          botao('→', 'Para a frente', function () { mexer(el.fotos, k, 1); mudou(); }));
        f.appendChild(m); lst.appendChild(f);
      });
      if (!el.fotos.length) lst.appendChild(dica('Nenhuma foto ainda.'));
      c.appendChild(lst);
      var acoesF = document.createElement('div'); acoesF.className = 'ibe-acoes';
      acoesF.appendChild(botao(ic('image') + 'Escolher fotos', '', function () { escolhendo = escolhendo === el ? null : el; redesenhar(); }));
      var envia = document.createElement('label'); envia.className = 'ibe-bt';
      envia.innerHTML = ic('upload-simple') + 'Enviar novas<input type="file" accept="image/*" multiple hidden>';
      envia.querySelector('input').onchange = function () { enviar(this.files, function (ch) { if (el.fotos.length < MAX_FOTOS) el.fotos.push(ch); }, c); };
      acoesF.appendChild(envia); c.appendChild(acoesF);
      if (escolhendo === el) c.appendChild(escolherFotos(el, true));
      c.appendChild(dica('Até ' + MAX_FOTOS + ' fotos. Todas ficam no formato do bloco (' + PROPORCOES[b.proporcao].toLowerCase() + ').'));
      return c;
    }
    function editorIcone(el) {
      var c = document.createElement('div'); c.className = 'ibe-icone';
      if (!galeria) { c.appendChild(dica('Carregando os ícones…')); return c; }
      var atual = document.createElement('div'); atual.className = 'ibe-icone-atual';
      atual.innerHTML = el.icone ? '<span class="ibe-bola">' + noSite(el.icone) + '</span>' : '<span class="ibe-dica">Nenhum ícone escolhido</span>';
      atual.appendChild(botao(escolhendo === el ? ic('x') + 'Fechar a galeria' : ic('star') + 'Escolher ícone', '', function () { escolhendo = escolhendo === el ? null : el; redesenhar(); }));
      c.appendChild(atual);
      c.appendChild(campo('Tamanho', '<select>' + opcoes(TAMANHOS, el.tamanho) + '</select>', function (v) { el.tamanho = v; }));
      if (escolhendo === el) {
        var procura = document.createElement('input'); procura.type = 'search'; procura.className = 'ibe-busca';
        procura.placeholder = 'Procurar: corte, café, pix, wi-fi…'; procura.value = busca;
        var grade = document.createElement('div'); grade.className = 'ibe-grade-icones';
        var desenhar = function () {
          var q = semAcento(procura.value.trim()); grade.innerHTML = '';
          galeria.filter(function (x) { return !q || semAcento(x.rotulo + ' ' + x.nome).indexOf(q) >= 0; }).forEach(function (x) {
            grade.appendChild(botao(noSite(x.nome) + '<small>' + esc(x.rotulo.split(' ')[0]) + '</small>', x.rotulo, function () {
              el.icone = x.nome; escolhendo = null; busca = ''; mudou(); }, x.nome === el.icone ? 'atual' : ''));
          });
          if (!grade.children.length) grade.appendChild(dica('Nenhum ícone com esse nome.'));
        };
        procura.addEventListener('input', function (ev) { ev.stopPropagation(); busca = procura.value; desenhar(); });
        c.append(procura, grade); desenhar();
      }
      return c;
    }
    function editorElemento(el, col, j, b) {
      var d = document.createElement('div'); d.className = 'ibe-el';
      var topo = document.createElement('div'); topo.className = 'ibe-topo';
      topo.innerHTML = '<b>' + ic(ICONE_EL[el.tipo]) + esc(NOMES[el.tipo]) + '</b>';
      topo.appendChild(ordem(col, j, 'este elemento (' + NOMES[el.tipo].toLowerCase() + ')'));
      d.appendChild(topo);
      if (el.tipo === 'titulo') {
        d.appendChild(campo('Rótulo pequeno em cima (opcional)', '<input maxlength="60" value="' + esc(el.rotulo || '') + '" placeholder="Ex.: Novidade">', function (v) { el.rotulo = v; }));
        d.appendChild(campo('Título', '<input maxlength="120" value="' + esc(el.texto || '') + '" placeholder="Ex.: Conheça {nome}">', function (v) { el.texto = v; }));
      } else if (el.tipo === 'texto') {
        d.appendChild(campo('Texto (linha em branco = novo parágrafo)', '<textarea rows="4" maxlength="1500">' + esc(el.texto || '') + '</textarea>', function (v) { el.texto = v; }));
      } else if (el.tipo === 'foto') {
        d.appendChild(editorFoto(el, b));
      } else if (el.tipo === 'botao') {
        var mapa = {}; acoes.forEach(function (a) { mapa[a] = ACOES[a]; });
        d.appendChild(campo('O botão leva para', '<select>' + opcoes(mapa, el.acao) + '</select>', function (v) { el.acao = v; redesenhar(); }));
        d.appendChild(campo('Texto do botão (vazio = o padrão)', '<input maxlength="60" value="' + esc(el.texto || '') + '">', function (v) { el.texto = v; }));
        if (el.acao === 'link') d.appendChild(campo('Link', '<input maxlength="300" inputmode="url" value="' + esc(el.link || '') + '" placeholder="https://...">', function (v) { el.link = v; }));
      } else if (el.tipo === 'espaco') {
        d.appendChild(campo('Tamanho', '<select>' + opcoes(TAMANHOS, el.tamanho) + '</select>', function (v) { el.tamanho = v; }));
      } else if (el.tipo === 'carrossel' || el.tipo === 'galeria') {
        d.appendChild(editorFotos(el, b));
      } else if (el.tipo === 'lista') {
        d.appendChild(campo('Um item por linha (até ' + MAX_ITENS + ')', '<textarea rows="4">' + esc((el.itens || []).join('\n')) + '</textarea>', function (v) { el.itens = v.split('\n').slice(0, MAX_ITENS); }));
      } else if (el.tipo === 'faq') {
        el.itens.forEach(function (it, k) {
          var q = document.createElement('div'); q.className = 'ibe-faq';
          q.appendChild(campo('Pergunta ' + (k + 1), '<input maxlength="160" value="' + esc(it.pergunta) + '">', function (v) { it.pergunta = v; }));
          q.appendChild(campo('Resposta', '<textarea rows="2" maxlength="800">' + esc(it.resposta) + '</textarea>', function (v) { it.resposta = v; }));
          q.appendChild(botao(ic('x') + 'Tirar esta pergunta', '', function () { el.itens.splice(k, 1); mudou(); }));
          d.appendChild(q);
        });
        var mais = botao(ic('plus') + 'Pergunta', '', function () { el.itens.push({ pergunta: '', resposta: '' }); mudou(); });
        mais.disabled = el.itens.length >= MAX_ITENS; d.appendChild(mais);
      } else if (el.tipo === 'video') {
        d.appendChild(campo('Link do vídeo no YouTube', '<input inputmode="url" maxlength="300" value="' + esc(el.video ? (el.video.length === 11 ? 'https://youtu.be/' + el.video : el.video) : '') + '" placeholder="https://youtu.be/...">', function (v) { el.video = v; }));
        d.appendChild(dica('O vídeo fica sempre deitado (16:9) e só carrega quando a pessoa toca no play.'));
      } else if (el.tipo === 'citacao') {
        d.appendChild(campo('Frase', '<textarea rows="3" maxlength="800">' + esc(el.texto || '') + '</textarea>', function (v) { el.texto = v; }));
        d.appendChild(campo('Quem disse (opcional)', '<input maxlength="60" value="' + esc(el.autor || '') + '">', function (v) { el.autor = v; }));
      } else if (el.tipo === 'icone') {
        d.appendChild(editorIcone(el));
      } else if (el.tipo === 'divisor') {
        d.appendChild(dica('Uma linha fina na largura da coluna.'));
      }
      return d;
    }
    function editorLivre(b, card) {
      var ajustes = document.createElement('div'); ajustes.className = 'ibe-ajustes';
      ajustes.appendChild(campo('Colunas', '<select>' + opcoes({ 1: '1 coluna', 2: '2 colunas', 3: '3 colunas' }, b.colunas) + '</select>', function (v) {
        var n = Number(v);
        while (b.itens.length < n) b.itens.push([]);
        if (b.itens.length > n) { var sobra = [].concat.apply([], b.itens.splice(n)); b.itens[n - 1] = b.itens[n - 1].concat(sobra); }
        b.colunas = n; redesenhar();
      }));
      ajustes.appendChild(campo('Fundo', '<select>' + opcoes(FUNDOS, b.fundo) + '</select>', function (v) { b.fundo = v; }));
      ajustes.appendChild(campo('Formato das fotos', '<select>' + opcoes(PROPORCOES, b.proporcao) + '</select>', function (v) { b.proporcao = v; redesenhar(); }));
      ajustes.appendChild(campo('Alinhamento', '<select>' + opcoes({ esquerda: 'Texto à esquerda', centro: 'Texto no centro' }, b.alinhamento) + '</select>', function (v) { b.alinhamento = v; }));
      card.appendChild(ajustes);
      var cols = document.createElement('div'); cols.className = 'ibe-colunas n' + b.colunas;
      b.itens.forEach(function (col, c) {
        var ce = document.createElement('div'); ce.className = 'ibe-coluna';
        if (b.colunas > 1) ce.innerHTML = '<div class="ibe-grupo">Coluna ' + (c + 1) + '</div>';
        col.forEach(function (el, j) { ce.appendChild(editorElemento(el, col, j, b)); });
        ce.appendChild(botao(painel === col ? ic('x') + 'Fechar a lista' : ic('plus') + 'Elemento', '', function () { painel = painel === col ? null : col; redesenhar(); }, 'ibe-add-el'));
        if (painel === col) {
          var p = document.createElement('div'); p.className = 'ibe-painel';
          ELEMENTOS.forEach(function (x) {
            p.appendChild(botao('<span class="ibe-cartao-ic">' + ic(x[1]) + '</span><b>' + esc(x[2]) + '</b><small>' + esc(x[3]) + '</small>', '', function () {
              if (col.length >= MAX_EL) { aviso('Até ' + MAX_EL + ' elementos em cada coluna.'); return; }
              var novo = novoElemento(x[0]); col.push(novo); painel = null;
              if (x[0] === 'foto' || x[0] === 'carrossel' || x[0] === 'galeria' || x[0] === 'icone') escolhendo = novo;
              mudou();
            }, 'ibe-cartao'));
          });
          ce.appendChild(p);
        }
        cols.appendChild(ce);
      });
      card.appendChild(cols);
    }
    function resumo(b) {
      var primeiro = [].concat.apply([], b.itens).filter(function (el) { return el.texto; })[0];
      return b.colunas + (b.colunas > 1 ? ' colunas' : ' coluna') + ' · ' + FUNDOS[b.fundo].toLowerCase() +
        (primeiro ? ' · “' + primeiro.texto.slice(0, 50) + '”' : ' · ainda vazio');
    }
    function redesenhar() {
      caixa.innerHTML = '';
      lista.forEach(function (b, i) {
        var s = b.tipo === 'secao' ? secoes[b.secao] || { nome: b.secao } : null;
        var card = document.createElement('div'); card.className = 'ibe-bloco' + (s ? '' : ' livre');
        var topo = document.createElement('div'); topo.className = 'ibe-topo';
        topo.innerHTML = '<b>' + (i + 1) + '. ' + (s ? ic(s.icone || 'squares-four') + esc(s.nome) + ' <span class="ibe-detalhe">· seção pronta</span>'
          : ic('columns') + 'Bloco livre') + '</b>';
        if (!s) topo.appendChild(botao(aberto === b.id ? ic('x') + 'Fechar' : ic('pencil-simple') + 'Editar', '', function () {
          aberto = aberto === b.id ? null : b.id; escolhendo = null; redesenhar(); }));
        topo.appendChild(ordem(lista, i, s ? 'a seção ' + s.nome : 'este bloco'));
        card.appendChild(topo);
        if (s) {
          if (s.dica) card.appendChild(dica(s.dica));
          if (s.extra) { var x = s.extra(b, card); if (x) card.appendChild(x); }
        } else if (aberto === b.id) editorLivre(b, card);
        else card.appendChild(dica(resumo(b)));
        caixa.appendChild(card);
      });
      var add = document.createElement('div'); add.className = 'ibe-add';
      add.innerHTML = '<b>' + ic('plus-circle') + 'Adicionar bloco</b>';
      var bts = document.createElement('div'); bts.className = 'ibe-acoes';
      [1, 2, 3].forEach(function (n) {
        bts.appendChild(botao(ic('columns') + n + (n > 1 ? ' colunas' : ' coluna'), '', function () {
          if (lista.length >= MAX_BLOCOS) { aviso('Até ' + MAX_BLOCOS + ' blocos.'); return; }
          var itens = [];
          for (var c = 0; c < n; c++) itens.push([{ tipo: 'titulo', texto: '', rotulo: '' }, { tipo: 'texto', texto: '' }]);
          lista.push({ id: aberto = novoId(), tipo: 'livre', colunas: n, fundo: 'auto', proporcao: 'deitada', alinhamento: n > 1 ? 'centro' : 'esquerda', itens: itens });
          mudou();
        }));
      });
      Object.keys(secoes).filter(function (id) { return !lista.some(function (b) { return b.secao === id; }); }).forEach(function (id) {
        bts.appendChild(botao(ic(secoes[id].icone || 'squares-four') + esc(secoes[id].nome), '', function () {
          lista.push({ id: id, tipo: 'secao', secao: id }); mudou(); }));
      });
      add.appendChild(bts);
      caixa.appendChild(add);
    }
    redesenhar();
    return { redesenhar: redesenhar, blocos: function () { return lista; }, trocar: function (nova) { lista = nova; aberto = null; escolhendo = null; painel = null; redesenhar(); } };
  }
  window.InjexBlocos = window.InjexBlocos || {};
  window.InjexBlocos.editor = editor;
})();
