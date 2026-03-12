"""
PPRL Multi-Source Integration Demo.

Simulates two data sources (EHR + Lab) from Synthea OMOP, runs privacy-preserving
record linkage (Option B: deterministic hash), and outputs a linkage map.

Aligns with GSK Challenge: "Enable privacy-preserving patient-level linkage across data sources"

Usage (from project root):
    python 02-data-sampling-feature/pprl_multi_source_demo.py

Prerequisites:
    - data/synthea1k.duckdb (from load_synthea_duckdb.py)
"""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "synthea1k.duckdb"
OUTPUT_DIR = PROJECT_ROOT / "data" / "pprl"
LINKAGE_SALT = b"rwd-trustchain-pprl-demo-2026"  # In production: from secrets manager


def make_linkage_key(year_of_birth: int, month_of_birth: int | float | None, gender_concept_id: int) -> str:
    """Generate privacy-preserving linkage key (no PHI). Option B: deterministic hash."""
    month = 0
    if month_of_birth is not None and not (isinstance(month_of_birth, float) and math.isnan(month_of_birth)):
        month = int(month_of_birth)
    payload = f"{year_of_birth}|{month}|{gender_concept_id}".encode()
    return hashlib.sha256(LINKAGE_SALT + payload).hexdigest()


def run_pprl_demo(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Simulate two sources from Synthea person table and run PPRL.
    Source A (EHR): first half of persons with source_a_id
    Source B (Lab): same persons with source_b_id (simulates Lab system with different IDs)
    """
    persons = con.execute("""
        SELECT person_id, year_of_birth, month_of_birth, gender_concept_id
        FROM person
        WHERE year_of_birth IS NOT NULL AND gender_concept_id IS NOT NULL
    """).fetchdf()

    if len(persons) < 10:
        raise SystemExit("Not enough person records for PPRL demo")

    # Simulate Source A (EHR) and Source B (Lab) - same persons, different source IDs
    n = min(500, len(persons) // 2)  # Use up to 500 persons for demo
    source_a = persons.head(n).copy()
    source_b = persons.head(n).copy()

    source_a["source_system"] = "EHR"
    source_a["source_person_id"] = ["EHR_" + str(pid) for pid in source_a["person_id"]]
    source_b["source_system"] = "Lab"
    source_b["source_person_id"] = ["LAB_" + str(pid) for pid in source_b["person_id"]]

    # Generate linkage keys (no PHI leaves)
    source_a["linkage_key"] = source_a.apply(
        lambda r: make_linkage_key(
            int(r["year_of_birth"]),
            int(r["month_of_birth"]) if r["month_of_birth"] is not None else None,
            int(r["gender_concept_id"]),
        ),
        axis=1,
    )
    source_b["linkage_key"] = source_b.apply(
        lambda r: make_linkage_key(
            int(r["year_of_birth"]),
            int(r["month_of_birth"]) if r["month_of_birth"] is not None else None,
            int(r["gender_concept_id"]),
        ),
        axis=1,
    )

    # Match by linkage_key -> build linkage map
    key_to_person = dict(zip(source_a["linkage_key"], source_a["person_id"]))
    mappings = []
    for _, row in source_b.iterrows():
        lk = row["linkage_key"]
        person_id = key_to_person.get(lk)
        if person_id is not None:
            mappings.append({
                "source_system": "Lab",
                "source_person_id": row["source_person_id"],
                "person_id": int(person_id),
            })
    for _, row in source_a.iterrows():
        mappings.append({
            "source_system": "EHR",
            "source_person_id": row["source_person_id"],
            "person_id": int(row["person_id"]),
        })

    # Metrics
    unique_persons = len(set(m["person_id"] for m in mappings))
    return {
        "linkage_run_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "method": "deterministic_hash",
        "sources": ["EHR", "Lab"],
        "mappings": mappings,
        "metrics": {
            "source_a_records": len(source_a),
            "source_b_records": len(source_b),
            "total_mappings": len(mappings),
            "unique_persons_linked": unique_persons,
            "linkage_key_attributes": ["year_of_birth", "month_of_birth", "gender_concept_id"],
        },
    }


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            f"DuckDB not found: {DB_PATH}\n"
            "Run: python 01-initial-notebook/load_synthea_duckdb.py"
        )

    con = duckdb.connect(DB_PATH.as_posix())
    result = run_pprl_demo(con)
    con.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"linkage_map_{result['linkage_run_id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    m = result["metrics"]
    print(f"PPRL linkage map written to: {out_path}")
    print(f"  Source A (EHR): {m['source_a_records']} records")
    print(f"  Source B (Lab): {m['source_b_records']} records")
    print(f"  Mappings: {m['total_mappings']} | Unique persons: {m['unique_persons_linked']}")


if __name__ == "__main__":
    main()
