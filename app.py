"""Box Office Gambler — Monte Carlo Box Office Simulator."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from engine import MovieInput, run_simulation, get_decision
from data import GENRES, MONTHS, STAR_TIERS, FRANCHISE_TYPES

st.set_page_config(
    page_title="Box Office Gambler",
    page_icon="🎬",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .decision-green { background: #0d4d2b; color: #4ade80; padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: 700; }
    .decision-orange { background: #4d3800; color: #fbbf24; padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: 700; }
    .decision-red { background: #4d0d0d; color: #f87171; padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: 700; }
    .factor-positive { color: #4ade80; }
    .factor-negative { color: #f87171; }
    .factor-neutral { color: #94a3b8; }
    .metric-card { background: #1e293b; padding: 1rem; border-radius: 10px; text-align: center; }
    .metric-card h3 { margin: 0; font-size: 0.85rem; color: #94a3b8; font-weight: 400; }
    .metric-card p { margin: 0; font-size: 1.6rem; font-weight: 700; color: #f8fafc; }
    div[data-testid="stSidebar"] { background: #0f172a; }
</style>
""", unsafe_allow_html=True)

st.title("🎬 Box Office Gambler")
st.caption("Monte Carlo simulation for box office forecasting — CS 458 Final Project")

# --- Sidebar: Inputs ---
with st.sidebar:
    st.header("Movie Parameters")

    title = st.text_input("Movie Title", value="Untitled Film")
    budget = st.slider("Production Budget ($M)", min_value=1, max_value=400, value=100, step=5)
    genre = st.selectbox("Primary Genre", GENRES, index=0)
    release_month = st.selectbox("Release Month", MONTHS, index=4)  # May default
    star_tier = st.selectbox("Lead Actor Star Power", STAR_TIERS, index=1)
    franchise_type = st.selectbox("Franchise Status", FRANCHISE_TYPES, index=0)
    rating = st.selectbox("MPAA Rating", ["G", "PG", "PG-13", "R"], index=2)

    st.divider()
    n_trials = st.select_slider("Simulation Trials", options=[1_000, 5_000, 10_000, 50_000, 100_000], value=10_000)

    run_btn = st.button("🎰 Run Simulation", use_container_width=True, type="primary")

