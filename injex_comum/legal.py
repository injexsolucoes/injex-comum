"""📜 As 3 páginas legais de todo site da Injex (privacidade, termos de uso e cookies) e o aviso de cookies.

Um texto-modelo só, com o que muda por tipo de negócio:
  "site"        Site simples (só o site e o formulário)       — Agenda Injex
  "agenda"      Agenda completa (agendamento, área do cliente) — Agenda Injex
  "loja"        Loja virtual (compra, Mercado Pago, entrega)   — Injex Lojas
  "lanchonete"  Cardápio digital (mesa, delivery, iFood)       — Lanchonete

Cada sistema passa:
  c      os códigos com os dados do negócio, SEM escapar: {"{nome}", "{empresa}", "{cnpj}", "{endereco}", "{whatsapp}",
         "{telefone}", "{email}", "{responsavel}"} (o que faltar = vazio). Os dados ficam no sistema do cliente: aqui só
         chegam na hora de montar a página.
  s      o que está ligado (o texto só fala do que existe). Chaves de cada tipo em SITUACAO.
  links  endereços das outras páginas: {"privacidade", "termos", "cookies"} e, se houver, "contato" e "trocas".
e recebe a lista de seções: [(título, [parágrafo HTML | ("lista", [item HTML, …])])]. `miolo(secoes)` monta o HTML.
Mudou o texto? Trocar ATUALIZADO_EM (aparece no topo das páginas). Revisão por advogado: recomendada uma vez.
"""

from .texto import e

ATUALIZADO_EM = "25/10/2026"
PAGINAS = {"privacidade": "Política de privacidade", "termos": "Termos de uso", "cookies": "Política de cookies"}
TIPOS = ("site", "agenda", "loja", "lanchonete")
# o que cada tipo pode dizer que está ligado (o resto fica falso)
SITUACAO = {
    "site": ("mapa", "video"),
    "agenda": ("mapa", "video", "antecedencia_min"),
    "loja": ("online", "envio", "retirada", "combinar", "emails", "novidades", "boleto", "trocas", "letras"),
    "lanchonete": ("mesas", "pedir", "delivery", "ifood", "taxa", "letras"),
}


def _ce(c):
    """Os códigos escapados (tudo o que vem do cliente passa por aqui antes de entrar no texto)."""
    chaves = ("{nome}", "{empresa}", "{cnpj}", "{endereco}", "{whatsapp}", "{telefone}", "{email}", "{responsavel}")
    saida = {k: e(c.get(k, "")) for k in chaves}
    saida["{empresa}"] = saida["{empresa}"] or saida["{nome}"]
    return saida


def _contato(c, links, fallback):
    meios = [m for m in (f"pelo e-mail {c['{email}']}" if c["{email}"] else "",
                         f"pelo WhatsApp {c['{whatsapp}']}" if c["{whatsapp}"] else "",
                         f"pelo telefone {c['{telefone}']}" if c["{telefone}"] and not c["{whatsapp}"] else "") if m]
    if meios:
        return " ou ".join(meios)
    if links.get("contato"):
        return f'pela página <a href="{e(links["contato"])}">Contato</a>'
    return fallback


def _quem(c):
    doc = f", CNPJ {c['{cnpj}']}" if c["{cnpj}"] else ""
    onde = f", com endereço em {c['{endereco}']}" if c["{endereco}"] else ""
    return f"<b>{c['{empresa}']}</b>{doc}{onde}"


def _lista(itens):
    return ("lista", [i for i in itens if i])


# ---------------------------------------------------------------- partes iguais para todos

def _secao_quem(c, contato, oque):
    return ("Quem cuida dos seus dados",
            [f"{oque} é de {_quem(c)}. É quem decide como os seus dados são usados (o \"controlador\", como diz a Lei "
             "Geral de Proteção de Dados, a LGPD, Lei nº 13.709/2018).",
             f"Para qualquer assunto sobre os seus dados, fale com a gente {contato}."
             + (f" A pessoa responsável é {c['{responsavel}']}." if c["{responsavel}"] else "")])


