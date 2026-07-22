"""
6_Methodology_Limitations.py
-----------------------------
How we built it, why we made the choices we did, what we validated,
and what this app honestly claims and does not claim.
"""

from __future__ import annotations

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

import streamlit as st  # noqa: E402

from utils.helpers import (  # noqa: E402
    configure_page, section, callout, sidebar_context_panel,
    pipeline_steps,
    COLOR_INK, COLOR_MUTED, COLOR_PANEL, COLOR_RULE,
    COLOR_PRIMARY, COLOR_AMBER, COLOR_GREEN, COLOR_NAVY_LT,
)
from utils.load_data import (  # noqa: E402
    load_assumptions, load_model_comparison, load_stage_summary,
    load_simulation_summary,
)


configure_page(
    title="Methodology & Limitations",
    subtitle=(
        "How our pipeline is constructed, why we made the model choices we did, "
        "what we validated out-of-sample, and what this app honestly claims — and does not."
    ),
)

sidebar_context_panel()


# ─────────────────────────────────────────────────────────────────────────────
# Full pipeline overview
# ─────────────────────────────────────────────────────────────────────────────
section("Our end-to-end pipeline", "FULL SYSTEM OVERVIEW")

pipeline_steps([
    {
        "num": "01",
        "title": "Monte Carlo Draw Simulation",
        "sub": "We simulate valid group-stage draws using a depth-first search with "
               "backtracking. Each draw respects all FIFA 2026 constraints: pot "
               "structure, confederation caps, host-country locks, and pathway "
               "separation. The full pipeline ran 98,258 valid draws from 100,000 "
               "attempts at a 98.3% acceptance rate.",
        "stat": "98,258 valid draws · 148.8M backtracks · seed-stable to ±2.35%",
    },
    {
        "num": "02",
        "title": "XGBoost Revenue Model",
        "sub": "We train an XGBoost model on 827 historical World Cup matches to "
               "predict ticket revenue per matchup × stadium. Target variable: "
               "attendance × $120 base ticket price (group stage). An 80/20 temporal "
               "train/holdout split prevents leakage. Neutral-venue Elo assigned to "
               "higher-ranked team for feature consistency.",
        "stat": "R² = 0.84 on holdout · RMSE $2.2M · 15,102 rows scored",
    },
    {
        "num": "03",
        "title": "Exhaustive Search Optimizer",
        "sub": "For each group, each matchday involves two simultaneous games assigned "
               "across two stadiums — a binary decision. With 3 matchdays per group, "
               "there are 2³ = 8 possible assignments. We evaluate all 8 and select "
               "the revenue-maximizing combination. This is exact optimal, not a "
               "heuristic, and runs across all 12 groups per scenario in under 5 min.",
        "stat": "8 options per group · exact · full 98,258-scenario pipeline < 5 min",
    },
    {
        "num": "04",
        "title": "General Policy Extraction & Validation",
        "sub": "We extract assignment rules that hold across diverse draw scenarios — "
               "not just favorable ones. High-confidence rules: MD3 highest-revenue "
               "game → largest market stadium; Pot 1 matchups → prime-market slots on "
               "MD1/MD2. We then validate out-of-sample on the real Dec 5, 2025 draw "
               "to confirm the policy generalizes beyond our training scenarios.",
        "stat": "3 confidence tiers · validated on real Dec 2025 draw · no overfitting",
    },
])


# ─────────────────────────────────────────────────────────────────────────────
# How we differentiated ourselves — specific prior-work comparison
# ─────────────────────────────────────────────────────────────────────────────
section("How we differentiated ourselves", "POSITIONING")

