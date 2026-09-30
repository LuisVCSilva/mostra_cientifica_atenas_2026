import sqlite3
from pathlib import Path


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "data"

DATABASE_FILE = DATABASE_DIR / "votacao.db"

SCHEMA_FILE = BASE_DIR / "schema.sql"


# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

def get_db():
    """
    Abre uma conexão com o banco SQLite.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(
        DATABASE_FILE,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def init_db():
    """
    Cria as tabelas definidas em schema.sql.
    """

    conn = get_db()

    try:

        with open(
            SCHEMA_FILE,
            "r",
            encoding="utf-8"
        ) as arquivo:

            conn.executescript(
                arquivo.read()
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# SELECT
# ============================================================

def query(
    sql,
    params=(),
    one=False
):
    """
    Executa uma consulta SQL.
    """

    conn = get_db()

    try:

        cursor = conn.execute(
            sql,
            params
        )

        if one:
            return cursor.fetchone()

        return cursor.fetchall()

    finally:

        conn.close()


# ============================================================
# INSERT / UPDATE / DELETE
# ============================================================

def execute(
    sql,
    params=()
):
    """
    Executa INSERT, UPDATE ou DELETE.
    """

    conn = get_db()

    try:

        cursor = conn.execute(
            sql,
            params
        )

        conn.commit()

        return cursor.lastrowid

    finally:

        conn.close()
