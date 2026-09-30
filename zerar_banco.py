import argparse

from database import get_db


DOMINIO_TESTE = "teste.mostra.uniatenas.edu.br"


def contar(conn, tabela):
    return conn.execute(
        f"SELECT COUNT(*) FROM {tabela}"
    ).fetchone()[0]


def zerar_projetos(conn):
    conn.execute("DELETE FROM historico_votos")
    conn.execute("DELETE FROM votos")
    conn.execute("DELETE FROM trabalho_autores")
    conn.execute("DELETE FROM autores")
    conn.execute("DELETE FROM trabalhos")

    print("Projetos zerados.")


def zerar_votos(conn):
    conn.execute("DELETE FROM historico_votos")
    conn.execute("DELETE FROM votos")

    print("Votos zerados.")


def zerar_cadastros(conn):
    conn.execute("DELETE FROM codigos_acesso")
    conn.execute("DELETE FROM participantes")

    print("Cadastros zerados.")


def zerar_testes(conn):
    participantes = conn.execute(
        """
        SELECT id
        FROM participantes
        WHERE email LIKE ?
        """,
        (f"%@{DOMINIO_TESTE}",)
    ).fetchall()

    ids = [p["id"] for p in participantes]

    if not ids:
        print("Nenhum cadastro de teste encontrado.")
        return

    placeholders = ",".join("?" for _ in ids)

    conn.execute(
        f"""
        DELETE FROM historico_votos
        WHERE participante_id IN ({placeholders})
        """,
        ids
    )

    conn.execute(
        f"""
        DELETE FROM votos
        WHERE participante_id IN ({placeholders})
        """,
        ids
    )

    conn.execute(
        f"""
        DELETE FROM participantes
        WHERE id IN ({placeholders})
        """,
        ids
    )

    print(f"{len(ids)} participantes de teste removidos.")
    print("Votos de teste removidos.")


def zerar_tudo(conn):
    tabelas = [
        "historico_votos",
        "votos",
        "codigos_acesso",
        "trabalho_autores",
        "autores",
        "trabalho_autores",
        "trabalhos",
        "participantes",
    ]

    # Evita apagar a mesma tabela duas vezes.
    tabelas = list(dict.fromkeys(tabelas))

    for tabela in tabelas:
        conn.execute(f"DELETE FROM {tabela}")

    print("Banco zerado.")


def mostrar_estado(conn):
    tabelas = [
        "participantes",
        "trabalhos",
        "autores",
        "trabalho_autores",
        "votos",
        "historico_votos",
        "codigos_acesso",
    ]

    print()
    print("=" * 45)
    print("ESTADO DO BANCO")
    print("=" * 45)

    for tabela in tabelas:
        print(
            f"{tabela:<22} "
            f"{contar(conn, tabela):>6}"
        )

    print("=" * 45)


def confirmar(operacao):
    resposta = input(
        f"Confirma '{operacao}'? "
        "Digite CONFIRMAR: "
    )

    return resposta.strip().upper() == "CONFIRMAR"


def executar(operacao):

    conn = get_db()

    try:

        if operacao == "projetos":

            zerar_projetos(conn)

        elif operacao == "votos":

            zerar_votos(conn)

        elif operacao == "cadastros":

            zerar_cadastros(conn)

        elif operacao == "testes":

            zerar_testes(conn)

        elif operacao == "tudo":

            zerar_tudo(conn)

        elif operacao == "estado":

            mostrar_estado(conn)
            return

        conn.commit()

        print()
        mostrar_estado(conn)

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


def main():

    parser = argparse.ArgumentParser(
        description="Gerenciador de limpeza do banco da Mostra Científica."
    )

    parser.add_argument(
        "operacao",
        nargs="?",
        choices=[
            "projetos",
            "votos",
            "cadastros",
            "testes",
            "tudo",
            "estado",
        ],
        help="Operação que será executada."
    )

    parser.add_argument(
        "--sim",
        action="store_true",
        help="Executa sem solicitar confirmação."
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Sem argumento: mostra ajuda
    # --------------------------------------------------------

    if not args.operacao:

        parser.print_help()

        print()
        print("Exemplos:")
        print("  python3 zerar_banco.py votos")
        print("  python3 zerar_banco.py testes")
        print("  python3 zerar_banco.py projetos")
        print("  python3 zerar_banco.py cadastros")
        print("  python3 zerar_banco.py tudo")
        print("  python3 zerar_banco.py estado")

        return

    # --------------------------------------------------------
    # Apenas consulta
    # --------------------------------------------------------

    if args.operacao == "estado":

        executar("estado")
        return

    # --------------------------------------------------------
    # Confirmação
    # --------------------------------------------------------

    if not args.sim:

        if not confirmar(args.operacao):

            print("Operação cancelada.")
            return

    executar(args.operacao)


if __name__ == "__main__":
    main()
