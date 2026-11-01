"""🔐 Backup trancado — módulo comum (o mesmo do Sistema Injex, 16/10/2026; peça comum desde 01/11/2026).

O .zip do backup sai TRANCADO (AES-256-GCM): quem pegar o arquivo (cópia no PC, pendrive, nuvem) não abre sem a chave.
O nome do arquivo continua o mesmo; por dentro começa com 8 letras (`magico`, ex.: "INJEXBK1") em vez de ser um .zip.
Precisa da biblioteca `cryptography`. A chave NÃO vai junto do backup: guarde uma cópia fora do servidor.

    from injex_comum.cripto_backup import Tranca
    TRANCA = Tranca("LOJA_CHAVE_BACKUP", lambda: pasta_dados() / "chave-backup.key", magico=b"LOJABK01")
    TRANCA.trancar(zip_comum, destino)          # destino trancado
    with TRANCA.aberto(arquivo) as zip_comum:  # backup antigo (sem tranca) ou trancado: dá um .zip comum
        ...

Formato: magico + 4 bytes da impressão da chave + 8 bytes de nonce; depois blocos de até 4 MB, cada um "tamanho
(4 bytes) + bloco trancado". O número do bloco e a marca de "último" vão no AAD: cortar ou trocar blocos é percebido.
"""

import base64
import hashlib
import os
import secrets
import struct
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BLOCO = 4 * 1024 * 1024


class ErroChave(ValueError):
    pass


def nova_chave() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


class Tranca:
    """A tranca dos backups de UM sistema. `variavel`: variável de ambiente com a chave (ex.: LOJA_CHAVE_BACKUP);
    sem ela, `arquivo` (caminho ou função) com a chave, criado sozinho. `magico`: 8 bytes do começo do arquivo."""

    def __init__(self, variavel, arquivo, magico=b"INJEXBK1"):
        assert len(magico) == 8
        self.variavel, self._arquivo, self.MAGICO = variavel, arquivo, magico

    @property
    def arquivo(self):
        return Path(self._arquivo() if callable(self._arquivo) else self._arquivo)

    def _chave(self) -> bytes:
        texto = os.environ.get(self.variavel, "").strip()
        if not texto:
            arquivo = self.arquivo
            if not arquivo.exists():
                arquivo.parent.mkdir(parents=True, exist_ok=True)
                arquivo.write_text(nova_chave())
                try:
                    os.chmod(arquivo, 0o600)
                except OSError:
                    pass
            texto = arquivo.read_text().strip()
        try:
            chave = base64.urlsafe_b64decode(texto)
        except ValueError:
            chave = b""
        if len(chave) != 32:
            raise ErroChave(f"A chave do backup está inválida ({self.variavel}).")
        return chave


    def _impressao(self, chave: bytes) -> bytes:
        return hashlib.sha256(b"injex-backup" + chave).digest()[:4]


    def trancado(self, arquivo: Path) -> bool:
        with open(arquivo, "rb") as f:
            return f.read(len(self.MAGICO)) == self.MAGICO


    def trancar(self, origem: Path, destino: Path) -> None:
        chave = self._chave()
        aes, prefixo = AESGCM(chave), secrets.token_bytes(8)
        tamanho = origem.stat().st_size
        with open(origem, "rb") as entrada, open(destino, "wb") as saida:
            saida.write(self.MAGICO + self._impressao(chave) + prefixo)
            n, lido = 0, 0
            while True:
                pedaco = entrada.read(BLOCO)
                lido += len(pedaco)
                ultimo = lido >= tamanho
                extra = self.MAGICO + struct.pack(">I?", n, ultimo)
                cifrado = aes.encrypt(prefixo + struct.pack(">I", n), pedaco, extra)
                saida.write(struct.pack(">I", len(cifrado)) + cifrado)
                n += 1
                if ultimo:
                    break


    def destrancar(self, origem: Path, destino: Path) -> None:
        chave = self._chave()
        aes = AESGCM(chave)
        with open(origem, "rb") as entrada, open(destino, "wb") as saida:
            cabeca = entrada.read(len(self.MAGICO) + 12)
            if cabeca[:len(self.MAGICO)] != self.MAGICO:
                raise ErroChave("Este arquivo não é um backup trancado do sistema.")
            if cabeca[len(self.MAGICO):len(self.MAGICO) + 4] != self._impressao(chave):
                raise ErroChave("Este backup foi trancado com OUTRA chave. Use a chave do servidor de onde ele veio.")
            prefixo = cabeca[len(self.MAGICO) + 4:]
            n = 0
            while True:
                tam = entrada.read(4)
                if len(tam) < 4:
                    raise ErroChave("Backup incompleto (o arquivo foi cortado).")
                cifrado = entrada.read(struct.unpack(">I", tam)[0])
                for ultimo in (False, True):
                    try:
                        pedaco = aes.decrypt(prefixo + struct.pack(">I", n), cifrado, self.MAGICO + struct.pack(">I?", n, ultimo))
                        break
                    except InvalidTag:
                        pedaco = None
                if pedaco is None:
                    raise ErroChave("Backup danificado ou alterado: não abre com esta chave.")
                saida.write(pedaco)
                n += 1
                if ultimo:
                    return


    @contextmanager
    def aberto(self, arquivo: Path):
        """Dá o caminho de um .zip comum: o próprio arquivo (backup antigo, sem tranca) ou uma cópia destrancada
        temporária (apagada no fim)."""
        if not self.trancado(arquivo):
            yield arquivo
            return
        fd, temporario = tempfile.mkstemp(suffix=".zip", prefix="destrancado-")
        os.close(fd)
        try:
            self.destrancar(arquivo, Path(temporario))
            yield Path(temporario)
        finally:
            Path(temporario).unlink(missing_ok=True)
