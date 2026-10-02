#estruturas do sistema
import math
from dataclasses import dataclass

from banco.erros import SaldoInsuficienteError

#formato usado em todas as datas do sistema
#(transações, movimentos e aplicações: dia/mês/ano hora:minuto)
FORMATO_DATA = "%d/%m/%Y %H:%M"


@dataclass
class Utilizador:
    username: str
    password: str


@dataclass
class Conta:
    username: str
    valor: float
    iban: str

    def depositar(self, valor):
        if not math.isfinite(valor):
            raise ValueError("O valor tem de ser um número válido")

        if valor <= 0:
            raise ValueError("O valor do depósito tem de ser positivo")

        self.valor = self.valor + valor

    def levantar(self, valor):
        if not math.isfinite(valor):
            raise ValueError("O valor tem de ser um número válido")

        if valor <= 0:
            raise ValueError("O valor do levantamento tem de ser positivo")

        if valor > self.valor:
            raise SaldoInsuficienteError("Saldo insuficiente")

        self.valor = self.valor - valor


@dataclass
class Transacao:
    data: str              #data e hora em que a transação foi efetuada
    valor: float
    iban_origem: str
    username_origem: str
    iban_destino: str
    username_destino: str


@dataclass
class Aplicacao:
    username: str          #dono da aplicação
    valor: float           #valor aplicado (fica cativo)
    taxa: float            #taxa de juro mensal
    meses: int             #prazo da aplicação
    data_fim: str          #quando acaba o prazo (dd/mm/aaaa hh:mm)
    valor_final: float = None   #quanto rendeu (só fica preenchido no histórico)


@dataclass
class Movimento:
    username: str          #a quem pertence o movimento
    tipo: str              #Depósito, Levantamento, Enviada ou Recebida
    data: str              #quando aconteceu (dd/mm/aaaa hh:mm)
    valor: float
    texto: str = ""        #detalhe (origem e destino, nas transferências)
