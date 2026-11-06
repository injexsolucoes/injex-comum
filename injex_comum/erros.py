"""🚨 Erros com a origem — módulo comum (dona, 01/11/2026: "alerta de erros e suas origens"; "cada um é um módulo e
quando a gente faz um sistema novo só adiciona").

Todo erro inesperado do servidor (o que viraria "Internal Server Error") e das telas (JavaScript no navegador) fica
guardado num arquivo SQLite próprio (fora do banco do sistema e do backup): QUANDO, ONDE (tela/rota), QUEM estava
usando, a ORIGEM (arquivo:linha do código do sistema) e a mensagem. O mesmo erro (mesmo tipo + origem + rota) é uma
linha só, com "vezes". Erro NOVO (ou que voltou depois de marcado como resolvido) fica marcado para avisar (e-mail).
Nunca guarda senha, código pessoal nem o corpo do pedido: só o caminho, a mensagem e a pilha do código.

Como um sistema liga (FastAPI):

    from injex_comum import erros
    REGISTRO = erros.Registro(lambda: PASTA_DADOS / "erros.db", raiz=PASTA_DO_CODIGO, sistema="Minha Loja",
                              onde_ver="Configurações › 🚨 Erros")
    ...  # depois de TODOS os outros middlewares (o de erros tem que ser o de fora):
    erros.instalar(app, REGISTRO, eh_admin=<dependência que devolve True/False>, quem_e=<request -> nome>)
    ...  # no lifespan: asyncio.create_task(erros.vigiar_avisos(REGISTRO, <função que devolve (remetente, senha, destino)>))

E em cada página, ANTES dos outros scripts:  <script src="/comum/erros.js"></script>
(a tela manda para /api/erros/tela; outro endereço: <script src="/comum/erros.js" data-endereco="/api/x/tela">).
"""

import asyncio
import hashlib
import re
import sqlite3
import threading
import time
import traceback
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ESTATICO = Path(__file__).with_name("estatico")
MAX_LINHAS = 500  # erros diferentes guardados (os mais antigos saem)
MENSAGEM = ("Deu um erro inesperado no sistema (código {codigo}). O administrador já foi avisado. "
            "Se precisar, tire um print e mande para o administrador.")


def navegador_de(agente):
    """Resumo do navegador/aparelho (sem o texto inteiro do User-Agent)."""
    a = agente or ""
    nav = next((n for n, m in (("Edge", "Edg/"), ("Chrome", "Chrome/"), ("Firefox", "Firefox/"), ("Safari", "Safari/"))
                if m in a), "")
    so = next((n for n, m in (("Android", "Android"), ("iPhone", "iPhone"), ("Windows", "Windows"), ("Mac", "Mac OS"),
                              ("Linux", "Linux")) if m in a), "")
    return " · ".join(x for x in (nav, so) if x) or a[:60]


def _limpar(texto, tamanho):
    return re.sub(r"\s+", " ", str(texto or "")).strip()[:tamanho]


def _rota(caminho):
    """/api/vendas/123/pdf → /api/vendas/#/pdf (o mesmo erro em vendas diferentes é um só)."""
    return "/".join("#" if parte.isdigit() else parte for parte in caminho.split("/"))


