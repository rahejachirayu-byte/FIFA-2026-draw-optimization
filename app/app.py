"""
app.py
------
FIFA 2026 Commercial Match Assignment Optimization
Landing page — decision context, pipeline overview, demo walkthrough.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_ROOT))

import streamlit as st  # noqa: E402

from utils.helpers import (  # noqa: E402
    configure_page, section, kpi_card, callout,
    sidebar_context_panel, timeline_block, pipeline_steps, step_card,
)
from utils.load_data import (  # noqa: E402
    load_kpis, load_country_summary, load_venue_summary,
    load_simulation_summary,
)
from utils.formatters import fmt_currency  # noqa: E402


configure_page(
    title="FIFA 2026 Match Assignment Optimizer",
    subtitle=(
        "We maximize ticket revenue by optimally assigning group-stage matches "
        "to stadiums across all possible draw outcomes — before the schedule is published."
    ),
)

with st.sidebar:
    st.markdown("### Navigation")
    st.caption("Use the page selector above to move through the app.")
    st.markdown(
        "1. **Executive Summary** — the answer in 30 seconds  \n"
        "2. **Tournament Scenarios** — draw simulation & venue optimizer  \n"
        "3. **Venue & Revenue Optimization** — venue economics & model signals  \n"
        "4. **Decision Tradeoffs** — revenue vs. equity scenario analysis  \n"
        "5. **Final Recommendation** — our recommended path forward  \n"
        "6. **Methodology & Limitations** — how to read the numbers"
    )
sidebar_context_panel()


# ─────────────────────────────────────────────────────────────────────────────
# Hero KPIs
# ─────────────────────────────────────────────────────────────────────────────
section("At a glance", "SNAPSHOT")

kpis     = load_kpis().set_index("label")
country  = load_country_summary()
venues   = load_venue_summary()
sim      = load_simulation_summary().iloc[0]

total_raw = float(kpis.loc["Total projected revenue (base)", "raw"])
top_v     = venues.iloc[0]
top_c     = country.iloc[0]

cols = st.columns(4)
with cols[0]:
    kpi_card(
        "Total projected revenue",
        fmt_currency(total_raw, precision=2),
        sub=f"Base scenario · {int(country['matches'].sum())} matches · 16 venues",
        accent=True,
    )
with cols[1]:
    kpi_card(
        "Top projected venue",
        top_v["venue"],
        sub=f"{fmt_currency(top_v['total_revenue_base_usd'])} · {top_v['city']}",
    )
with cols[2]:
    kpi_card(
        "Largest host share",
        f"{top_c['country']} · {top_c['share_of_total'] * 100:.1f}%",
        sub=f"{fmt_currency(top_c['total_revenue_base_usd'])} of projected total",
    )
with cols[3]:
    kpi_card(
        "Valid simulated draws",
        f"{int(sim['n_valid_draws']):,}",
        sub=f"From {int(sim['total_attempts']):,} attempts · "
            f"{sim['acceptance_rate'] * 100:.1f}% acceptance (demo scale)",
    )


# ─────────────────────────────────────────────────────────────────────────────
# WHERE OUR DECISION LIVES  (from deck slide 2)
# ─────────────────────────────────────────────────────────────────────────────
section("Where our decision lives", "DECISION CONTEXT")

st.markdown(
    "A World Cup match schedule is the result of a layered chain of decisions — "
    "most of them fixed long before any ball is kicked. Our optimization window "
    "sits in one precise gap: **after the draw reveals the teams, before the "
    "schedule is published.**"
)

timeline_block([
    {
        "tag": "Before the draw",
        "title": "Constraints Set",
        "items": [
            "Pot structure decided",
            "FIFA rankings frozen Nov 19, 2025",
            "Confederation caps & host locks published",
            "Venues pre-assigned to groups",
            "Schedule template fixed (dates & kick-off times)",
        ],
    },
    {
        "tag": "⭐  Our decision window",
        "title": "Optimize Assignment",
        "badge": "Our Work",
        "highlight": True,
        "items": [
            "Monte Carlo: 98,258 valid draw scenarios",
            "XGBoost: revenue per matchup × stadium",
            "Exhaustive search: all 2³ = 8 options per group",
            "General policy extracted across all scenarios",
        ],
    },
    {
        "tag": "🎲  The draw — Dec 5, 2025",
        "title": "Teams Revealed",
        "items": [
            "All 48 teams placed into 12 groups",
            "Matchups become concrete",
            "Our optimizer selects optimal assignment",
        ],
    },
    {
        "tag": "After schedule release",
        "title": "Assignments Locked",
        "items": [
            "Every match · date · venue confirmed",
            "Dynamic pricing activates on demand signals",
            "On Location activates hospitality inventory",
            "No further optimization possible",
        ],
    },
])

callout(
    "Our optimizer identifies the revenue-maximizing assignment across all 12 groups "
    "— <b>before the schedule is published</b>. We validated it out-of-sample against "
    "the real December 5, 2025 draw, which was never seen during model development.",
    title="Core thesis",
    kind="info",
)


# ─────────────────────────────────────────────────────────────────────────────
# END-TO-END PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
section("Our end-to-end pipeline", "METHODOLOGY OVERVIEW")

pipeline_steps([
    {
        "num": "01",
        "title": "Monte Carlo Simulation",
        "sub": "We simulate valid group-stage draws under all FIFA 2026 constraints: "
               "four pots, confederation caps, host-country locks, and pathway "
               "separation. A DFS backtracking engine enforces every rule.",
        "stat": "98,258 valid draws · 98.3% acceptance rate",
    },
    {
        "num": "02",
        "title": "XGBoost Revenue Model",
        "sub": "We train on 827 historical World Cup matches to predict ticket revenue "
               "for every matchup × stadium combination. Key signals: team Elo, "
               "recent form, venue market size, and match stage.",
        "stat": "R² = 0.84 · RMSE $2.2M · 15,102 rows scored",
    },
    {
        "num": "03",
        "title": "Exhaustive Search Optimizer",
        "sub": "For each group, we evaluate all 8 possible stadium assignments "
               "(2³ binary decisions per matchday) and select the combination "
               "that maximizes total group-stage ticket revenue. Exact and instant.",
        "stat": "8 options per group · exact optimal · full pipeline under 5 min",
    },
    {
        "num": "04",
        "title": "General Policy & Validation",
        "sub": "We extract assignment rules that hold across diverse draw scenarios "
               "— not just favorable ones. We then validate out-of-sample against "
               "the real Dec 5, 2025 draw to confirm the policy generalizes.",
        "stat": "Policy generalizes · validated on real draw · structure confirmed",
    },
])


# ─────────────────────────────────────────────────────────────────────────────
# WHAT THIS APP DOES
# ─────────────────────────────────────────────────────────────────────────────
section("What this app does", "FRAMING")

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown(
        """
