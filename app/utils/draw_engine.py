"""
utils/draw_engine.py
--------------------
Constrained Monte Carlo draw engine for FIFA 2026.

Public API
----------
generate_random_draw(teams_df, seed=None) -> dict[str, list[str]]
    Returns a valid 48-team draw {group: [pot1, pot2, pot3, pot4]}
    respecting all FIFA constraints (host locks, pot structure,
    confederation caps, min-UEFA-per-group).

    Raises RuntimeError if no valid draw found in max_attempts.

is_valid_draw(draw, teams_df) -> bool
    Validates an existing draw dict against all constraints.

TEAMS_DF_COLUMNS: expected columns in the teams DataFrame.
"""

from __future__ import annotations

import random
from typing import Optional

import pandas as pd

from utils.official_baseline import GROUPS, HOST_LOCKS

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

TEAMS_DF_COLUMNS = ["team", "pot", "confederation"]

MAX_UEFA_PER_GROUP = 2
MIN_UEFA_PER_GROUP = 1
MAX_OTHER_CONF_PER_GROUP = 1   # applies to each non-UEFA confederation

N_GROUPS = 12
N_POTS = 4

# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _conf_counts(group_teams: list[str], team_conf: dict[str, str]) -> dict[str, int]:
    """Return confederation → count for teams already in a group."""
    counts: dict[str, int] = {}
    for t in group_teams:
        c = team_conf.get(t, "UNKNOWN")
        counts[c] = counts.get(c, 0) + 1
    return counts


def _can_place(team: str, group_teams: list[str], team_conf: dict[str, str]) -> bool:
    """Return True if adding `team` to `group_teams` respects confederation caps."""
    conf = team_conf.get(team, "UNKNOWN")
    counts = _conf_counts(group_teams, team_conf)
    current = counts.get(conf, 0)
    if conf == "UEFA":
        return current < MAX_UEFA_PER_GROUP
    else:
        return current < MAX_OTHER_CONF_PER_GROUP


def _min_uefa_satisfied(group_teams: list[str], team_conf: dict[str, str]) -> bool:
    """Return True if the group already has at least MIN_UEFA_PER_GROUP UEFA teams."""
    return sum(1 for t in group_teams if team_conf.get(t) == "UEFA") >= MIN_UEFA_PER_GROUP


# ─────────────────────────────────────────────────────────────────────────────
# Public: generate_random_draw
# ─────────────────────────────────────────────────────────────────────────────

def generate_random_draw(
    teams_df: pd.DataFrame,
    seed: Optional[int] = None,
    max_attempts: int = 5_000,
) -> dict[str, list[str]]:
    """
    Generate a valid constrained group-stage draw.

    Parameters
    ----------
    teams_df : DataFrame with columns [team, pot, confederation]
    seed     : random seed for reproducibility (None = random)
    max_attempts : maximum rejection-sampling tries before giving up

    Returns
    -------
    draw : dict[group_letter, [pot1_team, pot2_team, pot3_team, pot4_team]]
    """
    rng = random.Random(seed)
    team_conf: dict[str, str] = dict(zip(teams_df["team"], teams_df["confederation"]))
    team_pot:  dict[str, int] = dict(zip(teams_df["team"], teams_df["pot"]))

    # Build host-locked assignments (host teams are Pot 1)
    host_map: dict[str, str] = {}   # team → group
    for team, group in HOST_LOCKS.items():
        # Find the actual team name (handles "USA" / "United States" alias)
        actual = _resolve_host(team, team_conf)
        if actual:
            host_map[actual] = group

    for attempt in range(max_attempts):
        draw: dict[str, list[str]] = {g: [] for g in GROUPS}

        # Pre-fill host slots (always Pot 1, position 0)
        for team, group in host_map.items():
            draw[group] = [team]

        success = True
        for pot_num in range(1, N_POTS + 1):
            pot_teams = [t for t, p in team_pot.items() if p == pot_num]
            # Remove already-placed hosts
            already_placed = {t for teams in draw.values() for t in teams}
            pot_teams = [t for t in pot_teams if t not in already_placed]

            pot_teams_shuffled = pot_teams[:]
            rng.shuffle(pot_teams_shuffled)

            # For each remaining group (those that don't yet have a Pot-N team),
            # find groups that still need a team from this pot
            groups_needing = [g for g in GROUPS if len(draw[g]) == pot_num - 1]
            rng.shuffle(groups_needing)

            placed = _assign_pot(
                pot_teams_shuffled, groups_needing, draw, team_conf, rng
            )
            if not placed:
                success = False
                break

        if not success:
            continue

        # Final check: min UEFA per group
        if all(_min_uefa_satisfied(draw[g], team_conf) for g in GROUPS):
            return draw

    raise RuntimeError(
        f"Could not find a valid draw in {max_attempts} attempts. "
        "Check confederation composition of teams_df."
    )


