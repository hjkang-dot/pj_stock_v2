from pathlib import Path

from pj_stock_backend.db.sqlite import get_connection, get_database_path


def test_get_database_path() -> None:
    database_path = get_database_path()

    assert database_path == Path("../data/app.db")



def test_get_connection_creates_sqlite_connection() -> None:
    connection = get_connection()

    try:
        cursor = connection.execute("select 1 as value")
        row = cursor.fetchone()

        assert row["value"] == 1
    finally:
        connection.close()
