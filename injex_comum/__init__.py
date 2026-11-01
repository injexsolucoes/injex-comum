"""Peças comuns a todos os sistemas da Injex Soluções (Agenda, Lojas, Lanchonete, Central…).

Só o que é genérico e igual para todos: a galeria de ícones (`icones`), as páginas legais e o aviso de cookies
(`legal`), pequenas peças de texto (`texto`) o construtor de blocos (`blocos`, com o CSS/JS da tela em estatico/) os erros com a origem + alerta (`erros`, com estatico/erros.js e erros-painel.js), o cofre dos segredos (`cofre`) e o backup trancado (`cripto_backup`). NUNCA dados de cliente, senhas, chaves ou nada de um negócio: os dados de
cada cliente ficam no sistema dele e só passam por aqui na hora de montar uma página.
"""

VERSAO = "1.3.0"
