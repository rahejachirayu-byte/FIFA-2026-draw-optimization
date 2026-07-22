"""
utils/validation.py
-------------------
Draw-swap validator for the FIFA 2026 scenario sandbox.

Public API
----------
validate_swap(team_a, team_b, current_draw, conf_map, pot_map, locked_teams)
    → (ok: bool, errors: list[str], warnings: list[str])

Hard blocks (ok=False):
  • Either team is a host nation (locked to a specific group)
  • The swap would exceed the confederation cap:
      – max 2 UEFA per group
      – max 1 non-UEFA confederation per group

Soft warnings (ok=True, but warn):
  • The swap crosses pot boundaries (different pot numbers)
  • Teams are already in the same group
"""

from __future__ import annotations

from utils.official_baseline import HOST_LOCKS

# ─────────────────────────────────────────────────────────────────────────────
# Constants (mirrors draw_engine.py)
# ─────────────────────────────────────────────────────────────────────────────
MAX_UEFA_PER_GROUP = 2
MAX_OTHER_CONF_PER_GROUP = 1


# ─────────────────────────────────────────────────────────────────────────────
# Public validator
# ─────────────────────────────────────────────────────────────────────────────

def validate_swap(
    team_a: str,
    team_b: str,
    current_draw: dict[str, list[str]],
    conf_map: dict[str, str],
    pot_map: dict[str, int],
    locked_teams: set[str] | None = None,
) -> tuple[bool, list[str], list[str]]:
    """
    Validate whether swapping team_a and team_b between their groups is legal.

    Parameters
    ----------
    team_a, team_b : display names matching current_draw values
    current_draw   : {group: [pot1, pot2, pot3, pot4]}
    conf_map       : {team: confederation}  (from teams_df)
    pot_map        : {team: pot_number}     (from teams_df)
    locked_teams   : set of teams that cannot be moved (defaults to HOST_LOCKS keys)

    Returns
    -------
    (ok, errors, warnings)
      ok       – True if swap is permissible (may have warnings)
      errors   – list of blocking error messages
      warnings – list of advisory messages (swap proceeds)
    """
    errors: list[str] = []
    warnings: list[str] = []

    # ── resolve locked teams ──────────────────────────────────────────────────
    if locked_teams is None:
        locked_teams = set(HOST_LOCKS.keys())

    # ── same team ─────────────────────────────────────────────────────────────
    if team_a == team_b:
        errors.append(f"Cannot swap a team with itself ({team_a}).")
        return False, errors, warnings

    # ── find current groups ───────────────────────────────────────────────────
    group_a = _find_group(team_a, current_draw)
    group_b = _find_group(team_b, current_draw)

    if group_a is None:
        errors.append(f"'{team_a}' not found in the current draw.")
        return False, errors, warnings
    if group_b is None:
        errors.append(f"'{team_b}' not found in the current draw.")
        return False, errors, warnings

    # ── same group ────────────────────────────────────────────────────────────
    if group_a == group_b:
        warnings.append(
            f"Both {team_a} and {team_b} are already in Group {group_a} — no swap needed."
        )
        return True, errors, warnings

    # ── host locks ────────────────────────────────────────────────────────────
    if team_a in locked_teams:
        errors.append(
            f"{team_a} is a host nation locked to Group {HOST_LOCKS.get(team_a, group_a)} "
            f"and cannot be moved."
        )
    if team_b in locked_teams:
        errors.append(
            f"{team_b} is a host nation locked to Group {HOST_LOCKS.get(team_b, group_b)} "
            f"and cannot be moved."
        )
    if errors:
        return False, errors, warnings

    # ── simulate the swap and check confederation caps ────────────────────────
    conf_a = conf_map.get(team_a, "UNKNOWN")
    conf_b = conf_map.get(team_b, "UNKNOWN")

    # Build post-swap group compositions
    teams_in_a_after = [t if t != team_a else team_b for t in current_draw[group_a]]
    teams_in_b_after = [t if t != team_b else team_a for t in current_draw[group_b]]

    cap_errors = _check_conf_caps(teams_in_a_after, conf_map, group_a)
    cap_errors += _check_conf_caps(teams_in_b_after, conf_map, group_b)
    errors.extend(cap_errors)

    if errors:
        return False, errors, warnings

    # ── soft warnings ─────────────────────────────────────────────────────────
    pot_a = pot_map.get(team_a)
    pot_b = pot_map.get(team_b)
    if pot_a is not None and pot_b is not None and pot_a != pot_b:
        warnings.append(
            f"Cross-pot swap: {team_a} is Pot {pot_a}, {team_b} is Pot {pot_b}. "
            f"This violates the official draw structure but is allowed in sandbox mode."
        )

    return True, errors, warnings


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _find_group(team: str, draw: dict[str, list[str]]) -> str | None:
    for group, teams in draw.items():
        if team in teams:
            return group
    return None


def _check_conf_caps(
    teams: list[str],
    conf_map: dict[str, str],
    group: str,
) -> list[str]:
    """Return a list of cap-violation messages for the given group composition."""
    counts: dict[str, int] = {}
    for t in teams:
        c = conf_map.get(t, "UNKNOWN")
        counts[c] = counts.get(c, 0) + 1

    violations: list[str] = []
    uefa_count = counts.get("UEFA", 0)
    if uefa_count > MAX_UEFA_PER_GROUP:
        violations.append(
            f"Group {group} would have {uefa_count} UEFA teams (max {MAX_UEFA_PER_GROUP})."
        )

    for conf, cnt in counts.items():
        if conf != "UEFA" and cnt > MAX_OTHER_CONF_PER_GROUP:
            violations.append(
                f"Group {group} would have {cnt} {conf} teams (max {MAX_OTHER_CONF_PER_GROUP} "
                f"per non-UEFA confederation)."
            )

    return violations


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: validate an entire draw (used by audit / tests)
# ─────────────────────────────────────────────────────────────────────────────

def audit_draw(
    draw: dict[str, list[str]],
    conf_map: dict[str, str],
    pot_map: dict[str, int],
) -> list[str]:
    """
    Return a list of all constraint violations in the given draw.
    Empty list = fully valid draw.
    """
    issues: list[str] = []
    placed: list[str] = []

    for group, teams in draw.items():
        if len(teams) != 4:
            issues.append(f"Group {group} has {len(teams)} teams (expected 4).")
            continue

        # Check one team per pot
        pots = sorted(pot_map.get(t, 0) for t in teams)
        if pots != [1, 2, 3, 4]:
            issues.append(f"Group {group} pot distribution is {pots} (expected [1,2,3,4]).")

        # Conf caps
        issues.extend(_check_conf_caps(teams, conf_map, group))

        placed.extend(teams)

    # Host locks
    for host, locked_group in HOST_LOCKS.items():
        if draw.get(locked_group, [None])[0] != host:
            actual = draw.get(locked_group, ["?"])[0]
            issues.append(
                f"Host lock violated: {host} should be in Group {locked_group} Pot-1 slot, "
                f"but found '{actual}'."
            )

    # Uniqueness
    if len(set(placed)) != len(placed):
        from collections import Counter
        dupes = [t for t, n in Counter(placed).items() if n > 1]
        issues.append(f"Duplicate teams in draw: {', '.join(dupes)}.")

    return issues
