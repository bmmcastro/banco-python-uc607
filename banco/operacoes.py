#funções do banco
import csv
import math
import time
from datetime import datetime

from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError
from banco.modelos import Utilizador, Conta, Transacao
from banco.dados import ver_bloqueio, anotar_tentativa, limpar_tentativas

#limite de tentativas de login: 3 passwords erradas bloqueiam a conta durante 30 segundos
MAXIMO_TENTATIVAS = 3
SEGUNDOS_BLOQUEIO = 30

#ver se a password é válida: 6 a 10 caracteres, pelo menos 1 letra e 1 número
def validar_password(password):
    if len(password) < 6 or len(password) > 10:
        return False

    tem_letra = False
    tem_numero = False
    for caracter in password:
        if caracter.isalpha():
            tem_letra = True
        if caracter.isdigit():
            tem_numero = True

    if tem_letra == False or tem_numero == False:
        return False

    return True

#limpar o IBAN escrito pelo utilizador: maiúsculas, sem espaços e sem o PT50 repetido
def limpar_iban(iban):
    iban = iban.replace(" ", "")  #tirar os espaços todos
    iban = iban.upper()           #o pt em minúsculas fica PT

    #se o utilizador já escreveu o PT50, tira-o para não ficar repetido
    while iban.startswith("PT50"):
        iban = iban[4:]

    #no fim o IBAN fica sempre no formato do sistema: PT50 seguido do número
    return "PT50 " + iban

#procurar uma conta pelo IBAN: devolve o username se existir, senão None
def procurar_por_iban(contas, iban):
    for username in contas:
        if contas[username].iban == iban:
            return username
    return None

#gerar um IBAN único: PT50 seguido de um número que ainda não exista no sistema
def gerar_iban(contas):
    numero = len(contas) + 1
    iban = f"PT50 {numero:04d}"

    #se o número já estiver a ser usado, passa para o próximo
    while procurar_por_iban(contas, iban) != None:
        numero = numero + 1
        iban = f"PT50 {numero:04d}"

    return iban

#criar utilizador novo (com a respetiva conta a zeros): levanta erro se não conseguir criar
def criar_utilizador(utilizadores, contas, username, password):
    if username == "":
        raise ValueError("O username não pode ser vazio")

    #só letras e números: usernames com barras ou pontos não podem ser usados para fugir da pasta
    if not username.isalnum():
        raise ValueError("O username só pode ter letras e números")

    if username in utilizadores:
        raise UtilizadorJaExisteError("O username já existe no sistema")

    if validar_password(password) == False:
        raise ValueError("Password inválida: tem de ter entre 6 a 10 caracteres, com pelo menos 1 letra e 1 número")

    iban = gerar_iban(contas)
    utilizadores[username] = Utilizador(username, password)
    contas[username] = Conta(username, 0, iban)  #a conta é criada com valor 0

#entrar: devolve o utilizador se o username e a password estiverem certos, senão None
#levanta a UtilizadorInexistenteError se o username não existir no sistema
#depois de 3 tentativas erradas a conta fica bloqueada durante 30 segundos
#(as tentativas são guardadas no banco.db, por isso valem para o terminal e para o site)
def entrar(utilizadores, username, password):
    agora = time.time()

    tentativas, bloqueado_ate = ver_bloqueio(username)

    #conta bloqueada: nem a password certa entra
    if bloqueado_ate > agora:
        restantes = int(bloqueado_ate - agora)
        raise ContaBloqueadaError(f"Muitas tentativas erradas. A conta está bloqueada mais {restantes} segundos")

    #entrar com um username que não existe (a mensagem não revela qual dos dois está errado)
    if username not in utilizadores:
        raise UtilizadorInexistenteError("Username ou password errados")

    if utilizadores[username].password == password:
        #login certo: esquecer as tentativas erradas dessa conta
        limpar_tentativas(username)
        return utilizadores[username]

    #login errado: contar a tentativa
    tentativas = tentativas + 1

    if tentativas >= MAXIMO_TENTATIVAS:
        anotar_tentativa(username, 0, agora + SEGUNDOS_BLOQUEIO)
        raise ContaBloqueadaError(f"Password errada demasiadas vezes. A conta fica bloqueada durante {SEGUNDOS_BLOQUEIO} segundos")

    anotar_tentativa(username, tentativas, 0)
    return None

