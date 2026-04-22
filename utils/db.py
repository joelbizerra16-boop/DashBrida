from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_DB_SCHEMA = "public"
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

logger = logging.getLogger("logbrida.db")
DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_STATEMENT_TIMEOUT_MS = 15000


def _get_secret_value(*keys: str) -> Any | None:
    for key in keys:
        env_value = os.getenv(key)
        if env_value:
            return env_value

    try:
        for key in keys:
            if key in st.secrets:
                return st.secrets[key]
    except Exception:
        return None

    return None


def log_database_event(message: str) -> None:
    logger.info(message)


def mask_url(url: str) -> str:
    try:
        return make_url(url).render_as_string(hide_password=True)
    except Exception:
        return "<DATABASE_URL invalido>"


def get_database_username(url: str) -> str:
    try:
        return make_url(url).username or "<desconhecido>"
    except Exception:
        return "<desconhecido>"


def build_database_url() -> str:
    return "postgresql+psycopg://postgres.zkixmtuezifuvmyfcvmv:Supabase%23Joel_2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"


def get_database_schema() -> str:
    schema = _get_secret_value("DB_SCHEMA", "POSTGRES_SCHEMA", "SUPABASE_SCHEMA")
    return str(schema or DEFAULT_DB_SCHEMA)


def _build_connect_args() -> dict[str, Any]:
    connect_timeout = int(_get_secret_value("DB_CONNECT_TIMEOUT", "PGCONNECT_TIMEOUT") or DEFAULT_CONNECT_TIMEOUT)
    statement_timeout_ms = int(
        _get_secret_value("DB_STATEMENT_TIMEOUT_MS", "PG_STATEMENT_TIMEOUT_MS")
        or DEFAULT_STATEMENT_TIMEOUT_MS
    )
    return {
        "connect_timeout": connect_timeout,
        "options": f"-c statement_timeout={statement_timeout_ms}",
    }


@st.cache_resource
def get_engine() -> Engine:
    database_url = build_database_url()
    logger.info("Inicializando conexao com banco")
    logger.debug("DATABASE_URL carregada com sucesso: %s", mask_url(database_url))
    logger.info("Usuario do banco: %s", get_database_username(database_url))
    return create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )


def get_database_engine() -> Engine:
    return get_engine()


def test_database_connection(engine: Engine | None = None, attempts: int = 2, delay_seconds: float = 1.0) -> None:
    last_error: Exception | None = None
    active_engine = engine or get_engine()

    for attempt in range(1, attempts + 1):
        try:
            logger.info("Teste de conexao com banco %s/%s", attempt, attempts)
            with active_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Conexao com banco validada com sucesso")
            return
        except Exception as exc:
            last_error = exc
            logger.error("Erro ao conectar ao banco", exc_info=True)
            if attempt < attempts:
                time.sleep(delay_seconds)

    raise RuntimeError(f"Falha ao conectar ao PostgreSQL/Supabase: {last_error}") from last_error


def validate_identifier(identifier: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError(f"Identificador SQL invalido: {identifier}")
    return identifier


def qualify_table_name(table_name: str, schema: str | None = None) -> str:
    safe_table = validate_identifier(table_name)
    target_schema = validate_identifier(schema or get_database_schema())
    return f'"{target_schema}"."{safe_table}"'