# arranque do programa
import pyfiglet

from banco.dados import criar_tabelas, carregar_dados, criar_dados_iniciais
from banco.menus import menu_principal

# o if é obrigatório no Windows: os processos do relatório voltam a ler
# este ficheiro, e sem a proteção cada um deles tentava arrancar o programa
# outra vez
if __name__ == "__main__":
    print(pyfiglet.figlet_format("Banco Python UC607"))

    # dados do sistema: carregar do ficheiro banco.db
    criar_tabelas()
    utilizadores, contas, transacoes, aplicacoes = carregar_dados()

    # primeira execução (ficheiro ainda vazio): criar utilizadores de teste
    # para testar as transações
    if len(contas) == 0:
        utilizadores, contas, transacoes = criar_dados_iniciais()

        print(f"Utilizador de teste: {utilizadores['bruno']}")
        print(f"Conta de teste: {contas['bruno']}")
        print(f"Conta de teste: {contas['ana']}")
        print(f"Transação de teste: {transacoes[0]}")

    print(f"Contas no sistema: {contas.keys()}")
    print("")

    # menu principal do programa
    menu_principal(utilizadores, contas, transacoes, aplicacoes)

    print(f"Contas no sistema: {contas.keys()}")
    print(f"Transações: {transacoes}")
