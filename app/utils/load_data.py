"""
load_data.py
------------
Single source of truth for loading the app-ready CSVs.
All pages import from here. Uses Streamlit's cache_data so every page load
is cheap.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

APP_ROOT = Path(__file__).resolve().parent.parent
APP_READY = APP_ROOT / "data" / "app_ready"
SIM_DIR = APP_ROOT / "data" / "simulation"
RAW_DIR = APP_ROOT / "data" / "raw"


@st.cache_data(show_spinner=False)
def load_kpis() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_kpis.csv")


@st.cache_data(show_spinner=False)
def load_country_summary() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_country_summary.csv")


@st.cache_data(show_spinner=False)
def load_venue_summary() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_venue_summary.csv")


@st.cache_data(show_spinner=False)
def load_venue_stage_revenue() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_venue_stage_revenue.csv")


@st.cache_data(show_spinner=False)
def load_stage_summary() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_stage_summary.csv")


@st.cache_data(show_spinner=False)
def load_model_comparison() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_model_comparison.csv")


@st.cache_data(show_spinner=False)
def load_feature_importance_main() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_feature_importance_main.csv")


@st.cache_data(show_spinner=False)
def load_feature_importance_attendance() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_feature_importance_attendance.csv")


@st.cache_data(show_spinner=False)
def load_feature_importance_benchmark() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_feature_importance_benchmark.csv")


@st.cache_data(show_spinner=False)
def load_assumptions() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_assumptions.csv")


@st.cache_data(show_spinner=False)
def load_teams() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_teams.csv")


@st.cache_data(show_spinner=False)
def load_draw_probabilities() -> pd.DataFrame:
    return pd.read_csv(SIM_DIR / "app_draw_probabilities.csv")


@st.cache_data(show_spinner=False)
def load_matchup_summary() -> pd.DataFrame:
    return pd.read_csv(SIM_DIR / "app_matchup_summary.csv")


@st.cache_data(show_spinner=False)
def load_simulation_summary() -> pd.DataFrame:
    return pd.read_csv(SIM_DIR / "app_simulation_summary.csv")


@st.cache_data(show_spinner=False)
def load_policy_scenarios() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_policy_scenarios.csv")


@st.cache_data(show_spinner=False)
def load_policy_venue_revenue() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_policy_venue_revenue.csv")


@st.cache_data(show_spinner=False)
def load_policy_country_revenue() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_policy_country_revenue.csv")


@st.cache_data(show_spinner=False)
def load_revenue_lookup() -> pd.DataFrame:
    return pd.read_csv(APP_READY / "app_revenue_lookup.csv")


@st.cache_data(show_spinner=False)
def load_manifest() -> dict:
    path = APP_READY / "manifest.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)
