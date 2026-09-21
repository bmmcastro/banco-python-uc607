#menus do sistema e conversa com o utilizador
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError
from banco.operacoes import criar_utilizador, entrar, transferir, procurar_por_iban, consultar_retorno, limpar_iban, transferir_por_ficheiro, pesquisar_transacoes, aplicar_dinheiro, verificar_aplicacoes
from banco.dados import guardar_csv, guardar_dados, ler_ficheiro_transferencias, apagar_ficheiro_transferencias, apagar_ficheiro_transacoes, guardar_aplicacoes, guardar_no_historico, listar_historico_aplicacoes
from banco.relatorio import gerar_relatorio

#pedir um número ao utilizador, sem deixar o programa rebentar se escrever letras
def pedir_numero(texto):
    while True:
        try:
            return float(input(texto))
        except ValueError:
            print("Escreva um número.")
        except (EOFError, KeyboardInterrupt):
            #ctrl+c ou fim do input: sair do programa de forma limpa
            print("")
            return 0

#pedir a opção do menu (número inteiro)
def pedir_opcao(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print("Escreva um número.")
        except (EOFError, KeyboardInterrupt):
            #ctrl+c ou fim do input: sair do programa de forma limpa
            print("")
            return 0

#menu depois de entrar na conta
def menu_conta(conta, utilizadores, contas, transacoes, aplicacoes):
    print(f"Bem-vindo {conta.username}!")

    #as aplicações que chegaram ao fim do prazo libertam o dinheiro com os juros
    libertadas = verificar_aplicacoes(conta, aplicacoes)
    for aplicacao in libertadas:
        print(f"Aplicação de {aplicacao.valor} acabou: voltaram {aplicacao.valor_final:.2f} ao saldo")
        guardar_no_historico(aplicacao)
    if len(libertadas) > 0:
        guardar_dados(utilizadores, contas, transacoes)
        guardar_aplicacoes(aplicacoes)
    print("")

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
            " 9 - Transferir por ficheiro CSV\n"
            " 10 - Pesquisar transações\n"
            " 11 - Aplicar dinheiro\n"
            "Valor: "
        )
        if opcao == 0:
            #os ficheiros do utilizador (transferências e transações exportadas) são apagados quando ele sai
            apagar_ficheiro_transferencias(conta.username)
            apagar_ficheiro_transacoes(conta.username)
            print("Saiu da conta.\n")
            break
        elif opcao == 1:
            try:
                valor = pedir_numero("Valor a levantar: ")
                conta.levantar(valor)
                guardar_dados(utilizadores, contas, transacoes)  #guardar logo depois da operação
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
                guardar_dados(utilizadores, contas, transacoes)  #guardar logo depois da operação
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
                        guardar_dados(utilizadores, contas, transacoes)  #guardar logo depois da operação
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
        elif opcao == 9:
            #transferências em lote: o ficheiro vive na pasta transferencias com o nome do utilizador
            try:
                conteudo = ler_ficheiro_transferencias(conta.username)
            except FileNotFoundError:
                print(f"Não existe ficheiro para a tua conta (transferencias/{conta.username}.csv).")
                print("")
                continue

            erros = transferir_por_ficheiro(contas, transacoes, conta.username, conteudo)

            if len(erros) > 0:
                print("O ficheiro tem problemas, não foi transferido nada:")
                for erro in erros:
                    print(f" - {erro}")
            else:
                guardar_dados(utilizadores, contas, transacoes)  #guardar logo depois da operação
                print(f"Transferências do ficheiro feitas com sucesso. Saldo atual: {conta.valor}")
            print("")
        elif opcao == 10:
            #pesquisar transações desta conta por texto (data, username, IBAN ou valor)
            pesquisa = input("Pesquisar: ")
            encontradas = pesquisar_transacoes(transacoes, conta, pesquisa)

            if len(encontradas) == 0:
                print("Nenhuma transação encontrada.")
            else:
                for transacao in encontradas:
                    print(f"[{transacao.data}] {transacao.username_origem} ({transacao.iban_origem}) -> "
                          f"{transacao.username_destino} ({transacao.iban_destino}) | {transacao.valor}")
            print("")
        elif opcao == 11:
            #menu das aplicações: as ativas (com o retorno previsto) e o histórico das terminadas
            minhas = []
            for aplicacao in aplicacoes:
                if aplicacao.username == conta.username:
                    minhas.append(aplicacao)

            if len(minhas) == 0:
                print("Não tens aplicações ativas.")
            else:
                print("Aplicações ativas:")
                for aplicacao in minhas:
                    retorno = consultar_retorno(aplicacao.valor, aplicacao.taxa, aplicacao.meses)
                    print(f" - {aplicacao.valor} | {aplicacao.taxa}% | {aplicacao.meses} meses | "
                          f"retorno {retorno:.2f} | até {aplicacao.data_fim}")

            historico = listar_historico_aplicacoes(conta.username)
            if len(historico) > 0:
                print("Histórico (aplicações terminadas):")
                for aplicacao in historico:
                    print(f" - {aplicacao.valor} | {aplicacao.taxa}% | {aplicacao.meses} meses | "
                          f"recebeu {aplicacao.valor_final:.2f} | terminou a {aplicacao.data_fim}")

            #perguntar se quer fazer uma aplicação nova
            quero = input("Queres fazer uma aplicação? (s/n): ")
            if quero != "s":
                print("")
                continue

            try:
                valor = pedir_numero("Valor a aplicar: ")
                taxa = pedir_numero("Taxa de juro mensal (%): ")
                meses = pedir_numero("Número de meses (1 a 12): ")

                aplicar_dinheiro(conta, aplicacoes, valor, taxa, int(meses))
                guardar_dados(utilizadores, contas, transacoes)
                guardar_aplicacoes(aplicacoes)
                print(f"Aplicação feita. O valor fica cativo até ao fim do prazo. Saldo atual: {conta.valor}")
            except ValueError as erro:
                print(erro)
            except SaldoInsuficienteError as erro:
                print(erro)
            print("")
        else:
            print("Opção inválida. Tente novamente.\n")

#menu principal do programa
def menu_principal(utilizadores, contas, transacoes, aplicacoes):
    while True:
        input_utilizador = pedir_opcao(
            "Introduza um dos seguintes valores:\n"
            " 0 - Sair do programa\n"
            " 1 - Criar utilizador\n"
            " 2 - Entrar\n"
            "Valor: "
        )
        if input_utilizador == 0:
            guardar_dados(utilizadores, contas, transacoes)  #guardar tudo no banco.db antes de sair
            print("Sair do programa.\n")
            break
        elif input_utilizador == 1:
            username = input("Username: ")
            password = input("Password: ")

            try:
                criar_utilizador(utilizadores, contas, username, password)
                guardar_dados(utilizadores, contas, transacoes)  #guardar logo depois de criar
                print(f"Utilizador {username} criado com sucesso. IBAN: {contas[username].iban}\n")
            except UtilizadorJaExisteError as erro:
                print(f"{erro}\n")
            except ValueError as erro:
                print(f"{erro}\n")
        elif input_utilizador == 2:
            username = input("Username: ")
            password = input("Password: ")

            try:
                utilizador_atual = entrar(utilizadores, username, password)
                if utilizador_atual == None:
                    print("Username ou password errados.\n")
                else:
                    menu_conta(contas[utilizador_atual.username], utilizadores, contas, transacoes, aplicacoes)
            except ContaBloqueadaError as erro:
                print(f"{erro}\n")
            except UtilizadorInexistenteError as erro:
                print(f"{erro}\n")
        else:
            print("Opção inválida. Tente novamente.\n")
