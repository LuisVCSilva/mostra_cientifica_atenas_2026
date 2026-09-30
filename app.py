import os
import secrets
import hashlib
import smtplib

from datetime import datetime, timezone
from email.message import EmailMessage

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from database import get_db, init_db


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "chave-dev-trocar-em-producao"
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
)

CODE_EXPIRATION_MINUTES = 10


# ============================================================
# INICIALIZAÇÃO
# ============================================================

init_db()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def agora():
    return datetime.now(timezone.utc).isoformat()


def normalizar_email(email):
    return email.strip().lower()


def hash_codigo(codigo):
    return hashlib.sha256(
        codigo.encode("utf-8")
    ).hexdigest()


def votacao_aberta():
    conn = get_db()

    row = conn.execute("""
        SELECT valor
        FROM configuracoes
        WHERE chave = 'votacao_aberta'
    """).fetchone()

    conn.close()

    return row and row["valor"] == "1"


def gerar_codigo():
    return f"{secrets.randbelow(1_000_000):06d}"


def enviar_codigo(email, codigo):
    """
    Configuração de e-mail.

    Para usar no PythonAnywhere, defina as variáveis:

    SMTP_HOST
    SMTP_PORT
    SMTP_USER
    SMTP_PASSWORD
    SMTP_FROM
    """

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)

    if not all([
        smtp_host,
        smtp_user,
        smtp_password,
        smtp_from
    ]):
        print(
            f"[DEV] Código para {email}: {codigo}"
        )
        return True

    mensagem = EmailMessage()

    mensagem["Subject"] = "Código de acesso — Mostra Científica"
    mensagem["From"] = smtp_from
    mensagem["To"] = email

    mensagem.set_content(
        f"""
Olá!

Seu código de acesso à votação da Mostra Científica é:

{codigo}

O código é válido por {CODE_EXPIRATION_MINUTES} minutos.

Se você não solicitou este código, ignore esta mensagem.

"""
    )

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as smtp:

        smtp.starttls()

        smtp.login(
            smtp_user,
            smtp_password
        )

        smtp.send_message(mensagem)

    return True


def participante_logado():
    return session.get("participante_id")


# ============================================================
# PÁGINAS
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/votar")
def votar():
    if not participante_logado():
        return redirect(url_for("index"))

    return render_template("votar.html")


@app.route("/ranking")
def ranking():
    return render_template("ranking.html")


@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("index"))

    return render_template("admin.html")


# ============================================================
# LOGIN
# ============================================================

# ============================================================
# DASHBOARD AO VIVO
# ============================================================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.get("/api/me")
def me():

    participante_id = participante_logado()

    if not participante_id:
        return jsonify({
            "autenticado": False
        })

    return jsonify({
        "autenticado": True,
        "participante": {
            "id": participante_id,
            "nome": session.get("participante_nome"),
            "email": session.get("participante_email")
        }
    })