def _secao_direitos(contato, consentimento):
    return ("Os seus direitos",
            ["Pela LGPD, você pode, a qualquer momento e de graça:",
             _lista(["saber se usamos os seus dados e receber uma cópia;", "corrigir dados errados ou desatualizados;",
                     "pedir que apaguemos, bloqueemos ou deixemos sem identificação o que não for necessário;",
                     consentimento, "saber com quem compartilhamos;", "levar os seus dados para outro fornecedor."]),
             f"É só pedir {contato}. Respondemos no prazo da lei. Se achar que não foi atendido, você também pode "
             "reclamar na Autoridade Nacional de Proteção de Dados (ANPD), em gov.br/anpd."])


def _secao_mudancas():
    return ("Mudanças nesta política", ["Se esta política mudar, a versão nova aparece nesta página, com a data no topo."])


def _secao_lei(contato):
    return ("Lei e foro",
            ["Estes termos seguem as leis do Brasil, incluindo o Código de Defesa do Consumidor. Qualquer questão pode "
             "ser resolvida no foro do domicílio do consumidor.", f"Dúvidas? Fale com a gente {contato}."])


def _secao_obs(c, observacoes):
    paragrafos = [e(p.strip()) for p in str(observacoes or "").replace("\r", "").split("\n") if p.strip()]
    return [(f"Observações de {c['{nome}']}", paragrafos)] if paragrafos else []


def _nucleo_cookies(oque, guardados, terceiros, links, contato):
    return [
        ("O que são cookies", ["São pequenos arquivos que o site guarda no seu navegador. Aqui também contamos o que "
                               "fica guardado na memória do navegador (que funciona parecido)."]),
        (f"O que {oque} usa",
         ["<b>Só o necessário para funcionar.</b> Não usamos cookies de propaganda nem de estatística, e não rastreamos "
          "você em outros sites.", _lista(guardados),
          "Como são necessários para funcionar, eles não dependem de autorização. Mesmo assim, contamos todos aqui."]),
        ("Serviços de outras empresas", [_lista(terceiros)]),
        ("Como apagar", ["Você pode apagar os cookies e os dados do site quando quiser, nas configurações do seu "
                         "navegador. Algumas partes podem deixar de lembrar o que você fez antes."]),
        ("Mais informações", [f'Veja também a <a href="{e(links["privacidade"])}">Política de privacidade</a> e os '
                              f'<a href="{e(links["termos"])}">Termos de uso</a>, ou fale com a gente {contato}.']),
    ]


GOOGLE_FONTS = ("<b>Google Fonts:</b> as letras vêm do Google. O seu navegador baixa as letras de lá, e o Google "
                "recebe o seu endereço IP. Não usamos cookies dele.")
REDES = ("<b>WhatsApp, Instagram e outras redes:</b> ao tocar nesses botões, você vai para o site ou aplicativo "
         "deles, com as regras de cada um.")


# ---------------------------------------------------------------- Site simples e Agenda

