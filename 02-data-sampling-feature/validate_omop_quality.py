"""
OMOP CDM data quality validation script.

Runs completeness, consistency, time-logic checks, and AI-based anomaly detection
(Isolation Forest on measurement values). Outputs a JSON report for downstream
hash anchoring and audit trail.

Usage (from project root):
    python 02-data-sampling-feature/validate_omop_quality.py

Prerequisites:
    - DuckDB database at data/synthea1k.duckdb (run 01-initial-notebook/load_synthea_duckdb.py first)
    - scikit-learn (pip install scikit-learn)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

import pandas as pd

try:
    import numpy as np
    from sklearn.ensemble import IsolationForest

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "synthea1k.duckdb"
REPORT_DIR = PROJECT_ROOT / "data" / "quality_reports"


# Required fields per table (OMOP CDM core)
REQUIRED_FIELDS = {
    "person": ["person_id", "gender_concept_id", "year_of_birth"],
    "visit_occurrence": ["visit_occurrence_id", "person_id", "visit_concept_id", "visit_start_date"],
    "condition_occurrence": [
        "condition_occurrence_id",
        "person_id",
        "condition_concept_id",
        "condition_start_date",
    ],
    "drug_exposure": [
        "drug_exposure_id",
        "person_id",
        "drug_concept_id",
        "drug_exposure_start_date",
    ],
    "measurement": [
        "measurement_id",
        "person_id",
        "measurement_concept_id",
        "measurement_date",
    ],
    "observation": ["observation_id", "person_id", "observation_concept_id", "observation_date"],
    "procedure_occurrence": [
        "procedure_occurrence_id",
        "person_id",
        "procedure_concept_id",
        "procedure_date",
    ],
    "observation_period": [
        "observation_period_id",
        "person_id",
        "observation_period_start_date",
        "observation_period_end_date",
    ],
}

# Time logic: (table, start_col, end_col)
TIME_LOGIC = [
    ("condition_occurrence", "condition_start_date", "condition_end_date"),
    ("drug_exposure", "drug_exposure_start_date", "drug_exposure_end_date"),
    ("visit_occurrence", "visit_start_date", "visit_end_date"),
    ("observation_period", "observation_period_start_date", "observation_period_end_date"),
]


def run_checks(con: duckdb.DuckDBPyConnection) -> dict:
    """Run all validation checks and return a structured report."""
    report = {
        "run_id": datetime.now(timezone.utc).isoformat(),
        "database": str(DB_PATH),
        "checks": {},
        "summary": {"passed": 0, "failed": 0, "warnings": 0},
    }

    tables = con.execute(
        "SELECT table_name FROM duckdb_tables() WHERE schema_name = 'main' ORDER BY table_name"
    ).fetchall()
    tables = [t[0] for t in tables]

    # 1. Table existence & row counts
    for table in tables:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            report["checks"][table] = {"row_count": count, "required_fields": {}, "time_logic": {}}
        except Exception as e:
            report["checks"][table] = {"error": str(e)}
            report["summary"]["failed"] += 1
            continue

    # 2. Required field completeness (non-null)
    for table, fields in REQUIRED_FIELDS.items():
        if table not in tables:
            continue
        if "error" in report["checks"].get(table, {}):
            continue

        for col in fields:
            try:
                null_count = con.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"
                ).fetchone()[0]
                total = report["checks"][table]["row_count"]
                pct_null = (null_count / total * 100) if total > 0 else 0
                report["checks"][table]["required_fields"][col] = {
                    "null_count": null_count,
                    "null_pct": round(pct_null, 2),
                    "passed": null_count == 0,
                }
                if null_count > 0:
                    report["summary"]["warnings"] += 1
                else:
                    report["summary"]["passed"] += 1
            except Exception as e:
                report["checks"][table]["required_fields"][col] = {"error": str(e)}
                report["summary"]["failed"] += 1

    # 3. Time logic (start <= end)
    for table, start_col, end_col in TIME_LOGIC:
        if table not in tables:
            continue
        if "error" in report["checks"].get(table, {}):
            continue

        try:
            invalid = con.execute(
                f"""
                SELECT COUNT(*) FROM {table}
                WHERE {end_col} IS NOT NULL AND {start_col} IS NOT NULL
                  AND {end_col} < {start_col}
                """
            ).fetchone()[0]
            total = report["checks"][table]["row_count"]
            report["checks"][table]["time_logic"] = {
                "invalid_count": invalid,
                "rule": f"{start_col} <= {end_col}",
                "passed": invalid == 0,
            }
            if invalid > 0:
                report["summary"]["warnings"] += 1
            else:
                report["summary"]["passed"] += 1
        except Exception as e:
            report["checks"][table]["time_logic"] = {"error": str(e)}
            report["summary"]["failed"] += 1

    # 4. Referential integrity: person_id in clinical tables exists in person
    for table in ["visit_occurrence", "condition_occurrence", "drug_exposure", "measurement"]:
        if table not in tables or "error" in report["checks"].get(table, {}):
            continue

        try:
            orphan = con.execute(
                f"""
                SELECT COUNT(*) FROM {table} t
                WHERE NOT EXISTS (SELECT 1 FROM person p WHERE p.person_id = t.person_id)
                """
            ).fetchone()[0]
            report["checks"][table]["referential_integrity"] = {
                "orphan_person_ids": orphan,
                "passed": orphan == 0,
            }
            if orphan > 0:
                report["summary"]["warnings"] += 1
            else:
                report["summary"]["passed"] += 1
        except Exception as e:
            report["checks"][table]["referential_integrity"] = {"error": str(e)}
            report["summary"]["failed"] += 1

    # 5. AI anomaly detection (Isolation Forest on measurement.value_as_number)
    report["ai_validation"] = run_ai_anomaly_detection(con, tables)

    return report


def run_ai_anomaly_detection(con: duckdb.DuckDBPyConnection, tables: list) -> dict:
    """Run Isolation Forest on numeric clinical values to flag outliers."""
    result = {
        "module": "Isolation Forest",
        "target": None,
        "status": "skipped",
        "anomaly_count": None,
        "total_analyzed": None,
        "contamination": 0.01,
        "sample_anomaly_ids": [],
    }

    if not SKLEARN_AVAILABLE:
        result["status"] = "skipped"
        result["reason"] = "scikit-learn not installed"
        return result

    # Prefer measurement.value_as_number; fallback to drug_exposure.quantity
    for target_table, id_col, value_col in [
        ("measurement", "measurement_id", "value_as_number"),
        ("drug_exposure", "drug_exposure_id", "quantity"),
    ]:
        if target_table not in tables:
            continue

        try:
            df = con.execute(
                f"""
                SELECT {id_col}, {value_col}
                FROM {target_table}
                WHERE {value_col} IS NOT NULL
                """
            ).fetchdf()

            df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
            df = df.dropna(subset=[value_col])

            if len(df) < 10:
                continue

            result["target"] = f"{target_table}.{value_col}"

            X = df[value_col].values.reshape(-1, 1).astype(np.float64)
            clf = IsolationForest(contamination=0.01, random_state=42)
            pred = clf.fit_predict(X)
            anomaly_mask = pred == -1
            anomaly_count = int(anomaly_mask.sum())

            result["status"] = "completed"
            result["total_analyzed"] = len(df)
            result["anomaly_count"] = anomaly_count
            result["anomaly_pct"] = round(anomaly_count / len(df) * 100, 2)
            result["passed"] = anomaly_count <= int(len(df) * 0.05)

            if anomaly_count > 0:
                anomaly_ids = df.loc[anomaly_mask, id_col].tolist()
                result["sample_anomaly_ids"] = [int(x) for x in anomaly_ids[:10]]

            return result

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            return result

    result["status"] = "skipped"
    result["reason"] = "no numeric columns with sufficient data"

    return result


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            f"DuckDB database not found: {DB_PATH}\n"
            "Run load_synthea_duckdb.py first:\n"
            "  python 01-initial-notebook/load_synthea_duckdb.py"
        )

    con = duckdb.connect(DB_PATH.as_posix())
    report = run_checks(con)
    con.close()

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"quality_report_{timestamp}.json"

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Quality report written to: {report_path}")
    print(
        f"Summary: {report['summary']['passed']} passed, "
        f"{report['summary']['warnings']} warnings, "
        f"{report['summary']['failed']} failed"
    )


if __name__ == "__main__":
    main()
