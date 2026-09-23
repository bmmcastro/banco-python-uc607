#servidor web do Banco Python UC607 (Flask)
#serve as páginas da pasta web/html e a API que liga o site às funções do pacote banco
import os
from datetime import datetime

from flask import Flask, request, jsonify, session, send_file, send_from_directory
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError, ContaBloqueadaError
from banco.operacoes import criar_utilizador, entrar, transferir, consultar_retorno, procurar_por_iban, limpar_iban, transferir_por_ficheiro, pesquisar_transacoes, aplicar_dinheiro, verificar_aplicacoes
from banco.dados import criar_tabelas, carregar_dados, guardar_dados, guardar_csv, guardar_ficheiro_transferencias, apagar_ficheiro_transferencias, apagar_ficheiro_transacoes, guardar_aplicacoes, guardar_no_historico, listar_historico_aplicacoes
from banco.relatorio import gerar_relatorio, gerar_relatorio_processos

app = Flask(__name__, static_folder=None)
#a chave das sessões vem do servidor (CHAVE_SECRETA no .htaccess); em local usa-se a chave de teste
app.secret_key = os.environ.get("CHAVE_SECRETA", "banco-python-uc607")

#dados do sistema em memória (iguais aos do main.py)
criar_tabelas()
utilizadores, contas, transacoes, aplicacoes = carregar_dados()

if len(contas) == 0:
    from banco.modelos import Utilizador, Conta, Transacao
    utilizadores["bruno"] = Utilizador("bruno", "bruno123")
    contas["bruno"] = Conta("bruno", 100, "PT50 0001")
    utilizadores["ana"] = Utilizador("ana", "ana123")
    contas["ana"] = Conta("ana", 200, "PT50 0002")
    contas["bruno"].valor = contas["bruno"].valor - 50
    contas["ana"].valor = contas["ana"].valor + 50
    transacoes.append(Transacao("07/09/2026 10:00", 50, "PT50 0001", "bruno", "PT50 0002", "ana"))
    guardar_dados(utilizadores, contas, transacoes)


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
    dados = request.get_json(silent=True)
    try:
        utilizador = entrar(utilizadores, dados["username"], dados["password"])
    except ContaBloqueadaError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except UtilizadorInexistenteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

    if utilizador == None:
        return jsonify({"ok": False, "erro": "Username ou password errados."})

    session["username"] = utilizador.username
    return jsonify({"ok": True})

@app.route("/api/registar", methods=["POST"])
def api_registar():
    dados = request.get_json(silent=True)
    try:
        criar_utilizador(utilizadores, contas, dados["username"], dados["password"])
        guardar_dados(utilizadores, contas, transacoes)
        return jsonify({"ok": True, "iban": contas[dados["username"]].iban})
    except UtilizadorJaExisteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

@app.route("/api/sair", methods=["POST"])
def api_sair():
    #os ficheiros do utilizador (transferências e transações exportadas) são apagados quando ele sai
    if "username" in session:
        apagar_ficheiro_transferencias(session["username"])
        apagar_ficheiro_transacoes(session["username"])
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

    #as aplicações que chegaram ao fim do prazo libertam o dinheiro com os juros
    libertadas = verificar_aplicacoes(conta, aplicacoes)
    for aplicacao in libertadas:
        guardar_no_historico(aplicacao)
    if len(libertadas) > 0:
        guardar_dados(utilizadores, contas, transacoes)
        guardar_aplicacoes(aplicacoes)

    return jsonify({"ok": True, "username": conta.username, "iban": conta.iban, "valor": conta.valor})

#as aplicações ativas (depósitos a prazo) da conta
@app.route("/api/aplicacoes")
def api_aplicacoes():
    if "username" not in session:
        return jsonify({"ok": False, "aplicacoes": []})

    lista = []
    for aplicacao in aplicacoes:
        if aplicacao.username == session["username"]:
            retorno = consultar_retorno(aplicacao.valor, aplicacao.taxa, aplicacao.meses)
            lista.append({
                "valor": aplicacao.valor,
                "taxa": aplicacao.taxa,
                "meses": aplicacao.meses,
                "retorno": retorno,
                "data_fim": aplicacao.data_fim,
            })

    #o histórico das aplicações que já terminaram
    historico = []
    for aplicacao in listar_historico_aplicacoes(session["username"]):
        historico.append({
            "valor": aplicacao.valor,
            "taxa": aplicacao.taxa,
            "meses": aplicacao.meses,
            "valor_final": aplicacao.valor_final,
            "data_fim": aplicacao.data_fim,
        })

    return jsonify({"ok": True, "aplicacoes": lista, "historico": historico})

