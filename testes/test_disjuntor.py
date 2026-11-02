"""🔌 Disjuntor (02/11/2026): serviço de fora caiu → para de insistir uns minutos e avisa na hora."""

import pytest

from injex_comum import disjuntor
from injex_comum.disjuntor import Disjuntor, ForaDoAr


@pytest.fixture
def relogio(monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr(disjuntor.time, "monotonic", lambda: agora[0])
    return agora


def _cai():
    raise ConnectionError("sem resposta")


def test_tres_quedas_seguidas_abre_e_responde_na_hora(relogio):
    d = Disjuntor("SEFAZ-teste", falhas=3, pausa=120)
    for _ in range(3):
        with pytest.raises(ConnectionError):
            d.chamar(_cai)
    chamou = []
    with pytest.raises(ForaDoAr) as e:
        d.chamar(lambda: chamou.append(1))
    assert not chamou and "SEFAZ-teste está fora do ar" in str(e.value) and "2 minutos" in str(e.value)
    assert isinstance(e.value, ConnectionError)  # quem já trata "sem internet" trata este também
    assert d.estado()["fora_do_ar"] is True


def test_passada_a_pausa_testa_uma_vez_e_volta_ao_normal(relogio):
    d = Disjuntor("teste-volta", falhas=2, pausa=60)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            d.chamar(_cai)
    relogio[0] += 61
    assert d.chamar(lambda: "ok") == "ok"
    assert d.estado() == {"nome": "teste-volta", "fora_do_ar": False, "segundos": 0, "falhas_seguidas": 0,
                          "ultimo_erro": ""}


def test_teste_que_falha_abre_de_novo(relogio):
    d = Disjuntor("teste-reabre", falhas=2, pausa=60)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            d.chamar(_cai)
    relogio[0] += 61
    with pytest.raises(ConnectionError):
        d.chamar(_cai)
    with pytest.raises(ForaDoAr):
        d.chamar(lambda: "ok")


def test_erro_do_proprio_servico_nao_conta(relogio):
    d = Disjuntor("teste-recusa", falhas=2, pausa=60)

    def recusou():
        raise ValueError("senha errada")
    for _ in range(5):
        with pytest.raises(ValueError):
            d.chamar(recusou)
    assert d.chamar(lambda: "ok") == "ok"


def test_um_sucesso_no_meio_zera_a_conta(relogio):
    d = Disjuntor("teste-zera", falhas=3, pausa=60)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            d.chamar(_cai)
    d.chamar(lambda: None)
    for _ in range(2):
        with pytest.raises(ConnectionError):
            d.chamar(_cai)
    assert d.chamar(lambda: "ok") == "ok"


def test_lista_todos():
    Disjuntor("teste-lista")
    assert any(x["nome"] == "teste-lista" for x in Disjuntor.todos())