def _privacidade_site(c, s, links, agenda):
    contato = _contato(c, links, "pelos contatos deste site")
    dados = ["<b>Formulário de contato:</b> nome, WhatsApp, o serviço de interesse e a mensagem que você escrever. "
             "Eles são enviados para o nosso WhatsApp e ficam guardados para a gente responder e acompanhar o seu pedido."]
    if agenda:
        dados += ["<b>Agendamento:</b> nome, WhatsApp, o serviço, quem vai atender, o dia e o horário.",
                  "<b>Histórico de atendimentos:</b> os horários marcados, atendidos, cancelados ou perdidos e os valores "
                  "pagos, para mostrar na sua área do cliente e organizar o nosso trabalho.",
                  "<b>Área do cliente:</b> o código de acesso que você cria. Ele é guardado cifrado, e nem a nossa equipe "
                  "consegue ver qual é."]
    dados.append("<b>Registros técnicos:</b> quando você abre o site, o servidor recebe dados como o endereço IP e o "
                 "horário do acesso. Eles servem para segurança (por exemplo, bloquear quem tenta invadir) e são guardados "
                 "só pelo tempo que a lei pede.")
    usos = ["responder o seu contato pelo WhatsApp;"]
    if agenda:
        usos += ["marcar, confirmar, remarcar e cancelar os seus horários;", "mostrar o seu histórico na área do cliente;",
                 "de vez em quando, mandar uma mensagem convidando você a voltar. Se não quiser receber, é só pedir;"]
    usos += ["manter o site seguro e funcionando;", "cumprir obrigações da lei."]
    return [
        _secao_quem(c, contato, "Este site"),
        ("Que dados coletamos", ["Só o necessário para atender você:", _lista(dados),
                                 "Não pedimos CPF, dados de cartão nem dados sensíveis (como saúde, religião ou "
                                 "orientação sexual). Por favor, não escreva esse tipo de informação na mensagem."]),
        ("Para que usamos", [_lista(usos), "Nunca vendemos nem alugamos os seus dados."]),
        ("Por que podemos usar (base legal)",
         [_lista(["<b>O seu consentimento</b>, quando você marca a autorização do formulário;",
                  "<b>A execução do serviço que você pediu</b>, quando você marca um horário;" if agenda else "",
                  "<b>O nosso legítimo interesse</b>, para a segurança do site"
                  + (" e para convidar você a voltar (você pode recusar a qualquer momento);" if agenda else ";"),
                  "<b>O cumprimento de obrigações legais.</b>"])]),
        ("Com quem compartilhamos",
         [_lista(["<b>Injex Soluções</b>, empresa que fornece e hospeda este site"
                  + (" e o sistema de agendamento" if agenda else "") + ". Ela só trata os dados por nossa conta e com "
                  "segurança;",
                  "<b>WhatsApp (Meta)</b>, quando você escolhe falar com a gente por lá. A conversa segue as regras do "
                  "próprio WhatsApp;", "<b>autoridades</b>, só quando a lei ou um juiz mandar."])]),
        ("Por quanto tempo guardamos",
         ["Guardamos os seus dados enquanto forem necessários para os usos acima"
          + (" (por exemplo, enquanto você for nosso cliente)" if agenda else "")
          + ". Depois, apagamos ou deixamos sem identificação, a não ser o que a lei mande guardar por mais tempo."]),
        _secao_direitos(contato, "retirar o consentimento e deixar de receber mensagens;"),
        ("Segurança",
         ["O site só abre com conexão segura (https). "
          + ("Os códigos de acesso são guardados cifrados e só a nossa equipe, com código pessoal, entra no sistema. "
             if agenda else "Só a nossa equipe, com código pessoal, vê os contatos recebidos. ")
          + "Nenhum sistema é 100% à prova de falhas. Se acontecer algum incidente que coloque você em risco, avisamos "
            "você e a ANPD, como manda a lei."]),
        ("Cookies", [f'O que o site guarda no seu navegador está explicado na <a href="{e(links["cookies"])}">Política de '
                     "cookies</a>." + (" O mapa do Google só carrega quando você toca em \"Ver o mapa\"." if s["mapa"] else "")]),
        _secao_mudancas(),
    ]


def _termos_site(c, s, links, observacoes, agenda):
    contato = _contato(c, links, "pelos contatos deste site")
    secoes = [
        ("Aceite", [f"Estes termos valem para quem usa o site de <b>{c['{nome}']}</b>. Ao usar o site"
                    + (" ou marcar um horário" if agenda else "") + ", você concorda com eles e com a "
                    f'<a href="{e(links["privacidade"])}">Política de privacidade</a>.']),
        ("Sobre o site",
         ["O site mostra os nossos serviços, fotos, horários e formas de contato. Os preços e as informações são uma "
          "referência e podem mudar sem aviso. O valor final é o combinado no atendimento.",
          "Mandar uma mensagem pelo formulário ou pelo WhatsApp não garante vaga nem preço: a gente responde e combina "
          "com você."]),
    ]
    if agenda:
        minutos = int(s.get("antecedencia_min") or 0)
        horas = minutos // 60
        folga = f"{horas} hora{'s' if horas > 1 else ''}" if minutos % 60 == 0 and horas else f"{minutos} minutos"
        secoes += [
            ("Agendamento",
             [_lista([f"Os horários livres aparecem no site. Dá para marcar com pelo menos {folga} de antecedência.",
                      "O horário fica garantido quando aparece a tela de \"Horário marcado\". Se duas pessoas tentarem o "
                      "mesmo horário ao mesmo tempo, fica com quem confirmou primeiro.",
                      "Use o seu nome verdadeiro e o seu WhatsApp. É por ele que a gente fala com você.",
                      "Para remarcar ou cancelar, use o link da confirmação, a área do cliente ou o WhatsApp. Avise o "
                      "quanto antes: assim outra pessoa pode usar o horário.",
                      "Atrasos podem diminuir o tempo do atendimento ou fazer o horário ser remarcado.",
                      "Quem falta muitas vezes sem avisar pode passar a ter que confirmar o horário antes, ou marcar só "
                      "pelo WhatsApp.",
                      "O pagamento é feito no local, nas formas que aceitamos, pelo preço combinado."])]),
            ("Área do cliente",
             ["Na área do cliente você vê os seus próximos horários, o histórico e quanto já gastou. O código de acesso é "
              "pessoal: não passe para ninguém. Esqueceu? Peça para a gente zerar e crie outro no próximo agendamento."]),
        ]
    secoes += [
        ("Uso correto", ["Não é permitido usar o site para mandar informação falsa, ofender alguém, marcar horários de "
                         "mentira ou tentar invadir ou atrapalhar o sistema. Nesses casos podemos bloquear o acesso."]),
        ("Conteúdo do site", [f"Os textos, fotos, logo e marca são de {c['{nome}']} ou usados com autorização. Não copie "
                              "sem pedir."]),
        ("Links de outros sites", ["Os botões do WhatsApp, Instagram e Google Maps levam para outros sites, que têm as "
                                   "próprias regras."]),
        ("Responsabilidade", ["Fazemos o possível para o site ficar sempre no ar e com informações certas, mas ele pode "
                              "sair do ar por alguns momentos (manutenção, internet ou falhas fora do nosso controle)."
                              + (" Se o site estiver fora do ar, marque pelo WhatsApp." if agenda else "")]),
    ]
    return secoes + _secao_obs(c, observacoes) + [_secao_lei(contato)]


