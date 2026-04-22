from __future__ import annotations

import os
import re
import time
from typing import Any
from urllib.parse import quote_plus

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_DB_SCHEMA = "public"
DATABASE_URL_KEYS = (
    "DATABASE_URL",
    "SUPABASE_DB_URL",
    "SUPABASE_DATABASE_URL",
)
POSTGRESQL_SCHEME_REPLACEMENTS = (
    ("postgresql+psycopg://", "postgresql+psycopg://"),
    ("postgresql://", "postgresql+psycopg://"),
    ("postgres://", "postgresql+psycopg://"),
)
DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_STATEMENT_TIMEOUT_MS = 15000


def _get_database_url_from_secrets() -> str | None:
    try:
        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"])
    except Exception:
        return None

    return None


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


def normalize_database_url(database_url: str) -> str:
    normalized = str(database_url).strip()
    for prefix, replacement in POSTGRESQL_SCHEME_REPLACEMENTS:
        if normalized.startswith(prefix):
            return normalized.replace(prefix, replacement, 1)
    return normalized


def log_database_event(message: str) -> None:
    print(f"[db] {message}")


def build_database_url() -> str:
    direct_url = _get_database_url_from_secrets() or _get_secret_value(*DATABASE_URL_KEYS)
    if direct_url:
        return normalize_database_url(str(direct_url))

    host = _get_secret_value("SUPABASE_HOST", "POSTGRES_HOST", "DB_HOST")
    port = _get_secret_value("SUPABASE_PORT", "POSTGRES_PORT", "DB_PORT") or "5432"
    database = _get_secret_value("SUPABASE_DB_NAME", "POSTGRES_DB", "DB_NAME")
    user = _get_secret_value("SUPABASE_USER", "POSTGRES_USER", "DB_USER")
    password = _get_secret_value("SUPABASE_PASSWORD", "POSTGRES_PASSWORD", "DB_PASSWORD")
    sslmode = _get_secret_value("SUPABASE_SSLMODE", "POSTGRES_SSLMODE", "DB_SSLMODE") or "require"

    if not all((host, database, user, password)):
        raise RuntimeError(
            "Configure DATABASE_URL ou as credenciais do PostgreSQL/Supabase em variaveis de ambiente ou .streamlit/secrets.toml."
        )

    encoded_user = quote_plus(str(user))
    encoded_password = quote_plus(str(password))
    return normalize_database_url(
        f"postgresql+psycopg://{encoded_user}:{encoded_password}@{host}:{port}/{database}?sslmode={sslmode}"
    )


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
    log_database_event(f"creating engine for {database_url.split('@')[-1]}")
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=10,
        connect_args=_build_connect_args(),
        future=True,
    )


def get_database_engine() -> Engine:
    return get_engine()


def test_database_connection(engine: Engine | None = None, attempts: int = 2, delay_seconds: float = 1.0) -> None:
    last_error: Exception | None = None
    active_engine = engine or get_engine()

    for attempt in range(1, attempts + 1):
        try:
            log_database_event(f"connection test attempt {attempt}/{attempts}")
            with active_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            log_database_event("connection test succeeded")
            return
        except Exception as exc:
            last_error = exc
            log_database_event(f"connection test failed: {exc}")
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