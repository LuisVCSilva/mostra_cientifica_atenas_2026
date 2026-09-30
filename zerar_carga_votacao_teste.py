from database import get_db


DOMINIO = "teste.mostra.uniatenas.edu.br"


def main():
    conn = get_db()

    try:
        # Participantes de teste
        participantes = conn.execute(
            """
            SELECT id, email
            FROM participantes
            WHERE email LIKE ?
            """,
            (f"%@{DOMINIO}",)
        ).fetchall()

        ids = [p["id"] for p in participantes]

        print(f"Participantes de teste encontrados: {len(ids)}")

        if not ids:
            print("Nenhuma carga de teste encontrada.")
            return

        # Apaga histórico dos participantes de teste
        placeholders = ",".join("?" for _ in ids)

        conn.execute(
            f"""
            DELETE FROM historico_votos
            WHERE participante_id IN ({placeholders})
            """,
            ids
        )

        # Apaga votos atuais
        conn.execute(
            f"""
            DELETE FROM votos
            WHERE participante_id IN ({placeholders})
            """,
            ids
        )

        # Apaga os próprios participantes de teste
        conn.execute(
            f"""
            DELETE FROM participantes
            WHERE id IN ({placeholders})
            """,
            ids
        )

        conn.commit()

        print()
        print("Carga de votação zerada.")
        print(f"Participantes removidos: {len(ids)}")
        print("Votos de teste removidos.")
        print("Histórico de votos de teste removido.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
