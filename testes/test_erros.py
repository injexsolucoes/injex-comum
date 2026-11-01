"""🚨 Módulo comum de erros com a origem (injex_comum/erros.py)."""

import pytest
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient

from injex_comum import blocos, erros
from testes.exemplo_app import rotas as exemplo

RAIZ = exemplo.__file__.rsplit("/testes/", 1)[0] + "/testes/exemplo_app"


@pytest.fixture
def sistema(tmp_path):
    registro = erros.Registro(lambda: tmp_path / "erros.db", raiz=RAIZ, sistema="Loja Teste", onde_ver="Config › Erros")
    app = FastAPI()

    def eh_admin(x_quem: str = Header("")):
        return x_quem == "admin"

    @app.get("/api/venda")
    def venda():
        return exemplo.total([{"nome": "caneca"}])

    @app.get("/api/ok")
    def ok():
        return {"ok": True}

    rotas = erros.instalar(app, registro, eh_admin=eh_admin, quem_e=lambda r: r.headers.get("x-quem", ""))
    return registro, TestClient(app), rotas


ADMIN = {"x-quem": "admin"}


def test_erro_do_servidor_com_a_origem_no_codigo_do_sistema(sistema):
    registro, c, _ = sistema
    r = c.get("/api/venda", headers={"x-quem": "Thayna", "user-agent": "Mozilla Chrome/1 Windows"})
    assert r.status_code == 500 and "código" in r.json()["detail"]
    [e] = registro.lista()
    assert e["tipo"] == "KeyError" and e["origem"].startswith("rotas.py:5 em ")
    assert e["rota"] == "GET /api/venda" and e["usuario"] == "Thayna" and e["navegador"] == "Chrome · Windows"
    assert e["chave"][:6].upper() in r.json()["detail"]
    assert c.get("/api/ok").json() == {"ok": True}  # o resto continua normal


def test_mesmo_erro_soma_avisa_uma_vez_e_volta_se_resolvido(sistema):
    registro, c, _ = sistema
    c.get("/api/venda"), c.get("/api/venda")
    [e] = registro.lista()
    assert e["vezes"] == 2 and len(registro.para_avisar()) == 1
    registro.avisados([e["chave"]])
    assert c.post(f"/api/erros/{e['chave']}/resolvido", json={"resolvido": True}, headers=ADMIN).json()["ok"]
    assert registro.lista() == [] and registro.para_avisar() == []
    c.get("/api/venda")
    assert len(registro.lista()) == 1 and len(registro.para_avisar()) == 1


def test_erro_da_tela_e_limite_por_minuto(sistema):
    registro, c, rotas = sistema
    r = c.post("/api/erros/tela", json={"mensagem": "x is not defined", "linha": 12, "coluna": 3, "tela": "/venda?a=1",
                                        "arquivo": "https://loja.com/static/js/venda.js?v=2"}, headers={"x-quem": "Ana"})
    assert r.json()["ok"]
    [e] = registro.lista()
    assert e["onde"] == "tela" and e["origem"] == "/static/js/venda.js:12:3" and e["tela"] == "/venda" and e["usuario"] == "Ana"
    rotas.limpar_limite()
    for n in range(40):
        c.post("/api/erros/tela", json={"mensagem": f"erro {n}", "arquivo": "/comum/a.js", "linha": n})
    assert len(registro.lista()) == 1 + 30


def test_so_o_administrador_ve_e_resolve(sistema):
    registro, c, _ = sistema
    c.get("/api/venda")
    assert c.get("/api/erros").status_code == 403
    assert c.get("/api/erros/resumo").json()["abertos"] == 0
    chave = registro.lista()[0]["chave"]
    assert c.post(f"/api/erros/{chave}/resolvido", json={}).status_code == 403
    d = c.get("/api/erros", headers=ADMIN).json()
    assert d["resumo"] == {"abertos": 1, "novos_hoje": 1, "hoje": 1} and len(d["erros"]) == 1


def test_email_dos_erros_novos(sistema, monkeypatch):
    registro, c, _ = sistema
    c.get("/api/venda")
    enviados = []

    class SMTPFalso:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def login(self, *a): pass
        def send_message(self, msg): enviados.append(msg)

    import smtplib
    monkeypatch.setattr(smtplib, "SMTP_SSL", SMTPFalso)
    assert registro.enviar_avisos("", "", "") == 0  # sem e-mail configurado
    assert registro.enviar_avisos("a@gmail.com", "x x", "b@gmail.com") == 1
    assert registro.enviar_avisos("a@gmail.com", "x", "b@gmail.com") == 0  # não repete
    texto = enviados[0].get_content()
    assert "Loja Teste" in enviados[0]["Subject"] and "rotas.py:" in texto and "Config › Erros" in texto


def test_js_servido_e_na_lista_dos_arquivos_comuns(sistema):
    _, c, _ = sistema
    r = c.get("/comum/erros.js")
    assert r.status_code == 200 and "unhandledrejection" in r.text and r.headers["content-type"].startswith("text/javascript")
    assert "InjexErros" in blocos.arquivo("erros.js")


def test_painel_servido(sistema):
    _, c, _ = sistema
    r = c.get("/comum/erros-painel.js")
    assert r.status_code == 200 and "InjexErrosPainel" in r.text
    assert "InjexErrosPainel" in blocos.arquivo("erros-painel.js")
