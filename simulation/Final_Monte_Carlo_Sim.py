# %% [markdown]
# # 2026 FIFA World Cup -- Monte Carlo Draw & Tournament Simulator (final_version_2)
#
# **Architecture:** Constraint-satisfaction draw engine with bounded lookahead + Elo-based Poisson match simulation
# **Mode:** Reservoir -- generate valid draws first, then sample for fast tournament sims
#
# **What this does:**
# 1. Generates thousands of estimated valid draws (respecting all FIFA constraints)
# 2. Simulates full tournaments (group stage -> R32 -> R16 -> QF -> SF -> Final)
# 3. Outputs: draw probability heatmaps, host opponent odds, title odds, advancement probabilities

# %% Setup
import sys, platform, time, json, math, os, random
_SLOTS = {"slots": True} if sys.version_info >= (3, 10) else {}
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace as _dc_replace
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import pandas as pd  # type: ignore
except ImportError:
    pd = None

try:
    from IPython.display import display
except ImportError:
    display = print

print(f"Python {sys.version.split()[0]} | NumPy {np.__version__}")
print("Ready.")

# %% Run-level constants
RUN_VERSION  = "final_version_2"
RESULTS_DIR  = Path.home() / "Downloads" / "final_version_2_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# %% Configuration flags
DRAW_SIMS               = 100_000
TOURNAMENT_SIMS         = 100_000
RANDOM_SEED             = 42
ENFORCE_MIN_UEFA        = True    # modeling assumption -- see validation report
ORDERING_MODE           = "random"  # "random" | "mcv" | "lcv"
PLACEHOLDER_MODE        = "sample"  # "sample" = pre-draw confederation sampling
TOURNAMENT_FROM_UNIQUE  = False   # if True sample only from unique draws
N_DIAG_SEEDS            = 3       # seeds for sensitivity diagnostics
DIAG_DRAWS_PER_SEED     = 3_000   # draws per diagnostic seed

# %% [markdown]
# ## Layer 1 -- Tournament Rules & Configuration

# %% Configuration
GROUPS: Tuple[str, ...] = tuple("ABCDEFGHIJKL")
GROUP_INDEX = {g: i for i, g in enumerate(GROUPS)}
GROUP_SIZE = 4
POTS = (1, 2, 3, 4)

UEFA, CONCACAF, CONMEBOL, CAF, AFC, OFC, PLACEHOLDER = (
    "UEFA", "CONCACAF", "CONMEBOL", "CAF", "AFC", "OFC", "PLACEHOLDER"
)
CONFEDS = (UEFA, CONCACAF, CONMEBOL, CAF, AFC, OFC)
CONFED_INDEX = {c: i for i, c in enumerate(CONFEDS)}

MAX_CONFED_PER_GROUP = {UEFA: 2, CONCACAF: 1, CONMEBOL: 1, CAF: 1, AFC: 1, OFC: 1}
MIN_UEFA_PER_GROUP = 1
MAX_UEFA_PER_GROUP = 2

HOST_LOCKS = {"Mexico": ("A", 1), "Canada": ("B", 1), "United States": ("D", 1)}
HOSTS = list(HOST_LOCKS.keys())

# Bracket pathways (derived from FIFA published R32 match schedule)
PATHWAY_1_GROUPS = frozenset({"A", "C", "E", "F", "I", "L"})
PATHWAY_2_GROUPS = frozenset({"B", "D", "G", "H", "J", "K"})
TOP_SEED_PAIRS = (("Spain", "Argentina"), ("France", "England"))

# Appendix B slot pattern
SLOT_PATTERN = {}
for _g in ["A", "D", "G", "J"]:
    SLOT_PATTERN[_g] = {1: 1, 2: 3, 3: 2, 4: 4}
for _g in ["B", "E", "H", "K"]:
    SLOT_PATTERN[_g] = {1: 1, 2: 4, 3: 3, 4: 2}
for _g in ["C", "F", "I", "L"]:
    SLOT_PATTERN[_g] = {1: 1, 2: 2, 3: 4, 4: 3}

GROUP_MATCHES = ((0, 1), (2, 3), (0, 2), (3, 1), (3, 0), (1, 2))

# Official R32 knockout skeleton
R32_MATCHES = (
    ("A2", "B2"), ("C1", "F2"),
    ("E1", ("3A", "3B", "3C", "3D", "3F")),
    ("F1", "C2"), ("E2", "I2"),
    ("I1", ("3C", "3D", "3F", "3G", "3H")),
    ("A1", ("3C", "3E", "3F", "3H", "3I")),
    ("L1", ("3E", "3H", "3I", "3J", "3K")),
    ("D1", ("3B", "3E", "3F", "3I", "3J")),
    ("G1", ("3A", "3E", "3H", "3I", "3J")),
    ("K2", "L2"), ("H1", "J2"),
    ("B1", ("3E", "3F", "3G", "3I", "3J")),
    ("J1", "H2"),
    ("K1", ("3D", "3E", "3I", "3J", "3L")),
    ("D2", "G2"),
)
R16_LINKS = ((0, 2), (1, 4), (3, 5), (6, 7), (10, 11), (8, 9), (13, 14), (12, 15))
QF_LINKS  = ((0, 1), (4, 5), (2, 3), (6, 7))
SF_LINKS  = ((0, 1), (2, 3))

print(f"Config: {len(GROUPS)} groups, {len(R32_MATCHES)} R32 matches")

# %% [markdown]
# ## Team Data

# %% Teams
@dataclass(frozen=True, **_SLOTS)
class Team:
    name: str
    confed: str
    pot: int
    elo: float
    fifa_rank: int = 999
    is_host: bool = False
    is_placeholder: bool = False
    placeholder_confeds: FrozenSet[str] = frozenset()


