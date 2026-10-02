# menus do sistema e conversa com o utilizador
from banco.erros import (
    UtilizadorJaExisteError,
    UtilizadorInexistenteError,
    SaldoInsuficienteError,
    ContaBloqueadaError,
)
from banco.operacoes import (
    criar_utilizador,
    entrar,
    transferir,
    procurar_por_iban,
    consultar_retorno,
    limpar_iban,
    transferir_por_ficheiro,
    ordenar_registos,
    aplicar_dinheiro,
    verificar_aplicacoes,
    situacao_aplicacao,
    cancelar_aplicacao,
)
from banco.dados import (
    guardar_csv,
    guardar_dados,
    ler_ficheiro_transferencias,
    apagar_ficheiro_transferencias,
    apagar_ficheiro_transacoes,
    guardar_aplicacoes,
    guardar_no_historico,
    listar_historico_aplicacoes,
    registar_movimento,
    listar_movimentos,
)
from banco.modelos import Movimento
from banco.relatorio import gerar_relatorio, gerar_relatorio_processos


# pedir um número ao utilizador, sem deixar o programa rebentar se escrever
# letras
def pedir_numero(texto):
    while True:
        try:
            return float(input(texto))
        except ValueError:
            print("Escreva um número.")
        except (EOFError, KeyboardInterrupt):
            # ctrl+c ou fim do input: sair do programa de forma limpa
            print("")
            return 0


# pedir a opção do menu (número inteiro)
def pedir_opcao(texto):
    while True:
        try:
            return int(input(texto))
        except ValueError:
            print("Escreva um número.")
        except (EOFError, KeyboardInterrupt):
            # ctrl+c ou fim do input: sair do programa de forma limpa
            print("")
            return 0


# opção 1: levantar dinheiro da conta
def menu_levantar(conta, utilizadores, contas, transacoes):
    try:
        valor = pedir_numero("Valor a levantar: ")
        conta.levantar(valor)
        registar_movimento(conta.username, "Levantamento", valor)
        guardar_dados(utilizadores, contas, transacoes)  # guardar logo
        print(f"Foi levantado {valor}. Saldo atual: {conta.valor}")
    except ValueError as erro:
        print(erro)
    except SaldoInsuficienteError as erro:
        print(erro)
    print("")


# opção 2: depositar dinheiro na conta
def menu_depositar(conta, utilizadores, contas, transacoes):
    try:
        valor = pedir_numero("Valor a depositar: ")
        conta.depositar(valor)
        registar_movimento(conta.username, "Depósito", valor)
        guardar_dados(utilizadores, contas, transacoes)  # guardar logo
        print(f"Foi depositado {valor}. Saldo atual: {conta.valor}")
    except ValueError as erro:
        print(erro)
    print("")


# opção 3: transferir para outro utilizador pelo IBAN, com confirmação do dono
def menu_transferir(conta, utilizadores, contas, transacoes):
    # o IBAN é limpo: funciona com ou sem PT50, maiúsculas ou minúsculas, com
    # ou sem espaços
    iban_destino = limpar_iban(input("IBAN de destino (só os números): "))

    # ver qual é a conta dona do IBAN antes de confirmar
    username_destino = procurar_por_iban(contas, iban_destino)

    if username_destino is None:
        print("O IBAN de destino não existe no sistema")
    elif username_destino == conta.username:
        print("Não podes transferir para a tua própria conta")
    else:
        print(f"O IBAN pertence a: {username_destino}")
        valor = pedir_numero("Valor a transferir: ")
        confirmar = input(
            f"Confirmar a transferência de {valor} "
            f"para {username_destino}? (s/n): "
        )

        if confirmar == "s":
            try:
                transferir(
                    contas, transacoes, conta.username, iban_destino, valor
                )
                guardar_dados(utilizadores, contas, transacoes)  # guardar logo
                print(
                    f"Foi transferido {valor} para {username_destino}. "
                    f"Saldo atual: {conta.valor}"
                )
            except UtilizadorInexistenteError as erro:
                print(erro)
            except ValueError as erro:
                print(erro)
            except SaldoInsuficienteError as erro:
                print(erro)
        else:
            print("Transferência cancelada.")
    print("")