# --- Run simulation ---
if run_btn:
    movie = MovieInput(
        title=title, budget=budget, genre=genre,
        release_month=release_month, star_tier=star_tier,
        franchise_type=franchise_type, rating=rating,
    )

    with st.spinner("Running Monte Carlo simulation..."):
        result = run_simulation(movie, n_trials=n_trials)
        decision = get_decision(result, budget)

    # --- Decision Banner ---
    st.markdown(f'<div class="decision-{decision["color"]}">{decision["decision"]}: {decision["reasoning"]}</div>', unsafe_allow_html=True)

    st.markdown("")

    # --- Key Metrics ---
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f'<div class="metric-card"><h3>Median Worldwide</h3><p>${result.median_worldwide:,.0f}M</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h3>P(Profit)</h3><p>{result.prob_profit:.0%}</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><h3>P(Blockbuster)</h3><p>{result.prob_blockbuster:.0%}</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><h3>P(Flop)</h3><p>{result.prob_flop:.0%}</p></div>', unsafe_allow_html=True)
    with c5:
        median_roi = float(np.median(result.roi_values))
        st.markdown(f'<div class="metric-card"><h3>Median ROI</h3><p>{median_roi:+.0f}%</p></div>', unsafe_allow_html=True)

    st.markdown("")

    # --- Charts ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Worldwide Gross Distribution")
        fig_ww = go.Figure()
        fig_ww.add_trace(go.Histogram(
            x=result.worldwide_totals, nbinsx=80,
            marker_color="#6366f1", opacity=0.85,
            name="Simulated outcomes",
        ))
        # Break-even line (studio needs 2x budget from worldwide to profit)
        breakeven = budget * 2
        fig_ww.add_vline(x=breakeven, line_dash="dash", line_color="#f87171", annotation_text=f"Break-even (${breakeven}M)")
        fig_ww.add_vline(x=result.median_worldwide, line_dash="dash", line_color="#4ade80", annotation_text=f"Median (${result.median_worldwide:.0f}M)")
        fig_ww.update_layout(
            xaxis_title="Worldwide Gross ($M)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=400,
            margin=dict(t=20, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig_ww, use_container_width=True)

    with chart_col2:
        st.subheader("Opening Weekend Distribution")
        fig_ow = go.Figure()
        fig_ow.add_trace(go.Histogram(
            x=result.opening_weekends, nbinsx=60,
            marker_color="#f59e0b", opacity=0.85,
        ))
        median_ow = float(np.median(result.opening_weekends))
        fig_ow.add_vline(x=median_ow, line_dash="dash", line_color="#4ade80", annotation_text=f"Median (${median_ow:.0f}M)")
        fig_ow.update_layout(
            xaxis_title="Opening Weekend ($M)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=400,
            margin=dict(t=20, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig_ow, use_container_width=True)

    # --- ROI distribution ---
    st.subheader("Return on Investment Distribution")
    fig_roi = go.Figure()
    roi_colors = np.where(result.roi_values >= 0, "#4ade80", "#f87171")
    fig_roi.add_trace(go.Histogram(
        x=result.roi_values, nbinsx=80,
        marker_color="#8b5cf6", opacity=0.85,
    ))
    fig_roi.add_vline(x=0, line_dash="dash", line_color="#f87171", annotation_text="Break-even")
    fig_roi.update_layout(
        xaxis_title="ROI (%)",
        yaxis_title="Frequency",
        template="plotly_dark",
        height=350,
        margin=dict(t=20, b=40),
        showlegend=False,
    )
    st.plotly_chart(fig_roi, use_container_width=True)

    # --- Percentile Table ---
    st.subheader("Outcome Percentiles")
    percentiles = [5, 10, 25, 50, 75, 90, 95]
    perc_data = {
        "Percentile": [f"P{p}" for p in percentiles],
        "Opening Weekend ($M)": [f"${np.percentile(result.opening_weekends, p):,.0f}" for p in percentiles],
        "Domestic Total ($M)": [f"${np.percentile(result.domestic_totals, p):,.0f}" for p in percentiles],
        "Worldwide Total ($M)": [f"${np.percentile(result.worldwide_totals, p):,.0f}" for p in percentiles],
        "ROI (%)": [f"{np.percentile(result.roi_values, p):+,.0f}%" for p in percentiles],
    }
    st.dataframe(perc_data, use_container_width=True, hide_index=True)

    # --- Factor Attribution (Explainability) ---
    st.subheader("Decision Explanation — Factor Attribution")
    st.caption("How each input factor influenced the simulation outcome")

    for factor_name, direction, description in result.explanations:
        icon = {"positive": "🟢", "negative": "🔴", "neutral": "🔵"}[direction]
        css_class = f"factor-{direction}"
        st.markdown(f'{icon} **{factor_name}** — <span class="{css_class}">{description}</span>', unsafe_allow_html=True)

    # --- Sensitivity (counterfactual) ---
    st.subheader("Counterfactual Analysis")
    st.caption("What if you changed one parameter? Showing median worldwide gross for each alternative.")

    # Genre sensitivity
    genre_medians = {}
    for g in GENRES:
        alt = MovieInput(title=title, budget=budget, genre=g, release_month=release_month,
                         star_tier=star_tier, franchise_type=franchise_type, rating=rating)
        alt_result = run_simulation(alt, n_trials=2_000, seed=42)
        genre_medians[g] = alt_result.median_worldwide

    fig_genre = go.Figure()
    colors = ["#6366f1" if g != genre else "#f59e0b" for g in genre_medians]
    fig_genre.add_trace(go.Bar(
        x=list(genre_medians.keys()),
        y=list(genre_medians.values()),
        marker_color=colors,
    ))
    fig_genre.update_layout(
        title="Median Worldwide by Genre (your pick highlighted)",
        yaxis_title="Median Worldwide ($M)",
        template="plotly_dark",
        height=350,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig_genre, use_container_width=True)

    # Month sensitivity
    month_medians = {}
    for m in MONTHS:
        alt = MovieInput(title=title, budget=budget, genre=genre, release_month=m,
                         star_tier=star_tier, franchise_type=franchise_type, rating=rating)
        alt_result = run_simulation(alt, n_trials=2_000, seed=42)
        month_medians[m] = alt_result.median_worldwide

    fig_month = go.Figure()
    colors_m = ["#6366f1" if m != release_month else "#f59e0b" for m in month_medians]
    fig_month.add_trace(go.Bar(
        x=list(month_medians.keys()),
        y=list(month_medians.values()),
        marker_color=colors_m,
    ))
    fig_month.update_layout(
        title="Median Worldwide by Release Month (your pick highlighted)",
        yaxis_title="Median Worldwide ($M)",
        template="plotly_dark",
        height=350,
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig_month, use_container_width=True)

else:
    # Landing state
    st.info("Configure your movie parameters in the sidebar and click **Run Simulation** to see the Monte Carlo forecast.")

    st.markdown("""
    ### How It Works

    **Box Office Gambler** uses Monte Carlo simulation to forecast a film's financial performance
    under uncertainty. Instead of a single prediction, it runs thousands of simulated outcomes
    by sampling from empirical distributions for:

    - **Opening weekend** — driven by budget, genre, release timing, star power, franchise status, and rating
    - **Domestic legs** — how much total domestic gross the opening weekend represents (genre-dependent)
    - **International multiplier** — how well the genre travels overseas
    - **Studio revenue share** — assumes ~50% of theatrical gross returns to the studio

    The system then produces:
    1. **A greenlight decision** (Green Light / Proceed with Caution / Pass)
    2. **Probability distributions** for worldwide gross, opening weekend, and ROI
    3. **Factor attribution** explaining which inputs helped or hurt the outlook
    4. **Counterfactual analysis** showing how different genre or month choices would change the outcome

    This approach makes the decision-making process **transparent and auditable** — you can see
    exactly which assumptions drive the forecast and how sensitive the outcome is to each input.
    """)