def build_teams() -> Dict[int, List[Team]]:
    pots: Dict[int, List[Team]] = {1: [], 2: [], 3: [], 4: []}

    for n, c, e, r, h in [
        ("Mexico",        CONCACAF, 1700, 15, True),
        ("Canada",        CONCACAF, 1600, 27, True),
        ("United States", CONCACAF, 1750, 14, True),
        ("Spain",         UEFA,     2050,  1, False),
        ("Argentina",     CONMEBOL, 2040,  2, False),
        ("France",        UEFA,     2020,  3, False),
        ("England",       UEFA,     2000,  4, False),
        ("Brazil",        CONMEBOL, 1980,  5, False),
        ("Portugal",      UEFA,     1960,  6, False),
        ("Netherlands",   UEFA,     1940,  7, False),
        ("Belgium",       UEFA,     1920,  8, False),
        ("Germany",       UEFA,     1910,  9, False),
    ]:
        pots[1].append(Team(n, c, 1, e, r, is_host=h))

    for n, c, e, r in [
        ("Croatia",     UEFA,     1870, 10), ("Morocco",     CAF,      1860, 11),
        ("Colombia",    CONMEBOL, 1840, 13), ("Uruguay",     CONMEBOL, 1830, 16),
        ("Switzerland", UEFA,     1820, 17), ("Japan",       AFC,      1810, 18),
        ("Senegal",     CAF,      1790, 19), ("Iran",        AFC,      1780, 20),
        ("South Korea", AFC,      1770, 21), ("Ecuador",     CONMEBOL, 1760, 22),
        ("Austria",     UEFA,     1750, 23), ("Australia",   AFC,      1740, 24),
    ]:
        pots[2].append(Team(n, c, 2, e, r))

    for n, c, e, r in [
        ("Norway",       UEFA,     1710, 29), ("Panama",       CONCACAF, 1660, 30),
        ("Egypt",        CAF,      1650, 34), ("Algeria",      CAF,      1640, 35),
        ("Scotland",     UEFA,     1630, 36), ("Paraguay",     CONMEBOL, 1620, 39),
        ("Tunisia",      CAF,      1610, 40), ("Ivory Coast",  CAF,      1600, 41),
        ("Uzbekistan",   AFC,      1580, 42), ("Qatar",        AFC,      1570, 43),
        ("Saudi Arabia", AFC,      1560, 44), ("South Africa", CAF,      1540, 45),
    ]:
        pots[3].append(Team(n, c, 3, e, r))

    for n, c, e, r in [
        ("Jordan",     AFC,      1460, 66), ("Cape Verde",  CAF,      1440, 68),
        ("Ghana",      CAF,      1430, 72), ("Curacao",     CONCACAF, 1380, 82),
        ("Haiti",      CONCACAF, 1370, 84), ("New Zealand", OFC,      1360, 85),
    ]:
        pots[4].append(Team(n, c, 4, e, r))

    for name, rank in [("UEFA Path A", 90), ("UEFA Path B", 91),
                       ("UEFA Path C", 92), ("UEFA Path D", 93)]:
        pots[4].append(Team(name, UEFA, 4, 1500, rank,
                            is_placeholder=True, placeholder_confeds=frozenset([UEFA])))

    pots[4].append(Team("IC Path 1", PLACEHOLDER, 4, 1450, 94,
                        is_placeholder=True,
                        placeholder_confeds=frozenset([OFC, CONCACAF, CAF])))
    pots[4].append(Team("IC Path 2", PLACEHOLDER, 4, 1450, 95,
                        is_placeholder=True,
                        placeholder_confeds=frozenset([CONMEBOL, CONCACAF, AFC])))
    return pots


ALL_TEAMS = {t.name: t for pot in build_teams().values() for t in pot}
MAJOR_TEAMS = [t.name for t in build_teams()[1] + build_teams()[2]]

print(f"Teams: {len(ALL_TEAMS)} total, {len(MAJOR_TEAMS)} tracked in heatmap")
for p in POTS:
    print(f"  Pot {p}: {', '.join(t.name for t in build_teams()[p])}")

# %% [markdown]
# ## Placeholder Realization

# %% realize_pots
def realize_pots(base_pots: dict, rng: random.Random) -> dict:
    """
    Pre-draw placeholder realization (PLACEHOLDER_MODE='sample').
    Each placeholder with multiple possible confederations is assigned
    exactly one confederation by random sampling before the draw begins.
    This prevents the original bug where one placeholder simultaneously
    incremented all its possible confederation counts.
    """
    realized = {}
    for pot, teams in base_pots.items():
        realized[pot] = []
        for t in teams:
            if t.is_placeholder and len(t.placeholder_confeds) > 1:
                conf = rng.choice(sorted(t.placeholder_confeds))
                t = _dc_replace(t, confed=conf, is_placeholder=False,
                                placeholder_confeds=frozenset())
            realized[pot].append(t)
    return realized

# %% [markdown]
# ## Layer 2 & 3 -- Draw Engine + Constraint Engine

# %% Draw Engine
@dataclass(**_SLOTS)
class DrawState:
    groups: List[List[Optional[Team]]]
    confed_counts: List[List[int]]
    uefa_counts: List[int]
    pathway_p1: List[str]
    pathway_p2: List[str]
    remaining: Dict[int, List[Team]]

    @classmethod
    def create(cls, pots):
        return cls(
            groups=[[None] * GROUP_SIZE for _ in range(len(GROUPS))],
            confed_counts=[[0] * len(CONFEDS) for _ in range(len(GROUPS))],
            uefa_counts=[0] * len(GROUPS),
            pathway_p1=[], pathway_p2=[],
            remaining={p: list(ts) for p, ts in pots.items()},
        )

    def clone(self):
        return DrawState(
            groups=[row[:] for row in self.groups],
            confed_counts=[row[:] for row in self.confed_counts],
            uefa_counts=self.uefa_counts[:],
            pathway_p1=self.pathway_p1[:],
            pathway_p2=self.pathway_p2[:],
            remaining={p: ts[:] for p, ts in self.remaining.items()},
        )

    def slot_available(self, g_idx, pot):
        pos = SLOT_PATTERN[GROUPS[g_idx]][pot] - 1
        return self.groups[g_idx][pos] is None

    def group_team_count(self, g_idx):
        return sum(1 for t in self.groups[g_idx] if t is not None)

    def place_team(self, team, g_idx):
        pos = SLOT_PATTERN[GROUPS[g_idx]][team.pot] - 1
        self.groups[g_idx][pos] = team
        if team.confed in CONFED_INDEX:
            self.confed_counts[g_idx][CONFED_INDEX[team.confed]] += 1
        if team.confed == UEFA:
            self.uefa_counts[g_idx] += 1
        if team.pot == 1:
            if GROUPS[g_idx] in PATHWAY_1_GROUPS:
                self.pathway_p1.append(team.name)
            else:
                self.pathway_p2.append(team.name)
        self.remaining[team.pot].remove(team)