def _cookies_site(c, s, links, agenda):
    contato = _contato(c, links, "pelos contatos deste site")
    guardados = ["<b>Aviso de cookies:</b> lembra que você já viu este aviso, para não aparecer de novo."]
    if agenda:
        guardados += ["<b>Seu agendamento:</b> lembra o seu último horário marcado neste aparelho, para abrir a "
                      "confirmação de novo.",
                      "<b>Área do cliente:</b> quando você entra com o seu código, um cookie mantém você conectado. Ao "
                      "tocar em Sair, ele é apagado."]
    guardados.append("<b>Painel da equipe:</b> só para quem trabalha aqui e entra com código.")
    terceiros = [GOOGLE_FONTS,
                 "<b>Google Maps:</b> o mapa só carrega quando você toca em \"Ver o mapa\". A partir daí, o Google pode "
                 "usar cookies próprios, conforme a política dele." if s["mapa"] else "",
                 "<b>YouTube:</b> o vídeo só carrega quando você toca no ▶ (antes aparece só a capa). A partir daí, o "
                 "YouTube pode usar cookies próprios, conforme a política dele." if s["video"] else "",
                 REDES]
    return _nucleo_cookies("este site", guardados, terceiros, links, contato)


# ---------------------------------------------------------------- Loja virtual

