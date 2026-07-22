"""
utils/schedule_data.py
----------------------
Per-match schedule data for the FIFA 2026 group stage.

Each match record contains:
  md             – matchday number (1, 2, or 3)
  slot           – 0 or 1 (MD_PAIRS slot index: 0 = pairs[0], 1 = pairs[1])
  city           – city key matching GROUP_MD_STADIUMS and revenue lookup
  date           – "Jun DD" formatted date string
  time           – local kickoff time, or "" if unverified
  team_a         – home/first team (display name)
  team_b         – away/second team (display name)
  official_match – display string "Team A vs Team B"

Source: 2026_FIFA_World_Cup_Cleaned_Schedule_with_Verified_Times.txt

Slot ordering follows MD_PAIRS in official_baseline.py:
  MD1: slot 0 = teams[0] vs teams[1],  slot 1 = teams[2] vs teams[3]
  MD2: slot 0 = teams[0] vs teams[2],  slot 1 = teams[1] vs teams[3]
  MD3: slot 0 = teams[0] vs teams[3],  slot 1 = teams[1] vs teams[2]
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Full 72-match group stage schedule
# ─────────────────────────────────────────────────────────────────────────────

OFFICIAL_SCHEDULE: dict[str, list[dict]] = {

    # ── Group A: Mexico(0), South Africa(1), Korea Republic(2), Czechia(3) ──
    "A": [
        {"md": 1, "slot": 0, "city": "Mexico City",            "date": "Jun 11", "time": "1:00 PM",  "team_a": "Mexico",        "team_b": "South Africa",  "official_match": "Mexico vs South Africa"},
        {"md": 1, "slot": 1, "city": "Guadalajara",            "date": "Jun 11", "time": "8:00 PM",  "team_a": "Korea Republic", "team_b": "Czechia",       "official_match": "Korea Republic vs Czechia"},
        {"md": 2, "slot": 0, "city": "Guadalajara",            "date": "Jun 18", "time": "7:00 PM",  "team_a": "Mexico",        "team_b": "Korea Republic", "official_match": "Mexico vs Korea Republic"},
        {"md": 2, "slot": 1, "city": "Atlanta",                "date": "Jun 18", "time": "12:00 PM", "team_a": "South Africa",  "team_b": "Czechia",       "official_match": "Czechia vs South Africa"},
        {"md": 3, "slot": 0, "city": "Mexico City",            "date": "Jun 24", "time": "7:00 PM",  "team_a": "Mexico",        "team_b": "Czechia",       "official_match": "Czechia vs Mexico"},
        {"md": 3, "slot": 1, "city": "Monterrey",              "date": "Jun 24", "time": "7:00 PM",  "team_a": "South Africa",  "team_b": "Korea Republic","official_match": "South Africa vs Korea Republic"},
    ],

    # ── Group B: Canada(0), Bosnia and Herzegovina(1), Qatar(2), Switzerland(3) ──
    "B": [
        {"md": 1, "slot": 0, "city": "Toronto",                "date": "Jun 12", "time": "3:00 PM",  "team_a": "Canada",        "team_b": "Bosnia and Herzegovina", "official_match": "Canada vs Bosnia and Herzegovina"},
        {"md": 1, "slot": 1, "city": "San Francisco Bay Area", "date": "Jun 13", "time": "12:00 PM", "team_a": "Qatar",         "team_b": "Switzerland",   "official_match": "Qatar vs Switzerland"},
        {"md": 2, "slot": 0, "city": "Vancouver",              "date": "Jun 18", "time": "3:00 PM",  "team_a": "Canada",        "team_b": "Qatar",         "official_match": "Canada vs Qatar"},
        {"md": 2, "slot": 1, "city": "Los Angeles",            "date": "Jun 18", "time": "",         "team_a": "Bosnia and Herzegovina", "team_b": "Switzerland", "official_match": "Switzerland vs Bosnia and Herzegovina"},
        {"md": 3, "slot": 0, "city": "Vancouver",              "date": "Jun 24", "time": "",         "team_a": "Canada",        "team_b": "Switzerland",   "official_match": "Switzerland vs Canada"},
        {"md": 3, "slot": 1, "city": "Seattle",                "date": "Jun 24", "time": "12:00 PM", "team_a": "Bosnia and Herzegovina", "team_b": "Qatar", "official_match": "Bosnia and Herzegovina vs Qatar"},
    ],

    # ── Group C: Brazil(0), Morocco(1), Haiti(2), Scotland(3) ──
    "C": [
        {"md": 1, "slot": 0, "city": "New York/NJ",            "date": "Jun 13", "time": "6:00 PM",  "team_a": "Brazil",        "team_b": "Morocco",       "official_match": "Brazil vs Morocco"},
        {"md": 1, "slot": 1, "city": "Boston",                 "date": "Jun 13", "time": "9:00 PM",  "team_a": "Haiti",         "team_b": "Scotland",      "official_match": "Haiti vs Scotland"},
        {"md": 2, "slot": 0, "city": "Philadelphia",           "date": "Jun 19", "time": "8:30 PM",  "team_a": "Brazil",        "team_b": "Haiti",         "official_match": "Brazil vs Haiti"},
        {"md": 2, "slot": 1, "city": "Boston",                 "date": "Jun 19", "time": "6:00 PM",  "team_a": "Morocco",       "team_b": "Scotland",      "official_match": "Scotland vs Morocco"},
        {"md": 3, "slot": 0, "city": "Miami",                  "date": "Jun 24", "time": "",         "team_a": "Brazil",        "team_b": "Scotland",      "official_match": "Scotland vs Brazil"},
        {"md": 3, "slot": 1, "city": "Atlanta",                "date": "Jun 24", "time": "6:00 PM",  "team_a": "Morocco",       "team_b": "Haiti",         "official_match": "Morocco vs Haiti"},
    ],

    # ── Group D: USA(0), Paraguay(1), Australia(2), Türkiye(3) ──
    "D": [
        {"md": 1, "slot": 0, "city": "Los Angeles",            "date": "Jun 12", "time": "6:00 PM",  "team_a": "USA",           "team_b": "Paraguay",      "official_match": "USA vs Paraguay"},
        {"md": 1, "slot": 1, "city": "Vancouver",              "date": "Jun 13", "time": "",         "team_a": "Australia",     "team_b": "Türkiye",       "official_match": "Australia vs Türkiye"},
        {"md": 2, "slot": 0, "city": "Seattle",                "date": "Jun 19", "time": "12:00 PM", "team_a": "USA",           "team_b": "Australia",     "official_match": "USA vs Australia"},
        {"md": 2, "slot": 1, "city": "San Francisco Bay Area", "date": "Jun 19", "time": "8:00 PM",  "team_a": "Paraguay",      "team_b": "Türkiye",       "official_match": "Türkiye vs Paraguay"},
        {"md": 3, "slot": 0, "city": "Los Angeles",            "date": "Jun 25", "time": "",         "team_a": "USA",           "team_b": "Türkiye",       "official_match": "Türkiye vs USA"},
        {"md": 3, "slot": 1, "city": "San Francisco Bay Area", "date": "Jun 25", "time": "7:00 PM",  "team_a": "Paraguay",      "team_b": "Australia",     "official_match": "Paraguay vs Australia"},
    ],

    # ── Group E: Germany(0), Curaçao(1), Côte d'Ivoire(2), Ecuador(3) ──
    "E": [
        {"md": 1, "slot": 0, "city": "Houston",                "date": "Jun 14", "time": "12:00 PM", "team_a": "Germany",       "team_b": "Curaçao",       "official_match": "Germany vs Curaçao"},
        {"md": 1, "slot": 1, "city": "Philadelphia",           "date": "Jun 14", "time": "7:00 PM",  "team_a": "Côte d'Ivoire", "team_b": "Ecuador",       "official_match": "Côte d'Ivoire vs Ecuador"},
        {"md": 2, "slot": 0, "city": "Toronto",                "date": "Jun 20", "time": "4:00 PM",  "team_a": "Germany",       "team_b": "Côte d'Ivoire", "official_match": "Germany vs Côte d'Ivoire"},
        {"md": 2, "slot": 1, "city": "Kansas City",            "date": "Jun 20", "time": "",         "team_a": "Curaçao",       "team_b": "Ecuador",       "official_match": "Ecuador vs Curaçao"},
        {"md": 3, "slot": 0, "city": "New York/NJ",            "date": "Jun 25", "time": "4:00 PM",  "team_a": "Germany",       "team_b": "Ecuador",       "official_match": "Ecuador vs Germany"},
        {"md": 3, "slot": 1, "city": "Philadelphia",           "date": "Jun 25", "time": "4:00 PM",  "team_a": "Curaçao",       "team_b": "Côte d'Ivoire", "official_match": "Curaçao vs Côte d'Ivoire"},
    ],

    # ── Group F: Netherlands(0), Japan(1), Sweden(2), Tunisia(3) ──
    "F": [
        {"md": 1, "slot": 0, "city": "Dallas",                 "date": "Jun 14", "time": "3:00 PM",  "team_a": "Netherlands",   "team_b": "Japan",         "official_match": "Netherlands vs Japan"},
        {"md": 1, "slot": 1, "city": "Monterrey",              "date": "Jun 14", "time": "8:00 PM",  "team_a": "Sweden",        "team_b": "Tunisia",       "official_match": "Sweden vs Tunisia"},
        {"md": 2, "slot": 0, "city": "Houston",                "date": "Jun 20", "time": "",         "team_a": "Netherlands",   "team_b": "Sweden",        "official_match": "Netherlands vs Sweden"},
        {"md": 2, "slot": 1, "city": "Monterrey",              "date": "Jun 20", "time": "",         "team_a": "Japan",         "team_b": "Tunisia",       "official_match": "Tunisia vs Japan"},
        {"md": 3, "slot": 0, "city": "Kansas City",            "date": "Jun 25", "time": "",         "team_a": "Netherlands",   "team_b": "Tunisia",       "official_match": "Tunisia vs Netherlands"},
        {"md": 3, "slot": 1, "city": "Dallas",                 "date": "Jun 25", "time": "",         "team_a": "Japan",         "team_b": "Sweden",        "official_match": "Japan vs Sweden"},
    ],

    # ── Group G: Belgium(0), Egypt(1), IR Iran(2), New Zealand(3) ──
    "G": [
        {"md": 1, "slot": 0, "city": "Seattle",                "date": "Jun 15", "time": "12:00 PM", "team_a": "Belgium",       "team_b": "Egypt",         "official_match": "Belgium vs Egypt"},
        {"md": 1, "slot": 1, "city": "Los Angeles",            "date": "Jun 15", "time": "6:00 PM",  "team_a": "IR Iran",       "team_b": "New Zealand",   "official_match": "IR Iran vs New Zealand"},
        {"md": 2, "slot": 0, "city": "Los Angeles",            "date": "Jun 21", "time": "",         "team_a": "Belgium",       "team_b": "IR Iran",       "official_match": "Belgium vs IR Iran"},
        {"md": 2, "slot": 1, "city": "Vancouver",              "date": "Jun 21", "time": "",         "team_a": "Egypt",         "team_b": "New Zealand",   "official_match": "New Zealand vs Egypt"},
        {"md": 3, "slot": 0, "city": "Kansas City",            "date": "Jun 26", "time": "",         "team_a": "Belgium",       "team_b": "New Zealand",   "official_match": "New Zealand vs Belgium"},
        {"md": 3, "slot": 1, "city": "New York/NJ",            "date": "Jun 26", "time": "",         "team_a": "Egypt",         "team_b": "IR Iran",       "official_match": "Egypt vs IR Iran"},
    ],

    # ── Group H: Spain(0), Cabo Verde(1), Saudi Arabia(2), Uruguay(3) ──
    "H": [
        {"md": 1, "slot": 0, "city": "Atlanta",                "date": "Jun 15", "time": "12:00 PM", "team_a": "Spain",         "team_b": "Cabo Verde",    "official_match": "Spain vs Cabo Verde"},
        {"md": 1, "slot": 1, "city": "Miami",                  "date": "Jun 15", "time": "6:00 PM",  "team_a": "Saudi Arabia",  "team_b": "Uruguay",       "official_match": "Saudi Arabia vs Uruguay"},
        {"md": 2, "slot": 0, "city": "Atlanta",                "date": "Jun 21", "time": "",         "team_a": "Spain",         "team_b": "Saudi Arabia",  "official_match": "Spain vs Saudi Arabia"},
        {"md": 2, "slot": 1, "city": "Miami",                  "date": "Jun 21", "time": "",         "team_a": "Cabo Verde",    "team_b": "Uruguay",       "official_match": "Uruguay vs Cabo Verde"},
        {"md": 3, "slot": 0, "city": "Houston",                "date": "Jun 26", "time": "",         "team_a": "Spain",         "team_b": "Uruguay",       "official_match": "Uruguay vs Spain"},
        {"md": 3, "slot": 1, "city": "Atlanta",                "date": "Jun 26", "time": "7:00 PM",  "team_a": "Cabo Verde",    "team_b": "Saudi Arabia",  "official_match": "Cabo Verde vs Saudi Arabia"},
    ],

    # ── Group I: France(0), Senegal(1), Iraq(2), Norway(3) ──
    "I": [
        {"md": 1, "slot": 0, "city": "New York/NJ",            "date": "Jun 16", "time": "3:00 PM",  "team_a": "France",        "team_b": "Senegal",       "official_match": "France vs Senegal"},
        {"md": 1, "slot": 1, "city": "Boston",                 "date": "Jun 16", "time": "6:00 PM",  "team_a": "Iraq",          "team_b": "Norway",        "official_match": "Iraq vs Norway"},
        {"md": 2, "slot": 0, "city": "Philadelphia",           "date": "Jun 22", "time": "5:00 PM",  "team_a": "France",        "team_b": "Iraq",          "official_match": "France vs Iraq"},
        {"md": 2, "slot": 1, "city": "New York/NJ",            "date": "Jun 22", "time": "8:00 PM",  "team_a": "Senegal",       "team_b": "Norway",        "official_match": "Norway vs Senegal"},
        {"md": 3, "slot": 0, "city": "Dallas",                 "date": "Jun 27", "time": "",         "team_a": "France",        "team_b": "Norway",        "official_match": "Norway vs France"},
        {"md": 3, "slot": 1, "city": "Houston",                "date": "Jun 27", "time": "",         "team_a": "Senegal",       "team_b": "Iraq",          "official_match": "Senegal vs Iraq"},
    ],

    # ── Group J: Argentina(0), Algeria(1), Austria(2), Jordan(3) ──
    "J": [
        {"md": 1, "slot": 0, "city": "Kansas City",            "date": "Jun 16", "time": "8:00 PM",  "team_a": "Argentina",     "team_b": "Algeria",       "official_match": "Argentina vs Algeria"},
        {"md": 1, "slot": 1, "city": "San Francisco Bay Area", "date": "Jun 16", "time": "9:00 PM",  "team_a": "Austria",       "team_b": "Jordan",        "official_match": "Austria vs Jordan"},
        {"md": 2, "slot": 0, "city": "Dallas",                 "date": "Jun 22", "time": "12:00 PM", "team_a": "Argentina",     "team_b": "Austria",       "official_match": "Argentina vs Austria"},
        {"md": 2, "slot": 1, "city": "San Francisco Bay Area", "date": "Jun 22", "time": "8:00 PM",  "team_a": "Algeria",       "team_b": "Jordan",        "official_match": "Jordan vs Algeria"},
        {"md": 3, "slot": 0, "city": "Guadalajara",            "date": "Jun 27", "time": "",         "team_a": "Argentina",     "team_b": "Jordan",        "official_match": "Jordan vs Argentina"},
        {"md": 3, "slot": 1, "city": "Monterrey",              "date": "Jun 27", "time": "9:00 PM",  "team_a": "Algeria",       "team_b": "Austria",       "official_match": "Algeria vs Austria"},
    ],

    # ── Group K: Portugal(0), DR Congo(1), Uzbekistan(2), Colombia(3) ──
    "K": [
        {"md": 1, "slot": 0, "city": "Houston",                "date": "Jun 17", "time": "",         "team_a": "Portugal",      "team_b": "DR Congo",      "official_match": "Portugal vs DR Congo"},
        {"md": 1, "slot": 1, "city": "Mexico City",            "date": "Jun 17", "time": "8:00 PM",  "team_a": "Uzbekistan",    "team_b": "Colombia",      "official_match": "Uzbekistan vs Colombia"},
        {"md": 2, "slot": 0, "city": "Houston",                "date": "Jun 23", "time": "",         "team_a": "Portugal",      "team_b": "Uzbekistan",    "official_match": "Portugal vs Uzbekistan"},
        {"md": 2, "slot": 1, "city": "Guadalajara",            "date": "Jun 23", "time": "",         "team_a": "DR Congo",      "team_b": "Colombia",      "official_match": "Colombia vs DR Congo"},
        {"md": 3, "slot": 0, "city": "Mexico City",            "date": "Jun 27", "time": "",         "team_a": "Portugal",      "team_b": "Colombia",      "official_match": "Colombia vs Portugal"},
        {"md": 3, "slot": 1, "city": "Atlanta",                "date": "Jun 27", "time": "",         "team_a": "DR Congo",      "team_b": "Uzbekistan",    "official_match": "DR Congo vs Uzbekistan"},
    ],

    # ── Group L: England(0), Croatia(1), Ghana(2), Panama(3) ──
    "L": [
        {"md": 1, "slot": 0, "city": "Dallas",                 "date": "Jun 17", "time": "",         "team_a": "England",       "team_b": "Croatia",       "official_match": "England vs Croatia"},
        {"md": 1, "slot": 1, "city": "Toronto",                "date": "Jun 17", "time": "",         "team_a": "Ghana",         "team_b": "Panama",        "official_match": "Ghana vs Panama"},
        {"md": 2, "slot": 0, "city": "Boston",                 "date": "Jun 23", "time": "",         "team_a": "England",       "team_b": "Ghana",         "official_match": "England vs Ghana"},
        {"md": 2, "slot": 1, "city": "Toronto",                "date": "Jun 23", "time": "",         "team_a": "Croatia",       "team_b": "Panama",        "official_match": "Panama vs Croatia"},
        {"md": 3, "slot": 0, "city": "Seattle",                "date": "Jun 27", "time": "5:00 PM",  "team_a": "England",       "team_b": "Panama",        "official_match": "Panama vs England"},
        {"md": 3, "slot": 1, "city": "Vancouver",              "date": "Jun 27", "time": "",         "team_a": "Croatia",       "team_b": "Ghana",         "official_match": "Croatia vs Ghana"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Lookup helper
# ─────────────────────────────────────────────────────────────────────────────

def get_match_info(group: str, md: int, slot: int) -> dict | None:
    """
    Return the schedule record for a specific group / matchday / slot.
    Returns None if not found.
    """
    for rec in OFFICIAL_SCHEDULE.get(group, []):
        if rec["md"] == md and rec["slot"] == slot:
            return rec
    return None


def get_group_schedule(group: str) -> list[dict]:
    """Return all 6 match records for a group, sorted by matchday then slot."""
    return sorted(
        OFFICIAL_SCHEDULE.get(group, []),
        key=lambda r: (r["md"], r["slot"]),
    )


def format_kickoff(time_str: str) -> str:
    """Return a display string for kickoff time, or 'TBC' if unverified."""
    return time_str if time_str else "TBC"
