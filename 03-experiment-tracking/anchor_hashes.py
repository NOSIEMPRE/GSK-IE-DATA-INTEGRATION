"""
Hash anchoring for RWD TrustChain provenance.

Computes SHA256 hashes of OMOP snapshot, quality reports, and ETL specs.
Outputs a provenance manifest for audit trail (simulates blockchain anchoring).

Usage (from project root):
    python 03-experiment-tracking/anchor_hashes.py

Prerequisites:
    - data/synthea1k.duckdb (from 01-initial-notebook/load_synthea_duckdb.py)
    - data/quality_reports/*.json (from 02-data-sampling-feature/validate_omop_quality.py)
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = PROJECT_ROOT / "data" / "provenance"


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def anchor_assets() -> dict:
    """Build provenance manifest with hashes of key assets."""
    manifest = {
        "manifest_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "RWD TrustChain provenance manifest (hash anchoring)",
        "anchored_assets": [],
    }

    assets = [
        ("OMOP snapshot", PROJECT_ROOT / "data" / "synthea1k.duckdb"),
        ("ETL spec: load", PROJECT_ROOT / "01-initial-notebook" / "load_synthea_duckdb.py"),
        ("ETL spec: download", PROJECT_ROOT / "01-initial-notebook" / "download_synthea_omop.sh"),
        ("Validation script", PROJECT_ROOT / "02-data-sampling-feature" / "validate_omop_quality.py"),
        ("PPRL demo script", PROJECT_ROOT / "02-data-sampling-feature" / "pprl_multi_source_demo.py"),
    ]

    for label, path in assets:
        if not path.exists():
            manifest["anchored_assets"].append(
                {"asset": label, "path": str(path), "status": "missing", "hash": None}
            )
            continue

        try:
            h = sha256_file(path)
            size = path.stat().st_size
            manifest["anchored_assets"].append(
                {
                    "asset": label,
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "hash_algorithm": "SHA256",
                    "hash_value": h,
                    "size_bytes": size,
                    "status": "anchored",
                }
            )
        except Exception as e:
            manifest["anchored_assets"].append(
                {"asset": label, "path": str(path), "status": "error", "error": str(e)}
            )

    # Latest PPRL linkage map (if exists)
    pprl_dir = PROJECT_ROOT / "data" / "pprl"
    if pprl_dir.exists():
        linkage_reports = sorted(pprl_dir.glob("linkage_map_*.json"), reverse=True)
        if linkage_reports:
            latest = linkage_reports[0]
            try:
                h = sha256_file(latest)
                manifest["anchored_assets"].append(
                    {
                        "asset": "PPRL linkage map (latest)",
                        "path": str(latest.relative_to(PROJECT_ROOT)),
                        "hash_algorithm": "SHA256",
                        "hash_value": h,
                        "size_bytes": latest.stat().st_size,
                        "status": "anchored",
                    }
                )
            except Exception as e:
                manifest["anchored_assets"].append(
                    {"asset": "PPRL linkage map", "path": str(latest), "status": "error", "error": str(e)}
                )

    # Latest quality report
    report_dir = PROJECT_ROOT / "data" / "quality_reports"
    if report_dir.exists():
        reports = sorted(report_dir.glob("quality_report_*.json"), reverse=True)
        if reports:
            latest = reports[0]
            try:
                h = sha256_file(latest)
                manifest["anchored_assets"].append(
                    {
                        "asset": "Quality report (latest)",
                        "path": str(latest.relative_to(PROJECT_ROOT)),
                        "hash_algorithm": "SHA256",
                        "hash_value": h,
                        "size_bytes": latest.stat().st_size,
                        "status": "anchored",
                    }
                )
            except Exception as e:
                manifest["anchored_assets"].append(
                    {"asset": "Quality report", "path": str(latest), "status": "error", "error": str(e)}
                )
        else:
            manifest["anchored_assets"].append(
                {"asset": "Quality report", "path": "data/quality_reports/", "status": "no_reports", "hash": None}
            )
    else:
        manifest["anchored_assets"].append(
            {"asset": "Quality report", "path": "data/quality_reports/", "status": "missing", "hash": None}
        )

    return manifest


def main() -> None:
    manifest = anchor_assets()

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFEST_DIR / f"provenance_manifest_{manifest['manifest_id']}.json"

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    anchored = sum(1 for a in manifest["anchored_assets"] if a.get("status") == "anchored")
    total = len(manifest["anchored_assets"])

    print(f"Provenance manifest written to: {manifest_path}")
    print(f"Anchored {anchored}/{total} assets")
    for a in manifest["anchored_assets"]:
        status = a.get("status", "?")
        h = a.get("hash_value", "—")[:16] + "..." if a.get("hash_value") else "—"
        print(f"  [{status}] {a['asset']}: {h}")


if __name__ == "__main__":
    main()
