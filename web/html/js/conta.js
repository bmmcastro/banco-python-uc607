//tudo o que acontece na página da conta

function pedirPost(url, dados) {
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
    }).then(function (resposta) {
        return resposta.json();
    });
}

function pedirGet(url) {
    return fetch(url).then(function (resposta) {
        return resposta.json();
    });
}

//formatar um valor em euros
function euros(valor) {
    return Number(valor).toLocaleString("pt-PT", { minimumFractionDigits: 2 }) + " €";
}

//se a sessão não estiver aberta, voltar ao início
pedirGet("/api/conta").then(function (dados) {
    if (dados.ok == false) {
        window.location.href = "/";
        return;
    }

    document.getElementById("nomeUtilizador").textContent = dados.username;
    document.getElementById("nomeNavbar").textContent = dados.username;
    document.getElementById("ibanConta").textContent = dados.iban;
    document.getElementById("saldoConta").textContent = euros(dados.valor);
    carregarHistorico();
    carregarRelatorio();
});

//levantar
document.getElementById("formLevantar").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const valor = document.getElementById("levantarValor").value;
    const mensagem = document.getElementById("mensagemLevantar");

    pedirPost("/api/levantar", { valor: valor }).then(function (dados) {
        if (dados.ok) {
            document.getElementById("saldoConta").textContent = euros(dados.valor);
            mensagem.textContent = "Foi levantado " + euros(valor) + ".";
            mensagem.classList.add("text-success");
            carregarHistorico();
        } else {
            mensagem.textContent = dados.erro;
            mensagem.classList.remove("text-success");
        }
    });
});

//depositar
document.getElementById("formDepositar").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const valor = document.getElementById("depositarValor").value;
    const mensagem = document.getElementById("mensagemDepositar");

    pedirPost("/api/depositar", { valor: valor }).then(function (dados) {
        if (dados.ok) {
            document.getElementById("saldoConta").textContent = euros(dados.valor);
            mensagem.textContent = "Foi depositado " + euros(valor) + ".";
            mensagem.classList.add("text-success");
            carregarHistorico();
        } else {
            mensagem.textContent = dados.erro;
            mensagem.classList.remove("text-success");
        }
    });
});

//transferir: primeiro vejo de quem é o IBAN, só depois confirmo
let ibanATransferir = "";

document.getElementById("formTransferir").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const mensagem = document.getElementById("mensagemTransferir");
    const valor = document.getElementById("transferirValor").value;
    const confirmacao = document.getElementById("confirmacaoTransferencia");

    //primeiro clique: ver de quem é o IBAN
    if (confirmacao.classList.contains("d-none")) {
        //envia-se o que foi escrito: o servidor mete o PT50 e limpa maiúsculas e espaços
        ibanATransferir = document.getElementById("transferirIban").value;

        pedirPost("/api/consultar_iban", { iban: ibanATransferir }).then(function (dados) {
            if (dados.ok == false) {
                mensagem.textContent = dados.erro;
                mensagem.classList.remove("d-none");
                return;
            }
            document.getElementById("donoIban").textContent = dados.username;
            confirmacao.classList.remove("d-none");
            mensagem.classList.add("d-none");
        });
        return;
    }

    //segundo clique: confirmar e transferir
    pedirPost("/api/transferir", { iban_destino: ibanATransferir, valor: valor }).then(function (dados) {
        if (dados.ok) {
            document.getElementById("saldoConta").textContent = euros(dados.valor);
            mensagem.textContent = "Transferência efetuada com sucesso.";
            mensagem.classList.remove("d-none");
            mensagem.classList.add("text-success");
            cancelarTransferencia();
            carregarHistorico();
            carregarRelatorio();
        } else {
            mensagem.textContent = dados.erro;
            mensagem.classList.remove("d-none");
            mensagem.classList.remove("text-success");
        }
    });
});

//limpar o formulário, para poder mudar de IBAN
function cancelarTransferencia() {
    document.getElementById("confirmacaoTransferencia").classList.add("d-none");
    document.getElementById("formTransferir").reset();
    ibanATransferir = "";
}