@app.post("/api/login")
def solicitar_codigo():

    data = request.get_json(silent=True) or {}

    email = normalizar_email(
        data.get("email", "")
    )

    if not email:
        return jsonify({
            "erro": "Informe um e-mail."
        }), 400

    conn = get_db()

    participante = conn.execute("""
        SELECT id, nome, email
        FROM participantes
        WHERE email = ?
        AND ativo = 1
    """, (email,)).fetchone()

    if not participante:
        conn.close()

        return jsonify({
            "erro": "E-mail não encontrado no cadastro do evento."
        }), 404

    codigo = gerar_codigo()

    codigo_hash = hash_codigo(codigo)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS codigos_acesso (
            email TEXT PRIMARY KEY,
            codigo_hash TEXT NOT NULL,
            expira_em TEXT NOT NULL
        )
    """)

    conn.execute("""
        INSERT INTO codigos_acesso (
            email,
            codigo_hash,
            expira_em
        )
        VALUES (?, ?, datetime('now', '+10 minutes'))

        ON CONFLICT(email)
        DO UPDATE SET
            codigo_hash = excluded.codigo_hash,
            expira_em = excluded.expira_em
    """, (
        email,
        codigo_hash
    ))

    conn.commit()
    conn.close()

    try:
        enviar_codigo(
            email,
            codigo
        )

    except Exception as erro:

        print(
            "Erro ao enviar e-mail:",
            erro
        )

        return jsonify({
            "erro": "Não foi possível enviar o código."
        }), 500

    return jsonify({
        "sucesso": True,
        "mensagem": "Código enviado para seu e-mail."
    })


@app.post("/api/verificar")
def verificar_codigo():

    data = request.get_json(silent=True) or {}

    email = normalizar_email(
        data.get("email", "")
    )

    codigo = data.get(
        "codigo",
        ""
    ).strip()

    if not email or not codigo:
        return jsonify({
            "erro": "E-mail e código são obrigatórios."
        }), 400

    conn = get_db()

    registro = conn.execute("""
        SELECT
            codigo_hash,
            expira_em
        FROM codigos_acesso
        WHERE email = ?
    """, (email,)).fetchone()

    if not registro:
        conn.close()

        return jsonify({
            "erro": "Código inválido."
        }), 401

    codigo_hash = hash_codigo(codigo)

    if codigo_hash != registro["codigo_hash"]:
        conn.close()

        return jsonify({
            "erro": "Código inválido."
        }), 401

    expirou = conn.execute("""
        SELECT datetime(?) < datetime('now')
    """, (registro["expira_em"],)).fetchone()[0]

    if expirou:
        conn.close()

        return jsonify({
            "erro": "Código expirado."
        }), 401

    participante = conn.execute("""
        SELECT id, nome, email
        FROM participantes
        WHERE email = ?
        AND ativo = 1
    """, (email,)).fetchone()

    conn.close()

    if not participante:
        return jsonify({
            "erro": "Participante não encontrado."
        }), 404

    session.clear()

    session["participante_id"] = participante["id"]
    session["participante_nome"] = participante["nome"]
    session["participante_email"] = participante["email"]

    return jsonify({
        "sucesso": True,
        "nome": participante["nome"]
    })


@app.post("/api/logout")
def logout():

    session.clear()

    return jsonify({
        "sucesso": True
    })


# ============================================================
# TRABALHOS
# ============================================================

@app.get("/api/trabalhos")
def listar_trabalhos():

    conn = get_db()

    trabalhos = conn.execute("""
        SELECT
            t.id,
            t.codigo,
            t.titulo,
            t.resumo,
            GROUP_CONCAT(a.nome, ', ') AS autores
        FROM trabalhos t

        LEFT JOIN trabalho_autores ta
            ON ta.trabalho_id = t.id

        LEFT JOIN autores a
            ON a.id = ta.autor_id

        WHERE t.ativo = 1

        GROUP BY
            t.id,
            t.codigo,
            t.titulo,
            t.resumo

        ORDER BY t.codigo
    """).fetchall()

    conn.close()

    return jsonify([
        dict(t)
        for t in trabalhos
    ])


# ============================================================
# MEU VOTO
# ============================================================

@app.get("/api/meu-voto")
def meu_voto():

    participante_id = participante_logado()

    if not participante_id:
        return jsonify({
            "erro": "Não autenticado."
        }), 401

    conn = get_db()

    voto = conn.execute("""
        SELECT trabalho_id
        FROM votos
        WHERE participante_id = ?
    """, (participante_id,)).fetchone()

    conn.close()

    return jsonify({
        "trabalho_id": (
            voto["trabalho_id"]
            if voto
            else None
        )
    })


@app.route("/anais")
def anais():
    return render_template("anais.html")

# ============================================================
# VOTAÇÃO
# ============================================================

@app.post("/api/voto")
def votar_trabalho():

    participante_id = participante_logado()

    if not participante_id:
        return jsonify({
            "erro": "Não autenticado."
        }), 401

    if not votacao_aberta():
        return jsonify({
            "erro": "A votação está encerrada."
        }), 403

    data = request.get_json(silent=True) or {}

    try:
        trabalho_id = int(
            data.get("trabalho_id")
        )

    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "erro": "Trabalho inválido."
        }), 400

    conn = get_db()

    try:

        trabalho = conn.execute("""
            SELECT id
            FROM trabalhos
            WHERE id = ?
            AND ativo = 1
        """, (trabalho_id,)).fetchone()

        if not trabalho:

            return jsonify({
                "erro": "Trabalho não encontrado."
            }), 404

        voto_atual = conn.execute("""
            SELECT trabalho_id
            FROM votos
            WHERE participante_id = ?
        """, (participante_id,)).fetchone()

        antigo = (
            voto_atual["trabalho_id"]
            if voto_atual
            else None
        )

        if antigo == trabalho_id:

            return jsonify({
                "sucesso": True,
                "mensagem": "Seu voto já está neste trabalho."
            })

        momento = agora()

        if voto_atual:

            conn.execute("""
                UPDATE votos
                SET
                    trabalho_id = ?,
                    atualizado_em = ?
                WHERE participante_id = ?
            """, (
                trabalho_id,
                momento,
                participante_id
            ))

        else:

            conn.execute("""
                INSERT INTO votos (
                    participante_id,
                    trabalho_id,
                    criado_em,
                    atualizado_em
                )
                VALUES (?, ?, ?, ?)
            """, (
                participante_id,
                trabalho_id,
                momento,
                momento
            ))

        conn.execute("""
            INSERT INTO historico_votos (
                participante_id,
                trabalho_anterior_id,
                trabalho_novo_id,
                criado_em
            )
            VALUES (?, ?, ?, ?)
        """, (
            participante_id,
            antigo,
            trabalho_id,
            momento
        ))

        conn.commit()

    except Exception:

        conn.rollback()

        return jsonify({
            "erro": "Não foi possível registrar o voto."
        }), 500

    finally:
        conn.close()

    return jsonify({
        "sucesso": True,
        "mensagem": "Voto registrado com sucesso.",
        "trabalho_id": trabalho_id
    })


# ============================================================
# RANKING
# ============================================================
@app.get("/api/ranking")
def obter_ranking():

    conn = get_db()

    ranking = conn.execute("""
        SELECT
            t.id,
            t.codigo,
            t.titulo,

            (
                SELECT GROUP_CONCAT(nome, ', ')
                FROM (
                    SELECT a.nome
                    FROM trabalho_autores ta2
                    JOIN autores a
                        ON a.id = ta2.autor_id
                    WHERE ta2.trabalho_id = t.id
                    ORDER BY a.nome
                )
            ) AS autores,

            (
                SELECT COUNT(*)
                FROM votos v2
                WHERE v2.trabalho_id = t.id
            ) AS votos

        FROM trabalhos t

        WHERE t.ativo = 1

        ORDER BY
            votos DESC,
            t.codigo ASC
    """).fetchall()

    total = conn.execute("""
        SELECT COUNT(*)
        FROM votos
    """).fetchone()[0]

    conn.close()

    resultado = []

    for posicao, trabalho in enumerate(
        ranking,
        start=1
    ):

        resultado.append({
            "posicao": posicao,
            "id": trabalho["id"],
            "codigo": trabalho["codigo"],
            "titulo": trabalho["titulo"],
            "autores": trabalho["autores"] or "",
            "votos": trabalho["votos"]
        })

    return jsonify({
        "total_votos": total,
        "trabalhos": resultado,
        "atualizado_em": agora()
    })
    
# ============================================================
# STATUS
# ============================================================

@app.get("/api/status")
def status():

    return jsonify({
        "votacao_aberta": votacao_aberta(),
        "autenticado": participante_logado() is not None
    })


# ============================================================
# ADMIN
# ============================================================

@app.post("/api/admin/login")
def admin_login():

    data = request.get_json(silent=True) or {}

    senha = data.get(
        "senha",
        ""
    )

    if senha != ADMIN_PASSWORD:

        return jsonify({
            "erro": "Senha incorreta."
        }), 401

    session["admin"] = True

    return jsonify({
        "sucesso": True
    })


@app.post("/api/admin/votacao")
def alterar_votacao():

    if not session.get("admin"):
        return jsonify({
            "erro": "Não autorizado."
        }), 401

    data = request.get_json(silent=True) or {}

    aberta = bool(
        data.get("aberta")
    )

    conn = get_db()

    conn.execute("""
        UPDATE configuracoes
        SET valor = ?
        WHERE chave = 'votacao_aberta'
    """, (
        "1" if aberta else "0",
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "sucesso": True,
        "votacao_aberta": aberta
    })


@app.get("/api/admin/estatisticas")
def estatisticas():

    if not session.get("admin"):
        return jsonify({
            "erro": "Não autorizado."
        }), 401

    conn = get_db()

    participantes = conn.execute("""
        SELECT COUNT(*)
        FROM participantes
        WHERE ativo = 1
    """).fetchone()[0]

    trabalhos = conn.execute("""
        SELECT COUNT(*)
        FROM trabalhos
        WHERE ativo = 1
    """).fetchone()[0]

    votos = conn.execute("""
        SELECT COUNT(*)
        FROM votos
    """).fetchone()[0]

    conn.close()

    return jsonify({
        "participantes": participantes,
        "trabalhos": trabalhos,
        "votos": votos,
        "votacao_aberta": votacao_aberta()
    })


# ============================================================
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
