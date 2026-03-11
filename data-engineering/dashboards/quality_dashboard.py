import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys
import re
import io
import json
from pathlib import Path
from datetime import datetime, timezone
from functools import wraps
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings

st.set_page_config(page_title="DataPulse Quality Dashboard", layout="wide")


# =============================================================================
# Security Utilities
# =============================================================================


def sanitize_input(value: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not value:
        return ""
    # Remove potentially dangerous characters
    return re.sub(r"[;'\"\-\-\/\*]", "", str(value))


def validate_ids(ids: list) -> list[int]:
    """Validate that all IDs are integers to prevent SQL injection."""
    validated = []
    for id_val in ids:
        try:
            validated.append(int(id_val))
        except (ValueError, TypeError):
            continue
    return validated


def validate_severities(severities: list, allowed: list) -> list[str]:
    """Validate severity values against allowed list."""
    return [s for s in severities if s in allowed]


def mask_connection_string(conn_str: str) -> str:
    """Mask credentials in connection string for logging."""
    pattern = r"(?P<pre>.*://)(?P<user>[^:@]+)(:(?P<pass>[^@]+))?@(?P<post>.*)"
    match = re.match(pattern, conn_str)
    if match:
        groups = match.groupdict()
        masked = "***" if groups.get("pass") else ""
        return f"{groups['pre']}{groups['user']}:{masked}@{groups['post']}"
    return conn_str


def get_session_id() -> str:
    """Generate a session ID for audit logging."""
    if "session_id" not in st.session_state:
        timestamp = datetime.now(timezone.utc).isoformat()
        st.session_state.session_id = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return st.session_state.session_id


def log_query(query_name: str, params: dict = None):
    """Log query execution for audit trail."""
    session_id = get_session_id()
    # In production, this would write to a proper audit log
    # For now, we track in session state
    if "query_log" not in st.session_state:
        st.session_state.query_log = []
    st.session_state.query_log.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "query": query_name,
            "params": {k: str(v)[:50] for k, v in (params or {}).items()},
        }
    )


# =============================================================================
# Database Connection with Security
# =============================================================================


def get_engine():
    """Create database engine with connection pooling."""
    try:
        url = settings["database"]["target_url"]
        engine = create_engine(
            url,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_size=5,
            max_overflow=10,
        )
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {type(e).__name__}")
        return None


def run_query_safe(query: str, params: dict = None, query_name: str = "unnamed") -> pd.DataFrame:
    """Execute query with error handling and audit logging."""
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()

    log_query(query_name, params)

    try:
        with engine.connect() as conn:
            # Set statement timeout for query protection (PostgreSQL)
            try:
                conn.execute(text("SET statement_timeout = '30s'"))
            except SQLAlchemyError:
                pass  # SQLite doesn't support this

            result = pd.read_sql(text(query), conn, params=params)
            return result
    except SQLAlchemyError as e:
        st.error(f"Query error: {type(e).__name__}")
        return pd.DataFrame()


def run_query(query: str, params: dict = None) -> pd.DataFrame:
    """Legacy wrapper for compatibility."""
    return run_query_safe(query, params, "legacy")


# =============================================================================
# Download Utilities
# =============================================================================


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()


def create_download_button(df: pd.DataFrame, filename: str, label: str = "Download", file_format: str = "csv"):
    """Create a download button for DataFrame."""
    if df.empty:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    full_filename = f"{filename}_{timestamp}.{file_format}"

    if file_format == "csv":
        data = convert_df_to_csv(df)
        mime = "text/csv"
    else:
        try:
            data = convert_df_to_excel(df)
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        except ImportError:
            # Fall back to CSV if openpyxl not available
            data = convert_df_to_csv(df)
            full_filename = f"{filename}_{timestamp}.csv"
            mime = "text/csv"

    st.download_button(
        label=label,
        data=data,
        file_name=full_filename,
        mime=mime,
    )


def download_chart_data(chart_df: pd.DataFrame, chart_name: str):
    """Add download buttons for chart data."""
    col1, col2 = st.columns([1, 1])
    with col1:
        create_download_button(chart_df, chart_name, "📥 CSV", "csv")
    with col2:
        create_download_button(chart_df, chart_name, "📥 Excel", "xlsx")