# ── Narrative block ──────────────────────────────────────────────────────────
_narrative_html = (
f'<div style="background:{COLOR_NAVY_LT};border-left:4px solid {COLOR_PRIMARY};'
f'border-radius:8px;padding:1.1rem 1.4rem;margin:0.4rem 0 1.3rem 0;">'
f'<div style="font-size:0.68rem;font-weight:700;letter-spacing:0.13em;'
f'text-transform:uppercase;color:{COLOR_PRIMARY};margin-bottom:0.6rem;">'
'How Our Approach Differentiates Itself'
'</div>'
f'<div style="display:flex;gap:1.4rem;">'
f'<div style="flex:1;">'
f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;'
f'text-transform:uppercase;color:{COLOR_MUTED};margin-bottom:0.35rem;">'
'Revenue &amp; Ticketing Literature'
'</div>'
f'<div style="font-size:0.91rem;color:{COLOR_INK};line-height:1.6;">'
'Work such as <b>&#350;ahin &amp; Erol (2017)</b>, which models dynamic ticket pricing '
'to improve match-day revenue, demonstrates that football economics can be '
'formalised into operational decisions. That work optimises the '
'<em>pricing lever</em> \u2014 the decision variable is a ticket price, not a venue '
'assignment. It does not address which match should go to which stadium under '
'tournament constraints.'
'</div>'
'</div>'
f'<div style="flex:1;">'
f'<div style="font-size:0.72rem;font-weight:700;letter-spacing:0.1em;'
f'text-transform:uppercase;color:{COLOR_MUTED};margin-bottom:0.35rem;">'
'Draw-Simulation Literature'
'</div>'
f'<div style="font-size:0.91rem;color:{COLOR_INK};line-height:1.6;">'
'Work such as <b>Csat\u00f3 (2025)</b> on World Cup group draw fairness and '
'<b>Roberts &amp; Rosenthal (2023)</b> on draw probability corrections models '
'constrained football draws with rigour \u2014 characterising valid assignments '
'and probability distributions across outcomes. That work is draw-mechanics '
'oriented; it does not optimise commercial venue placement within those outcomes.'
'</div>'
'</div>'
'</div>'
f'<div style="margin-top:1.0rem;padding-top:0.8rem;border-top:1px solid #C9D8EC;'
f'font-size:0.91rem;color:{COLOR_INK};line-height:1.6;">'
'Our system takes the <b>revenue-orientation</b> of the first stream, the '
'<b>draw-constraint rigour</b> of the second, and the '
'<b>structural reality</b> of official FIFA 2026 materials \u2014 and connects them '
'into a single framework that answers the operational question neither prior stream '
'was built to address: <em>given the tournament structure, where should each match '
'be played to maximise expected revenue?</em>'
'</div>'
'</div>'
)
st.markdown(_narrative_html, unsafe_allow_html=True)