class Registro:
    """O registro de erros de UM sistema. `arquivo`: caminho do .db (ou função que devolve o caminho, para quando a
    pasta de dados muda nos testes). `raiz`: pasta do código do sistema (a origem aparece como "app/caixa.py:120")."""

    def __init__(self, arquivo, raiz, sistema="Sistema", onde_ver="🚨 Erros"):
        self._arquivo = arquivo
        self.raiz = Path(raiz).resolve()
        self.sistema = sistema
        self.onde_ver = onde_ver
        self._trava = threading.Lock()

    # ---------- arquivo ----------
    @property
    def arquivo(self):
        return Path(self._arquivo() if callable(self._arquivo) else self._arquivo)

    @contextmanager
    def _abrir(self):
        with self._trava:
            self.arquivo.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(self.arquivo, timeout=10)
            con.row_factory = sqlite3.Row
            try:
                con.execute("""CREATE TABLE IF NOT EXISTS erros (
                    chave TEXT PRIMARY KEY, onde TEXT NOT NULL, tipo TEXT NOT NULL, mensagem TEXT NOT NULL,
                    origem TEXT NOT NULL, pilha TEXT NOT NULL, rota TEXT NOT NULL, tela TEXT NOT NULL,
                    usuario TEXT NOT NULL, navegador TEXT NOT NULL, primeira TEXT NOT NULL, ultima TEXT NOT NULL,
                    vezes INTEGER NOT NULL, resolvido INTEGER NOT NULL DEFAULT 0, avisar INTEGER NOT NULL DEFAULT 0)""")
                yield con
                con.commit()
            finally:
                con.close()

    # ---------- origem ----------
    def _relativo(self, arquivo):
        try:
            return Path(arquivo).resolve().relative_to(self.raiz).as_posix()
        except ValueError:
            return Path(arquivo).name

    def _do_sistema(self, arquivo):
        """Código do próprio sistema: dentro da raiz e fora das bibliotecas e dos testes."""
        caminho = Path(arquivo).resolve()
        if not caminho.is_relative_to(self.raiz):
            return False
        return not {"site-packages", ".venv", "venv", "testes", "tests"} & set(caminho.relative_to(self.raiz).parts)

    def origem_da_excecao(self, e):
        """(origem, pilha): origem = a ÚLTIMA linha do código DO SISTEMA por onde o erro passou (senão a última de
        todas, de uma biblioteca). A pilha mostra só as 8 últimas passagens, em texto curto."""
        quadros = traceback.extract_tb(e.__traceback__)
        nossos = [q for q in quadros if self._do_sistema(q.filename)]
        alvo = (nossos or quadros or [None])[-1]
        origem = f"{self._relativo(alvo.filename)}:{alvo.lineno} em {alvo.name}()" if alvo else "(desconhecida)"
        pilha = "\n".join(f"{self._relativo(q.filename)}:{q.lineno} em {q.name}() → {(q.line or '').strip()[:160]}"
                          for q in quadros[-8:])
        return origem, pilha

    # ---------- gravar ----------
    def registrar(self, onde, tipo, mensagem, origem, pilha="", rota="", tela="", navegador="", usuario=""):
        """Guarda (ou soma) um erro. Devolve {"chave", "novo"}; novo = 1ª vez ou voltou depois de resolvido."""
        onde = "tela" if onde == "tela" else "servidor"
        tipo, origem, rota = _limpar(tipo, 80) or "Erro", _limpar(origem, 200) or "(desconhecida)", _limpar(_rota(rota), 200)
        mensagem = _limpar(mensagem, 500)
        # mensagem sem números (ids, valores) para o mesmo erro não virar vários
        chave = hashlib.sha1(f"{onde}|{tipo}|{origem}|{rota if onde == 'servidor' else ''}|"
                             f"{re.sub(r'[0-9]+', '#', mensagem)[:120]}".encode()).hexdigest()[:12]
        agora = datetime.now().isoformat(timespec="seconds")
        usuario, tela, navegador = _limpar(usuario, 60), _limpar(tela, 200), _limpar(navegador, 120)
        with self._abrir() as con:
            r = con.execute("SELECT resolvido FROM erros WHERE chave = ?", (chave,)).fetchone()
            novo = r is None or bool(r["resolvido"])
            if r is None:
                con.execute("INSERT INTO erros VALUES (?,?,?,?,?,?,?,?,?,?,?,?,1,0,1)",
                            (chave, onde, tipo, mensagem, origem, pilha[:4000], rota, tela, usuario, navegador, agora, agora))
                con.execute("DELETE FROM erros WHERE chave IN "
                            "(SELECT chave FROM erros ORDER BY ultima DESC LIMIT -1 OFFSET ?)", (MAX_LINHAS,))
            else:
                con.execute("""UPDATE erros SET vezes = vezes + 1, ultima = ?, mensagem = ?, pilha = ?, usuario = ?,
                               tela = ?, navegador = ?, resolvido = 0,
                               avisar = CASE WHEN resolvido = 1 THEN 1 ELSE avisar END WHERE chave = ?""",
                            (agora, mensagem, pilha[:4000], usuario, tela, navegador, chave))
        return {"chave": chave, "novo": novo}

    def registrar_excecao(self, e, metodo, caminho, usuario="", navegador=""):
        origem, pilha = self.origem_da_excecao(e)
        return self.registrar("servidor", type(e).__name__, str(e) or type(e).__name__, origem, pilha,
                              f"{metodo} {caminho}", navegador=navegador, usuario=usuario)

    # ---------- ler ----------
    def lista(self, resolvidos=False):
        with self._abrir() as con:
            return [dict(r) for r in con.execute("SELECT * FROM erros WHERE resolvido = ? ORDER BY ultima DESC",
                                                 (int(resolvidos),))]

    def resumo(self):
        """Para o Início do administrador: quantos em aberto, quantos novos hoje e quantos aconteceram hoje."""
        hoje = datetime.now().date().isoformat()
        with self._abrir() as con:
            r = con.execute("SELECT COUNT(*) AS abertos, SUM(primeira >= ?) AS novos_hoje, SUM(ultima >= ?) AS hoje "
                            "FROM erros WHERE resolvido = 0", (hoje, hoje)).fetchone()
        return {"abertos": r["abertos"] or 0, "novos_hoje": r["novos_hoje"] or 0, "hoje": r["hoje"] or 0}

    def marcar_resolvido(self, chave, resolvido=True):
        with self._abrir() as con:
            return con.execute("UPDATE erros SET resolvido = ?, avisar = 0 WHERE chave = ?",
                               (int(resolvido), chave)).rowcount > 0

    # ---------- avisar ----------
    def para_avisar(self):
        with self._abrir() as con:
            return [dict(r) for r in con.execute("SELECT * FROM erros WHERE avisar = 1 ORDER BY primeira")]

    def avisados(self, chaves):
        with self._abrir() as con:
            con.executemany("UPDATE erros SET avisar = 0 WHERE chave = ?", [(c,) for c in chaves])

    def texto_do_email(self, itens):
        partes = [f"O {self.sistema} teve {len(itens)} erro(s) novo(s). Veja em {self.onde_ver}.\n"]
        for e in itens:
            partes.append(f"• {e['tipo']}: {e['mensagem']}\n  Onde: {e['onde']} · {e['rota'] or e['tela']}\n"
                          f"  Origem: {e['origem']}\n  Quem: {e['usuario'] or '(ninguém logado)'} · {e['ultima']} · "
                          f"{e['vezes']} vez(es)\n")
        partes.append("Mande este e-mail para o responsável corrigir (a correção começa por um teste que repete o erro).")
        return "\n".join(partes)

    def enviar_avisos(self, remetente, senha, destino):
        """UM e-mail (Gmail, senha de app) com os erros novos. Sem e-mail configurado: não manda (tenta depois).
        Devolve quantos avisou."""
        import smtplib
        from email.message import EmailMessage
        itens = self.para_avisar()
        if not itens or not (remetente and senha and destino):
            return 0
        msg = EmailMessage()
        msg["Subject"] = f"🚨 {self.sistema} · {len(itens)} erro(s) novo(s)"
        msg["From"], msg["To"] = remetente, destino
        msg.set_content(self.texto_do_email(itens))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
            smtp.login(remetente, senha.replace(" ", ""))
            smtp.send_message(msg)
        self.avisados([e["chave"] for e in itens])
        return len(itens)


