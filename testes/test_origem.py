"""🛡️ Conferência de origem (CSRF), 02/11/2026."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from injex_comum import origem


def _cliente(**kw):
    app = FastAPI()

    @app.post("/api/vender")
    def vender():
        return {"ok": True}

    @app.get("/api/ver")
    def ver():
        return {"ok": True}
    origem.instalar(app, **kw)
    return TestClient(app, base_url="https://sistema.exemplo.com")


def test_pedido_do_proprio_endereco_passa():
    c = _cliente()
    assert c.post("/api/vender", headers={"Origin": "https://sistema.exemplo.com"}).status_code == 200
    assert c.post("/api/vender", headers={"Referer": "https://sistema.exemplo.com/venda"}).status_code == 200


def test_pedido_de_outro_site_ou_subdominio_e_recusado():
    c = _cliente()
    for de_fora in ("https://golpe.com", "https://cliente.lojas.exemplo.com", "null"):
        r = c.post("/api/vender", headers={"Origin": de_fora})
        assert r.status_code == 403 and "outra página" in r.json()["detail"], de_fora
    assert c.post("/api/vender", headers={"Referer": "https://golpe.com/x"}).status_code == 403


def test_sem_origem_extensao_leitura_e_aceitos_passam():
    c = _cliente(aceitos=["https://parceiro.com"])
    assert c.post("/api/vender").status_code == 200  # servidor → servidor (avisos de pagamento)
    assert c.post("/api/vender", headers={"Origin": "chrome-extension://abcdef"}).status_code == 200
    assert c.get("/api/ver", headers={"Origin": "https://golpe.com"}).status_code == 200
    assert c.post("/api/vender", headers={"Origin": "https://parceiro.com"}).status_code == 200