//transferir por ficheiro CSV: o site le o ficheiro e o servidor valida tudo
document.getElementById("formCsv").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const mensagem = document.getElementById("mensagemCsv");
    const ficheiro = document.getElementById("csvFicheiro").files[0];

    if (ficheiro == undefined) {
        return;
    }

    //ler o conteúdo do ficheiro escolhido pelo utilizador
    const leitor = new FileReader();
    leitor.onload = function () {
        pedirPost("/api/transferencias_ficheiro", { conteudo: leitor.result }).then(function (dados) {
            mensagem.classList.remove("d-none");
            mensagem.classList.remove("text-success");
            mensagem.textContent = "";

            if (dados.ok) {
                document.getElementById("saldoConta").textContent = euros(dados.valor);
                mensagem.textContent = "Transferências do ficheiro efetuadas com sucesso.";
                mensagem.classList.add("text-success");
                document.getElementById("formCsv").reset();
                carregarHistorico();
                carregarRelatorio();
            } else if (dados.erros != undefined) {
                //mostrar a lista de problemas encontrados no ficheiro
                const lista = document.createElement("ul");
                lista.className = "mb-0 ps-3";
                for (const erro of dados.erros) {
                    const item = document.createElement("li");
                    item.textContent = erro;
                    lista.appendChild(item);
                }
                mensagem.appendChild(lista);
            } else {
                mensagem.textContent = dados.erro;
            }
        });
    };
    leitor.readAsText(ficheiro);
});

//consultar o retorno (juro composto)
document.getElementById("formRetorno").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const taxa = document.getElementById("retornoTaxa").value;
    const meses = document.getElementById("retornoMeses").value;
    const resultado = document.getElementById("resultadoRetorno");

    pedirPost("/api/retorno", { taxa: taxa, meses: meses }).then(function (dados) {
        if (dados.ok) {
            resultado.textContent = "A conta fica com " + euros(dados.resultado) + " no final dos " + meses + " meses.";
            resultado.classList.remove("d-none");
        } else {
            resultado.textContent = dados.erro;
            resultado.classList.remove("d-none");
        }
    });
});

//histórico de transações (tabela); com pesquisa, só as transações que correspondem
function carregarHistorico(pesquisa) {
    let url = "/api/transacoes";
    if (pesquisa != undefined && pesquisa != "") {
        url = url + "?pesquisa=" + encodeURIComponent(pesquisa);
    }

    pedirGet(url).then(function (dados) {
        const corpo = document.getElementById("corpoHistorico");
        corpo.textContent = "";

        if (dados.transacoes.length == 0) {
            corpo.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">Ainda não existem transações nesta conta.</td></tr>';
            return;
        }

        for (const transacao of dados.transacoes) {
            const linha = document.createElement("tr");

            const tipo = document.createElement("td");
            const badge = document.createElement("span");
            badge.className = transacao.tipo == "Enviada" ? "badge text-bg-danger" : "badge text-bg-success";
            badge.textContent = transacao.tipo;
            tipo.appendChild(badge);

            const data = document.createElement("td");
            data.textContent = transacao.data;

            const conta = document.createElement("td");
            conta.textContent = "De " + transacao.username_origem + " (" + transacao.iban_origem + ")"
                + " → Para " + transacao.username_destino + " (" + transacao.iban_destino + ")";

            const valor = document.createElement("td");
            valor.className = transacao.tipo == "Enviada" ? "text-danger" : "text-success";
            valor.textContent = (transacao.tipo == "Enviada" ? "-" : "+") + euros(transacao.valor);

            linha.appendChild(tipo);
            linha.appendChild(data);
            linha.appendChild(conta);
            linha.appendChild(valor);
            corpo.appendChild(linha);
        }
    });
}

