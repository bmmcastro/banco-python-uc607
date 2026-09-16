#testes ao sistema (correr com: python testes.py)
import unittest

from banco.modelos import Conta
from banco.operacoes import criar_conta, transferir
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError


class TestesBanco(unittest.TestCase):

    def setUp(self):
        #contas de teste usadas por todos os testes
        self.contas = {}
        self.transacoes = []
        self.contas["bruno"] = Conta("bruno", "bruno123", 100, "PT50 0001")
        self.contas["ana"] = Conta("ana", "ana123", 200, "PT50 0002")

    def test_utilizador_duplicado(self):
        #criar um utilizador que já existe tem de dar erro
        with self.assertRaises(UtilizadorJaExisteError):
            criar_conta(self.contas, "bruno", "outra123")

    def test_utilizador_inexistente(self):
        #transferir para um IBAN que não existe tem de dar erro
        with self.assertRaises(UtilizadorInexistenteError):
            transferir(self.contas, self.transacoes, "bruno", "PT50 9999", 10)

    def test_saldo_insuficiente(self):
        #levantar mais do que o saldo tem de dar erro
        with self.assertRaises(SaldoInsuficienteError):
            self.contas["bruno"].levantar(500)

    def test_deposito(self):
        #depositar aumenta o saldo
        self.contas["bruno"].depositar(50)
        self.assertEqual(self.contas["bruno"].valor, 150)

    def test_levantamento(self):
        #levantar diminui o saldo
        self.contas["bruno"].levantar(30)
        self.assertEqual(self.contas["bruno"].valor, 70)


if __name__ == "__main__":
    unittest.main()
