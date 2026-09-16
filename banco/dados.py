#tudo o que mexe em ficheiros: a base de dados sqlite e os ficheiros csv
import sqlite3
import csv

from banco.modelos import Conta, Transacao

#criar as tabelas no ficheiro banco.db (só cria se ainda não existirem)
def criar_tabelas():
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            username TEXT,
            password TEXT,
            valor REAL,
            iban TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            data TEXT,
            valor REAL,
            iban_origem TEXT,
            username_origem TEXT,
            iban_destino TEXT,
            username_destino TEXT
        )
    """)

    ligacao.commit()
    ligacao.close()

#carregar os dados guardados no banco.db para o sistema
def carregar_dados():
    contas = {}
    transacoes = []
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()

    #cada linha vem como um tuplo, separa-se logo nas variáveis
    for username, password, valor, iban in cursor.execute(
        "SELECT username, password, valor, iban FROM contas"
    ):
        contas[username] = Conta(username, password, valor, iban)

    for data, valor, iban_origem, username_origem, iban_destino, username_destino in cursor.execute(
        "SELECT data, valor, iban_origem, username_origem, iban_destino, username_destino FROM transacoes"
    ):
        transacoes.append(Transacao(data, valor, iban_origem, username_origem, iban_destino, username_destino))

    ligacao.close()
    return contas, transacoes

#guardar os dados do sistema no banco.db (apaga o que lá estava e guarda tudo de novo)
def guardar_dados(contas, transacoes):
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()
    cursor.execute("DELETE FROM contas")
    cursor.execute("DELETE FROM transacoes")

    for username in contas:
        conta = contas[username]
        cursor.execute(
            "INSERT INTO contas (username, password, valor, iban) VALUES (?, ?, ?, ?)",
            (conta.username, conta.password, conta.valor, conta.iban)
        )

    for transacao in transacoes:
        cursor.execute(
            "INSERT INTO transacoes (data, valor, iban_origem, username_origem, iban_destino, username_destino) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (transacao.data, transacao.valor, transacao.iban_origem, transacao.username_origem,
             transacao.iban_destino, transacao.username_destino)
        )

    ligacao.commit()  #confirmar as alterações no ficheiro
    ligacao.close()

#guardar as transações de uma conta num ficheiro CSV: devolve o nome do ficheiro criado
#(o nome tem o username, por isso só é substituído quando o mesmo user exporta de novo)
def guardar_csv(conta, transacoes_da_conta):
    nome_ficheiro = f"transacoes_{conta.username}.csv"
    ficheiro = open(nome_ficheiro, "w", encoding="utf-8", newline="")
    escritor = csv.writer(ficheiro)
    escritor.writerow(["tipo", "data", "iban origem", "username origem", "iban destino", "username destino", "valor"])

    for transacao in transacoes_da_conta:
        if transacao.iban_origem == conta.iban:
            tipo = "Enviada"
        else:
            tipo = "Recebida"

        escritor.writerow([tipo, transacao.data, transacao.iban_origem, transacao.username_origem,
                           transacao.iban_destino, transacao.username_destino, transacao.valor])

    ficheiro.close()
    return nome_ficheiro
