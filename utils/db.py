from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import quote_plus

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DEFAULT_DB_SCHEMA = "public"
DATABASE_URL_KEYS = (
    "DATABASE_URL",
    "SUPABASE_DB_URL",
    "SUPABASE_DATABASE_URL",
)


def _get_database_url_from_secrets() -> str | None:
    try:
        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"])

        if "database" in st.secrets and "DATABASE_URL" in st.secrets["database"]:
            return str(st.secrets["database"]["DATABASE_URL"])
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

        for section_name in ("database", "db", "supabase"):
            if section_name not in st.secrets:
                continue
            section = st.secrets[section_name]
            for key in keys:
                if key in section:
                    return section[key]
    except Exception:
        return None

    return None


def build_database_url() -> str:
    direct_url = _get_database_url_from_secrets() or _get_secret_value(*DATABASE_URL_KEYS)
    if direct_url:
        return str(direct_url)

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
    return f"postgresql+psycopg://{encoded_user}:{encoded_password}@{host}:{port}/{database}?sslmode={sslmode}"


def get_database_schema() -> str:
    schema = _get_secret_value("DB_SCHEMA", "POSTGRES_SCHEMA", "SUPABASE_SCHEMA")
    return str(schema or DEFAULT_DB_SCHEMA)


@st.cache_resource
def get_engine() -> Engine:
    return create_engine(
        build_database_url(),
        pool_pre_ping=True,
        pool_recycle=300,
        future=True,
    )


def get_database_engine() -> Engine:
    return get_engine()


def validate_identifier(identifier: str) -> str:
    if not IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError(f"Identificador SQL invalido: {identifier}")
    return identifier


def qualify_table_name(table_name: str, schema: str | None = None) -> str:
    safe_table = validate_identifier(table_name)
    target_schema = validate_identifier(schema or get_database_schema())
    return f'"{target_schema}"."{safe_table}"'