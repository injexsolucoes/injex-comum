"""🚦 Limite nas rotas abertas (sem login) — módulo comum (02/11/2026): um robô não enche o banco nem derruba o sistema."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from injex_comum import limites


def _app(**kw):
    app = FastAPI()

    @app.post("/api/menu/pedir")
    def pedir(dados: dict):
        return {"ok": True}

    @app.post("/api/menu/outra")
    def outra(dados: dict):
        return {"ok": True}

    @app.get("/api/menu/ver")
    def ver():
        return {"ok": True}

    @app.post("/api/interno")
    def interno(dados: dict):
        return {"ok": True}

    limites.instalar(app, [("/api/menu/pedir", 3), ("/api/menu/", 5)], **kw)
    return app


def test_passou_do_limite_responde_429_com_mensagem_clara():
    c = TestClient(_app())
    assert [c.post("/api/menu/pedir", json={}).status_code for _ in range(4)] == [200, 200, 200, 429]
    r = c.post("/api/menu/pedir", json={})
    assert "Espere um minuto" in r.json()["detail"] and r.headers["retry-after"] == "60"
    # a regra mais específica vem primeiro; as outras rotas do mesmo começo contam separado
    assert [c.post("/api/menu/outra", json={}).status_code for _ in range(6)] == [200] * 5 + [429]


def test_leitura_e_rotas_fora_da_lista_nao_contam():
    c = TestClient(_app())
    assert all(c.get("/api/menu/ver").status_code == 200 for _ in range(20))
    assert all(c.post("/api/interno", json={}).status_code == 200 for _ in range(20))


def test_cada_endereco_tem_a_sua_conta():
    lim = limites.Limitador()
    assert all(lim.pode("1.1.1.1", 2) for _ in range(2)) and not lim.pode("1.1.1.1", 2)
    assert lim.pode("2.2.2.2", 2)


def test_janela_de_um_minuto(monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr(limites.time, "monotonic", lambda: agora[0])
    lim = limites.Limitador()
    assert lim.pode("x", 1) and not lim.pode("x", 1)
    agora[0] += 61
    assert lim.pode("x", 1)


def test_corpo_grande_demais_nas_rotas_abertas_e_recusado():
    c = TestClient(_app(corpo_max=1000))
    r = c.post("/api/menu/outra", content=b'{"a": "' + b"x" * 2000 + b'"}', headers={"content-type": "application/json"})
    assert r.status_code == 413 and "grande" in r.json()["detail"]
    assert c.post("/api/interno", content=b'{"a": "' + b"x" * 2000 + b'"}',
                  headers={"content-type": "application/json"}).status_code == 200  # fora da lista: não mexe


def test_desligado_nos_testes_dos_sistemas(monkeypatch):
    monkeypatch.setenv(limites.DESLIGAR, "1")
    c = TestClient(_app())
    assert all(c.post("/api/menu/pedir", json={}).status_code == 200 for _ in range(10))
