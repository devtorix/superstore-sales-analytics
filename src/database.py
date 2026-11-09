"""
Database Module for SuperStore Sales Analytics
================================================

Handles creating a SQLite database from the cleaned dataset and
executing analytical SQL queries.

Why SQLite?
    - Zero installation — comes bundled with Python.
    - Single portable file — easy to share and version control.
    - Perfect for single-user analytics projects and portfolios.
    - For production multi-user systems, PostgreSQL would be preferred.
"""

import sqlite3
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
DB_PATH = PROJECT_ROOT / "data" / "superstore.db"
SQL_DIR = PROJECT_ROOT / "sql"


# ---------------------------------------------------------------------------
# Database creation
# ---------------------------------------------------------------------------

def create_database(csv_path: Path = PROCESSED_DATA_PATH,
                    db_path: Path = DB_PATH) -> None:
    """Create a SQLite database from the cleaned CSV.

    Drops and recreates the 'orders' table each time to ensure
    the database reflects the latest cleaned data.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {csv_path}. "
            "Run src/data_cleaning.py first."
        )

    df = pd.read_csv(csv_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        df.to_sql("orders", conn, if_exists="replace", index=False)
        row_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        print(f"✅ Database created at: {db_path}")
        print(f"   Table 'orders': {row_count:,} rows, {len(df.columns)} columns")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

def execute_query(query: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Execute a SQL query and return results as a DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql_query(query, conn)
        return result
    finally:
        conn.close()


def run_query_file(file_path: Path, db_path: Path = DB_PATH) -> list:
    """Execute all queries in a SQL file, splitting on semicolons.

    Returns a list of (query_comment, DataFrame) tuples.
    """
    sql_text = file_path.read_text(encoding="utf-8")
    # Split on semicolons, skip empty
    queries = [q.strip() for q in sql_text.split(";") if q.strip()]

    results = []
    for query in queries:
        # Extract leading comment as title
        lines = query.strip().split("\n")
        title = ""
        for line in lines:
            if line.strip().startswith("--"):
                title = line.strip().lstrip("- ").strip()
                break
        if not title:
            title = query[:60] + "..."

        try:
            df = execute_query(query, db_path)
            results.append((title, df))
        except Exception as e:
            results.append((title, f"ERROR: {e}"))

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🗄️  CREATING SUPERSTORE DATABASE")
    print("=" * 50)
    create_database()

    # Run analysis queries if the file exists
    queries_file = SQL_DIR / "analysis_queries.sql"
    if queries_file.exists():
        print(f"\n📊 Running analysis queries from {queries_file.name}...")
        results = run_query_file(queries_file)
        for title, result in results:
            print(f"\n--- {title} ---")
            if isinstance(result, pd.DataFrame):
                print(result.to_string(index=False))
            else:
                print(result)
    else:
        print(f"\nℹ️  No query file found at {queries_file}")
