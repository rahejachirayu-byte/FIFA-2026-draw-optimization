"""
3_Venue_Revenue_Optimization.py
--------------------------------
How our projected ticket revenue distributes across countries, venues, and stages —
and which features our primary model says matter most.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from utils.helpers import (  # noqa: E402
    configure_page, section, kpi_card, callout, interp,
    sidebar_context_panel,
    COUNTRY_COLORS, STAGE_COLORS, COLOR_PRIMARY, COLOR_ACCENT,
)
from utils.load_data import (  # noqa: E402
    load_venue_summary, load_venue_stage_revenue, load_stage_summary,
    load_country_summary, load_model_comparison, load_assumptions,
    load_feature_importance_main, load_feature_importance_attendance,
    load_feature_importance_benchmark,
)
from utils.formatters import fmt_currency, fmt_currency_full  # noqa: E402


configure_page(
    title="Venue & Revenue Optimization",
    subtitle=(
        "How our projected ticket revenue distributes across countries, venues, and "
        "stages — and which signals our primary model identifies as the real demand drivers."
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
venues = load_venue_summary()
venue_stage = load_venue_stage_revenue()
stages = load_stage_summary()
countries = load_country_summary()
metrics = load_model_comparison()
assumptions = load_assumptions()
fi_main = load_feature_importance_main()
fi_att = load_feature_importance_attendance()
fi_bench = load_feature_importance_benchmark()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar filters
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    country_options = sorted(venues["country"].unique())
    sel_countries = st.multiselect(
        "Country",
        country_options,
        default=country_options,
    )
    sel_stages = st.multiselect(
        "Stage",
        options=stages["stage"].tolist(),
        default=stages["stage"].tolist(),
    )
    sel_scenario = st.radio(
        "Revenue scenario",
        options=["Base", "Low", "High"],
        index=0,
        help="Applies a ±20% band on projected per-match revenue.",
    )
    sel_model = st.selectbox(
        "Feature-importance model",
        options=[
            "Main model · revenue_proxy_no_stage_feature",
            "Benchmark · revenue_proxy_full (with stage_detail)",
            "Sensitivity check · attendance_signal_model",
        ],
        index=0,
    )

sidebar_context_panel()

scen_col_map = {"Base": "base", "Low": "low", "High": "high"}
scen = scen_col_map[sel_scenario]
venue_col = f"total_revenue_{scen}_usd"
country_col = f"total_revenue_{scen}_usd"
vs_total_col = f"total_{scen}_usd"
vs_per_col = f"per_match_{scen}_usd"


# ─────────────────────────────────────────────────────────────────────────────
# Apply filters
# ─────────────────────────────────────────────────────────────────────────────
venues_f = venues[venues["country"].isin(sel_countries)].copy()
venue_stage_f = venue_stage[
    venue_stage["country"].isin(sel_countries) & venue_stage["stage"].isin(sel_stages)
].copy()
countries_f = countries[countries["country"].isin(sel_countries)].copy()


# ─────────────────────────────────────────────────────────────────────────────
# Top KPIs
# ─────────────────────────────────────────────────────────────────────────────
total_rev = venue_stage_f[vs_total_col].sum()
n_venues = venues_f.shape[0]
n_matches = venue_stage_f["n_matches"].sum()

cols = st.columns(4)
with cols[0]:
    kpi_card(
        "Projected revenue",
        fmt_currency(total_rev, precision=2),
        sub=f"{sel_scenario} · {int(n_matches)} matches",
        accent=True,
    )
with cols[1]:
    top_v = venues_f.sort_values(venue_col, ascending=False).iloc[0] if n_venues else None
    kpi_card(
        "Top venue (filtered)",
        top_v["venue"] if top_v is not None else "—",
        sub=f"{fmt_currency(top_v[venue_col])}" if top_v is not None else "—",
    )
with cols[2]:
    if not countries_f.empty:
        top_c = countries_f.sort_values(country_col, ascending=False).iloc[0]
        kpi_card(
            "Top country (filtered)",
            top_c["country"],
            sub=fmt_currency(top_c[country_col]),
        )
    else:
        kpi_card("Top country (filtered)", "—", "—")
with cols[3]:
    kpi_card(
        "Venues in view",
        f"{n_venues}",
        sub="Out of 16 total",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Venue ranking
# ─────────────────────────────────────────────────────────────────────────────
section("Venue ranking", "PROJECTED REVENUE BY VENUE")

if venues_f.empty:
    st.info("No venues match the current filters.")
else:
    # Recompute venue totals using only filtered stages
    venue_stage_totals = (
        venue_stage_f.groupby(["venue", "country"], as_index=False)[vs_total_col].sum()
        .sort_values(vs_total_col, ascending=False)
    )
    fig = px.bar(
        venue_stage_totals.iloc[::-1],
        x=vs_total_col,
        y="venue",
        color="country",
        color_discrete_map=COUNTRY_COLORS,
        orientation="h",
        text=venue_stage_totals.iloc[::-1][vs_total_col].map(
            lambda v: fmt_currency(v, precision=1)
        ),
        labels={vs_total_col: "Projected revenue (USD)", "venue": "", "country": "Country"},
        height=max(360, 30 * len(venue_stage_totals)),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(margin=dict(l=10, r=80, t=10, b=40))
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)
    interp(
        "The largest-capacity US venues (MetLife, AT&T, Mercedes-Benz) lead under every "
        "scenario. Canadian and Mexican venues project lower revenue primarily because "
        "of capacity, not demand — a key point for policy discussions."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Country & stage views side by side
# ─────────────────────────────────────────────────────────────────────────────
section("Where revenue lands: country & stage", "DISTRIBUTION")

c1, c2 = st.columns(2, gap="large")

with c1:
    st.markdown("**Revenue by country**")
    country_totals = (
        venue_stage_f.groupby("country", as_index=False)[vs_total_col].sum()
        .sort_values(vs_total_col, ascending=False)
    )
    fig = px.bar(
        country_totals,
        x="country", y=vs_total_col,
        color="country",
        color_discrete_map=COUNTRY_COLORS,
        text=country_totals[vs_total_col].map(lambda v: fmt_currency(v, precision=2)),
        labels={"country": "Country", vs_total_col: "Projected revenue"},
        height=360,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=30), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    if not country_totals.empty:
        top_share = country_totals.iloc[0][vs_total_col] / country_totals[vs_total_col].sum()
        interp(
            f"{country_totals.iloc[0]['country']} accounts for "
            f"{top_share * 100:.1f}% of projected revenue in the current filter."
        )

with c2:
    st.markdown("**Revenue by stage**")
    stage_totals = (
        venue_stage_f.groupby("stage", as_index=False)[vs_total_col].sum()
    )
    # Sort by stage order in the stages table
    stage_order = [s for s in stages["stage"].tolist() if s in stage_totals["stage"].values]
    stage_totals["stage_order"] = stage_totals["stage"].map({s: i for i, s in enumerate(stage_order)})
    stage_totals = stage_totals.sort_values("stage_order")
    fig = px.bar(
        stage_totals,
        x="stage", y=vs_total_col,
        color="stage",
        color_discrete_map=STAGE_COLORS,
        text=stage_totals[vs_total_col].map(lambda v: fmt_currency(v, precision=1)),
        labels={"stage": "Stage", vs_total_col: "Projected revenue"},
        height=360,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=60), showlegend=False)
    fig.update_xaxes(tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)
    interp(
        "The group stage contributes the largest aggregate revenue because of volume "
        "(72 matches); per-match revenue rises sharply through the knockout rounds."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Model comparison + feature importance
# ─────────────────────────────────────────────────────────────────────────────
section("Our revenue model — performance & feature importance", "MODEL VIEW")

mc1, mc2 = st.columns([2, 3], gap="large")

with mc1:
    st.markdown("**Our executed-model scorecard**")
    # Focus on revenue_proxy_full as the comparison view (that's what was executed)
    rev = metrics[metrics["target"] == "revenue_proxy"].copy()
    rev["Model"] = rev["model"].str.replace("_", " ").str.title()
    rev["RMSE ($M)"] = (rev["rmse"] / 1_000_000).round(2)
    fig = px.bar(
        rev.sort_values("RMSE ($M)", ascending=False),
        x="RMSE ($M)", y="Model",
        orientation="h",
        color_discrete_sequence=[COLOR_PRIMARY],
        text=rev.sort_values("RMSE ($M)", ascending=False)["RMSE ($M)"].map(
            lambda v: f"${v:.2f}M"
        ),
        labels={"Model": "", "RMSE ($M)": "RMSE — lower is better"},
        height=260,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(margin=dict(l=10, r=80, t=10, b=40))
    st.plotly_chart(fig, use_container_width=True)

    att = metrics[metrics["target"] == "attendance"].copy()
    att["Model"] = att["model"].str.replace("_", " ").str.title()
    att["RMSE (attendees)"] = att["rmse"].astype(int)
    fig2 = px.bar(
        att.sort_values("RMSE (attendees)", ascending=False),
        x="RMSE (attendees)", y="Model",
        orientation="h",
        color_discrete_sequence=[COLOR_ACCENT],
        text=att.sort_values("RMSE (attendees)", ascending=False)["RMSE (attendees)"].map(
            lambda v: f"{v:,}"
        ),
        labels={"Model": "", "RMSE (attendees)": "Attendance RMSE"},
        height=260,
    )
    fig2.update_traces(textposition="outside", cliponaxis=False)
    fig2.update_layout(margin=dict(l=10, r=80, t=10, b=40))
    st.plotly_chart(fig2, use_container_width=True)
    interp(
        "Tree models (XGBoost, Random Forest) meaningfully outperform the linear baseline "
        "on both targets. Our revenue-proxy R² is high mostly because stage pricing is "
        "embedded in the target — see Methodology for why we demote that spec."
    )

with mc2:
    if sel_model.startswith("Main"):
        df = fi_main.copy()
        title = "Our primary model · revenue_proxy_no_stage_feature"
        note = (
            "Derived from the executed XGBoost ranking with the mechanical "
            "`stage_detail` feature removed. This is the view we use to explain "
            "what actually drives revenue — the signals a planning committee can act on."
        )
    elif sel_model.startswith("Benchmark"):
        df = fi_bench.copy()
        title = "Benchmark reference · revenue_proxy_full (diagnostic only)"
        note = (
            "Shown for completeness only. `stage_detail` dominates because stage-level "
            "pricing is mechanically embedded in the target. We demote this spec to "
            "appendix status — it does not represent causal revenue drivers."
        )
    else:
        df = fi_att.copy()
        title = "Sensitivity check · attendance_signal_model"
        note = (
            "Our attendance-only sanity check confirms that the same structural features "
            "emerge in the demand-side view before any pricing is layered on top."
        )

    df_plot = df.head(10).copy()
    df_plot["Feature"] = df_plot["feature"].str.replace("_", " ")
    df_plot["Share"] = df_plot["share_of_total"] * 100

    st.markdown(f"**{title}**")
    fig = px.bar(
        df_plot.iloc[::-1],
        x="Share", y="Feature",
        orientation="h",
        color="feature_bucket",
        color_discrete_map={
            "Structural": COLOR_PRIMARY,
            "Proxy": "#9AB3C9",
            "Mechanical": "#C8102E",
            "Weak": "#C4C9D1",
        },
        text=df_plot.iloc[::-1]["Share"].map(lambda v: f"{v:.1f}%"),
        labels={"Share": "Share of model importance", "feature_bucket": "Signal type"},
        height=520,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%")
    fig.update_layout(margin=dict(l=10, r=60, t=10, b=60),
                      legend=dict(orientation="h", y=-0.12))
    st.plotly_chart(fig, use_container_width=True)
    interp(note)


# ─────────────────────────────────────────────────────────────────────────────
# Plain-language interpretation of top features
# ─────────────────────────────────────────────────────────────────────────────
section("What our model learned — plain-language interpretation", "NARRATIVE")

top_main = fi_main.head(5)
for _, row in top_main.iterrows():
    st.markdown(
        f"**{row['feature'].replace('_', ' ').title()}** "
        f"*({row['feature_bucket']})* — {row['interpretation']}. "
        f"Share of main-model importance: {row['share_of_total'] * 100:.1f}%."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Assumptions panel
# ─────────────────────────────────────────────────────────────────────────────
section("Assumptions & modeling guardrails", "TRANSPARENCY")

# Pull the stage price table from assumptions
stage_prices = assumptions[assumptions["assumption_group"] == "stage_price"].copy()
stage_prices = stage_prices.rename(columns={"assumption": "Stage", "value": "Assumed price (USD)"})
stage_prices = stage_prices[["Stage", "Assumed price (USD)"]]

ap1, ap2 = st.columns([2, 3], gap="large")
with ap1:
    st.markdown("**Stage ticket-price assumptions**")
    st.dataframe(stage_prices, use_container_width=True, hide_index=True)
    interp("These prices drive the proxy revenue target and are assumed, not observed.")

with ap2:
    guardrails = assumptions[
        ~assumptions["assumption_group"].isin(["stage_price"])
    ][["assumption_group", "assumption", "value", "presentation_guidance"]]
    guardrails.columns = ["Group", "Assumption", "Value", "Guidance"]
    st.markdown("**Model-selection & narrative guardrails**")
    st.dataframe(guardrails, use_container_width=True, hide_index=True)


callout(
    """
Stadium and city features are tagged as <b>proxy</b> signals because our modeling dataset
lacked explicit capacity and metro-demand fields. Introducing those fields is the single
most important upgrade before any figure here is used for commercial commitment.
    """,
    title="Primary data upgrade",
    kind="limit",
)
