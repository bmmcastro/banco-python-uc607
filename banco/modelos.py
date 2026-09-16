#estruturas do sistema
from dataclasses import dataclass

from banco.erros import SaldoInsuficienteError


@dataclass
class Conta:
    username: str
    password: str
    valor: float
    iban: str

    def depositar(self, valor):
        if valor <= 0:
            raise ValueError("O valor do depósito tem de ser positivo")

        self.valor = self.valor + valor

    def levantar(self, valor):
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
