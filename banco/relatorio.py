#relatório do sistema: usa threads para contar as transferências de cada conta
#e processos para as estatísticas das contas e das transferências
import threading
from multiprocessing import Process, Queue

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

#estatísticas das contas: os utilizadores com maior saldo, com menor saldo
#e a soma de todos os saldos (se houver empate, aparecem todos)
def relatorio_contas(contas):
    if len(contas) == 0:
        return {"maior": None, "menor": None, "soma": 0}

    maior_valor = None
    menor_valor = None
    soma = 0
    for username in contas:
        valor = contas[username].valor
        soma = soma + valor
        if maior_valor == None or valor > maior_valor:
            maior_valor = valor
        if menor_valor == None or valor < menor_valor:
            menor_valor = valor

    #os utilizadores que têm o maior e o menor saldo
    maiores = []
    menores = []
    for username in contas:
        if contas[username].valor == maior_valor:
            maiores.append(username)
        if contas[username].valor == menor_valor:
            menores.append(username)

    return {"maior": [maior_valor, maiores], "menor": [menor_valor, menores], "soma": round(soma, 2)}

#estatísticas das transferências: o utilizador que mais dinheiro recebeu,
#o que mais enviou e a soma de todo o dinheiro transferido
def relatorio_transferencias(transacoes):
    if len(transacoes) == 0:
        return {"mais_recebeu": None, "mais_enviou": None, "total": 0}

    recebido = {}
    enviado = {}
    total = 0
    for transacao in transacoes:
        recebido[transacao.username_destino] = recebido.get(transacao.username_destino, 0) + transacao.valor
        enviado[transacao.username_origem] = enviado.get(transacao.username_origem, 0) + transacao.valor
        total = total + transacao.valor

    maior_recebido = None
    for valor in recebido.values():
        if maior_recebido == None or valor > maior_recebido:
            maior_recebido = valor

    maior_enviado = None
    for valor in enviado.values():
        if maior_enviado == None or valor > maior_enviado:
            maior_enviado = valor

    #os utilizadores que mais receberam e os que mais enviaram (pode haver empate)
    mais_recebeu = []
    mais_enviou = []
    for username in recebido:
        if recebido[username] == maior_recebido:
            mais_recebeu.append(username)
    for username in enviado:
        if enviado[username] == maior_enviado:
            mais_enviou.append(username)

    return {
        "mais_recebeu": [round(maior_recebido, 2), mais_recebeu],
        "mais_enviou": [round(maior_enviado, 2), mais_enviou],
        "total": round(total, 2),
    }

#os processos põem o resultado na fila (é a forma de devolver valores entre processos)
def _tarefa_contas(fila, contas):
    fila.put(relatorio_contas(contas))

def _tarefa_transferencias(fila, transacoes):
    fila.put(relatorio_transferencias(transacoes))

#gerar o relatório com dois processos: um analisa as contas, outro as transferências
def gerar_relatorio_processos(contas, transacoes):
    fila = Queue()

    processo1 = Process(target=_tarefa_contas, args=(fila, contas))
    processo2 = Process(target=_tarefa_transferencias, args=(fila, transacoes))

    processo1.start()
    processo2.start()

    #ir buscar os resultados e só depois esperar pelos processos
    estatisticas_contas = fila.get()
    estatisticas_transferencias = fila.get()
    processo1.join()
    processo2.join()

    return estatisticas_contas, estatisticas_transferencias
