"""
1_Executive_Summary.py
----------------------
The 30-second answer: total projected revenue, top hosts, top drivers,
and one clear recommendation — framed for an executive audience.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from utils.helpers import (  # noqa: E402
    configure_page, section, kpi_card, callout, interp,
    sidebar_context_panel, COUNTRY_COLORS, COLOR_PRIMARY,
    COLOR_INK, COLOR_MUTED, COLOR_PANEL, COLOR_RULE,
)
from utils.load_data import (  # noqa: E402
    load_kpis, load_country_summary, load_venue_summary,
    load_feature_importance_main, load_simulation_summary,
)
from utils.formatters import fmt_currency  # noqa: E402


configure_page(
    title="Executive Summary",
    subtitle=(
        "The answer in 30 seconds: our total projected revenue, the venues and "
        "countries that lead, and the demand signals our model says matter most."
    ),
)

with st.sidebar:
    st.markdown("### Filters")
    scenario = st.radio(
        "Revenue scenario",
        options=["Base", "Low", "High"],
        index=0,
        help="Low = 80% of base; High = 120% of base. Useful for sensitivity framing.",
    )
sidebar_context_panel()

scenario_col = {
    "Base": "total_revenue_base_usd",
    "Low":  "total_revenue_low_usd",
    "High": "total_revenue_high_usd",
}[scenario]


# ─────────────────────────────────────────────────────────────────────────────
# KPI row
# ─────────────────────────────────────────────────────────────────────────────
country  = load_country_summary()
venues   = load_venue_summary()
fi_main  = load_feature_importance_main()
sim      = load_simulation_summary().iloc[0]

total_rev         = country[scenario_col].sum()
top_venue         = venues.sort_values(scenario_col, ascending=False).iloc[0]
top_country       = country.sort_values(scenario_col, ascending=False).iloc[0]
top_country_share = top_country[scenario_col] / total_rev

cols = st.columns(5)
with cols[0]:
    kpi_card(
        "Total projected revenue",
        fmt_currency(total_rev, precision=2),
        sub=f"{scenario} scenario · 104 matches · 16 venues",
        accent=True,
    )
with cols[1]:
    kpi_card(
        "Top projected venue",
        top_venue["venue"],
        sub=f"{fmt_currency(top_venue[scenario_col])} · {top_venue['city']}",
    )
with cols[2]:
    kpi_card(
        "Top host country",
        top_country["country"],
        sub=f"{top_country_share * 100:.1f}% of our projected total",
    )
with cols[3]:
    kpi_card(
        "Simulated draws (demo)",
        f"{int(sim['n_valid_draws']):,}",
        sub=f"{sim['acceptance_rate'] * 100:.1f}% acceptance rate",
    )
with cols[4]:
    kpi_card(
        "Primary model",
        "XGBoost",
        sub="revenue_proxy_no_stage_feature · R² 0.84",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Top revenue drivers + revenue by country
# ─────────────────────────────────────────────────────────────────────────────
section("What drives revenue — and where it lands", "HEADLINE CHARTS")

chart_cols = st.columns([3, 2], gap="large")

with chart_cols[0]:
    st.markdown("**Top 5 revenue drivers** · from our primary model")
    top5 = fi_main.head(5).copy()
    top5["Feature"] = top5["feature"].str.replace("_", " ").str.title()
    top5["Share"]   = top5["share_of_total"] * 100
    fig = px.bar(
        top5.iloc[::-1],
        x="Share",
        y="Feature",
        orientation="h",
        text=top5.iloc[::-1]["Share"].map(lambda v: f"{v:.1f}%"),
        color="feature_bucket",
        color_discrete_map={
            "Structural": COLOR_PRIMARY,
            "Proxy":      "#9AB3C9",
            "Mechanical": "#C8102E",
            "Weak":       "#C4C9D1",
        },
        labels={"Share": "Share of model importance", "feature_bucket": "Signal type"},
        height=320,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        margin=dict(l=10, r=40, t=10, b=40),
        legend=dict(orientation="h", y=-0.28),
        showlegend=True,
    )
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)
    interp(
        "Pre-match team strength and team identity lead. Venue and city features appear "
        "but are flagged as capacity / market proxies — see Methodology & Limitations for why."
    )

with chart_cols[1]:
    st.markdown("**Projected revenue by host country**")
    country_plot          = country.copy()
    country_plot["Revenue"] = country_plot[scenario_col]
    country_plot["Country"] = country_plot["country"]
    fig = px.pie(
        country_plot,
        values="Revenue",
        names="Country",
        color="Country",
        color_discrete_map=COUNTRY_COLORS,
        hole=0.55,
    )
    fig.update_traces(
        textinfo="label+percent",
        textfont_size=13,
        hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        showlegend=False,
        annotations=[dict(
            text=(
                f"<b>{fmt_currency(total_rev)}</b>"
                f"<br><span style='font-size:11px;color:#5B6575'>projected total</span>"
            ),
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=17, family="Fraunces"),
        )],
    )
    st.plotly_chart(fig, use_container_width=True)
    interp(
        f"The United States concentrates roughly {top_country_share * 100:.0f}% of our "
        "projected ticket revenue — the single biggest lever for any rebalancing policy."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation + key limitation
# ─────────────────────────────────────────────────────────────────────────────
section("Our recommendation & primary guardrail", "TAKEAWAY")

rec_cols = st.columns(2, gap="large")
with rec_cols[0]:
    callout(
        f"""
