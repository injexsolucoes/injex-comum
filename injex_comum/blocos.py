"""🧱 Construtor por blocos (dona, 25/10/2026): o mesmo em todos os sites da Injex (Agenda, Lojas, Lanchonete).

Uma página é uma lista de blocos, um embaixo do outro:

- **Seção pronta** (`{"tipo": "secao", "secao": "<id>"}`): o que é do sistema (na Agenda: Quem somos, Serviços…; na
  Loja: Banners, Vitrines; na Lanchonete: o Cardápio). O sistema diz quais existem (`secoes_validas`) e monta cada uma.
- **Bloco livre** (`{"tipo": "livre", "colunas": 1-3, "fundo", "proporcao", "alinhamento", "itens": [[…], …]}`): cada
  coluna tem elementos (os de `ELEMENTOS`).
- **Responsivo sempre** (regra da dona): ninguém escolhe largura nem altura. O bloco decide as colunas (no celular
  ficam uma embaixo da outra) e a proporção das fotos; tudo o que entra se encaixa nele (estatico/blocos.css).

O sistema guarda a lista (JSON), passa por `validar` ao salvar e por `montar_livre` ao montar a página. As fotos são do
sistema: ele diz quais chaves existem (`minhas`) e como vira endereço (`foto_url`). Na tela, o editor é o
estatico/editor-blocos.js e o site usa estatico/blocos.css + blocos.js (`arquivo(nome)` devolve o texto).
"""

import re
import secrets
from pathlib import Path

from . import icones
from .texto import e

ESTATICO = Path(__file__).resolve().parent / "estatico"
ARQUIVOS = {"blocos.css": "text/css", "blocos.js": "text/javascript", "editor-blocos.css": "text/css",
            "editor-blocos.js": "text/javascript"}

MAX_BLOCOS, MAX_ELEMENTOS = 30, 12
FUNDOS = {"auto": "Automático (alterna)", "claro": "Claro", "cor": "Na cor da marca"}
PROPORCOES = {"deitada": ("Deitada (4:3)", "4 / 3"), "quadrada": ("Quadrada", "1 / 1"),
              "larga": ("Larga (16:9)", "16 / 9"), "em_pe": ("Em pé (3:4)", "3 / 4")}
ALINHAMENTOS = {"esquerda": "À esquerda", "centro": "No centro"}
# ação do botão: (nome no editor, texto padrão do botão, ícone). Cada sistema diz quais valem para ele.
ACOES = {"agendar": ("Agendar", "Agendar horário", "calendar-check"),
         "whatsapp": ("WhatsApp", "Chamar no WhatsApp", "whatsapp-logo"),
         "cardapio": ("Ver o cardápio", "Ver o cardápio", "fork-knife"),
         "produtos": ("Ver os produtos", "Ver os produtos", "shopping-bag"),
         "link": ("Um link", "Saiba mais", "")}
ESPACOS = {"p": 12, "m": 32, "g": 64}
TAMANHOS = {"titulo": 120, "texto": 1500, "rotulo": 60, "botao": 60, "link": 300, "pergunta": 160, "resposta": 800,
            "item": 120, "autor": 60}
MAX_FOTOS_EL, MAX_ITENS = 12, 15
# 🧰 O painel de elementos (o "＋ Elemento" do editor mostra estes cartões; editor-blocos.js › ELEMENTOS tem os mesmos)
ELEMENTOS = ["icone", "titulo", "texto", "foto", "botao", "carrossel", "galeria", "lista", "faq", "video", "citacao",
             "divisor", "espaco"]
TAMANHOS_ICONE = {"p": 40, "m": 56, "g": 76}


class ErroBlocos(ValueError):
    """Algo que a pessoa digitou não vale (a mensagem é para mostrar na tela)."""


def arquivo(nome):
    """O texto de um arquivo da tela (CSS/JS do site e do editor), para o sistema servir ou pôr dentro da página."""
    if nome not in ARQUIVOS:
        raise KeyError(nome)
    return (ESTATICO / nome).read_text(encoding="utf-8")


def youtube_id(valor):
    """O código do vídeo de um link do YouTube (youtu.be/…, watch?v=…, shorts/…, embed/…) ou o próprio código."""
    valor = str(valor or "").strip()
    m = re.search(r"(?:youtu\.be/|[?&]v=|/shorts/|/embed/|/live/)([\w-]{11})", valor)
    if m:
        return m.group(1)
    return valor if re.fullmatch(r"[\w-]{11}", valor) else ""