#transferir por IBAN: mexe nos dois saldos e registra a transação
def transferir(contas, transacoes, username_origem, iban_destino, valor):
    username_destino = procurar_por_iban(contas, iban_destino)

    if username_destino == None:
        raise UtilizadorInexistenteError("O IBAN de destino não existe no sistema")

    if username_destino == username_origem:
        raise ValueError("Não podes transferir para a tua própria conta")

    if not math.isfinite(valor):
        raise ValueError("O valor tem de ser um número válido")

    if valor <= 0:
        raise ValueError("O valor da transferência tem de ser positivo")

    if valor > contas[username_origem].valor:
        raise SaldoInsuficienteError("Saldo insuficiente")

    #mexer nos saldos: tira à origem e dá ao destino
    contas[username_origem].valor = contas[username_origem].valor - valor
    contas[username_destino].valor = contas[username_destino].valor + valor

    #registrar a transação com a data e hora automáticas
    data = datetime.now().strftime("%d/%m/%Y %H:%M")
    transacao = Transacao(
        data,
        valor,
        contas[username_origem].iban,
        username_origem,
        contas[username_destino].iban,
        username_destino,
    )
    transacoes.append(transacao)

#transferências em lote a partir de um ficheiro CSV (iban, nome, valor)
#valida todas as linhas primeiro: o IBAN existe, o nome é o dono certo e há saldo para tudo
#se houver algum erro não se transfere nada; devolve a lista de erros (vazio = transferências feitas)
def transferir_por_ficheiro(contas, transacoes, username_origem, conteudo):
    erros = []
    transferencias = []
    saldo_disponivel = contas[username_origem].valor

    leitor = csv.DictReader(conteudo.splitlines())

    #a primeira linha é o cabeçalho, por isso os dados começam na linha 2
    for linha in leitor:
        numero = leitor.line_num

        #o cabeçalho tem de ter as três colunas
        if "iban" not in linha or "nome" not in linha or "valor" not in linha:
            erros.append(f"linha {numero}: faltam colunas (o cabeçalho tem de ser iban,nome,valor)")
            continue

        #1: o IBAN tem de existir
        iban = limpar_iban(linha["iban"])
        dono = procurar_por_iban(contas, iban)
        if dono == None:
            erros.append(f"linha {numero}: o IBAN {linha['iban']} não existe no sistema")
            continue

        #2: o nome tem de ser o dono do IBAN
        nome = linha["nome"].strip()
        if nome != dono:
            erros.append(f"linha {numero}: o nome {nome} não é o dono do IBAN {iban} (é {dono})")
            continue

        #3: não se pode transferir para a própria conta
        if dono == username_origem:
            erros.append(f"linha {numero}: não podes transferir para a tua própria conta")
            continue

        #4: o valor tem de ser um número maior que zero
        try:
            valor = float(linha["valor"].replace(",", "."))
        except ValueError:
            erros.append(f"linha {numero}: o valor {linha['valor']} não é um número")
            continue

        if valor <= 0:
            erros.append(f"linha {numero}: o valor tem de ser maior que zero")
            continue

        #5: o saldo tem de chegar para todas as transferências do ficheiro
        if valor > saldo_disponivel:
            erros.append(f"linha {numero}: o saldo não chega para todas as transferências")
            continue
        saldo_disponivel = saldo_disponivel - valor

        transferencias.append((iban, valor))

    #com algum erro não se transfere nada
    if len(erros) > 0:
        return erros

    #tudo certo: fazer as transferências (o transferir já regista as transações)
    for iban, valor in transferencias:
        transferir(contas, transacoes, username_origem, iban, valor)

    return []

#pesquisar as transações de uma conta por texto: a pesquisa pode ser uma data,
#um username, um IBAN ou um valor; devolve a lista das transações que correspondem
def pesquisar_transacoes(transacoes, conta, pesquisa):
    encontradas = []

    for transacao in transacoes:
        #só interessam as transações onde esta conta consta (enviadas ou recebidas)
        if transacao.iban_origem != conta.iban and transacao.iban_destino != conta.iban:
            continue

        #juntar tudo o que se pode pesquisar numa só linha de texto
        texto = (transacao.data + " " + transacao.username_origem + " " + transacao.iban_origem + " "
                 + transacao.username_destino + " " + transacao.iban_destino + " " + str(transacao.valor))

        if pesquisa.lower() in texto.lower():
            encontradas.append(transacao)

    return encontradas

#calcular o valor da conta com juro composto, de forma recursiva
#cada mês o valor é multiplicado pela taxa, até acabarem os meses
#a taxa pode ser negativa ou positiva: só o valor absoluto tem de ficar entre 0 e 100
def consultar_retorno(valor, taxa, meses):
    if abs(taxa) > 100:
        raise ValueError("A taxa de juro tem de ter um valor absoluto entre 0 e 100")

    if meses != int(meses):
        raise ValueError("O número de meses tem de ser um número inteiro")

    if meses < 1 or meses > 12:
        raise ValueError("O número de meses tem de estar entre 1 e 12")

    #caso base: no último mês o valor já rende uma vez
    if meses == 1:
        return valor * (1 + taxa / 100)

    return consultar_retorno(valor, taxa, meses - 1) * (1 + taxa / 100)