def _privacidade_loja(c, s, links):
    contato = _contato(c, links, "pelos contatos desta loja")
    dados = []
    if s["online"]:
        dados += ["<b>Na compra:</b> nome, e-mail, WhatsApp, CPF, endereço de entrega, os produtos, os valores e o cupom "
                  "usado. O CPF é pedido pelo Mercado Pago e pelas transportadoras, e serve para a nota.",
                  "<b>No pagamento:</b> é feito na página segura do Mercado Pago. Nós <b>não vemos nem guardamos</b> o "
                  "número do seu cartão."]
    if s["novidades"]:
        dados.append("<b>Lista de novidades:</b> nome e e-mail, só se você se cadastrar no rodapé.")
    dados += ["<b>Atendimento:</b> o que você mandar pelo WhatsApp, e-mail ou Instagram.",
              "<b>Visitas ao site:</b> contamos só quantas visitas cada página teve, <b>sem</b> guardar IP, nome ou "
              "cookie. Os registros técnicos do servidor (IP e horário) servem para segurança e são guardados só pelo "
              "tempo que a lei pede."]
    usos = ["separar, entregar e acompanhar o seu pedido;" if s["online"] else "",
            "mandar os e-mails do pedido (confirmação, envio e, se o pagamento não terminar, um lembrete);"
            if s["online"] and s["emails"] else "",
            "mandar novidades e promoções, só se você pediu (cada e-mail tem o link para sair da lista);"
            if s["novidades"] else "",
            "responder você no atendimento e nas trocas;", "emitir nota e cumprir outras obrigações da lei;",
            "manter o site seguro."]
    parceiros = ["<b>Injex Soluções</b>, que fornece e hospeda o site e o sistema da loja. Ela só trata os dados por "
                 "nossa conta e com segurança;",
                 "<b>Mercado Pago</b>, que recebe o pagamento (Pix, cartão" + (" ou boleto" if s["boleto"] else "") + ");"
                 if s["online"] else "",
                 "<b>SuperFrete / Melhor Envio e os Correios ou a transportadora</b>, que levam o pedido até você (nome, "
                 "CPF, endereço e telefone);" if s["envio"] else "",
                 "<b>Brevo</b>, o serviço que manda os nossos e-mails;" if s["emails"] else "",
                 "<b>WhatsApp (Meta)</b>, quando você escolhe falar com a gente por lá;",
                 "<b>autoridades</b>, só quando a lei ou um juiz mandar."]
    bases = ["<b>a compra que você fez</b> (para entregar o pedido);" if s["online"] else "",
             "<b>o seu consentimento</b>, para a lista de novidades;" if s["novidades"] else "",
             "<b>o nosso legítimo interesse</b>, para a segurança do site"
             + (" e o lembrete de pagamento não terminado;" if s["online"] and s["emails"] else ";"),
             "<b>obrigações da lei</b>, como as fiscais."]
    return [
        _secao_quem(c, contato, "Esta loja"),
        ("Que dados coletamos", [_lista(dados), "Não pedimos dados sensíveis (como saúde, religião ou orientação sexual)."]),
        ("Para que usamos", [_lista(usos), "Nunca vendemos nem alugamos os seus dados."]),
        ("Por que podemos usar (base legal)", [_lista(bases)]),
        ("Com quem compartilhamos", [_lista(parceiros)]),
        ("Por quanto tempo guardamos",
         ["Os dados dos pedidos ficam guardados pelo tempo que a lei pede (por exemplo, 5 anos para os dados fiscais). "
          "Os da lista de novidades, até você sair dela. O resto, só enquanto for necessário. Depois, apagamos ou "
          "deixamos sem identificação."]),
        _secao_direitos(contato, "retirar o consentimento e sair da lista de novidades;"),
        ("Segurança",
         ["O site só abre com conexão segura (https), o pagamento é feito no Mercado Pago e só a nossa equipe, com código "
          "pessoal, entra no sistema da loja. Nenhum sistema é 100% à prova de falhas: se acontecer algum incidente que "
          "coloque você em risco, avisamos você e a ANPD, como manda a lei."]),
        ("Cookies", [f'O que o site guarda no seu navegador está na <a href="{e(links["cookies"])}">Política de '
                     "cookies</a>."]),
        _secao_mudancas(),
    ]


