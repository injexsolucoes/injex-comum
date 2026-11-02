# Injex · Comum

Peças **iguais em todos os sistemas** da Injex Soluções (Agenda e Site simples, Lojas, Lanchonete, Central e, depois, o
Sistema Injex). Assim a gente muda num lugar só e todos pegam na próxima atualização.

| Parte | O que tem |
|---|---|
| `injex_comum/icones.py` | 🎨 Galeria de ícones (146), em 3 estilos: **linha** (padrão), **preenchido** e **emoji**. `svg(nome, estilo)`, `sprite(nomes)`, `para_o_painel()` |
| `injex_comum/legal.py` | 📜 Política de privacidade, Termos de uso e Política de cookies para os tipos `site`, `agenda`, `loja` e `lanchonete` (`secoes()` + `miolo()`), e o aviso de cookies (`aviso_cookies()`, `CSS_COOKIES`) |
| `injex_comum/texto.py` | 🔤 Códigos `{nome}`, `{whatsapp}`… (`trocar`), telefone, CNPJ, e-mail |
| `injex_comum/blocos.py` + `estatico/` | 🧱 Construtor por blocos (1 a 3 colunas, 13 elementos: ícone, título, texto, foto, botão, carrossel, galeria, lista, perguntas, vídeo, frase, linha, espaço). `validar()`, `montar_livre()`, `montar()`; a tela usa `estatico/blocos.css` + `blocos.js` (site) e `editor-blocos.css` + `editor-blocos.js` (editor, `InjexBlocos.editor`). Cada sistema serve esses arquivos em `/comum/<arquivo>` (`arquivo(nome)`). **Responsivo sempre:** ninguém escolhe largura; o bloco decide |
| `injex_comum/erros.py` + `estatico/erros.js` | 🚨 **Erros com a origem + alerta** (módulo, 01/11/2026). Todo erro inesperado do servidor e das telas fica num .db próprio com quando, onde, quem, **origem** (arquivo:linha do código do sistema) e vezes; erro novo = e-mail (Gmail). Ligar num sistema FastAPI: `REGISTRO = erros.Registro(lambda: DADOS / "erros.db", raiz=PASTA_DO_CODIGO, sistema="Nome", onde_ver="Configurações › 🚨 Erros")`, depois de todos os middlewares `erros.instalar(app, REGISTRO, eh_admin=<dependência True/False>, quem_e=<request → nome>)`, no lifespan `erros.vigiar_avisos(REGISTRO, <() → (remetente, senha, destino)>)` e em cada página `<script src="/comum/erros.js"></script>` antes dos outros. Rotas: `GET /api/erros`, `/api/erros/resumo`, `POST /api/erros/{chave}/resolvido`, `POST /api/erros/tela` (mude com `prefixo=`) |
| `injex_comum/estatico/erros-painel.js` | 🚨 Quadro "Erros do sistema" pronto para a tela do administrador: `<script src="/comum/erros-painel.js"></script>` + `InjexErrosPainel.montar(elemento)` (lista, "📋 Copiar para o Claude", "✔ Resolvido"). Sem depender de outro script |
| `injex_comum/cofre.py` | 🔐 **Cofre** dos segredos (chaves do Mercado Pago, Gemini, senhas): `COFRE = Cofre("LOJA_CHAVE_SENHAS", lambda: DADOS / "chave-senhas.key")`, `trancar_valor(v)` → "cofre:…" para gravar, `abrir_valor(v)` para ler (valor antigo sem "cofre:" volta igual). Precisa de `cryptography` |
| `injex_comum/cripto_backup.py` | 🔐 **Backup trancado** (AES-256-GCM): `TRANCA = Tranca("LOJA_CHAVE_BACKUP", lambda: DADOS / "chave-backup.key", magico=b"LOJABK01")`, `trancar(zip, destino)`, `with aberto(arquivo) as zip_comum:` (abre antigo ou trancado). A chave nunca vai no backup: guardar uma cópia. Precisa de `cryptography` |
| `injex_comum/limites.py` | 🚦 **Limite nas rotas abertas** (02/11/2026): `limites.instalar(app, [("/api/menu/pedir", 10), ("/api/menu/", 60)])` (antes do `erros.instalar`). Só conta quem grava (POST/PUT/PATCH/DELETE), por endereço, janela de 1 min (passou = 429 "Espere um minuto"); corpo acima de `corpo_max` (256 KB) = 413. Nos testes dos sistemas: `INJEX_LIMITES_DESLIGADOS=1` no conftest |
| `injex_comum/disjuntor.py` | 🔌 **Disjuntor** (02/11/2026): `SEFAZ = Disjuntor("SEFAZ", falhas=3, pausa=120, conta=(OSError,))` e `SEFAZ.chamar(fn, ...)` ou `with SEFAZ.vigiar():`. Depois de N quedas seguidas para de insistir e levanta `ForaDoAr` (um `ConnectionError`) na hora com "<serviço> está fora do ar agora… tente daqui a N minutos"; passada a pausa testa uma vez. Erro do próprio serviço (recusou, senha) não conta. `Disjuntor.todos()` = estado de cada um |
| `injex_comum/origem.py` | 🛡️ **Conferência de origem (contra CSRF)** (02/11/2026): `origem.instalar(app)` (antes do `erros.instalar`). Pedido que muda algo (POST/PUT/PATCH/DELETE) com Origin/Referer de OUTRO endereço (inclusive outro `*.lojas…`) = 403. Passam: mesmo endereço, sem Origin (servidor → servidor), extensões do navegador e `aceitos=[...]` |

## Regra de ouro

Aqui só entra o que é **genérico**. **Nunca** dados de cliente, senhas, chaves, contas ou qualquer coisa de um negócio.
Os dados de cada cliente ficam no sistema dele e só passam por aqui na hora de montar uma página.

## Como cada sistema usa

No `requirements.txt` do sistema, com a versão fixa pelo envio (commit) — nunca o `main`, para uma mudança aqui não
entrar sozinha num sistema:

```
injex-comum @ https://github.com/injexsolucoes/injex-comum/archive/b9849e1b2e1ac43d9d5763fc4896818eb18a0d6a.zip
```

O sistema baixa a versão **na hora de atualizar** (o `atualizar.sh` de cada um já instala as bibliotecas) e guarda
uma cópia. Os sites nunca buscam nada daqui enquanto alguém está navegando.

## Versão nova

1. Mudar aqui, rodar os testes (`python -m pytest`) e subir.
2. Trocar `VERSAO` (em `injex_comum/__init__.py`) e `version` (em `pyproject.toml`), e subir.
3. Em cada sistema, trocar o código do envio (commit) no `requirements.txt`, testar e atualizar. Um sistema por vez.

## Licenças

Os desenhos dos ícones são do [Phosphor Icons](https://phosphoricons.com) (licença MIT, ver
`LICENCA-ICONES-PHOSPHOR.txt`). O resto: © Injex Soluções.