# opção 6: histórico de transações e movimentos, com pesquisa, filtro e
# ordenação
def menu_historico(conta, transacoes):
    # histórico: escolher o tipo de movimentos a ver e a ordenação
    tipo = pedir_opcao(
        "Ver:\n"
        " 0 - Tudo\n"
        " 1 - Depósitos\n"
        " 2 - Levantamentos\n"
        " 3 - Transferências recebidas\n"
        " 4 - Transferências enviadas\n"
        "Valor: "
    )

    # juntar numa só lista os movimentos (depósitos e levantamentos)
    # e as transferências desta conta (como registos com tipo)
    registos = listar_movimentos(conta.username)
    for transacao in transacoes:
        if (transacao.iban_origem == conta.iban
                or transacao.iban_destino == conta.iban):
            if transacao.iban_origem == conta.iban:
                tipo_t = "Enviada"
            else:
                tipo_t = "Recebida"
            texto = (
                f"{transacao.iban_origem} ({transacao.username_origem}) "
                f"-> {transacao.iban_destino} ({transacao.username_destino})"
            )
            registos.append(
                Movimento(conta.username, tipo_t, transacao.data,
                          transacao.valor, texto)
            )

    # a pesquisa filtra por texto (enter para ver tudo): procura no tipo,
    # na data, no valor e na descrição de cada registo
    pesquisa = input("Pesquisar (enter para ver tudo): ")
    if pesquisa != "":
        encontrados = []
        for registo in registos:
            texto = (
                registo.tipo + " " + registo.data + " "
                + str(registo.valor) + " " + registo.texto
            ).lower()
            if pesquisa.lower() in texto:
                encontrados.append(registo)
        registos = encontrados

    # filtrar pelo tipo escolhido
    if tipo >= 1:
        if tipo == 1:
            nome_tipo = "Depósito"
        elif tipo == 2:
            nome_tipo = "Levantamento"
        elif tipo == 3:
            nome_tipo = "Recebida"
        else:
            nome_tipo = "Enviada"

        filtrados = []
        for registo in registos:
            if registo.tipo == nome_tipo:
                filtrados.append(registo)
        registos = filtrados

    # a ordenação é à escolha: por valor ou por data, crescente ou decrescente
    campo = pedir_opcao(
        "Ordenar por:\n"
        " 0 - Sem ordenação\n"
        " 1 - Valor\n"
        " 2 - Data\n"
        "Valor: "
    )
    if campo == 1 or campo == 2:
        sentido = pedir_opcao(
            "Ordem:\n"
            " 1 - Crescente\n"
            " 2 - Decrescente\n"
            "Valor: "
        )
        if campo == 1:
            nome_campo = "valor"
        else:
            nome_campo = "data"
        registos = ordenar_registos(registos, nome_campo, sentido == 2)

    if len(registos) == 0:
        print("Não há movimentos para ver.")
    else:
        for registo in registos:
            if registo.texto == "":
                print(f"[{registo.tipo}] {registo.data} | {registo.valor}")
            else:
                print(
                    f"[{registo.tipo}] {registo.data} | {registo.texto} "
                    f"| {registo.valor}"
                )

        # o CSV só guarda as transferências completas (a ver Tudo)
        if tipo == 0:
            guardar = input(
                "Quer guardar as transferências num ficheiro CSV? (s/n): "
            )
            if guardar == "s":
                minhas_transacoes = []
                for transacao in transacoes:
                    if (transacao.iban_origem == conta.iban
                            or transacao.iban_destino == conta.iban):
                        minhas_transacoes.append(transacao)
                nome_ficheiro = guardar_csv(conta, minhas_transacoes)
                print(f"Transações guardadas no ficheiro {nome_ficheiro}")
            else:
                print("Ficheiro não guardado.")
    print("")


# opção 7: investimento — simular o retorno com juro composto ou aplicar
# dinheiro a prazo
def menu_investimento(conta, utilizadores, contas, transacoes, aplicacoes):
    opcao_investimento = pedir_opcao(
        "Investimento — introduza um dos seguintes valores:\n"
        " 0 - Voltar\n"
        " 1 - Simular retorno\n"
        " 2 - Aplicar dinheiro\n"
        "Valor: "
    )

    if opcao_investimento == 1:
        # simular: quanto valeria um valor com juro composto (sem mexer no
        # dinheiro)
        try:
            valor = pedir_numero("Valor a simular: ")
            taxa = pedir_numero("Taxa de juro mensal (%): ")
            meses = pedir_numero("Número de meses: ")

            resultado = consultar_retorno(valor, taxa, int(meses))
            print(
                f"No final dos {int(meses)} meses o valor fica em "
                f"{resultado:.2f}"
            )
        except ValueError as erro:
            print(erro)
    elif opcao_investimento == 2:
        # aplicar: o valor sai do saldo e fica cativo até ao fim do prazo
        try:
            valor = pedir_numero("Valor a aplicar: ")
            taxa = pedir_numero("Taxa de juro mensal (%): ")
            meses = pedir_numero("Número de meses (1 a 12): ")

            aplicar_dinheiro(conta, aplicacoes, valor, taxa, int(meses))
            guardar_dados(utilizadores, contas, transacoes)
            guardar_aplicacoes(aplicacoes)
            print(
                f"Aplicação feita. O valor fica cativo até ao fim do prazo. "
                f"Saldo atual: {conta.valor}"
            )
        except ValueError as erro:
            print(erro)
        except SaldoInsuficienteError as erro:
            print(erro)
    print("")