def _termos_loja(c, s, links, observacoes):
    contato = _contato(c, links, "pelos contatos desta loja")
    empresa = f" ({c['{empresa}']}, CNPJ {c['{cnpj}']})" if c["{cnpj}"] else ""
    secoes = [
        ("Aceite", [f"Estes termos valem para quem usa o site de <b>{c['{nome}']}</b>{empresa}. Ao navegar ou comprar, "
                    f'você concorda com eles e com a <a href="{e(links["privacidade"])}">Política de privacidade</a>.']),
        ("Produtos e preços",
         [_lista(["As fotos mostram o produto do jeito mais fiel possível, mas a cor pode variar um pouco de tela para "
                  "tela.",
                  "O preço que vale é o do site no momento da compra. Se aparecer um erro evidente de preço, avisamos "
                  "você antes de enviar, e você escolhe se quer continuar ou receber o dinheiro de volta.",
                  "Promoções e cupons valem pelo prazo e pelas regras de cada um."])]),
    ]
    if s["online"]:
        formas = ", ".join(f for f in ("Pix (aprovação na hora)", "cartão de crédito", "boleto" if s["boleto"] else "") if f)
        secoes.append(("Pedido e pagamento",
                       [_lista([f"O pagamento é feito no Mercado Pago: {formas}.",
                                "O pedido é confirmado quando o pagamento é aprovado. Se o produto acabar antes disso, "
                                "avisamos e devolvemos todo o valor.",
                                "Guarde o número do pedido: é por ele que acompanhamos a sua compra."])]))
        entrega = ["<b>Receber em casa:</b> pelos Correios ou transportadora. O valor e o prazo aparecem antes de pagar, e "
                   "o prazo conta a partir da aprovação do pagamento." if s["envio"] else "",
                   "<b>Retirar na loja:</b> sem frete" + (f", em {c['{endereco}']}" if c["{endereco}"] else "")
                   + ". Avisamos quando estiver separado." if s["retirada"] else "",
                   "<b>Combinar o frete pelo WhatsApp:</b> você paga os produtos no site e o frete é combinado com a gente "
                   "depois." if s["combinar"] else ""]
        if any(entrega):
            secoes.append(("Entrega", [_lista(entrega), "Confira o endereço antes de pagar. Se o pedido voltar por "
                                                        "endereço errado ou por ninguém receber, o novo envio é cobrado."]))
    trocas = (f' As regras de troca estão em <a href="{e(links["trocas"])}">Trocas e devoluções</a>.'
              if s["trocas"] and links.get("trocas") else "")
    mp = ", e a página de pagamento do Mercado Pago," if s["online"] else ""
    secoes += [
        ("Arrependimento, trocas e devoluções",
         ["Nas compras pelo site, você pode desistir em até <b>7 dias</b> depois de receber, sem precisar dizer o motivo "
          "(Código de Defesa do Consumidor, art. 49). Devolvemos todo o valor pago, inclusive o frete. É só falar com a "
          f"gente {contato} e devolver o produto sem uso.{trocas}",
          "Produto com defeito: fale com a gente, que resolvemos como manda o Código de Defesa do Consumidor."]),
        ("Uso correto", ["Não é permitido usar o site para fazer pedidos falsos, usar dados de outra pessoa ou tentar "
                         "invadir ou atrapalhar o sistema. Nesses casos podemos cancelar o pedido e bloquear o acesso."]),
        ("Conteúdo do site", [f"Os textos, fotos, logo e marca são de {c['{nome}']} ou usados com autorização. Não copie "
                              "sem pedir."]),
        ("Links de outros sites", [f"Os botões do WhatsApp, Instagram e das outras redes{mp} são de outras empresas, com "
                                   "as próprias regras."]),
    ]
    return secoes + _secao_obs(c, observacoes) + [_secao_lei(contato)]


def _cookies_loja(c, s, links):
    contato = _contato(c, links, "pelos contatos desta loja")
    guardados = ["<b>Carrinho e cupom:</b> o que você pôs no carrinho e o cupom digitado, para não perder ao fechar a "
                 "página.", "<b>CEP:</b> para calcular o frete de novo sem digitar.",
                 "<b>Seus dados de entrega:</b> depois de uma compra, este aparelho lembra o nome, e-mail, telefone e "
                 "endereço para a próxima (o CPF não fica guardado). Em aparelho que outras pessoas usam, apague os dados "
                 "do site no navegador." if s["online"] else "",
                 "<b>Aviso de cookies:</b> lembra que você já viu este aviso.",
                 "<b>Sistema da loja:</b> só para a nossa equipe, que entra com código."]
    terceiros = [GOOGLE_FONTS if s["letras"] else "",
                 "<b>Mercado Pago:</b> quando você vai pagar, abre a página do Mercado Pago, que tem cookies e regras "
                 "próprias." if s["online"] else "", REDES]
    secoes = _nucleo_cookies("este site", guardados, terceiros, links, contato)
    secoes[1][1][0] = ("<b>Só o necessário para a loja funcionar.</b> Não usamos cookies de propaganda nem de "
                       "rastreamento, e as visitas são contadas sem cookie e sem guardar quem você é.")
    return secoes


# ---------------------------------------------------------------- Cardápio digital (lanchonete)

