"""
policy_logic.py
---------------
Scenario metadata, custom weighted scoring, and winners/losers computation
used by the Policy Tradeoff Lab.

This module does NOT re-run the revenue model. It reads the pre-built
app_policy_*.csv files from data/app_ready/ and provides comparison logic
on top of them.
"""

from __future__ import annotations

import pandas as pd


SCENARIO_METADATA = {
    "baseline": {
        "display_name": "Baseline",
        "tagline": "Current announced FIFA 2026 match allocation.",
        "description": (
            "The current published allocation across the 16 host venues. "
            "Used as the reference point against which every other scenario "
            "is measured."
        ),
        "priorities": ["Status quo"],
    },
    "revenue_first": {
        "display_name": "Revenue-First",
        "tagline": "Concentrate high-value matches in highest-capacity venues.",
        "description": (
            "Shifts quarter-finals, Round-of-16 matches, and several group "
            "games from smaller-capacity venues into MetLife, AT&T, and SoFi. "
            "Maximizes ticket-revenue proxy at the cost of host-country equity."
        ),
        "priorities": ["Maximize revenue", "Prioritize marquee matchups"],
    },
    "fairness": {
        "display_name": "Fairness-Constrained",
        "tagline": "Protect smaller host markets and more-even country share.",
        "description": (
            "Reduces allocation to the three dominant US venues and redistributes "
            "matches toward Canadian (BMO, BC Place) and Mexican (Akron, BBVA, "
            "Azteca) hosts. Moves a Round-of-16 match to Estadio Azteca."
        ),
        "priorities": ["Improve fairness", "Protect smaller host markets",
                       "Host-country equity"],
    },
    "low_travel": {
        "display_name": "Low-Travel",
        "tagline": "Concentrate group-stage matches in regional hubs.",
        "description": (
            "Shifts group-stage matches out of geographically peripheral venues "
            "(Lumen, Hard Rock, Gillette) into regional hubs (Levi's, "
            "Mercedes-Benz, MetLife). Reduces intra-tournament travel for "
            "teams and supporters."
        ),
        "priorities": ["Reduce travel burden", "Regional clustering"],
    },
    "balanced": {
        "display_name": "Balanced",
        "tagline": "Modest fairness lift without a revenue hit.",
        "description": (
            "A measured compromise: one extra group match for Estadio Azteca "
            "and BC Place, offset by reductions at mid-capacity US venues. "
            "Small improvements across equity and utilization with negligible "
            "revenue change."
        ),
        "priorities": ["Balanced compromise", "Iconic-venue visibility"],
    },
}


# Policy-goal → metric mapping used for the custom weighted score in the app
POLICY_GOALS = [
    ("maximize_revenue",       "Maximize revenue",           "total_revenue_usd"),
    ("improve_fairness",       "Improve fairness/equity",    "equity_score"),
    ("increase_utilization",   "Increase utilization",       "utilization_proxy"),
    ("reduce_travel",          "Reduce travel burden",       "travel_regions_touched_inverted"),
    ("protect_small_markets",  "Protect smaller host markets", "small_market_share"),
]


def normalize(series: pd.Series) -> pd.Series:
    """Min-max scale a Series to [0, 1]."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - lo) / (hi - lo)


def compute_scenario_scores(
    scenarios_df: pd.DataFrame,
    country_df: pd.DataFrame,
    weights: dict,
) -> pd.DataFrame:
    """Compute a weighted composite score for each scenario.

    weights: dict with keys matching the first element of POLICY_GOALS tuples.
             Values are numeric weights (will be normalized to sum=1).
    """
    out = scenarios_df.copy()

    # Build derived metrics we need that aren't already in scenarios_df
    # travel_regions_touched_inverted: lower is better, so invert
    out["travel_regions_touched_inverted"] = (
        out["travel_regions_touched"].max() - out["travel_regions_touched"] + 1
    )

    # small_market_share: revenue share going to Canada + Mexico combined
    small_shares = {}
    for scen in out["scenario"].unique():
        sub = country_df[country_df["scenario"] == scen]
        total = sub["revenue"].sum()
        non_usa = sub[sub["country"] != "USA"]["revenue"].sum()
        small_shares[scen] = non_usa / total if total > 0 else 0
    out["small_market_share"] = out["scenario"].map(small_shares)

    # Normalize each goal column (higher = better after normalization)
    goal_columns = {}
    for key, _label, col in POLICY_GOALS:
        goal_columns[key] = normalize(out[col])

    # Normalize weights to sum = 1 (skip zeros gracefully)
    total_weight = sum(weights.values())
    if total_weight == 0:
        norm_weights = {k: 0 for k in weights}
    else:
        norm_weights = {k: v / total_weight for k, v in weights.items()}

    composite = pd.Series([0.0] * len(out), index=out.index)
    for key, _label, _col in POLICY_GOALS:
        w = norm_weights.get(key, 0.0)
        if w > 0:
            composite = composite + w * goal_columns[key]
    out["composite_score"] = composite.round(3)

    # Store the normalized goal columns for transparency
    for key, _label, _col in POLICY_GOALS:
        out[f"{key}_norm"] = goal_columns[key].round(3)

    return out.sort_values("composite_score", ascending=False).reset_index(drop=True)


def winners_losers(
    venue_df: pd.DataFrame,
    scenario: str,
    baseline: str = "baseline",
    top_n: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (winners, losers) DataFrames of venues most changed vs baseline."""
    pivot = venue_df.pivot_table(
        index=["venue", "country"],
        columns="scenario",
        values="revenue",
        fill_value=0,
    ).reset_index()
    if scenario not in pivot.columns or baseline not in pivot.columns:
        return pd.DataFrame(), pd.DataFrame()
    pivot["delta"] = pivot[scenario] - pivot[baseline]
    pivot["delta_pct"] = (pivot["delta"] / pivot[baseline].replace(0, 1)) * 100

    winners = pivot[pivot["delta"] > 0].sort_values("delta", ascending=False).head(top_n)
    losers = pivot[pivot["delta"] < 0].sort_values("delta").head(top_n)

    winners = winners[["venue", "country", baseline, scenario, "delta", "delta_pct"]]
    losers = losers[["venue", "country", baseline, scenario, "delta", "delta_pct"]]
    return winners.reset_index(drop=True), losers.reset_index(drop=True)


def recommend_scenario(scored_df: pd.DataFrame) -> dict:
    """Return the top-scoring scenario plus runner-up for display."""
    top = scored_df.iloc[0]
    runner = scored_df.iloc[1] if len(scored_df) > 1 else None
    return {
        "top_scenario": top["scenario"],
        "top_display": SCENARIO_METADATA.get(top["scenario"], {}).get(
            "display_name", top["scenario"]
        ),
        "top_score": top["composite_score"],
        "runner_scenario": runner["scenario"] if runner is not None else None,
        "runner_display": (
            SCENARIO_METADATA.get(runner["scenario"], {}).get("display_name", runner["scenario"])
            if runner is not None else None
        ),
        "runner_score": runner["composite_score"] if runner is not None else None,
    }
