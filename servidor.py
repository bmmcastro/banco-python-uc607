#servidor web do Banco Python UC607 (Flask)
#serve as páginas da pasta web/html e a API que liga o site às funções do pacote banco
import os
from datetime import datetime

from flask import Flask, request, jsonify, session, send_file, send_from_directory
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError
from banco.operacoes import criar_conta, entrar, transferir, consultar_retorno, procurar_por_iban, limpar_iban
from banco.dados import criar_tabelas, carregar_dados, guardar_dados, guardar_csv
from banco.relatorio import gerar_relatorio

app = Flask(__name__, static_folder=None)
#a chave das sessões vem do servidor (CHAVE_SECRETA no .htaccess); em local usa-se a chave de teste
app.secret_key = os.environ.get("CHAVE_SECRETA", "banco-python-uc607")

#dados do sistema em memória (iguais aos do main.py)
criar_tabelas()
contas, transacoes = carregar_dados()

if len(contas) == 0:
    from banco.modelos import Conta, Transacao
    contas["bruno"] = Conta("bruno", "bruno123", 100, "PT50 0001")
    contas["ana"] = Conta("ana", "ana123", 200, "PT50 0002")
    contas["bruno"].valor = contas["bruno"].valor - 50
    contas["ana"].valor = contas["ana"].valor + 50
    transacoes.append(Transacao("07/09/2026 10:00", 50, "PT50 0001", "bruno", "PT50 0002", "ana"))
    guardar_dados(contas, transacoes)


#as páginas e os ficheiros do site
@app.route("/")
def pagina_inicial():
    return send_from_directory("web/html", "index.html")

@app.route("/conta")
def pagina_conta():
    return send_from_directory("web/html", "conta.html")

@app.route("/sobre")
def pagina_sobre():
    return send_from_directory("web/html", "sobre.html")

@app.route("/faq")
def pagina_faq():
    return send_from_directory("web/html", "faq.html")

@app.route("/homebanking")
def pagina_homebanking():
    return send_from_directory("web/html", "homebanking.html")

@app.route("/estado")
def pagina_estado():
    return send_from_directory("web/html", "estado.html")

@app.route("/css/<ficheiro>")
def ficheiros_css(ficheiro):
    return send_from_directory("web/html/css", ficheiro)

@app.route("/js/<ficheiro>")
def ficheiros_js(ficheiro):
    return send_from_directory("web/html/js", ficheiro)

@app.route("/algarit-assets/<ficheiro>")
def ficheiros_algarit(ficheiro):
    return send_from_directory("web/html/algarit-assets", ficheiro)

#ficheiros da app instalável (PWA)
@app.route("/manifest.json")
def ficheiro_manifest():
    return send_from_directory("web/html", "manifest.json")

@app.route("/sw.js")
def ficheiro_sw():
    return send_from_directory("web/html", "sw.js")

@app.route("/icons/<ficheiro>")
def ficheiros_icones(ficheiro):
    return send_from_directory("web/html/icons", ficheiro)


#a API do banco

@app.route("/api/entrar", methods=["POST"])
def api_entrar():
    dados = request.get_json()
    conta = entrar(contas, dados["username"], dados["password"])

    if conta == None:
        return jsonify({"ok": False, "erro": "Username ou password errados."})

    session["username"] = conta.username
    return jsonify({"ok": True})

@app.route("/api/registar", methods=["POST"])
def api_registar():
    dados = request.get_json()
    try:
        criar_conta(contas, dados["username"], dados["password"])
        guardar_dados(contas, transacoes)
        return jsonify({"ok": True, "iban": contas[dados["username"]].iban})
    except UtilizadorJaExisteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})

@app.route("/api/sair", methods=["POST"])
def api_sair():
    session.clear()
    return jsonify({"ok": True})

#estado da API: a página do estado usa isto para ver se o Python está vivo
@app.route("/api/estado")
def api_estado():
    return jsonify({
        "ok": True,
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "contas": len(contas),
        "transacoes": len(transacoes)
    })

@app.route("/api/conta")
def api_conta():
    if "username" not in session:
        return jsonify({"ok": False})

    conta = contas[session["username"]]
    return jsonify({"ok": True, "username": conta.username, "iban": conta.iban, "valor": conta.valor})

@app.route("/api/levantar", methods=["POST"])
def api_levantar():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    try:
        conta.levantar(float(request.get_json()["valor"]))
        guardar_dados(contas, transacoes)
        return jsonify({"ok": True, "valor": conta.valor})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except SaldoInsuficienteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})

@app.route("/api/depositar", methods=["POST"])
def api_depositar():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    try:
        conta.depositar(float(request.get_json()["valor"]))
        guardar_dados(contas, transacoes)
        return jsonify({"ok": True, "valor": conta.valor})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})

@app.route("/api/consultar_iban", methods=["POST"])
def api_consultar_iban():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    #limpar o IBAN recebido (maiúsculas, espaços, PT50 repetido)
    iban = limpar_iban(request.get_json()["iban"])
    username = procurar_por_iban(contas, iban)

    if username == None:
        return jsonify({"ok": False, "erro": "O IBAN de destino não existe no sistema."})

    return jsonify({"ok": True, "username": username})

@app.route("/api/transferir", methods=["POST"])
def api_transferir():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    dados = request.get_json()
    try:
        transferir(contas, transacoes, session["username"], limpar_iban(dados["iban_destino"]), float(dados["valor"]))
        guardar_dados(contas, transacoes)
        return jsonify({"ok": True, "valor": contas[session["username"]].valor})
    except UtilizadorInexistenteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except SaldoInsuficienteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})

@app.route("/api/transacoes")
def api_transacoes():
    if "username" not in session:
        return jsonify({"ok": False, "transacoes": []})

    conta = contas[session["username"]]
    lista = []
    for transacao in transacoes:
        if transacao.iban_origem == conta.iban or transacao.iban_destino == conta.iban:
            tipo = "Enviada" if transacao.iban_origem == conta.iban else "Recebida"
            lista.append({
                "tipo": tipo,
                "data": transacao.data,
                "valor": transacao.valor,
                "iban_origem": transacao.iban_origem,
                "username_origem": transacao.username_origem,
                "iban_destino": transacao.iban_destino,
                "username_destino": transacao.username_destino,
            })

    return jsonify({"ok": True, "transacoes": lista})

@app.route("/api/relatorio")
def api_relatorio():
    if "username" not in session:
        return jsonify({"ok": False, "relatorio": []})

    return jsonify({"ok": True, "relatorio": gerar_relatorio(contas, transacoes)})

@app.route("/api/retorno", methods=["POST"])
def api_retorno():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    dados = request.get_json()
    try:
        resultado = consultar_retorno(conta.valor, float(dados["taxa"]), int(float(dados["meses"])))
        return jsonify({"ok": True, "resultado": resultado})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})

@app.route("/api/exportar")
def api_exportar():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    nome_ficheiro = guardar_csv(conta, [
        transacao for transacao in transacoes
        if transacao.iban_origem == conta.iban or transacao.iban_destino == conta.iban
    ])
    return send_file(nome_ficheiro, as_attachment=True)


#arrancar o servidor em http://127.0.0.1:5000
if __name__ == "__main__":
    app.run(debug=True)
