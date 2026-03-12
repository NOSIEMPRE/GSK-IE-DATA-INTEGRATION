"""
RWD TrustChain — Governance Dashboard (Streamlit).

Visualizes:
- Data quality summary (from latest quality_report_*.json)
- AI validation status (Isolation Forest / Ensemble)
- HBV-style care cascade (Testing → Diagnosis → Treatment)
- Provenance manifest (hash anchoring overview)
- MLflow experiment tracking link

Usage (from project root):
    streamlit run 04-deployment/app.py
"""

from pathlib import Path

import json

import altair as alt
import pandas as pd
import streamlit as st

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MLRUNS_DIR = PROJECT_ROOT / "mlruns"
MLFLOW_EXPERIMENT_NAME = "rwd-trustchain-quality"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality_reports"
PROVENANCE_DIR = PROJECT_ROOT / "data" / "provenance"
PPRL_DIR = PROJECT_ROOT / "data" / "pprl"
DB_PATH = PROJECT_ROOT / "data" / "synthea1k.duckdb"


def load_latest_quality_report() -> dict | None:
    if not QUALITY_DIR.exists():
        return None
    reports = sorted(QUALITY_DIR.glob("quality_report_*.json"), reverse=True)
    if not reports:
        return None
    with open(reports[0], "r", encoding="utf-8") as f:
        return json.load(f)


def load_latest_manifest() -> dict | None:
    if not PROVENANCE_DIR.exists():
        return None
    manifests = sorted(PROVENANCE_DIR.glob("provenance_manifest_*.json"), reverse=True)
    if not manifests:
        return None
    with open(manifests[0], "r", encoding="utf-8") as f:
        return json.load(f)


def load_latest_linkage_map() -> dict | None:
    if not PPRL_DIR.exists():
        return None
    reports = sorted(PPRL_DIR.glob("linkage_map_*.json"), reverse=True)
    if not reports:
        return None
    with open(reports[0], "r", encoding="utf-8") as f:
        return json.load(f)


def get_mlflow_experiment_url() -> tuple[str, str]:
    """
    Get MLflow UI URL, deep-linking to rwd-trustchain-quality if it exists.
    Returns (url, caption).
    """
    base = "http://localhost:5000"
    if not MLFLOW_AVAILABLE or not MLRUNS_DIR.exists():
        return base, "Run `bash 03-experiment-tracking/mlflow_ui.sh` first"
    try:
        client = MlflowClient(tracking_uri=MLRUNS_DIR.resolve().as_uri())
        exp = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
        if exp and exp.experiment_id:
            return f"{base}/#/experiments/{exp.experiment_id}", "Direct link to experiment"
    except Exception:
        pass
    return base, "Run `run_with_mlflow.py` (scenario1 + scenario2) to create runs"


def load_hbv_cascade() -> dict | None:
    """HBV-style care cascade: Testing → Diagnosis → Treatment (Synthea proxy)."""
    if not DUCKDB_AVAILABLE or not DB_PATH.exists():
        return None
    try:
        con = duckdb.connect(DB_PATH.as_posix())
        cascade_query = """
        WITH cohort AS (SELECT person_id FROM person),
             tested AS (SELECT DISTINCT person_id FROM measurement),
             diagnosed AS (
                 SELECT DISTINCT t.person_id FROM tested t
                 WHERE t.person_id IN (SELECT person_id FROM condition_occurrence)
             ),
             treated AS (
                 SELECT DISTINCT d.person_id FROM diagnosed d
                 WHERE d.person_id IN (SELECT person_id FROM drug_exposure)
             )
        SELECT
            (SELECT COUNT(*) FROM cohort) AS total_persons,
            (SELECT COUNT(*) FROM tested) AS tested,
            (SELECT COUNT(*) FROM diagnosed) AS diagnosed,
            (SELECT COUNT(*) FROM treated) AS treated,
            (SELECT COUNT(*) FROM tested t WHERE t.person_id NOT IN (SELECT person_id FROM diagnosed))
                AS gap_tested_not_diagnosed,
            (SELECT COUNT(*) FROM diagnosed d WHERE d.person_id NOT IN (SELECT person_id FROM treated))
                AS gap_diagnosed_not_treated
        """
        row = con.execute(cascade_query).fetchone()
        con.close()
        return {
            "total_persons": row[0],
            "tested": row[1],
            "diagnosed": row[2],
            "treated": row[3],
            "gap_tested_not_diagnosed": row[4],
            "gap_diagnosed_not_treated": row[5],
        }
    except Exception:
        return None


