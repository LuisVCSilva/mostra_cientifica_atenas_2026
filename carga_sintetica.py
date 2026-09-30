import argparse
import random
from datetime import datetime

from database import get_db


DOMINIO = "teste.mostra.uniatenas.edu.br"


# ============================================================
# DADOS SINTÉTICOS
# ============================================================

NOMES = [
    "Ana",
    "Bruno",
    "Carlos",
    "Daniela",
    "Eduardo",
    "Fernanda",
    "Gabriel",
    "Helena",
    "Isabela",
    "João",
    "Juliana",
    "Lucas",
    "Mariana",
    "Mateus",
    "Natalia",
    "Paulo",
    "Rafael",
    "Renata",
    "Ricardo",
    "Sofia",
]
SOBRENOMES = [
    "Almeida",
    "Barbosa",
    "Carvalho",
    "Costa",
    "Ferreira",
    "Lima",
    "Martins",
    "Mendes",
    "Oliveira",
    "Pereira",
    "Ribeiro",
    "Rodrigues",
    "Santos",
    "Silva",
    "Souza",
]

AREAS = [
    "Inteligência Artificial",
    "Ciência de Dados",
    "Visão Computacional",
    "Sistemas Distribuídos",
    "Computação Científica",
    "Internet das Coisas",
    "Engenharia de Software",
    "Robótica",
    "Segurança da Informação",
    "Modelagem Computacional",
    "Aprendizado de Máquina",
    "Sistemas de Recomendação",
]

TIPOS = [
    "Aplicação",
    "Desenvolvimento",
    "Análise",
    "Modelagem",
    "Estudo",
    "Implementação",
    "Avaliação",
]


def agora():
    return datetime.now().isoformat(timespec="seconds")


def nome_aleatorio():
    return (
        f"{random.choice(NOMES)} "
        f"{random.choice(SOBRENOMES)}"
    )


# ============================================================
# AUTORES
# ============================================================

def criar_autores(conn, quantidade):

    autores = []

    for i in range(quantidade):

        nome = nome_aleatorio()

        # Garante que o nome seja diferente
        # caso o sorteio produza duplicação.
        nome = f"{nome} {i + 1:04d}"

        cursor = conn.execute(
            """
            INSERT INTO autores
            (
                nome
            )
            VALUES (?)
            """,
            (nome,)
        )

        autores.append(cursor.lastrowid)

    print(
        f"Autores criados: {len(autores)}"
    )

    return autores


def proximo_codigo_projeto(conn):
    existentes = {
        row["codigo"]
        for row in conn.execute(
            "SELECT codigo FROM trabalhos"
        ).fetchall()
    }

    numero = 1

    while True:
        codigo = f"S-{numero:03d}"

        if codigo not in existentes:
            return codigo

        numero += 1


def proximo_email(conn, indice):
    email = f"participante{indice:05d}@{DOMINIO}"

    existente = conn.execute(
        """
        SELECT id
        FROM participantes
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    if existente:
        return None

    return email

# ============================================================
# PROJETOS
# ============================================================
def criar_projetos(
    conn,
    quantidade,
    autores,
    autores_por_projeto
):

    trabalhos = []

    for _ in range(quantidade):

        codigo = proximo_codigo_projeto(conn)

        area = random.choice(AREAS)
        tipo = random.choice(TIPOS)

        titulo = (
            f"{tipo} em {area} "
            f"— Estudo Sintético {codigo}"
        )

        resumo = (
            f"Trabalho sintético para demonstração "
            f"da Mostra Científica. "
            f"Área de pesquisa: {area}."
        )

        cursor = conn.execute(
            """
            INSERT INTO trabalhos
            (
                codigo,
                titulo,
                resumo,
                ativo
            )
            VALUES (?, ?, ?, 1)
            """,
            (
                codigo,
                titulo,
                resumo,
            )
        )

        trabalho_id = cursor.lastrowid

        trabalhos.append(trabalho_id)

        quantidade_autores = min(
            autores_por_projeto,
            len(autores)
        )

        autores_escolhidos = random.sample(
            autores,
            quantidade_autores
        )

        for autor_id in autores_escolhidos:

            conn.execute(
                """
                INSERT INTO trabalho_autores
                (
                    trabalho_id,
                    autor_id
                )
                VALUES (?, ?)
                """,
                (
                    trabalho_id,
                    autor_id,
                )
            )

    print(
        f"Projetos criados: {len(trabalhos)}"
    )

    return trabalhos


# ============================================================
# PARTICIPANTES
# ============================================================
def criar_participantes(
    conn,
    quantidade
):

    participantes = []

    numero = 1

    while len(participantes) < quantidade:

        email = (
            f"participante{numero:05d}"
            f"@{DOMINIO}"
        )

        numero += 1

        existente = conn.execute(
            """
            SELECT id
            FROM participantes
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existente:
            continue

        nome = (
            f"Participante Sintético "
            f"{len(participantes) + 1:05d}"
        )

        cursor = conn.execute(
            """
            INSERT INTO participantes
            (
                nome,
                email,
                ativo
            )
            VALUES (?, ?, 1)
            """,
            (
                nome,
                email,
            )
        )

        participantes.append(
            cursor.lastrowid
        )

    print(
        f"Participantes criados: "
        f"{len(participantes)}"
    )

    return participantes

# ============================================================
# VOTOS
# ============================================================

def criar_votos(
    conn,
    participantes,
    trabalhos,
    quantidade_votos
):

    quantidade_votos = min(
        quantidade_votos,
        len(participantes)
    )

    participantes_votantes = random.sample(
        participantes,
        quantidade_votos
    )

    votos = 0

    for participante_id in participantes_votantes:

        trabalho_id = random.choice(
            trabalhos
        )

        momento = agora()

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
                participante_id,
                trabalho_id,
                momento,
                momento,
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
                participante_id,
                trabalho_id,
                momento,
            )
        )

        votos += 1

    print(
        f"Votos criados: {votos}"
    )

    return votos