# opção 8: relatório do sistema (estatísticas em dois processos + tabela com
# threads)
def menu_relatorio(contas, transacoes):
    # relatório do sistema: as estatísticas correm em dois processos
    # (um analisa as contas, outro as transferências)
    stats_contas, stats_transf = gerar_relatorio_processos(contas, transacoes)

    print("")
    print("Relatório do sistema")
    print("----------------------------------------")

    if stats_contas["maior"] is None:
        print("Contas: ainda não há contas no sistema")
    else:
        print("Contas:")
        print(
            f" - maior saldo: {', '.join(stats_contas['maior'][1])} "
            f"({stats_contas['maior'][0]})"
        )
        print(
            f" - menor saldo: {', '.join(stats_contas['menor'][1])} "
            f"({stats_contas['menor'][0]})"
        )
        print(f" - soma de todos os saldos: {stats_contas['soma']}")

    if stats_transf["mais_recebeu"] is None:
        print("Transferências: ainda não há transferências no sistema")
    else:
        print("Transferências:")
        print(
            f" - quem mais recebeu: "
            f"{', '.join(stats_transf['mais_recebeu'][1])} "
            f"({stats_transf['mais_recebeu'][0]})"
        )
        print(
            f" - quem mais enviou: "
            f"{', '.join(stats_transf['mais_enviou'][1])} "
            f"({stats_transf['mais_enviou'][0]})"
        )
        print(f" - total transferido: {stats_transf['total']}")

    # a tabela com todas as contas, ordenada pelo valor atual
    relatorio = gerar_relatorio(contas, transacoes)
    print("----------------------------------------")
    print("Username | Transferências | Valor atual")
    print("----------------------------------------")
    for linha in relatorio:
        print(f"{linha[1]} | {linha[2]} | {linha[0]}")
    print("")


# opção 9: transferências em lote a partir do ficheiro CSV do utilizador
def menu_ficheiro(conta, utilizadores, contas, transacoes):
    # transferências em lote: o ficheiro vive na pasta transferencias com o
    # nome do utilizador
    try:
        conteudo = ler_ficheiro_transferencias(conta.username)
    except FileNotFoundError:
        print(
            f"Não existe ficheiro para a tua conta "
            f"(transferencias/{conta.username}.csv)."
        )
        print("")
        return

    erros = transferir_por_ficheiro(
        contas, transacoes, conta.username, conteudo
    )

    if len(erros) > 0:
        print("O ficheiro tem problemas, não foi transferido nada:")
        for erro in erros:
            print(f" - {erro}")
    else:
        guardar_dados(utilizadores, contas, transacoes)  # guardar logo
        print(
            f"Transferências do ficheiro feitas com sucesso. "
            f"Saldo atual: {conta.valor}"
        )
    print("")


# opção 10: aplicações a prazo — as ativas, o histórico e o cancelamento
def menu_aplicacoes(conta, utilizadores, contas, transacoes, aplicacoes):
    # aplicações: as ativas (numeradas, com totais), o histórico e o
    # cancelamento
    minhas = []
    for aplicacao in aplicacoes:
        if aplicacao.username == conta.username:
            minhas.append(aplicacao)

    if len(minhas) == 0:
        print("Não tens aplicações ativas.")
    else:
        print("Aplicações ativas:")
        total_aplicado = 0
        total_a_ganhar = 0
        numero = 1
        for aplicacao in minhas:
            retorno = consultar_retorno(
                aplicacao.valor, aplicacao.taxa, aplicacao.meses
            )
            valor_hoje, dias_restantes = situacao_aplicacao(aplicacao)
            print(
                f" {numero} - {aplicacao.valor} | {aplicacao.taxa}% "
                f"| {aplicacao.meses} meses "
                f"| hoje vale {valor_hoje:.2f} "
                f"| faltam {dias_restantes} dias "
                f"| retorno final {retorno:.2f} | até {aplicacao.data_fim}"
            )
            total_aplicado = total_aplicado + aplicacao.valor
            total_a_ganhar = total_a_ganhar + (retorno - aplicacao.valor)
            numero = numero + 1
        print(
            f"Total aplicado: {total_aplicado:.2f} | "
            f"a ganhar no fim dos prazos: {total_a_ganhar:.2f}"
        )

    historico = listar_historico_aplicacoes(conta.username)
    if len(historico) > 0:
        print("Histórico (aplicações terminadas):")
        total_ganho = 0
        for aplicacao in historico:
            ganho = aplicacao.valor_final - aplicacao.valor
            print(
                f" - {aplicacao.valor} | {aplicacao.taxa}% "
                f"| {aplicacao.meses} meses "
                f"| recebeu {aplicacao.valor_final:.2f} "
                f"(ganhou {ganho:.2f}) | terminou a {aplicacao.data_fim}"
            )
            total_ganho = total_ganho + ganho
        print(f"Total ganho: {total_ganho:.2f}")

    quero = input("Queres cancelar alguma aplicação? (s/n): ")
    if quero == "s" and len(minhas) > 0:
        try:
            numero = pedir_opcao("Número da aplicação a cancelar: ")
            cancelada = cancelar_aplicacao(conta, aplicacoes, numero)
            guardar_no_historico(cancelada)
            guardar_dados(utilizadores, contas, transacoes)
            guardar_aplicacoes(aplicacoes)
            print(
                f"Aplicação cancelada: voltaram {cancelada.valor_final:.2f} "
                f"ao saldo. Saldo atual: {conta.valor}"
            )
        except ValueError as erro:
            print(erro)

    print("(para fazer uma aplicação nova, usa a opção 7 - Investimento)")
    print("")