def _privacidade_lanchonete(c, s, links):
    contato = _contato(c, links, "no balcão")
    dados = ["<b>Pedido pelo celular na mesa:</b> o seu nome (se você quiser pôr) e os itens escolhidos." if s["pedir"] else "",
             "<b>Delivery:</b> nome, telefone, endereço de entrega e o pedido, que você passa para a gente pelo WhatsApp "
             "ou telefone." if s["delivery"] else "",
             "<b>Pedidos pelo iFood:</b> os dados que o iFood nos repassa para preparar e entregar o pedido (o iFood tem a "
             "própria política de privacidade)." if s["ifood"] else "",
             "<b>Atendimento:</b> o que você mandar pelo WhatsApp ou Instagram.",
             "<b>Registros técnicos:</b> ao abrir o cardápio, o servidor recebe dados como o endereço IP e o horário. Eles "
             "servem para segurança e são guardados só pelo tempo que a lei pede."]
    return [
        _secao_quem(c, contato, "Este cardápio"),
        ("Que dados coletamos", ["Só o necessário para atender você. Para ver o cardápio, não precisa se cadastrar.",
                                 _lista(dados), "Não pedimos CPF, dados de cartão nem dados sensíveis. Se tiver alguma "
                                                "alergia, conte direto para a equipe."]),
        ("Para que usamos", [_lista(["preparar, servir e entregar o seu pedido;",
                                     "fechar a conta da mesa;" if s["mesas"] else "",
                                     "avisar pelo WhatsApp quando o pedido sair para entrega;" if s["delivery"] else "",
                                     "responder você no atendimento;", "cumprir obrigações da lei;",
                                     "manter o cardápio seguro."]),
                             "Nunca vendemos nem alugamos os seus dados."]),
        ("Por que podemos usar (base legal)", [_lista(["<b>O pedido que você fez</b> (para preparar e entregar);",
                                                       "<b>O nosso legítimo interesse</b>, para a segurança do sistema;",
                                                       "<b>Obrigações da lei</b>, como as fiscais."])]),
        ("Com quem compartilhamos",
         [_lista(["<b>Injex Soluções</b>, que fornece e hospeda o cardápio digital e o sistema da lanchonete. Ela só trata "
                  "os dados por nossa conta e com segurança;", "<b>iFood</b>, nos pedidos feitos por lá;" if s["ifood"] else "",
                  "<b>WhatsApp (Meta)</b>, quando você escolhe falar com a gente por lá;",
                  "<b>autoridades</b>, só quando a lei ou um juiz mandar."])]),
        ("Por quanto tempo guardamos", ["Os dados dos pedidos ficam guardados pelo tempo que a lei pede (por exemplo, para "
                                        "as obrigações fiscais). O resto, só enquanto for necessário. Depois, apagamos ou "
                                        "deixamos sem identificação."]),
        _secao_direitos(contato, ""),
        ("Segurança", ["O cardápio abre com conexão segura (https) e só a nossa equipe, com código pessoal, entra no "
                       "sistema. Nenhum sistema é 100% à prova de falhas: se acontecer algum incidente que coloque você em "
                       "risco, avisamos você e a ANPD, como manda a lei."]),
        ("Cookies", [f'O que o cardápio guarda no seu celular está na <a href="{e(links["cookies"])}">Política de '
                     "cookies</a>."]),
        _secao_mudancas(),
    ]


def _termos_lanchonete(c, s, links, observacoes):
    contato = _contato(c, links, "no balcão")
    secoes = [
        ("Aceite", [f"Estes termos valem para quem usa o cardápio digital de <b>{c['{nome}']}</b>. Ao usar, você concorda "
                    f'com eles e com a <a href="{e(links["privacidade"])}">Política de privacidade</a>.']),
        ("Cardápio e preços", [_lista(["As fotos são ilustrativas: a montagem pode mudar um pouco.",
                                       "Os preços e os itens disponíveis podem mudar ao longo do dia. Item que acabou some "
                                       "do cardápio.",
                                       "Tem alergia ou restrição? Avise a equipe antes de pedir. O cardápio não substitui "
                                       "essa conversa."])]),
    ]
    if s["mesas"]:
        taxa = str(s.get("taxa") or "")
        secoes.append(("Na mesa", [_lista([
            "O QR Code de cada mesa é só daquela mesa: ele libera chamar o garçom e pedir a conta.",
            "O pedido feito pelo celular só vai para a cozinha depois que alguém da equipe confirma. Você paga no fim, "
            "junto com a conta." if s["pedir"] else "",
            f"A taxa de serviço ({e(taxa)}%) é opcional: só entra na conta se você aceitar." if taxa not in ("", "0") else ""])]))
    if s["delivery"]:
        secoes.append(("Delivery", [_lista(["A taxa de entrega depende do bairro e é informada antes de confirmar o pedido.",
                                            "O tempo de entrega é uma estimativa e pode mudar nos horários de movimento.",
                                            "Confira o endereço e o telefone: é por eles que a gente encontra você."])]))
    secoes += [
        ("Uso correto", ["Não é permitido usar o cardápio para fazer pedidos falsos, chamar o garçom de brincadeira ou "
                         "tentar atrapalhar o sistema. Nesses casos podemos bloquear o pedido pelo celular."]),
        ("Conteúdo", [f"Os textos, fotos, logo e marca são de {c['{nome}']} ou usados com autorização. Não copie sem "
                      "pedir."]),
    ]
    return secoes + _secao_obs(c, observacoes) + [_secao_lei(contato)]


