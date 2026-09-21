#estruturas do sistema
import math
from dataclasses import dataclass

from banco.erros import SaldoInsuficienteError


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
