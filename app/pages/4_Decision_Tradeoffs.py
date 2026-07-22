"""
4_Decision_Tradeoffs.py
-----------------------
What happens when we optimize for different priorities? Toggle weights, compare
five prebuilt scenarios, and see which venues win and lose under each choice.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from utils.helpers import (  # noqa: E402
    configure_page, section, kpi_card, callout, interp,
    sidebar_context_panel,
    COUNTRY_COLORS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_GOLD, COLOR_GREEN,
)
from utils.load_data import (  # noqa: E402
    load_policy_scenarios, load_policy_venue_revenue, load_policy_country_revenue,
)
from utils.policy_logic import (  # noqa: E402
    SCENARIO_METADATA, POLICY_GOALS, compute_scenario_scores,
    winners_losers, recommend_scenario,
)
from utils.formatters import fmt_currency, fmt_delta_pct  # noqa: E402


configure_page(
    title="Decision Tradeoffs",
    subtitle=(
        "What happens when we optimize for different priorities? Toggle our weights, "
        "compare five prebuilt scenarios, and see exactly which venues win or lose."
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
scenarios = load_policy_scenarios()
pol_venues = load_policy_venue_revenue()
pol_countries = load_policy_country_revenue()

# Apply display names
scenarios["display_name"] = scenarios["scenario"].map(
    lambda s: SCENARIO_METADATA.get(s, {}).get("display_name", s)
)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — policy weight sliders
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Your priorities")
    st.caption(
        "Assign weights (0–10) to each goal. The app normalizes them and ranks the "
        "five scenarios by composite score."
    )
    weights = {}
    default_weights = {
        "maximize_revenue": 6,
        "improve_fairness": 5,
        "increase_utilization": 3,
        "reduce_travel": 2,
        "protect_small_markets": 4,
    }
    for key, label, _col in POLICY_GOALS:
        weights[key] = st.slider(label, 0, 10, default_weights[key], step=1)

    st.markdown("---")
    st.markdown("### Presets")
    preset_cols = st.columns(2)
    with preset_cols[0]:
        if st.button("Revenue-first"):
            st.session_state["_preset"] = "revenue"
        if st.button("Balanced"):
            st.session_state["_preset"] = "balanced"
    with preset_cols[1]:
        if st.button("Fairness"):
            st.session_state["_preset"] = "fairness"
        if st.button("Low-travel"):
            st.session_state["_preset"] = "travel"

    # Apply presets if clicked
    preset = st.session_state.get("_preset")
    if preset:
        preset_weights = {
            "revenue":   {"maximize_revenue": 10, "improve_fairness": 1,
                          "increase_utilization": 5, "reduce_travel": 1,
                          "protect_small_markets": 1},
            "fairness":  {"maximize_revenue": 2,  "improve_fairness": 10,
                          "increase_utilization": 3, "reduce_travel": 3,
                          "protect_small_markets": 9},
            "travel":    {"maximize_revenue": 3,  "improve_fairness": 4,
                          "increase_utilization": 5, "reduce_travel": 10,
                          "protect_small_markets": 3},
            "balanced":  {"maximize_revenue": 5,  "improve_fairness": 5,
                          "increase_utilization": 5, "reduce_travel": 5,
                          "protect_small_markets": 5},
        }
        weights = preset_weights[preset]
        st.session_state["_preset"] = None
        st.rerun()

sidebar_context_panel()


# ─────────────────────────────────────────────────────────────────────────────
# Context panel: how the optimizer works
# ─────────────────────────────────────────────────────────────────────────────
section("How our optimizer works", "EXHAUSTIVE SEARCH")

opt_cols = st.columns([3, 2], gap="large")
with opt_cols[0]:
    st.markdown(
        """
For each of the 12 groups, every matchday involves two simultaneous matches that can
be assigned to two different stadiums. Our **exhaustive search optimizer** evaluates
all 2³ = **8 possible stadium assignments** per group and selects the combination that
maximizes projected ticket revenue for that group.

This is the exact optimal — not a heuristic. The problem is deliberately tractable:
8 options × 12 groups = 96 evaluations per draw scenario. We run this across all
98,258 valid draw scenarios in under five minutes.

The five policy scenarios on this page vary *which matches go to which venues*, then
our composite scoring model ranks them against your stated priorities.
        """
    )
with opt_cols[1]:
    callout(
        """
