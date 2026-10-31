import os
from pathlib import Path

import psycopg2
import pytest
from dotenv import load_dotenv
from psycopg2 import sql

load_dotenv()

TEST_DB = "premier_league_test"
SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "001_create_raw_tables.sql"


def connect(dbname):
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=dbname,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


@pytest.fixture
def conn():
    """Create an isolated test database and remove it after the test."""
    admin_db = os.getenv("POSTGRES_DB")
    if not admin_db:
        pytest.fail("POSTGRES_DB must be set to create the isolated test database.")
    if TEST_DB == admin_db:
        pytest.fail("POSTGRES_DB must not be the test database.")

    admin = connect(admin_db)
    admin.autocommit = True
    test_identifier = sql.Identifier(TEST_DB)
    test_conn = None
    try:
        with admin.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(test_identifier))
            cur.execute(sql.SQL("CREATE DATABASE {}").format(test_identifier))

        test_conn = connect(TEST_DB)
        with test_conn.cursor() as cur:
            cur.execute(SQL_FILE.read_text(encoding="utf-8"))
        test_conn.commit()

        yield test_conn
    finally:
        if test_conn is not None:
            test_conn.close()
        with admin.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(test_identifier))
        admin.close()