def is_feasible(team, g_idx, state):
    if not state.slot_available(g_idx, team.pot):
        return False
    if state.group_team_count(g_idx) >= GROUP_SIZE:
        return False
    is_team_uefa = (team.confed == UEFA)
    if ENFORCE_MIN_UEFA and state.group_team_count(g_idx) == GROUP_SIZE - 1 \
            and state.uefa_counts[g_idx] == 0 and not is_team_uefa:
        return False
    if team.confed == UEFA:
        if state.uefa_counts[g_idx] >= MAX_UEFA_PER_GROUP:
            return False
    elif team.confed in CONFED_INDEX:
        if state.confed_counts[g_idx][CONFED_INDEX[team.confed]] >= \
                MAX_CONFED_PER_GROUP.get(team.confed, 99):
            return False
    if team.pot == 1 and team.name in ("Spain", "Argentina", "France", "England"):
        pathway = state.pathway_p1 if GROUPS[g_idx] in PATHWAY_1_GROUPS else state.pathway_p2
        for a, b in TOP_SEED_PAIRS:
            if team.name == a and b in pathway:
                return False
            if team.name == b and a in pathway:
                return False
    return True


def global_capacity_ok(state: DrawState) -> bool:
    """
    Forward-check: verify remaining teams can still be placed without
    overflowing confederation slot capacities. Returns False early if
    any confederation has more remaining teams than available slots.
    """
    for confed in CONFEDS:
        if confed not in CONFED_INDEX:
            continue
        limit = MAX_CONFED_PER_GROUP.get(confed, 1 if confed != UEFA else MAX_UEFA_PER_GROUP)
        n_rem = sum(1 for pot in POTS for t in state.remaining[pot] if t.confed == confed)
        if n_rem == 0:
            continue
        capacity = sum(
            max(0, limit - state.confed_counts[g][CONFED_INDEX[confed]])
            for g in range(len(GROUPS))
        )
        if n_rem > capacity:
            return False
    return True


def validate_draw(state):
    for g_idx in range(len(GROUPS)):
        teams = [t for t in state.groups[g_idx] if t is not None]
        if len(teams) != GROUP_SIZE:
            return False
        uefa_ct = sum(1 for t in teams if t.confed == UEFA)
        if ENFORCE_MIN_UEFA and not (MIN_UEFA_PER_GROUP <= uefa_ct <= MAX_UEFA_PER_GROUP):
            return False
        elif not ENFORCE_MIN_UEFA and uefa_ct > MAX_UEFA_PER_GROUP:
            return False
        counts = Counter(t.confed for t in teams)
        for c, ct in counts.items():
            if c != UEFA and c in MAX_CONFED_PER_GROUP and ct > MAX_CONFED_PER_GROUP[c]:
                return False
    return True


class ExactSequentialDrawEngine:
    """Sequential physical draw order with bounded deep lookahead."""

    def __init__(self, pots, rng, ordering="random"):
        self.pots = pots
        self.rng = rng
        self.ordering = ordering
        self._stats = defaultdict(int)

    @property
    def stats(self):
        return dict(self._stats)

    def run(self):
        state = DrawState.create(self.pots)
        for team_name, (group, _) in HOST_LOCKS.items():
            team = next(t for t in state.remaining[1] if t.name == team_name)
            state.place_team(team, GROUP_INDEX[group])
        for pot in POTS:
            if not self._draw_pot(state, pot):
                return None
        return state

    def _draw_pot(self, state, pot):
        teams = state.remaining[pot][:]
        if self.ordering == "random":
            self.rng.shuffle(teams)
        elif self.ordering == "mcv":
            teams.sort(key=lambda t: sum(1 for g in range(len(GROUPS)) if is_feasible(t, g, state)))
        elif self.ordering == "lcv":
            teams.sort(key=lambda t: sum(1 for g in range(len(GROUPS)) if is_feasible(t, g, state)), reverse=True)
        for team in teams:
            feasible = [g for g in range(len(GROUPS)) if is_feasible(team, g, state)]
            self.rng.shuffle(feasible)
            placed = False
            for g_idx in feasible:
                if self._bounded_lookahead(state, pot, team, g_idx):
                    state.place_team(team, g_idx)
                    placed = True
                    break
            if not placed:
                return False
        return True

    def _bounded_lookahead(self, state, pot, team, g_idx):
        test = state.clone()
        test.place_team(team, g_idx)
        if not global_capacity_ok(test):
            self._stats["global_prunes"] += 1
            return False
        remaining = test.remaining[pot][:]
        remaining.sort(key=lambda t: sum(1 for gi in range(len(GROUPS)) if is_feasible(t, gi, test)))
        if not self._dfs_pot(test, remaining, 0):
            return False
        for fp in range(pot + 1, 5):
            for ft in test.remaining[fp]:
                if not any(is_feasible(ft, gi, test) for gi in range(len(GROUPS))):
                    return False
        return True

    def _dfs_pot(self, state, teams, idx):
        if idx >= len(teams):
            return True
        team = teams[idx]
        feasible = [g for g in range(len(GROUPS)) if is_feasible(team, g, state)]
        if not feasible:
            return False
        feasible.sort(key=lambda gi: state.group_team_count(gi))
        for g_idx in feasible:
            saved = state.clone()
            state.place_team(team, g_idx)
            ok = all(
                any(is_feasible(teams[j], gi, state) for gi in range(len(GROUPS)))
                for j in range(idx + 1, len(teams))
            )
            if ok and self._dfs_pot(state, teams, idx + 1):
                return True
            self._stats["backtracks"] += 1
            state.groups = saved.groups
            state.confed_counts = saved.confed_counts
            state.uefa_counts = saved.uefa_counts
            state.pathway_p1 = saved.pathway_p1
            state.pathway_p2 = saved.pathway_p2
            state.remaining = saved.remaining
        return False


