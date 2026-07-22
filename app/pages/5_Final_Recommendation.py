"""
5_Final_Recommendation.py
--------------------------
The closing page of the presentation.
One clear, confident recommendation — what we propose, why it works,
what value it creates, and what we would validate next.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

import streamlit as st  # noqa: E402

from utils.helpers import (  # noqa: E402
    configure_page, section, callout, sidebar_context_panel,
    COLOR_INK, COLOR_MUTED, COLOR_PRIMARY, COLOR_RULE, COLOR_PANEL,
    COLOR_GOLD, COLOR_GREEN, COLOR_AMBER, COLOR_NAVY_LT,
)
from utils.load_data import load_country_summary, load_venue_summary  # noqa: E402
from utils.formatters import fmt_currency  # noqa: E402
from utils.official_baseline import OFFICIAL_DRAW  # noqa: E402
from utils.assignment_engine import optimize_all_groups, total_revenue  # noqa: E402
from utils.load_data import load_revenue_lookup, load_teams  # noqa: E402

configure_page(
    title="Final Recommendation",
    subtitle=(
        "Our recommended path forward — what we propose, the commercial rationale, "
        "which constraints remain intact, and the immediate next step."
    ),
)

sidebar_context_panel()


# ─────────────────────────────────────────────────────────────────────────────
# Load live data for KPIs
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_opt_revenue() -> float:
    rev_df = load_revenue_lookup()
    opt    = optimize_all_groups(OFFICIAL_DRAW, rev_df)
    return total_revenue(opt)

country  = load_country_summary()
venues   = load_venue_summary()
opt_rev  = _load_opt_revenue()

total_base = country["total_revenue_base_usd"].sum()
top_venue  = venues.sort_values("total_revenue_base_usd", ascending=False).iloc[0]
us_share   = (
    country[country["country"] == "USA"]["total_revenue_base_usd"].sum()
    / total_base * 100
)


# ─────────────────────────────────────────────────────────────────────────────
# Hero recommendation block (animated)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <style>
      @keyframes heroFadeUp {{
        from {{ opacity: 0; transform: translateY(18px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
      }}
      @keyframes cardReveal {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
      }}
      .hero-block {{
        background: linear-gradient(135deg, #0B1E3A 0%, {COLOR_PRIMARY} 100%);
        border-radius: 14px;
        padding: 2.2rem 2.4rem;
        margin-bottom: 1.8rem;
        animation: heroFadeUp 0.55s ease both;
      }}
      .hero-eyebrow {{
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.17em;
        text-transform: uppercase;
        color: {COLOR_GOLD};
        margin-bottom: 0.75rem;
      }}
      .hero-headline {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.95rem;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.2;
        margin-bottom: 1.0rem;
      }}
      .hero-body {{
        font-size: 1.02rem;
        color: rgba(255,255,255,0.82);
        line-height: 1.65;
        max-width: 72rem;
      }}
      .hero-body b {{ color: #ffffff; }}
      .rec-card {{
        background: white;
        border: 1px solid {COLOR_RULE};
        border-radius: 10px;
        padding: 1.2rem 1.3rem;
        height: 100%;
        animation: cardReveal 0.5s ease both;
        box-shadow: 0 2px 6px rgba(11,19,32,0.06);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
      }}
      .rec-card:hover {{
        box-shadow: 0 6px 18px rgba(11,19,32,0.10);
        transform: translateY(-2px);
      }}
      .rec-card-tag {{
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {COLOR_PRIMARY};
        margin-bottom: 0.45rem;
      }}
      .rec-card-title {{
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.0rem;
        font-weight: 600;
        color: {COLOR_INK};
        margin-bottom: 0.5rem;
        line-height: 1.25;
      }}
      .rec-card-body {{
        font-size: 0.87rem;
        color: {COLOR_MUTED};
        line-height: 1.55;
      }}
      .rec-card-body b {{ color: {COLOR_INK}; }}
      .takeaway-item {{
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        padding: 0.65rem 0;
        border-bottom: 1px solid {COLOR_RULE};
        font-size: 0.92rem;
        color: {COLOR_INK};
        line-height: 1.5;
      }}
      .takeaway-item:last-child {{ border-bottom: none; }}
      .takeaway-dot {{
        width: 8px;
        height: 8px;
        min-width: 8px;
        border-radius: 50%;
        background: {COLOR_GOLD};
        margin-top: 0.42rem;
      }}
      .next-step-block {{
        background: {COLOR_NAVY_LT};
        border: 1px solid {COLOR_PRIMARY}33;
        border-left: 4px solid {COLOR_PRIMARY};
        border-radius: 8px;
        padding: 1.2rem 1.4rem;
        font-size: 0.93rem;
        line-height: 1.6;
        color: {COLOR_INK};
      }}
      .next-step-block b {{ color: {COLOR_PRIMARY}; }}
    </style>

    <div class="hero-block">
      <div class="hero-eyebrow">Our recommendation</div>
      <div class="hero-headline">
        Deploy the Balanced scenario with revenue-first venue assignment
        on the official FIFA 2026 draw.
      </div>
      <div class="hero-body">
        Our analysis across 98,258 valid draw scenarios shows that applying our
        exhaustive optimizer to the official bracket — with a <b>Balanced policy
        weighting</b> — captures <b>near-optimal projected ticket revenue</b> while
        maintaining the equity and travel constraints FIFA and its host partners
        care about. The optimizer is exact, the policy generalizes across draws,
        and the implementation requires no structural changes to the published schedule.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation cards — four pillars
# ─────────────────────────────────────────────────────────────────────────────
section("Our recommended path in four parts", "RECOMMENDATION BREAKDOWN")

c1, c2, c3, c4 = st.columns(4, gap="small")

with c1:
    st.markdown(
        f"""
        <div class="rec-card">
          <div class="rec-card-tag">Assignment strategy</div>
          <div class="rec-card-title">Exhaustive optimizer on the official draw</div>
          <div class="rec-card-body">
            For each of the 12 groups, our optimizer evaluates all
            <b>2&#179; = 8 venue-assignment combinations</b> per matchday and selects
            the revenue-maximising option. Applied to the official bracket, this
            produces an exact optimal — not an approximation.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="rec-card">
          <div class="rec-card-tag">Revenue rationale</div>
          <div class="rec-card-title">
            {fmt_currency(opt_rev, precision=1)} projected group-stage revenue
          </div>
          <div class="rec-card-body">
            Optimizer applied to the official December 2025 draw projects
            <b>{fmt_currency(opt_rev, precision=1)}</b> in group-stage ticket revenue
            (base scenario). The US accounts for roughly <b>{us_share:.0f}%</b> of
            projected total — the single largest lever for any reallocation decision.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="rec-card">
          <div class="rec-card-tag">Constraint integrity</div>
          <div class="rec-card-title">All FIFA rules intact — no structural changes required</div>
          <div class="rec-card-body">
            Host locks (Mexico&#8594;A, Canada&#8594;B, USA&#8594;D), confederation
            caps, pot structure, and all group-stage schedule constraints are
            <b>fully preserved</b>. The optimizer works inside the defined decision
            space — no variance from published FIFA procedures.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="rec-card">
          <div class="rec-card-tag">Operational implication</div>
          <div class="rec-card-title">One pre-schedule decision — maximum commercial upside</div>
          <div class="rec-card-body">
            The optimizer runs in <b>under five minutes</b> across all 12 groups.
            The decision window is <b>after the draw, before the schedule is published</b>.
            Implementing our recommended assignment requires no visible change to
            fan-facing fixtures — only venue-slot reordering within fixed group dates.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Key takeaways
# ─────────────────────────────────────────────────────────────────────────────
section("Key takeaways", "WHAT THIS DELIVERS")

takeaways = [
    (
        "Revenue-first venue assignment adds value without touching the draw.",
        "Reassigning which matchup plays at which stadium — within each group's fixed venue pair — "
        "is the one lever FIFA controls after the draw. Our optimizer makes that decision "
        "exactly and instantly."
    ),
    (
        "Team identity and Elo strength drive demand — not just venue size.",
        "Our model confirms that high-demand matchups (strong teams, recognized identities, "
        "competitive Elo gaps) should be routed to the highest-capacity, highest-market venues. "
        "This is actionable before the schedule is published."
    ),
    (
        "The Balanced scenario preserves most revenue gains while satisfying equity constraints.",
        "In our five-scenario analysis, Balanced consistently captures 95%+ of the Revenue-First "
        "upside while materially improving the equity score. It is the operationally viable "
        "recommendation for a tournament with three host nations and 16 venues."
    ),
    (
        "The policy generalizes — it is not draw-specific.",
        "Tested across 98,258 valid draw scenarios, our general assignment rule holds: "
        "route the highest-revenue MD3 matchup to the largest market venue, prioritize "
        "Pot 1 matchups in prime slots on MD1 and MD2. The optimizer then handles edge cases exactly."
    ),
]

items_html = ""
for title, body in takeaways:
    items_html += (
        f'<div class="takeaway-item">'
        f'<div class="takeaway-dot"></div>'
        f'<div><b>{title}</b> {body}</div>'
        f'</div>'
    )

st.markdown(
    f'<div style="background:white;border:1px solid {COLOR_RULE};border-radius:10px;'
    f'padding:0.4rem 1.2rem 0.6rem 1.2rem;margin-bottom:1rem;">'
    f'{items_html}'
    f'</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Caveat / guardrail box
# ─────────────────────────────────────────────────────────────────────────────
section("Guardrails", "HONEST CAVEATS")

callout(
    """
<b>Revenue figures are proxy revenue</b>, not audited commercial truth. Our target is
constructed from assumed stage-level ticket prices scaled by venue capacity and match count.
The optimizer is <b>exact within our defined decision space</b> — exhaustive across all 2&#179;
per-group options — but the revenue numbers it optimizes are planning-grade estimates, not
contracted hospitality or broadcast revenue.<br><br>
Future upgrades that would materially improve precision: <b>(1)</b> explicit venue capacity
and metro-demand fields replacing current proxy signals; <b>(2)</b> full expansion of the
matchup revenue table to all 48 qualified teams (currently 6 use city/matchday median
fallback); <b>(3)</b> travel and hospitality cost layers alongside ticket revenue to support
a total-commercial-value objective.
    """,
    title="What our numbers represent",
    kind="limit",
)


# ─────────────────────────────────────────────────────────────────────────────
# Immediate next step
# ─────────────────────────────────────────────────────────────────────────────
section("Immediate next step", "PATH FORWARD")

st.markdown(
    f"""
    <div class="next-step-block">
      <b>What we would validate next:</b> Run the optimizer against the confirmed
      December 2025 group draw with an expanded revenue table that covers all 48 qualified
      teams — replacing the six city/matchday median fallbacks with team-specific demand
      estimates. Pair the output with On Location's hospitality inventory model to convert
      per-match ticket revenue into a total-commercial-value objective.<br><br>
      <b>How FIFA could operationalize this:</b> The optimizer integrates directly into
      the schedule-publication workflow. After the draw ceremony concludes and groups are
      confirmed, a single pipeline run — under five minutes — produces the revenue-maximising
      match-to-venue assignment for all 72 group-stage fixtures. The output is a venue-slot
      mapping that can be reviewed against broadcast and logistics constraints before
      the schedule is formally released.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

# Closing strip
st.markdown(
    f"""
    <div style="border-top:2px solid {COLOR_PRIMARY};padding-top:1.1rem;
    display:flex;justify-content:space-between;align-items:center;
    flex-wrap:wrap;gap:0.75rem;">
      <div style="font-family:'Fraunces',Georgia,serif;font-size:1.1rem;
      font-weight:600;color:{COLOR_INK};">
        FIFA 2026 · Commercial Match Assignment Optimization
      </div>
      <div style="font-size:0.78rem;color:{COLOR_MUTED};">
        MQM Capstone &nbsp;·&nbsp; Team 7 &nbsp;·&nbsp; Duke Fuqua &nbsp;·&nbsp; Spring 2026
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