def main() -> None:
    st.set_page_config(page_title="RWD TrustChain Governance Dashboard", layout="wide")
    st.title("RWD TrustChain Governance Dashboard")
    st.caption("Data quality, AI validation, HBV cascade, and provenance overview")

    # Sidebar: MLflow link (deep-link to rwd-trustchain-quality when it exists)
    with st.sidebar:
        st.subheader("Experiment Tracking")
        mlflow_url, mlflow_caption = get_mlflow_experiment_url()
        st.markdown(f"[**MLflow UI**]({mlflow_url}) — experiment `{MLFLOW_EXPERIMENT_NAME}`")
        st.caption(mlflow_caption)

    # HBV Cascade
    st.subheader("HBV-Style Care Cascade (Testing → Diagnosis → Treatment)")
    cascade = load_hbv_cascade()
    if not cascade:
        st.info("DuckDB not available or database missing. Run `load_synthea_duckdb.py` first.")
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Total Persons", cascade["total_persons"])
        with c2:
            st.metric("Tested", cascade["tested"])
        with c3:
            st.metric("Diagnosed", cascade["diagnosed"])
        with c4:
            st.metric("Treated", cascade["treated"])
        with c5:
            st.metric("Gaps", f"{cascade['gap_tested_not_diagnosed']} + {cascade['gap_diagnosed_not_treated']}")

        funnel_df = pd.DataFrame({
            "Stage": ["Total", "Tested", "Diagnosed", "Treated"],
            "Count": [
                cascade["total_persons"],
                cascade["tested"],
                cascade["diagnosed"],
                cascade["treated"],
            ],
        })
        chart = (
            alt.Chart(funnel_df)
            .mark_bar()
            .encode(
                x=alt.X("Stage", axis=alt.Axis(labelAngle=0)),
                y="Count",
            )
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption("Gap (tested→diagnosed): %d | Gap (diagnosed→treated): %d" % (
            cascade["gap_tested_not_diagnosed"],
            cascade["gap_diagnosed_not_treated"],
        ))

    # PPRL linkage (if available)
    linkage = load_latest_linkage_map()
    if linkage:
        st.markdown("---")
        st.subheader("PPRL — Privacy-Preserving Record Linkage")
        m = linkage.get("metrics", {})
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Source A (EHR)", m.get("source_a_records", 0))
        with c2:
            st.metric("Source B (Lab)", m.get("source_b_records", 0))
        with c3:
            st.metric("Persons Linked", m.get("unique_persons_linked", 0))
        st.caption(f"Method: {linkage.get('method', 'N/A')} | Run: {linkage.get('linkage_run_id', 'N/A')}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Quality summary & AI validation
    with col1:
        st.subheader("Data Quality & AI Validation")
        report = load_latest_quality_report()
        if not report:
            st.warning("No quality reports found. Run the validation script first.")
        else:
            summary = report.get("summary", {})
            st.metric("Checks Passed", summary.get("passed", 0))
            st.metric("Warnings", summary.get("warnings", 0))
            st.metric("Failed", summary.get("failed", 0))

            ai = report.get("ai_validation", {})
            module = ai.get("module", "Isolation Forest")
            st.markdown(f"**AI Validation ({module})**")
            if ai.get("status") == "completed":
                st.metric("Anomalies", ai.get("anomaly_count", 0))
                st.metric("Total Analyzed", ai.get("total_analyzed", 0))
            st.json(ai)

    # Provenance manifest
    with col2:
        st.subheader("Provenance & Hash Anchoring")
        manifest = load_latest_manifest()
        if not manifest:
            st.warning("No provenance manifests found. Run the hash anchoring script first.")
        else:
            st.markdown(f"**Manifest ID:** `{manifest.get('manifest_id')}`")
            st.markdown(f"**Created at:** `{manifest.get('created_at')}`")
            anchored = [a for a in manifest.get("anchored_assets", []) if a.get("status") == "anchored"]
            st.metric("Anchored Assets", len(anchored))
            st.markdown("**Anchored Assets (truncated hashes):**")
            for a in anchored:
                hv = a.get("hash_value", "")
                short = hv[:10] + "..." if hv else "—"
                st.write(f"- `{a['asset']}` — `{short}`")

    st.markdown("---")
    st.markdown("### Raw Artifacts")
    st.markdown("- Quality reports: `data/quality_reports/`")
    st.markdown("- Provenance manifests: `data/provenance/`")
    st.markdown("- PPRL linkage maps: `data/pprl/`")


if __name__ == "__main__":
    main()