def freeze_draw(state):
    return tuple(tuple(t.name for t in row) for row in state.groups)

def thaw_draw(frozen):
    return {GROUPS[i]: [ALL_TEAMS[name] for name in row] for i, row in enumerate(frozen)}

# Quick sanity test
_base_pots = build_teams()
_rng_sanity = random.Random(42)
_realized_sanity = realize_pots(_base_pots, _rng_sanity)
_eng = ExactSequentialDrawEngine(_realized_sanity, _rng_sanity, ordering=ORDERING_MODE)
_test = _eng.run()
assert _test is not None and validate_draw(_test), "Sanity check failed!"
print("Draw engine OK -- sanity test passed")

# %% [markdown]
# ## Match Engine (Elo + Poisson)

# %% Match Engine
def expected_goals_from_elo(elo_a, elo_b):
    diff = max(-600.0, min(600.0, elo_a - elo_b))
    base_total = 2.55
    share_a = 1.0 / (1.0 + math.exp(-diff / 180.0))
    lam_a = max(0.35, min(2.75, base_total * share_a))
    lam_b = max(0.35, min(2.75, base_total * (1.0 - share_a)))
    return lam_a, lam_b


def poisson_match(a, b, rng, knockout=False):
    lam_a, lam_b = expected_goals_from_elo(a.elo, b.elo)
    g_a, g_b = int(rng.poisson(lam_a)), int(rng.poisson(lam_b))
    if not knockout:
        winner = a if g_a > g_b else b if g_b > g_a else None
        return g_a, g_b, winner
    if g_a != g_b:
        return g_a, g_b, a if g_a > g_b else b
    et_a, et_b = int(rng.poisson(lam_a * 0.33)), int(rng.poisson(lam_b * 0.33))
    g_a += et_a; g_b += et_b
    if g_a != g_b:
        return g_a, g_b, a if g_a > g_b else b
    p_a = 0.5 + max(-0.12, min(0.12, (a.elo - b.elo) / 3000.0))
    return g_a, g_b, a if rng.random() < p_a else b


@dataclass(**_SLOTS)
class GroupRecord:
    team: Team
    points: int = 0
    gf: int = 0
    ga: int = 0
    gd: int = 0
    fair_play: float = 0.0

    def tiebreak_key(self, rng_val):
        return (self.points, self.gd, self.gf, -self.fair_play, rng_val, -self.team.fifa_rank)


def simulate_group(teams, rng):
    table = {t.name: GroupRecord(team=t) for t in teams}
    for i, j in GROUP_MATCHES:
        a, b = teams[i], teams[j]
        ga, gb, _ = poisson_match(a, b, rng)
        ra, rb = table[a.name], table[b.name]
        ra.gf += ga; ra.ga += gb; rb.gf += gb; rb.ga += ga
        ra.fair_play += float(rng.uniform()); rb.fair_play += float(rng.uniform())
        if ga > gb:   ra.points += 3
        elif gb > ga: rb.points += 3
        else:         ra.points += 1; rb.points += 1
    for r in table.values():
        r.gd = r.gf - r.ga
    return sorted(table.values(), key=lambda r: r.tiebreak_key(float(rng.random())), reverse=True)


def rank_best_thirds(thirds, rng):
    return sorted(thirds, key=lambda x: (
        x[1].points, x[1].gd, x[1].gf, -x[1].fair_play, float(rng.random()), -x[1].team.fifa_rank
    ), reverse=True)


def resolve_r32_pairings(rankings, rng):
    qualified = {}
    third_records = []
    for g, ranked in rankings.items():
        qualified[f"{g}1"] = ranked[0].team
        qualified[f"{g}2"] = ranked[1].team
        qualified[f"{g}3"] = ranked[2].team
        third_records.append((g, ranked[2]))
    best_thirds = rank_best_thirds(third_records, rng)[:8]
    best_third_groups = {g for g, _ in best_thirds}
    remaining_tokens = {f"3{g}": rec.team for g, rec in best_thirds}
    pairings = []
    for left, right in R32_MATCHES:
        team_left = qualified[left]
        if isinstance(right, tuple):
            eligible = [t for t in right if t[1] in best_third_groups and t in remaining_tokens]
            if not eligible:
                eligible = sorted(remaining_tokens.keys())
            ranked_t = [f"3{g}" for g, _ in best_thirds if f"3{g}" in eligible]
            token = ranked_t[0] if ranked_t else eligible[0]
            team_right = remaining_tokens.pop(token)
        else:
            team_right = qualified[right]
        pairings.append((team_left, team_right))
    return pairings


def simulate_knockout(rankings, rng):
    r32 = resolve_r32_pairings(rankings, rng)
    stage_reached = defaultdict(int)
    def play_round(matchups, stage_code):
        winners = []
        for a, b in matchups:
            stage_reached[a.name] = max(stage_reached[a.name], stage_code)
            stage_reached[b.name] = max(stage_reached[b.name], stage_code)
            _, _, w = poisson_match(a, b, rng, knockout=True)
            winners.append(w)
        return winners
    r16_t = play_round(r32, 1)
    r16 = [(r16_t[i], r16_t[j]) for i, j in R16_LINKS]
    qf_t = play_round(r16, 2)
    qf = [(qf_t[i], qf_t[j]) for i, j in QF_LINKS]
    sf_t = play_round(qf, 3)
    sf = [(sf_t[i], sf_t[j]) for i, j in SF_LINKS]
    fin_t = play_round(sf, 4)
    champ = play_round([(fin_t[0], fin_t[1])], 5)[0]
    stage_reached[champ.name] = 6
    return dict(stage_reached)


