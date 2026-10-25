"""Testes do comum: ícones, textos e as páginas legais dos 4 tipos."""

import re

import pytest

from injex_comum import icones, legal, texto

LINKS = {"privacidade": "/privacidade", "termos": "/termos", "cookies": "/cookies", "contato": "/contato",
         "trocas": "/trocas"}
CODIGOS = {"{nome}": "Barbearia <Zé>", "{empresa}": "", "{cnpj}": "12.345.678/0001-90", "{endereco}": "Rua A, 1",
           "{whatsapp}": "(19) 99999-9999", "{email}": "ze@ze.com", "{responsavel}": "José"}


def test_icones_nos_tres_estilos():
    assert set(icones.ICONES) == set(icones.EMOJI) and len(icones.ICONES) >= 120
    linha, cheio, emoji = (icones.svg("scissors", e) for e in ("linha", "preenchido", "emoji"))
    assert linha != cheio and linha.startswith("<svg") and "✂️" in emoji
    assert icones.svg("nao-existe") == ""
    s = icones.sprite(["plus", "nao-existe", "globe"])
    assert s.count("<symbol") == 2 and 'id="i-plus"' in s
    assert {"nome", "rotulo", "linha", "preenchido", "emoji"} <= set(icones.para_o_painel()[0])


def test_texto():
    assert texto.trocar("Oi {nome} {inventado}", {"{nome}": "Zé"}) == "Oi Zé {inventado}"
    assert texto.telefone_bonito("5519999998888") == "(19) 99999-8888" and texto.telefone_bonito("1934000000") == "(19) 3400-0000"
    assert texto.cnpj_bonito("12345678000190") == "12.345.678/0001-90" and texto.cnpj_bonito("123") == ""
    assert texto.email_ok("a@b.co") and not texto.email_ok("a@")


@pytest.mark.parametrize("tipo", legal.TIPOS)
@pytest.mark.parametrize("qual", list(legal.PAGINAS))
def test_paginas_de_todos_os_tipos(tipo, qual):
    html = legal.miolo(legal.secoes(qual, tipo, CODIGOS, {}, LINKS, observacoes="Regra <b>da casa</b>"))
    assert "<section><h2>" in html and "<Zé>" not in html and "ze@ze.com" in html                 # dados escapados
    if qual != "cookies":
        assert "Barbearia &lt;Zé&gt;" in html
    assert not re.search(r"<p></p>|<li></li>|<ul></ul>", html)
    if qual == "termos":
        assert "Observações de Barbearia &lt;Zé&gt;" in html and "Regra &lt;b&gt;da casa&lt;/b&gt;" in html


def test_texto_segue_o_que_esta_ligado():
    def h(qual, tipo, s):
        return legal.miolo(legal.secoes(qual, tipo, CODIGOS, s, LINKS))
    assert "Mercado Pago" not in h("termos", "loja", {}) and "7 dias" in h("termos", "loja", {})
    loja = h("privacidade", "loja", {"online": True, "envio": True, "emails": True, "boleto": True})
    assert "SuperFrete" in loja and "Brevo" in loja and "ou boleto" in loja
    assert "Agendamento" in h("termos", "agenda", {"antecedencia_min": 60}) and "1 hora" in h("termos", "agenda", {"antecedencia_min": 60})
    assert "Agendamento" not in h("termos", "site", {})
    assert "YouTube" in h("cookies", "site", {"video": True}) and "YouTube" not in h("cookies", "site", {})
    lanche = h("termos", "lanchonete", {"mesas": True, "pedir": True, "taxa": "10", "delivery": True})
    assert "taxa de serviço (10%)" in lanche and "<h2>Delivery</h2>" in lanche
    assert "iFood" not in h("privacidade", "lanchonete", {})
    with pytest.raises(ValueError):
        legal.secoes("outra", "loja", CODIGOS, {}, LINKS)


def test_aviso_de_cookies():
    a = legal.aviso_cookies("/x/cookies", "loja_cookies_ok", "Esta loja")
    assert 'href="/x/cookies"' in a and "'loja_cookies_ok'" in a and "Esta loja usa" in a