# =============================================================================
# Parameterized Queries (SQL Injection Prevention)
# =============================================================================


def build_parameterized_query(
    base_query: str, dataset_ids: list[int], start_date, end_date, severities: list[str]
) -> tuple[str, dict]:
    """
    Build query with proper parameterization to prevent SQL injection.

    Uses numbered placeholders for IDs and severities.
    """
    params = {"start": start_date, "end": end_date}

    # Build ID placeholders (:id_0, :id_1, ...)
    id_placeholders = []
    for i, id_val in enumerate(dataset_ids):
        param_name = f"id_{i}"
        id_placeholders.append(f":{param_name}")
        params[param_name] = id_val

    # Build severity placeholders (:sev_0, :sev_1, ...)
    sev_placeholders = []
    for i, sev in enumerate(severities):
        param_name = f"sev_{i}"
        sev_placeholders.append(f":{param_name}")
        params[param_name] = sev

    # Replace placeholders in query
    query = base_query.replace("{id_list}", ", ".join(id_placeholders))
    query = query.replace("{sev_list}", ", ".join(sev_placeholders))

    return query, params


def calculate_trend(values):
    if len(values) < 2:
        return 0
    return ((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100) if values.iloc[0] != 0 else 0


def get_pipeline_state() -> dict:
    """Read ETL state metadata for dashboard visibility."""
    state_file = Path(__file__).parent.parent / "logs" / "pipeline_state.json"
    if not state_file.exists():
        return {}
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


# =============================================================================
# Dashboard UI
# =============================================================================

st.title("DataPulse - Data Quality Analytics")

# Session info in sidebar footer
session_id = get_session_id()
pipeline_state = get_pipeline_state()

datasets_df = run_query_safe("SELECT DISTINCT id, name FROM dim_datasets ORDER BY name", query_name="get_datasets")
if datasets_df.empty:
    st.warning("No analytics data available. Run the ETL pipeline first.")
    st.stop()

with st.sidebar:
    st.header("Filters")

    refresh_clicked = st.button("Reload Latest Data", use_container_width=True)
    if refresh_clicked:
        st.session_state["force_filter_reset"] = True
        st.rerun()

    dataset_options = datasets_df["name"].tolist()
    force_filter_reset = st.session_state.pop("force_filter_reset", False)
    dataset_options_changed = set(st.session_state.get("dataset_options_seen", [])) != set(dataset_options)
    if force_filter_reset or dataset_options_changed or "selected_datasets_filter" not in st.session_state:
        st.session_state["selected_datasets_filter"] = dataset_options.copy()
    st.session_state["dataset_options_seen"] = dataset_options.copy()
    selected_datasets = st.multiselect(
        "Datasets",
        dataset_options,
        key="selected_datasets_filter",
    )

    date_df = run_query_safe(
        "SELECT MIN(full_date) AS min_d, MAX(full_date) AS max_d FROM dim_date", query_name="get_date_range"
    )
    min_date = pd.to_datetime(date_df["min_d"].iloc[0]).date()
    max_date = pd.to_datetime(date_df["max_d"].iloc[0]).date()
    today_date = datetime.now().date()
    st.caption(f"Latest data date: {max_date}")

    if "date_range_filter" in st.session_state:
        del st.session_state["date_range_filter"]

    if force_filter_reset or "start_date_filter" not in st.session_state:
        st.session_state["start_date_filter"] = min_date
    if force_filter_reset or "end_date_filter" not in st.session_state:
        st.session_state["end_date_filter"] = max_date

    st.markdown("**Date Range**")
    start_date = st.date_input(
        "Start Date",
        key="start_date_filter",
        min_value=min_date,
        max_value=today_date,
    )
    end_date = st.date_input(
        "End Date",
        key="end_date_filter",
        min_value=min_date,
        max_value=today_date,
    )

    if start_date > end_date:
        st.warning("Start date cannot be after end date. Resetting to available data range.")
        st.session_state["start_date_filter"] = min_date
        st.session_state["end_date_filter"] = max_date
        st.rerun()

    if end_date > max_date:
        st.info(f"No loaded data yet beyond {max_date}. Run ETL for newer dates.")

    severity_options = ["HIGH", "MEDIUM", "LOW"]
    if force_filter_reset or "severity_filter" not in st.session_state:
        st.session_state["severity_filter"] = severity_options.copy()
    selected_severities = st.multiselect(
        "Severity",
        severity_options,
        key="severity_filter",
    )

    st.divider()
    st.header("ETL Status")
    if pipeline_state:
        st.caption(f"Last ETL run: {pipeline_state.get('last_successful_run', 'N/A')}")
        st.caption(f"Watermark: {pipeline_state.get('high_watermark', 'N/A')}")
    else:
        st.caption("No ETL state found yet.")

    st.divider()
    st.header("Export Options")
    export_format = st.selectbox("Download Format", ["CSV", "Excel"])

    st.divider()
    st.caption(f"Session: {session_id}")
    st.caption(f"Queries: {len(st.session_state.get('query_log', []))}")

# Validate and sanitize inputs
selected_ids = validate_ids(datasets_df[datasets_df["name"].isin(selected_datasets)]["id"].tolist())
selected_severities = validate_severities(selected_severities, severity_options)

if not selected_ids:
    st.info("Select at least one dataset.")
    st.stop()

if not selected_severities:
    st.info("Select at least one severity level.")
    st.stop()

st.subheader("Quality Overview")

kpi_query_template = """
    SELECT
        COUNT(*) AS total_checks,
        SUM(CASE WHEN passed THEN 1 ELSE 0 END) AS passed_checks,
        AVG(score) AS avg_score,
        MIN(score) AS min_score,
        MAX(score) AS max_score
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE f.dataset_id IN ({id_list})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({sev_list})
"""
kpi_query, kpi_params = build_parameterized_query(
    kpi_query_template, selected_ids, start_date, end_date, selected_severities
)
kpi_df = run_query_safe(kpi_query, kpi_params, "kpi_overview")

if not kpi_df.empty and kpi_df["total_checks"].iloc[0] > 0:
    total = kpi_df["total_checks"].iloc[0]
    passed = kpi_df["passed_checks"].iloc[0]
    avg_score = kpi_df["avg_score"].iloc[0]
    pass_rate = (passed / total * 100) if total > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Checks", f"{total:,}")
    with col2:
        st.metric("Pass Rate", f"{pass_rate:.1f}%")
    with col3:
        st.metric("Average Score", f"{avg_score:.1f}%")
    with col4:
        failed = total - passed
        st.metric("Failed Checks", f"{failed:,}", delta=f"-{failed}" if failed > 0 else None, delta_color="inverse")
    with col5:
        # Download KPI summary
        kpi_export = pd.DataFrame(
            {
                "Metric": ["Total Checks", "Passed", "Failed", "Pass Rate %", "Avg Score"],
                "Value": [total, passed, total - passed, round(pass_rate, 1), round(avg_score, 1)],
            }
        )
        create_download_button(kpi_export, "kpi_summary", "📥 KPIs", export_format.lower())

st.subheader("Quality Score Trends")

trend_query_template = """
    SELECT d.full_date, ds.name AS dataset_name, AVG(f.score) AS avg_score,
           COUNT(*) AS check_count
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_datasets ds ON f.dataset_id = ds.id
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE ds.id IN ({id_list})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({sev_list})
    GROUP BY d.full_date, ds.name
    ORDER BY d.full_date
"""
trend_query, trend_params = build_parameterized_query(
    trend_query_template, selected_ids, start_date, end_date, selected_severities
)
trend_df = run_query_safe(trend_query, trend_params, "quality_trends")

if not trend_df.empty:
    col1, col2 = st.columns([3, 1])

    with col1:
        fig = px.line(
            trend_df,
            x="full_date",
            y="avg_score",
            color="dataset_name",
            labels={"full_date": "Date", "avg_score": "Average Score (%)", "dataset_name": "Dataset"},
        )
        fig.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Target (90%)")
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Critical (70%)")
        st.plotly_chart(fig, use_container_width=True)

        # Download trend data
        download_chart_data(trend_df, "quality_trends")

    with col2:
        st.markdown("**Trend Insights**")
        for dataset in trend_df["dataset_name"].unique():
            ds_data = trend_df[trend_df["dataset_name"] == dataset]
            trend = calculate_trend(ds_data["avg_score"])
            latest = ds_data["avg_score"].iloc[-1] if len(ds_data) > 0 else 0

            if trend > 5:
                st.success(f"{dataset}: Improving (+{trend:.1f}%)")
            elif trend < -5:
                st.error(f"{dataset}: Declining ({trend:.1f}%)")
            else:
                st.info(f"{dataset}: Stable ({trend:+.1f}%)")

            if latest < 70:
                st.warning(f"  Current score ({latest:.1f}%) below critical threshold")
else:
    st.info("No trend data for selected filters.")

st.subheader("Failure Analysis")

col1, col2 = st.columns(2)

with col1:
    failure_query_template = """
        SELECT r.rule_type,
               COUNT(*) AS total,
               SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed,
               ROUND(AVG(CASE WHEN NOT f.passed THEN 1.0 ELSE 0.0 END) * 100, 1) AS failure_rate
        FROM fact_quality_checks f
        JOIN dim_rules r ON f.rule_id = r.id
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.dataset_id IN ({id_list})
          AND d.full_date BETWEEN :start AND :end
          AND r.severity IN ({sev_list})
        GROUP BY r.rule_type
        ORDER BY failure_rate DESC
    """
    failure_query, failure_params = build_parameterized_query(
        failure_query_template, selected_ids, start_date, end_date, selected_severities
    )
    failure_df = run_query_safe(failure_query, failure_params, "failure_by_ruletype")

    if not failure_df.empty:
        fig = px.bar(
            failure_df,
            x="rule_type",
            y="failure_rate",
            labels={"rule_type": "Rule Type", "failure_rate": "Failure Rate (%)"},
            color="failure_rate",
            color_continuous_scale=["#2ecc71", "#f1c40f", "#e74c3c"],
        )
        st.plotly_chart(fig, use_container_width=True)
        create_download_button(failure_df, "failure_by_ruletype", "📥 Download", export_format.lower())

        if failure_df["failure_rate"].max() > 30:
            worst_rule = failure_df.iloc[0]["rule_type"]
            st.warning(f"High failure rate detected: {worst_rule} rules need attention")

with col2:
    severity_query_template = """
        SELECT r.severity,
               COUNT(*) AS total,
               SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed
        FROM fact_quality_checks f
        JOIN dim_rules r ON f.rule_id = r.id
        JOIN dim_date d ON f.date_key = d.date_key
        WHERE f.dataset_id IN ({id_list})
          AND d.full_date BETWEEN :start AND :end
          AND r.severity IN ({sev_list})
        GROUP BY r.severity
    """
    severity_query, severity_params = build_parameterized_query(
        severity_query_template, selected_ids, start_date, end_date, selected_severities
    )
    severity_df = run_query_safe(severity_query, severity_params, "failure_by_severity")

    if not severity_df.empty:
        severity_df["passed"] = severity_df["total"] - severity_df["failed"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Passed", x=severity_df["severity"], y=severity_df["passed"], marker_color="#2ecc71"))
        fig.add_trace(go.Bar(name="Failed", x=severity_df["severity"], y=severity_df["failed"], marker_color="#e74c3c"))
        fig.update_layout(barmode="stack", xaxis_title="Severity", yaxis_title="Check Count")
        st.plotly_chart(fig, use_container_width=True)
        create_download_button(severity_df, "failure_by_severity", "📥 Download", export_format.lower())

        high_failures = (
            severity_df[severity_df["severity"] == "HIGH"]["failed"].sum()
            if "HIGH" in severity_df["severity"].values
            else 0
        )
        if high_failures > 0:
            st.error(f"{high_failures} HIGH severity failures require immediate attention")

st.subheader("Dataset Quality Comparison")

comparison_query_template = """
    SELECT ds.name AS dataset,
           ROUND(AVG(f.score)::numeric, 1) AS avg_score,
           COUNT(*) AS total_checks,
           SUM(CASE WHEN f.passed THEN 1 ELSE 0 END) AS passed,
           SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failed,
           ROUND(STDDEV(f.score)::numeric, 2) AS score_std
    FROM fact_quality_checks f
    JOIN dim_datasets ds ON f.dataset_id = ds.id
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE ds.id IN ({id_list})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({sev_list})
    GROUP BY ds.name
    ORDER BY avg_score ASC
"""
comparison_query, comparison_params = build_parameterized_query(
    comparison_query_template, selected_ids, start_date, end_date, selected_severities
)
comparison_df = run_query_safe(comparison_query, comparison_params, "dataset_comparison")

if not comparison_df.empty:
    comparison_df["pass_rate"] = round(comparison_df["passed"] / comparison_df["total_checks"] * 100, 1)
    comparison_df["quality_status"] = comparison_df["avg_score"].apply(
        lambda x: "Critical" if x < 70 else ("Warning" if x < 90 else "Healthy")
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            comparison_df,
            x="dataset",
            y="avg_score",
            color="quality_status",
            color_discrete_map={"Critical": "#e74c3c", "Warning": "#f39c12", "Healthy": "#2ecc71"},
            labels={"dataset": "Dataset", "avg_score": "Average Score (%)"},
        )
        fig.add_hline(y=90, line_dash="dash", line_color="green")
        fig.add_hline(y=70, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Quality Assessment**")
        for _, row in comparison_df.iterrows():
            if row["quality_status"] == "Critical":
                st.error(f"{row['dataset']}: {row['avg_score']}% - Immediate action required")
            elif row["quality_status"] == "Warning":
                st.warning(f"{row['dataset']}: {row['avg_score']}% - Monitor closely")
            else:
                st.success(f"{row['dataset']}: {row['avg_score']}% - Healthy")

            if row["score_std"] and row["score_std"] > 15:
                st.info(f"  High variability (std: {row['score_std']})")

    st.dataframe(
        comparison_df[["dataset", "avg_score", "pass_rate", "total_checks", "quality_status"]],
        use_container_width=True,
        hide_index=True,
    )
    download_chart_data(comparison_df, "dataset_comparison")

st.subheader("Field-Level Quality Issues")

field_query_template = """
    SELECT r.field_name, r.rule_type, r.severity,
           COUNT(*) AS total_checks,
           SUM(CASE WHEN NOT f.passed THEN 1 ELSE 0 END) AS failures,
           ROUND(AVG(CASE WHEN NOT f.passed THEN 1.0 ELSE 0.0 END) * 100, 1) AS failure_rate
    FROM fact_quality_checks f
    JOIN dim_rules r ON f.rule_id = r.id
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.dataset_id IN ({id_list})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({sev_list})
      AND NOT f.passed
    GROUP BY r.field_name, r.rule_type, r.severity
    ORDER BY failures DESC
    LIMIT 10
"""
field_query, field_params = build_parameterized_query(
    field_query_template, selected_ids, start_date, end_date, selected_severities
)
field_df = run_query_safe(field_query, field_params, "field_quality_issues")

if not field_df.empty:
    fig = px.treemap(
        field_df,
        path=["field_name", "rule_type"],
        values="failures",
        color="severity",
        color_discrete_map={"HIGH": "#e74c3c", "MEDIUM": "#f39c12", "LOW": "#3498db"},
    )
    st.plotly_chart(fig, use_container_width=True)
    create_download_button(field_df, "field_quality_issues", "📥 Download", export_format.lower())

    st.markdown("**Top Problem Fields:**")
    for _, row in field_df.head(3).iterrows():
        st.markdown(
            f"- **{row['field_name']}** ({row['rule_type']}): {row['failures']} failures - {row['severity']} severity"
        )
else:
    st.success("No field-level failures detected for selected filters.")

st.subheader("Quality Patterns by Day of Week")

dow_query_template = """
    SELECT d.day_of_week,
           ROUND(AVG(f.score)::numeric, 1) AS avg_score,
           COUNT(*) AS check_count
    FROM fact_quality_checks f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_rules r ON f.rule_id = r.id
    WHERE f.dataset_id IN ({id_list})
      AND d.full_date BETWEEN :start AND :end
      AND r.severity IN ({sev_list})
    GROUP BY d.day_of_week
    ORDER BY d.day_of_week
"""
dow_query, dow_params = build_parameterized_query(
    dow_query_template, selected_ids, start_date, end_date, selected_severities
)
dow_df = run_query_safe(dow_query, dow_params, "quality_by_dow")

if not dow_df.empty:
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    dow_df["day_name"] = dow_df["day_of_week"].apply(lambda x: dow_names[x] if x < 7 else "Unknown")

    fig = px.bar(
        dow_df,
        x="day_name",
        y="avg_score",
        labels={"day_name": "Day of Week", "avg_score": "Average Score (%)"},
        color="avg_score",
        color_continuous_scale=["#e74c3c", "#f1c40f", "#2ecc71"],
    )
    st.plotly_chart(fig, use_container_width=True)
    create_download_button(dow_df, "quality_by_dow", "📥 Download", export_format.lower())

    if dow_df["avg_score"].std() > 5:
        worst_day = dow_df.loc[dow_df["avg_score"].idxmin(), "day_name"]
        best_day = dow_df.loc[dow_df["avg_score"].idxmax(), "day_name"]
        st.info(
            f"Quality varies by day: Best on {best_day}, worst on {worst_day}. Consider investigating data sources active on {worst_day}."
        )

# --- Full Report Export ---
st.markdown("---")
st.subheader("Export Full Report")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Export All Data (CSV)", use_container_width=True):
        # Combine all data into a single export
        all_data = {}
        if not kpi_df.empty:
            all_data["kpi_summary"] = kpi_df
        if "trend_df" in dir() and not trend_df.empty:
            all_data["quality_trends"] = trend_df
        if "failure_df" in dir() and not failure_df.empty:
            all_data["failure_analysis"] = failure_df
        if "comparison_df" in dir() and not comparison_df.empty:
            all_data["dataset_comparison"] = comparison_df
        if "field_df" in dir() and not field_df.empty:
            all_data["field_issues"] = field_df
        if "dow_df" in dir() and not dow_df.empty:
            all_data["day_of_week"] = dow_df

        # Create combined CSV
        combined_csv = ""
        for name, df in all_data.items():
            combined_csv += f"\n\n=== {name.upper()} ===\n"
            combined_csv += df.to_csv(index=False)

        st.download_button(
            label="⬇️ Download Combined CSV",
            data=combined_csv,
            file_name=f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

with col2:
    if st.button("📈 Export Charts Data (Excel)", use_container_width=True):
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                if "trend_df" in dir() and not trend_df.empty:
                    trend_df.to_excel(writer, sheet_name="Trends", index=False)
                if "failure_df" in dir() and not failure_df.empty:
                    failure_df.to_excel(writer, sheet_name="Failures", index=False)
                if "comparison_df" in dir() and not comparison_df.empty:
                    comparison_df.to_excel(writer, sheet_name="Comparison", index=False)
                if "field_df" in dir() and not field_df.empty:
                    field_df.to_excel(writer, sheet_name="Field_Issues", index=False)
                if "dow_df" in dir() and not dow_df.empty:
                    dow_df.to_excel(writer, sheet_name="Day_of_Week", index=False)

            st.download_button(
                label="⬇️ Download Excel Workbook",
                data=buffer.getvalue(),
                file_name=f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ImportError:
            st.warning("Install openpyxl for Excel export: pip install openpyxl")

with col3:
    if st.button("📋 Export JSON Summary", use_container_width=True):
        summary = {
            "report_generated": datetime.now().isoformat(),
            "filters": {
                "datasets": selected_datasets,
                "severities": selected_severities,
                "date_range": {"start": str(start_date), "end": str(end_date)},
            },
            "kpi": {
                "total_checks": int(kpi_df["total_checks"].iloc[0]) if not kpi_df.empty else 0,
                "pass_rate": round(pass_rate, 1) if "pass_rate" in dir() else 0,
                "avg_score": round(float(kpi_df["avg_score"].iloc[0]), 1) if not kpi_df.empty else 0,
            },
        }

        st.download_button(
            label="⬇️ Download JSON Summary",
            data=json.dumps(summary, indent=2),
            file_name=f"quality_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

# --- Footer ---
st.markdown("---")
st.caption(
    f"Dashboard refreshed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Session: {get_session_id()[:8]}..."
)
