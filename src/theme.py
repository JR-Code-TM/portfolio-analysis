"""Theme C — Modern Fintech: soft white bg, indigo/teal accents, card shadows.
Dark variant: deep navy bg, slate card surfaces, lighter indigo accents.
"""
from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Light theme CSS
# ---------------------------------------------------------------------------
LIGHT_CSS = """
<style>
/* ── App background ─────────────────────────────────────────────────── */
.stApp {
    background-color: #f8f9ff;
}

/* ── Sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label {
    color: #1e293b;
}

/* ── Navigation links in sidebar ────────────────────────────────────── */
[data-testid="stSidebarNavLink"] {
    border-radius: 8px;
    margin: 2px 4px;
    color: #475569;
    font-weight: 500;
}
[data-testid="stSidebarNavLink"]:hover {
    background-color: #eef2ff;
    color: #6366f1;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background-color: #eef2ff;
    color: #6366f1;
    font-weight: 600;
}

/* ── Metric cards ────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 6px rgba(99, 102, 241, 0.07) !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    color: #1e293b !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDeltaPositive"] {
    color: #0d9488 !important;
    font-weight: 600;
}
[data-testid="stMetricDeltaNegative"] {
    color: #e11d48 !important;
    font-weight: 600;
}

/* ── Input fields ────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: #1e293b !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* ── Selectbox ───────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: #1e293b !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* ── Primary buttons ────────────────────────────────────────────────── */
button[kind="primary"] {
    background-color: #6366f1 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}
button[kind="primary"]:hover {
    background-color: #4f46e5 !important;
}
button[kind="secondary"] {
    border-color: #6366f1 !important;
    color: #6366f1 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton button {
    white-space: nowrap !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
[data-testid="stTab"] {
    color: #64748b;
    font-weight: 500;
}
[data-testid="stTab"][aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
    font-weight: 600;
}

/* ── Expanders ───────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    background: #ffffff !important;
}

/* ── Headings ────────────────────────────────────────────────────────── */
h1 { color: #1e293b !important; font-weight: 700 !important; }
h2 { color: #1e293b !important; font-weight: 600 !important; }
h3 { color: #334155 !important; font-weight: 600 !important; }

/* ── Dividers ────────────────────────────────────────────────────────── */
hr { border-color: #e2e8f0 !important; opacity: 0.7; }

/* ── Dataframe ───────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
}
</style>
"""

# ---------------------------------------------------------------------------
# Dark theme CSS
# ---------------------------------------------------------------------------
DARK_CSS = """
<style>
/* ── App background ─────────────────────────────────────────────────── */
.stApp {
    background-color: #0f172a;
    color: #f1f5f9;
}

/* ── Sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #1e293b !important;
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}

/* ── Navigation links in sidebar ────────────────────────────────────── */
[data-testid="stSidebarNavLink"] {
    border-radius: 8px;
    margin: 2px 4px;
    color: #94a3b8;
    font-weight: 500;
}
[data-testid="stSidebarNavLink"]:hover {
    background-color: #312e81;
    color: #a5b4fc;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background-color: #312e81;
    color: #a5b4fc;
    font-weight: 600;
}

/* ── Metric cards ────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 6px rgba(0, 0, 0, 0.3) !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDeltaPositive"] {
    color: #14b8a6 !important;
    font-weight: 600;
}
[data-testid="stMetricDeltaNegative"] {
    color: #fb7185 !important;
    font-weight: 600;
}

/* ── Input fields ────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border: 1.5px solid #334155 !important;
    border-radius: 8px !important;
    background: #0f172a !important;
    color: #f1f5f9 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.15) !important;
}

/* ── Selectbox ───────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    border: 1.5px solid #334155 !important;
    border-radius: 8px !important;
    background: #0f172a !important;
    color: #f1f5f9 !important;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.15) !important;
}

/* ── Primary buttons ────────────────────────────────────────────────── */
button[kind="primary"] {
    background-color: #818cf8 !important;
    border: none !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}
button[kind="primary"]:hover {
    background-color: #6366f1 !important;
    color: #ffffff !important;
}
button[kind="secondary"] {
    border-color: #818cf8 !important;
    color: #818cf8 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton button {
    white-space: nowrap !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
[data-testid="stTab"] {
    color: #94a3b8;
    font-weight: 500;
}
[data-testid="stTab"][aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8 !important;
    font-weight: 600;
}

/* ── Expanders ───────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    background: #1e293b !important;
}

/* ── Headings ────────────────────────────────────────────────────────── */
h1 { color: #f1f5f9 !important; font-weight: 700 !important; }
h2 { color: #e2e8f0 !important; font-weight: 600 !important; }
h3 { color: #cbd5e1 !important; font-weight: 600 !important; }
p, span, label, .stMarkdown {
    color: #cbd5e1 !important;
}

/* ── Dividers ────────────────────────────────────────────────────────── */
hr { border-color: #334155 !important; opacity: 0.7; }

/* ── Dataframe ───────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #334155;
    border-radius: 10px;
    overflow: hidden;
}
</style>
"""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def apply_theme() -> None:
    """Inject the appropriate CSS for the current theme into the page."""
    css = DARK_CSS if st.session_state.get("theme") == "dark" else LIGHT_CSS
    st.markdown(css, unsafe_allow_html=True)


def get_plotly_template() -> str:
    return "plotly_dark" if st.session_state.get("theme") == "dark" else "plotly_white"


def get_plotly_bg_color() -> str:
    return "#0f172a" if st.session_state.get("theme") == "dark" else "#f8f9ff"
