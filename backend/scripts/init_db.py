from pj_stock_backend.db.sqlite import get_database_path, initialize_database


def main() -> None:
    initialize_database()
    database_path = get_database_path()

    print(f"Initialized database: {database_path}")


if __name__ == "__main__":
    main()