def simulate_tournament(frozen, seed):
    rng = np.random.default_rng(seed)
    groups = thaw_draw(frozen)
    rankings = {g: simulate_group(teams, rng) for g, teams in groups.items()}
    win_group = {rankings[g][0].team.name for g in rankings}
    top2 = set()
    for g, ranked in rankings.items():
        top2.add(ranked[0].team.name); top2.add(ranked[1].team.name)
    thirds = rank_best_thirds([(g, rankings[g][2]) for g in rankings], rng)
    advanced = set(top2)
    advanced.update(rankings[g][2].team.name for g, _ in thirds[:8])
    stages = simulate_knockout(rankings, rng)
    return {"win_group": tuple(win_group), "advance_r32": tuple(advanced), "stage_reached": stages}

print("Match engine OK")

# %% [markdown]
# ## Aggregation & Plotting

# %% Aggregator
@dataclass(**_SLOTS)
class Aggregator:
    draw_successes: int = 0
    draw_matrix: Dict[str, np.ndarray] = field(default_factory=dict)
    host_opponents: Dict[str, Counter] = field(default_factory=dict)
    win_group: Counter = field(default_factory=Counter)
    advance_r32: Counter = field(default_factory=Counter)
    qf: Counter = field(default_factory=Counter)
    sf: Counter = field(default_factory=Counter)
    finalist: Counter = field(default_factory=Counter)
    champion: Counter = field(default_factory=Counter)
    draw_unique_set: set = field(default_factory=set)

    def __post_init__(self):
        if not self.draw_matrix:
            self.draw_matrix = {n: np.zeros(len(GROUPS), dtype=np.int64) for n in MAJOR_TEAMS}
        if not self.host_opponents:
            self.host_opponents = {h: Counter() for h in HOSTS}

    def absorb_draw(self, frozen):
        self.draw_successes += 1
        self.draw_unique_set.add(frozen)
        groups = thaw_draw(frozen)
        team_to_group = {}
        for g, teams in groups.items():
            for t in teams:
                team_to_group[t.name] = g
                if t.name in self.draw_matrix:
                    self.draw_matrix[t.name][GROUP_INDEX[g]] += 1
        for host in HOSTS:
            g = team_to_group[host]
            for t in groups[g]:
                if t.name != host:
                    self.host_opponents[host][t.name] += 1

    def absorb_tournament(self, result):
        for t in result["win_group"]:    self.win_group[t] += 1
        for t in result["advance_r32"]:  self.advance_r32[t] += 1
        for team, stage in result["stage_reached"].items():
            if stage >= 3: self.qf[team] += 1
            if stage >= 4: self.sf[team] += 1
            if stage >= 5: self.finalist[team] += 1
            if stage >= 6: self.champion[team] += 1

    @property
    def unique_draw_count(self):
        return len(self.draw_unique_set)


def plot_draw_heatmap(agg, n_unique):
    teams = MAJOR_TEAMS
    data = np.vstack([agg.draw_matrix[t] / max(1, agg.draw_successes) for t in teams])
    fig, ax = plt.subplots(figsize=(14, 10))
    im = ax.imshow(data, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(GROUPS))); ax.set_xticklabels(GROUPS)
    ax.set_yticks(range(len(teams))); ax.set_yticklabels(teams, fontsize=9)
    ax.set_title(
        f"Estimated Group Placement Probabilities\n"
        f"({agg.draw_successes:,} simulated valid draws, {n_unique:,} unique)",
        fontsize=14
    )
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            if v > 0:
                color = "white" if v < 0.08 else "black"
                ax.text(j, i, f"{100*v:.1f}%", ha="center", va="center", fontsize=7, color=color)
    fig.colorbar(im, ax=ax, label="Probability")
    fig.tight_layout()
    path = RESULTS_DIR / "final_version_2_draw_matrix.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  {path}")


def plot_host_opponents(agg):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Host Nation Opponent Probabilities (Estimated)", fontsize=14, fontweight="bold")
    for ax, host in zip(axes, HOSTS):
        items = agg.host_opponents[host].most_common(10)
        labels = [x[0] for x in items][::-1]
        vals = [x[1] / max(1, agg.draw_successes) for x in items][::-1]
        ax.barh(labels, vals, color="steelblue")
        ax.set_title(host, fontsize=12); ax.set_xlabel("Probability")
        for i, v in enumerate(vals):
            ax.text(v + 0.002, i, f"{100*v:.1f}%", va="center", fontsize=8)
    fig.tight_layout()
    path = RESULTS_DIR / "final_version_2_host_opponents.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  {path}")


def plot_title_odds(agg, n_tourn):
    items = sorted(agg.champion.items(), key=lambda x: x[1], reverse=True)[:15]
    labels = [x[0] for x in items][::-1]
    vals = [x[1] / max(1, n_tourn) for x in items][::-1]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(labels, vals, color="steelblue")
    ax.set_title("Estimated Title Odds (Top 15)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Win Probability")
    for i, v in enumerate(vals):
        ax.text(v + 0.002, i, f"{100*v:.2f}%", va="center", fontsize=9)
    fig.tight_layout()
    path = RESULTS_DIR / "final_version_2_title_odds.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  {path}")


def plot_advancement(agg, n_tourn):
    items = sorted(agg.advance_r32.items(), key=lambda x: x[1], reverse=True)[:25]
    labels = [x[0] for x in items][::-1]
    vals = [x[1] / max(1, n_tourn) for x in items][::-1]
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.barh(labels, vals, color="teal")
    ax.set_title("Estimated Advancement Probability -- Top 25", fontsize=13)
    ax.set_xlabel("Probability")
    for i, v in enumerate(vals):
        ax.text(v + 0.005, i, f"{100*v:.1f}%", va="center", fontsize=8)
    fig.tight_layout()
    path = RESULTS_DIR / "final_version_2_advancement.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"  {path}")