# menu depois de entrar na conta
def menu_conta(conta, utilizadores, contas, transacoes, aplicacoes):
    print(f"Bem-vindo {conta.username}!")

    # as aplicações que chegaram ao fim do prazo libertam o dinheiro com os
    # juros
    libertadas = verificar_aplicacoes(conta, aplicacoes)
    for aplicacao in libertadas:
        print(
            f"Aplicação de {aplicacao.valor} acabou: "
            f"voltaram {aplicacao.valor_final:.2f} ao saldo"
        )
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
            " 7 - Investimento\n"
            " 8 - Relatório do sistema\n"
            " 9 - Transferir por ficheiro CSV\n"
            " 10 - Aplicações\n"
            "Valor: "
        )
        if opcao == 0:
            # os ficheiros do utilizador (transferências e transações
            # exportadas) são apagados quando ele sai
            apagar_ficheiro_transferencias(conta.username)
            apagar_ficheiro_transacoes(conta.username)
            print("Saiu da conta.\n")
            break
        elif opcao == 1:
            menu_levantar(conta, utilizadores, contas, transacoes)
        elif opcao == 2:
            menu_depositar(conta, utilizadores, contas, transacoes)
        elif opcao == 3:
            menu_transferir(conta, utilizadores, contas, transacoes)
        elif opcao == 4:
            print(f"Saldo atual: {conta.valor}")
            print("")
        elif opcao == 5:
            print(f"IBAN: {conta.iban}")
            print("")
        elif opcao == 6:
            menu_historico(conta, transacoes)
        elif opcao == 7:
            menu_investimento(
                conta, utilizadores, contas, transacoes, aplicacoes
            )
        elif opcao == 8:
            menu_relatorio(contas, transacoes)
        elif opcao == 9:
            menu_ficheiro(conta, utilizadores, contas, transacoes)
        elif opcao == 10:
            menu_aplicacoes(
                conta, utilizadores, contas, transacoes, aplicacoes
            )
        else:
            print("Opção inválida. Tente novamente.\n")


# menu principal do programa
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
            # guardar tudo antes de sair
            guardar_dados(utilizadores, contas, transacoes)
            print("Sair do programa.\n")
            break
        elif input_utilizador == 1:
            username = input("Username: ")
            password = input("Password: ")

            try:
                criar_utilizador(utilizadores, contas, username, password)
                guardar_dados(utilizadores, contas, transacoes)  # guardar logo

                print(
                    f"Utilizador {username} criado com sucesso. "
                    f"IBAN: {contas[username].iban}\n"
                )
            except UtilizadorJaExisteError as erro:
                print(f"{erro}\n")
            except ValueError as erro:
                print(f"{erro}\n")
        elif input_utilizador == 2:
            username = input("Username: ")
            password = input("Password: ")

            try:
                utilizador_atual = entrar(utilizadores, username, password)
                if utilizador_atual is None:
                    print("Username ou password errados.\n")
                else:
                    menu_conta(
                        contas[utilizador_atual.username], utilizadores,
                        contas, transacoes, aplicacoes
                    )
            except ContaBloqueadaError as erro:
                print(f"{erro}\n")
            except UtilizadorInexistenteError as erro:
                print(f"{erro}\n")
        else:
            print("Opção inválida. Tente novamente.\n")
