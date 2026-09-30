import random
import time
from datetime import datetime

from database import get_db


# ============================================================
# CONFIGURAÇÃO
# ============================================================

TOTAL_PARTICIPANTES = 500
INTERVALO_MIN = 0.15
INTERVALO_MAX = 0.80

DOMINIO = "teste.mostra.uniatenas.edu.br"

# Quanto maior, mais provável de votar
# em determinados trabalhos.
PESOS_TRABALHOS = {
    "P-001": 40,
    "P-002": 25,
    "P-003": 20,
    "P-004": 15,
}


# ============================================================
# UTILIDADES
# ============================================================

def agora():
    return datetime.now().isoformat(timespec="seconds")


def criar_participantes(conn):
    print()
    print("=" * 60)
    print("CRIANDO PARTICIPANTES")
    print("=" * 60)

    participantes = []

    for i in range(1, TOTAL_PARTICIPANTES + 1):

        nome = f"Participante Teste {i:04d}"
        email = f"participante{i:04d}@{DOMINIO}"

        conn.execute(
            """
            INSERT OR IGNORE INTO participantes
            (
                nome,
                email,
                ativo
            )
            VALUES (?, ?, 1)
            """,
            (nome, email)
        )

        participante = conn.execute(
            """
            SELECT id, nome, email
            FROM participantes
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        participantes.append(participante)

    conn.commit()

    print(f"{len(participantes)} participantes preparados.")

    return participantes


def obter_trabalhos(conn):
    trabalhos = conn.execute(
        """
        SELECT
            id,
            codigo,
            titulo
        FROM trabalhos
        WHERE ativo = 1
        ORDER BY codigo
        """
    ).fetchall()

    if not trabalhos:
        raise RuntimeError(
            "Nenhum trabalho ativo encontrado."
        )

    return trabalhos


def escolher_trabalho(trabalhos):
    codigos = []
    pesos = []

    for trabalho in trabalhos:

        codigo = trabalho["codigo"]

        codigos.append(trabalho)

        pesos.append(
            PESOS_TRABALHOS.get(codigo, 1)
        )

    return random.choices(
        codigos,
        weights=pesos,
        k=1
    )[0]


def registrar_voto(conn, participante, trabalho):
    momento = agora()

    # Verifica se já existe voto
    voto_existente = conn.execute(
        """
        SELECT trabalho_id
        FROM votos
        WHERE participante_id = ?
        """,
        (participante["id"],)
    ).fetchone()

    if voto_existente:

        return False

    conn.execute(
        """
        INSERT INTO votos
        (
            participante_id,
            trabalho_id,
            criado_em,
            atualizado_em
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            participante["id"],
            trabalho["id"],
            momento,
            momento
        )
    )

    conn.execute(
        """
        INSERT INTO historico_votos
        (
            participante_id,
            trabalho_anterior_id,
            trabalho_novo_id,
            criado_em
        )
        VALUES (?, NULL, ?, ?)
        """,
        (
            participante["id"],
            trabalho["id"],
            momento
        )
    )

    conn.commit()

    return True


def mostrar_ranking(conn):
    ranking = conn.execute(
        """
        SELECT
            t.codigo,
            t.titulo,
            COUNT(DISTINCT v.participante_id) AS votos

        FROM trabalhos t

        LEFT JOIN votos v
            ON v.trabalho_id = t.id

        WHERE t.ativo = 1

        GROUP BY
            t.id,
            t.codigo,
            t.titulo

        ORDER BY
            votos DESC,
            t.codigo ASC
        """
    ).fetchall()

    print()

    for trabalho in ranking:

        barra = "█" * trabalho["votos"]

        print(
            f'{trabalho["codigo"]:6} '
            f'{trabalho["votos"]:4} votos '
            f'{barra}'
        )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    conn = get_db()

    try:

        trabalhos = obter_trabalhos(conn)

        print()
        print("=" * 60)
        print("CARGA DE VOTAÇÃO")
        print("=" * 60)

        print()
        print("Trabalhos disponíveis:")

        for trabalho in trabalhos:
            print(
                f'  {trabalho["codigo"]} - '
                f'{trabalho["titulo"]}'
            )

        participantes = criar_participantes(conn)

        random.shuffle(participantes)

        print()
        print("=" * 60)
        print("INICIANDO VOTAÇÃO")
        print("=" * 60)

        print()
        print(
            f"Participantes : {len(participantes)}"
        )

        print(
            f"Intervalo    : "
            f"{INTERVALO_MIN:.2f}s - "
            f"{INTERVALO_MAX:.2f}s"
        )

        print()
        print(
            "Abra http://127.0.0.1:5000/dashboard "
            "em outra janela."
        )

        print()
        print("Pressione CTRL+C para interromper.")
        print()

        votos = 0

        for participante in participantes:

            trabalho = escolher_trabalho(trabalhos)

            sucesso = registrar_voto(
                conn,
                participante,
                trabalho
            )

            if sucesso:

                votos += 1

                print(
                    f"[{votos:04d}] "
                    f'{participante["nome"]:<25} '
                    f'→ {trabalho["codigo"]} '
                    f'- {trabalho["titulo"]}'
                )

            time.sleep(
                random.uniform(
                    INTERVALO_MIN,
                    INTERVALO_MAX
                )
            )

        print()
        print("=" * 60)
        print("CARGA FINALIZADA")
        print("=" * 60)

        print()
        print(f"Votos inseridos: {votos}")

        mostrar_ranking(conn)

    except KeyboardInterrupt:

        print()
        print()
        print("Carga interrompida pelo usuário.")

        print()
        mostrar_ranking(conn)

    finally:

        conn.close()


if __name__ == "__main__":
    main()
