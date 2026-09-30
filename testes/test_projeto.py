#testes ao projeto escritos diretamente com a biblioteca pytest
#(correr com: python -m pytest testes/ a partir da pasta do projeto)
import os
import sys

#garantir que a pasta do projeto está no caminho do Python,
#para os testes correrem bem mesmo quando são arrancados de outra pasta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from banco.modelos import Utilizador, Conta
from banco.operacoes import criar_utilizador, transferir
from banco.erros import UtilizadorJaExisteError, UtilizadorInexistenteError, SaldoInsuficienteError


#utilizadores e contas de teste usados pelos testes (o mesmo arranjo para todos)
def arranjar():
    utilizadores = {}
    contas = {}
    transacoes = []
    utilizadores["bruno"] = Utilizador("bruno", "bruno123")
    contas["bruno"] = Conta("bruno", 100, "PT50 0001")
    utilizadores["ana"] = Utilizador("ana", "ana123")
    contas["ana"] = Conta("ana", 200, "PT50 0002")
    return utilizadores, contas, transacoes


#teste ao utilizador duplicado na criação
def test_utilizador_duplicado_na_criacao():
    utilizadores, contas, _ = arranjar()

    with pytest.raises(UtilizadorJaExisteError):
        criar_utilizador(utilizadores, contas, "bruno", "outra123")


#teste ao utilizador inexistente na transferência
def test_utilizador_inexistente_na_transferencia():
    _, contas, transacoes = arranjar()

    with pytest.raises(UtilizadorInexistenteError):
        transferir(contas, transacoes, "bruno", "PT50 9999", 10)


#teste à transferência com sucesso
def test_transferencia_com_sucesso():
    _, contas, transacoes = arranjar()

    transferir(contas, transacoes, "bruno", "PT50 0002", 25)

    assert contas["bruno"].valor == 75    #100 - 25
    assert contas["ana"].valor == 225     #200 + 25
    assert len(transacoes) == 1           #a transferência ficou registada


#teste ao saldo insuficiente na transferência
def test_saldo_insuficiente_na_transferencia():
    _, contas, transacoes = arranjar()

    with pytest.raises(SaldoInsuficienteError):
        transferir(contas, transacoes, "bruno", "PT50 0002", 500)
