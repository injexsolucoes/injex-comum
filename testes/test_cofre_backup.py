"""🔐 Cofre e backup trancado (módulos comuns)."""

import zipfile

import pytest

from injex_comum.cofre import Cofre, ErroCofre, MARCA
from injex_comum.cripto_backup import ErroChave, Tranca, nova_chave


def test_cofre_tranca_abre_e_aceita_valor_antigo(tmp_path, monkeypatch):
    monkeypatch.delenv("X_CHAVE", raising=False)
    cofre = Cofre("X_CHAVE", lambda: tmp_path / "chave.key")
    v = cofre.trancar_valor("APP_USR-123")
    assert v.startswith(MARCA) and "APP_USR" not in v and (tmp_path / "chave.key").exists()
    assert cofre.trancar_valor(v) == v  # não tranca duas vezes
    assert cofre.abrir_valor(v) == "APP_USR-123"
    assert cofre.abrir_valor("antigo-sem-marca") == "antigo-sem-marca" and cofre.trancar_valor("") == ""
    outro = Cofre("X_CHAVE", tmp_path / "outra.key")  # outra chave: não abre, devolve vazio
    assert outro.abrir_valor(v) == ""
    with pytest.raises(ErroCofre):
        outro.abrir(v[len(MARCA):])


def test_cofre_chave_pela_variavel(tmp_path, monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("X_CHAVE", Fernet.generate_key().decode())
    cofre = Cofre("X_CHAVE", tmp_path / "nao-usa.key")
    assert cofre.abrir_valor(cofre.trancar_valor("s")) == "s" and not (tmp_path / "nao-usa.key").exists()


def test_backup_trancado_abre_so_com_a_chave(tmp_path, monkeypatch):
    monkeypatch.delenv("X_BK", raising=False)
    comum = tmp_path / "b.zip"
    with zipfile.ZipFile(comum, "w") as z:
        z.writestr("loja.db", b"dados" * 1000)
    tranca = Tranca("X_BK", tmp_path / "bk.key", magico=b"LOJABK01")
    trancado = tmp_path / "t.zip"
    tranca.trancar(comum, trancado)
    assert tranca.trancado(trancado) and not tranca.trancado(comum) and b"dados" not in trancado.read_bytes()
    with tranca.aberto(trancado) as aberto, zipfile.ZipFile(aberto) as z:
        assert z.read("loja.db") == b"dados" * 1000
    with tranca.aberto(comum) as aberto:  # backup antigo (sem tranca) continua abrindo
        assert aberto == comum
    monkeypatch.setenv("X_BK", nova_chave())  # outra chave
    with pytest.raises(ErroChave):
        tranca.destrancar(trancado, tmp_path / "x.zip")
