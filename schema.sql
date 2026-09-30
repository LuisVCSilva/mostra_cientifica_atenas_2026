PRAGMA foreign_keys = ON;

-- ============================================================
-- PARTICIPANTES
-- ============================================================

CREATE TABLE IF NOT EXISTS participantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    ativo INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- TRABALHOS
-- ============================================================

CREATE TABLE IF NOT EXISTS trabalhos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    resumo TEXT,
    ativo INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- AUTORES
-- ============================================================

CREATE TABLE IF NOT EXISTS autores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trabalho_autores (
    trabalho_id INTEGER NOT NULL,
    autor_id INTEGER NOT NULL,

    PRIMARY KEY (trabalho_id, autor_id),

    FOREIGN KEY (trabalho_id)
        REFERENCES trabalhos(id)
        ON DELETE CASCADE,

    FOREIGN KEY (autor_id)
        REFERENCES autores(id)
        ON DELETE CASCADE
);

-- ============================================================
-- VOTOS ATUAIS
-- Um participante possui no máximo um voto ativo.
-- ============================================================

CREATE TABLE IF NOT EXISTS votos (
    participante_id INTEGER PRIMARY KEY,
    trabalho_id INTEGER NOT NULL,

    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,

    FOREIGN KEY (participante_id)
        REFERENCES participantes(id)
        ON DELETE CASCADE,

    FOREIGN KEY (trabalho_id)
        REFERENCES trabalhos(id)
        ON DELETE CASCADE
);

-- ============================================================
-- HISTÓRICO DOS VOTOS
-- Permite saber quando um participante mudou de trabalho.
-- ============================================================

CREATE TABLE IF NOT EXISTS historico_votos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    participante_id INTEGER NOT NULL,

    trabalho_anterior_id INTEGER,

    trabalho_novo_id INTEGER NOT NULL,

    criado_em TEXT NOT NULL,

    FOREIGN KEY (participante_id)
        REFERENCES participantes(id),

    FOREIGN KEY (trabalho_anterior_id)
        REFERENCES trabalhos(id),

    FOREIGN KEY (trabalho_novo_id)
        REFERENCES trabalhos(id)
);

-- ============================================================
-- CÓDIGOS DE ACESSO POR E-MAIL
-- ============================================================

CREATE TABLE IF NOT EXISTS codigos_acesso (
    email TEXT PRIMARY KEY,

    codigo_hash TEXT NOT NULL,

    expira_em TEXT NOT NULL
);

-- ============================================================
-- CONFIGURAÇÕES
-- ============================================================

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,

    valor TEXT NOT NULL
);

INSERT OR IGNORE INTO configuracoes (
    chave,
    valor
)
VALUES (
    'votacao_aberta',
    '1'
);
