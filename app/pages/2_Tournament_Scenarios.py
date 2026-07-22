"""
2_Tournament_Scenarios.py  —  Tournament Scenarios
---------------------------------------------------
Three modes for answering:
  "Given a group-stage lineup, where should each match be played to
   maximise projected ticket revenue under tournament constraints?"

MODE 1 — Official FIFA Baseline
  Load the official FIFA 2026 group draw, run our exhaustive optimizer,
  and display revenue-maximising venue assignments for all 12 groups.

MODE 2 — Random Valid Draw
  Generate a fully constrained random draw, run the optimizer, and
  compare projected revenue against the official baseline.

MODE 3 — Hypothetical Swap Sandbox
  Swap any non-host team between groups, re-run the optimizer, and
  inspect per-matchday what-if revenue deltas in real time.

Design system: follows utils/helpers.py tokens throughout.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_ROOT))

import pandas as pd               # noqa: E402
import plotly.express as px       # noqa: E402
import plotly.graph_objects as go # noqa: E402
import streamlit as st            # noqa: E402

from utils.helpers import (       # noqa: E402
    configure_page, section, kpi_card, callout, interp,
    sidebar_context_panel, COLOR_PRIMARY, COLOR_ACCENT,
    COLOR_GOLD, COLOR_GREEN, COLOR_AMBER, COLOR_MUTED,
    COLOR_PANEL, COLOR_RULE, COLOR_INK, COUNTRY_COLORS,
)
from utils.load_data import load_teams, load_revenue_lookup  # noqa: E402
from utils.formatters import fmt_currency                    # noqa: E402
from utils.official_baseline import (                        # noqa: E402
    OFFICIAL_DRAW, GROUP_MD_STADIUMS, CITY_TO_VENUE,
    GROUPS, HOST_LOCKS,
)
from utils.draw_engine import generate_random_draw           # noqa: E402
from utils.assignment_engine import (                        # noqa: E402
    optimize_all_groups, summarise_results, total_revenue,
    all_group_options,
)
from utils.validation import validate_swap                   # noqa: E402
from utils.schedule_data import get_match_info, format_kickoff  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
configure_page(
    title="Tournament Scenarios",
    subtitle=(
        "Three ways to interrogate the FIFA 2026 draw: official baseline, "
        "random valid draw, or hypothetical swap sandbox. Our exhaustive optimizer "
        "finds the revenue-maximising venue assignment for every scenario in real time."
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
# Load static data (cached)
# ─────────────────────────────────────────────────────────────────────────────
teams_df = load_teams()
rev_df   = load_revenue_lookup()

_conf_map = dict(zip(teams_df["team"], teams_df["confederation"]))
_pot_map  = dict(zip(teams_df["team"], teams_df["pot"]))

CONF_BG: dict[str, str] = {
    "UEFA":     "#1F4E79",
    "CONMEBOL": "#1B6E4C",
    "CAF":      "#7B4E1E",
    "AFC":      "#4A1A6E",
    "CONCACAF": "#1A3A4E",
    "OFC":      "#3A3A3A",
}

# ─────────────────────────────────────────────────────────────────────────────
# Session-state initialisation
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("mode",        "Mode 1: Official FIFA Baseline"),
    ("random_draw", None),
    ("random_opt",  None),
    ("swap_draw",   {g: list(v) for g, v in OFFICIAL_DRAW.items()}),
    ("swap_opt",    None),
    ("swap_flips",  {g: {1: False, 2: False, 3: False} for g in GROUPS}),
    ("baseline_opt", None),
    ("baseline_rev", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# Locked host teams
# ─────────────────────────────────────────────────────────────────────────────
LOCKED_TEAMS: set[str] = set()
for _hn in HOST_LOCKS:
    if _hn in _conf_map:
        LOCKED_TEAMS.add(_hn)
    elif _hn == "United States" and "USA" in _conf_map:
        LOCKED_TEAMS.add("USA")
    else:
        LOCKED_TEAMS.add(_hn)


# ═════════════════════════════════════════════════════════════════════════════
# RENDERING HELPERS  — defined before any mode logic
# ═════════════════════════════════════════════════════════════════════════════

def _count_estimates(opt_result: dict) -> int:
    """Count how many match revenues use the median-fallback estimate."""
    return sum(
        1
        for a in opt_result.get("assignments", [])
        for key in ["match_a", "match_b"]
        if a[key].get("is_estimate", False)
    )


def _render_draw_grid(
    draw: dict[str, list[str]],
    diff_draw: dict[str, list[str]] | None = None,
) -> None:
    """Render 12 group cards in a 3×4 grid. Highlights changed teams if diff_draw given."""
    rows = [GROUPS[:4], GROUPS[4:8], GROUPS[8:12]]
    for row in rows:
        cols = st.columns(4, gap="small")
        for col, g in zip(cols, row):
            with col:
                teams   = draw.get(g, [])
                diff_ts = set(diff_draw.get(g, [])) if diff_draw else set()
                lines   = ""
                for t in teams:
                    locked  = t in LOCKED_TEAMS
                    changed = diff_draw is not None and t not in diff_ts
                    conf    = _conf_map.get(t, "")
                    pot     = _pot_map.get(t, "")
                    bg      = CONF_BG.get(conf, "#888")
                    lock_icon = "🔒 " if locked else ""
                    hl = "background:#FFF9E6;border-left:3px solid #F5C842;" if changed else ""
                    lines += (
                        f'<div style="padding:3px 6px;margin:2px 0;border-radius:4px;{hl}">'
                        f'{lock_icon}'
                        f'<span style="font-size:0.81rem;font-weight:{"700" if locked else "500"}'
                        f';color:#1F3A5F;">{t}</span> '
                        f'<span style="display:inline-block;padding:1px 5px;border-radius:6px;'
                        f'font-size:0.58rem;font-weight:700;background:{bg};color:#fff;">'
                        f'{conf[:3]}</span>'
                        f'<span style="font-size:0.58rem;color:#aaa;"> P{pot}</span>'
                        f'</div>'
                    )
                st.markdown(
                    f'<div style="border:1px solid #DEE2EA;border-radius:8px;'
                    f'padding:8px 10px;background:#FAFBFC;margin-bottom:6px;">'
                    f'<div style="font-weight:700;font-size:0.9rem;color:#1F3A5F;'
                    f'margin-bottom:5px;border-bottom:1px solid #DEE2EA;'
                    f'padding-bottom:4px;">Group {g}</div>'
                    f'{lines}</div>',
                    unsafe_allow_html=True,
                )


def _render_group_detail(group_result: dict, show_8_options: bool = True) -> None:
    """Render match-level assignment table + matchday bar + 8-option comparison."""
    group       = group_result["group"]
    teams       = group_result["teams"]
    assignments = group_result.get("assignments", [])
    total_rev   = group_result.get("total_revenue_usd", 0.0)
    n_estimates = _count_estimates(group_result)

    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        st.markdown(f"**Group {group}** · {' · '.join(teams)}")
        st.metric("Group total revenue", fmt_currency(total_rev, precision=2))
        if n_estimates > 0:
            st.caption(
                f"⚠ {n_estimates} of 6 match revenues estimated from city/matchday "
                f"median — team not in lookup table. Marked with ~."
            )
        else:
            st.caption("✓ All 6 match revenues from direct lookup.")

    with c2:
        rows = []
        for asgn in assignments:
            md = asgn["matchday"]
            for slot_idx, key in enumerate(["match_a", "match_b"]):
                m        = asgn[key]
                est_flag = " ~" if m.get("is_estimate") else ""
                sched    = get_match_info(group, md, slot_idx)
                kickoff  = format_kickoff(sched["time"]) if sched else "TBC"
                rows.append({
                    "MD":      f"MD{md}",
                    "Date":    m["date"],
                    "Time":    kickoff,
                    "Match":   m["teams"],
                    "City":    m["city"],
                    "Venue":   m["venue"],
                    "Revenue": fmt_currency(m["revenue_usd"], precision=1) + est_flag,
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.caption("No schedule data available for this group.")

    if assignments:
        md_rev = {a["matchday"]: a["md_total_usd"] for a in assignments}
        md_df  = pd.DataFrame([
            {"Matchday": f"MD{md}", "Revenue": rev}
            for md, rev in sorted(md_rev.items())
        ])
        fig = px.bar(
            md_df, x="Matchday", y="Revenue",
            color_discrete_sequence=[COLOR_PRIMARY],
            text=md_df["Revenue"].map(lambda v: fmt_currency(v, precision=1)),
            height=200,
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        fig.update_layout(margin=dict(l=30, r=10, t=10, b=30))
        st.plotly_chart(fig, use_container_width=True)

    if show_8_options:
        _render_eight_options(group, teams)


def _render_eight_options(group: str, teams: list[str]) -> None:
    """Show all 8 assignment combinations for a group, best → worst."""
    with st.expander(f"All 8 venue-assignment options for Group {group}", expanded=False):
        st.caption(
            "Each column pair represents one (2³) stadium-assignment combination. "
            "The optimizer always selects Option 1 (highest revenue). "
            "Options 2–8 show the revenue cost of any other assignment choice."
        )
        try:
            opts = all_group_options(group, teams, rev_df)
        except Exception as e:
            st.warning(f"Could not compute options: {e}")
            return

        opt_df = pd.DataFrame([
            {
                "Rank":       opt["rank"],
                "Assignment": opt["label"],
                "Revenue":    fmt_currency(opt["total_revenue_usd"], precision=2),
                "vs Optimal": (
                    "— optimal" if opt["is_optimal"]
                    else fmt_currency(
                        opt["total_revenue_usd"] - opts[0]["total_revenue_usd"],
                        precision=1,
                    )
                ),
                "MD1 Rev":    fmt_currency(opt["md_revenues"].get(1, 0), precision=1),
                "MD2 Rev":    fmt_currency(opt["md_revenues"].get(2, 0), precision=1),
                "MD3 Rev":    fmt_currency(opt["md_revenues"].get(3, 0), precision=1),
            }
            for opt in opts
        ])
        st.dataframe(opt_df, use_container_width=True, hide_index=True)

        # Bar chart of all 8 revenues
        bar_df = pd.DataFrame([
            {
                "Option": f"#{opt['rank']}",
                "Revenue": opt["total_revenue_usd"],
                "Color":   COLOR_GOLD if opt["is_optimal"] else COLOR_MUTED,
            }
            for opt in opts
        ])
        fig = px.bar(
            bar_df, x="Option", y="Revenue",
            color="Color",
            color_discrete_map="identity",
            text=bar_df["Revenue"].map(lambda v: fmt_currency(v, precision=1)),
            height=220,
            labels={"Revenue": "Projected revenue (USD)", "Option": "Assignment option"},
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_yaxes(tickprefix="$", tickformat=",.0f")
        fig.update_layout(margin=dict(l=40, r=10, t=10, b=30), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        interp(
            "Gold bar = revenue-optimal assignment our optimizer selects. "
            "Grey bars = revenue foregone under any other assignment choice."
        )


def _render_venue_comparison(
    group: str,
    result_a: dict,
    label_a: str,
    result_b: dict,
    label_b: str,
) -> None:
    """
    Compact matchday-level venue comparison between two scenario results
    for the same group.
    """
    assignments_a = {a["matchday"]: a for a in result_a.get("assignments", [])}
    assignments_b = {b["matchday"]: b for b in result_b.get("assignments", [])}
    rows = []
    for md in [1, 2, 3]:
        a = assignments_a.get(md, {})
        b = assignments_b.get(md, {})
        if not a or not b:
            continue
        rev_a = a.get("md_total_usd", 0.0)
        rev_b = b.get("md_total_usd", 0.0)
        delta  = rev_b - rev_a
        sign   = "+" if delta >= 0 else ""
        rows.append({
            "MD":                    f"MD{md}",
            f"{label_a} venues":     f"{a.get('match_a', {}).get('city','?')} / {a.get('match_b', {}).get('city','?')}",
            f"{label_a} revenue":    fmt_currency(rev_a, precision=1),
            f"{label_b} venues":     f"{b.get('match_a', {}).get('city','?')} / {b.get('match_b', {}).get('city','?')}",
            f"{label_b} revenue":    fmt_currency(rev_b, precision=1),
            "Delta":                 f"{sign}{fmt_currency(delta, precision=1)}",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    total_a = result_a.get("total_revenue_usd", 0.0)
    total_b = result_b.get("total_revenue_usd", 0.0)
    total_delta = total_b - total_a
    sign = "+" if total_delta >= 0 else ""
    interp(
        f"Group {group} total: {label_a} = {fmt_currency(total_a, precision=1)} · "
        f"{label_b} = {fmt_currency(total_b, precision=1)} · "
        f"delta = {sign}{fmt_currency(total_delta, precision=1)}"
    )


def _render_scenario_integrity(
    draw: dict[str, list[str]],
    label: str = "Official",
    n_team_edits: int = 0,
) -> None:
    """
    Compact scenario-integrity panel: host locks, confederation rules,
    pot structure, estimate coverage.
    """
    from utils.draw_engine import is_valid_draw

    valid = True
    try:
        valid = is_valid_draw(draw, teams_df)
    except Exception:
        valid = False

    # Check host locks manually for granular feedback
    host_ok = all(
        draw.get(grp, [None])[0] == team
        for team, grp in HOST_LOCKS.items()
    )

    # Confederation check
    conf_ok = True
    for g, tlist in draw.items():
        counts: dict[str, int] = {}
        for t in tlist:
            c = _conf_map.get(t, "UNKNOWN")
            counts[c] = counts.get(c, 0) + 1
        if counts.get("UEFA", 0) > 2:
            conf_ok = False
            break
        if counts.get("UEFA", 0) < 1:
            conf_ok = False
            break
        for c, n in counts.items():
            if c != "UEFA" and n > 1:
                conf_ok = False
                break

    def _pill(ok: bool, yes: str = "✓", no: str = "✗") -> str:
        color = "#E6F4EA" if ok else "#FEE2E2"
        text_color = "#1B5E20" if ok else "#991B1B"
        label_txt = yes if ok else no
        return (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:8px;'
            f'font-size:0.75rem;font-weight:700;background:{color};color:{text_color};">'
            f'{label_txt}</span>'
        )

    html = (
        f'<div style="background:#F6F7F9;border:1px solid #E4E7EC;border-radius:8px;'
        f'padding:0.75rem 1rem;font-size:0.82rem;color:#0B1320;">'
        f'<div style="font-size:0.63rem;font-weight:700;letter-spacing:0.12em;'
        f'text-transform:uppercase;color:#5B6575;margin-bottom:0.5rem;">Scenario Integrity</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:0.5rem 1rem;">'
        f'<span>Scenario: <b>{label}</b></span>'
        f'<span>Draw valid {_pill(valid)}</span>'
        f'<span>Host locks {_pill(host_ok)}</span>'
        f'<span>Conf. limits {_pill(conf_ok)}</span>'
        f'<span>Team edits: <b>{n_team_edits}</b></span>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Mode")
    MODE_OPTIONS = [
        "Mode 1: Official FIFA Baseline",
        "Mode 2: Random Valid Draw",
        "Mode 3: Hypothetical Swap Sandbox",
    ]
    mode = st.radio(
        "Select scenario mode",
        options=MODE_OPTIONS,
        index=MODE_OPTIONS.index(st.session_state["mode"]),
        label_visibility="collapsed",
    )
    st.session_state["mode"] = mode
    st.markdown("---")
    st.markdown("### How the optimizer works")
    st.caption(
        "For each matchday in a group, two matches play simultaneously at two "
        "venues. Our exhaustive search evaluates all **2³ = 8** possible "
        "stadium assignments per group and picks the revenue-maximising one — "
        "exact optimal, not a heuristic. Total search: **96 evaluations** across "
        "12 groups."
    )
    st.markdown("---")
    st.markdown("### Host locks")
    st.caption(
        "🔒 **Mexico** → Group A · Estadio Azteca / Estadio Akron  \n"
        "🔒 **Canada** → Group B · BMO Field / BC Place  \n"
        "🔒 **USA** → Group D · SoFi Stadium / Lumen Field"
    )
    sidebar_context_panel()


# ─────────────────────────────────────────────────────────────────────────────
# Shared: ensure baseline is always computed (cached in session state)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["baseline_opt"] is None:
    with st.spinner("Running optimizer on official FIFA 2026 baseline…"):
        st.session_state["baseline_opt"] = optimize_all_groups(OFFICIAL_DRAW, rev_df)
        st.session_state["baseline_rev"] = total_revenue(st.session_state["baseline_opt"])

baseline_opt = st.session_state["baseline_opt"]
baseline_rev = st.session_state["baseline_rev"]


# ═════════════════════════════════════════════════════════════════════════════
# MODE 1 — Official FIFA Baseline
# ═════════════════════════════════════════════════════════════════════════════

if mode == "Mode 1: Official FIFA Baseline":

    section("Official FIFA 2026 draw — revenue-optimised assignments", "MODE 1")

    callout(
        "Source: <b>World_Cup_2026_Official_Bracket.txt</b> — all 48 group-stage slots are "
        "fully resolved from the December 5, 2025 draw. No placeholders. We run our "
        "exhaustive 2³-per-group optimizer across all 12 groups and display the "
        "revenue-maximising venue assignment for every matchday. Host slots are "
        "deterministic: <b>Mexico → Group A · Canada → Group B · USA → Group D</b>. "
        "Use the drill-down below to inspect all 8 possible assignments for any group.",
        title="What this mode does",
        kind="info",
    )

    opt           = baseline_opt
    total_rev_val = baseline_rev
    summary_df    = summarise_results(opt)
    top_group     = summary_df.sort_values("total_revenue_usd", ascending=False).iloc[0]
    avg_rev       = summary_df["total_revenue_usd"].mean()
    # Computed dynamically from the optimizer's optimal assignment — not hardcoded.
    # A match is fallback-priced when its exact team-pair × city × matchday key is
    # absent from the revenue lookup table; we substitute the city/matchday median.
    # 6 teams have zero direct entries: Bosnia and Herzegovina, Czechia, DR Congo,
    # Iraq, Sweden, Türkiye. Some additional fallbacks arise when the optimizer routes
    # a well-covered matchup to a venue where that specific pair has no lookup entry.
    total_fallback = sum(_count_estimates(opt[g]) for g in GROUPS)
    total_matches  = sum(
        len(opt[g]["assignments"]) * 2 for g in GROUPS
    )

    cols = st.columns(4)
    with cols[0]:
        kpi_card(
            "Total optimised revenue",
            fmt_currency(total_rev_val, precision=2),
            sub="Official draw · all 12 groups",
            accent=True,
        )
    with cols[1]:
        kpi_card(
            "Highest-revenue group",
            f"Group {top_group['group']}",
            sub=fmt_currency(top_group["total_revenue_usd"], precision=1),
        )
    with cols[2]:
        kpi_card(
            "Average per group",
            fmt_currency(avg_rev, precision=1),
            sub="Across 3 matchdays · 6 matches",
        )
    with cols[3]:
        kpi_card(
            "Fallback-priced matches",
            f"{total_fallback} / {total_matches}",
            sub="Priced via city/matchday median — no direct team entry",
        )

    # Scenario integrity
    st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
    _render_scenario_integrity(OFFICIAL_DRAW, label="Official FIFA 2026", n_team_edits=0)

    section("Group revenue ranking", "OPTIMISED TOTALS")
    sum_sorted = summary_df.sort_values("total_revenue_usd", ascending=True)
    fig = px.bar(
        sum_sorted,
        x="total_revenue_usd", y="group",
        orientation="h",
        text=sum_sorted["total_revenue_usd"].map(lambda v: fmt_currency(v, precision=1)),
        color_discrete_sequence=[COLOR_PRIMARY],
        labels={"total_revenue_usd": "Projected revenue (USD)", "group": "Group"},
        height=400,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(margin=dict(l=30, r=80, t=10, b=40))
    st.plotly_chart(fig, use_container_width=True)
    interp(
        "Groups routed through high-capacity US venues (MetLife, AT&T, SoFi) generate "
        "the highest projected revenue. Canadian and Mexican venue groups project lower "
        "totals — driven by capacity constraints, not demand."
    )

    section("Official draw", "GROUP LINEUP")
    _render_draw_grid(OFFICIAL_DRAW)

    section("Match-level assignments", "DRILL DOWN BY GROUP")
    sel_group = st.selectbox(
        "Select a group to inspect",
        options=sorted(opt.keys()),
        format_func=lambda g: f"Group {g} — {' · '.join(opt[g]['teams'])}",
    )
    _render_group_detail(opt[sel_group], show_8_options=True)


# ═════════════════════════════════════════════════════════════════════════════
# MODE 2 — Random Valid Draw
# ═════════════════════════════════════════════════════════════════════════════

elif mode == "Mode 2: Random Valid Draw":

    section("Random valid draw — generate & optimise", "MODE 2")

    callout(
        "Our constrained Monte Carlo engine uses depth-first search with backtracking to "
        "produce a valid FIFA 2026 group draw from scratch. All constraints are enforced: "
        "pot structure, host locks, confederation caps (max 2 UEFA / max 1 other per group), "
        "and min 1 UEFA per group. We then run the same exhaustive optimizer and compare "
        "revenue against the official baseline.",
        title="What this mode does",
        kind="info",
    )

    col_btn, col_seed, col_reset = st.columns([2, 2, 1], gap="small")
    with col_btn:
        gen_clicked = st.button("🎲  Generate random valid draw", use_container_width=True)
    with col_seed:
        use_seed = st.checkbox("Fix seed for reproducibility", value=True)
        seed_val = st.number_input(
            "Seed",
            min_value=0, max_value=999999,
            value=42, step=1,
            label_visibility="collapsed",
            disabled=not use_seed,
        )
    with col_reset:
        st.markdown("<div style='margin-top:1.55rem;'></div>", unsafe_allow_html=True)
        if st.button("↺ Reset", use_container_width=True):
            st.session_state["random_draw"] = None
            st.session_state["random_opt"]  = None
            st.rerun()

    if gen_clicked:
        prog = st.progress(0, text="Generating valid draw…")
        try:
            seed_arg = int(seed_val) if use_seed else None
            rd = generate_random_draw(teams_df, seed=seed_arg)
            prog.progress(40, text="Draw complete — running optimizer…")
            time.sleep(0.05)
            ropt = optimize_all_groups(rd, rev_df)
            prog.progress(95, text="Finalising…")
            time.sleep(0.05)
            st.session_state["random_draw"] = rd
            st.session_state["random_opt"]  = ropt
            prog.progress(100, text="Done.")
            time.sleep(0.15)
            prog.empty()
        except RuntimeError as e:
            prog.empty()
            st.error(f"Could not generate a valid draw: {e}")

    rand_draw = st.session_state.get("random_draw")
    rand_opt  = st.session_state.get("random_opt")

    if rand_draw is None:
        st.info(
            "Click **Generate random valid draw** above to produce a new constrained "
            "draw and run the optimizer."
        )
    else:
        rand_rev     = total_revenue(rand_opt)
        delta_abs    = rand_rev - baseline_rev
        delta_pct    = (delta_abs / baseline_rev * 100) if baseline_rev else 0.0
        delta_sign   = "+" if delta_abs >= 0 else ""
        rand_summary = summarise_results(rand_opt)
        cols = st.columns(4)
        with cols[0]:
            kpi_card(
                "Random draw revenue",
                fmt_currency(rand_rev, precision=2),
                sub="All 12 groups · optimised",
                accent=True,
            )
        with cols[1]:
            kpi_card(
                "vs Official baseline",
                f"{delta_sign}{fmt_currency(delta_abs, precision=1)}",
                sub=f"{delta_sign}{delta_pct:.1f}% vs baseline",
            )
        with cols[2]:
            top_g = rand_summary.sort_values("total_revenue_usd", ascending=False).iloc[0]
            kpi_card(
                "Highest-revenue group",
                f"Group {top_g['group']}",
                sub=fmt_currency(top_g["total_revenue_usd"], precision=1),
            )
        with cols[3]:
            seed_label = str(seed_val) if use_seed else "True random"
            kpi_card("Seed used", seed_label, sub="Re-enter seed to reproduce")

        st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
        _render_scenario_integrity(rand_draw, label="Random Valid Draw", n_team_edits=0)

        section("Generated draw", "GROUP LINEUP")
        _render_draw_grid(rand_draw)

        section("Revenue comparison — random vs official", "SIDE BY SIDE")

        base_summary = summarise_results(baseline_opt).rename(
            columns={"total_revenue_usd": "baseline_usd"}
        )[["group", "baseline_usd"]]
        comp_df = rand_summary.rename(
            columns={"total_revenue_usd": "random_usd"}
        )[["group", "random_usd"]].merge(base_summary, on="group")

        fig = go.Figure()
        fig.add_bar(
            x=comp_df["group"], y=comp_df["baseline_usd"],
            name="Official baseline", marker_color=COLOR_ACCENT,
        )
        fig.add_bar(
            x=comp_df["group"], y=comp_df["random_usd"],
            name="This draw", marker_color=COLOR_PRIMARY,
        )
        fig.update_layout(
            barmode="group", height=380,
            margin=dict(l=40, r=20, t=20, b=40),
            yaxis=dict(tickprefix="$", tickformat=",.0f"),
            legend=dict(orientation="h", y=1.05),
        )
        st.plotly_chart(fig, use_container_width=True)
        interp(
            "Revenue variation across draws reflects where high-demand teams "
            "(Argentina, France, Brazil, England) land relative to high-capacity US venues. "
            "Our optimizer captures the best available assignment for whatever draw it receives."
        )

        section("Match-level assignments", "DRILL DOWN BY GROUP")
        sel_g2 = st.selectbox(
            "Select a group to inspect",
            options=sorted(rand_opt.keys()),
            format_func=lambda g: f"Group {g} — {' · '.join(rand_opt[g]['teams'])}",
            key="rand_group_sel",
        )
        _render_group_detail(rand_opt[sel_g2], show_8_options=True)


# ═════════════════════════════════════════════════════════════════════════════
# MODE 3 — Hypothetical Swap Sandbox
# ═════════════════════════════════════════════════════════════════════════════

else:  # Mode 3

    section("Hypothetical swap sandbox", "MODE 3")

    callout(
        "Swap any non-host team between groups, then inspect the revenue impact "
        "at the group and matchday level. <b>Mexico (A), Canada (B), and USA (D)</b> "
        "are permanently locked. After every valid swap, the optimizer reruns and "
        "updates projected revenue against the official baseline.",
        title="What this mode does",
        kind="info",
    )

    # Always work off a mutable copy
    if st.session_state["swap_draw"] is None:
        st.session_state["swap_draw"] = {g: list(v) for g, v in OFFICIAL_DRAW.items()}

    swap_draw: dict[str, list[str]] = st.session_state["swap_draw"]

    # ── Swap controls ──────────────────────────────────────────────────────
    st.markdown("#### Swap teams between groups")
    sc = st.columns([2, 0.3, 2, 0.8, 0.8], gap="small")

    swappable = sorted(t for t in teams_df["team"].tolist() if t not in LOCKED_TEAMS)

    with sc[0]:
        team_a_swap = st.selectbox(
            "Team A", options=swappable, key="swap_team_a",
        )
    with sc[1]:
        st.markdown(
            "<div style='margin-top:1.85rem;text-align:center;font-size:1.3rem;'>⇄</div>",
            unsafe_allow_html=True,
        )
    with sc[2]:
        team_b_opts  = [t for t in swappable if t != team_a_swap]
        team_b_swap  = st.selectbox(
            "Team B", options=team_b_opts, key="swap_team_b",
        )
    with sc[3]:
        st.markdown("<div style='margin-top:1.65rem;'></div>", unsafe_allow_html=True)
        do_swap = st.button("Swap ⇄", use_container_width=True)
    with sc[4]:
        st.markdown("<div style='margin-top:1.65rem;'></div>", unsafe_allow_html=True)
        if st.button("↺ Reset", use_container_width=True):
            st.session_state["swap_draw"]  = {g: list(v) for g, v in OFFICIAL_DRAW.items()}
            st.session_state["swap_opt"]   = None
            st.session_state["swap_flips"] = {g: {1: False, 2: False, 3: False} for g in GROUPS}
            st.rerun()

    # Apply swap — with validation
    if do_swap:
        ok, errors, warnings = validate_swap(
            team_a_swap, team_b_swap,
            swap_draw, _conf_map, _pot_map,
            locked_teams=LOCKED_TEAMS,
        )
        if not ok:
            for err in errors:
                st.error(f"🚫 {err}")
        else:
            for warn in warnings:
                st.warning(f"⚠️ {warn}")
            # Only proceed if it isn't a same-group no-op
            new_draw = {g: list(v) for g, v in swap_draw.items()}
            pos_a = pos_b = group_a = group_b = None
            for g, t_list in new_draw.items():
                if team_a_swap in t_list:
                    group_a, pos_a = g, t_list.index(team_a_swap)
                if team_b_swap in t_list:
                    group_b, pos_b = g, t_list.index(team_b_swap)
            if group_a and group_b and group_a != group_b:
                new_draw[group_a][pos_a] = team_b_swap
                new_draw[group_b][pos_b] = team_a_swap
                st.session_state["swap_draw"]  = new_draw
                st.session_state["swap_opt"]   = None
                st.session_state["swap_flips"] = {g: {1: False, 2: False, 3: False} for g in GROUPS}
                swap_draw = new_draw

    # ── Run optimizer ────────────────────────────────────────────────────
    if st.session_state.get("swap_opt") is None:
        with st.spinner("Running optimizer on current draw…"):
            st.session_state["swap_opt"] = optimize_all_groups(swap_draw, rev_df)

    swap_opt  = st.session_state["swap_opt"]

    # Apply matchday flips for what-if total
    swap_flips = st.session_state.get(
        "swap_flips", {g: {1: False, 2: False, 3: False} for g in GROUPS}
    )

    def _flip_adjusted_revenue(opt_result: dict, flips: dict[int, bool]) -> float:
        """
        Compute total revenue for a group after applying matchday flips.
        A flip swaps match_a and match_b venues for that matchday, effectively
        choosing the alternative assignment rather than the optimal one.
        """
        from utils.assignment_engine import _get_index, _city_alias, _alias
        from utils.official_baseline import GROUP_MD_STADIUMS, MD_PAIRS
        idx, median = _get_index(rev_df)
        group  = opt_result["group"]
        teams  = opt_result["teams"]
        md_cfg = GROUP_MD_STADIUMS.get(group, {})
        total  = 0.0
        for md in [1, 2, 3]:
            pairs  = MD_PAIRS[md]
            cities = md_cfg.get(md, {})
            s1, s2 = cities.get("s1", ""), cities.get("s2", "")
            if not s1 or not s2:
                continue
            flip  = flips.get(md, False)
            city0 = s2 if flip else s1
            city1 = s1 if flip else s2
            lc0, lc1 = _city_alias(city0), _city_alias(city1)
            ta0, tb0 = teams[pairs[0][0]], teams[pairs[0][1]]
            ta1, tb1 = teams[pairs[1][0]], teams[pairs[1][1]]
            a0, b0   = sorted([_alias(ta0), _alias(tb0)])
            a1, b1   = sorted([_alias(ta1), _alias(tb1)])
            k0       = f"{a0}|{b0}|{lc0}|{md}"
            k1       = f"{a1}|{b1}|{lc1}|{md}"
            r0 = idx.get(k0) if k0 in idx else median.get((lc0, md), 0.0)
            r1 = idx.get(k1) if k1 in idx else median.get((lc1, md), 0.0)
            total += r0 + r1
        return total

    # Total with flips
    flip_total = sum(
        _flip_adjusted_revenue(swap_opt[g], swap_flips.get(g, {}))
        for g in GROUPS
    )

    swap_rev_optimal = total_revenue(swap_opt)
    delta_abs  = swap_rev_optimal - baseline_rev
    delta_pct  = (delta_abs / baseline_rev * 100) if baseline_rev else 0.0
    delta_sign = "+" if delta_abs >= 0 else ""

    flip_delta      = flip_total - swap_rev_optimal
    flip_delta_sign = "+" if flip_delta >= 0 else ""

    n_diff = sum(
        1 for g in GROUPS
        if sorted(swap_draw[g]) != sorted(OFFICIAL_DRAW[g])
    )
    total_fallback = sum(_count_estimates(swap_opt[g]) for g in GROUPS)
    total_matches_swap = sum(len(swap_opt[g]["assignments"]) * 2 for g in GROUPS)
    n_flipped = sum(
        1 for g in GROUPS
        for md, v in swap_flips.get(g, {}).items()
        if v
    )

    cols = st.columns(4)
    with cols[0]:
        kpi_card(
            "Optimised revenue",
            fmt_currency(swap_rev_optimal, precision=2),
            sub="Current swap draw",
            accent=True,
        )
    with cols[1]:
        kpi_card(
            "vs Official baseline",
            f"{delta_sign}{fmt_currency(delta_abs, precision=1)}",
            sub=f"{delta_sign}{delta_pct:.1f}%",
        )
    with cols[2]:
        swap_summary = summarise_results(swap_opt)
        top_sg = swap_summary.sort_values("total_revenue_usd", ascending=False).iloc[0]
        kpi_card(
            "Highest-revenue group",
            f"Group {top_sg['group']}",
            sub=fmt_currency(top_sg["total_revenue_usd"], precision=1),
        )
    with cols[3]:
        kpi_card("Groups modified", str(n_diff), sub=f"{total_fallback}/{total_matches_swap} fallback-priced")

    # Scenario integrity
    st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
    _render_scenario_integrity(swap_draw, label="Hypothetical Sandbox", n_team_edits=n_diff * 2)

    section("Current draw", "SWAP STATE")
    _render_draw_grid(swap_draw, diff_draw=OFFICIAL_DRAW)

    section("Revenue delta vs official baseline", "GROUP-LEVEL IMPACT")

    base_summary = summarise_results(baseline_opt).rename(
        columns={"total_revenue_usd": "baseline_usd"}
    )[["group", "baseline_usd"]]
    delta_df = swap_summary.rename(
        columns={"total_revenue_usd": "swap_usd"}
    )[["group", "swap_usd"]].merge(base_summary, on="group")
    delta_df["delta_usd"] = delta_df["swap_usd"] - delta_df["baseline_usd"]
    delta_df["color"]     = delta_df["delta_usd"].apply(
        lambda v: COLOR_GREEN if v >= 0 else "#C8102E"
    )
    delta_sorted = delta_df.sort_values("delta_usd")

    fig = px.bar(
        delta_sorted,
        x="delta_usd", y="group",
        orientation="h",
        color="color",
        color_discrete_map="identity",
        text=delta_sorted["delta_usd"].map(
            lambda v: ("+" if v >= 0 else "") + fmt_currency(v, precision=1)
        ),
        labels={"delta_usd": "Revenue delta vs baseline (USD)", "group": "Group"},
        height=400,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(tickprefix="$", tickformat=",.0f")
    fig.update_layout(margin=dict(l=30, r=90, t=10, b=40), showlegend=False)
    fig.add_vline(x=0, line_dash="dot", line_color="#888", line_width=1)
    st.plotly_chart(fig, use_container_width=True)
    interp(
        "Groups with positive bars gain revenue when the swapped team brings higher "
        "market demand or better Elo matchups to that venue slot."
    )

    # ── Venue comparison + drill-down ──────────────────────────────────────
    section("Venue comparison & match-level drill-down", "SCENARIO DETAIL")

    tab_cmp, tab_detail, tab_wi = st.tabs([
        "📍 Venue comparison",
        "📋 Match-level assignments",
        "🔀 What-if matchday flips",
    ])

    with tab_cmp:
        st.caption(
            "Compare venue assignments and projected revenue between the official "
            "FIFA baseline and the current sandbox — matchday by matchday."
        )
        cmp_group = st.selectbox(
            "Select a group to compare",
            options=sorted(swap_opt.keys()),
            format_func=lambda g: f"Group {g} — {' · '.join(swap_opt[g]['teams'])}",
            key="cmp_group_sel",
        )
        # Check if this group actually differs
        grp_changed = sorted(swap_draw[cmp_group]) != sorted(OFFICIAL_DRAW[cmp_group])
        if not grp_changed:
            st.info(
                f"Group {cmp_group} has not been modified in the sandbox — "
                "venue assignments are identical to the official baseline."
            )
        _render_venue_comparison(
            cmp_group,
            baseline_opt[cmp_group], "Official",
            swap_opt[cmp_group],     "Sandbox",
        )

        # Revenue pill summary
        opt_total_cmp  = baseline_opt[cmp_group].get("total_revenue_usd", 0.0)
        sand_total_cmp = swap_opt[cmp_group].get("total_revenue_usd", 0.0)
        delta_cmp      = sand_total_cmp - opt_total_cmp
        sign_cmp       = "+" if delta_cmp >= 0 else ""
        delta_color    = "#E6F4EA" if delta_cmp >= 0 else "#FEE2E2"
        delta_text_col = "#1B5E20" if delta_cmp >= 0 else "#991B1B"
        pill_html = (
            f'<div style="margin-top:0.5rem;display:flex;gap:1rem;flex-wrap:wrap;'
            f'font-size:0.83rem;">'
            f'<span>Official: <b>{fmt_currency(opt_total_cmp,precision=1)}</b></span>'
            f'<span>Sandbox: <b>{fmt_currency(sand_total_cmp,precision=1)}</b></span>'
            f'<span style="background:{delta_color};color:{delta_text_col};'
            f'padding:2px 8px;border-radius:8px;font-weight:700;">'
            f'Delta: {sign_cmp}{fmt_currency(delta_cmp,precision=1)}</span>'
            f'</div>'
        )
        st.markdown(pill_html, unsafe_allow_html=True)

    with tab_detail:
        sel_g3 = st.selectbox(
            "Select a group to inspect",
            options=sorted(swap_opt.keys()),
            format_func=lambda g: f"Group {g} — {' · '.join(swap_opt[g]['teams'])}",
            key="swap_group_sel",
        )
        _render_group_detail(swap_opt[sel_g3], show_8_options=True)

    with tab_wi:
        st.caption(
            "Override the optimizer's assignment for specific matchdays to explore "
            "what-if scenarios. The optimizer always picks the revenue-maximising option; "
            "flipping a matchday forces the alternative assignment for that group/matchday pair."
        )
        wi_group = st.selectbox(
            "Select a group",
            options=sorted(swap_opt.keys()),
            format_func=lambda g: f"Group {g} — {' · '.join(swap_opt[g]['teams'])}",
            key="wi_group_sel",
        )
        st.markdown(f"**Group {wi_group}** — flip individual matchday assignments:")
        group_flips = swap_flips.get(wi_group, {1: False, 2: False, 3: False})
        result_g    = swap_opt[wi_group]
        assignments = {a["matchday"]: a for a in result_g.get("assignments", [])}
        flip_changed = False
        for md in [1, 2, 3]:
            asgn = assignments.get(md, {})
            if not asgn:
                continue
            opt_a = asgn.get("match_a", {})
            opt_b = asgn.get("match_b", {})
            cur_label = (
                f"MD{md} · optimal: {opt_a.get('teams','?')} @ {opt_a.get('city','?')} | "
                f"{opt_b.get('teams','?')} @ {opt_b.get('city','?')} "
                f"({fmt_currency(asgn.get('md_total_usd',0),precision=1)})"
            )
            new_val = st.checkbox(f"↔ Flip MD{md}", value=group_flips.get(md, False), key=f"flip_{wi_group}_{md}")
            st.caption(cur_label)
            if new_val != group_flips.get(md, False):
                swap_flips[wi_group][md] = new_val
                flip_changed = True

        if flip_changed:
            st.session_state["swap_flips"] = swap_flips
            st.rerun()

        # What-if summary for this group
        opt_rev_g  = _flip_adjusted_revenue(result_g, {md: False for md in [1, 2, 3]})
        flip_rev_g = _flip_adjusted_revenue(result_g, group_flips)
        wi_delta   = flip_rev_g - opt_rev_g
        wi_sign    = "+" if wi_delta >= 0 else ""
        st.markdown("---")
        wc = st.columns(3)
        wc[0].metric("Optimal revenue", fmt_currency(opt_rev_g, precision=2))
        wc[1].metric("What-if revenue", fmt_currency(flip_rev_g, precision=2))
        wc[2].metric("What-if delta", f"{wi_sign}{fmt_currency(wi_delta, precision=2)}")

        if n_flipped > 0:
            st.info(
                f"**{n_flipped} matchday flip(s) active** across all groups. "
                f"What-if total: {fmt_currency(flip_total, precision=2)} "
                f"({flip_delta_sign}{fmt_currency(flip_delta, precision=1)} vs optimised)."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Bottom — always shown
# ─────────────────────────────────────────────────────────────────────────────
callout(
    "Revenue entries for some team pairings may not exist in our lookup table. "
    "Where an exact entry is missing, the optimizer uses the city/matchday median "
    "as a proxy and flags it with a tilde (~). Estimates are clearly marked in the "
    "match table and counted in the KPI tile above. "
    "Expanding the scoring matrix to all 48 qualified teams is our primary "
    "data-completeness upgrade.",
    title="Revenue lookup coverage",
    kind="limit",
)
