"""
utils/assignment_engine.py
--------------------------
Exhaustive stadium-assignment optimizer for FIFA 2026 group stage.

Given a group draw (12 groups × 4 teams), this engine evaluates all
2³ = 8 possible stadium assignments per group per matchday pair and
selects the combination that maximises projected ticket revenue.

Public API
----------
optimize_all_groups(draw, revenue_df) -> dict
    For every group, find the revenue-maximising stadium assignment.
    Returns {group: {"assignments": [...], "total_revenue": float,
                     "matchday_revenues": {...}}}

get_match_revenue(team_a, team_b, city, matchday, revenue_df) -> float
    Look up a single match's projected revenue (USD).

summarise_results(optimised) -> pd.DataFrame
    Flatten optimised dict to a DataFrame for display.
"""

from __future__ import annotations

import itertools
from typing import Optional

import pandas as pd

from utils.official_baseline import GROUP_MD_STADIUMS, MD_PAIRS, CITY_TO_VENUE

# ─────────────────────────────────────────────────────────────────────────────
# Team name aliases
# The revenue lookup CSV was built with official FIFA data-feed names, which
# differ from the display names used in app_teams.csv and the draw.
# ─────────────────────────────────────────────────────────────────────────────
TEAM_ALIASES: dict[str, str] = {
    # Official bracket names → revenue-table lookup names
    "Côte d'Ivoire":         "Cote d'Ivoire",   # bracket uses accented é
    "Curaçao":               "Curacao",          # bracket uses ç
    # Legacy aliases (backward compatibility)
    "South Korea":           "Korea Republic",
    "Iran":                  "IR Iran",
    "Ivory Coast":           "Cote d'Ivoire",
}


def _alias(team: str) -> str:
    """Return the revenue-table name for a team (applying aliases if needed)."""
    return TEAM_ALIASES.get(team, team)


# ─────────────────────────────────────────────────────────────────────────────
# City aliases for revenue lookup
# "San Francisco Bay Area" (Levi's Stadium) has no entries in the revenue table.
# We proxy it with Seattle (Lumen Field) — same region, near-identical capacity.
# ─────────────────────────────────────────────────────────────────────────────
CITY_ALIASES: dict[str, str] = {
    "San Francisco Bay Area": "Seattle",
}


def _city_alias(city: str) -> str:
    """Return the revenue-table city name (applying aliases if needed)."""
    return CITY_ALIASES.get(city, city)


