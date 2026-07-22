"""
helpers.py
----------
Shared UI primitives: page config, custom CSS, KPI cards, section
headers, timeline, pipeline steps, plotly theming.

Single source of truth for all design-system tokens and components.
Every page imports from here — no inline styling anywhere else.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM TOKENS
# ─────────────────────────────────────────────────────────────────────────────

# Typography scale (applied via CSS, documented here for reference)
# PAGE_TITLE    : Fraunces, 2.2rem, weight 600
# SECTION_HEAD  : Inter/Fraunces, 1.25rem, weight 600
# CARD_LABEL    : Inter, 0.74rem, weight 600, uppercase, tracked
# CARD_VALUE    : Fraunces, 1.7rem, weight 600
# BODY          : Inter, 1.0rem, weight 400
# CAPTION       : Inter, 0.88rem, muted italic

# Spacing scale
# SECTION_MARGIN_TOP : 1.6rem
# CARD_PADDING       : 1rem 1.05rem
# CARD_GAP           : use st.columns gap="large"
# CONTAINER_MAX_W    : 1400px

# Color palette
COLOR_INK      = "#0B1320"   # near-black headline
COLOR_MUTED    = "#5B6575"   # secondary text / captions
COLOR_PANEL    = "#F6F7F9"   # soft panel / card background
COLOR_RULE     = "#E4E7EC"   # hairline border / divider
COLOR_PRIMARY  = "#1F4E79"   # deep navy — authoritative
COLOR_ACCENT   = "#C8102E"   # FIFA red — accent only
COLOR_GOLD     = "#C9A227"   # premium gold — highlight / recommended
COLOR_GREEN    = "#2E7D32"   # success / positive callout
COLOR_AMBER    = "#B7791F"   # warning / limitation callout
COLOR_TEAL     = "#1B6E4C"   # Mexico brand / supporting accent
COLOR_NAVY_LT  = "#EBF0F8"   # light navy wash — highlight panels

# Country palette
COUNTRY_COLORS = {
    "USA":    "#1F4E79",
    "Canada": "#C8102E",
    "Mexico": "#1B6E4C",
}

# Stage palette — warm-to-cool gradient: later round = bigger
STAGE_COLORS = {
    "Group":          "#9AB3C9",
    "Early knockout": "#6E90B2",
    "Round of 16":    "#4E739C",
    "Third place":    "#A9842E",
    "Quarter-finals": "#2E5C8A",
    "Semi-finals":    "#C9A227",
    "Final":          "#C8102E",
}

# Default Plotly colorway
COLORWAY = [
    "#1F4E79", "#C8102E", "#C9A227", "#1B6E4C",
    "#5B6575", "#9AB3C9", "#6E90B2", "#A9842E",
]


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────

def configure_page(title: str, subtitle: str | None = None, icon: str = "⚽") -> None:
    """Call at the top of every page. Sets page config and injects the full
    design-system CSS. Pass subtitle=None for pages that set their own header."""
    st.set_page_config(
        page_title=f"FIFA 2026 Planning · {title}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    _configure_plotly()

    if subtitle:
        st.markdown(
            f"""
            <div class="page-head">
              <div class="page-eyebrow">FIFA 2026 · Commercial Match Assignment Optimization</div>
              <h1 class="page-title">{title}</h1>
              <div class="page-subtitle">{subtitle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="page-head">
              <div class="page-eyebrow">FIFA 2026 · Commercial Match Assignment Optimization</div>
              <h1 class="page-title">{title}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _inject_css() -> None:
    st.markdown(
        f"""
        <style>
          /* ── Fonts ──────────────────────────────────────────────── */
          @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

          html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, system-ui, sans-serif;
            color: {COLOR_INK};
          }}
          h1, h2, h3, .page-title {{
            font-family: 'Fraunces', Georgia, serif;
            letter-spacing: -0.01em;
            color: {COLOR_INK};
          }}

          /* ── Page header ────────────────────────────────────────── */
          .page-head {{
            padding: 0.25rem 0 1.1rem 0;
            border-bottom: 2px solid {COLOR_PRIMARY};
            margin-bottom: 1.6rem;
          }}
          .page-eyebrow {{
            font-size: 0.70rem;
            font-weight: 600;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: {COLOR_PRIMARY};
            margin-bottom: 0.35rem;
          }}
          .page-title {{
            font-size: 2.2rem;
            font-weight: 600;
            margin: 0 0 0.3rem 0;
            line-height: 1.1;
          }}
          .page-subtitle {{
            color: {COLOR_MUTED};
            font-size: 1.02rem;
            max-width: 68rem;
            line-height: 1.5;
          }}

          /* ── Section headers ────────────────────────────────────── */
          .section-head {{
            display: flex;
            align-items: baseline;
            gap: 0.9rem;
            margin: 2.0rem 0 0.9rem 0;
            padding-bottom: 0.4rem;
            border-bottom: 1px solid {COLOR_RULE};
          }}
          .section-head h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
            font-family: 'Fraunces', Georgia, serif;
          }}
          .section-head .section-tag {{
            font-size: 0.68rem;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: {COLOR_MUTED};
          }}

          /* ── KPI cards ──────────────────────────────────────────── */
          .kpi-card {{
            background: white;
            border: 1px solid {COLOR_RULE};
            border-radius: 10px;
            padding: 1rem 1.1rem;
            height: 100%;
            box-shadow: 0 1px 3px rgba(11, 19, 32, 0.05);
          }}
          .kpi-card .kpi-label {{
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: {COLOR_MUTED};
            margin-bottom: 0.5rem;
          }}
          .kpi-card .kpi-value {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 1.72rem;
            font-weight: 600;
            color: {COLOR_INK};
            line-height: 1.15;
            word-break: break-word;
          }}
          .kpi-card .kpi-sub {{
            margin-top: 0.35rem;
            font-size: 0.82rem;
            color: {COLOR_MUTED};
            line-height: 1.4;
          }}
          .kpi-card.accent {{
            border-left: 4px solid {COLOR_PRIMARY};
          }}
          .kpi-card.gold {{
            border-left: 4px solid {COLOR_GOLD};
          }}
          .kpi-card.green {{
            border-left: 4px solid {COLOR_GREEN};
          }}

          /* ── Callouts ───────────────────────────────────────────── */
          .callout {{
            padding: 0.95rem 1.15rem;
            border-radius: 8px;
            border: 1px solid {COLOR_RULE};
            background: {COLOR_PANEL};
            margin: 0.8rem 0;
          }}
          .callout.rec   {{ border-left: 4px solid {COLOR_GREEN}; }}
          .callout.limit {{ border-left: 4px solid {COLOR_AMBER}; }}
          .callout.warn  {{ border-left: 4px solid {COLOR_ACCENT}; }}
          .callout.info  {{ border-left: 4px solid {COLOR_PRIMARY}; }}
          .callout .callout-title {{
            font-size: 0.70rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: {COLOR_MUTED};
            margin-bottom: 0.35rem;
          }}
          .callout .callout-body {{
            font-size: 0.95rem;
            color: {COLOR_INK};
            line-height: 1.55;
          }}

          /* ── Interpretation line ─────────────────────────────────── */
          .interp {{
            font-size: 0.87rem;
            color: {COLOR_MUTED};
            font-style: italic;
            margin: 0.25rem 0 0.9rem 0;
            line-height: 1.5;
          }}

          /* ── Timeline (Where our decision lives) ─────────────────── */
          .timeline-outer {{
            display: flex;
            gap: 0;
            margin: 1.2rem 0 1.8rem 0;
            align-items: stretch;
          }}
          .timeline-phase {{
            flex: 1;
            padding: 1.1rem 1.2rem;
            background: white;
            border: 1px solid {COLOR_RULE};
            border-right: none;
          }}
          .timeline-phase:last-child {{
            border-right: 1px solid {COLOR_RULE};
            border-radius: 0 10px 10px 0;
          }}
          .timeline-phase:first-child {{
            border-radius: 10px 0 0 10px;
          }}
          .timeline-phase.decision {{
            background: {COLOR_NAVY_LT};
            border: 2px solid {COLOR_PRIMARY};
            border-radius: 10px;
            margin: -2px 0;
            z-index: 1;
            position: relative;
          }}
          .timeline-arrow {{
            width: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {COLOR_MUTED};
            font-size: 1.1rem;
            flex-shrink: 0;
            background: white;
            border-top: 1px solid {COLOR_RULE};
            border-bottom: 1px solid {COLOR_RULE};
          }}
          .tl-tag {{
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            color: {COLOR_MUTED};
            margin-bottom: 0.45rem;
          }}
          .timeline-phase.decision .tl-tag {{
            color: {COLOR_PRIMARY};
          }}
          .tl-title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 1.05rem;
            font-weight: 600;
            color: {COLOR_INK};
            margin-bottom: 0.6rem;
            line-height: 1.2;
          }}
          .timeline-phase.decision .tl-title {{
            color: {COLOR_PRIMARY};
          }}
          .tl-items {{
            font-size: 0.80rem;
            color: {COLOR_MUTED};
            line-height: 1.65;
          }}
          .timeline-phase.decision .tl-items {{
            color: {COLOR_INK};
            font-size: 0.83rem;
          }}
          .tl-badge {{
            display: inline-block;
            background: {COLOR_PRIMARY};
            color: white;
            font-size: 0.64rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 2px 8px;
            border-radius: 10px;
            margin-bottom: 0.5rem;
          }}

          /* ── Pipeline steps ──────────────────────────────────────── */
          .pipeline-outer {{
            display: flex;
            gap: 1.1rem;
            margin: 1.0rem 0 1.6rem 0;
            align-items: stretch;
          }}
          .pipeline-step {{
            flex: 1;
            background: white;
            border: 1px solid {COLOR_RULE};
            border-radius: 10px;
            padding: 1.1rem 1.1rem 1.0rem 1.1rem;
            position: relative;
          }}
          .pipeline-step-num {{
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: {COLOR_PRIMARY};
            color: white;
            font-size: 0.78rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.7rem;
          }}
          .pipeline-step-title {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 1.0rem;
            font-weight: 600;
            color: {COLOR_INK};
            margin-bottom: 0.35rem;
          }}
          .pipeline-step-sub {{
            font-size: 0.80rem;
            color: {COLOR_MUTED};
            line-height: 1.55;
            margin-bottom: 0.5rem;
          }}
          .pipeline-step-stat {{
            font-size: 0.87rem;
            font-weight: 700;
            color: {COLOR_PRIMARY};
            border-top: 1px solid {COLOR_RULE};
            padding-top: 0.45rem;
            margin-top: 0.45rem;
          }}

          /* ── Walkthrough step cards ──────────────────────────────── */
          .step-card {{
            background: white;
            border: 1px solid {COLOR_RULE};
            border-radius: 10px;
            padding: 1rem 1.05rem;
            height: 100%;
            box-shadow: 0 1px 3px rgba(11, 19, 32, 0.05);
          }}
          .step-card .step-num {{
            font-size: 0.70rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: {COLOR_PRIMARY};
            margin-bottom: 0.3rem;
          }}
          .step-card .step-name {{
            font-family: 'Fraunces', Georgia, serif;
            font-size: 1.02rem;
            font-weight: 600;
            margin: 0.2rem 0 0.35rem 0;
            color: {COLOR_INK};
          }}
          .step-card .step-desc {{
            font-size: 0.83rem;
            color: {COLOR_MUTED};
            line-height: 1.45;
          }}

          /* ── Sidebar ─────────────────────────────────────────────── */
          section[data-testid="stSidebar"] {{
            background: #FAFBFC;
            border-right: 1px solid {COLOR_RULE};
          }}
          section[data-testid="stSidebar"] .block-container {{
            padding-top: 1.2rem;
          }}

          /* ── Container ───────────────────────────────────────────── */
          .block-container {{
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1400px;
          }}

          /* ── Streamlit metric cleanup ────────────────────────────── */
          [data-testid="stMetricLabel"] {{
            font-size: 0.72rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {COLOR_MUTED} !important;
          }}
          [data-testid="stMetricValue"] {{
            font-family: 'Fraunces', Georgia, serif !important;
            font-size: 1.55rem !important;
          }}

          /* ── Tabs ────────────────────────────────────────────────── */
          .stTabs [data-baseweb="tab-list"] {{
            gap: 0.25rem;
          }}
          .stTabs [data-baseweb="tab"] {{
            font-weight: 500;
          }}

          /* ── DataFrames ──────────────────────────────────────────── */
          [data-testid="stDataFrame"] {{
            border-radius: 8px;
            overflow: hidden;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _configure_plotly() -> None:
    pio.templates["fifa_exec"] = go.layout.Template(
        layout=dict(
            font=dict(family="Inter, sans-serif", color=COLOR_INK, size=13),
            title=dict(font=dict(family="Fraunces, serif", size=17, color=COLOR_INK)),
            colorway=COLORWAY,
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(gridcolor=COLOR_RULE, linecolor=COLOR_RULE, zerolinecolor=COLOR_RULE),
            yaxis=dict(gridcolor=COLOR_RULE, linecolor=COLOR_RULE, zerolinecolor=COLOR_RULE),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
            margin=dict(l=60, r=30, t=50, b=50),
        )
    )
    pio.templates.default = "fifa_exec"


# ─────────────────────────────────────────────────────────────────────────────
# UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def section(title: str, tag: str | None = None) -> None:
    """Section header with optional eyebrow tag."""
    tag_html = f'<span class="section-tag">{tag}</span>' if tag else ""
    st.markdown(
        f'<div class="section-head"><h2>{title}</h2>{tag_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(
    label: str,
    value: str,
    sub: str | None = None,
    accent: bool = False,
    variant: str = "",
) -> None:
    """KPI metric tile.

    variant: '' (default), 'accent' (navy left border),
             'gold' (gold left border), 'green' (green left border).
    accent=True is a shorthand for variant='accent'.
    """
    if accent:
        variant = "accent"
    klass = f"kpi-card {variant}".strip()
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="{klass}">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def callout(body: str, title: str = "Note", kind: str = "rec") -> None:
    """Callout box. kind ∈ {'rec', 'limit', 'warn', 'info'}."""
    st.markdown(
        f"""
        <div class="callout {kind}">
          <div class="callout-title">{title}</div>
          <div class="callout-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def interp(text: str) -> None:
    """One-line interpretation note below a chart."""
    st.markdown(f'<div class="interp">{text}</div>', unsafe_allow_html=True)


def timeline_block(phases: list[dict]) -> None:
    """Render a horizontal timeline with a highlighted decision window.

    Each phase dict:
        tag      : str  — eyebrow label (e.g. "BEFORE THE DRAW")
        title    : str  — bold title
        items    : list[str] — bullet lines
        badge    : str | None  — optional top badge text
        highlight: bool — draws navy highlight border (the decision window)
    """
    parts = []
    for i, phase in enumerate(phases):
        is_decision = phase.get("highlight", False)
        cls = "timeline-phase decision" if is_decision else "timeline-phase"
        badge_html = (
            f'<div class="tl-badge">{phase["badge"]}</div>'
            if phase.get("badge") else ""
        )
        items_html = "".join(f"{item}<br>" for item in phase.get("items", []))
        parts.append(
            f'<div class="{cls}">'
            f'{badge_html}'
            f'<div class="tl-tag">{phase["tag"]}</div>'
            f'<div class="tl-title">{phase["title"]}</div>'
            f'<div class="tl-items">{items_html}</div>'
            f'</div>'
        )
        if i < len(phases) - 1:
            parts.append('<div class="timeline-arrow">›</div>')

    st.markdown(
        f'<div class="timeline-outer">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )


def pipeline_steps(steps: list[dict]) -> None:
    """Render a row of numbered pipeline step cards.

    Each step dict:
        num   : str — step number
        title : str — card title
        sub   : str — description
        stat  : str | None — highlighted bottom stat
    """
    cards = []
    for step in steps:
        stat_html = (
            f'<div class="pipeline-step-stat">{step["stat"]}</div>'
            if step.get("stat") else ""
        )
        cards.append(
            f'<div class="pipeline-step">'
            f'<div class="pipeline-step-num">{step["num"]}</div>'
            f'<div class="pipeline-step-title">{step["title"]}</div>'
            f'<div class="pipeline-step-sub">{step["sub"]}</div>'
            f'{stat_html}'
            f'</div>'
        )
    st.markdown(
        f'<div class="pipeline-outer">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def step_card(num: str, name: str, desc: str) -> None:
    """Single demo-walkthrough step card."""
    st.markdown(
        f"""
        <div class="step-card">
          <div class="step-num">Step {num}</div>
          <div class="step-name">{name}</div>
          <div class="step-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_context_panel() -> None:
    """Standing sidebar footer reminding viewers of model choice and data caveat.
    Call from any page after its own sidebar controls."""
    with st.sidebar:
        st.markdown("---")
        st.caption("**Primary model**")
        st.caption("`revenue_proxy_no_stage_feature`")
        st.caption(
            "All revenue figures are **scenario / proxy** revenue derived from "
            "assumed stage-level ticket prices. Not audited observed revenue."
        )
        st.caption("MQM Capstone · Team 7 · Duke Fuqua · Spring 2026")