This workbench consolidates our three analytical layers into one decision tool:

**1. Draw simulation.** Our constrained Monte Carlo engine produces thousands of valid
group-stage draws under FIFA 2026 rules — pots, confederation caps, host-country slots,
and pathway separation. It tells us which matchups are likely, which teams cluster,
and how tournament structure shapes the bracket before a single name is drawn.

**2. Revenue projection.** Stage-level revenue benchmarks from the executed project
summary are mapped onto each of the 16 host venues, scaled by capacity. Output is
venue-by-venue and country-by-country ticket revenue under base, low, and high
scenario envelopes.

**3. Decision tradeoffs.** Five pre-built scenarios — *Revenue-First*, *Fairness-Constrained*,
*Low-Travel*, *Balanced*, and the announced *Baseline* — let us explore what moves when
priorities shift. A weighted scoring panel lets us tune our own blend of goals.
        """
    )

with col2:
    callout(
        "Our model surfaces <b>team strength, recent form, team identity, venue "
        "context, and matchup competitiveness</b> as the drivers that matter — "
        "exactly the signals a planning committee can act on before the draw.",
        title="What drives revenue",
        kind="rec",
    )
    callout(
        "Revenue outputs are <b>scenario / proxy revenue</b> built on assumed "
        "stage-level ticket prices from the executed project summary. This is a "
        "planning and scenario tool, not an audited revenue forecast.",
        title="What we claim (and don't)",
        kind="limit",
    )


# ─────────────────────────────────────────────────────────────────────────────
# DEMO WALKTHROUGH
# ─────────────────────────────────────────────────────────────────────────────
section("Suggested demo flow", "WALKTHROUGH")

flow_cols = st.columns(6, gap="small")
steps = [
    ("1", "Executive Summary",
     "Total revenue, top venues, and the demand drivers that matter most."),
    ("2", "Tournament Scenarios",
     "How FIFA constraints shape likely matchups — and which venue assignments maximise revenue."),
    ("3", "Venue & Revenue Optimization",
     "Venue and country economics, feature importance, model scorecard."),
    ("4", "Decision Tradeoffs",
     "Live scenario toggling and composite scoring — revenue vs. equity."),
    ("5", "Final Recommendation",
     "Our recommended path forward, commercial upside, and immediate next step."),
    ("6", "Methodology & Limitations",
     "Our pipeline, model choices, real-draw validation, and honest guardrails."),
]
for col, (num, name, desc) in zip(flow_cols, steps):
    with col:
        step_card(num, name, desc)


# ─────────────────────────────────────────────────────────────────────────────
# DATA GROUNDING
# ─────────────────────────────────────────────────────────────────────────────
section("Key data grounding", "SOURCES")

st.markdown(
    """
- **Stage-level benchmarks** (Group $4.7M median → Final $33.1M) come directly from
  the executed project's stage summary and drive all proxy revenue outputs.
- **Primary feature-importance ranking** is derived from the executed XGBoost
  `revenue_proxy_full` model with the mechanical `stage_detail` feature removed —
  the `revenue_proxy_no_stage_feature` view — so surviving signals reflect genuine
  demand, not pricing mechanics.
- **Venue list, capacities, and match allocations** follow the publicly announced
  FIFA 2026 host-city lineup across the US, Canada, and Mexico.
- **Draw simulation** follows FIFA's four-pot structure with standard confederation
  caps and host-country prefills (Mexico → Group A, Canada → Group B, USA → Group D).
- **XGBoost training data** consists of 827 historical World Cup matches with an
  80/20 temporal train/holdout split. Elo ratings frozen April 2026.
    """
)

st.caption(
    "Navigate using the sidebar to enter any page. Filter state resets on navigation "
    "for clarity during live demo. · MQM Capstone · Team 7 · Duke Fuqua · Spring 2026"
)