def arquivo_js(nome="erros.js"):
    """erros.js = o vigia das telas; erros-painel.js = o quadro "Erros do sistema" (o sistema serve em /comum/<nome>)."""
    if nome not in ("erros.js", "erros-painel.js"):
        raise KeyError(nome)
    return (ESTATICO / nome).read_text(encoding="utf-8")


async def vigiar_avisos(registro, config_email, intervalo=300):
    """Para o lifespan: a cada 5 min manda UM e-mail com os erros novos. `config_email()` devolve
    (remetente, senha, destino) — roda numa thread (pode ler o banco do sistema). Nunca derruba o sistema."""
    while True:
        await asyncio.sleep(intervalo)
        try:
            n = await asyncio.to_thread(lambda: registro.enviar_avisos(*config_email()))
            if n:
                print(f"[erros] e-mail com {n} erro(s) novo(s) enviado")
        except Exception as e:
            print("Aviso: falha ao mandar o e-mail dos erros:", e)


def instalar(app, registro, eh_admin, quem_e=None, prefixo="/api/erros", servir_js=True, mensagem=MENSAGEM,
             por_minuto=30):
    """Liga o módulo num app FastAPI:
    - middleware que pega o erro inesperado → registra com a origem → a tela recebe 500 com `mensagem` e o código
      (chamar DEPOIS de todos os outros middlewares: este tem que ser o de fora);
    - GET {prefixo} (lista; ?resolvidos=true), GET {prefixo}/resumo (não admin recebe zeros),
      POST {prefixo}/{chave}/resolvido {"resolvido": bool}, POST {prefixo}/tela (aberto, `por_minuto` por endereço);
    - GET /comum/erros.js e /comum/erros-painel.js (servir_js=False se o sistema já serve /comum/<arquivo>).
    `eh_admin`: dependência do FastAPI que devolve True/False (e recusa quem não está logado).
    `quem_e(request)`: nome de quem estava logado (roda numa thread, só quando dá erro)."""
    from fastapi import APIRouter, Depends, HTTPException, Request
    from fastapi.responses import JSONResponse, Response
    from pydantic import BaseModel

    async def _quem(request):
        if not quem_e:
            return ""
        try:
            return await asyncio.to_thread(quem_e, request) or ""
        except Exception:
            return ""

    @app.middleware("http")
    async def pegar_erros(request: Request, chamar_proximo):
        try:
            return await chamar_proximo(request)
        except Exception as e:
            try:
                r = await asyncio.to_thread(registro.registrar_excecao, e, request.method, request.url.path,
                                            await _quem(request), navegador_de(request.headers.get("user-agent", "")))
                codigo = r["chave"][:6].upper()
            except Exception as falha:  # o registro nunca pode esconder o erro de verdade
                print("Aviso: não consegui registrar o erro:", falha)
                codigo = "?"
            print(f"[erro {codigo}] {request.method} {request.url.path}: {type(e).__name__}: {e}")
            return JSONResponse({"detail": mensagem.format(codigo=codigo)}, status_code=500)

    rotas = APIRouter(prefix=prefixo)

    def _so_admin(admin: bool = Depends(eh_admin)):
        if not admin:
            raise HTTPException(403, "Só o administrador vê os erros do sistema.")

    @rotas.get("", dependencies=[Depends(_so_admin)])
    async def ver(resolvidos: bool = False):
        return {"erros": await asyncio.to_thread(registro.lista, resolvidos),
                "resumo": await asyncio.to_thread(registro.resumo)}

    @rotas.get("/resumo")
    async def resumo(admin: bool = Depends(eh_admin)):
        return await asyncio.to_thread(registro.resumo) if admin else {"abertos": 0, "novos_hoje": 0, "hoje": 0}

    class Resolvido(BaseModel):
        resolvido: bool = True

    class ErroDaTela(BaseModel):
        mensagem: str = ""
        arquivo: str = ""
        linha: int = 0
        coluna: int = 0
        pilha: str = ""
        tela: str = ""

    fila_por_ip = defaultdict(lambda: deque(maxlen=por_minuto))

    @rotas.post("/tela")
    async def erro_da_tela(dados: ErroDaTela, request: Request):
        ip = request.client.host if request.client else "?"
        fila, agora = fila_por_ip[ip], time.monotonic()
        if len(fila) == fila.maxlen and agora - fila[0] < 60:
            return {"ok": False}
        fila.append(agora)
        arquivo = dados.arquivo.split("?")[0]
        if "/static/" in arquivo or "/comum/" in arquivo:
            arquivo = arquivo[arquivo.find("/static/") if "/static/" in arquivo else arquivo.find("/comum/"):]
        else:
            arquivo = arquivo.rsplit("/", 1)[-1]
        origem = f"{arquivo or '(na própria página)'}:{dados.linha}" + (f":{dados.coluna}" if dados.coluna else "")
        r = await asyncio.to_thread(registro.registrar, "tela", "Erro na tela", dados.mensagem[:500], origem,
                                    dados.pilha[:3000], tela=dados.tela.split("?")[0][:200],
                                    navegador=navegador_de(request.headers.get("user-agent", "")),
                                    usuario=await _quem(request))
        return {"ok": True, "codigo": r["chave"][:6].upper()}

    @rotas.post("/{chave}/resolvido", dependencies=[Depends(_so_admin)])
    async def marcar(chave: str, dados: Resolvido):
        if not await asyncio.to_thread(registro.marcar_resolvido, chave, dados.resolvido):
            raise HTTPException(404, "Erro não encontrado.")
        return {"ok": True}

    rotas.limpar_limite = fila_por_ip.clear  # para os testes
    app.include_router(rotas)
    if servir_js:
        for nome in ("erros.js", "erros-painel.js"):
            def js(nome=nome):
                return Response(arquivo_js(nome), media_type="text/javascript", headers={"Cache-Control": "no-cache"})
            app.add_api_route(f"/comum/{nome}", js, methods=["GET"], include_in_schema=False)
    return rotas
