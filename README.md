# FIFA 2026 Draw Optimization

Simulation and optimization engine for the FIFA 2026 World Cup draw. Built as a team capstone project for the MS in Quantitative Management program at Duke Fuqua, exploring whether a data-driven redesign of the draw procedure could improve commercial value and competitive balance across the expanded 48-team format.

**Live app:** [fifa-2026-draw.streamlit.app](https://fifa-2026-draw.streamlit.app)

---

## The Problem

The 2026 World Cup expands from 32 to 48 teams and runs across 16 host cities in the US, Canada, and Mexico. FIFA's draw procedure determines which teams land in which groups and which venues host which matches. Those decisions drive:

- **Broadcast and sponsorship revenue** (marquee matchups in prime-time windows)
- **Competitive balance** (group difficulty spread, avoiding "groups of death")
- **Venue economics** (matchup quality vs venue capacity and market)

The current draw is largely rule-bound and random. This project asks: what would a draw procedure optimized against revenue and competitive balance look like, and how much value is on the table?

## What This Project Does

1. **Simulates FIFA's current draw procedure** across 10,000+ Monte Carlo iterations to establish a baseline distribution of group compositions and venue allocations
2. **Models revenue** per match as a function of team quality, matchup appeal, venue capacity, market size, and time slot
3. **Proposes an optimized draw procedure** that improves expected commercial value while maintaining competitive balance constraints
4. **Quantifies the trade-offs** between revenue maximization, competitive fairness, and adherence to existing FIFA rules
5. **Delivers findings through an interactive Streamlit app** with six analytical views (executive summary, tournament scenarios, venue revenue optimization, decision trade-offs, final recommendation, methodology)

## Key Findings

_(See `app/data/raw/FIFA_Revenue_Executive_Summary_0417.md` for the full write-up.)_

- Baseline vs optimized draw comparison across 10,000+ simulations
- Revenue lift estimates from targeted matchup and venue allocation
- Competitive balance metrics that hold or improve under the optimized procedure
- Sensitivity analysis on key modeling assumptions

## Tech Stack

- **Python**: pandas, numpy, scipy, scikit-learn
- **Simulation**: custom Monte Carlo engine
- **Modeling**: revenue regression on historical tournament data
- **App**: Streamlit multi-page interface
- **Visualization**: plotly, matplotlib

## Repo Structure

```
FIFA-2026-draw-optimization/
├── README.md                       This file
├── LICENSE                         MIT license
├── .gitignore                      Python ignore rules
├── app/                            Interactive Streamlit application
│   ├── app.py                      Streamlit entry point
│   ├── build_app_data.py           Assembles app-ready data from model outputs
│   ├── requirements.txt            Python dependencies for the app
│   ├── README.md                   Team's original app-level readme
│   ├── pages/                      6 Streamlit analytical views
│   │   ├── 1_Executive_Summary.py
│   │   ├── 2_Tournament_Scenarios.py
│   │   ├── 3_Venue_Revenue_Optimization.py
│   │   ├── 4_Decision_Tradeoffs.py
│   │   ├── 5_Final_Recommendation.py
│   │   └── 6_Methodology_Limitations.py
│   ├── utils/                      Core logic modules
│   │   ├── assignment_engine.py
│   │   ├── draw_engine.py
│   │   ├── policy_logic.py
│   │   ├── schedule_data.py
│   │   ├── official_baseline.py
│   │   ├── load_data.py
│   │   ├── helpers.py
│   │   ├── formatters.py
│   │   └── validation.py
│   └── data/                       App datasets and reference material
│       ├── raw/                    Source data, assumptions, and written deliverables
│       ├── app_ready/              Model-ready datasets loaded by the app
│       └── simulation/             Simulation outputs used by the app
└── simulation/                     Standalone Monte Carlo simulation
    ├── Final_Monte_Carlo_Sim.py    Simulation engine
    └── (CSV, PNG, JSON outputs from 10,000+ iteration runs)
```

## Running Locally

```bash
git clone https://github.com/rahejachirayu-byte/FIFA-2026-draw-optimization.git
cd FIFA-2026-draw-optimization/app
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`.

To re-run the standalone Monte Carlo simulation:

```bash
cd FIFA-2026-draw-optimization/simulation
python Final_Monte_Carlo_Sim.py
```

## Methodology in Brief

The simulation engine reproduces FIFA's pot-based draw procedure with regional and confederation constraints. Each iteration produces a full 48-team group stage with venue and time slot assignments. The revenue model was trained on historical World Cup data (attendance, broadcast estimates, sponsorship categories) and applied to each simulated tournament to produce an expected revenue distribution.

The optimization layer treats the draw as a constrained assignment problem: maximize expected revenue subject to competitive balance thresholds and FIFA's non-negotiable rules (regional separation, host team placement). Trade-off curves show how much revenue is gained per unit of competitive balance relaxed.

Full methodology, assumptions, and change history are documented in the `app/data/raw/` folder (executive summary, presentation story flow, change log, assumptions CSV).

## What This Project Is Not

- Not affiliated with FIFA or any host committee
- Not a prediction of actual match outcomes
- Not a claim that FIFA's real draw is suboptimal in ways that would be politically implementable
- A modeling exercise to quantify the value of decision-support tools in mega-event planning

## About

This project was completed as a team capstone for the MS in Quantitative Management: Business Analytics program at Duke Fuqua (2026).

**Maintainer of this repository:**

Chirayu Raheja. MS in Quantitative Management, Business Analytics, Duke Fuqua (2026). Prior experience in finance and analytics at PwC India and Aureate Healthcare.

- LinkedIn: [linkedin.com/in/chirayu-raheja](https://linkedin.com/in/chirayu-raheja)
- Email: chirayu.raheja@duke.edu

## License

MIT License. See `LICENSE` for details.
