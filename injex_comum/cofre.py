"""🔐 Cofre — módulo comum (o mesmo do Sistema Injex, 16/10/2026; virou peça comum em 01/11/2026).

Guarda senhas e chaves de integração (Mercado Pago, Gemini, Nuvemshop…) TRANCADAS (Fernet: AES + assinatura). Sem a
chave, o banco e os backups não mostram nenhum segredo. Precisa da biblioteca `cryptography` no sistema.

Onde fica a chave: a variável de ambiente (ex.: LOJA_CHAVE_SENHAS) ou, sem ela, um arquivo na pasta de dados
(criado sozinho no primeiro uso, só o dono do arquivo lê). A chave NÃO entra no backup: guarde uma cópia.

    from injex_comum.cofre import Cofre
    COFRE = Cofre("LOJA_CHAVE_SENHAS", lambda: pasta_dados() / "chave-senhas.key")
    valor_no_banco = COFRE.trancar_valor("APP_USR-123")   # "cofre:gAAAA…"
    COFRE.abrir_valor(valor_no_banco)                      # "APP_USR-123" (valor antigo sem "cofre:" volta igual)
"""

import os
from pathlib import Path

MARCA = "cofre:"


class ErroCofre(ValueError):
    pass


class Cofre:
    def __init__(self, variavel, arquivo):
        self.variavel = variavel
        self._arquivo = arquivo

    @property
    def arquivo(self):
        return Path(self._arquivo() if callable(self._arquivo) else self._arquivo)

    def _chave(self):
        from cryptography.fernet import Fernet
        do_ambiente = os.environ.get(self.variavel, "").strip()
        if do_ambiente:
            return do_ambiente.encode()
        arquivo = self.arquivo
        if not arquivo.exists():
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_bytes(Fernet.generate_key())
            try:
                os.chmod(arquivo, 0o600)
            except OSError:
                pass
        return arquivo.read_bytes().strip()

    def _fernet(self):
        from cryptography.fernet import Fernet
        try:
            return Fernet(self._chave())
        except ValueError:
            raise ErroCofre(f"A chave do cofre está inválida ({self.variavel}). Fale com o administrador.")

    def guardar(self, segredo):
        return self._fernet().encrypt(segredo.encode()).decode() if segredo else ""

    def abrir(self, trancado):
        from cryptography.fernet import InvalidToken
        if not trancado:
            return ""
        try:
            return self._fernet().decrypt(trancado.encode()).decode()
        except InvalidToken:
            raise ErroCofre("Não consegui abrir este segredo: ele foi guardado com outra chave (backup de outro lugar?).")

    # ---------- valores de configuração (texto no banco) ----------
    def trancar_valor(self, valor):
        """Valor para gravar no banco: vazio fica vazio; já trancado não tranca de novo."""
        if not valor or valor.startswith(MARCA):
            return valor
        return MARCA + self.guardar(valor)

    def abrir_valor(self, valor):
        """Valor lido do banco: trancado → aberto; antigo (sem a marca) → igual; chave trocada → "" (cadastrar de novo)."""
        if not valor or not valor.startswith(MARCA):
            return valor
        try:
            return self.abrir(valor[len(MARCA):])
        except ErroCofre:
            return ""