def write_simulation_summary(agg, n_tourn: int, stats_dict: dict):
    leaderboard = []
    for team in sorted(agg.champion):
        if agg.champion[team] > 0:
            leaderboard.append({
                "team": team,
                "qf_prob": round(agg.qf[team] / max(1, n_tourn), 4),
                "sf_prob": round(agg.sf[team] / max(1, n_tourn), 4),
                "final_prob": round(agg.finalist[team] / max(1, n_tourn), 4),
                "win_prob": round(agg.champion[team] / max(1, n_tourn), 4),
            })
    leaderboard.sort(key=lambda x: x["win_prob"], reverse=True)

    draw_probs = {
        team: {
            g: round(int(agg.draw_matrix[team][GROUP_INDEX[g]]) / max(1, agg.draw_successes), 4)
            for g in GROUPS
        }
        for team in MAJOR_TEAMS
    }
    payload = {
        "run_version": RUN_VERSION,
        "note": "All probabilities are Monte Carlo estimates under the current heuristic draw engine.",
        "draw_successes": agg.draw_successes,
        "unique_draws": stats_dict["unique_draws"],
        "duplicate_ratio": round(1 - stats_dict["unique_draws"] / max(1, agg.draw_successes), 4),
        "tournament_sims": n_tourn,
        "leaderboard": leaderboard[:20],
        "estimated_draw_probabilities": draw_probs,
        "host_opponents": {
            h: {k: round(v / max(1, agg.draw_successes), 4)
                for k, v in agg.host_opponents[h].most_common(15)}
            for h in HOSTS
        },
    }
    path = RESULTS_DIR / "final_version_2_simulation_summary.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  {path}")


def write_draw_matrix_csv(agg):
    rows = []
    for team in MAJOR_TEAMS:
        row = {"team": team}
        for g in GROUPS:
            row[f"group_{g}"] = round(agg.draw_matrix[team][GROUP_INDEX[g]] / max(1, agg.draw_successes), 4)
        rows.append(row)
    import pandas as pd
    df = pd.DataFrame(rows).set_index("team")
    path = RESULTS_DIR / "final_version_2_draw_matrix.csv"
    df.to_csv(path)
    print(f"  {path}")


def write_draw_probabilities_long_csv(agg):
    """
    Long-format CSV: one row per (team, group) pair.
    Includes confidence intervals, structural impossibility flags, and metadata.
    """
    import pandas as pd

    POT_MAP = {t.name: t.pot for pot_teams in build_teams().values() for t in pot_teams}
    CONF_MAP = {t.name: t.confed for pot_teams in build_teams().values() for t in pot_teams}

    HOST_GROUPS = {v[0] for v in HOST_LOCKS.values()}

    rows = []
    n = agg.draw_successes
    for team in MAJOR_TEAMS:
        pot  = POT_MAP.get(team, 0)
        conf = CONF_MAP.get(team, "")
        is_host   = team in HOST_LOCKS
        lock_grp  = HOST_LOCKS.get(team, (None,))[0]

        for g in GROUPS:
            k = int(agg.draw_matrix[team][GROUP_INDEX[g]])
            p = k / max(1, n)
            se = math.sqrt(p * (1 - p) / max(1, n))
            lo = max(0.0, p - 1.96 * se)
            hi = min(1.0, p + 1.96 * se)

            # Structural impossibility
            struct_impossible = False
            if is_host and g != lock_grp:
                struct_impossible = True
            elif pot == 1 and not is_host and g in HOST_GROUPS:
                struct_impossible = True

            rows.append({
                "team":                   team,
                "group":                  g,
                "count":                  k,
                "probability":            round(p, 6),
                "lower_ci_95":            round(lo, 6),
                "upper_ci_95":            round(hi, 6),
                "pot":                    pot,
                "confederation":          conf,
                "is_host":                is_host,
                "is_locked":              is_host,
                "locked_to_group":        lock_grp if is_host else "",
                "structurally_impossible": struct_impossible,
                "observed_zero":          (k == 0),
            })

    df = pd.DataFrame(rows)
    path = RESULTS_DIR / "final_version_2_draw_probabilities_long.csv"
    df.to_csv(path, index=False)
    print(f"  {path}")


def save_unique_draws_sample(unique_frozen: set, agg):
    sample = list(unique_frozen)[:500]
    draws_list = []
    for frozen in sample:
        entry = {}
        for g_idx, group_letter in enumerate(GROUPS):
            entry[group_letter] = list(frozen[g_idx])
        draws_list.append(entry)
    payload = {
        "run_version": RUN_VERSION,
        "total_unique_draws": len(unique_frozen),
        "sample_size": len(draws_list),
        "draws": draws_list,
    }
    path = RESULTS_DIR / "final_version_2_unique_draws.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  {path}")