def _id(valor):
    return re.sub(r"[^a-z0-9]", "", str(valor or "").lower())[:12] or secrets.token_hex(4)


def _txt(valor, tamanho, linhas=False):
    valor = str(valor or "").replace("\r", "")
    if not linhas:
        valor = " ".join(valor.split())
    return valor.strip()[:tamanho]


def link_seguro(valor):
    """Link de botão: https://…, o próprio site ("/…") ou uma parte da página ("#…"). Vazio se for outra coisa."""
    valor = str(valor or "").strip()
    if not valor:
        return ""
    if re.fullmatch(r"#[\w-]{1,40}", valor) or (valor.startswith("/") and not valor.startswith("//")
                                                 and re.fullmatch(r"/[\w./?=&%-]*", valor)):
        return valor[:TAMANHOS["link"]]
    if re.match(r"^(www\.)?[\w-]+(\.[\w-]+)+(/\S*)?$", valor):
        valor = "https://" + valor
    return valor[:TAMANHOS["link"]] if re.fullmatch(r"https?://[^\s<>\"']+", valor) else ""


def de_secoes(secoes):
    """Página antiga (sem blocos): as seções na ordem de sempre viram blocos (fica igual até alguém mexer)."""
    return [{"id": s, "tipo": "secao", "secao": s} for s in secoes]


def _elemento(el, minhas, acoes):
    tipo = el.get("tipo") if isinstance(el, dict) else None
    if tipo == "titulo":
        # vazio fica guardado (a pessoa acabou de pôr e ainda vai escrever); no site, vazio não aparece
        return {"tipo": tipo, "texto": _txt(el.get("texto"), TAMANHOS["titulo"]),
                "rotulo": _txt(el.get("rotulo"), TAMANHOS["rotulo"])}
    if tipo == "texto":
        return {"tipo": tipo, "texto": _txt(el.get("texto"), TAMANHOS["texto"], linhas=True)}
    if tipo == "foto":
        return {"tipo": tipo, "foto": el.get("foto") if el.get("foto") in minhas else ""}
    if tipo == "botao":
        acao = el.get("acao") if el.get("acao") in acoes else acoes[0]
        digitado = str(el.get("link") or "").strip()
        link = link_seguro(digitado) if acao == "link" else ""
        if acao == "link" and digitado and not link:
            raise ErroBlocos(f"Link do botão não vale: {digitado[:60]} (use https://…)")
        return {"tipo": tipo, "acao": acao, "texto": _txt(el.get("texto"), TAMANHOS["botao"]), "link": link}
    if tipo == "espaco":
        return {"tipo": tipo, "tamanho": el.get("tamanho") if el.get("tamanho") in ESPACOS else "m"}
    if tipo in ("carrossel", "galeria"):
        fotos = [f for f in (el.get("fotos") or []) if f in minhas] if isinstance(el.get("fotos"), list) else []
        return {"tipo": tipo, "fotos": list(dict.fromkeys(fotos))[:MAX_FOTOS_EL]}
    if tipo == "lista":
        itens = el.get("itens") if isinstance(el.get("itens"), list) else []
        return {"tipo": tipo, "itens": [_txt(i, TAMANHOS["item"]) for i in itens[:MAX_ITENS]]}
    if tipo == "faq":
        itens = el.get("itens") if isinstance(el.get("itens"), list) else []
        return {"tipo": tipo, "itens": [{"pergunta": _txt(i.get("pergunta"), TAMANHOS["pergunta"]),
                                         "resposta": _txt(i.get("resposta"), TAMANHOS["resposta"], linhas=True)}
                                        for i in itens[:MAX_ITENS] if isinstance(i, dict)]}
    if tipo == "video":
        digitado = str(el.get("video") or "").strip()
        codigo = youtube_id(digitado)
        if digitado and not codigo:
            raise ErroBlocos("Esse link não é de um vídeo do YouTube (copie o link do vídeo no YouTube)")
        return {"tipo": tipo, "video": codigo}
    if tipo == "citacao":
        return {"tipo": tipo, "texto": _txt(el.get("texto"), TAMANHOS["resposta"], linhas=True),
                "autor": _txt(el.get("autor"), TAMANHOS["autor"])}
    if tipo == "divisor":
        return {"tipo": tipo}
    if tipo == "icone":
        return {"tipo": tipo, "icone": el.get("icone") if el.get("icone") in icones.ICONES else "",
                "tamanho": el.get("tamanho") if el.get("tamanho") in TAMANHOS_ICONE else "m"}
    return None


