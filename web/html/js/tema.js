//tema claro ou escuro (a escolha fica guardada)
function aplicarTemaGuardado() {
    let tema = localStorage.getItem("tema");
    if (tema == null) {
        tema = "dark";
    }
    document.documentElement.setAttribute("data-bs-theme", tema);
}

function alternarTema() {
    let tema = document.documentElement.getAttribute("data-bs-theme");
    if (tema == "dark") {
        tema = "light";
    } else {
        tema = "dark";
    }
    document.documentElement.setAttribute("data-bs-theme", tema);
    localStorage.setItem("tema", tema);

    //trocar o ícone do botão (sol / lua)
    const botao = document.getElementById("botaoTema");
    if (botao != null) {
        botao.textContent = tema == "dark" ? "☀️" : "🌙";
    }
}

//aplicar o tema guardado assim que a página abre
document.addEventListener("DOMContentLoaded", function () {
    aplicarTemaGuardado();

    const botao = document.getElementById("botaoTema");
    if (botao != null) {
        botao.addEventListener("click", alternarTema);
        botao.textContent = document.documentElement.getAttribute("data-bs-theme") == "dark" ? "☀️" : "🌙";
    }
});