<b>General policy rules</b> extracted across all draws:<br><br>
• MD3 highest-revenue game → largest market stadium in that matchday pair<br>
• Pot 1 team matchups prioritized for prime-market slots on MD1 and MD2<br>
• More balanced Elo matchups → placed at the larger venue
        """,
        title="General assignment policy",
        kind="info",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Compute scored scenarios
# ─────────────────────────────────────────────────────────────────────────────
scored = compute_scenario_scores(scenarios, pol_countries, weights)
scored["display_name"] = scored["scenario"].map(
    lambda s: SCENARIO_METADATA.get(s, {}).get("display_name", s)
)
rec = recommend_scenario(scored)


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation strip
# ─────────────────────────────────────────────────────────────────────────────
top = scored.iloc[0]
baseline_row = scored[scored["scenario"] == "baseline"].iloc[0]
top_meta = SCENARIO_METADATA[top["scenario"]]

section("Our recommendation — under your current weights", "SCORING OUTPUT")

cols = st.columns([2, 2, 2, 2], gap="small")

with cols[0]:
    kpi_card(
        "Recommended scenario",
        top_meta["display_name"],
        sub=top_meta["tagline"],
        accent=True,
    )
with cols[1]:
    kpi_card(
        "Composite score",
        f"{top['composite_score']:.2f}",
        sub=(
            f"Runner-up: {rec['runner_display']} · {rec['runner_score']:.2f}"
            if rec["runner_display"] else ""
        ),
    )
with cols[2]:
    delta_rev_pct = top["revenue_change_vs_baseline_pct"]
    kpi_card(
        "Revenue vs baseline",
        fmt_delta_pct(delta_rev_pct),
        sub=fmt_currency(top["total_revenue_usd"], precision=2),
    )
with cols[3]:
    delta_equity = top["equity_score"] - baseline_row["equity_score"]
    kpi_card(
        "Equity vs baseline",
        f"{top['equity_score']:.2f}",
        sub=f"Δ {delta_equity:+.2f}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Scenario comparison table
# ─────────────────────────────────────────────────────────────────────────────
section("Scenario comparison", "ALL FIVE SCENARIOS")

disp = scored[[
    "display_name", "scenario", "total_revenue_usd",
    "revenue_change_vs_baseline_pct", "equity_score", "utilization_proxy",
    "travel_regions_touched", "small_market_share", "composite_score",
]].copy()
disp["total_revenue_usd"] = disp["total_revenue_usd"].map(lambda v: fmt_currency(v, precision=2))
disp["revenue_change_vs_baseline_pct"] = disp["revenue_change_vs_baseline_pct"].map(
    lambda v: fmt_delta_pct(v)
)
disp["small_market_share"] = disp["small_market_share"].map(lambda v: f"{v * 100:.1f}%")
disp.columns = [
    "Scenario", "Key", "Revenue", "Δ Revenue vs baseline", "Equity score",
    "Utilization proxy", "Travel regions", "Small-market share", "Composite score",
]
st.dataframe(disp, use_container_width=True, hide_index=True)
interp(
    "Revenue-First delivers the highest projected revenue but our lowest equity score. "
    "Fairness-Constrained inverts that tradeoff. Balanced captures most of the "
    "equity gain with nearly unchanged revenue — typically our best compromise."
)


# ─────────────────────────────────────────────────────────────────────────────
# Revenue vs equity tradeoff plot
# ─────────────────────────────────────────────────────────────────────────────
section("The tradeoff frontier", "REVENUE vs EQUITY")

fig = px.scatter(
    scored,
    x="equity_score",
    y="total_revenue_usd",
    color="display_name",
    size=[18] * len(scored),
    text="display_name",
    labels={
        "equity_score": "Equity score (higher = more even country distribution)",
        "total_revenue_usd": "Total projected revenue (USD)",
        "display_name": "Scenario",
    },
    height=440,
)
fig.update_traces(textposition="top center", textfont=dict(size=12))
fig.update_yaxes(tickprefix="$", tickformat=",.0f")
fig.update_layout(margin=dict(l=60, r=30, t=10, b=60), showlegend=False)

# Highlight recommended scenario with a ring
top_row = scored.iloc[0]
fig.add_trace(
    go.Scatter(
        x=[top_row["equity_score"]],
        y=[top_row["total_revenue_usd"]],
        mode="markers",
        marker=dict(size=38, color="rgba(0,0,0,0)",
                    line=dict(color=COLOR_GOLD, width=3)),
        showlegend=False,
        hoverinfo="skip",
    )
)
st.plotly_chart(fig, use_container_width=True)
interp(
    f"Gold ring = our recommended scenario under your current weights: "
    f"— **{top_meta['display_name']}**."
)


# ─────────────────────────────────────────────────────────────────────────────
# Scenario detail: pick one to inspect
# ─────────────────────────────────────────────────────────────────────────────
section("Inspect a scenario", "DRILL DOWN")

insp_scenario = st.selectbox(
    "Select a scenario",
    options=scored["scenario"].tolist(),
    format_func=lambda s: SCENARIO_METADATA.get(s, {}).get("display_name", s),
    index=0,
)
meta = SCENARIO_METADATA[insp_scenario]

c1, c2 = st.columns([2, 3], gap="large")

with c1:
    st.markdown(f"### {meta['display_name']}")
    st.markdown(f"*{meta['tagline']}*")
    st.markdown(meta["description"])
    st.markdown(
        "**Priorities:** " + ", ".join(meta["priorities"])
    )

with c2:
    # Country revenue under this scenario
    sub = pol_countries[pol_countries["scenario"] == insp_scenario].copy()
    sub["Country"] = sub["country"]
    sub["Revenue"] = sub["revenue"]
    fig = px.bar(
        sub.sort_values("revenue", ascending=True),
        x="revenue", y="Country",
        orientation="h",
        color="Country",
        color_discrete_map=COUNTRY_COLORS,
        text=sub.sort_values("revenue", ascending=True)["revenue"].map(
            lambda v: fmt_currency(v, precision=1)
        ),
        labels={"revenue": "Projected revenue (USD)", "Country": ""},
        height=240,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(margin=dict(l=10, r=80, t=10, b=40), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# Winners and losers vs baseline
if insp_scenario != "baseline":
    section("Winners and losers vs baseline", "VENUE CHANGES")
    winners, losers = winners_losers(pol_venues, insp_scenario, top_n=5)

    col_w, col_l = st.columns(2, gap="large")
    with col_w:
        st.markdown("**Winners** — venues gaining revenue")
        if not winners.empty:
            wd = winners.copy()
            wd["Venue"] = wd["venue"]
            wd["Country"] = wd["country"]
            wd["Baseline"] = wd["baseline"].map(fmt_currency)
            wd["New"] = wd[insp_scenario].map(fmt_currency)
            wd["Δ ($)"] = wd["delta"].map(lambda v: fmt_currency(v, precision=1))
            wd["Δ (%)"] = wd["delta_pct"].map(fmt_delta_pct)
            st.dataframe(
                wd[["Venue", "Country", "Baseline", "New", "Δ ($)", "Δ (%)"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.caption("No venues gain revenue in this scenario.")

    with col_l:
        st.markdown("**Losers** — venues giving up revenue")
        if not losers.empty:
            ld = losers.copy()
            ld["Venue"] = ld["venue"]
            ld["Country"] = ld["country"]
            ld["Baseline"] = ld["baseline"].map(fmt_currency)
            ld["New"] = ld[insp_scenario].map(fmt_currency)
            ld["Δ ($)"] = ld["delta"].map(lambda v: fmt_currency(v, precision=1))
            ld["Δ (%)"] = ld["delta_pct"].map(fmt_delta_pct)
            st.dataframe(
                ld[["Venue", "Country", "Baseline", "New", "Δ ($)", "Δ (%)"]],
                use_container_width=True, hide_index=True,
            )
        else:
            st.caption("No venues lose revenue in this scenario.")


# ─────────────────────────────────────────────────────────────────────────────
# Final recommendation block
# ─────────────────────────────────────────────────────────────────────────────
section("What our weights recommend", "SCORING SUMMARY")

recommendation_text = (
    f"**{top_meta['display_name']}** scores highest under your current priority "
    f"weights. Relative to the announced baseline, this scenario delivers "
    f"**{fmt_delta_pct(top_row['revenue_change_vs_baseline_pct'])}** in projected "
    f"revenue, "
    f"**{(top_row['equity_score'] - baseline_row['equity_score']):+.2f}** in equity, "
    f"and "
    f"**{int(baseline_row['travel_regions_touched'] - top_row['travel_regions_touched']):+d}** "
    f"in travel regions touched (lower is better). {top_meta['description']}"
)
callout(recommendation_text, title="Our recommended approach", kind="rec")

callout(
    """
Our scenario mechanics are simplified for demonstration. Real match-allocation decisions
must also account for calendar constraints, broadcast windows, stadium readiness, and
local-government commitments that this prototype does not yet fully model.
    """,
    title="Limitation to note",
    kind="limit",
)