def validar(lista, secoes_validas, minhas, acoes=("whatsapp", "link")):
    """Só passa o que o construtor conhece, com limites (o que vem da tela não é confiável). None = página antiga.

    `secoes_validas` = as seções prontas do sistema; `minhas` = as fotos que existem; `acoes` = as ações de botão que
    valem (a 1ª é a padrão)."""
    if lista is None:
        return None
    if not isinstance(lista, list):
        raise ErroBlocos("Blocos inválidos")
    if len(lista) > MAX_BLOCOS:
        raise ErroBlocos(f"Até {MAX_BLOCOS} blocos")
    acoes = [a for a in acoes if a in ACOES] or ["link"]
    minhas = set(minhas)
    saida, vistas = [], set()
    for b in lista:
        if not isinstance(b, dict):
            continue
        if b.get("tipo") == "secao":
            s = b.get("secao")
            if s in secoes_validas and s not in vistas:
                vistas.add(s)
                saida.append({"id": s, "tipo": "secao", "secao": s})
            continue
        if b.get("tipo") != "livre":
            continue
        colunas = b.get("colunas") if b.get("colunas") in (1, 2, 3) else 1
        itens = b.get("itens") if isinstance(b.get("itens"), list) else []
        cols = []
        for i in range(colunas):
            col = itens[i] if i < len(itens) and isinstance(itens[i], list) else []
            if len(col) > MAX_ELEMENTOS:
                raise ErroBlocos(f"Até {MAX_ELEMENTOS} elementos em cada coluna")
            cols.append([x for x in (_elemento(el, minhas, acoes) for el in col) if x])
        saida.append({"id": _id(b.get("id")), "tipo": "livre", "colunas": colunas,
                      "fundo": b.get("fundo") if b.get("fundo") in FUNDOS else "auto",
                      "proporcao": b.get("proporcao") if b.get("proporcao") in PROPORCOES else "deitada",
                      "alinhamento": b.get("alinhamento") if b.get("alinhamento") in ALINHAMENTOS else "esquerda",
                      "itens": cols})
    return saida


def fotos_usadas(lista):
    """As chaves de foto que os blocos usam (o sistema pode apagar as que ninguém usa)."""
    usadas = set()
    for b in lista or []:
        for col in b.get("itens", []) if b.get("tipo") == "livre" else []:
            for el in col:
                if el.get("foto"):
                    usadas.add(el["foto"])
                usadas.update(el.get("fotos") or [])
    return usadas


def _paragrafos(texto):
    return "".join("<p>" + "<br>".join(e(linha) for linha in p.split("\n")) + "</p>"
                   for p in re.split(r"\n\s*\n", texto) if p.strip())


