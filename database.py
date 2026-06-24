"""
database.py - Módulo responsável pela conexão e manipulação do banco de dados SQLite.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "agendamentos.db")


def inicializar_banco() -> None:
    """
    Cria o banco de dados e a tabela 'agendamentos' caso ainda não existam.
    Também aplica migrações seguras (ADD COLUMN) se a tabela já existir.
    Deve ser chamada uma única vez na inicialização do bot.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_paciente    TEXT    NOT NULL,
                especialidade    TEXT    NOT NULL,
                data_hora        TEXT    NOT NULL,
                google_event_id  TEXT,
                criado_em        TEXT    NOT NULL
            )
        """)
        # Migração segura: adiciona coluna google_event_id caso a tabela
        # já exista de uma versão anterior sem ela.
        try:
            cursor.execute("ALTER TABLE agendamentos ADD COLUMN google_event_id TEXT")
        except sqlite3.OperationalError:
            pass  # Coluna já existe — ignoramos o erro

        conn.commit()
    print("[DB] Banco de dados inicializado com sucesso.")


def inserir_agendamento(
    nome_paciente: str,
    especialidade: str,
    data_hora: str,
    google_event_id: str | None = None,
) -> int:
    """
    Insere um novo agendamento na tabela e retorna o ID gerado.

    Args:
        nome_paciente:   Nome completo do paciente.
        especialidade:   Especialidade da consulta.
        data_hora:       Data e hora no formato ISO 8601.
        google_event_id: ID do evento criado no Google Calendar (opcional).

    Returns:
        ID do registro inserido.
    """
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO agendamentos
                (nome_paciente, especialidade, data_hora, google_event_id, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nome_paciente, especialidade, data_hora, google_event_id, criado_em),
        )
        conn.commit()
        return cursor.lastrowid


def buscar_agendamento_por_id(agendamento_id: int) -> dict | None:
    """
    Retorna um agendamento pelo seu ID, ou None se não encontrado.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agendamentos WHERE id = ?", (agendamento_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def buscar_agendamentos_por_nome(nome_paciente: str) -> list[dict]:
    """
    Busca agendamentos pelo nome do paciente (busca parcial, case-insensitive).

    Args:
        nome_paciente: Nome completo ou parcial do paciente.

    Returns:
        Lista de dicionários com os agendamentos encontrados, ordenados por data.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM agendamentos
            WHERE LOWER(nome_paciente) LIKE LOWER(?)
            ORDER BY data_hora ASC
            """,
            (f"%{nome_paciente}%",),
        )
        return [dict(row) for row in cursor.fetchall()]


def deletar_agendamento(agendamento_id: int) -> bool:
    """
    Remove um agendamento pelo ID.

    Returns:
        True se alguma linha foi afetada, False caso contrário.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agendamentos WHERE id = ?", (agendamento_id,))
        conn.commit()
        return cursor.rowcount > 0


def listar_agendamentos() -> list[dict]:
    """
    Retorna todos os agendamentos cadastrados no banco de dados.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agendamentos ORDER BY data_hora ASC")
        return [dict(row) for row in cursor.fetchall()]
