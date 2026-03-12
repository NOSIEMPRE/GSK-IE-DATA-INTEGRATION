"""
Load Synthea OMOP 1k CSVs into a local DuckDB database for analysis.

Usage (from project root):
    python 01-initial-notebook/load_synthea_duckdb.py

Prerequisites:
    pip install duckdb
    bash 01-initial-notebook/download_synthea_omop.sh
"""

import pathlib

import duckdb


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "synthea1k"
DB_PATH = PROJECT_ROOT / "data" / "synthea1k.duckdb"

# Core OMOP clinical event tables we typically need first
TABLES = [
    "person",
    "visit_occurrence",
    "condition_occurrence",
    "drug_exposure",
    "measurement",
    "observation",
    "procedure_occurrence",
    "condition_era",
    "drug_era",
    "observation_period",
]


def main() -> None:
    if not DATA_DIR.exists():
        raise SystemExit(
            f"Data folder not found: {DATA_DIR}\n"
            "Run the download script first:\n"
            "  bash 01-initial-notebook/download_synthea_omop.sh"
        )

    con = duckdb.connect(DB_PATH.as_posix())

    for table in TABLES:
        csv_path = DATA_DIR / f"{table}.csv"
        if not csv_path.exists():
            print(f"[skip] {csv_path} not found")
            continue

        print(f"[load] {table} <- {csv_path.name}")
        # Let DuckDB auto-detect schema from the CSV
        con.execute(
            f"""
            CREATE OR REPLACE TABLE {table} AS
            SELECT * FROM read_csv_auto('{csv_path.as_posix()}');
            """
        )

    # Simple sanity check
    try:
        count = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]
        print(f"[ok] Loaded person table with {count} rows")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Could not query person table: {exc}")

    con.close()
    print(f"DuckDB database written to: {DB_PATH}")


if __name__ == "__main__":
    main()