# ============================================================
# RESUMO
# ============================================================

def mostrar_estado(conn):

    print()
    print("=" * 60)
    print("ESTADO DO BANCO")
    print("=" * 60)

    tabelas = [
        "participantes",
        "trabalhos",
        "autores",
        "trabalho_autores",
        "votos",
        "historico_votos",
    ]

    for tabela in tabelas:

        quantidade = conn.execute(
            f"SELECT COUNT(*) FROM {tabela}"
        ).fetchone()[0]

        print(
            f"{tabela:<22} {quantidade:>8}"
        )

    print("=" * 60)


# ============================================================
# ARGUMENTOS
# ============================================================

def criar_parser():

    parser = argparse.ArgumentParser(
        description=(
            "Gera dados sintéticos para o "
            "sistema da Mostra Científica."
        )
    )

    parser.add_argument(
        "--projetos",
        type=int,
        default=10,
        help="Quantidade de projetos.",
    )

    parser.add_argument(
        "--autores",
        type=int,
        default=20,
        help="Quantidade de autores.",
    )

    parser.add_argument(
        "--autores-por-projeto",
        type=int,
        default=2,
        help="Quantidade média de autores por projeto.",
    )

    parser.add_argument(
        "--participantes",
        type=int,
        default=100,
        help="Quantidade de participantes.",
    )

    parser.add_argument(
        "--votos",
        type=int,
        default=None,
        help=(
            "Quantidade de votos. "
            "Por padrão, todos os participantes votam."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semente aleatória para reprodução dos dados.",
    )

    parser.add_argument(
        "--sem-votos",
        action="store_true",
        help="Cria os dados sem gerar votos.",
    )

    return parser


# ============================================================
# MAIN
# ============================================================

def main():

    parser = criar_parser()
    args = parser.parse_args()

    if args.projetos < 1:
        parser.error("--projetos deve ser >= 1")

    if args.autores < 1:
        parser.error("--autores deve ser >= 1")

    if args.autores_por_projeto < 1:
        parser.error(
            "--autores-por-projeto deve ser >= 1"
        )

    if args.participantes < 1:
        parser.error(
            "--participantes deve ser >= 1"
        )

    if args.votos is not None and args.votos < 0:
        parser.error("--votos deve ser >= 0")

    if args.seed is not None:
        random.seed(args.seed)

    if args.votos is None:
        quantidade_votos = args.participantes
    else:
        quantidade_votos = args.votos

    if args.sem_votos:
        quantidade_votos = 0

    conn = get_db()

    try:

        print()
        print("=" * 60)
        print("CARGA SINTÉTICA")
        print("=" * 60)

        print()
        print(
            f"Projetos              : {args.projetos}"
        )

        print(
            f"Autores               : {args.autores}"
        )

        print(
            f"Autores/projeto       : "
            f"{args.autores_por_projeto}"
        )

        print(
            f"Participantes         : "
            f"{args.participantes}"
        )

        print(
            f"Votos                 : "
            f"{quantidade_votos}"
        )

        print()

        autores = criar_autores(
            conn,
            args.autores,
        )

        trabalhos = criar_projetos(
            conn,
            args.projetos,
            autores,
            args.autores_por_projeto,
        )

        participantes = criar_participantes(
            conn,
            args.participantes,
        )

        criar_votos(
            conn,
            participantes,
            trabalhos,
            quantidade_votos,
        )

        conn.commit()

        mostrar_estado(conn)

        print()
        print("Carga sintética concluída.")

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()
