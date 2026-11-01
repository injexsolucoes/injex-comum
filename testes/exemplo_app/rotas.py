"""Um "sistema" de exemplo para testar o módulo de erros (a origem tem que apontar para cá)."""


def total(itens):
    return sum(i["preco"] for i in itens)  # KeyError de propósito quando falta o preço