# ─────────────────────────────────────────────────────────────────────────────
# Revenue lookup helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_index(revenue_df: pd.DataFrame) -> tuple[dict[str, float], dict[tuple, float]]:
    """
    Build two lookup structures:
      idx      : {full_key: revenue_usd}    — exact match lookup
      median   : {(city, matchday): median_usd} — fallback for unknown teams
    """
    idx: dict[str, float] = {}
    city_md_vals: dict[tuple, list[float]] = {}

    for _, row in revenue_df.iterrows():
        rev_usd = float(row["revenue_usd_m"]) * 1_000_000
        idx[str(row["key"])] = rev_usd
        cm_key = (str(row["city"]), int(row["matchday"]))
        city_md_vals.setdefault(cm_key, []).append(rev_usd)

    median: dict[tuple, float] = {}
    for cm_key, vals in city_md_vals.items():
        sorted_vals = sorted(vals)
        n = len(sorted_vals)
        median[cm_key] = sorted_vals[n // 2]

    return idx, median


def _make_key(team_a: str, team_b: str, city: str, matchday: int) -> str:
    a, b = sorted([_alias(team_a), _alias(team_b)])
    c = _city_alias(city)
    return f"{a}|{b}|{c}|{matchday}"


# Module-level cache: keyed by id of revenue_df to survive Streamlit reruns
_IDX_CACHE: dict[int, tuple[dict, dict]] = {}


def _get_index(revenue_df: pd.DataFrame) -> tuple[dict[str, float], dict[tuple, float]]:
    df_id = id(revenue_df)
    if df_id not in _IDX_CACHE:
        _IDX_CACHE.clear()          # keep memory tidy
        _IDX_CACHE[df_id] = _build_index(revenue_df)
    return _IDX_CACHE[df_id]


def get_match_revenue(
    team_a: str,
    team_b: str,
    city: str,
    matchday: int,
    revenue_df: pd.DataFrame,
) -> float:
    """
    Return projected revenue (USD) for a single match.
    Falls back to the city/matchday median when no exact entry is found.
    """
    idx, median = _get_index(revenue_df)
    key = _make_key(team_a, team_b, city, matchday)
    if key in idx:
        return idx[key]
    # Fallback: use median revenue for this city × matchday
    return median.get((city, matchday), 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Per-group optimizer
# ─────────────────────────────────────────────────────────────────────────────

def _optimize_group(
    group: str,
    teams: list[str],          # [pot1, pot2, pot3, pot4]
    revenue_df: pd.DataFrame,
    idx: dict[str, float],
    median: dict[tuple, float],
) -> dict:
    """
    Exhaustively evaluate all 2³ = 8 stadium assignments for one group
    across all three matchdays and return the best.

    Each matchday has two simultaneous matches in two different stadiums.
    MD_PAIRS[md] = [[i,j],[k,l]] → teams[i] vs teams[j] and teams[k] vs teams[l].
    The only degree of freedom per matchday: which match gets stadium s1 vs s2.
    """
    md_config = GROUP_MD_STADIUMS.get(group, {})
    best_revenue = -1.0
    best_assignment: list[dict] = []
    best_md_revenues: dict[int, float] = {}

    for flips in itertools.product([False, True], repeat=3):
        total = 0.0
        assignment: list[dict] = []
        md_revenues: dict[int, float] = {}

        for md_idx, md in enumerate([1, 2, 3]):
            pairs  = MD_PAIRS[md]
            cities = md_config.get(md, {})
            s1, s2 = cities.get("s1", ""), cities.get("s2", "")
            date1, date2 = cities.get("d1", ""), cities.get("d2", "")

            if not s1 or not s2:
                continue

            flip = flips[md_idx]
            city0  = s2 if flip else s1
            city1  = s1 if flip else s2
            date0  = date2 if flip else date1
            date1_ = date1 if flip else date2

            ta0, tb0 = teams[pairs[0][0]], teams[pairs[0][1]]
            ta1, tb1 = teams[pairs[1][0]], teams[pairs[1][1]]

            a0, b0 = sorted([_alias(ta0), _alias(tb0)])
            a1, b1 = sorted([_alias(ta1), _alias(tb1)])
            lc0 = _city_alias(city0)
            lc1 = _city_alias(city1)
            key0 = f"{a0}|{b0}|{lc0}|{md}"
            key1 = f"{a1}|{b1}|{lc1}|{md}"

            rev0 = idx.get(key0) if key0 in idx else median.get((lc0, md), 0.0)
            rev1 = idx.get(key1) if key1 in idx else median.get((lc1, md), 0.0)

            # Track whether lookup hit or used fallback
            hit0 = key0 in idx
            hit1 = key1 in idx

            md_rev = rev0 + rev1
            total += md_rev
            md_revenues[md] = md_rev

            assignment.append({
                "matchday": md,
                "match_a": {
                    "teams": f"{ta0} vs {tb0}",
                    "city": city0,
                    "venue": CITY_TO_VENUE.get(city0, city0),
                    "date": date0,
                    "revenue_usd": rev0,
                    "is_estimate": not hit0,
                },
                "match_b": {
                    "teams": f"{ta1} vs {tb1}",
                    "city": city1,
                    "venue": CITY_TO_VENUE.get(city1, city1),
                    "date": date1_,
                    "revenue_usd": rev1,
                    "is_estimate": not hit1,
                },
                "md_total_usd": md_rev,
            })

        if total > best_revenue:
            best_revenue = total
            best_assignment = assignment
            best_md_revenues = md_revenues

    return {
        "group": group,
        "teams": teams,
        "assignments": best_assignment,
        "total_revenue_usd": best_revenue,
        "matchday_revenues_usd": best_md_revenues,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public: optimize_all_groups
# ─────────────────────────────────────────────────────────────────────────────

def optimize_all_groups(
    draw: dict[str, list[str]],
    revenue_df: pd.DataFrame,
) -> dict[str, dict]:
    """
    Run the exhaustive optimizer across all 12 groups.

    Parameters
    ----------
    draw       : {group: [pot1, pot2, pot3, pot4]}
    revenue_df : DataFrame loaded from app_revenue_lookup.csv

    Returns
    -------
    results : {group: {"teams", "assignments", "total_revenue_usd",
                       "matchday_revenues_usd"}}
    """
    idx, median = _get_index(revenue_df)
    results: dict[str, dict] = {}
    for group in sorted(draw.keys()):
        teams = draw[group]
        results[group] = _optimize_group(group, teams, revenue_df, idx, median)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Public: summarise_results
# ─────────────────────────────────────────────────────────────────────────────

def summarise_results(optimised: dict[str, dict]) -> pd.DataFrame:
    """
    Flatten optimised results into a summary DataFrame.
    Columns: group, teams_str, total_revenue_usd, md1_usd, md2_usd, md3_usd
    """
    rows = []
    for group, res in sorted(optimised.items()):
        md_rev = res.get("matchday_revenues_usd", {})
        rows.append({
            "group": group,
            "teams": " · ".join(res["teams"]),
            "total_revenue_usd": res["total_revenue_usd"],
            "md1_usd": md_rev.get(1, 0.0),
            "md2_usd": md_rev.get(2, 0.0),
            "md3_usd": md_rev.get(3, 0.0),
        })
    return pd.DataFrame(rows)


def total_revenue(optimised: dict[str, dict]) -> float:
    """Sum total projected revenue across all groups."""
    return sum(v["total_revenue_usd"] for v in optimised.values())


# ─────────────────────────────────────────────────────────────────────────────
# Public: all_group_options
# ─────────────────────────────────────────────────────────────────────────────

def all_group_options(
    group: str,
    teams: list[str],
    revenue_df: pd.DataFrame,
) -> list[dict]:
    """
    Return all 8 (2³) stadium-assignment combinations for one group,
    sorted best → worst by total revenue.

    Each item in the returned list:
    {
        "rank"              : int (1 = optimal),
        "total_revenue_usd" : float,
        "is_optimal"        : bool,
        "flip_pattern"      : (bool, bool, bool),   # True = swapped vs default
        "md_revenues"       : {1: float, 2: float, 3: float},
        "label"             : str  e.g. "MD1✓ MD2↔ MD3✓"
    }
    """
    from utils.official_baseline import GROUP_MD_STADIUMS, MD_PAIRS

    idx, median = _get_index(revenue_df)
    md_config   = GROUP_MD_STADIUMS.get(group, {})

    options: list[dict] = []

    for flips in itertools.product([False, True], repeat=3):
        total = 0.0
        md_revenues: dict[int, float] = {}

        for md_idx, md in enumerate([1, 2, 3]):
            pairs   = MD_PAIRS[md]
            cities  = md_config.get(md, {})
            s1, s2  = cities.get("s1", ""), cities.get("s2", "")
            if not s1 or not s2:
                continue

            flip   = flips[md_idx]
            city0  = s2 if flip else s1
            city1  = s1 if flip else s2
            lc0    = _city_alias(city0)
            lc1    = _city_alias(city1)

            ta0, tb0 = teams[pairs[0][0]], teams[pairs[0][1]]
            ta1, tb1 = teams[pairs[1][0]], teams[pairs[1][1]]

            a0, b0   = sorted([_alias(ta0), _alias(tb0)])
            a1, b1   = sorted([_alias(ta1), _alias(tb1)])
            key0     = f"{a0}|{b0}|{lc0}|{md}"
            key1     = f"{a1}|{b1}|{lc1}|{md}"

            rev0 = idx.get(key0) if key0 in idx else median.get((lc0, md), 0.0)
            rev1 = idx.get(key1) if key1 in idx else median.get((lc1, md), 0.0)

            md_rev          = rev0 + rev1
            total          += md_rev
            md_revenues[md] = md_rev

        label_parts = []
        for md_idx, md in enumerate([1, 2, 3]):
            label_parts.append(f"MD{md}{'↔' if flips[md_idx] else '✓'}")

        options.append({
            "flip_pattern"      : flips,
            "total_revenue_usd" : total,
            "md_revenues"       : md_revenues,
            "label"             : " ".join(label_parts),
        })

    options.sort(key=lambda x: x["total_revenue_usd"], reverse=True)
    best_total = options[0]["total_revenue_usd"]
    for i, opt in enumerate(options):
        opt["rank"]       = i + 1
        opt["is_optimal"] = (opt["total_revenue_usd"] == best_total and i == 0)

    return options
