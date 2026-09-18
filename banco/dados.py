#tudo o que mexe em ficheiros: a base de dados sqlite e os ficheiros csv
import os
import sqlite3
import csv
import time

from banco.modelos import Utilizador, Conta, Transacao

#criar as tabelas no ficheiro banco.db (só cria se ainda não existirem)
def criar_tabelas():
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            username TEXT,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            username TEXT,
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bloqueios (
            username TEXT,
            tentativas INTEGER,
            bloqueado_ate REAL
        )
    """)

    ligacao.commit()
    ligacao.close()

#carregar os dados guardados no banco.db para o sistema
def carregar_dados():
    utilizadores = {}
    contas = {}
    transacoes = []
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()

    #migração: nas bases de dados antigas as passwords vinham na tabela contas
    colunas = [linha[1] for linha in cursor.execute("PRAGMA table_info(contas)")]
    if "password" in colunas:
        quantidade = cursor.execute("SELECT COUNT(*) FROM utilizadores").fetchone()[0]
        if quantidade == 0:
            cursor.execute("INSERT INTO utilizadores (username, password) SELECT username, password FROM contas")
            ligacao.commit()

    #cada linha vem como um tuplo, separa-se logo nas variáveis
    for username, password in cursor.execute(
        "SELECT username, password FROM utilizadores"
    ):
        utilizadores[username] = Utilizador(username, password)

    for username, valor, iban in cursor.execute(
        "SELECT username, valor, iban FROM contas"
    ):
        contas[username] = Conta(username, valor, iban)

    for data, valor, iban_origem, username_origem, iban_destino, username_destino in cursor.execute(
        "SELECT data, valor, iban_origem, username_origem, iban_destino, username_destino FROM transacoes"
    ):
        transacoes.append(Transacao(data, valor, iban_origem, username_origem, iban_destino, username_destino))

    ligacao.close()
    return utilizadores, contas, transacoes

#guardar os dados do sistema no banco.db (apaga o que lá estava e guarda tudo de novo)
#se a base de dados estiver ocupada (dois pedidos do site ao mesmo tempo), tenta outra vez
def guardar_dados(utilizadores, contas, transacoes):
    for tentativa in range(3):
        try:
            ligacao = sqlite3.connect("banco.db")
            cursor = ligacao.cursor()
            cursor.execute("DELETE FROM utilizadores")
            cursor.execute("DELETE FROM contas")
            cursor.execute("DELETE FROM transacoes")

            for username in utilizadores:
                utilizador = utilizadores[username]
                cursor.execute(
                    "INSERT INTO utilizadores (username, password) VALUES (?, ?)",
                    (utilizador.username, utilizador.password)
                )

            for username in contas:
                conta = contas[username]
                cursor.execute(
                    "INSERT INTO contas (username, valor, iban) VALUES (?, ?, ?)",
                    (conta.username, conta.valor, conta.iban)
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
            break
        except sqlite3.OperationalError:
            time.sleep(0.2)  #a base de dados estava ocupada, tentar outra vez

#tentativas de login erradas e bloqueios (guardadas na base de dados para
#funcionarem igual no terminal e no site, mesmo com o servidor a correr em processos separados)

#ver o estado das tentativas de um utilizador: devolve (tentativas, bloqueado_ate)
def ver_bloqueio(username):
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()
    cursor.execute("SELECT tentativas, bloqueado_ate FROM bloqueios WHERE username = ?", (username,))
    linha = cursor.fetchone()
    ligacao.close()

    if linha == None:
        return 0, 0
    return linha[0], linha[1]

#anotar as tentativas erradas (e até quando está bloqueado, se for o caso)
def anotar_tentativa(username, tentativas, bloqueado_ate):
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()
    cursor.execute("DELETE FROM bloqueios WHERE username = ?", (username,))
    cursor.execute(
        "INSERT INTO bloqueios (username, tentativas, bloqueado_ate) VALUES (?, ?, ?)",
        (username, tentativas, bloqueado_ate)
    )
    ligacao.commit()
    ligacao.close()

#esquecer as tentativas de um utilizador (login certo ou fim do bloqueio)
def limpar_tentativas(username):
    ligacao = sqlite3.connect("banco.db")
    cursor = ligacao.cursor()
    cursor.execute("DELETE FROM bloqueios WHERE username = ?", (username,))
    ligacao.commit()
    ligacao.close()

#ficheiros de transferências por CSV: vivem na pasta transferencias, um por utilizador
#(transferencias/<username>.csv) e são apagados quando o utilizador sai do sistema

#o caminho do ficheiro de transferências de um utilizador
def caminho_ficheiro_transferencias(username):
    return os.path.join("transferencias", username + ".csv")

#guardar o ficheiro de transferências do utilizador (o site guarda o que foi carregado)
def guardar_ficheiro_transferencias(username, conteudo):
    if not os.path.exists("transferencias"):
        os.mkdir("transferencias")

    ficheiro = open(caminho_ficheiro_transferencias(username), "w", encoding="utf-8")
    ficheiro.write(conteudo)
    ficheiro.close()

#ler o ficheiro de transferências do utilizador
def ler_ficheiro_transferencias(username):
    ficheiro = open(caminho_ficheiro_transferencias(username), "r", encoding="utf-8")
    conteudo = ficheiro.read()
    ficheiro.close()
    return conteudo

#apagar o ficheiro de transferências do utilizador (quando sai do sistema)
def apagar_ficheiro_transferencias(username):
    if os.path.exists(caminho_ficheiro_transferencias(username)):
        os.remove(caminho_ficheiro_transferencias(username))

#ficheiros das transações exportadas: vivem na pasta transacoes, um por utilizador
#(transacoes/transacoes_<username>.csv) e são apagados quando o utilizador sai do sistema

#o caminho do ficheiro de transações exportado de um utilizador
def caminho_ficheiro_transacoes(username):
    return os.path.join("transacoes", f"transacoes_{username}.csv")

#apagar o ficheiro de transações exportado do utilizador (quando sai do sistema)
#só o ficheiro dele é apagado: os dos outros utilizadores ficam intactos
def apagar_ficheiro_transacoes(username):
    if os.path.exists(caminho_ficheiro_transacoes(username)):
        os.remove(caminho_ficheiro_transacoes(username))

#guardar as transações de uma conta num ficheiro CSV: devolve o nome do ficheiro criado
#(o nome tem o username, por isso só é substituído quando o mesmo user exporta de novo)
def guardar_csv(conta, transacoes_da_conta):
    #a pasta transacoes é criada se ainda não existir
    if not os.path.exists("transacoes"):
        os.mkdir("transacoes")

    nome_ficheiro = caminho_ficheiro_transacoes(conta.username)
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
