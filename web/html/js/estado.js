//página do estado da API: o JavaScript pergunta ao Python se ele está vivo

//os endpoints a testar (todos respondem JSON, mesmo sem sessão iniciada)
const endpoints = [
    "/api/estado",
    "/api/conta",
    "/api/transacoes",
    "/api/relatorio"
];

//testar um endpoint: devolve o tempo que demorou, ou falha se não responder
function testarEndpoint(url) {
    const inicio = Date.now();
    return fetch(url).then(function (resposta) {
        return resposta.json();
    }).then(function (dados) {
        if (dados.ok == undefined) {
            throw new Error("resposta sem json");
        }
        return { tempo: Date.now() - inicio };
    });
}

//uma linha da tabela por endpoint
function linhaDoTeste(url) {
    const linha = document.createElement("tr");

    const nome = document.createElement("td");
    nome.className = "iban-mono";
    nome.textContent = url;

    const estado = document.createElement("td");
    const tempo = document.createElement("td");
    tempo.className = "text-end";

    linha.appendChild(nome);
    linha.appendChild(estado);
    linha.appendChild(tempo);

    testarEndpoint(url).then(function (resultado) {
        const badge = document.createElement("span");
        badge.className = "badge text-bg-success";
        badge.textContent = "a responder";
        estado.appendChild(badge);
        tempo.textContent = resultado.tempo + " ms";
    }).catch(function () {
        const badge = document.createElement("span");
        badge.className = "badge text-bg-danger";
        badge.textContent = "sem resposta";
        estado.appendChild(badge);
    });

    return linha;
}

//construir a tabela e preencher a informação do servidor
function verificarTudo() {
    const corpo = document.getElementById("corpoEstado");
    corpo.textContent = "";

    for (const endpoint of endpoints) {
        corpo.appendChild(linhaDoTeste(endpoint));
    }

    //a informação do servidor vem toda do /api/estado
    fetch("/api/estado").then(function (resposta) {
        return resposta.json();
    }).then(function (dados) {
        document.getElementById("estadoHora").textContent = dados.hora;
        document.getElementById("estadoContas").textContent = dados.contas;
        document.getElementById("estadoTransacoes").textContent = dados.transacoes;
    });
}

document.getElementById("botaoVerificar").addEventListener("click", verificarTudo);

//verificar logo quando a página abre
verificarTudo();

//os testes unitários do projeto: correm no servidor e a saída aparece como no terminal
function correrTestes() {
    const saida = document.getElementById("saidaTestes");
    saida.textContent = "";
    const inicio = Date.now();

    fetch("/api/testes").then(function (resposta) {
        return resposta.json();
    }).then(function (dados) {
        const tempo = ((Date.now() - inicio) / 1000).toFixed(3);

        //as linhas do terminal: uma por teste e, no fim, o resumo do unittest
        const linhas = [];
        for (const teste of dados.testes) {
            linhas.push({
                texto: teste.nome + " ... " + (teste.ok ? "ok" : "FAIL"),
                classe: teste.ok ? "linha-ok" : "linha-falha"
            });
            //se falhou, o motivo vem logo abaixo, afastado como no terminal
            if (teste.problema) {
                linhas.push({ texto: "    " + teste.problema, classe: "linha-falha" });
            }
        }
        linhas.push({ texto: "-".repeat(70), classe: "linha-separador" });
        linhas.push({ texto: "Ran " + dados.total + " tests in " + tempo + "s", classe: "" });
        linhas.push({ texto: "", classe: "" });

        const falhas = dados.total - dados.passaram;
        linhas.push({
            texto: falhas == 0 ? "OK" : "FAILED (failures=" + falhas + ")",
            classe: falhas == 0 ? "linha-ok" : "linha-falha"
        });

        //mostrar as linhas uma a uma, como um terminal a correr de verdade
        let atraso = 0;
        for (const linha of linhas) {
            setTimeout(function () {
                const pedaco = document.createElement("span");
                pedaco.className = linha.classe;
                pedaco.textContent = linha.texto;
                saida.appendChild(pedaco);
                saida.appendChild(document.createTextNode("\n"));
                saida.scrollTop = saida.scrollHeight;
            }, atraso);
            atraso = atraso + 30;
        }
    }).catch(function () {
        saida.textContent = "não foi possível correr os testes";
    });
}

document.getElementById("botaoTestes").addEventListener("click", correrTestes);