def write_config_json(stats_dict: dict, t_draw: float, t_tourn: float):
    cfg = {
        "run_version": RUN_VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "random_seed": RANDOM_SEED,
        "draw_sims_attempted": DRAW_SIMS,
        "valid_draws_collected": stats_dict["valid_draws"],
        "unique_draws_collected": stats_dict["unique_draws"],
        "duplicate_ratio": round(1 - stats_dict["unique_draws"] / max(1, stats_dict["valid_draws"]), 4),
        "tournament_sims": TOURNAMENT_SIMS,
        "tournament_from_unique": TOURNAMENT_FROM_UNIQUE,
        "placeholder_mode": PLACEHOLDER_MODE,
        "ordering_mode": ORDERING_MODE,
        "enforce_min_uefa_per_group": ENFORCE_MIN_UEFA,
        "enforce_min_uefa_note": "Modeling assumption. With 16 UEFA teams and max 2 per group, this constraint is mathematically guaranteed to be satisfied regardless.",
        "total_backtracks": stats_dict["backtracks"],
        "total_global_prunes": stats_dict["global_prunes"],
        "draw_phase_seconds": round(t_draw, 1),
        "tournament_phase_seconds": round(t_tourn, 1),
        "total_seconds": round(t_draw + t_tourn, 1),
        "output_files": [str(RESULTS_DIR / f) for f in [
            "final_version_2_draw_matrix.png",
            "final_version_2_host_opponents.png",
            "final_version_2_title_odds.png",
            "final_version_2_advancement.png",
            "final_version_2_simulation_summary.json",
            "final_version_2_validation_report.json",
            "final_version_2_draw_matrix.csv",
            "final_version_2_draw_probabilities_long.csv",
            "final_version_2_unique_draws.json",
            "final_version_2_config.json",
        ]],
    }
    path = RESULTS_DIR / "final_version_2_config.json"
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"  {path}")


def write_validation_report(agg, stats_dict: dict):
    report = {
        "run_version": RUN_VERSION,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "assumptions": {
            "enforce_min_uefa_per_group": ENFORCE_MIN_UEFA,
            "min_uefa_note": "Requires >=1 UEFA team per group. This is mathematically guaranteed given 16 UEFA teams and max-2-per-group cap, so this flag has no practical effect when True.",
            "max_uefa_per_group": MAX_UEFA_PER_GROUP,
            "max_confed_per_group": MAX_CONFED_PER_GROUP,
            "placeholder_handling": "Pre-draw confederation sampling. Each placeholder is assigned one concrete confederation by uniform random sampling before each draw attempt. No simultaneous multi-confederation counting.",
            "pathway_constraint": "Spain/Argentina and France/England cannot be in same R32 half.",
            "host_locks": HOST_LOCKS,
        },
        "draw_stats": {
            "attempts": DRAW_SIMS,
            "valid": stats_dict["valid_draws"],
            "unique": stats_dict["unique_draws"],
            "success_rate": round(stats_dict["valid_draws"] / max(1, DRAW_SIMS), 4),
            "duplicate_ratio": round(1 - stats_dict["unique_draws"] / max(1, stats_dict["valid_draws"]), 4),
            "total_backtracks": stats_dict["backtracks"],
            "global_prunes": stats_dict["global_prunes"],
        },
        "honesty_notes": [
            "Probabilities are Monte Carlo estimates, not analytically exact values.",
            "The draw engine uses a heuristic sequential approach with bounded lookahead, not full exhaustive enumeration.",
            "Results are conditional on the placeholder confederation sampling distribution.",
            "Tournament results use an uncalibrated Elo-Poisson model. No historical calibration was performed.",
            "Tiebreak fair-play column is a uniform random noise fallback, not a real card model.",
            "Extra time goal model uses 33% of regular-time lambda as a rough heuristic.",
        ],
        "seed": RANDOM_SEED,
        "ordering_mode": ORDERING_MODE,
        "placeholder_mode": PLACEHOLDER_MODE,
    }
    path = RESULTS_DIR / "final_version_2_validation_report.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  {path}")


def run_seed_diagnostics(base_pots: dict, n_per_seed: int = DIAG_DRAWS_PER_SEED) -> dict:
    """
    Run mini-samples across N_DIAG_SEEDS different seeds and compute
    max absolute deviation in group-placement probabilities.
    Returns a dict with seed -> {team -> group -> prob} and deviation stats.
    """
    print(f"\nDiagnostics: seed sensitivity ({N_DIAG_SEEDS} seeds x {n_per_seed:,} draws)...")
    seed_results = {}
    diag_seeds = [RANDOM_SEED + 100_000 + i * 31337 for i in range(N_DIAG_SEEDS)]

    for seed in diag_seeds:
        rng = random.Random(seed)
        mini_agg = Aggregator()
        for _ in range(n_per_seed):
            realized = realize_pots(base_pots, rng)
            eng = ExactSequentialDrawEngine(realized, rng, ordering=ORDERING_MODE)
            st = eng.run()
            if st is not None and validate_draw(st):
                mini_agg.absorb_draw(freeze_draw(st))
        probs = {
            team: {
                g: mini_agg.draw_matrix[team][GROUP_INDEX[g]] / max(1, mini_agg.draw_successes)
                for g in GROUPS
            }
            for team in MAJOR_TEAMS
        }
        seed_results[seed] = {"n_valid": mini_agg.draw_successes, "probs": probs}
        print(f"  seed {seed}: {mini_agg.draw_successes} valid draws")

    # Compute max absolute deviation across seeds for each (team, group)
    max_devs = {}
    for team in MAJOR_TEAMS:
        for g in GROUPS:
            vals = [seed_results[s]["probs"][team][g] for s in diag_seeds]
            max_devs[(team, g)] = max(vals) - min(vals)

    overall_max = max(max_devs.values())
    p95 = sorted(max_devs.values())[int(0.95 * len(max_devs))]

    report = {
        "run_version": RUN_VERSION,
        "method": "seed_sensitivity",
        "diag_seeds": diag_seeds,
        "draws_per_seed": [seed_results[s]["n_valid"] for s in diag_seeds],
        "max_absolute_deviation_overall": round(overall_max, 4),
        "p95_absolute_deviation": round(p95, 4),
        "interpretation": (
            "Max absolute deviation across seeds in any single (team, group) cell. "
            "Values < 0.01 suggest stable estimates; > 0.05 suggests high uncertainty."
        ),
        "top_unstable_cells": sorted(
            [{"team": t, "group": g, "max_dev": round(v, 4)} for (t, g), v in max_devs.items()],
            key=lambda x: x["max_dev"], reverse=True
        )[:20],
    }
    path = RESULTS_DIR / "final_version_2_bias_diagnostics.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  {path}  (max_dev={overall_max:.4f}, p95={p95:.4f})")
    return report

