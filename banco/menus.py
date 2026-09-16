#menus do sistema e conversa com o utilizador
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError
from banco.operacoes import criar_conta, entrar, transferir, procurar_por_iban, consultar_retorno, limpar_iban
from banco.dados import guardar_csv, guardar_dados
from banco.relatorio import gerar_relatorio

#pedir um número ao utilizador, sem deixar o programa rebentar se escrever letras
def pedir_numero(texto):
    while True:
        try:
            return float(input(texto))
        except ValueError:
            print("Escreva um número.")

#pedir a opção do menu (número inteiro)
def pedir_opcao(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print("Escreva um número.")

#menu depois de entrar na conta
def menu_conta(conta, contas, transacoes):
    print(f"Bem-vindo {conta.username}!\n")

    while True:
        opcao = pedir_opcao(
            "Introduza um dos seguintes valores:\n"
            " 0 - Sair da conta\n"
            " 1 - Levantar\n"
            " 2 - Depositar\n"
            " 3 - Transferir\n"
            " 4 - Consultar saldo\n"
            " 5 - Consultar IBAN\n"
            " 6 - Histórico de transações\n"
            " 7 - Consultar retorno\n"
            " 8 - Relatório do sistema\n"
            "Valor: "
        )
        if opcao == 0:
            print("Saiu da conta.\n")
            break
        elif opcao == 1:
            try:
                valor = pedir_numero("Valor a levantar: ")
                conta.levantar(valor)
                guardar_dados(contas, transacoes)  #guardar logo depois da operação
                print(f"Foi levantado {valor}. Saldo atual: {conta.valor}")
            except ValueError as erro:
                print(erro)
            except SaldoInsuficienteError as erro:
                print(erro)
            print("")
        elif opcao == 2:
            try:
                valor = pedir_numero("Valor a depositar: ")
                conta.depositar(valor)
                guardar_dados(contas, transacoes)  #guardar logo depois da operação
                print(f"Foi depositado {valor}. Saldo atual: {conta.valor}")
            except ValueError as erro:
                print(erro)
            print("")
        elif opcao == 3:
            #o IBAN é limpo: funciona com ou sem PT50, maiúsculas ou minúsculas, com ou sem espaços
            iban_destino = limpar_iban(input("IBAN de destino (só os números): "))

            #ver qual é a conta dona do IBAN antes de confirmar
            username_destino = procurar_por_iban(contas, iban_destino)

            if username_destino == None:
                print("O IBAN de destino não existe no sistema")
            elif username_destino == conta.username:
                print("Não podes transferir para a tua própria conta")
            else:
                print(f"O IBAN pertence a: {username_destino}")
                valor = pedir_numero("Valor a transferir: ")
                confirmar = input(f"Confirmar a transferência de {valor} para {username_destino}? (s/n): ")

                if confirmar == "s":
                    try:
                        transferir(contas, transacoes, conta.username, iban_destino, valor)
                        guardar_dados(contas, transacoes)  #guardar logo depois da operação
                        print(f"Foi transferido {valor} para {username_destino}. Saldo atual: {conta.valor}")
                    except UtilizadorInexistenteError as erro:
                        print(erro)
                    except ValueError as erro:
                        print(erro)
                    except SaldoInsuficienteError as erro:
                        print(erro)
                else:
                    print("Transferência cancelada.")
            print("")
        elif opcao == 4:
            print(f"Saldo atual: {conta.valor}")
            print("")
        elif opcao == 5:
            print(f"IBAN: {conta.iban}")
            print("")
        elif opcao == 6:
            #histórico: só as transações onde consta o IBAN desta conta (enviadas ou recebidas)
            minhas_transacoes = []
            for transacao in transacoes:
                if transacao.iban_origem == conta.iban or transacao.iban_destino == conta.iban:
                    minhas_transacoes.append(transacao)

            if len(minhas_transacoes) == 0:
                print("Ainda não existem transações nesta conta.")
            else:
                #mostrar o histórico, marcando se foi enviada ou recebida
                for transacao in minhas_transacoes:
                    if transacao.iban_origem == conta.iban:
                        tipo = "Enviada"
                    else:
                        tipo = "Recebida"

                    print(f"[{tipo}] {transacao.data} | {transacao.iban_origem} ({transacao.username_origem}) -> "
                          f"{transacao.iban_destino} ({transacao.username_destino}) | {transacao.valor}")

                #perguntar se quer guardar o histórico num ficheiro CSV
                guardar = input("Quer guardar estas transações num ficheiro CSV? (s/n): ")
                if guardar == "s":
                    nome_ficheiro = guardar_csv(conta, minhas_transacoes)
                    print(f"Transações guardadas no ficheiro {nome_ficheiro}")
                else:
                    print("Ficheiro não guardado.")
            print("")
        elif opcao == 7:
            #consultar o retorno: quanto vale a conta com juro composto
            try:
                taxa = pedir_numero("Taxa de juro mensal (%): ")
                meses = pedir_numero("Número de meses: ")

                resultado = consultar_retorno(conta.valor, taxa, int(meses))
                print(f"A conta fica com {resultado:.2f} no final dos {int(meses)} meses")
            except ValueError as erro:
                print(erro)
            print("")
        elif opcao == 8:
            #relatório do sistema: todas as contas ordenadas pelo valor atual
            relatorio = gerar_relatorio(contas, transacoes)

            print("")
            print("Relatório do sistema")
            print("----------------------------------------")
            print("Username | Transferências | Valor atual")
            print("----------------------------------------")
            for linha in relatorio:
                print(f"{linha[1]} | {linha[2]} | {linha[0]}")
            print("")
        else:
            print("Opção inválida. Tente novamente.\n")

#menu principal do programa
def menu_principal(contas, transacoes):
    while True:
        input_utilizador = pedir_opcao(
            "Introduza um dos seguintes valores:\n"
            " 0 - Sair do programa\n"
            " 1 - Criar utilizador\n"
            " 2 - Entrar\n"
            "Valor: "
        )
        if input_utilizador == 0:
            guardar_dados(contas, transacoes)  #guardar tudo no banco.db antes de sair
            print("Sair do programa.\n")
            break
        elif input_utilizador == 1:
            username = input("Username: ")
            password = input("Password: ")

            try:
                criar_conta(contas, username, password)
                guardar_dados(contas, transacoes)  #guardar logo depois de criar
                print(f"Utilizador {username} criado com sucesso. IBAN: {contas[username].iban}\n")
            except UtilizadorJaExisteError as erro:
                print(f"{erro}\n")
            except ValueError as erro:
                print(f"{erro}\n")
        elif input_utilizador == 2:
            username = input("Username: ")
            password = input("Password: ")

            try:
                conta_atual = entrar(contas, username, password)
                if conta_atual == None:
                    print("Username ou password errados.\n")
                else:
                    menu_conta(conta_atual, contas, transacoes)
            except ContaBloqueadaError as erro:
                print(f"{erro}\n")
        else:
            print("Opção inválida. Tente novamente.\n")
