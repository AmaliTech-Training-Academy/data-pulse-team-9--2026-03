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
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from config import settings
from queries import (
    GET_DATASETS,
    GET_DATE_RANGE,
    KPI_OVERVIEW,
    OVERVIEW_SPARK,
    QUALITY_TRENDS,
    FAILURE_BY_RULETYPE,
    FAILURE_BY_SEVERITY,
    DATASET_COMPARISON,
    FIELD_QUALITY_ISSUES,
    QUALITY_BY_DOW,
)

st.set_page_config(
    page_title="DataPulse Quality Dashboard",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Color Palette & Styling Constants
# =============================================================================

COLORS = {
    "healthy": "#00c48c",
    "warning": "#f5a623",
    "critical": "#ff4757",
    "info": "#2f86eb",
    "neutral": "#8392a5",
    "background": "#f4f6fb",
    "surface": "#ffffff",
    "border": "#e3e8f0",
    "text_primary": "#1a2035",
    "text_secondary": "#5a6478",
    "accent": "#6c63ff",
}

# =============================================================================
# SVG Icon Library  (Feather Icons stroke style, uses currentColor)
# =============================================================================


def _svg(path: str, w: int = 18) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{w}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:middle;">{path}</svg>'
    )


_I = {
    "check": _svg('<polyline points="20 6 9 17 4 12"/>'),
    "warning": _svg(
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "alert": _svg(
        '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'
    ),
    "trend_up": _svg('<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>'),
    "trend_down": _svg('<polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/>'),
    "search": _svg('<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'),
    "bar_chart": _svg(
        '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/>'
    ),
    "target": _svg('<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>'),
    "calendar": _svg(
        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>'
    ),
    "upload": _svg(
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'
    ),
    "arrow_right": _svg('<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>', 16),
    "arrow_down": _svg('<line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>', 16),
    "arrow_up": _svg('<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>', 16),
    "clipboard": _svg(
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
    ),
    "lightbulb": _svg(
        '<line x1="9" y1="18" x2="15" y2="18"/><line x1="10" y1="22" x2="14" y2="22"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>'
    ),
    "folder": _svg('<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>', 16),
}

STATUS_CONFIG = {
    "Healthy": {"color": COLORS["healthy"], "bg": "#e6faf4", "icon": _I["check"], "threshold": 90},
    "Warning": {"color": COLORS["warning"], "bg": "#fff8ec", "icon": _I["warning"], "threshold": 70},
    "Critical": {"color": COLORS["critical"], "bg": "#fff0f2", "icon": _I["alert"], "threshold": 0},
}

NAV_SECTIONS = [
    ("overview", "", "Overview"),
    ("trends", "", "Quality Trends"),
    ("failures", "", "Failure Analysis"),
    ("comparison", "", "Dataset Comparison"),
    ("fields", "", "Field-Level Issues"),
    ("dow", "", "Day Patterns"),
    ("export", "", "Export Report"),
]


def get_quality_status(score: float) -> str:
    if score >= 90:
        return "Healthy"
    elif score >= 70:
        return "Warning"
    return "Critical"


def get_status_color(status: str) -> str:
    return STATUS_CONFIG.get(status, {}).get("color", COLORS["neutral"])


def get_status_bg(status: str) -> str:
    return STATUS_CONFIG.get(status, {}).get("bg", "#f4f6fb")


def get_status_icon(status: str) -> str:
    return STATUS_CONFIG.get(status, {}).get("icon", _I["alert"])


# =============================================================================
# Custom CSS
# =============================================================================

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* ── Hide default Streamlit padding ── */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

    /* ── Page header ── */
    .page-header {
        display: flex; align-items: center; gap: 0.75rem;
        padding: 0.25rem 0 1.25rem 0;
        border-bottom: 2px solid #e3e8f0;
        margin-bottom: 1.5rem;
    }
    .page-title {
        font-size: 1.8rem; font-weight: 700; color: #1a2035; margin: 0; line-height: 1.1;
    }
    .page-subtitle {
        font-size: 0.85rem; color: #5a6478; margin: 0.2rem 0 0 0; font-weight: 400;
    }

    /* ── Section title ── */
    .section-title {
        font-size: 1.15rem; font-weight: 700; color: #1a2035;
        margin: 0 0 0.25rem 0; display: flex; align-items: center; gap: 0.4rem;
    }
    .section-desc {
        font-size: 0.82rem; color: #5a6478; margin: 0 0 1.25rem 0; line-height: 1.5;
    }
    .section-divider {
        border: none; border-top: 1.5px solid #e3e8f0; margin: 2rem 0;
    }

    /* ── Health banner ── */
    .health-banner {
        padding: 1rem 1.4rem; border-radius: 12px; margin-bottom: 1.5rem;
        border-left: 5px solid; display: flex; align-items: center; gap: 1rem;
    }
    .health-banner .hb-icon { font-size: 2rem; line-height: 1; }
    .health-banner .hb-icon svg { width: 28px !important; height: 28px !important; }
    .health-banner .hb-title { font-size: 1rem; font-weight: 700; margin: 0; }
    .health-banner .hb-detail { font-size: 0.82rem; margin: 0.2rem 0 0 0; opacity: 0.8; }

    /* ── KPI metric cards ── */
    .kpi-card {
        background: #ffffff; border-radius: 14px; padding: 1.1rem 1.25rem;
        border: 1.5px solid #e3e8f0; position: relative; overflow: hidden;
        transition: box-shadow .2s;
    }
    .kpi-card:hover { box-shadow: 0 4px 18px rgba(0,0,0,0.07); }
    .kpi-card .kpi-label { font-size: 0.75rem; font-weight: 600; color: #5a6478;
        text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 0.4rem 0; }
    .kpi-card .kpi-value { font-size: 2rem; font-weight: 700; color: #1a2035;
        line-height: 1; margin: 0 0 0.35rem 0; font-family: 'DM Mono', monospace; }
    .kpi-card .kpi-delta { font-size: 0.78rem; font-weight: 500; }
    .kpi-card .kpi-bar {
        position: absolute; bottom: 0; left: 0; height: 3px; border-radius: 0 3px 3px 0;
    }

    /* ── Insight panels ── */
    .insight-card {
        background: #f4f6fb; border-radius: 10px; padding: 0.85rem 1rem;
        margin-bottom: 0.6rem; border-left: 3px solid;
    }
    .insight-card .ic-title { font-size: 0.82rem; font-weight: 700; color: #1a2035; margin: 0 0 0.2rem 0; }
    .insight-card .ic-body  { font-size: 0.78rem; color: #5a6478; margin: 0; line-height: 1.5; }

    /* ── Dataset badge ── */
    .status-badge {
        display: inline-block; padding: 0.18rem 0.6rem; border-radius: 20px;
        font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em;
    }

    /* ── Sidebar nav buttons ── */
    div[data-testid="stButton"] > button {
        border-radius: 8px !important; text-align: left !important;
        padding: 0.55rem 0.9rem !important; font-size: 0.875rem !important;
        font-weight: 500 !important; transition: all .15s !important;
        border: 1.5px solid transparent !important;
    }

    /* ── Sidebar filter labels ── */
    .filter-label {
        font-size: 0.72rem; font-weight: 600; color: #5a6478;
        text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.25rem;
    }
    .sidebar-group {
        background: #f4f6fb; border-radius: 10px; padding: 0.9rem 0.9rem 0.75rem;
        margin-bottom: 0.85rem;
    }
    .sidebar-group-title {
        font-size: 0.72rem; font-weight: 700; color: #1a2035;
        text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.6rem;
    }

    /* ── Pipeline status ── */
    .pipeline-ok  { background:#e6faf4; color:#00c48c; border-radius:8px;
        padding:0.5rem 0.75rem; font-size:0.8rem; font-weight:600; }
    .pipeline-warn{ background:#fff8ec; color:#f5a623; border-radius:8px;
        padding:0.5rem 0.75rem; font-size:0.8rem; font-weight:600; }

    /* ── Comparison row ── */
    .cmp-row {
        display:flex; align-items:center; justify-content:space-between;
        padding:0.65rem 0.9rem; border-radius:8px; margin-bottom:0.45rem;
        background:#ffffff; border:1.5px solid #e3e8f0;
    }
    .cmp-name { font-size:0.85rem; font-weight:600; color:#1a2035; }
    .cmp-score{ font-family:'DM Mono',monospace; font-size:0.95rem; font-weight:700; }

    /* ── Field pill ── */
    .field-pill {
        background:#f4f6fb; border-radius:8px; padding:0.6rem 0.85rem;
        margin-bottom:0.4rem; border-left:3px solid;
    }
    .field-pill .fp-name { font-size:0.82rem; font-weight:700; color:#1a2035; margin:0; }
    .field-pill .fp-meta { font-size:0.74rem; color:#5a6478; margin:0.15rem 0 0 0; }

    /* remove default metric borders */
    [data-testid="stMetric"] { background: transparent !important; }
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# Security Utilities  (UNCHANGED)
# =============================================================================


def sanitize_input(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"[;'\"\-\-\/\*]", "", str(value))


def validate_ids(ids: list) -> list[int]:
    validated = []
    for id_val in ids:
        try:
            validated.append(int(id_val))
        except (ValueError, TypeError):
            continue
    return validated


def validate_severities(severities: list, allowed: list) -> list[str]:
    return [s for s in severities if s in allowed]


def mask_connection_string(conn_str: str) -> str:
    pattern = r"(?P<pre>.*://)(?P<user>[^:@]+)(:(?P<pass>[^@]+))?@(?P<post>.*)"
    match = re.match(pattern, conn_str)
    if match:
        groups = match.groupdict()
        masked = "***" if groups.get("pass") else ""
        return f"{groups['pre']}{groups['user']}:{masked}@{groups['post']}"
    return conn_str


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        timestamp = datetime.now(timezone.utc).isoformat()
        st.session_state.session_id = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return st.session_state.session_id


def log_query(query_name: str, params: dict = None):
    session_id = get_session_id()
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
# Database Connection  (UNCHANGED)
# =============================================================================


@st.cache_resource
def get_engine():
    try:
        url = settings["database"]["target_url"]
        engine = create_engine(url, pool_pre_ping=True)
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {type(e).__name__} - {e}")
        return None


def run_query_safe(query: str, params: dict = None, query_name: str = "unnamed") -> pd.DataFrame:
    """Run a SQL query and return a DataFrame."""
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        st.error(f"Query error ({query_name}): {type(e).__name__} - {str(e)[:300]}")
        return pd.DataFrame()


def run_query(query: str, params: dict = None) -> pd.DataFrame:
    return run_query_safe(query, params, "legacy")


# =============================================================================
# Download Utilities  (UNCHANGED)
# =============================================================================


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return output.getvalue()


def create_download_button(df: pd.DataFrame, filename: str, label: str = "Download", file_format: str = "csv"):
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
            data = convert_df_to_csv(df)
            full_filename = f"{filename}_{timestamp}.csv"
            mime = "text/csv"
    st.download_button(label=label, data=data, file_name=full_filename, mime=mime)


def download_chart_data(chart_df: pd.DataFrame, chart_name: str):
    col1, col2 = st.columns([1, 1])
    with col1:
        create_download_button(chart_df, chart_name, "CSV", "csv")
    with col2:
        create_download_button(chart_df, chart_name, "Excel", "xlsx")


# =============================================================================
# Parameterized Queries  (UNCHANGED)
# =============================================================================


def build_parameterized_query(
    base_query: str, dataset_ids: list[int], start_date, end_date, severities: list[str]
) -> tuple[str, dict]:
    params = {"start": start_date, "end": end_date}
    id_placeholders = []
    for i, id_val in enumerate(dataset_ids):
        param_name = f"id_{i}"
        id_placeholders.append(f":{param_name}")
        params[param_name] = id_val
    sev_placeholders = []
    for i, sev in enumerate(severities):
        param_name = f"sev_{i}"
        sev_placeholders.append(f":{param_name}")
        params[param_name] = sev
    query = base_query.replace("{id_list}", ", ".join(id_placeholders))
    query = query.replace("{sev_list}", ", ".join(sev_placeholders))
    return query, params


def calculate_trend(values):
    if len(values) < 2:
        return 0
    return ((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100) if values.iloc[0] != 0 else 0


def get_pipeline_state() -> dict:
    state_file = Path(__file__).parent.parent / "logs" / "pipeline_state.json"
    if not state_file.exists():
        return {}
    try:
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


# =============================================================================
# Chart helpers
# =============================================================================


def base_layout(title="", xtitle="", ytitle="", yaxis_extra=None):
    yaxis = dict(title=ytitle, gridcolor="#eef0f5", tickfont=dict(size=11))
    if yaxis_extra:
        yaxis.update(yaxis_extra)
    return dict(
        title=dict(text=title, font=dict(size=14, color=COLORS["text_primary"]), x=0),
        xaxis=dict(title=xtitle, gridcolor="#eef0f5", tickfont=dict(size=11)),
        yaxis=yaxis,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="DM Sans, sans-serif", color=COLORS["text_primary"], size=12),
        hovermode="x unified",
        margin=dict(l=0, r=10, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
    )


def add_thresholds(fig):
    fig.add_hline(
        y=90,
        line_dash="dot",
        line_color=COLORS["healthy"],
        line_width=1.5,
        annotation_text="Target 90%",
        annotation_font_size=10,
        annotation_font_color=COLORS["healthy"],
        annotation_position="right",
    )
    fig.add_hline(
        y=70,
        line_dash="dot",
        line_color=COLORS["critical"],
        line_width=1.5,
        annotation_text="Critical 70%",
        annotation_font_size=10,
        annotation_font_color=COLORS["critical"],
        annotation_position="right",
    )
    return fig


# =============================================================================
# Reusable UI Snippets
# =============================================================================


def render_section_header(icon: str, title: str, description: str = ""):
    st.markdown(
        f'<p class="section-title">{icon} {title}</p>'
        + (f'<p class="section-desc">{description}</p>' if description else ""),
        unsafe_allow_html=True,
    )


def render_insight_card(title: str, body: str, color: str):
    st.markdown(
        f'<div class="insight-card" style="border-color:{color};">'
        f'<p class="ic-title">{title}</p>'
        f'<p class="ic-body">{body}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, delta_text: str, delta_ok: bool, bar_color: str, bar_pct: float = 0):
    delta_color = COLORS["healthy"] if delta_ok else COLORS["critical"]
    arrow = "▲" if delta_ok else "▼"
    bar_w = max(0, min(100, bar_pct))
    st.markdown(
        f'<div class="kpi-card">'
        f'<p class="kpi-label">{label}</p>'
        f'<p class="kpi-value">{value}</p>'
        f'<span class="kpi-delta" style="color:{delta_color};">{arrow} {delta_text}</span>'
        f'<div class="kpi-bar" style="width:{bar_w}%;background:{bar_color};"></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_health_banner(status: str, avg_score: float, pass_rate: float, total: int, n_datasets: int):
    cfg = STATUS_CONFIG[status]
    st.markdown(
        f'<div class="health-banner" style="background:{cfg["bg"]};border-color:{cfg["color"]};">'
        f'<div class="hb-icon" style="color:{cfg["color"]};">{cfg["icon"]}</div>'
        f"<div>"
        f'<p class="hb-title" style="color:{cfg["color"]};">Data Health: {status}</p>'
        f'<p class="hb-detail" style="color:{COLORS["text_secondary"]};">'
        f'Average quality score <strong style="color:{COLORS["text_primary"]};">{avg_score:.1f}%</strong> '
        f'across <strong style="color:{COLORS["text_primary"]};">{total:,} checks</strong> '
        f'&nbsp;·&nbsp; Pass rate <strong style="color:{COLORS["text_primary"]};">{pass_rate:.1f}%</strong> '
        f"&nbsp;·&nbsp; {n_datasets} dataset(s) selected"
        f"</p>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# Bootstrap: load datasets & pipeline state
# =============================================================================

datasets_df = run_query_safe(GET_DATASETS, query_name="get_datasets")
pipeline_state = get_pipeline_state()

if datasets_df.empty:
    st.warning("No analytics data available. Run the ETL pipeline first.")
    st.info("Run `python main.py --mode full` from the data-engineering directory.")
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    # Logo / title
    st.markdown(
        '<div style="padding:0.5rem 0 1rem 0;">'
        f'<p style="font-size:1.15rem;font-weight:800;color:#1a2035;margin:0;"><span style="color:{COLORS["accent"]};">{_I["bar_chart"]}</span> DataPulse</p>'
        '<p style="font-size:0.72rem;color:#5a6478;margin:0;">Quality Monitoring Dashboard</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Navigation ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="sidebar-group-title" style="margin-bottom:0.4rem;">Navigation</div>',
        unsafe_allow_html=True,
    )
    if "active_section" not in st.session_state:
        st.session_state.active_section = "overview"

    for key, icon, label in NAV_SECTIONS:
        is_active = st.session_state.active_section == key
        if st.button(
            label,
            key=f"nav_{key}",
            help=f"Go to {label}",
            type="primary" if is_active else "secondary",
        ):
            st.session_state.active_section = key
            st.rerun()

    st.markdown("<hr style='margin:0.85rem 0;border-color:#e3e8f0;'>", unsafe_allow_html=True)

    # ── Filters ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="sidebar-group-title">Filters</div>',
        unsafe_allow_html=True,
    )

    # Refresh
    if st.button("Refresh Data", use_container_width=True):
        st.session_state["force_filter_reset"] = True
        st.rerun()

    st.markdown('<div style="height:0.4rem;"></div>', unsafe_allow_html=True)

    # Dataset
    with st.container():
        st.markdown(f'<p class="filter-label">{_I["folder"]} Datasets</p>', unsafe_allow_html=True)
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
            label_visibility="collapsed",
            help="Filter quality metrics by dataset",
        )

    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)

    # Date range
    with st.container():
        st.markdown(f'<p class="filter-label">{_I["calendar"]} Date Range</p>', unsafe_allow_html=True)
        date_df = run_query_safe(GET_DATE_RANGE, query_name="get_date_range")
        min_date = pd.to_datetime(date_df["min_d"].iloc[0]).date()
        max_date = pd.to_datetime(date_df["max_d"].iloc[0]).date()
        today_date = datetime.now().date()

        if "date_range_filter" in st.session_state:
            del st.session_state["date_range_filter"]
        if force_filter_reset or "start_date_filter" not in st.session_state:
            st.session_state["start_date_filter"] = min_date
        if force_filter_reset or "end_date_filter" not in st.session_state:
            st.session_state["end_date_filter"] = max_date

        col_s, col_e = st.columns(2)
        with col_s:
            start_date = st.date_input("From", key="start_date_filter", min_value=min_date, max_value=today_date)
        with col_e:
            end_date = st.date_input("To", key="end_date_filter", min_value=min_date, max_value=today_date)

        if start_date > end_date:
            st.warning("Invalid range — resetting.")
            st.session_state["start_date_filter"] = min_date
            st.session_state["end_date_filter"] = max_date
            st.rerun()
        if end_date > max_date:
            st.caption(f"No data beyond {max_date}.")

    st.markdown('<div style="height:0.3rem;"></div>', unsafe_allow_html=True)

    # Severity
    with st.container():
        st.markdown(f'<p class="filter-label">{_I["target"]} Severity</p>', unsafe_allow_html=True)
        severity_options = ["HIGH", "MEDIUM", "LOW"]
        if force_filter_reset or "severity_filter" not in st.session_state:
            st.session_state["severity_filter"] = severity_options.copy()
        selected_severities = st.multiselect(
            "Severity",
            severity_options,
            key="severity_filter",
            label_visibility="collapsed",
            help="HIGH=critical, MEDIUM=important, LOW=minor",
        )

    st.markdown("<hr style='margin:0.75rem 0;border-color:#e3e8f0;'>", unsafe_allow_html=True)

    # ── Pipeline Status ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-group-title">Pipeline Status</div>', unsafe_allow_html=True)
    if pipeline_state:
        last_run = pipeline_state.get("last_successful_run", "N/A")
        watermark = pipeline_state.get("high_watermark", "N/A")
        st.markdown(
            f'<div class="pipeline-ok">{_I["check"]} Last run: {last_run}<br>'
            f'<span style="font-weight:400;font-size:0.74rem;">Watermark: {watermark}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="pipeline-warn">{_I["warning"]} No ETL runs recorded yet</div>', unsafe_allow_html=True
        )

    st.markdown("<hr style='margin:0.75rem 0;border-color:#e3e8f0;'>", unsafe_allow_html=True)

    # Export format + session info
    st.markdown(f'<p class="filter-label">{_I["upload"]} Export Format</p>', unsafe_allow_html=True)
    export_format = st.selectbox("Export format", ["CSV", "Excel"], label_visibility="collapsed")
    st.caption(f"Session: {get_session_id()}")
    st.caption(f"Queries: {len(st.session_state.get('query_log', []))}")
    st.caption(f"Data: {min_date} → {max_date}")


# =============================================================================
# Input Validation
# =============================================================================

selected_ids = validate_ids(datasets_df[datasets_df["name"].isin(selected_datasets)]["id"].tolist())
selected_severities = validate_severities(selected_severities, ["HIGH", "MEDIUM", "LOW"])

# Gate
if not selected_ids:
    st.info("Select at least one dataset from the sidebar to begin analysis.")
    st.stop()
if not selected_severities:
    st.info("Select at least one severity level from the sidebar.")
    st.stop()

# =============================================================================
# Page-level header (always visible)
# =============================================================================

st.markdown(
    '<div class="page-header">'
    "<div>"
    f'<p class="page-title"><span style="color:{COLORS["accent"]};">{_I["bar_chart"]}</span> DataPulse Quality Dashboard</p>'
    '<p class="page-subtitle">Monitor data quality metrics, identify issues, and track trends across your datasets</p>'
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

active = st.session_state.active_section

# =============================================================================
# ── SECTION: Overview ────────────────────────────────────────────────────────
# =============================================================================

if active == "overview":
    render_section_header(
        _I["trend_up"],
        "Quality Overview",
        "High-level health snapshot for the selected datasets and date range.",
    )

    kpi_query, kpi_params = build_parameterized_query(
        KPI_OVERVIEW, selected_ids, start_date, end_date, selected_severities
    )
    kpi_df = run_query_safe(kpi_query, kpi_params, "kpi_overview")

    if not kpi_df.empty and kpi_df["total_checks"].iloc[0] > 0:
        total = int(kpi_df["total_checks"].iloc[0])
        passed = int(kpi_df["passed_checks"].iloc[0])
        failed = total - passed
        avg_score = float(kpi_df["avg_score"].iloc[0])
        min_score = float(kpi_df["min_score"].iloc[0])
        max_score = float(kpi_df["max_score"].iloc[0])
        pass_rate = passed / total * 100 if total > 0 else 0
        overall_status = get_quality_status(avg_score)

        render_health_banner(overall_status, avg_score, pass_rate, total, len(selected_datasets))

        # KPI Cards
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_kpi_card(
                "Total Checks",
                f"{total:,}",
                f"{len(selected_datasets)} dataset(s)",
                True,
                COLORS["info"],
                total / max(total, 1) * 100,
            )
        with c2:
            render_kpi_card(
                "Pass Rate",
                f"{pass_rate:.1f}%",
                f"{pass_rate - 90:+.1f}% vs 90% target",
                pass_rate >= 90,
                COLORS["healthy"] if pass_rate >= 90 else COLORS["critical"],
                pass_rate,
            )
        with c3:
            render_kpi_card(
                "Avg Score",
                f"{avg_score:.1f}%",
                f"Range {min_score:.0f}–{max_score:.0f}%",
                avg_score >= 90,
                get_status_color(overall_status),
                avg_score,
            )
        with c4:
            render_kpi_card(
                "Failed Checks",
                f"{failed:,}",
                f"{failed / total * 100:.1f}% of total" if total else "—",
                failed == 0,
                COLORS["critical"] if failed > 0 else COLORS["healthy"],
                failed / total * 100 if total else 0,
            )
        with c5:
            kpi_export = pd.DataFrame(
                {
                    "Metric": [
                        "Total Checks",
                        "Passed",
                        "Failed",
                        "Pass Rate %",
                        "Avg Score",
                        "Min Score",
                        "Max Score",
                    ],
                    "Value": [
                        total,
                        passed,
                        failed,
                        round(pass_rate, 1),
                        round(avg_score, 1),
                        round(min_score, 1),
                        round(max_score, 1),
                    ],
                }
            )
            st.markdown('<div style="padding-top:0.35rem;"></div>', unsafe_allow_html=True)
            create_download_button(kpi_export, "kpi_summary", "Export KPIs", export_format.lower())

        st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

        # Mini trend sparkline in overview
        sq, sp = build_parameterized_query(OVERVIEW_SPARK, selected_ids, start_date, end_date, selected_severities)
        spark_df = run_query_safe(sq, sp, "overview_spark")

        col_spark, col_action = st.columns([3, 1])
        with col_spark:
            st.markdown("#### Quality Score — Combined Trend")
            if not spark_df.empty:
                fig = go.Figure()
                # Shaded fill
                fig.add_trace(
                    go.Scatter(
                        x=spark_df["full_date"],
                        y=spark_df["avg_score"],
                        fill="tozeroy",
                        fillcolor="rgba(108,99,255,0.08)",
                        line=dict(color=COLORS["accent"], width=2.5),
                        mode="lines+markers",
                        marker=dict(size=5, color=COLORS["accent"]),
                        hovertemplate="<b>%{y:.1f}%</b> on %{x}<extra></extra>",
                        name="Avg Score",
                    )
                )
                fig = add_thresholds(fig)
                fig.update_layout(**base_layout("", "Date", "Quality Score (%)", yaxis_extra={"range": [0, 105]}))
                st.plotly_chart(fig, use_container_width=True)

        with col_action:
            st.markdown("#### Quick Actions")
            if st.button("View Detailed Trends", use_container_width=True):
                st.session_state.active_section = "trends"
                st.rerun()
            if st.button("Analyse Failures", use_container_width=True):
                st.session_state.active_section = "failures"
                st.rerun()
            if st.button("Compare Datasets", use_container_width=True):
                st.session_state.active_section = "comparison"
                st.rerun()
            if st.button("Field Issues", use_container_width=True):
                st.session_state.active_section = "fields"
                st.rerun()
            st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
            if overall_status == "Critical":
                st.error("Action required — quality is below critical threshold.")
            elif overall_status == "Warning":
                st.warning("Quality is below target. Review trend data.")
            else:
                st.success("All systems healthy.")
    else:
        st.warning("No quality check data found for the selected filters.")

# =============================================================================
# ── SECTION: Quality Trends ──────────────────────────────────────────────────
# =============================================================================

elif active == "trends":
    render_section_header(
        _I["trend_down"],
        "Quality Score Trends",
        "Track how data quality changes over time. Look for patterns and identify datasets needing attention.",
    )

    tq, tp = build_parameterized_query(QUALITY_TRENDS, selected_ids, start_date, end_date, selected_severities)
    trend_df = run_query_safe(tq, tp, "quality_trends")

    if not trend_df.empty:
        col_chart, col_ins = st.columns([3, 1])

        with col_chart:
            fig = px.line(
                trend_df,
                x="full_date",
                y="avg_score",
                color="dataset_name",
                markers=True,
                labels={"full_date": "Date", "avg_score": "Quality Score (%)", "dataset_name": "Dataset"},
                hover_data={"check_count": True},
                color_discrete_sequence=[
                    COLORS["accent"],
                    COLORS["info"],
                    COLORS["healthy"],
                    COLORS["warning"],
                    COLORS["critical"],
                ],
            )
            fig = add_thresholds(fig)
            fig.update_layout(
                **base_layout("Quality Score Over Time", "Date", "Avg Score (%)", yaxis_extra={"range": [0, 105]})
            )
            fig.update_traces(hovertemplate="<b>%{y:.1f}%</b><br>Checks: %{customdata[0]}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
            download_chart_data(trend_df, "quality_trends")

        with col_ins:
            st.markdown(f'#### {_I["lightbulb"]} Trend Insights', unsafe_allow_html=True)
            insights = []
            for ds in trend_df["dataset_name"].unique():
                ds_data = trend_df[trend_df["dataset_name"] == ds].sort_values("full_date")
                trend = calculate_trend(ds_data["avg_score"])
                latest = ds_data["avg_score"].iloc[-1] if len(ds_data) else 0
                insights.append({"name": ds, "trend": trend, "latest": latest})
            insights.sort(key=lambda x: x["trend"])

            for ins in insights:
                t, l, n = ins["trend"], ins["latest"], ins["name"]
                color = COLORS["healthy"] if t > 5 else (COLORS["critical"] if t < -5 else COLORS["info"])
                _arrow_svg = _I["trend_up"] if t > 5 else (_I["trend_down"] if t < -5 else _I["arrow_right"])
                arrow = f'<span style="color:{color};">{_arrow_svg}</span>'
                direction = f"{'Improving' if t>5 else 'Declining' if t<-5 else 'Stable'}: {t:+.1f}%"
                render_insight_card(f"{arrow} {n}", f"{direction} · Current: {l:.1f}%", color)
                if l < 70:
                    st.markdown(
                        f'<div style="background:#fff0f2;color:{COLORS["critical"]};'
                        f"border-radius:6px;padding:0.3rem 0.6rem;font-size:0.75rem;"
                        f'font-weight:600;margin:-0.3rem 0 0.4rem 0;">{_I["warning"]} Below critical threshold</div>',
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No trend data. Try adjusting the date range or datasets.")

# =============================================================================
# ── SECTION: Failure Analysis ────────────────────────────────────────────────
# =============================================================================

elif active == "failures":
    render_section_header(
        _I["search"],
        "Failure Analysis",
        "Understand where and why quality checks fail. Pinpoint rule types and severity levels requiring attention.",
    )

    col_rule, col_sev = st.columns(2)

    # --- Failure by Rule Type ---
    with col_rule:
        st.markdown("##### Failure Rate by Rule Type")
        st.caption("Which validation rules fail most often?")

        fq, fp = build_parameterized_query(FAILURE_BY_RULETYPE, selected_ids, start_date, end_date, selected_severities)
        failure_df = run_query_safe(fq, fp, "failure_by_ruletype")

        if not failure_df.empty:
            # Color each bar by severity bucket
            def _bar_color(rate):
                if rate >= 30:
                    return COLORS["critical"]
                if rate >= 10:
                    return COLORS["warning"]
                return COLORS["healthy"]

            failure_df["color"] = failure_df["failure_rate"].apply(_bar_color)
            fig = go.Figure(
                go.Bar(
                    x=failure_df["rule_type"],
                    y=failure_df["failure_rate"],
                    text=failure_df["failure_rate"].apply(lambda v: f"{v:.1f}%"),
                    textposition="outside",
                    marker_color=failure_df["color"],
                    hovertemplate="<b>%{x}</b><br>Failure rate: %{y:.1f}%<br>Total: %{customdata}<extra></extra>",
                    customdata=failure_df["total"],
                )
            )
            fig.update_layout(
                **base_layout(
                    "",
                    "Rule Type",
                    "Failure Rate (%)",
                    yaxis_extra={"range": [0, max(failure_df["failure_rate"].max() * 1.25, 15)]},
                ),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
            create_download_button(failure_df, "failure_by_ruletype", "Download", export_format.lower())

            max_rate = failure_df["failure_rate"].max()
            worst_rule = failure_df.iloc[0]["rule_type"]
            if max_rate > 30:
                render_insight_card(
                    f'<span style="color:{COLORS["critical"]};">{_I["alert"]}</span> High failure rate: {worst_rule}',
                    f"{max_rate:.1f}% failure rate — investigate data sources immediately.",
                    COLORS["critical"],
                )
            elif max_rate > 10:
                render_insight_card(
                    f'<span style="color:{COLORS["warning"]};">{_I["warning"]}</span> Elevated rate: {worst_rule}',
                    f"{max_rate:.1f}% — review recent data changes.",
                    COLORS["warning"],
                )
            else:
                render_insight_card(
                    f'<span style="color:{COLORS["healthy"]};">{_I["check"]}</span> All rules healthy',
                    "Failure rates below 10% across all rule types.",
                    COLORS["healthy"],
                )

    # --- Failure by Severity ---
    with col_sev:
        st.markdown("##### Checks by Severity Level")
        st.caption("Distribution of passed vs failed checks by severity")

        sq2, sp2 = build_parameterized_query(
            FAILURE_BY_SEVERITY, selected_ids, start_date, end_date, selected_severities
        )
        severity_df = run_query_safe(sq2, sp2, "failure_by_severity")

        if not severity_df.empty:
            severity_df["passed"] = severity_df["total"] - severity_df["failed"]
            sev_order = ["HIGH", "MEDIUM", "LOW"]
            severity_df["severity"] = pd.Categorical(severity_df["severity"], categories=sev_order, ordered=True)
            severity_df = severity_df.sort_values("severity")

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    name="Passed",
                    x=severity_df["severity"],
                    y=severity_df["passed"],
                    marker_color=COLORS["healthy"],
                    hovertemplate="Passed: %{y:,}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Bar(
                    name="Failed",
                    x=severity_df["severity"],
                    y=severity_df["failed"],
                    marker_color=COLORS["critical"],
                    hovertemplate="Failed: %{y:,}<extra></extra>",
                )
            )
            fig.update_layout(
                **base_layout("", "Severity Level", "Check Count"),
                barmode="stack",
            )
            st.plotly_chart(fig, use_container_width=True)
            create_download_button(severity_df, "failure_by_severity", "Download", export_format.lower())

            hi_fail = (
                severity_df[severity_df["severity"] == "HIGH"]["failed"].sum()
                if "HIGH" in severity_df["severity"].values
                else 0
            )
            md_fail = (
                severity_df[severity_df["severity"] == "MEDIUM"]["failed"].sum()
                if "MEDIUM" in severity_df["severity"].values
                else 0
            )
            if hi_fail > 0:
                render_insight_card(
                    f'<span style="color:{COLORS["critical"]};">{_I["alert"]}</span> HIGH severity failures',
                    f"{int(hi_fail)} critical failures require immediate attention.",
                    COLORS["critical"],
                )
            if md_fail > 10:
                render_insight_card(
                    f'<span style="color:{COLORS["warning"]};">{_I["warning"]}</span> MEDIUM severity failures',
                    f"{int(md_fail)} medium-severity failures to review.",
                    COLORS["warning"],
                )
            if hi_fail == 0 and md_fail <= 10:
                render_insight_card(
                    f'<span style="color:{COLORS["healthy"]};">{_I["check"]}</span> No critical failures',
                    "Severity distribution looks healthy.",
                    COLORS["healthy"],
                )

# =============================================================================
# ── SECTION: Dataset Comparison ──────────────────────────────────────────────
# =============================================================================

elif active == "comparison":
    render_section_header(
        _I["bar_chart"],
        "Dataset Quality Comparison",
        "Compare quality scores across datasets. Identify best and worst performers at a glance.",
    )

    cq, cp = build_parameterized_query(DATASET_COMPARISON, selected_ids, start_date, end_date, selected_severities)
    comparison_df = run_query_safe(cq, cp, "dataset_comparison")

    if not comparison_df.empty:
        comparison_df["pass_rate"] = round(comparison_df["passed"] / comparison_df["total_checks"] * 100, 1)
        comparison_df["quality_status"] = comparison_df["avg_score"].apply(get_quality_status)

        best = comparison_df.iloc[-1]
        worst = comparison_df.iloc[0]

        c_worst, c_best = st.columns(2)
        with c_worst:
            st.markdown(
                f'<div style="background:#fff0f2;padding:1rem 1.25rem;border-radius:12px;'
                f'border-left:4px solid {COLORS["critical"]};">'
                f'<p style="font-size:0.72rem;font-weight:700;color:{COLORS["critical"]};'
                f'text-transform:uppercase;letter-spacing:.05em;margin:0 0 .3rem 0;">{_I["arrow_down"]} Needs Attention</p>'
                f'<p style="font-size:1.15rem;font-weight:700;color:{COLORS["text_primary"]};margin:0;">{worst["dataset"]}</p>'
                f'<p style="font-size:0.82rem;color:{COLORS["text_secondary"]};margin:.2rem 0 0 0;">'
                f'Score: {worst["avg_score"]:.1f}% &nbsp;·&nbsp; Pass rate: {worst["pass_rate"]:.1f}%</p>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with c_best:
            st.markdown(
                f'<div style="background:#e6faf4;padding:1rem 1.25rem;border-radius:12px;'
                f'border-left:4px solid {COLORS["healthy"]};">'
                f'<p style="font-size:0.72rem;font-weight:700;color:{COLORS["healthy"]};'
                f'text-transform:uppercase;letter-spacing:.05em;margin:0 0 .3rem 0;">{_I["arrow_up"]} Top Performer</p>'
                f'<p style="font-size:1.15rem;font-weight:700;color:{COLORS["text_primary"]};margin:0;">{best["dataset"]}</p>'
                f'<p style="font-size:0.82rem;color:{COLORS["text_secondary"]};margin:.2rem 0 0 0;">'
                f'Score: {best["avg_score"]:.1f}% &nbsp;·&nbsp; Pass rate: {best["pass_rate"]:.1f}%</p>'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

        col_chart, col_list = st.columns([2, 1])

        with col_chart:
            clr_map = {"Critical": COLORS["critical"], "Warning": COLORS["warning"], "Healthy": COLORS["healthy"]}
            fig = px.bar(
                comparison_df,
                x="dataset",
                y="avg_score",
                text="avg_score",
                color="quality_status",
                color_discrete_map=clr_map,
                labels={"dataset": "Dataset", "avg_score": "Avg Score (%)", "quality_status": "Status"},
                hover_data={"pass_rate": True, "total_checks": True, "failed": True},
            )
            fig.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}%<br>"
                "Pass rate: %{customdata[0]:.1f}%<br>"
                "Total: %{customdata[1]:,}<br>"
                "Failed: %{customdata[2]:,}<extra></extra>",
            )
            fig.add_hline(
                y=90,
                line_dash="dot",
                line_color=COLORS["healthy"],
                line_width=1.5,
                annotation_text="Target",
                annotation_font_size=10,
            )
            fig.add_hline(
                y=70,
                line_dash="dot",
                line_color=COLORS["critical"],
                line_width=1.5,
                annotation_text="Critical",
                annotation_font_size=10,
            )
            fig.update_layout(**base_layout("", "Dataset", "Avg Score (%)", yaxis_extra={"range": [0, 108]}))
            st.plotly_chart(fig, use_container_width=True)

        with col_list:
            st.markdown(f'#### {_I["clipboard"]} Quality Assessment', unsafe_allow_html=True)
            for _, row in comparison_df.sort_values("avg_score").iterrows():
                status = row["quality_status"]
                sc = get_status_color(status)
                icon = get_status_icon(status)
                var_note = f" · Var: {row['score_std']:.1f}" if row["score_std"] and row["score_std"] > 15 else ""
                st.markdown(
                    f'<div class="cmp-row">'
                    f"<div>"
                    f'<p class="cmp-name">{icon} {row["dataset"]}</p>'
                    f'<p style="font-size:0.74rem;color:{COLORS["text_secondary"]};margin:0;">'
                    f'Pass: {row["pass_rate"]:.1f}%{var_note}</p>'
                    f"</div>"
                    f'<span class="cmp-score" style="color:{sc};">{row["avg_score"]}%</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown(f'##### {_I["clipboard"]} Full Comparison Table', unsafe_allow_html=True)
        disp = comparison_df[["dataset", "avg_score", "pass_rate", "total_checks", "failed", "quality_status"]].copy()
        disp.columns = ["Dataset", "Avg Score (%)", "Pass Rate (%)", "Total Checks", "Failed", "Status"]
        st.dataframe(disp, use_container_width=True, hide_index=True)
        download_chart_data(comparison_df, "dataset_comparison")
    else:
        st.info("No comparison data for selected filters.")

# =============================================================================
# ── SECTION: Field-Level Issues ───────────────────────────────────────────────
# =============================================================================

elif active == "fields":
    render_section_header(
        _I["target"],
        "Field-Level Quality Issues",
        "Drill down to specific fields causing failures. "
        "Treemap area = failure volume; colour = severity (red=HIGH, amber=MEDIUM, blue=LOW).",
    )

    fq, fp = build_parameterized_query(FIELD_QUALITY_ISSUES, selected_ids, start_date, end_date, selected_severities)
    field_df = run_query_safe(fq, fp, "field_quality_issues")

    if not field_df.empty:
        col_tree, col_list = st.columns([2, 1])

        with col_tree:
            fig = px.treemap(
                field_df,
                path=["field_name", "rule_type"],
                values="failures",
                color="severity",
                color_discrete_map={"HIGH": COLORS["critical"], "MEDIUM": COLORS["warning"], "LOW": COLORS["info"]},
                hover_data=["failure_rate", "total_checks"],
            )
            fig.update_layout(
                title=dict(
                    text="Failure Volume by Field & Rule Type", font=dict(size=13, color=COLORS["text_primary"])
                ),
                margin=dict(l=0, r=0, t=40, b=0),
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>Failures: %{value:,}<br>"
                "Failure Rate: %{customdata[0]:.1f}%<extra></extra>"
            )
            st.plotly_chart(fig, use_container_width=True)
            create_download_button(field_df, "field_quality_issues", "Download", export_format.lower())

        with col_list:
            st.markdown(f'#### {_I["search"]} Top Problem Fields', unsafe_allow_html=True)
            st.caption("Sorted by failure count — fix these first.")

            # Build all pills as one HTML block inside a scrollable container
            pills_html = ""
            for _, row in field_df.iterrows():
                sc = (
                    COLORS["critical"]
                    if row["severity"] == "HIGH"
                    else (COLORS["warning"] if row["severity"] == "MEDIUM" else COLORS["info"])
                )
                pills_html += (
                    f'<div class="field-pill" style="border-color:{sc};">'
                    f'<p class="fp-name">{row["field_name"]}</p>'
                    f'<p class="fp-meta">'
                    f'{row["rule_type"]} &nbsp;·&nbsp; {int(row["failures"])} failures '
                    f'({row["failure_rate"]:.1f}%) &nbsp;·&nbsp; '
                    f'<span style="color:{sc};font-weight:700;">{row["severity"]}</span>'
                    f"</p>"
                    f"</div>"
                )
            st.markdown(
                f'<div style="max-height:340px; overflow-y:auto; padding-right:4px;">' f"{pills_html}" f"</div>",
                unsafe_allow_html=True,
            )

            if field_df["severity"].iloc[0] == "HIGH":
                render_insight_card(
                    f'<span style="color:{COLORS["critical"]};">{_I["alert"]}</span> Top field is HIGH severity',
                    f"'{field_df.iloc[0]['field_name']}' has {int(field_df.iloc[0]['failures'])} "
                    f"failures at {field_df.iloc[0]['failure_rate']:.1f}% — prioritise immediately.",
                    COLORS["critical"],
                )
    else:
        st.success("No field-level failures detected for the selected filters.")

# =============================================================================
# ── SECTION: Day-of-Week Patterns ────────────────────────────────────────────
# =============================================================================

elif active == "dow":
    render_section_header(
        _I["calendar"],
        "Quality Patterns by Day of Week",
        "Detect if quality varies by day — useful for spotting weekend batch issues or specific pipeline schedules.",
    )

    dq, dp = build_parameterized_query(QUALITY_BY_DOW, selected_ids, start_date, end_date, selected_severities)
    dow_df = run_query_safe(dq, dp, "quality_by_dow")

    if not dow_df.empty:
        dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        dow_df["day_name"] = dow_df["day_of_week"].apply(lambda x: dow_names[x] if x < 7 else "Unknown")

        col_chart, col_ins = st.columns([3, 1])

        with col_chart:
            dow_df["color"] = dow_df["avg_score"].apply(
                lambda s: COLORS["critical"] if s < 70 else (COLORS["warning"] if s < 90 else COLORS["healthy"])
            )
            fig = go.Figure(
                go.Bar(
                    x=dow_df["day_name"],
                    y=dow_df["avg_score"],
                    text=dow_df["avg_score"].apply(lambda v: f"{v:.1f}%"),
                    textposition="outside",
                    marker_color=dow_df["color"],
                    hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}%<br>Checks: %{customdata}<extra></extra>",
                    customdata=dow_df["check_count"],
                )
            )
            fig = add_thresholds(fig)
            fig.update_layout(
                **base_layout("Average Quality Score by Day", "Day", "Avg Score (%)", yaxis_extra={"range": [0, 108]}),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
            download_chart_data(dow_df, "quality_by_dow")

        with col_ins:
            st.markdown(f'#### {_I["lightbulb"]} Pattern Insights', unsafe_allow_html=True)
            wi = dow_df["avg_score"].idxmin()
            bi = dow_df["avg_score"].idxmax()
            wd = dow_df.loc[wi, "day_name"]
            bd = dow_df.loc[bi, "day_name"]
            ws = dow_df.loc[wi, "avg_score"]
            bs = dow_df.loc[bi, "avg_score"]
            var = dow_df["avg_score"].std()

            _wc = COLORS["critical"] if ws < 70 else COLORS["warning"]
            render_insight_card(
                f'<span style="color:{COLORS["healthy"]};">{_I["trend_up"]}</span> Best day: {bd}',
                f"Average score {bs:.1f}%",
                COLORS["healthy"],
            )
            render_insight_card(
                f'<span style="color:{_wc};">{_I["trend_down"]}</span> Worst day: {wd}', f"Average score {ws:.1f}%", _wc
            )

            if var > 5:
                render_insight_card(
                    f'<span style="color:{COLORS["warning"]};">{_I["warning"]}</span> High day variance ({var:.1f})',
                    f"Quality differs significantly across days — investigate pipelines running on {wd}.",
                    COLORS["warning"],
                )
            else:
                render_insight_card(
                    f'<span style="color:{COLORS["healthy"]};">{_I["check"]}</span> Stable across days (std {var:.1f})',
                    "Quality is consistent throughout the week.",
                    COLORS["healthy"],
                )
    else:
        st.info("No day-of-week data for selected filters.")

# =============================================================================
# ── SECTION: Export Report ────────────────────────────────────────────────────
# =============================================================================

elif active == "export":
    render_section_header(
        _I["upload"],
        "Export Full Report",
        "Download all dashboard data for offline analysis or sharing with stakeholders.",
    )

    # Re-fetch all datasets needed for export
    def _fetch_all():
        _bpq = build_parameterized_query
        _args = (selected_ids, start_date, end_date, selected_severities)

        kpi_q, kpi_p = _bpq(KPI_OVERVIEW, *_args)
        tq, tp = _bpq(QUALITY_TRENDS, *_args)
        fq, fp = _bpq(FAILURE_BY_RULETYPE, *_args)
        cq, cp = _bpq(DATASET_COMPARISON, *_args)
        ffq, ffp = _bpq(FIELD_QUALITY_ISSUES, *_args)
        dq, dp = _bpq(QUALITY_BY_DOW, *_args)

        return {
            "kpi_summary": run_query_safe(kpi_q, kpi_p, "export_kpi"),
            "quality_trends": run_query_safe(tq, tp, "export_trends"),
            "failure_analysis": run_query_safe(fq, fp, "export_failures"),
            "dataset_comparison": run_query_safe(cq, cp, "export_comparison"),
            "field_issues": run_query_safe(ffq, ffp, "export_fields"),
            "day_of_week": run_query_safe(dq, dp, "export_dow"),
        }

    col_csv, col_excel, col_json = st.columns(3)

    with col_csv:
        st.markdown(f'##### {_I["bar_chart"]} Combined CSV', unsafe_allow_html=True)
        st.caption("All sections exported as a single CSV file with section separators.")
        if st.button("Generate CSV", width="stretch"):
            all_data = _fetch_all()
            combined = ""
            for name, df in all_data.items():
                if not df.empty:
                    combined += f"\n\n=== {name.upper()} ===\n"
                    combined += df.to_csv(index=False)
            st.download_button(
                "Download Combined CSV",
                combined,
                file_name=f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    with col_excel:
        st.markdown(f'##### {_I["trend_up"]} Multi-Sheet Excel', unsafe_allow_html=True)
        st.caption("Each section in a separate worksheet — ideal for stakeholder sharing.")
        if st.button("Generate Excel", width="stretch"):
            all_data = _fetch_all()
            try:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    sheet_map = {
                        "quality_trends": "Trends",
                        "failure_analysis": "Failures",
                        "dataset_comparison": "Comparison",
                        "field_issues": "Field_Issues",
                        "day_of_week": "Day_of_Week",
                        "kpi_summary": "KPI_Summary",
                    }
                    for key, sheet in sheet_map.items():
                        df = all_data.get(key, pd.DataFrame())
                        if not df.empty:
                            df.to_excel(writer, sheet_name=sheet, index=False)
                st.download_button(
                    "Download Excel Workbook",
                    buf.getvalue(),
                    file_name=f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except ImportError:
                st.warning("Install openpyxl: `pip install openpyxl`")

    with col_json:
        st.markdown(f'##### {_I["clipboard"]} JSON Summary', unsafe_allow_html=True)
        st.caption("Compact machine-readable summary for integration with other tools.")
        if st.button("Generate JSON", width="stretch"):
            kpi_data = _fetch_all()["kpi_summary"]
            avg_s = float(kpi_data["avg_score"].iloc[0]) if not kpi_data.empty else 0
            total_c = int(kpi_data["total_checks"].iloc[0]) if not kpi_data.empty else 0
            passed_c = int(kpi_data["passed_checks"].iloc[0]) if not kpi_data.empty else 0
            summary = {
                "report_generated": datetime.now().isoformat(),
                "filters": {
                    "datasets": selected_datasets,
                    "severities": selected_severities,
                    "date_range": {"start": str(start_date), "end": str(end_date)},
                },
                "overall_health": {
                    "status": get_quality_status(avg_s),
                    "avg_score": round(avg_s, 1),
                },
                "kpi": {
                    "total_checks": total_c,
                    "passed_checks": passed_c,
                    "failed_checks": total_c - passed_c,
                    "pass_rate": round(passed_c / total_c * 100, 1) if total_c else 0,
                    "avg_score": round(avg_s, 1),
                    "min_score": round(float(kpi_data["min_score"].iloc[0]), 1) if not kpi_data.empty else 0,
                    "max_score": round(float(kpi_data["max_score"].iloc[0]), 1) if not kpi_data.empty else 0,
                },
            }
            st.download_button(
                "Download JSON Summary",
                json.dumps(summary, indent=2),
                file_name=f"quality_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

# =============================================================================
# Footer (always visible)
# =============================================================================

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns(3)
with fc1:
    st.caption(f"Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with fc2:
    st.caption(f"Session: {get_session_id()}")
with fc3:
    st.caption(f"Queries executed: {len(st.session_state.get('query_log', []))}")

st.markdown(
    '<div style="text-align:center;color:#8392a5;padding:0.75rem 0 0.5rem;font-size:0.8rem;">'
    "<strong>DataPulse Quality Dashboard</strong> &nbsp;·&nbsp; Monitor &nbsp;·&nbsp; "
    "Analyse &nbsp;·&nbsp; Improve"
    "</div>",
    unsafe_allow_html=True,
)
