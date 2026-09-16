#funções do banco
from datetime import datetime

from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError
from banco.modelos import Conta, Transacao

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

#criar conta nova: levanta erro se não conseguir criar
def criar_conta(contas, username, password):
    if username == "":
        raise ValueError("O username não pode ser vazio")

    if username in contas:
        raise UtilizadorJaExisteError("O username já existe no sistema")

    if validar_password(password) == False:
        raise ValueError("Password inválida: tem de ter entre 6 a 10 caracteres, com pelo menos 1 letra e 1 número")

    iban = gerar_iban(contas)
    contas[username] = Conta(username, password, 0, iban)  #a conta é criada com valor 0

#entrar: devolve a conta se o username e a password estiverem certos, senão None
def entrar(contas, username, password):
    if username in contas and contas[username].password == password:
        return contas[username]
    return None

#transferir por IBAN: mexe nos dois saldos e registra a transação
def transferir(contas, transacoes, username_origem, iban_destino, valor):
    username_destino = procurar_por_iban(contas, iban_destino)

    if username_destino == None:
        raise UtilizadorInexistenteError("O IBAN de destino não existe no sistema")

    if username_destino == username_origem:
        raise ValueError("Não podes transferir para a tua própria conta")

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

#calcular o valor da conta com juro composto, de forma recursiva
#cada mês o valor é multiplicado pela taxa, até acabarem os meses
def consultar_retorno(valor, taxa, meses):
    if taxa < 0 or taxa > 100:
        raise ValueError("A taxa de juro tem de ser um valor entre 0 e 100")

    if meses != int(meses):
        raise ValueError("O número de meses tem de ser um número inteiro")

    if meses < 0:
        raise ValueError("O número de meses tem de ser positivo")

    #caso base: sem meses já não há juros
    if meses == 0:
        return valor

    return consultar_retorno(valor, taxa, meses - 1) * (1 + taxa / 100)
