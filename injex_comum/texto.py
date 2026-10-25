"""🔤 Pequenas peças de texto que todo sistema da Injex usa: os códigos ({nome}, {whatsapp}…), telefone, CNPJ, e-mail.

**Códigos:** qualquer texto que o cliente escreve no site pode usar `{nome}`, `{whatsapp}`… (igual à tabela de preços do
Sistema Injex). Cada sistema monta o dicionário com os dados dele (`{"{nome}": "Barbearia do Zé", …}`) e chama
`trocar`. Código que não existe fica como foi escrito.
"""

import html
import re


def e(texto):
    """Escapa para pôr no HTML."""
    return html.escape(str(texto or ""), quote=True)


def so_numeros(texto):
    return re.sub(r"\D", "", str(texto or ""))


def trocar(texto, codigos):
    """Troca os códigos conhecidos; o resto do texto (e código que não existe) fica igual. Sem escapar."""
    if not texto or "{" not in texto:
        return texto
    return re.sub(r"\{[a-z_]+\}", lambda m: codigos.get(m.group(0), m.group(0)), texto)


def telefone_bonito(texto):
    """(19) 99999-9999 / (19) 3400-0000, com ou sem o 55 na frente. Outra coisa volta como veio."""
    n = so_numeros(texto)
    if n.startswith("55") and len(n) in (12, 13):
        n = n[2:]
    if len(n) == 11:
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) == 10:
        return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return str(texto or "").strip()


def cnpj_bonito(texto):
    """00.000.000/0000-00 se tiver 14 números; senão vazio."""
    n = so_numeros(texto)
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}" if len(n) == 14 else ""


def email_ok(texto):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(texto or "").strip()))
