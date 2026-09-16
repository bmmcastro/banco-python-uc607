//página inicial: entrar e criar conta

//fazer um pedido POST com json (uso isto em todas as páginas)
function pedirPost(url, dados) {
    return fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
    }).then(function (resposta) {
        return resposta.json();
    });
}

//entrar na conta
document.getElementById("formEntrar").addEventListener("submit", function (evento) {
    evento.preventDefault();

    const username = document.getElementById("entrarUsername").value;
    const password = document.getElementById("entrarPassword").value;
    const mensagem = document.getElementById("mensagemEntrar");

    pedirPost("/api/entrar", { username: username, password: password }).then(function (dados) {
        if (dados.ok) {
            window.location.href = "/conta";
        } else {
            mensagem.textContent = dados.erro;
            mensagem.classList.remove("d-none");
        }
    });
});

//criar conta nova
document.getElementById("formRegistar").addEventListener("submit", function (evento) {
    evento.preventDefault();

    const username = document.getElementById("registarUsername").value;
    const password = document.getElementById("registarPassword").value;
    const mensagem = document.getElementById("mensagemRegistar");

    pedirPost("/api/registar", { username: username, password: password }).then(function (dados) {
        if (dados.ok) {
            mensagem.textContent = "Conta criada com sucesso! O teu IBAN é " + dados.iban + ". Já podes entrar.";
            mensagem.classList.remove("d-none");
            mensagem.classList.add("text-success");
        } else {
            mensagem.textContent = dados.erro;
            mensagem.classList.remove("d-none");
        }
    });
});
