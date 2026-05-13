import sqlite3
from collections.abc import Generator
from pathlib import Path

from pj_stock_backend.core.config import settings


def get_database_path() -> Path:
    database_url = settings.database_url

    if not database_url.startswith("sqlite:///"):
        msg = f"Only sqlite database URLs are supported: {database_url}"
        raise ValueError(msg)

    return Path(database_url.removeprefix("sqlite:///"))


def get_connection() -> sqlite3.Connection:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row

    return connection


def get_db() -> Generator[sqlite3.Connection]:
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()

def initialize_database() -> None:
    schema_path = Path(__file__).parent / "schema" / "schema.sql"

    with get_connection() as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.commit()
