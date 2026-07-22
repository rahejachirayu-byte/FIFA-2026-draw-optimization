# FIFA 2026 Tournament Planning — Demo App

A polished Streamlit decision-support application for a FIFA 2026 capstone
demo. Combines three analytical layers into one workbench:

1. **Draw simulation** — Monte Carlo over FIFA's pot / confederation / host-slot
   constraints.
2. **Revenue projection** — venue-by-venue and country-by-country proxy
   revenue under Base / Low / High scenarios.
3. **Policy tradeoffs** — five pre-built scenarios (Baseline, Revenue-First,
   Fairness-Constrained, Low-Travel, Balanced) plus a custom weighted scoring
   panel.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Rebuild the app-ready datasets from the raw project files
python build_app_data.py

# 3. Launch the app
streamlit run app.py
```

The app opens at `http://localhost:8501`. Use the sidebar to navigate
between the five pages.

---

## Folder structure

```
fifa_demo_app/
├── app.py                          # Landing page
├── build_app_data.py               # One-shot data-prep script
├── requirements.txt
├── README.md
│
├── pages/                          # Streamlit auto-discovers these
│   ├── 1_Executive_Overview.py
│   ├── 2_Draw_Simulation_Explorer.py
│   ├── 3_Revenue_Impact_Explorer.py
│   ├── 4_Policy_Tradeoff_Lab.py
│   └── 5_Methodology.py
│
├── data/
│   ├── raw/                        # Source CSVs from the 4_17 project
│   ├── app_ready/                  # Derived tables the app consumes
│   └── simulation/                 # Draw-simulation outputs
│
├── utils/
│   ├── __init__.py
│   ├── load_data.py                # Cached loaders for every CSV
│   ├── formatters.py               # Currency / percent / delta formatting
│   ├── helpers.py                  # Page config, CSS, KPI cards, plotly theme
│   └── policy_logic.py             # Scenario metadata + composite scoring
│
└── assets/branding/                # Reserved for logo/typography assets
```

---

## Page-by-page logic

### 1. Executive Overview

Purpose: answer "what does the model say overall?" in 30 seconds.

- Four KPI cards: total projected revenue, top venue, top country share,
  valid simulated draws.
- Sidebar toggle for Low / Base / High scenarios.
- Top-5 feature drivers from the **main model**
  (`revenue_proxy_no_stage_feature`).
- Donut of revenue by host country.
- Recommendation callout + limitation callout.
- Top-5 venue table as reference.

### 2. Draw Simulation Explorer

Purpose: answer "what draw outcomes are most likely?"

- Filters: pot, confederation, spotlight team.
- Group-assignment probability heatmap (team × group).
- Spotlight-team view with most-frequent opponents.
- Top-15 matchup frequency bar chart.
- Rare/impossible pairings table (surfaces host-slot prefill effects).

### 3. Revenue Impact Explorer

Purpose: answer "which venues and countries project strongest and which
features drive that?"

- Filters: country, stage, scenario, feature-importance model view.
- Venue ranking (horizontal bar, colored by country).
- Revenue by country and revenue by stage side-by-side.
- Model scorecard (revenue-proxy + attendance RMSE panels).
- Feature importance chart with three selectable views:
  - Main: `revenue_proxy_no_stage_feature`
  - Benchmark: `revenue_proxy_full` (shows why stage_detail must be removed)
  - Sensitivity: `attendance_signal_model`
- Stage-pricing assumptions and narrative guardrails.

### 4. Policy Tradeoff Lab

Purpose: answer "what happens when we optimize for different priorities?"

- Sidebar sliders for five goals (0–10): maximize revenue, improve
  fairness, increase utilization, reduce travel, protect small markets.
- Four preset buttons (Revenue-first, Fairness, Low-travel, Balanced).
- Recommendation strip with composite score and deltas vs baseline.
- Scenario comparison table (all five scenarios, all metrics).
- Revenue vs equity tradeoff scatter with recommended scenario circled.
- Scenario detail drill-down: description, country revenue bar, winners /
  losers tables vs baseline.
- Final synthesized recommendation callout.

### 5. Methodology & Limitations

Purpose: answer "how should I interpret these numbers?"

- Revenue-target construction formula with stage benchmarks.
- Primary model choice rationale (why `revenue_proxy_no_stage_feature`).
- Monte Carlo draw simulation mechanics.
- Policy tradeoff metric definitions.
- "What this app claims" vs "what it does not claim" split.
- Full assumption registry.
- Ranked next-step upgrades.

---

## Key data-engineering decisions

**Revenue formula.** Per-match revenue is computed as
`stage_median_revenue × clip(capacity / 70000, 0.45, 1.35)`. The linear
capacity factor is what makes scenarios diverge — large-venue matches
earn proportionally more, small-venue matches less. A 70k-seat venue hits
the stage median exactly.

**Main model feature importance.** The executed project file does not
expose a standalone `revenue_proxy_no_stage_feature` ranking. Following
the Spec Decision instruction, the app derives it by taking the XGBoost
`revenue_proxy_full` ranking and removing the mechanical `stage_detail`
row. All remaining features are real signals that survive the proxy
construction.

**Draw simulation constraints.** Max 2 UEFA per group, max 1 team from
any other confederation per group, hosts prefilled (USA→D, Mexico→A,
Canada→B). Acceptance rate in the current build is 99.95%.

**Scenario construction.** Each scenario is a small, interpretable
perturbation of the baseline allocation — moving 1–3 knockout matches or
3–5 group matches between venues. Revenue deltas are driven by the
capacity factor, not by arbitrary multipliers.

---

## Main assumptions

| Assumption | Value | Basis |
|---|---|---|
| Stage ticket prices | Group $120 → Final $450 | Executed project summary |
| Revenue target | `attendance × stage_price` | Proxy construction |
| Reference venue capacity | 70,000 | App design choice |
| Capacity-factor clipping | [0.45, 1.35] | App design choice |
| Low / High revenue band | ±20% of base | App design choice |
| Confederation cap | Max 2 UEFA, max 1 other per group | Simplified FIFA rule |
| Host prefill | Mexico→A, Canada→B, USA→D | Simplified FIFA convention |

---

## Design notes

- **Typography.** Display font is Fraunces (serif), body font is Inter.
  Both loaded from Google Fonts.
- **Color.** Navy (`#1F4E79`) primary, FIFA-adjacent red (`#C8102E`)
  accent, gold (`#C9A227`) highlight. Country colors distinct.
- **Chart theme.** A custom `fifa_exec` plotly template with hairline
  gridlines and Fraunces titles. Applied globally by
  `utils.helpers.configure_page`.
- **Formatting.** All currency values route through `fmt_currency` (short
  form: $1.2B, $45M, $789K) or `fmt_currency_full` (full precision) so the
  app looks consistent everywhere.
- **No state across pages.** Streamlit resets sidebar filters between
  pages by design — this keeps the demo narrative clean.

---

## What this app is, and is not

**Is:** a planning and scenario-exploration tool for capstone presentation
and Q&A. Useful for ranking venues, understanding model-learned signals,
comparing policy tradeoffs, and stress-testing the revenue envelope.

**Is not:** an audited revenue forecast. Revenue figures are proxy
scenarios built on assumed stage pricing. Stadium and city features
absorb missing capacity and metro-demand fields. Scenario mechanics do
not enforce calendar, broadcast, or venue-readiness constraints.
