//service worker do Banco Python UC607
//guarda as páginas e os ficheiros do site para funcionar offline
//os pedidos à API (/api/...) nunca são guardados: os dados do banco são sempre frescos

const NOME_CACHE = "banco-uc607-v1";

//o que fica guardado logo na instalação
const FICHEIROS = [
    "/",
    "/sobre",
    "/faq",
    "/homebanking",
    "/estado",
    "/conta",
    "/css/estilo.css",
    "/js/tema.js",
    "/js/app.js",
    "/js/conta.js",
    "/js/estado.js",
    "/manifest.json",
    "/icons/icon-192.png",
    "/icons/icon-512.png"
];

//instalar: guardar os ficheiros principais
self.addEventListener("install", function (evento) {
    evento.waitUntil(
        caches.open(NOME_CACHE).then(function (cache) {
            return cache.addAll(FICHEIROS);
        })
    );
});

//ativar: apagar caches de versões antigas
self.addEventListener("activate", function (evento) {
    evento.waitUntil(
        caches.keys().then(function (nomes) {
            return Promise.all(nomes.map(function (nome) {
                if (nome != NOME_CACHE) {
                    return caches.delete(nome);
                }
            }));
        })
    );
});

//responder aos pedidos: primeiro a cache, senão a rede (e guarda a resposta)
self.addEventListener("fetch", function (evento) {
    const caminho = new URL(evento.request.url).pathname;

    //a API do banco vai sempre à rede: saldos e transações não se guardam
    if (caminho.startsWith("/api/")) {
        return;
    }

    evento.respondWith(
        caches.match(evento.request).then(function (guardada) {
            if (guardada) {
                return guardada;
            }

            return fetch(evento.request).then(function (resposta) {
                //só se guarda o que é nosso e correu bem
                if (resposta.ok && new URL(evento.request.url).origin == self.location.origin) {
                    const copia = resposta.clone();
                    caches.open(NOME_CACHE).then(function (cache) {
                        cache.put(evento.request, copia);
                    });
                }
                return resposta;
            }).catch(function () {
                //sem rede e sem cache: mostrar a página inicial
                return caches.match("/");
            });
        })
    );
});
