"""🔌 Disjuntor — módulo comum da Injex (02/11/2026).

Serviço de fora caiu (SEFAZ, Gemini, Mercado Pago…): sem o disjuntor, TODA tentativa espera o tempo limite inteiro
(30–60 s) e a tela fica parada. Com ele: depois de `falhas` erros de conexão SEGUIDOS, o sistema para de insistir por
`pausa` segundos e responde na hora "<serviço> está fora do ar…". Passada a pausa, deixa UMA tentativa passar: deu certo
→ volta ao normal; falhou → mais uma pausa. Erro "de verdade" do serviço (recusou o pedido, senha errada) NÃO conta:
só conta o que a chamada marca como queda (exceções de `conta`).

    from injex_comum.disjuntor import Disjuntor, ForaDoAr
    SEFAZ = Disjuntor("SEFAZ", conta=(OSError,))
    resposta = SEFAZ.chamar(requests.post, url, ...)     # ou:  with SEFAZ.vigiar(): ...

`Disjuntor.todos()` lista o estado de cada um (para uma tela de diagnóstico). Fica na memória (reiniciar zera).
"""

import threading
import time
from contextlib import contextmanager

_TODOS: dict[str, "Disjuntor"] = {}


class ForaDoAr(ConnectionError):
    """O disjuntor está aberto: nem tentou. É um ConnectionError (quem já trata "sem internet" trata este também)."""

    def __init__(self, nome, faltam):
        minutos = max(1, round(faltam / 60))
        super().__init__(f"{nome} está fora do ar agora (não respondeu nas últimas tentativas). "
                         f"Tente de novo daqui a {minutos} minuto{'s' if minutos > 1 else ''}.")
        self.nome, self.faltam = nome, faltam


class Disjuntor:
    def __init__(self, nome: str, falhas: int = 3, pausa: float = 120.0, conta=(OSError,)):
        self.nome, self.falhas, self.pausa, self.conta = nome, falhas, pausa, tuple(conta)
        self._seguidas = 0
        self._aberto_ate = 0.0
        self._testando = False
        self._ultimo_erro = ""
        self._trava = threading.Lock()
        _TODOS[nome] = self

    # ---------- estado ----------
    def _antes(self):
        with self._trava:
            agora = time.monotonic()
            if self._seguidas < self.falhas:
                return
            if agora < self._aberto_ate or self._testando:
                raise ForaDoAr(self.nome, max(self._aberto_ate - agora, 1))
            self._testando = True  # a pausa passou: deixa esta tentativa passar (meio aberto)

    def _deu_certo(self):
        with self._trava:
            self._seguidas, self._testando, self._ultimo_erro = 0, False, ""

    def _caiu(self, erro):
        with self._trava:
            self._seguidas += 1
            self._testando = False
            self._ultimo_erro = f"{erro.__class__.__name__}: {erro}"[:200]
            if self._seguidas >= self.falhas:
                self._aberto_ate = time.monotonic() + self.pausa
                print(f"[disjuntor] {self.nome} fora do ar ({self._seguidas} falhas seguidas): pausa de "
                      f"{int(self.pausa)} s — {self._ultimo_erro}")

    def _nao_contou(self):
        with self._trava:
            self._testando = False

    # ---------- uso ----------
    @contextmanager
    def vigiar(self):
        self._antes()
        try:
            yield
        except self.conta as e:
            self._caiu(e)
            raise
        except BaseException:
            self._nao_contou()  # o serviço respondeu (com um erro dele): a ligação está viva
            raise
        else:
            self._deu_certo()

    def chamar(self, funcao, *args, **kwargs):
        with self.vigiar():
            return funcao(*args, **kwargs)

    def estado(self) -> dict:
        with self._trava:
            faltam = max(0.0, self._aberto_ate - time.monotonic()) if self._seguidas >= self.falhas else 0.0
            return {"nome": self.nome, "fora_do_ar": faltam > 0, "segundos": int(faltam),
                    "falhas_seguidas": self._seguidas, "ultimo_erro": self._ultimo_erro}

    def zerar(self):
        self._deu_certo()
        with self._trava:
            self._aberto_ate = 0.0

    @staticmethod
    def todos() -> list[dict]:
        return [d.estado() for d in _TODOS.values()]