//relatório do sistema (ordenado pelo valor)
function carregarRelatorio() {
    pedirGet("/api/relatorio").then(function (dados) {
        const corpo = document.getElementById("corpoRelatorio");
        corpo.textContent = "";

        //as estatísticas (calculadas em dois processos no servidor)
        const estatisticas = document.getElementById("estatisticasRelatorio");
        estatisticas.textContent = "";

        if (dados.estatisticas != undefined) {
            const contas = dados.estatisticas.contas;
            const transferencias = dados.estatisticas.transferencias;

            if (contas.maior != null) {
                const linha = document.createElement("div");
                linha.textContent = "💰 Maior saldo: " + contas.maior[1].join(", ") + " (" + euros(contas.maior[0])
                    + ") | Menor: " + contas.menor[1].join(", ") + " (" + euros(contas.menor[0])
                    + ") | Soma de todos os saldos: " + euros(contas.soma);
                estatisticas.appendChild(linha);
            }

            if (transferencias.mais_recebeu != null) {
                const linha = document.createElement("div");
                linha.textContent = "🔁 Quem mais recebeu: " + transferencias.mais_recebeu[1].join(", ")
                    + " (" + euros(transferencias.mais_recebeu[0])
                    + ") | Quem mais enviou: " + transferencias.mais_enviou[1].join(", ")
                    + " (" + euros(transferencias.mais_enviou[0])
                    + ") | Total transferido: " + euros(transferencias.total);
                estatisticas.appendChild(linha);
            }
        }

        for (const linha of dados.relatorio) {
            const tr = document.createElement("tr");

            const username = document.createElement("td");
            username.textContent = linha[1];

            const transferencias = document.createElement("td");
            transferencias.textContent = linha[2];

            const valor = document.createElement("td");
            valor.textContent = euros(linha[0]);

            tr.appendChild(username);
            tr.appendChild(transferencias);
            tr.appendChild(valor);
            corpo.appendChild(tr);
        }
    });
}

//pesquisar no histórico: a pesquisa é feita pelo Python no servidor
document.getElementById("formPesquisar").addEventListener("submit", function (evento) {
    evento.preventDefault();
    carregarHistorico(document.getElementById("pesquisarTexto").value);
});

//aplicar dinheiro (depósito a prazo): o valor sai do saldo e fica cativo até ao fim do prazo
document.getElementById("formAplicar").addEventListener("submit", function (evento) {
    evento.preventDefault();
    const mensagem = document.getElementById("mensagemAplicar");

    pedirPost("/api/aplicar", {
        valor: document.getElementById("aplicarValor").value,
        taxa: document.getElementById("aplicarTaxa").value,
        meses: document.getElementById("aplicarMeses").value
    }).then(function (dados) {
        mensagem.classList.remove("d-none");
        mensagem.classList.remove("text-success");

        if (dados.ok) {
            document.getElementById("saldoConta").textContent = euros(dados.valor);
            mensagem.textContent = "Aplicação feita. O valor fica cativo até ao fim do prazo.";
            mensagem.classList.add("text-success");
            document.getElementById("formAplicar").reset();
            carregarAplicacoes();
        } else {
            mensagem.textContent = dados.erro;
        }
    });
});

//as aplicações ativas da conta (o dinheiro cativo) e o histórico das terminadas
function carregarAplicacoes() {
    pedirGet("/api/aplicacoes").then(function (dados) {
        const lista = document.getElementById("listaAplicacoes");
        lista.textContent = "";

        if (dados.aplicacoes.length > 0) {
            const titulo = document.createElement("div");
            titulo.className = "text-secondary";
            titulo.textContent = "Aplicações ativas:";
            lista.appendChild(titulo);

            for (const aplicacao of dados.aplicacoes) {
                const linha = document.createElement("div");
                linha.textContent = euros(aplicacao.valor) + " | " + aplicacao.taxa + "% | "
                    + aplicacao.meses + " meses | hoje vale " + euros(aplicacao.valor_hoje)
                    + " | faltam " + aplicacao.dias_restantes + " dias (até " + aplicacao.data_fim + ")";
                lista.appendChild(linha);
            }
        }

        if (dados.historico.length > 0) {
            const titulo = document.createElement("div");
            titulo.className = "text-secondary mt-2";
            titulo.textContent = "Histórico (terminadas):";
            lista.appendChild(titulo);

            for (const aplicacao of dados.historico) {
                const linha = document.createElement("div");
                linha.textContent = euros(aplicacao.valor) + " | " + aplicacao.taxa + "% | "
                    + aplicacao.meses + " meses | recebeu " + euros(aplicacao.valor_final)
                    + " | terminou a " + aplicacao.data_fim;
                lista.appendChild(linha);
            }
        }
    });
}
carregarAplicacoes();

//sair da conta
document.getElementById("botaoSair").addEventListener("click", function () {
    pedirPost("/api/sair", {}).then(function () {
        window.location.href = "/";
    });
});
