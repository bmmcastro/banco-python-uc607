#relatório do sistema: usa threads para contar as transferências de cada conta
import threading

#contar as transferências enviadas por uma conta (cada thread conta uma conta)
def contar_transferencias(username, transacoes, contadores):
    contador = 0
    for transacao in transacoes:
        if transacao.username_origem == username:
            contador = contador + 1

    contadores[username] = contador

#gerar o relatório do sistema: devolve uma lista ordenada com
#[valor, username, nº de transferências] de cada conta (ordenada do maior valor para o menor)
def gerar_relatorio(contas, transacoes):
    contadores = {}

    #uma thread por conta, todas a contar ao mesmo tempo
    threads = []
    for username in contas:
        thread = threading.Thread(target=contar_transferencias, args=(username, transacoes, contadores))
        threads.append(thread)
        thread.start()

    #esperar que todas as threads terminem antes de continuar
    for thread in threads:
        thread.join()

    #pôr tudo numa lista de listas [valor, username, transferências]
    relatorio = []
    for username in contas:
        relatorio.append([contas[username].valor, username, contadores[username]])

    #o sort ordena pelo primeiro elemento de cada lista (o valor)
    relatorio.sort(reverse=True)

    return relatorio
