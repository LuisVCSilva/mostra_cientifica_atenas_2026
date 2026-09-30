async function carregarParticipante() {

    const response = await fetch("/api/me");

    if (!response.ok) {
        window.location.href = "/";
        return;
    }

    const data = await response.json();

    if (!data.autenticado) {
        window.location.href = "/";
        return;
    }

    document.getElementById("participante")
        .textContent =
        `Olá, ${data.participante.nome}.`;
}


async function carregarStatus() {

    const response = await fetch("/api/status");

    const data = await response.json();

    const elemento =
        document.getElementById("status-votacao");

    if (data.votacao_aberta) {

        elemento.textContent =
            "Votação aberta";

        elemento.className =
            "badge bg-success";

    } else {

        elemento.textContent =
            "Votação encerrada";

        elemento.className =
            "badge bg-danger";
    }
}


async function carregarVoto() {

    const response =
        await fetch("/api/meu-voto");

    if (!response.ok) {
        return null;
    }

    const data = await response.json();

    return data.trabalho_id;
}


async function carregarTrabalhos() {

    const response =
        await fetch("/api/trabalhos");

    const trabalhos =
        await response.json();

    const votoAtual =
        await carregarVoto();

    const container =
        document.getElementById("trabalhos");

    container.innerHTML = "";

    trabalhos.forEach(trabalho => {

        const selecionado =
            trabalho.id === votoAtual;

        const autores =
            trabalho.autores ||
            "Autor(es) não informado";

        container.innerHTML += `

            <div class="col-md-6">

                <div class="
                    card
                    h-100
                    shadow-sm
                    ${selecionado ? "border-success border-3" : ""}
                ">

                    <div class="card-body">

                        <span class="badge bg-secondary">
                            ${trabalho.codigo}
                        </span>

                        <h2 class="h5 mt-3">
                            ${trabalho.titulo}
                        </h2>

                        <p class="text-muted">
                            ${autores}
                        </p>

                        <p>
                            ${trabalho.resumo || ""}
                        </p>

                        ${
                            selecionado
                            ? `
                                <div class="alert alert-success">
                                    Seu voto atual
                                </div>
                            `
                            : ""
                        }

                        <button
                            class="btn ${
                                selecionado
                                ? "btn-success"
                                : "btn-primary"
                            } w-100"
                            onclick="votar(${trabalho.id})"
                        >
                            ${
                                selecionado
                                ? "Voto selecionado"
                                : "Votar neste trabalho"
                            }
                        </button>

                    </div>

                </div>

            </div>
        `;
    });
}


async function votar(trabalhoId) {

    const mensagem =
        document.getElementById("mensagem");

    const confirmar =
        confirm(
            "Deseja registrar seu voto neste trabalho?"
        );

    if (!confirmar) {
        return;
    }

    const response =
        await fetch("/api/voto", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                trabalho_id: trabalhoId
            })
        });

    const data =
        await response.json();

    if (!response.ok) {

        mensagem.innerHTML = `
            <div class="alert alert-danger">
                ${data.erro}
            </div>
        `;

        return;
    }

    mensagem.innerHTML = `
        <div class="alert alert-success">
            ${data.mensagem}
        </div>
    `;

    await carregarTrabalhos();
}


document
    .getElementById("logout")
    .addEventListener("click", async function() {

        await fetch(
            "/api/logout",
            {
                method: "POST"
            }
        );

        window.location.href = "/";

    });


carregarParticipante();
carregarStatus();
carregarTrabalhos();
