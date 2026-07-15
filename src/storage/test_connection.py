"""
test_connection.py — run this after setting DATABASE_URL and running
`alembic upgrade head`, to confirm the connection works and every table
from the schema exists.

Usage:
    python src/storage/test_connection.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "config"))

from sqlalchemy import inspect
from db import get_engine
from models import Base


def main():
    engine = get_engine()
    print(f"Connecting to database...")
    with engine.connect() as conn:
        print("Connection successful.")

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = set(Base.metadata.tables.keys())

    print(f"\nExpected tables: {sorted(expected_tables)}")
    print(f"Found tables:    {sorted(existing_tables)}")

    missing = expected_tables - existing_tables
    if missing:
        print(f"\nMISSING TABLES: {missing}")
        print("Run: alembic upgrade head")
        sys.exit(1)
    else:
        print("\nAll expected tables are present. Phase 1 storage layer is ready.")


if __name__ == "__main__":
    main()
