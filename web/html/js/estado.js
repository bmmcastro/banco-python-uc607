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