# ── 4-column comparison table ────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
      .cmp-wrap {{
        overflow-x: auto;
        margin: 0.2rem 0 1.3rem 0;
      }}
      .cmp-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.86rem;
        font-family: 'Inter', system-ui, sans-serif;
        color: {COLOR_INK};
      }}
      .cmp-table thead tr {{
        background: {COLOR_PRIMARY};
        color: white;
      }}
      .cmp-table thead th {{
        padding: 0.7rem 0.9rem;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-align: left;
        vertical-align: top;
      }}
      .cmp-table thead th.col-ours {{
        background: #163C61;
      }}
      .cmp-table thead .th-cite {{
        font-size: 0.62rem;
        font-weight: 400;
        font-style: italic;
        opacity: 0.85;
        display: block;
        margin-top: 0.2rem;
        white-space: normal;
      }}
      .cmp-table tbody tr:nth-child(even) {{
        background: {COLOR_PANEL};
      }}
      .cmp-table tbody tr:nth-child(odd) {{
        background: white;
      }}
      .cmp-table tbody td {{
        padding: 0.6rem 0.9rem;
        vertical-align: top;
        border-bottom: 1px solid {COLOR_RULE};
        line-height: 1.45;
      }}
      .cmp-table td.row-label {{
        font-weight: 600;
        font-size: 0.76rem;
        color: {COLOR_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        width: 14%;
      }}
      .cmp-table td.col-ours {{
        background: {COLOR_NAVY_LT} !important;
        font-weight: 500;
      }}
      .pill {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.73rem;
        font-weight: 700;
        white-space: nowrap;
      }}
      .pill-yes  {{ background:#E6F4EA; color:#1B5E20; }}
      .pill-no   {{ background:#F3F4F6; color:#6B7280; }}
      .pill-part {{ background:#FEF3C7; color:#92400E; }}
    </style>
    <div class="cmp-wrap">
    <table class="cmp-table">
      <thead>
        <tr>
          <th style="width:14%;"></th>
          <th style="width:21%;">
            Revenue Prior Work
            <span class="th-cite">e.g. Şahin &amp; Erol (2017) — dynamic ticket pricing</span>
          </th>
          <th style="width:21%;">
            Draw-Simulation Prior Work
            <span class="th-cite">e.g. Csató (2025); Roberts &amp; Rosenthal (2023)</span>
          </th>
          <th style="width:20%;">
            Official FIFA Baseline
            <span class="th-cite">Draw procedures, schedule, host locks — FIFA 2026</span>
          </th>
          <th class="col-ours" style="width:24%;">
            Our System ↗
            <span class="th-cite">Tournament-aware decision-support framework</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="row-label">Primary question</td>
          <td>How should ticket prices adjust to improve match-day revenue?</td>
          <td>How do constrained football draws behave — and are they fair or correctly distributed?</td>
          <td>What is the real tournament structure and official setup?</td>
          <td class="col-ours">Given the tournament structure or a valid hypothetical draw, where should each match be played to maximise expected revenue?</td>
        </tr>
        <tr>
          <td class="row-label">Decision variable</td>
          <td>Ticket price</td>
          <td>Draw mechanism / valid group-assignment probabilities</td>
          <td>None — baseline reference</td>
          <td class="col-ours">Matchup-to-venue assignment within the defined decision space</td>
        </tr>
        <tr>
          <td class="row-label">FIFA 2026 tournament constraints</td>
          <td><span class="pill pill-no">No</span></td>
          <td><span class="pill pill-part">Related in spirit</span></td>
          <td><span class="pill pill-yes">Yes — defines them</span></td>
          <td class="col-ours"><span class="pill pill-yes">Yes — enforces them</span></td>
        </tr>
        <tr>
          <td class="row-label">Uses official 2026 draw / schedule</td>
          <td><span class="pill pill-no">No</span></td>
          <td><span class="pill pill-no">Generally no</span></td>
          <td><span class="pill pill-yes">Yes — source of record</span></td>
          <td class="col-ours"><span class="pill pill-yes">Yes — baseline &amp; sandbox modes</span></td>
        </tr>
        <tr>
          <td class="row-label">Revenue-oriented?</td>
          <td><span class="pill pill-yes">Yes — pricing</span></td>
          <td><span class="pill pill-no">No</span></td>
          <td><span class="pill pill-no">No</span></td>
          <td class="col-ours"><span class="pill pill-yes">Yes — venue assignment</span></td>
        </tr>
        <tr>
          <td class="row-label">Draw-simulation oriented?</td>
          <td><span class="pill pill-no">No</span></td>
          <td><span class="pill pill-yes">Yes — core focus</span></td>
          <td><span class="pill pill-no">No</span></td>
          <td class="col-ours"><span class="pill pill-yes">Yes — integrated</span></td>
        </tr>
        <tr>
          <td class="row-label">Optimizes venue assignment?</td>
          <td><span class="pill pill-no">No</span></td>
          <td><span class="pill pill-no">No</span></td>
          <td><span class="pill pill-no">No</span></td>
          <td class="col-ours"><span class="pill pill-yes">Yes — exhaustive exact search</span></td>
        </tr>
        <tr>
          <td class="row-label">What-if scenarios?</td>
          <td><span class="pill pill-part">Pricing context only</span></td>
          <td><span class="pill pill-part">Draw mechanics only</span></td>
          <td><span class="pill pill-no">No</span></td>
          <td class="col-ours"><span class="pill pill-yes">Yes — draw &amp; swap sandbox</span></td>
        </tr>
        <tr>
          <td class="row-label">Operational usefulness for scheduling / allocation</td>
          <td>Pricing strategy — not match placement</td>
          <td>Draw fairness and probability understanding</td>
          <td>Real-world reference baseline</td>
          <td class="col-ours">High — designed for commercial assignment decisions</td>
        </tr>
        <tr>
          <td class="row-label">Main limitation</td>
          <td>Does not decide where matches should be played; not designed for tournament allocation</td>
          <td>Does not optimise revenue-driven venue placement within draw outcomes</td>
          <td>Defines the structure; does not optimise commercial assignment within it</td>
          <td class="col-ours">Revenue is a proxy, not audited commercial truth; optimizer is exact only within the defined binary-assignment decision space</td>
        </tr>
      </tbody>
    </table>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Interpretation Guardrails ────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:white;border:1px solid {COLOR_RULE};
                border-left:4px solid {COLOR_AMBER};border-radius:8px;
                padding:1.0rem 1.2rem;margin:0.2rem 0 1.4rem 0;">
      <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.13em;
                  text-transform:uppercase;color:{COLOR_AMBER};margin-bottom:0.55rem;">
        Interpretation Guardrails
      </div>
      <div style="font-size:0.88rem;color:{COLOR_INK};line-height:1.6;">
        <ul style="margin:0;padding-left:1.3rem;">
          <li style="margin-bottom:0.4rem;">
            <b>Revenue outputs are scenario projections, not audited ticket revenue.</b>
            Built on assumed stage-level pricing scaled by venue capacity.
            Treat as planning envelopes, not commercial commitments.
          </li>
          <li style="margin-bottom:0.4rem;">
            <b>The optimizer is exact within our defined decision space.</b>
            That space is a binary assignment per matchday (which of two simultaneous
            matches goes to which of two stadiums per group). It does not yet optimise
            across matchdays, knockout rounds, or broadcast scheduling windows.
          </li>
          <li style="margin-bottom:0.4rem;">
            <b>This comparison is about scope and operational usefulness,
            not direct metric superiority.</b>
            Şahin &amp; Erol optimise within pricing — a different decision than ours.
            Csató and Roberts &amp; Rosenthal characterise draw distributions — a
            different question than ours. We combine ideas across both streams;
            we are not claiming to outperform either on their own terms.
          </li>
          <li style="margin-bottom:0.4rem;">
            <b>Stadium and city features absorb omitted market variables.</b>
            Explicit capacity, metro demand, travel, diaspora, and hospitality measures
            are the primary next-step upgrades before any output is used for commercial
            commitment.
          </li>
          <li>
            <b>Draw probabilities are directional, not legally precise.</b>
            Real FIFA procedures include geographic and scheduling overlays beyond what
            our simulation fully enforces.
          </li>
        </ul>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Revenue target construction
# ─────────────────────────────────────────────────────────────────────────────
section("Revenue target construction", "HOW THE NUMBER IS BUILT")

st.markdown(
    """
The revenue outputs in this app are **proxy / scenario revenue**, not audited
observed revenue. We construct them as:

$$
\\text{revenue}_{\\text{venue, stage}}
=
\\text{median proxy revenue}_{\\text{stage}}
\\times
\\text{capacity factor}_{\\text{venue}}
$$

where:
- `median proxy revenue by stage` comes from the executed project's stage
  summary (Group $4.7M, Round of 16 $8.1M, Quarter-finals $10.5M,
  Semi-finals $21.4M, Final $33.1M).
- `capacity factor = clip(capacity / 70,000, 0.45, 1.35)` — a linear scaling
  so a 70,000-seat venue hits the stage median exactly; larger venues earn
  proportionally more, smaller venues earn proportionally less.

Our `Low` and `High` scenarios apply ±20% envelope bands around this base.
    """
)

stage_df = load_stage_summary()
with st.expander("View stage-level benchmarks (from our executed project summary)"):
    st.dataframe(stage_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Primary model choice
# ─────────────────────────────────────────────────────────────────────────────
section("Why we chose revenue_proxy_no_stage_feature", "PRIMARY MODEL CHOICE")

st.markdown(
    """
Our project produced three revenue-proxy model specifications. Here is why we
use `revenue_proxy_no_stage_feature` as our primary model throughout the app:

**1. `revenue_proxy_full`** — includes the `stage_detail` feature. Achieves the
highest R² (0.839) but that fit is mechanically driven: since stage-level ticket
pricing is embedded in the revenue target, knowing the stage trivially unlocks
most of the target. This is a cautionary exhibit, not a causal story. We demote
it to appendix status.

**2. `revenue_proxy_no_stage_feature`** — the same model with `stage_detail`
removed. **This is our primary model** for all feature-importance discussion.
Once the trivial shortcut is removed, the features that survive are the signals
that actually drive demand: pre-match team strength (`home_pre_elo`), team
identity (`home_team`), recent form (`home_points_per_match_l5`), and
venue/market context.

**3. `attendance_equivalent_after_price_removal`** — an attendance-only sanity
check. We use it to confirm that the same structural features emerge in the
demand-side view before any pricing is layered on.

The Spec Decision table in our executed project summary demotes
`revenue_proxy_full` to appendix status and elevates the no-stage view for
exactly this reason.
    """
)

metrics = load_model_comparison()
with st.expander("View our executed-model scorecard"):
    st.dataframe(metrics, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# XGBoost model details
# ─────────────────────────────────────────────────────────────────────────────
section("XGBoost model — key decisions", "MODEL DETAIL")

xgb_cols = st.columns(2, gap="large")
with xgb_cols[0]:
    st.markdown(
        """
**Feature families used:**
- **Stage** — Group / R32 / QF / SF / Final — single strongest driver in the full model
- **Team strength** — Elo ratings, expected result, Elo differential
- **Recent form** — Points, goals for/against over last 5 matches
- **Venue & market** — Stadium, city (captures market size signal as proxy)
- **Date & time** — Month, day of week, weekend indicator

**Modeling decisions:**
- Target: ticket revenue proxy = attendance × $120 (group stage base)
- Training: 827 historical World Cup matches, 80/20 temporal split
- Neutral venue: higher Elo team assigned as "home" for feature consistency
- Form defaults: training-set medians used for 2026 (pre-draw, unknown form)
- Elo source: eloratings.net methodology, ratings frozen April 2026
        """
    )
with xgb_cols[1]:
    callout(
        """
<b>Why Elo matters for our optimizer:</b> The optimizer places high-Elo vs. "upset-potential"
matchups at larger venues — exactly the matches that drive disproportionate demand.
Our model captures this because Elo differential is a top surviving feature once the
stage shortcut is removed.
        """,
        title="Elo as a demand signal",
        kind="rec",
    )
    callout(
        """
<b>Known limitation:</b> Our proxy is attendance × $120. Venue premiums are
well-captured; team-level differentiation is limited by training data. MLS and
Liga MX attendance rows are not yet in our training set — a model re-run is
recommended once those are ingested.
        """,
        title="Honest caveat",
        kind="limit",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Draw simulation methodology
# ─────────────────────────────────────────────────────────────────────────────
section("Draw simulation — how our Monte Carlo works", "SIMULATION METHODOLOGY")

sim = load_simulation_summary().iloc[0]
st.markdown(
    f"""
Our draw simulator builds a 48-team, 12-group bracket under FIFA 2026 rules
using a **depth-first search with backtracking**:

- **Pot structure.** 4 pots of 12 teams. Pot 1 is seeded by FIFA ranking plus
  the three hosts; remaining pots are ranked on average FIFA ranking.
- **Host slots.** Mexico is prefilled into Group A, Canada into Group B, and
  the United States into Group D.
- **Confederation cap.** Maximum of 2 UEFA teams per group (since UEFA has 17
  teams across 12 groups, at least 5 groups must contain 2 UEFA sides). Maximum
  of 1 team per group for every other confederation (CONMEBOL, CONCACAF, AFC,
  CAF, OFC).
- **Pathway separation.** Spain/Argentina and France/England are placed in
  opposite R32 halves.
- **Minimum UEFA.** At least 1 UEFA team per group enforced.

**Validation:** We ran 3 seeds × 3,000 draws each. Maximum probability deviation
was 2.35%; p95 deviation = 1.64%. Zero duplicate draws — no sampling bias.

The full pipeline produced **{int(sim['n_valid_draws']):,} valid draws** from
**{int(sim['total_attempts']):,} attempts** — an acceptance rate of
**{sim['acceptance_rate'] * 100:.1f}%** (this app uses a demo-scale subset).
The full run generated 98,258 valid draws from 100,000 attempts.

**Where our simulation is simplified:** Real FIFA rules also include geographic
and scheduling overlays for specific groups and venue sequencing rules that this
prototype does not fully enforce. Use the probability outputs for qualitative
comparison, not legal tournament planning.
    """
)


# ─────────────────────────────────────────────────────────────────────────────
# Optimizer methodology
# ─────────────────────────────────────────────────────────────────────────────
section("Match assignment optimizer — problem formulation", "OPTIMIZER METHODOLOGY")

st.markdown(
    """
**Decision:** For each matchday within each group, which of the 2 simultaneous
matches goes to which stadium?

**Structure:** 3 binary decisions per group (one per matchday) → 2³ = 8
combinations to evaluate.

**Method:** Exhaustive search — all 8 evaluated, maximum revenue selected.

**Why not MIP?** The problem is trivially small (8 options). Exhaustive search
is exact, instantaneous, and fully interpretable. We scale across all 12 groups
independently per scenario (parallelizable).

**Baselines we compare against:**

| Baseline | Description |
|---|---|
| **Optimal** | Exhaustive search result — revenue-maximizing assignment |
| **Naive** | Pot 1 team matchup always goes to the larger stadium, regardless of opponent |
| **Random** | Stadium assignment chosen uniformly at random |

Our optimizer consistently outperforms both baselines. The gap vs. naive
is smaller than vs. random because the naive rule partially approximates
the optimal policy — but misses the Elo differential and matchup-balance signals
that our model captures.
    """
)


# ─────────────────────────────────────────────────────────────────────────────
# Real draw validation
# ─────────────────────────────────────────────────────────────────────────────
section("Out-of-sample validation — the real Dec 2025 draw", "VALIDATION")

val_cols = st.columns([3, 2], gap="large")
with val_cols[0]:
    st.markdown(
        """
The most important test of any optimizer is whether it generalizes beyond the
scenarios it was trained on. We validated our policy out-of-sample against the
**real December 5, 2025 draw** — a draw our model never saw during development.

**Validation setup:**
- Draw used: Real Dec 5, 2025 draw — 12 groups, 48 teams
- Groups scored: All 12 groups × 6 matches = 72 group-stage matches
- Comparison: Optimal assignment vs. naive baseline vs. random assignment

**What we confirmed:**
- Our optimizer identified a revenue-maximizing assignment for every group
- The general policy rules extracted from simulation held on the real draw
- Revenue gap vs. naive was confirmed (specific figures in the executed project output)
- The policy generalizes — it is not overfit to one draw outcome or favorable scenario

This out-of-sample structure is the key validation step that distinguishes our
approach from a curve-fitting exercise.
        """
    )
with val_cols[1]:
    callout(
        """
<b>Structure validated.</b> The Dec 2025 draw was entirely unseen during model
development. Our optimizer produced consistent assignments and the extracted
policy rules held — confirming that our approach generalizes across draw outcomes,
not just the training scenarios.
        """,
        title="Validation result",
        kind="rec",
    )
    callout(
        """
The Dec 2025 draw validation used our proxy revenue model. Since revenue is
not audited commercial revenue, the gap figures represent projected proxy
improvement, not confirmed commercial value.
        """,
        title="Caveat on validation figures",
        kind="limit",
    )


# ─────────────────────────────────────────────────────────────────────────────
# General policy extraction
# ─────────────────────────────────────────────────────────────────────────────
section("General policy — rules that hold across all scenarios", "POLICY EXTRACTION")

st.markdown(
    """
Rather than just reporting optimal assignments for one scenario, we extracted
**general assignment rules** that are consistent across diverse draw outcomes.
These rules can be deployed without re-running the full optimizer:
    """
)

pol_cols = st.columns(3, gap="large")
with pol_cols[0]:
    callout(
        """
<b>HIGH confidence</b><br><br>
Matchday 3's highest-revenue game → largest market stadium in that matchday pair.
MD3 typically features the most meaningful group-stage match — this rule captures
the demand premium reliably.
        """,
        title="Rule 1 — MD3 placement",
        kind="rec",
    )
with pol_cols[1]:
    callout(
        """
<b>HIGH confidence</b><br><br>
Pot 1 team matchups are prioritized for prime-market slots on MD1 and MD2.
Seeded teams carry disproportionate brand equity and fan base — placing them
in the largest venues on early matchdays maximizes early-tournament revenue.
        """,
        title="Rule 2 — Pot 1 early placement",
        kind="rec",
    )
with pol_cols[2]:
    callout(
        """
<b>MEDIUM confidence</b><br><br>
Elo differential matters within a group — more balanced matchups (lower Elo gap)
are placed at the larger venue. Competitive balance drives higher demand and
is partially independent of team brand equity.
        """,
        title="Rule 3 — Competitive balance",
        kind="info",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Policy tradeoff metrics
# ─────────────────────────────────────────────────────────────────────────────
section("Policy tradeoff metrics — how we score scenarios", "SCORING METHODOLOGY")

st.markdown(
    """
Each scenario reallocates matches across venues. We then recompute five metrics:

- **Total revenue (USD)** — sum of proxy revenue across all venue-stage pairs.
- **Equity score** — a normalized measure of evenness across our three host
  countries. Calculated as `1 - (std(country_revenue) / mean(country_revenue)) / 2`,
  clipped to [0, 1]. Higher is more even.
- **Utilization proxy** — weighted average fill rate based on each stage's
  expected average attendance relative to venue capacity.
- **Travel regions touched** — the number of distinct geographic clusters that
  host group-stage matches. Lower means more regional concentration.
- **Small-market share** — the share of projected revenue flowing to Canadian
  and Mexican hosts combined.

When you set priority weights on the Decision Tradeoffs page, we min-max
normalize each metric across the five scenarios, normalize your weights to sum
to one, and compute a composite score for each scenario. The recommended scenario
is the one with the highest composite score under your current weights.
    """
)


# ─────────────────────────────────────────────────────────────────────────────
# What we claim — and what we don't
# ─────────────────────────────────────────────────────────────────────────────
section("What this app claims — and what it does not", "BOUNDARIES")

col1, col2 = st.columns(2, gap="large")
with col1:
    callout(
        """
<b>We claim this is a planning and scenario exploration tool.</b><br><br>
The outputs are directionally useful for: ranking venues under different
priorities, understanding which features our model has learned to weight,
comparing how policy choices reshape host-country distribution, stress-testing
the revenue envelope, and identifying the revenue-maximizing match-to-stadium
assignment for any given draw outcome.
        """,
        title="What this app IS",
        kind="rec",
    )

with col2:
    callout(
        """
<b>We do not claim this is an audited revenue forecast.</b><br><br>
Revenue figures are built on assumed stage pricing. Our attendance model has
modest R². Stadium and city features absorb missing capacity and metro-market
variables. Scenario mechanics are simplified and do not enforce calendar,
broadcast, or local-government constraints that would apply in production.
        """,
        title="What this app is NOT",
        kind="limit",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Assumption registry
# ─────────────────────────────────────────────────────────────────────────────
section("Full assumption registry", "TRANSPARENCY")

assumptions = load_assumptions()
st.dataframe(assumptions, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Next-step upgrades
# ─────────────────────────────────────────────────────────────────────────────
section("Our next-step upgrade roadmap", "ROADMAP")

st.markdown(
    """
In priority order, the improvements that would most strengthen this work:

**1. Explicit stadium capacity and metro-demand fields** in the modeling base.
These are currently absorbed by the `stadium` and `city` proxy features — replacing
them unlocks proper causal feature-importance claims and improves venue-level
revenue estimates.

**2. Local North American attendance rows.** Our modeling base is thin on MLS,
Liga MX, and Canadian domestic matches. Adding these improves the attendance model's
applicability to 2026 venues and reduces reliance on historical WC matches alone.

**3. Observed revenue reconciliation.** If even a subset of venues or matches had
audited revenue numbers, our proxy scenarios could be calibrated against them and
reported with confidence bands rather than scenario envelopes.

**4. Tournament-level constraints in the scenario engine.** Enforcing calendar,
broadcast, and venue-readiness constraints when moving matches between venues would
make the Decision Tradeoffs output actionable at a commercial planning level.

**5. Confidence bands on draw probabilities.** Our simulation currently reports
point estimates. Bootstrap resampling would add uncertainty ranges to the heatmap
and make the probabilistic framing more defensible.
    """
)

st.caption(
    "Built for the FIFA 2026 Capstone · MQM · Team 7 · Duke Fuqua · Spring 2026 · "
    "Clean, honest, and decision-support oriented."
)