Lead with the demand story, not the revenue number. Our model identifies
<b>team strength, recent form, team identity, venue context, and matchup
competitiveness</b> as the real signals. We should use these to inform marketing,
venue allocation, and matchup scheduling — then layer the
{fmt_currency(total_rev)} projection as a planning envelope, not a commitment.
        """,
        title="Our recommendation",
        kind="rec",
    )

with rec_cols[1]:
    callout(
        """
Revenue outputs are proxy revenue built from assumed stage-level pricing, scaled
by capacity. They are not audited observed revenue. Stadium and city features
absorb missing capacity and market variables; our next upgrade is to introduce
explicit capacity and metro-demand fields to unlock proper causal claims.
        """,
        title="Key limitation",
        kind="limit",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Top five venues reference table
# ─────────────────────────────────────────────────────────────────────────────
section("Top five venues by projected revenue", "REFERENCE TABLE")

top_venues = venues.head(5).copy()
top_venues["Venue"]             = top_venues["venue"]
top_venues["City"]              = top_venues["city"]
top_venues["Country"]           = top_venues["country"]
top_venues["Capacity"]          = top_venues["capacity"].map(lambda x: f"{x:,}")
top_venues["Matches"]           = top_venues["total_matches"]
top_venues["Projected Revenue"] = top_venues[scenario_col].map(fmt_currency)

st.dataframe(
    top_venues[["Venue", "City", "Country", "Capacity", "Matches", "Projected Revenue"]],
    use_container_width=True,
    hide_index=True,
)
interp(
    "The final-host venue leads by design. AT&T Stadium and Mercedes-Benz Stadium "
    "follow by absorbing both semifinal-tier matches and multiple group games."
)

callout(
    """
<b>Key context:</b> The revenue advantage from our optimizer comes from knowing
<i>which</i> matchup plays at <i>which</i> stadium — not from changing the matches
themselves. The optimizer works within fixed constraints and finds the assignment
that best matches high-demand matchups to high-capacity, high-market venues.
    """,
    title="Why the optimizer matters",
    kind="info",
)


# ─────────────────────────────────────────────────────────────────────────────
# Positioning strip — where our work sits in the landscape
# ─────────────────────────────────────────────────────────────────────────────
section("Where our work sits", "POSITIONING")

st.markdown(
    f"""
    <style>
      .pos-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 1rem;
        margin: 0.4rem 0 1.2rem 0;
      }}
      .pos-card {{
        background: white;
        border: 1px solid {COLOR_RULE};
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        position: relative;
      }}
      .pos-card.ours {{
        border: 2px solid #1F4E79;
        background: #EBF0F8;
      }}
      .pos-tag {{
        font-size: 0.64rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {COLOR_MUTED};
        margin-bottom: 0.5rem;
      }}
      .pos-card.ours .pos-tag {{ color: #1F4E79; }}
      .pos-title {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: {COLOR_INK};
        margin-bottom: 0.55rem;
        line-height: 1.2;
      }}
      .pos-body {{
        font-size: 0.88rem;
        color: {COLOR_MUTED};
        line-height: 1.55;
      }}
      .pos-body b {{ color: {COLOR_INK}; }}
      .pos-verdict {{
        margin-top: 0.7rem;
        padding-top: 0.6rem;
        border-top: 1px solid {COLOR_RULE};
        font-size: 0.80rem;
        font-style: italic;
        color: {COLOR_MUTED};
      }}
      .pos-card.ours .pos-verdict {{ color: #1F4E79; font-style: normal; font-weight: 600; }}
    </style>
    <div class="pos-grid">
      <div class="pos-card">
        <div class="pos-tag">Revenue Research</div>
        <div class="pos-title">Ticket Pricing &amp; Demand Estimation</div>
        <div class="pos-body">
          &#350;ahin &amp; Erol (2017) and related work model <b>ticket price as the decision
          variable</b> &#8212; predicting how demand responds to price across segments and
          match types. Establishes the demand drivers we adapt: team strength, market
          size, competitive balance.
        </div>
        <div class="pos-verdict">
          Optimises price. Not venue assignment.
        </div>
      </div>
      <div class="pos-card">
        <div class="pos-tag">Draw Research</div>
        <div class="pos-title">Draw Fairness &amp; Constraint Simulation</div>
        <div class="pos-body">
          Csat&#243; (2025) and Roberts &amp; Rosenthal (2023) analyse draw <b>fairness,
          competitive balance, and constraint satisfaction</b>. Rigorous on draw mechanics
          but focused on sporting equity, not commercial venue-assignment decisions.
        </div>
        <div class="pos-verdict">
          Simulates draws. Not revenue-aware.
        </div>
      </div>
      <div class="pos-card">
        <div class="pos-tag">Official FIFA Materials</div>
        <div class="pos-title">Draw Procedures, Schedule &amp; Venue Plan</div>
        <div class="pos-body">
          Defines the tournament structure, host assignments, group draw constraints,
          match schedule, and venue allocations. Sets the <b>real-world baseline</b> every
          planning decision must respect.
        </div>
        <div class="pos-verdict">
          Defines the rules. Does not optimise within them.
        </div>
      </div>
      <div class="pos-card ours">
        <div class="pos-tag">Our System</div>
        <div class="pos-title">Tournament-Aware Decision-Support Framework</div>
        <div class="pos-body">
          Combines draw-constraint simulation, matchup-level demand scoring, and an
          exact venue-assignment optimizer &#8212; all within the FIFA 2026 tournament structure.
          Turns demand insight into a <b>specific allocation recommendation</b>.
        </div>
        <div class="pos-verdict">
          &#8594; Demand intelligence + FIFA constraints + exact optimization
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
