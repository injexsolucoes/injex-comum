# Injex · Comum

Peças **iguais em todos os sistemas** da Injex Soluções (Agenda e Site simples, Lojas, Lanchonete, Central e, depois, o
Sistema Injex). Assim a gente muda num lugar só e todos pegam na próxima atualização.

| Parte | O que tem |
|---|---|
| `injex_comum/icones.py` | 🎨 Galeria de ícones (127), em 3 estilos: **linha** (padrão), **preenchido** e **emoji**. `svg(nome, estilo)`, `sprite(nomes)`, `para_o_painel()` |
| `injex_comum/legal.py` | 📜 Política de privacidade, Termos de uso e Política de cookies para os tipos `site`, `agenda`, `loja` e `lanchonete` (`secoes()` + `miolo()`), e o aviso de cookies (`aviso_cookies()`, `CSS_COOKIES`) |
| `injex_comum/texto.py` | 🔤 Códigos `{nome}`, `{whatsapp}`… (`trocar`), telefone, CNPJ, e-mail |

## Regra de ouro

Aqui só entra o que é **genérico**. **Nunca** dados de cliente, senhas, chaves, contas ou qualquer coisa de um negócio.
Os dados de cada cliente ficam no sistema dele e só passam por aqui na hora de montar uma página.

## Como cada sistema usa

No `requirements.txt` do sistema, com a versão fixa:

```
injex-comum @ https://github.com/injexsolucoes/injex-comum/archive/refs/tags/v1.0.0.zip
```

O sistema baixa a versão **na hora de atualizar** (o `atualizar.sh` de cada um já instala as bibliotecas) e guarda
uma cópia. Os sites nunca buscam nada daqui enquanto alguém está navegando.

## Versão nova

1. Mudar aqui, rodar os testes (`python -m pytest`) e subir.
2. Trocar `VERSAO` (em `injex_comum/__init__.py`) e `version` (em `pyproject.toml`), e criar a tag (`v1.1.0`).
3. Em cada sistema, trocar a versão no `requirements.txt`, testar e atualizar. Um sistema por vez.

## Licenças

Os desenhos dos ícones são do [Phosphor Icons](https://phosphoricons.com) (licença MIT, ver
`LICENCA-ICONES-PHOSPHOR.txt`). O resto: © Injex Soluções.
