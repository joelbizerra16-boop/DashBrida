from __future__ import annotations

from sqlalchemy import text

from utils.db import build_database_url, get_engine, test_database_connection


def main() -> None:
    print("[test_db] DATABASE_URL:", build_database_url())
    engine = get_engine()
    test_database_connection(engine=engine, attempts=2, delay_seconds=1.0)

    with engine.connect() as connection:
        value = connection.execute(text("SELECT 1")).scalar_one()

    print("[test_db] SELECT 1 =>", value)
    print("[test_db] Conexao OK")


if __name__ == "__main__":
    main()