def _resolve_host(name: str, team_conf: dict[str, str]) -> Optional[str]:
    """Resolve host team name — handle 'USA' / 'United States' alias."""
    if name in team_conf:
        return name
    aliases = {"United States": "USA", "USA": "United States"}
    alt = aliases.get(name)
    if alt and alt in team_conf:
        return alt
    return None


def _assign_pot(
    pot_teams: list[str],
    groups_needing: list[str],
    draw: dict[str, list[str]],
    team_conf: dict[str, str],
    rng: random.Random,
) -> bool:
    """
    Depth-first backtracking assignment of pot_teams into groups_needing.
    Returns True if all groups were filled, False otherwise.
    """
    if not groups_needing:
        return True
    if not pot_teams:
        return False

    group = groups_needing[0]
    # Try each team in shuffled order
    for i, team in enumerate(pot_teams):
        if _can_place(team, draw[group], team_conf):
            draw[group].append(team)
            remaining_teams = pot_teams[:i] + pot_teams[i + 1:]
            if _assign_pot(remaining_teams, groups_needing[1:], draw, team_conf, rng):
                return True
            draw[group].pop()

    return False


# ─────────────────────────────────────────────────────────────────────────────
# Public: is_valid_draw
# ─────────────────────────────────────────────────────────────────────────────

def is_valid_draw(
    draw: dict[str, list[str]],
    teams_df: pd.DataFrame,
) -> bool:
    """
    Validate an existing draw against all FIFA constraints.
    Returns True if valid, False otherwise.
    """
    team_conf: dict[str, str] = dict(zip(teams_df["team"], teams_df["confederation"]))
    team_pot:  dict[str, int] = dict(zip(teams_df["team"], teams_df["pot"]))

    if set(draw.keys()) != set(GROUPS):
        return False

    all_teams_placed: list[str] = []
    for group in GROUPS:
        teams = draw[group]
        if len(teams) != N_POTS:
            return False

        # Pot structure: one team per pot
        pots = [team_pot.get(t) for t in teams]
        if sorted(pots) != list(range(1, N_POTS + 1)):
            return False

        # Confederation caps
        counts = _conf_counts(teams, team_conf)
        if counts.get("UEFA", 0) > MAX_UEFA_PER_GROUP:
            return False
        if counts.get("UEFA", 0) < MIN_UEFA_PER_GROUP:
            return False
        for conf, cnt in counts.items():
            if conf != "UEFA" and cnt > MAX_OTHER_CONF_PER_GROUP:
                return False

        all_teams_placed.extend(teams)

    # Each team appears exactly once
    if len(set(all_teams_placed)) != len(all_teams_placed):
        return False

    # Host locks
    for host_name, locked_group in HOST_LOCKS.items():
        actual = _resolve_host(host_name, team_conf) or host_name
        if draw.get(locked_group, [None])[0] != actual:
            return False

    return True
