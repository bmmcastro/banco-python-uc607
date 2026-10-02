# Banco Python UC607

Sistema de transferências bancárias com **duas interfaces a partilhar a mesma lógica**: um programa de terminal e um site web. Cada utilizador tem username e password, a sua conta tem um IBAN único, e o sistema suporta depósitos, levantamentos, transferências por IBAN com confirmação do destinatário, transferências em lote por ficheiro CSV (iban, nome, valor) com validação de tudo antes de executar, histórico com exportação para CSV e pesquisa por data, nome, IBAN ou valor, relatório do sistema com threads (tabela ordenada por valor) e processos (maior/menor saldo, quem mais recebeu/enviou e somas totais), aplicações a prazo com valor cativo, e cálculo de retorno com juro composto (recursivo).

Projeto final da formação **UC00607 — Desenvolver Programas Complexos em Linguagem Estruturada**.
A linguagem de programação principal usada é o Python.
Formador: Diogo Lopes Vaz (EISNT).

Online: https://bancopy607.algarit.pt
Código: https://github.com/bmmcastro/banco-python-uc607
Contas de demonstração: `bruno / bruno123`, `rui / rui123`, `amanda / amanda123` e `mateus / mateus123`

O site tem um menu à esquerda (Início, Sobre e FAQ) e à direita o **Homebanking**
(entrar/criar conta e usar o sistema) e o **Estado da API e Testes**, que testa do browser
(JavaScript) se o Python do servidor está a responder, endpoint a endpoint —
e onde, com um clique, correm-se todos os testes do projeto no servidor
(26 unittest + 4 pytest, juntos).
A página **Sobre** explica o sistema: https://bancopy607.algarit.pt/sobre

## Como correr (a partir desta pasta)

```
pip install -r requirements.txt   uma vez só
python main.py                    o programa no terminal
python -m testes.test_testes      os testes unitários
python -m pytest testes/          os testes todos no pytest (30)
python servidor.py                a interface web em http://127.0.0.1:5000
```

Na primeira execução é criado o `banco.db` com duas contas de teste (bruno e ana) e uma transação de exemplo.

## Como está organizado

O projeto está dividido em módulos e num pacote. A regra é simples: **toda a lógica vive no pacote `banco`** e as duas interfaces são só "caras" diferentes para o mesmo sistema — o `menus.py` conversa com o utilizador no terminal e o `servidor.py` expõe uma API JSON que o site chama com `fetch`.

```
projeto_banco/
├── main.py            arranque da versão terminal
├── servidor.py        a API web (Flask) que liga o site às funções do pacote banco
├── banco/             o pacote com a lógica do sistema
│   ├── modelos.py     as estruturas Utilizador, Conta e Transacao (dataclasses)
│   ├── erros.py       os erros próprios (UtilizadorJaExiste, SaldoInsuficiente, ...)
│   ├── operacoes.py   as funções do banco (criar conta, entrar, transferir, IBAN, retorno)
│   ├── dados.py       a base de dados sqlite e a exportação para CSV
│   ├── relatorio.py   o relatório do sistema com threads
│   └── menus.py       os menus e a conversa com o utilizador (terminal)
├── web/html/          as páginas do site (HTML, CSS e JavaScript)
└── testes/            os testes unitários
```

## O caminho de uma transferência

1. Escreve-se o IBAN de destino. O `limpar_iban()` normaliza o que foi escrito: maiúsculas, sem espaços e sem o `PT50` repetido — por isso `0002`, `pt50 0002` ou `PT50 0002` funcionam todos.
2. O sistema procura de quem é o IBAN (`procurar_por_iban()`) e **mostra o dono antes de qualquer dinheiro sair da conta**.
3. Só depois da confirmação é que a transferência acontece: o valor sai da conta de origem e entra na de destino (`transferir()`).
4. A transação é registada com data e hora e tudo é gravado no `banco.db` logo a seguir à operação.

## Regras e validações

- Password com 6 a 10 caracteres, pelo menos 1 letra e 1 número
- Depois de 3 tentativas de login erradas, a conta fica bloqueada durante 30 segundos
- IBAN único, gerado pelo sistema (`PT50` seguido de um número livre)
- Valor da transferência positivo e saldo suficiente (senão `SaldoInsuficienteError`)
- Não se pode transferir para a própria conta
- Erros próprios em `erros.py`, apanhados com try/except nas duas interfaces

## Dados

- `banco.db` — base de dados SQLite com as contas e as transações (criada automaticamente). Foi a opção tomada para a **persistência dos dados**; a **manipulação de ficheiros** pedida no enunciado está nos dois CSVs abaixo (exportação do histórico e importação de transferências)
- `transacoes/` — as exportações do histórico (`transacoes_<username>.csv`, um por utilizador; a pasta é criada se não existir e o ficheiro é apagado quando o utilizador sai — os dos outros ficam intactos)
- `transferencias/` — os ficheiros de transferências por CSV (um por utilizador; no terminal é `transferencias/<username>.csv`, no site é guardado o ficheiro carregado; o ficheiro é apagado quando o utilizador sai)

## Testes

`testes/test_testes.py` tem 26 testes unitários (unittest): saldo insuficiente, levantamento, depósito, bloqueio de login, exportação e pesquisa de transações, transferências por ficheiro, valores inválidos, retorno (taxa negativa e limites), aplicações (aplicar, libertar com juros, situação e cancelar), estatísticas dos relatórios, registo de movimentos e ordenação por valor e por data.

O projeto tem ainda `testes/test_projeto.py` com 4 testes escritos diretamente em pytest (utilizador duplicado na criação, utilizador inexistente na transferência, transferência com sucesso e saldo insuficiente na transferência) — sem repetir o que já está coberto no outro módulo. O pytest corre tudo: `python -m pytest testes/` passa os 30.

## Bibliotecas usadas

- `dataclasses`, `datetime`, `sqlite3`, `csv`, `threading`, `unittest` (vêm com o Python)
- `pyfiglet` (o banner do arranque), `flask` (a interface web) e `pytest` (os testes de `testes/test_projeto.py`)
