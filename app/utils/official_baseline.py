"""
utils/official_baseline.py
--------------------------
Static reference data for the FIFA 2026 scenario engine:

  • OFFICIAL_DRAW        – official 48-team group draw per World_Cup_2026_Official_Bracket.txt
  • GROUP_MD_STADIUMS    – per-group, per-matchday stadium-city pairs (from published schedule)
  • CITY_TO_VENUE        – city names → venue display names
  • VENUE_TO_CITY        – inverse mapping
  • HOST_LOCKS           – team → group (deterministic, per FIFA host assignments)
  • MD_PAIRS             – which slot indices play each matchday
  • GROUPS / POTS        – ordered lists for iteration

Source of truth for OFFICIAL_DRAW:
  World_Cup_2026_Official_Bracket.txt
  Tournament Dates: June 11 – July 19, 2026
  Hosts: Canada, Mexico, United States

Pot structure (12 teams per pot, one per group):
  Pot 1  – hosts + top-ranked non-hosts
  Pot 2  – second-tier teams
  Pot 3  – third-tier teams
  Pot 4  – lower-ranked / qualifying-route teams

Confederation caps verified per group:
  • max 2 UEFA per group
  • max 1 of any other confederation per group
  • min 1 UEFA per group
  • host locks: Mexico→A, Canada→B, USA→D
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Groups and matchday structure
# ─────────────────────────────────────────────────────────────────────────────

GROUPS = list("ABCDEFGHIJKL")

# For each matchday, which slot-index pairs play simultaneously.
# Slots are 0-indexed (group positions 0–3).
# MD1: [0v1, 2v3]  MD2: [0v2, 1v3]  MD3: [0v3, 1v2]
MD_PAIRS: dict[int, list[list[int]]] = {
    1: [[0, 1], [2, 3]],
    2: [[0, 2], [1, 3]],
    3: [[0, 3], [1, 2]],
}

# ─────────────────────────────────────────────────────────────────────────────
# Host locks  (team name must match app_teams.csv exactly)
# ─────────────────────────────────────────────────────────────────────────────

HOST_LOCKS: dict[str, str] = {
    "Mexico": "A",
    "Canada": "B",
    "USA":    "D",
}

# ─────────────────────────────────────────────────────────────────────────────
# Official FIFA 2026 group-stage draw
# Source: World_Cup_2026_Official_Bracket.txt
# Each group: [Pot1_team, Pot2_team, Pot3_team, Pot4_team]
# ─────────────────────────────────────────────────────────────────────────────

OFFICIAL_DRAW: dict[str, list[str]] = {
    "A": ["Mexico",      "South Africa",          "Korea Republic",  "Czechia"],
    "B": ["Canada",      "Bosnia and Herzegovina", "Qatar",           "Switzerland"],
    "C": ["Brazil",      "Morocco",               "Haiti",           "Scotland"],
    "D": ["USA",         "Paraguay",              "Australia",       "Türkiye"],
    "E": ["Germany",     "Curaçao",               "Côte d'Ivoire",   "Ecuador"],
    "F": ["Netherlands", "Japan",                 "Sweden",          "Tunisia"],
    "G": ["Belgium",     "Egypt",                 "IR Iran",         "New Zealand"],
    "H": ["Spain",       "Cabo Verde",            "Saudi Arabia",    "Uruguay"],
    "I": ["France",      "Senegal",               "Iraq",            "Norway"],
    "J": ["Argentina",   "Algeria",               "Austria",         "Jordan"],
    "K": ["Portugal",    "DR Congo",              "Uzbekistan",      "Colombia"],
    "L": ["England",     "Croatia",               "Ghana",           "Panama"],
}

# ─────────────────────────────────────────────────────────────────────────────
# Stadium city pairs per group per matchday
# Source: FIFA 2026 published schedule / HTML reference app
# City names match REVENUE_TABLE keys in app_revenue_lookup.csv
# ─────────────────────────────────────────────────────────────────────────────

GROUP_MD_STADIUMS: dict[str, dict[int, dict[str, str]]] = {
    # s1 = city for MD_PAIRS[md][0] (pairs[0]),  s2 = city for MD_PAIRS[md][1] (pairs[1])
    # d1/d2 = local date for each match
    # Source: 2026_FIFA_World_Cup_Cleaned_Schedule_with_Verified_Times.txt
    "A": {
        # MD1: Mexico(0)vsSouthAfrica(1)@MexicoCity | KoreaRepublic(2)vsCzechia(3)@Guadalajara
        1: {"s1": "Mexico City",            "s2": "Guadalajara",            "d1": "Jun 11", "d2": "Jun 11"},
        # MD2: Mexico(0)vsKoreaRepublic(2)@Guadalajara | SouthAfrica(1)vsCzechia(3)@Atlanta
        2: {"s1": "Guadalajara",            "s2": "Atlanta",                "d1": "Jun 18", "d2": "Jun 18"},
        # MD3: Mexico(0)vsCzechia(3)@MexicoCity | SouthAfrica(1)vsKoreaRepublic(2)@Monterrey
        3: {"s1": "Mexico City",            "s2": "Monterrey",              "d1": "Jun 24", "d2": "Jun 24"},
    },
    "B": {
        # MD1: Canada(0)vsBosnia(1)@Toronto | Qatar(2)vsSwitzerland(3)@SFBayArea
        1: {"s1": "Toronto",                "s2": "San Francisco Bay Area", "d1": "Jun 12", "d2": "Jun 13"},
        # MD2: Canada(0)vsQatar(2)@Vancouver | Bosnia(1)vsSwitzerland(3)@LosAngeles
        2: {"s1": "Vancouver",              "s2": "Los Angeles",            "d1": "Jun 18", "d2": "Jun 18"},
        # MD3: Canada(0)vsSwitzerland(3)@Vancouver | Bosnia(1)vsQatar(2)@Seattle
        3: {"s1": "Vancouver",              "s2": "Seattle",                "d1": "Jun 24", "d2": "Jun 24"},
    },
    "C": {
        # MD1: Brazil(0)vsMorocco(1)@NewYork | Haiti(2)vsScotland(3)@Boston
        1: {"s1": "New York/NJ",            "s2": "Boston",                 "d1": "Jun 13", "d2": "Jun 13"},
        # MD2: Brazil(0)vsHaiti(2)@Philadelphia | Morocco(1)vsScotland(3)@Boston
        2: {"s1": "Philadelphia",           "s2": "Boston",                 "d1": "Jun 19", "d2": "Jun 19"},
        # MD3: Brazil(0)vsScotland(3)@Miami | Morocco(1)vsHaiti(2)@Atlanta
        3: {"s1": "Miami",                  "s2": "Atlanta",                "d1": "Jun 24", "d2": "Jun 24"},
    },
    "D": {
        # MD1: USA(0)vsParaguay(1)@LosAngeles | Australia(2)vsTürkiye(3)@Vancouver
        1: {"s1": "Los Angeles",            "s2": "Vancouver",              "d1": "Jun 12", "d2": "Jun 13"},
        # MD2: USA(0)vsAustralia(2)@Seattle | Paraguay(1)vsTürkiye(3)@SFBayArea
        2: {"s1": "Seattle",                "s2": "San Francisco Bay Area", "d1": "Jun 19", "d2": "Jun 19"},
        # MD3: USA(0)vsTürkiye(3)@LosAngeles | Paraguay(1)vsAustralia(2)@SFBayArea
        3: {"s1": "Los Angeles",            "s2": "San Francisco Bay Area", "d1": "Jun 25", "d2": "Jun 25"},
    },
    "E": {
        # MD1: Germany(0)vsCuraçao(1)@Houston | CôtedIvoire(2)vsEcuador(3)@Philadelphia
        1: {"s1": "Houston",                "s2": "Philadelphia",           "d1": "Jun 14", "d2": "Jun 14"},
        # MD2: Germany(0)vsCôtedIvoire(2)@Toronto | Curaçao(1)vsEcuador(3)@KansasCity
        2: {"s1": "Toronto",                "s2": "Kansas City",            "d1": "Jun 20", "d2": "Jun 20"},
        # MD3: Germany(0)vsEcuador(3)@NewYork | Curaçao(1)vsCôtedIvoire(2)@Philadelphia
        3: {"s1": "New York/NJ",            "s2": "Philadelphia",           "d1": "Jun 25", "d2": "Jun 25"},
    },
    "F": {
        # MD1: Netherlands(0)vsJapan(1)@Dallas | Sweden(2)vsTunisia(3)@Monterrey
        1: {"s1": "Dallas",                 "s2": "Monterrey",              "d1": "Jun 14", "d2": "Jun 14"},
        # MD2: Netherlands(0)vsSweden(2)@Houston | Japan(1)vsTunisia(3)@Monterrey
        2: {"s1": "Houston",                "s2": "Monterrey",              "d1": "Jun 20", "d2": "Jun 20"},
        # MD3: Netherlands(0)vsTunisia(3)@KansasCity | Japan(1)vsSweden(2)@Dallas
        3: {"s1": "Kansas City",            "s2": "Dallas",                 "d1": "Jun 25", "d2": "Jun 25"},
    },
    "G": {
        # MD1: Belgium(0)vsEgypt(1)@Seattle | IRIran(2)vsNewZealand(3)@LosAngeles
        1: {"s1": "Seattle",                "s2": "Los Angeles",            "d1": "Jun 15", "d2": "Jun 15"},
        # MD2: Belgium(0)vsIRIran(2)@LosAngeles | Egypt(1)vsNewZealand(3)@Vancouver
        2: {"s1": "Los Angeles",            "s2": "Vancouver",              "d1": "Jun 21", "d2": "Jun 21"},
        # MD3: Belgium(0)vsNewZealand(3)@KansasCity | Egypt(1)vsIRIran(2)@NewYork
        3: {"s1": "Kansas City",            "s2": "New York/NJ",            "d1": "Jun 26", "d2": "Jun 26"},
    },
    "H": {
        # MD1: Spain(0)vsCaboVerde(1)@Atlanta | SaudiArabia(2)vsUruguay(3)@Miami
        1: {"s1": "Atlanta",                "s2": "Miami",                  "d1": "Jun 15", "d2": "Jun 15"},
        # MD2: Spain(0)vsSaudiArabia(2)@Atlanta | CaboVerde(1)vsUruguay(3)@Miami
        2: {"s1": "Atlanta",                "s2": "Miami",                  "d1": "Jun 21", "d2": "Jun 21"},
        # MD3: Spain(0)vsUruguay(3)@Houston | CaboVerde(1)vsSaudiArabia(2)@Atlanta
        3: {"s1": "Houston",                "s2": "Atlanta",                "d1": "Jun 26", "d2": "Jun 26"},
    },
    "I": {
        # MD1: France(0)vsSenegal(1)@NewYork | Iraq(2)vsNorway(3)@Boston
        1: {"s1": "New York/NJ",            "s2": "Boston",                 "d1": "Jun 16", "d2": "Jun 16"},
        # MD2: France(0)vsIraq(2)@Philadelphia | Senegal(1)vsNorway(3)@NewYork
        2: {"s1": "Philadelphia",           "s2": "New York/NJ",            "d1": "Jun 22", "d2": "Jun 22"},
        # MD3: France(0)vsNorway(3)@Dallas | Senegal(1)vsIraq(2)@Houston
        3: {"s1": "Dallas",                 "s2": "Houston",                "d1": "Jun 27", "d2": "Jun 27"},
    },
    "J": {
        # MD1: Argentina(0)vsAlgeria(1)@KansasCity | Austria(2)vsJordan(3)@SFBayArea
        1: {"s1": "Kansas City",            "s2": "San Francisco Bay Area", "d1": "Jun 16", "d2": "Jun 16"},
        # MD2: Argentina(0)vsAustria(2)@Dallas | Algeria(1)vsJordan(3)@SFBayArea
        2: {"s1": "Dallas",                 "s2": "San Francisco Bay Area", "d1": "Jun 22", "d2": "Jun 22"},
        # MD3: Argentina(0)vsJordan(3)@Guadalajara | Algeria(1)vsAustria(2)@Monterrey
        3: {"s1": "Guadalajara",            "s2": "Monterrey",              "d1": "Jun 27", "d2": "Jun 27"},
    },
    "K": {
        # MD1: Portugal(0)vsDRCongo(1)@Houston | Uzbekistan(2)vsColombia(3)@MexicoCity
        1: {"s1": "Houston",                "s2": "Mexico City",            "d1": "Jun 17", "d2": "Jun 17"},
        # MD2: Portugal(0)vsUzbekistan(2)@Houston | DRCongo(1)vsColombia(3)@Guadalajara
        2: {"s1": "Houston",                "s2": "Guadalajara",            "d1": "Jun 23", "d2": "Jun 23"},
        # MD3: Portugal(0)vsColombia(3)@MexicoCity | DRCongo(1)vsUzbekistan(2)@Atlanta
        3: {"s1": "Mexico City",            "s2": "Atlanta",                "d1": "Jun 27", "d2": "Jun 27"},
    },
    "L": {
        # MD1: England(0)vsCroatia(1)@Dallas | Ghana(2)vsPanama(3)@Toronto
        1: {"s1": "Dallas",                 "s2": "Toronto",                "d1": "Jun 17", "d2": "Jun 17"},
        # MD2: England(0)vsGhana(2)@Boston | Croatia(1)vsPanama(3)@Toronto
        2: {"s1": "Boston",                 "s2": "Toronto",                "d1": "Jun 23", "d2": "Jun 23"},
        # MD3: England(0)vsPanama(3)@Seattle | Croatia(1)vsGhana(2)@Vancouver
        3: {"s1": "Seattle",                "s2": "Vancouver",              "d1": "Jun 27", "d2": "Jun 27"},
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# City / venue name mappings
# Revenue lookup uses city names; venue_summary display uses venue names
# ─────────────────────────────────────────────────────────────────────────────

CITY_TO_VENUE: dict[str, str] = {
    "Mexico City":           "Estadio Azteca",
    "Guadalajara":           "Estadio Akron",
    "Atlanta":               "Mercedes-Benz Stadium",
    "Toronto":               "BMO Field",
    "San Francisco Bay Area":"Levi's Stadium",
    "Los Angeles":           "SoFi Stadium",
    "Vancouver":             "BC Place",
    "Seattle":               "Lumen Field",
    "New York/NJ":           "MetLife Stadium",
    "Boston":                "Gillette Stadium",
    "Philadelphia":          "Lincoln Financial Field",
    "Miami":                 "Hard Rock Stadium",
    "Houston":               "NRG Stadium",
    "Dallas":                "AT&T Stadium",
    "Kansas City":           "Arrowhead Stadium",
    "Monterrey":             "Estadio BBVA",
}

VENUE_TO_CITY: dict[str, str] = {v: k for k, v in CITY_TO_VENUE.items()}

# ─────────────────────────────────────────────────────────────────────────────
# Knockout bracket structure (informational — for context panel display only)
# Source: World_Cup_2026_Official_Bracket.txt
# ─────────────────────────────────────────────────────────────────────────────

ROUND_OF_32: list[dict] = [
    {"match": 73,  "desc": "Runner-up A vs Runner-up B",       "date": "Jun 28", "city": "Los Angeles"},
    {"match": 74,  "desc": "Winner E vs 3rd A/B/C/D/F",        "date": "Jun 29", "city": "Boston"},
    {"match": 75,  "desc": "Winner F vs Runner-up C",          "date": "Jun 29", "city": "Monterrey"},
    {"match": 76,  "desc": "Winner C vs Runner-up F",          "date": "Jun 29", "city": "Houston"},
    {"match": 77,  "desc": "Winner I vs 3rd C/D/F/G/H",        "date": "Jun 30", "city": "New York/NJ"},
    {"match": 78,  "desc": "Runner-up E vs Runner-up I",       "date": "Jun 30", "city": "Dallas"},
    {"match": 79,  "desc": "Winner A vs 3rd C/E/F/H/I",        "date": "Jun 30", "city": "Mexico City"},
    {"match": 80,  "desc": "Winner L vs 3rd E/H/I/J/K",        "date": "Jul 1",  "city": "Atlanta"},
    {"match": 81,  "desc": "Winner D vs 3rd B/E/F/I/J",        "date": "Jul 1",  "city": "San Francisco Bay Area"},
    {"match": 82,  "desc": "Winner G vs 3rd A/E/H/I/J",        "date": "Jul 1",  "city": "Seattle"},
    {"match": 83,  "desc": "Runner-up K vs Runner-up L",       "date": "Jul 2",  "city": "Toronto"},
    {"match": 84,  "desc": "Winner H vs Runner-up J",          "date": "Jul 2",  "city": "Los Angeles"},
    {"match": 85,  "desc": "Winner B vs 3rd E/F/G/I/J",        "date": "Jul 2",  "city": "Vancouver"},
    {"match": 86,  "desc": "Winner J vs Runner-up H",          "date": "Jul 3",  "city": "Miami"},
    {"match": 87,  "desc": "Winner K vs 3rd D/E/I/J/L",        "date": "Jul 3",  "city": "Kansas City"},
    {"match": 88,  "desc": "Runner-up D vs Runner-up G",       "date": "Jul 3",  "city": "Dallas"},
]

FINAL_VENUE = "MetLife Stadium"   # New York/NJ — July 19