def _cookies_lanchonete(c, s, links):
    contato = _contato(c, links, "no balcão")
    guardados = ["<b>Sacola do pedido:</b> o que você escolheu na mesa, até enviar o pedido." if s["pedir"] else "",
                 "<b>Aviso de cookies:</b> lembra que você já viu este aviso."]
    return _nucleo_cookies("o cardápio", guardados, [GOOGLE_FONTS if s["letras"] else "", REDES], links, contato)


# ---------------------------------------------------------------- entrada

def secoes(qual, tipo, codigos, situacao, links, observacoes=""):
    """As seções de uma página legal. `qual` = privacidade | termos | cookies; `tipo` = um de TIPOS."""
    if qual not in PAGINAS or tipo not in TIPOS:
        raise ValueError(f"página ou tipo desconhecido: {qual}, {tipo}")
    c = _ce(codigos)
    s = {k: situacao.get(k) for k in SITUACAO[tipo]}
    for k in s:
        if k not in ("antecedencia_min", "taxa"):
            s[k] = bool(s[k])
    if tipo in ("site", "agenda"):
        agenda = tipo == "agenda"
        if qual == "privacidade":
            return _privacidade_site(c, s, links, agenda)
        return _termos_site(c, s, links, observacoes, agenda) if qual == "termos" else _cookies_site(c, s, links, agenda)
    f = {"loja": (_privacidade_loja, _termos_loja, _cookies_loja),
         "lanchonete": (_privacidade_lanchonete, _termos_lanchonete, _cookies_lanchonete)}[tipo]
    if qual == "privacidade":
        return f[0](c, s, links)
    return f[1](c, s, links, observacoes) if qual == "termos" else f[2](c, s, links)


def miolo(lista):
    """As seções em HTML (<section><h2>…</h2><p>…</p><ul>…</ul></section>). Títulos e textos já vêm escapados."""
    partes = []
    for titulo, paragrafos in lista:
        corpo = "".join("<ul>" + "".join(f"<li>{x}</li>" for x in p[1]) + "</ul>" if isinstance(p, tuple) else f"<p>{p}</p>"
                        for p in paragrafos if p)
        partes.append(f"<section><h2>{titulo}</h2>{corpo}</section>")
    return "\n".join(partes)


# ---------------------------------------------------------------- aviso de cookies (barrinha no alto, uma vez)

CSS_COOKIES = (
    ".cookies { position: fixed; left: 12px; right: 12px; top: 12px; z-index: 60; max-width: 560px; margin: 0 auto;"
    " display: none; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 14px; background: #1d1d1f;"
    " color: #f3f1ec; font: 14px/1.45 var(--corpo, system-ui, sans-serif); box-shadow: 0 10px 30px rgba(0,0,0,.3); }"
    " .cookies.aberto { display: flex; } .cookies a { color: #fff; } .cookies p { margin: 0; flex: 1; }"
    " .cookies button { flex: none; border: 0; border-radius: 99px; padding: 9px 16px;"
    " font: 600 14px/1 var(--corpo, system-ui, sans-serif); background: #fff; color: #1d1d1f; cursor: pointer; }")


def aviso_cookies(link_cookies, chave="injex_cookies_ok", oque="Este site"):
    """A barrinha: aparece uma vez por navegador (guarda na memória dele; sem memória, aparece de novo e tudo bem).
    Fica no alto para não cobrir os botões de WhatsApp, agendar e carrinho. Precisa do CSS_COOKIES na página."""
    return (f'<div class="cookies" id="cookies" role="region" aria-label="Aviso de cookies"><p>{e(oque)} usa só o '
            f'necessário para funcionar, sem propaganda e sem rastrear você. <a href="{e(link_cookies)}">Saiba mais</a>'
            f'</p><button type="button">Entendi</button></div>'
            "<script>(function () { var c = document.getElementById('cookies'), k = " + repr(chave) + ";"
            " try { if (localStorage.getItem(k)) return; } catch (x) { /* sem memória */ }"
            " c.classList.add('aberto');"
            " c.querySelector('button').onclick = function () { c.classList.remove('aberto');"
            " try { localStorage.setItem(k, '1'); } catch (x) { /* */ } };"
            " })();</script>")
