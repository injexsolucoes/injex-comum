"""🛡️ Conferência de origem (contra CSRF) — módulo comum da Injex (02/11/2026).

Um site de fora (ou a página de outro cliente em *.lojas.injexsolucoes.com, que o navegador trata como o "mesmo site")
não consegue fazer o navegador de quem está logado salvar, apagar ou vender no sistema: todo pedido que MUDA algo
(POST/PUT/PATCH/DELETE) que chega com o cabeçalho Origin (ou Referer) de OUTRO endereço é recusado (403).

Passam: pedido do próprio endereço; pedido sem Origin e sem Referer (servidor falando com servidor: avisos do Mercado
Pago, Nuvemshop, Central, o aplicativo de monitoramento); extensões do navegador (chrome-extension://, moz-extension://);
e os endereços em `aceitos`. Abrir páginas (GET) nunca é barrado.

    from injex_comum import origem
    origem.instalar(app)                       # antes do erros.instalar (o de erros é o de fora)
"""

from urllib.parse import urlsplit

METODOS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
EXTENSOES = ("chrome-extension://", "moz-extension://", "safari-web-extension://")
MENSAGEM = "Pedido recusado: veio de outra página. Abra o sistema pelo endereço dele e tente de novo."


def _host(valor: str) -> str:
    try:
        return (urlsplit(valor).netloc or "").lower()
    except ValueError:
        return ""


class ConferirOrigem:
    def __init__(self, app, aceitos=()):
        self.app = app
        self.aceitos = {_host(a) or a.lower() for a in aceitos}

    def _permitido(self, cabecalhos) -> bool:
        origem = cabecalhos.get(b"origin", b"").decode("latin-1").strip()
        if not origem:
            origem = cabecalhos.get(b"referer", b"").decode("latin-1").strip()
            if not origem:
                return True  # servidor falando com servidor (sem navegador no meio)
        if origem.startswith(EXTENSOES):
            return True
        host_pedido = cabecalhos.get(b"host", b"").decode("latin-1").strip().lower()
        host_origem = _host(origem)  # "null" (página isolada) → "" → recusa
        return bool(host_origem) and (host_origem == host_pedido or host_origem in self.aceitos)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("method") in METODOS:
            if not self._permitido(dict(scope.get("headers") or [])):
                corpo = ('{"detail": "%s"}' % MENSAGEM).encode()
                await send({"type": "http.response.start", "status": 403,
                            "headers": [(b"content-type", b"application/json; charset=utf-8"),
                                        (b"content-length", str(len(corpo)).encode())]})
                await send({"type": "http.response.body", "body": corpo})
                return
        await self.app(scope, receive, send)


def instalar(app, aceitos=()):
    """Liga a conferência. `aceitos` = outros endereços que podem mandar pedidos (ex.: "https://site.com")."""
    app.add_middleware(ConferirOrigem, aceitos=aceitos)