def montar_livre(b, trocar, links, foto_url, alterna=False, I=lambda nome: icones.svg(nome)):  # noqa: E741
    """Um bloco livre em HTML (vazio = não aparece).

    `trocar(texto)` = troca os códigos ({nome}…); `links` = {ação: endereço} (ação sem endereço cai no WhatsApp; sem
    os dois, o botão não aparece); `foto_url(chave)`; `alterna` = este bloco leva o fundo alternado; `I(nome)` = o
    ícone no estilo do site (linha, preenchido ou emoji)."""
    colunas, tem_conteudo = [], False
    for col in b["itens"]:
        partes = []
        for el in col:
            if el["tipo"] == "icone" and el["icone"]:
                partes.append(f'<div class="icone-livre" style="--tam:{TAMANHOS_ICONE[el["tamanho"]]}px">{I(el["icone"])}</div>')
            elif el["tipo"] == "titulo" and el["texto"]:
                rotulo = f'<div class="ib-rotulo">{e(trocar(el["rotulo"]))}</div>' if el.get("rotulo") else ""
                partes.append(f'{rotulo}<h2>{e(trocar(el["texto"]))}</h2>')
            elif el["tipo"] == "texto" and el["texto"]:
                partes.append(f'<div class="texto-livre">{_paragrafos(trocar(el["texto"]))}</div>')
            elif el["tipo"] == "foto" and el["foto"]:
                partes.append(f'<img class="foto-livre" src="{e(foto_url(el["foto"]))}" alt="" loading="lazy">')
            elif el["tipo"] == "botao":
                acao = el["acao"] if el["acao"] in ACOES else "link"
                href = el["link"] if acao == "link" else links.get(acao) or links.get("whatsapp")
                if href:
                    fora = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
                    icone = I(ACOES[acao][2]) if ACOES[acao][2] else ""
                    partes.append(f'<a class="ib-botao ib-{acao}" href="{e(href)}"{fora}>{icone}'
                                  f'<span>{e(trocar(el["texto"]) or ACOES[acao][1])}</span></a>')
            elif el["tipo"] == "espaco":
                partes.append(f'<div class="espaco" style="height:{ESPACOS[el["tamanho"]]}px" aria-hidden="true"></div>')
            elif el["tipo"] == "carrossel" and el["fotos"]:
                slides = "".join(f'<img src="{e(foto_url(f))}" alt="" loading="lazy">' for f in el["fotos"])
                setas = (f'<button type="button" class="seta ant" aria-label="Foto anterior">{I("caret-left")}</button>'
                         f'<button type="button" class="seta prox" aria-label="Próxima foto">{I("caret-right")}</button>'
                         if len(el["fotos"]) > 1 else "")
                partes.append(f'<div class="carrossel" data-carrossel><div class="trilho">{slides}</div>{setas}</div>')
            elif el["tipo"] == "galeria" and el["fotos"]:
                fotos = "".join(f'<button type="button" data-grande="{e(foto_url(f))}" aria-label="Ampliar foto">'
                                f'<img src="{e(foto_url(f))}" alt="" loading="lazy"></button>' for f in el["fotos"])
                partes.append(f'<div class="galeria-livre">{fotos}</div>')
            elif el["tipo"] == "lista" and any(el["itens"]):
                itens = "".join(f"<li>{I('check-circle')}<span>{e(trocar(i))}</span></li>" for i in el["itens"] if i)
                partes.append(f'<ul class="lista-livre">{itens}</ul>')
            elif el["tipo"] == "faq" and any(i["pergunta"] for i in el["itens"]):
                itens = "".join(f'<details><summary>{e(trocar(i["pergunta"]))}</summary>{_paragrafos(trocar(i["resposta"]))}'
                                f'</details>' for i in el["itens"] if i["pergunta"])
                partes.append(f'<div class="faq-livre">{itens}</div>')
            elif el["tipo"] == "video" and el["video"]:
                # 🍪 o player do YouTube (cookies dele) só carrega no toque; antes é só a capa do vídeo
                v = e(el["video"])
                partes.append(f'<div class="video-livre" data-video="{v}"><img src="https://i.ytimg.com/vi/{v}/hqdefault.jpg" '
                              f'alt="" loading="lazy"><button type="button" aria-label="Ver o vídeo">{icones.svg("play", "preenchido")}</button></div>')
            elif el["tipo"] == "citacao" and el["texto"]:
                autor = f'<cite>{e(trocar(el["autor"]))}</cite>' if el["autor"] else ""
                partes.append(f'<blockquote class="citacao-livre">{_paragrafos(trocar(el["texto"]))}{autor}</blockquote>')
            elif el["tipo"] == "divisor":
                partes.append('<hr class="divisor-livre">')
        tem_conteudo = tem_conteudo or any('class="espaco"' not in p and "divisor-livre" not in p for p in partes)
        colunas.append(f'<div class="coluna">{"".join(partes)}</div>')
    if not tem_conteudo:
        return ""   # bloco vazio (ou só com espaço) não aparece
    fundo = {"cor": "fundo-cor", "claro": "", "auto": "alterna" if alterna else ""}[b["fundo"]]
    return (f'<section id="b-{e(b["id"])}" class="bloco-livre {fundo}" style="--proporcao:{PROPORCOES[b["proporcao"]][1]}">'
            f'<div class="ib-miolo"><div class="grade-bloco cols-{b["colunas"]} alin-{b["alinhamento"]}">'
            f'{"".join(colunas)}</div></div></section>')


def montar(lista, secao, trocar, links, foto_url, I=lambda nome: icones.svg(nome)):  # noqa: E741
    """A página inteira: cada bloco livre vira HTML e cada seção pronta é pedida ao sistema (`secao(id)` → HTML ou "").
    O fundo alternado conta só o que aparece."""
    partes = []
    for b in lista or []:
        if b["tipo"] == "secao":
            html = secao(b["secao"]) or ""
        else:
            html = montar_livre(b, trocar, links, foto_url, len(partes) % 2 == 1, I)
        if html:
            partes.append(html)
    return "".join(partes)
