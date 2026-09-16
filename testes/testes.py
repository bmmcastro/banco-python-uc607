#testes ao sistema (correr com: python testes.py)
import unittest

from banco.modelos import Conta
from banco.operacoes import criar_conta, transferir, entrar, transferir_por_ficheiro
from banco.dados import limpar_tentativas
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError


class TestesBanco(unittest.TestCase):

    def setUp(self):
        #contas de teste usadas por todos os testes
        self.contas = {}
        self.transacoes = []
        self.contas["bruno"] = Conta("bruno", "bruno123", 100, "PT50 0001")
        self.contas["ana"] = Conta("ana", "ana123", 200, "PT50 0002")

        #limpar as tentativas de login para cada teste começar igual
        limpar_tentativas("brunoteste")

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

    def test_bloqueio_depois_de_tentativas_erradas(self):
        #a terceira password errada bloqueia a conta
        entrar(self.contas, "brunoteste", "errada1")
        entrar(self.contas, "brunoteste", "errada2")
        with self.assertRaises(ContaBloqueadaError):
            entrar(self.contas, "brunoteste", "errada3")

        #bloqueada: o login não entra, nem com outra password
        with self.assertRaises(ContaBloqueadaError):
            entrar(self.contas, "brunoteste", "outra")

        #arranjar o utilizador de teste para os próximos testes
        limpar_tentativas("brunoteste")

    def test_login_certo_reseta_as_tentativas(self):
        #um login certo esquece as tentativas erradas anteriores
        entrar(self.contas, "bruno", "errada1")
        entrar(self.contas, "bruno", "errada2")
        conta = entrar(self.contas, "bruno", "bruno123")
        self.assertEqual(conta.username, "bruno")

    def test_transferencia_por_ficheiro_ok(self):
        #um ficheiro certo transfere tudo de uma vez
        conteudo = "iban,nome,valor\nPT50 0001,bruno,10\n"
        erros = transferir_por_ficheiro(self.contas, self.transacoes, "ana", conteudo)

        self.assertEqual(erros, [])
        self.assertEqual(self.contas["ana"].valor, 190)    #200 - 10
        self.assertEqual(self.contas["bruno"].valor, 110)  #100 + 10
        self.assertEqual(len(self.transacoes), 1)

    def test_transferencia_por_ficheiro_com_erro_nada_transfere(self):
        #nome errado numa linha => erro e nenhuma transferência é feita
        conteudo = "iban,nome,valor\nPT50 0001,bruno,10\nPT50 0001,ana,5\n"
        erros = transferir_por_ficheiro(self.contas, self.transacoes, "ana", conteudo)

        self.assertEqual(len(erros), 1)
        self.assertEqual(self.contas["ana"].valor, 200)  #nada mudou
        self.assertEqual(len(self.transacoes), 0)


if __name__ == "__main__":
    unittest.main()