#aplicar dinheiro: o valor sai do saldo e fica cativo até ao fim do prazo
@app.route("/api/aplicar", methods=["POST"])
def api_aplicar():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    dados = request.get_json(silent=True)
    try:
        aplicar_dinheiro(conta, aplicacoes, float(dados["valor"]), float(dados["taxa"]), int(float(dados["meses"])))
        guardar_dados(utilizadores, contas, transacoes)
        guardar_aplicacoes(aplicacoes)
        return jsonify({"ok": True, "valor": conta.valor})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except SaldoInsuficienteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

@app.route("/api/levantar", methods=["POST"])
def api_levantar():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    try:
        conta.levantar(float(request.get_json(silent=True)["valor"]))
        guardar_dados(utilizadores, contas, transacoes)
        return jsonify({"ok": True, "valor": conta.valor})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except SaldoInsuficienteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

@app.route("/api/depositar", methods=["POST"])
def api_depositar():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    try:
        conta.depositar(float(request.get_json(silent=True)["valor"]))
        guardar_dados(utilizadores, contas, transacoes)
        return jsonify({"ok": True, "valor": conta.valor})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

@app.route("/api/consultar_iban", methods=["POST"])
def api_consultar_iban():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    #limpar o IBAN recebido (maiúsculas, espaços, PT50 repetido)
    try:
        iban = limpar_iban(request.get_json(silent=True)["iban"])
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

    username = procurar_por_iban(contas, iban)

    if username == None:
        return jsonify({"ok": False, "erro": "O IBAN de destino não existe no sistema."})

    return jsonify({"ok": True, "username": username})

@app.route("/api/transferir", methods=["POST"])
def api_transferir():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    dados = request.get_json(silent=True)
    try:
        transferir(contas, transacoes, session["username"], limpar_iban(dados["iban_destino"]), float(dados["valor"]))
        guardar_dados(utilizadores, contas, transacoes)
        return jsonify({"ok": True, "valor": contas[session["username"]].valor})
    except UtilizadorInexistenteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except SaldoInsuficienteError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

#ficheiro de exemplo das transferências por CSV (para o utilizador ver o formato)
@app.route("/transferencias_exemplo.csv")
def ficheiro_exemplo_transferencias():
    return send_from_directory("web/html", "transferencias_exemplo.csv", as_attachment=True)

#transferências em lote a partir de um ficheiro CSV enviado pelo site
@app.route("/api/transferencias_ficheiro", methods=["POST"])
def api_transferencias_ficheiro():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    try:
        conteudo = request.get_json(silent=True)["conteudo"]

        #o ficheiro carregado fica guardado na pasta transferencias (sai quando o utilizador sai)
        guardar_ficheiro_transferencias(session["username"], conteudo)

        erros = transferir_por_ficheiro(contas, transacoes, session["username"], conteudo)
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

    if len(erros) > 0:
        return jsonify({"ok": False, "erros": erros})

    guardar_dados(contas, transacoes)
    return jsonify({"ok": True, "valor": contas[session["username"]].valor})

@app.route("/api/transacoes")
def api_transacoes():
    if "username" not in session:
        return jsonify({"ok": False, "transacoes": []})

    conta = contas[session["username"]]

    #a pesquisa vem no endereço (?pesquisa=...); sem pesquisa mostra tudo
    pesquisa = request.args.get("pesquisa", "")
    minhas_transacoes = pesquisar_transacoes(transacoes, conta, pesquisa)

    lista = []
    for transacao in minhas_transacoes:
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

    #as estatísticas correm em dois processos (contas e transferências)
    stats_contas, stats_transf = gerar_relatorio_processos(contas, transacoes)

    return jsonify({
        "ok": True,
        "relatorio": gerar_relatorio(contas, transacoes),
        "estatisticas": {"contas": stats_contas, "transferencias": stats_transf},
    })

@app.route("/api/retorno", methods=["POST"])
def api_retorno():
    if "username" not in session:
        return jsonify({"ok": False, "erro": "Não tens sessão iniciada."})

    conta = contas[session["username"]]
    dados = request.get_json(silent=True)
    try:
        resultado = consultar_retorno(conta.valor, float(dados["taxa"]), int(float(dados["meses"])))
        return jsonify({"ok": True, "resultado": resultado})
    except ValueError as erro:
        return jsonify({"ok": False, "erro": str(erro)})
    except (KeyError, TypeError):
        return jsonify({"ok": False, "erro": "Pedido inválido: faltam dados."})

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
