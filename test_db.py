from __future__ import annotations

import logging

from sqlalchemy import text

from utils.db import build_database_url, get_engine, test_database_connection

logger = logging.getLogger("logbrida.test_db")


def main() -> None:
    logger.info("Iniciando teste isolado de conexao com banco")
    engine = get_engine()
    test_database_connection(engine=engine, attempts=2, delay_seconds=1.0)

    with engine.connect() as connection:
        value = connection.execute(text("SELECT 1")).scalar_one()

    logger.info("SELECT 1 => %s", value)
    logger.info("Conexao OK")


if __name__ == "__main__":
    main()