#arranque do programa
import pyfiglet

from banco.modelos import Utilizador, Conta, Transacao
from banco.dados import criar_tabelas, carregar_dados
from banco.menus import menu_principal

print(pyfiglet.figlet_format("Banco Python UC607"))

#dados do sistema: carregar do ficheiro banco.db
criar_tabelas()
utilizadores, contas, transacoes = carregar_dados()

#primeira execução (ficheiro ainda vazio): criar utilizadores de teste para testar as transações
if len(contas) == 0:
    utilizadores["bruno"] = Utilizador("bruno", "bruno123")
    contas["bruno"] = Conta("bruno", 100, "PT50 0001")
    utilizadores["ana"] = Utilizador("ana", "ana123")
    contas["ana"] = Conta("ana", 200, "PT50 0002")

    #transação de teste: o bruno transferiu 50 para a ana
    #a transferência mexe nos saldos: tira ao bruno e dá à ana
    contas["bruno"].valor = contas["bruno"].valor - 50
    contas["ana"].valor = contas["ana"].valor + 50
    transacao1 = Transacao("07/09/2026 10:00", 50, "PT50 0001", "bruno", "PT50 0002", "ana")
    transacoes.append(transacao1)

    print(f"Utilizador de teste: {utilizadores['bruno']}")
    print(f"Conta de teste: {contas['bruno']}")
    print(f"Conta de teste: {contas['ana']}")
    print(f"Transação de teste: {transacao1}")

print(f"Contas no sistema: {contas.keys()}")
print("")

#menu principal do programa
menu_principal(utilizadores, contas, transacoes)

print(f"Contas no sistema: {contas.keys()}")
print(f"Transações: {transacoes}")