print("Aggregator & plotting OK")

# %% [markdown]
# ## Run Simulation

# %% Run
print("=" * 60)
print("  2026 FIFA WORLD CUP -- MONTE CARLO SIMULATION (final_version_2)")
print("=" * 60)

# Phase 1: Build draw reservoir
print(f"\nPhase 1: Building draw reservoir ({DRAW_SIMS:,} attempts)...")

t0 = time.time()
reservoir        = []
unique_frozen    = set()
base_pots        = build_teams()
rng_draw         = random.Random(RANDOM_SEED)
total_backtracks = 0
total_gprunes    = 0
agg              = Aggregator()

batch = 500
for start in range(0, DRAW_SIMS, batch):
    end = min(start + batch, DRAW_SIMS)
    for _ in range(end - start):
        realized = realize_pots(base_pots, rng_draw)
        engine = ExactSequentialDrawEngine(realized, rng_draw, ordering=ORDERING_MODE)
        state  = engine.run()
        total_backtracks += engine.stats.get("backtracks", 0)
        total_gprunes    += engine.stats.get("global_prunes", 0)
        if state is not None and validate_draw(state):
            frozen = freeze_draw(state)
            reservoir.append(frozen)
            unique_frozen.add(frozen)
            agg.absorb_draw(frozen)
    elapsed = time.time() - t0
    rate = (start + batch) / elapsed if elapsed > 0 else 0
    print(f"  [{min(start+batch, DRAW_SIMS):>7,}/{DRAW_SIMS:,}] "
          f"valid={len(reservoir):,}  unique={len(unique_frozen):,}  "
          f"rate={rate:.0f}/s  success={len(reservoir)/max(1,min(start+batch,DRAW_SIMS)):.1%}")

t_draw = time.time() - t0
print(f"\n  Reservoir: {len(reservoir):,} valid draws in {t_draw:.1f}s "
      f"({len(reservoir)/DRAW_SIMS:.1%} success rate)")
print(f"  Unique draws: {len(unique_frozen):,}  "
      f"backtracks: {total_backtracks:,}  global_prunes: {total_gprunes:,}")

assert len(reservoir) > 0, "No valid draws! Try different seed."

# Phase 2: Tournament simulation
print(f"\nPhase 2: Simulating {TOURNAMENT_SIMS:,} tournaments...")
t1 = time.time()
py_rng = random.Random(RANDOM_SEED + 50000)

if TOURNAMENT_FROM_UNIQUE:
    draw_pool = list(unique_frozen)
else:
    draw_pool = reservoir

report_interval = max(1, TOURNAMENT_SIMS // 10)
for i in range(TOURNAMENT_SIMS):
    frozen = draw_pool[py_rng.randrange(len(draw_pool))]
    result = simulate_tournament(frozen, py_rng.randrange(1, 2**31 - 1))
    agg.absorb_tournament(result)
    if (i + 1) % report_interval == 0:
        elapsed = time.time() - t1
        rate = (i + 1) / elapsed
        print(f"  [{i+1:>8,}/{TOURNAMENT_SIMS:,}] {rate:.0f} sims/sec")

t_tourn = time.time() - t1
print(f"\n  Tournaments: {TOURNAMENT_SIMS:,} in {t_tourn:.1f}s ({TOURNAMENT_SIMS/t_tourn:.0f} sims/sec)")
print(f"\n  Total runtime: {t_draw + t_tourn:.1f}s")
print("=" * 60)

# %% [markdown]
# ## Results

# %% Outputs
print("Generating outputs...")
stats_dict = {
    "valid_draws":   len(reservoir),
    "unique_draws":  len(unique_frozen),
    "backtracks":    total_backtracks,
    "global_prunes": total_gprunes,
}
plot_draw_heatmap(agg, len(unique_frozen))
plot_host_opponents(agg)
plot_title_odds(agg, TOURNAMENT_SIMS)
plot_advancement(agg, TOURNAMENT_SIMS)
write_simulation_summary(agg, TOURNAMENT_SIMS, stats_dict)
write_draw_matrix_csv(agg)
write_draw_probabilities_long_csv(agg)
save_unique_draws_sample(unique_frozen, agg)
write_config_json(stats_dict, t_draw, t_tourn)
write_validation_report(agg, stats_dict)
run_seed_diagnostics(base_pots)
print(f"\nAll outputs saved to {RESULTS_DIR}/")

# %% [markdown]
# ## Title Odds Leaderboard

# %% Title Odds
title_rows = []
for team in sorted(ALL_TEAMS):
    if agg.champion[team] > 0:
        title_rows.append({
            "Team": team,
            "Win %": f"{100 * agg.champion[team] / TOURNAMENT_SIMS:.2f}%",
            "Final %": f"{100 * agg.finalist[team] / TOURNAMENT_SIMS:.2f}%",
            "SF %": f"{100 * agg.sf[team] / TOURNAMENT_SIMS:.2f}%",
            "QF %": f"{100 * agg.qf[team] / TOURNAMENT_SIMS:.2f}%",
        })
title_rows.sort(key=lambda x: float(x["Win %"].replace("%", "")), reverse=True)

if pd is not None:
    display(pd.DataFrame(title_rows).head(20))
else:
    for row in title_rows[:20]:
        print(f"  {row['Team']:<20} Win={row['Win %']:>7}  Final={row['Final %']:>7}  SF={row['SF %']:>7}  QF={row['QF %']:>7}")

# %% [markdown]
# ## Estimated Draw Probability Matrix

# %% Draw Matrix
if pd is not None:
    matrix_data = {}
    for team in MAJOR_TEAMS:
        probs = agg.draw_matrix[team] / max(1, agg.draw_successes)
        matrix_data[team] = {GROUPS[i]: f"{100*probs[i]:.1f}%" for i in range(len(GROUPS))}
    df = pd.DataFrame(matrix_data).T
    display(df)
else:
    print("Install pandas for formatted table")
