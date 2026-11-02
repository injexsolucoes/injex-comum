"""🚦 Limite nas rotas abertas (sem login) — módulo comum da Injex (02/11/2026).

Rotas que qualquer um chama sem entrar (pedido pelo celular da mesa, carrinho/pedido do site, "receber novidades",
pedir aprovação de aparelho, avisos dos bancos/marketplaces) ganham:
  - um limite de pedidos por minuto POR ENDEREÇO (passou = 429 "Espere um minuto e tente de novo");
  - um tamanho máximo do que mandam (passou = 413), conferido antes de ler tudo.
Só conta quem GRAVA (POST/PUT/PATCH/DELETE); abrir páginas e consultas não conta. Fica na memória (reiniciar zera).

    from injex_comum import limites
    limites.instalar(app, [("/api/menu/pedir", 10), ("/api/menu/", 60)])   # a 1ª regra que bate vale

O endereço é o `request.client` (o uvicorn roda com --proxy-headers atrás do Caddy). Instale ANTES do
`erros.instalar` (o de erros tem que ser o de fora).
"""

import json
import os
import threading
import time
from collections import deque

METODOS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CORPO_MAX = 256 * 1024  # 256 KB: um pedido/formulário de verdade é bem menor
MENSAGEM_LIMITE = "Muitas tentativas seguidas deste aparelho. Espere um minuto e tente de novo."
MENSAGEM_GRANDE = "O que foi enviado é grande demais."
DESLIGAR = "INJEX_LIMITES_DESLIGADOS"  # "1" = sem limite (só os testes dos sistemas, que mandam tudo do mesmo endereço)


class Limitador:
    """Janela de 60 s por chave (endereço + regra). Seguro com várias linhas de execução."""

    def __init__(self, janela: float = 60.0, max_chaves: int = 20000):
        self.janela, self.max_chaves = janela, max_chaves
        self._filas: dict[str, deque] = {}
        self._trava = threading.Lock()

    def pode(self, chave: str, por_minuto: int) -> bool:
        agora = time.monotonic()
        with self._trava:
            fila = self._filas.get(chave)
            if fila is None:
                if len(self._filas) >= self.max_chaves:  # muitos endereços: esquece os parados
                    self._filas = {k: f for k, f in self._filas.items() if f and agora - f[-1] < self.janela}
                fila = self._filas[chave] = deque()
            while fila and agora - fila[0] >= self.janela:
                fila.popleft()
            if len(fila) >= por_minuto:
                return False
            fila.append(agora)
            return True


async def _responder(send, status: int, detalhe: str, extra=()):
    corpo = json.dumps({"detail": detalhe}, ensure_ascii=False).encode()
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json; charset=utf-8"),
                            (b"content-length", str(len(corpo)).encode()), *extra]})
    await send({"type": "http.response.body", "body": corpo})


class _Grande(Exception):
    pass


class LimiteAberto:
    """Middleware ASGI (use `instalar`)."""

    def __init__(self, app, regras, corpo_max=CORPO_MAX, limitador=None):
        self.app = app
        self.regras = [(p, int(n)) for p, n in regras]
        self.corpo_max = corpo_max
        self.limitador = limitador or Limitador()

    def _regra(self, caminho):
        return next(((p, n) for p, n in self.regras if caminho.startswith(p)), None)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method") not in METODOS or os.environ.get(DESLIGAR) == "1":
            return await self.app(scope, receive, send)
        regra = self._regra(scope.get("path", ""))
        if regra is None:
            return await self.app(scope, receive, send)
        prefixo, por_minuto = regra
        cliente = scope.get("client") or ("?", 0)
        if not self.limitador.pode(f"{cliente[0]}|{prefixo}", por_minuto):
            return await _responder(send, 429, MENSAGEM_LIMITE, [(b"retry-after", b"60")])
        cabecalhos = dict(scope.get("headers") or [])
        try:
            tamanho = int(cabecalhos.get(b"content-length", b"0") or 0)
        except ValueError:
            tamanho = 0
        if tamanho > self.corpo_max:
            return await _responder(send, 413, MENSAGEM_GRANDE)
        lido = 0
        comecou = False

        async def receber():
            nonlocal lido
            msg = await receive()
            if msg["type"] == "http.request":
                lido += len(msg.get("body", b""))
                if lido > self.corpo_max:  # sem content-length (em pedaços): conta o que chega
                    raise _Grande()
            return msg

        async def enviar(msg):
            nonlocal comecou
            if msg["type"] == "http.response.start":
                comecou = True
            await send(msg)

        try:
            await self.app(scope, receber, enviar)
        except _Grande:
            if not comecou:
                await _responder(send, 413, MENSAGEM_GRANDE)


def instalar(app, regras, corpo_max: int = CORPO_MAX):
    """Liga o limite nas rotas abertas. `regras` = [(começo do endereço, pedidos por minuto)], a 1ª que bate vale."""
    app.add_middleware(LimiteAberto, regras=regras, corpo_max=corpo_max)
