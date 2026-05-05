"""Streamlit front-end for Box Office Gambler."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from data import GENRES, MONTHS, STAR_TIERS, FRANCHISE_TYPES
from engine import MovieInput, run_simulation, get_decision

st.set_page_config(
    page_title="Box Office Gambler",
    page_icon="🎬",
    layout="wide",
)

STYLE = """
<style>
    .block-container { padding-top: 1.5rem; }
    .decision-green  { background: #0d4d2b; color: #4ade80; padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: 700; }
    .decision-orange { background: #4d3800; color: #fbbf24; padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: 700; }
    .decision-red    { background: #4d0d0d; color: #f87171; padding: 1.2rem; border-radius: 12px; text-align: center; font-size: 1.4rem; font-weight: 700; }
    .factor-positive { color: #4ade80; }
    .factor-negative { color: #f87171; }
    .factor-neutral  { color: #94a3b8; }
    .metric-card     { background: #1e293b; padding: 1rem; border-radius: 10px; text-align: center; }
    .metric-card h3  { margin: 0; font-size: 0.85rem; color: #94a3b8; font-weight: 400; }
    .metric-card p   { margin: 0; font-size: 1.6rem; font-weight: 700; color: #f8fafc; }
    div[data-testid="stSidebar"] { background: #0f172a; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

st.title("Box Office Gambler")
st.caption("Monte Carlo greenlight simulator — CS 4580 final project")


with st.sidebar:
    st.header("Movie Parameters")
    title = st.text_input("Movie Title", value="Untitled Film")
    budget = st.slider("Production Budget ($M)", min_value=1, max_value=400, value=100, step=5)
    genre = st.selectbox("Primary Genre", GENRES, index=0)
    release_month = st.selectbox("Release Month", MONTHS, index=4)
    star_tier = st.selectbox("Lead Actor Star Power", STAR_TIERS, index=1)
    franchise_type = st.selectbox("Franchise Status", FRANCHISE_TYPES, index=0)
    rating = st.selectbox("MPAA Rating", ["G", "PG", "PG-13", "R"], index=2)

    st.divider()
    n_trials = st.select_slider(
        "Simulation Trials",
        options=[1_000, 5_000, 10_000, 50_000, 100_000],
        value=10_000,
    )
    run_btn = st.button("Run Simulation", use_container_width=True, type="primary")


def _metric(label: str, value: str) -> str:
    return f'<div class="metric-card"><h3>{label}</h3><p>{value}</p></div>'


def _histogram(values, title, color, breakeven=None):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=values, nbinsx=80, marker_color=color, opacity=0.85))
    median = float(np.median(values))
    if breakeven is not None:
        fig.add_vline(
            x=breakeven, line_dash="dash", line_color="#f87171",
            annotation_text=f"Break-even (${breakeven:.0f}M)",
        )
    fig.add_vline(
        x=median, line_dash="dash", line_color="#4ade80",
        annotation_text=f"Median (${median:.0f}M)",
    )
    fig.update_layout(
        xaxis_title=title,
        yaxis_title="Frequency",
        template="plotly_dark",
        height=400,
        margin=dict(t=20, b=40),
        showlegend=False,
    )
    return fig


def _counterfactual_bar(values_by_label, current_choice, title):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(values_by_label.keys()),
        y=list(values_by_label.values()),
        marker_color=[
            "#f59e0b" if k == current_choice else "#6366f1"
            for k in values_by_label
        ],
    ))
    fig.update_layout(
        title=title,
        yaxis_title="Median Worldwide ($M)",
        template="plotly_dark",
        height=350,
        margin=dict(t=40, b=40),
    )
    return fig


if run_btn:
    movie = MovieInput(
        title=title, budget=budget, genre=genre,
        release_month=release_month, star_tier=star_tier,
        franchise_type=franchise_type, rating=rating,
    )

    with st.spinner("Running Monte Carlo simulation..."):
        result = run_simulation(movie, n_trials=n_trials)
        decision = get_decision(result, budget)

    st.markdown(
        f'<div class="decision-{decision["color"]}">'
        f'{decision["decision"]}: {decision["reasoning"]}'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    median_roi = float(np.median(result.roi_values))
    cols = st.columns(5)
    cols[0].markdown(_metric("Median Worldwide", f"${result.median_worldwide:,.0f}M"), unsafe_allow_html=True)
    cols[1].markdown(_metric("P(Profit)", f"{result.prob_profit:.0%}"), unsafe_allow_html=True)
    cols[2].markdown(_metric("P(Blockbuster)", f"{result.prob_blockbuster:.0%}"), unsafe_allow_html=True)
    cols[3].markdown(_metric("P(Flop)", f"{result.prob_flop:.0%}"), unsafe_allow_html=True)
    cols[4].markdown(_metric("Median ROI", f"{median_roi:+.0f}%"), unsafe_allow_html=True)
    st.markdown("")

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.subheader("Worldwide Gross Distribution")
        st.plotly_chart(
            _histogram(result.worldwide_totals, "Worldwide Gross ($M)", "#6366f1", breakeven=budget * 2),
            use_container_width=True,
        )
    with chart_right:
        st.subheader("Opening Weekend Distribution")
        st.plotly_chart(
            _histogram(result.opening_weekends, "Opening Weekend ($M)", "#f59e0b"),
            use_container_width=True,
        )

    st.subheader("Return on Investment Distribution")
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Histogram(x=result.roi_values, nbinsx=80, marker_color="#8b5cf6", opacity=0.85))
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

    st.subheader("Outcome Percentiles")
    percentiles = [5, 10, 25, 50, 75, 90, 95]
    perc_data = {
        "Percentile": [f"P{p}" for p in percentiles],
        "Opening Weekend ($M)": [f"${np.percentile(result.opening_weekends, p):,.0f}" for p in percentiles],
        "Domestic Total ($M)":  [f"${np.percentile(result.domestic_totals, p):,.0f}" for p in percentiles],
        "Worldwide Total ($M)": [f"${np.percentile(result.worldwide_totals, p):,.0f}" for p in percentiles],
        "ROI (%)":              [f"{np.percentile(result.roi_values, p):+,.0f}%" for p in percentiles],
    }
    st.dataframe(perc_data, use_container_width=True, hide_index=True)

    st.subheader("Decision Explanation — Factor Attribution")
    st.caption("How each input factor influenced the simulation outcome")
    direction_marker = {"positive": "▲", "negative": "▼", "neutral": "•"}
    for factor_name, direction, description in result.explanations:
        st.markdown(
            f'{direction_marker[direction]} **{factor_name}** — '
            f'<span class="factor-{direction}">{description}</span>',
            unsafe_allow_html=True,
        )

    st.subheader("Counterfactual Analysis")
    st.caption("What if you changed one parameter? Median worldwide gross for each alternative.")

    def _sweep(field: str, options):
        out = {}
        for value in options:
            kwargs = dict(
                title=title, budget=budget, genre=genre, release_month=release_month,
                star_tier=star_tier, franchise_type=franchise_type, rating=rating,
            )
            kwargs[field] = value
            alt = MovieInput(**kwargs)
            out[value] = run_simulation(alt, n_trials=2_000, seed=42).median_worldwide
        return out

    st.plotly_chart(
        _counterfactual_bar(_sweep("genre", GENRES), genre,
                            "Median Worldwide by Genre (your pick highlighted)"),
        use_container_width=True,
    )
    st.plotly_chart(
        _counterfactual_bar(_sweep("release_month", MONTHS), release_month,
                            "Median Worldwide by Release Month (your pick highlighted)"),
        use_container_width=True,
    )

else:
    st.info("Configure your movie parameters in the sidebar and click **Run Simulation** "
            "to see the Monte Carlo forecast.")

    st.markdown(
        """
        ### How it works

        Box Office Gambler runs a Monte Carlo simulation over a movie's financial
        outcome rather than producing a single point estimate. Each trial samples
        an opening weekend (driven by budget, genre, release month, star power,
        franchise status, and rating), applies a genre-specific legs multiplier
        to get a domestic total, then layers on an international multiplier
        and a studio revenue share to arrive at ROI.

        The result, after thousands of trials, is a probability distribution
        over worldwide gross and ROI. From that you get a greenlight decision,
        per-factor attributions explaining what's helping or hurting the outlook,
        and counterfactual sweeps showing how a different genre or release
        month would have shifted the median.
        """
    )
