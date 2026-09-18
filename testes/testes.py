#testes ao sistema (correr com: python testes.py)
import os
import unittest

from banco.modelos import Utilizador, Conta
from banco.operacoes import criar_utilizador, transferir, entrar, transferir_por_ficheiro, pesquisar_transacoes
from banco.dados import limpar_tentativas, guardar_ficheiro_transferencias, ler_ficheiro_transferencias, apagar_ficheiro_transferencias, guardar_csv, apagar_ficheiro_transacoes
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError


class TestesBanco(unittest.TestCase):

    def setUp(self):
        #utilizadores e contas de teste usados por todos os testes
        self.utilizadores = {}
        self.contas = {}
        self.transacoes = []
        self.utilizadores["bruno"] = Utilizador("bruno", "bruno123")
        self.contas["bruno"] = Conta("bruno", 100, "PT50 0001")
        self.utilizadores["ana"] = Utilizador("ana", "ana123")
        self.contas["ana"] = Conta("ana", 200, "PT50 0002")

        #limpar as tentativas de login para cada teste começar igual
        limpar_tentativas("brunoteste")

    def test_utilizador_duplicado(self):
        #criar um utilizador que já existe tem de dar erro
        with self.assertRaises(UtilizadorJaExisteError):
            criar_utilizador(self.utilizadores, self.contas, "bruno", "outra123")

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
        entrar(self.utilizadores, "brunoteste", "errada1")
        entrar(self.utilizadores, "brunoteste", "errada2")
        with self.assertRaises(ContaBloqueadaError):
            entrar(self.utilizadores, "brunoteste", "errada3")

        #bloqueada: o login não entra, nem com outra password
        with self.assertRaises(ContaBloqueadaError):
            entrar(self.utilizadores, "brunoteste", "outra")

        #arranjar o utilizador de teste para os próximos testes
        limpar_tentativas("brunoteste")

    def test_login_certo_reseta_as_tentativas(self):
        #um login certo esquece as tentativas erradas anteriores
        entrar(self.utilizadores, "bruno", "errada1")
        entrar(self.utilizadores, "bruno", "errada2")
        utilizador = entrar(self.utilizadores, "bruno", "bruno123")
        self.assertEqual(utilizador.username, "bruno")

    def test_criar_utilizador_cria_conta_com_iban(self):
        #criar um utilizador cria também a conta a zeros com um IBAN único
        criar_utilizador(self.utilizadores, self.contas, "carla", "carla123")

        self.assertIn("carla", self.utilizadores)
        self.assertEqual(self.utilizadores["carla"].password, "carla123")
        self.assertEqual(self.contas["carla"].valor, 0)
        self.assertIn("PT50", self.contas["carla"].iban)

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

    def test_ficheiro_de_transferencias_guarda_le_apaga(self):
        #o ficheiro do utilizador vive na pasta transferencias e é apagado quando ele sai
        guardar_ficheiro_transferencias("brunoteste", "iban,nome,valor\n")
        self.assertEqual(ler_ficheiro_transferencias("brunoteste"), "iban,nome,valor\n")

        apagar_ficheiro_transferencias("brunoteste")
        with self.assertRaises(FileNotFoundError):
            ler_ficheiro_transferencias("brunoteste")

    def test_exportacao_apaga_so_o_ficheiro_do_utilizador(self):
        #exportar cria a pasta transacoes; ao sair só o ficheiro do utilizador é apagado
        guardar_csv(self.contas["bruno"], [])
        guardar_csv(self.contas["ana"], [])

        apagar_ficheiro_transacoes("bruno")
        self.assertFalse(os.path.exists("transacoes/transacoes_bruno.csv"))
        self.assertTrue(os.path.exists("transacoes/transacoes_ana.csv"))  #o dos outros fica

        #arranjar para os próximos testes
        apagar_ficheiro_transacoes("ana")

    def test_pesquisar_transacoes(self):
        #pesquisar por username, por IBAN e por data encontra as transações certas
        transferir(self.contas, self.transacoes, "bruno", "PT50 0002", 10)

        #o bruno pesquisa por "ana": encontra a transação que enviou
        encontradas = pesquisar_transacoes(self.transacoes, self.contas["bruno"], "ana")
        self.assertEqual(len(encontradas), 1)

        #a ana pesquisa pelo IBAN do bruno: encontra a que recebeu
        encontradas = pesquisar_transacoes(self.transacoes, self.contas["ana"], "PT50 0001")
        self.assertEqual(len(encontradas), 1)

        #pesquisa que não existe em nenhuma transação: não encontra nada
        encontradas = pesquisar_transacoes(self.transacoes, self.contas["bruno"], "zeze")
        self.assertEqual(len(encontradas), 0)


if __name__ == "__main__":
    unittest.main()
