#testes ao sistema (correr com: python testes.py)
import os
import unittest

from banco.modelos import Utilizador, Conta, Aplicacao
from banco.operacoes import criar_utilizador, transferir, entrar, transferir_por_ficheiro, pesquisar_transacoes, consultar_retorno, aplicar_dinheiro, verificar_aplicacoes, situacao_aplicacao
from banco.dados import limpar_tentativas, guardar_ficheiro_transferencias, ler_ficheiro_transferencias, apagar_ficheiro_transferencias, guardar_csv, apagar_ficheiro_transacoes, guardar_no_historico, listar_historico_aplicacoes
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError
from banco.relatorio import relatorio_contas, relatorio_transferencias


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
        limpar_tentativas("bruno")
        limpar_tentativas("ana")

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
        entrar(self.utilizadores, "ana", "errada1")
        entrar(self.utilizadores, "ana", "errada2")
        with self.assertRaises(ContaBloqueadaError):
            entrar(self.utilizadores, "ana", "errada3")

        #bloqueada: o login não entra, nem com outra password
        with self.assertRaises(ContaBloqueadaError):
            entrar(self.utilizadores, "ana", "ana123")

        #arranjar a utilizadora para os próximos testes
        limpar_tentativas("ana")

    def test_login_certo_reseta_as_tentativas(self):
        #um login certo esquece as tentativas erradas anteriores
        entrar(self.utilizadores, "bruno", "errada1")
        entrar(self.utilizadores, "bruno", "errada2")
        utilizador = entrar(self.utilizadores, "bruno", "bruno123")
        self.assertEqual(utilizador.username, "bruno")

    def test_entrar_com_username_inexistente(self):
        #tentar entrar com um username que não existe lança a exceção
        with self.assertRaises(UtilizadorInexistenteError):
            entrar(self.utilizadores, "zeza", "qualquer123")

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

    def test_deposito_com_valor_invalido(self):
        #infinito e nan não são valores válidos para dinheiro
        with self.assertRaises(ValueError):
            self.contas["bruno"].depositar(float("inf"))
        with self.assertRaises(ValueError):
            self.contas["bruno"].depositar(float("nan"))

    def test_transferencia_com_valor_invalido(self):
        #uma transferência com infinito não pode passar
        with self.assertRaises(ValueError):
            transferir(self.contas, self.transacoes, "bruno", "PT50 0002", float("inf"))

    def test_retorno_com_taxa_negativa(self):
        #a taxa pode ser negativa (entre -100 e 100) e diminui o valor
        resultado = consultar_retorno(200, -50, 2)
        self.assertAlmostEqual(resultado, 50.0)  #200 * 0,5 * 0,5

    def test_retorno_valida_taxa_e_meses(self):
        #a taxa fora do valor absoluto 0-100 e os meses fora de 1-12 dão erro
        with self.assertRaises(ValueError):
            consultar_retorno(100, -101, 5)
        with self.assertRaises(ValueError):
            consultar_retorno(100, 10, 0)
        with self.assertRaises(ValueError):
            consultar_retorno(100, 10, 13)

    def test_aplicar_tira_o_valor_do_saldo(self):
        #aplicar 50 com saldo 100: o valor sai do saldo e fica cativo
        aplicacoes = []
        aplicar_dinheiro(self.contas["bruno"], aplicacoes, 50, 10, 3)

        self.assertEqual(self.contas["bruno"].valor, 50)
        self.assertEqual(len(aplicacoes), 1)

        #aplicar mais do que o saldo não pode passar
        with self.assertRaises(SaldoInsuficienteError):
            aplicar_dinheiro(self.contas["bruno"], aplicacoes, 100, 10, 3)

    def test_aplicacao_no_fim_do_prazo_devolve_com_juros(self):
        #aplicação com o prazo já passado: o valor volta ao saldo com os juros
        aplicacao = Aplicacao("bruno", 100, 10, 2, "01/01/2026 10:00")
        aplicacoes = [aplicacao]

        libertadas = verificar_aplicacoes(self.contas["bruno"], aplicacoes)

        self.assertEqual(len(libertadas), 1)
        self.assertEqual(len(aplicacoes), 0)  #saiu das ativas
        self.assertAlmostEqual(self.contas["bruno"].valor, 221.0)  #100 do saldo + 100 * 1,1 * 1,1

    def test_aplicacao_libertada_fica_no_historico(self):
        #quando liberta, o valor_final fica preenchido e a aplicação entra no histórico
        aplicacao = Aplicacao("ana", 200, -50, 2, "01/01/2026 10:00")

        libertadas = verificar_aplicacoes(self.contas["ana"], [aplicacao])
        self.assertAlmostEqual(libertadas[0].valor_final, 50.0)  #200 * 0,5 * 0,5

        guardar_no_historico(libertadas[0])
        historico = listar_historico_aplicacoes("ana")
        self.assertEqual(len(historico), 1)
        self.assertAlmostEqual(historico[0].valor_final, 50.0)

        #arranjar para os próximos testes
        import sqlite3
        ligacao = sqlite3.connect("banco.db")
        ligacao.execute("DELETE FROM historico_aplicacoes WHERE username = 'ana'")
        ligacao.commit()
        ligacao.close()

    def test_relatorio_contas(self):
        #maior saldo, menor saldo e soma de todos os saldos
        resultado = relatorio_contas(self.contas)

        self.assertEqual(resultado["maior"], [200, ["ana"]])
        self.assertEqual(resultado["menor"], [100, ["bruno"]])
        self.assertEqual(resultado["soma"], 300)

    def test_relatorio_transferencias(self):
        #quem mais recebeu, quem mais enviou e o total transferido
        transferir(self.contas, self.transacoes, "bruno", "PT50 0002", 10)
        transferir(self.contas, self.transacoes, "bruno", "PT50 0002", 5)
        transferir(self.contas, self.transacoes, "ana", "PT50 0001", 3)

        resultado = relatorio_transferencias(self.transacoes)

        self.assertEqual(resultado["mais_recebeu"], [15, ["ana"]])
        self.assertEqual(resultado["mais_enviou"], [15, ["bruno"]])
        self.assertEqual(resultado["total"], 18)

    def test_situacao_aplicacao(self):
        #uma aplicação a meio do prazo: já rendeu os meses passados e faltam os dias restantes
        from datetime import datetime, timedelta
        fim = datetime.now() + timedelta(days=40)
        aplicacao = Aplicacao("bruno", 100, 10, 3, fim.strftime("%d/%m/%Y %H:%M"))

        valor_hoje, dias_restantes = situacao_aplicacao(aplicacao)

        #começou há 50 dias (90 - 40): passou 1 mês completo, já rendeu uma vez
        self.assertAlmostEqual(valor_hoje, 110.0)
        #39 e não 40: a data guardada não tem segundos, fica um pouco atrás
        self.assertEqual(dias_restantes, 39)


if __name__ == "__main__":
    unittest.main()
