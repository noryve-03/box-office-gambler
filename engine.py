"""Monte Carlo simulation engine for box office prediction."""

import numpy as np
from dataclasses import dataclass
from data import (
    GENRE_MULTIPLIERS, LEGS_BY_GENRE, MONTH_FACTORS,
    STAR_POWER, FRANCHISE_BOOST, INTL_MULTIPLIER,
)


@dataclass
class MovieInput:
    title: str
    budget: float          # millions USD
    genre: str
    release_month: str
    star_tier: str
    franchise_type: str
    rating: str            # G, PG, PG-13, R


# Rating affects audience ceiling
RATING_FACTORS = {
    "G": 0.85,
    "PG": 1.05,
    "PG-13": 1.10,
    "R": 0.80,
}


@dataclass
class SimulationResult:
    opening_weekends: np.ndarray
    domestic_totals: np.ndarray
    worldwide_totals: np.ndarray
    roi_values: np.ndarray
    prob_profit: float
    prob_blockbuster: float   # > 2x budget worldwide
    prob_flop: float          # < 0.5x budget worldwide
    median_worldwide: float
    explanations: list        # list of (factor, direction, magnitude) tuples


def run_simulation(movie: MovieInput, n_trials: int = 10_000, seed: int = None) -> SimulationResult:
    """Run Monte Carlo simulation for a movie's box office performance."""
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    budget = movie.budget
    genre = movie.genre
    month = movie.release_month

    # --- Base opening weekend from budget (empirical: ~15-25% of budget for wide release) ---
    base_ow_frac = rng.normal(0.20, 0.05, n_trials).clip(0.08, 0.50)
    base_ow = budget * base_ow_frac

    # --- Genre multiplier on total gross ---
    gm = GENRE_MULTIPLIERS[genre]
    genre_mult = rng.normal(gm["mean"], gm["std"], n_trials).clip(0.5, 8.0)

    # --- Month factor on opening weekend ---
    month_factor = MONTH_FACTORS[month]
    month_noise = rng.normal(month_factor, 0.08, n_trials).clip(0.3, 2.0)

    # --- Star power boost (absolute, in millions) ---
    sp = STAR_POWER[movie.star_tier]
    star_boost = rng.normal(sp["boost_mean"], sp["boost_std"], n_trials).clip(0, 80)

    # --- Franchise multiplier ---
    fb = FRANCHISE_BOOST[movie.franchise_type]
    franchise_mult = rng.normal(fb["mult_mean"], fb["mult_std"], n_trials).clip(0.5, 3.0)

    # --- Rating factor ---
    rating_f = RATING_FACTORS.get(movie.rating, 1.0)

    # --- Compute opening weekend ---
    opening_weekends = (base_ow * month_noise * franchise_mult * rating_f + star_boost).clip(1, None)

    # --- Legs: opening weekend as fraction of domestic total ---
    legs = LEGS_BY_GENRE[genre]
    ow_fraction = rng.normal(legs["mean"], legs["std"], n_trials).clip(0.15, 0.75)
    domestic_totals = opening_weekends / ow_fraction

    # --- International multiplier ---
    im = INTL_MULTIPLIER[genre]
    intl_mult = rng.normal(im["mean"], im["std"], n_trials).clip(0.1, 4.0)
    international = domestic_totals * intl_mult
    worldwide_totals = domestic_totals + international

    # --- ROI (assuming theatrical revenue = ~50% of gross goes to studio) ---
    studio_revenue = worldwide_totals * 0.50
    roi_values = (studio_revenue - budget) / budget * 100  # percentage

    # --- Probabilities ---
    prob_profit = float(np.mean(studio_revenue > budget))
    prob_blockbuster = float(np.mean(worldwide_totals > 2 * budget))
    prob_flop = float(np.mean(worldwide_totals < 0.5 * budget))
    median_worldwide = float(np.median(worldwide_totals))

    # --- Build explanations (factor attribution) ---
    explanations = _build_explanations(movie, month_factor, rating_f, genre_mult, intl_mult, franchise_mult, star_boost)

    return SimulationResult(
        opening_weekends=opening_weekends,
        domestic_totals=domestic_totals,
        worldwide_totals=worldwide_totals,
        roi_values=roi_values,
        prob_profit=prob_profit,
        prob_blockbuster=prob_blockbuster,
        prob_flop=prob_flop,
        median_worldwide=median_worldwide,
        explanations=explanations,
    )


def _build_explanations(movie, month_factor, rating_f, genre_mult, intl_mult, franchise_mult, star_boost):
    """Generate human-readable factor attributions."""
    factors = []

    # Month
    if month_factor > 1.1:
        factors.append(("Release month", "positive", f"{movie.release_month} is a peak season (+{(month_factor-1)*100:.0f}% opening boost)"))
    elif month_factor < 0.8:
        factors.append(("Release month", "negative", f"{movie.release_month} is a dump month ({(month_factor-1)*100:.0f}% opening drag)"))
    else:
        factors.append(("Release month", "neutral", f"{movie.release_month} is an average release window"))

    # Genre
    gm = GENRE_MULTIPLIERS[movie.genre]
    if gm["mean"] > 2.7:
        factors.append(("Genre", "positive", f"{movie.genre} films tend to have strong total multipliers ({gm['mean']:.1f}x budget avg)"))
    elif gm["mean"] < 2.1:
        factors.append(("Genre", "negative", f"{movie.genre} films have modest multipliers ({gm['mean']:.1f}x budget avg)"))
    else:
        factors.append(("Genre", "neutral", f"{movie.genre} has a typical gross multiplier ({gm['mean']:.1f}x)"))

    # Legs
    legs = LEGS_BY_GENRE[movie.genre]
    if legs["mean"] > 0.40:
        factors.append(("Legs", "negative", f"{movie.genre} is front-loaded — {legs['mean']*100:.0f}% of domestic gross in opening weekend"))
    elif legs["mean"] < 0.30:
        factors.append(("Legs", "positive", f"{movie.genre} has long legs — only {legs['mean']*100:.0f}% of gross in opening weekend"))
    else:
        factors.append(("Legs", "neutral", f"Typical legs for {movie.genre} ({legs['mean']*100:.0f}% opening share)"))

    # Star power
    sp = STAR_POWER[movie.star_tier]
    if sp["boost_mean"] > 15:
        factors.append(("Star power", "positive", f"{movie.star_tier} adds ~${sp['boost_mean']}M to opening weekend"))
    elif sp["boost_mean"] > 0:
        factors.append(("Star power", "neutral", f"{movie.star_tier} gives a modest +${sp['boost_mean']}M opening bump"))
    else:
        factors.append(("Star power", "negative", "No star power premium on opening weekend"))

    # Franchise
    fb = FRANCHISE_BOOST[movie.franchise_type]
    if fb["mult_mean"] > 1.2:
        factors.append(("Franchise", "positive", f"{movie.franchise_type} status multiplies performance by ~{fb['mult_mean']:.1f}x"))
    else:
        factors.append(("Franchise", "neutral", f"{movie.franchise_type} — no built-in audience multiplier"))

    # Rating
    if rating_f > 1.0:
        factors.append(("Rating", "positive", f"{movie.rating} rating maximizes audience reach (+{(rating_f-1)*100:.0f}%)"))
    elif rating_f < 0.9:
        factors.append(("Rating", "negative", f"{movie.rating} rating limits audience ceiling ({(rating_f-1)*100:.0f}%)"))
    else:
        factors.append(("Rating", "neutral", f"{movie.rating} rating has minimal audience impact"))

    # International
    im = INTL_MULTIPLIER[movie.genre]
    if im["mean"] > 1.3:
        factors.append(("International", "positive", f"{movie.genre} travels well internationally ({im['mean']:.1f}x domestic)"))
    elif im["mean"] < 0.8:
        factors.append(("International", "negative", f"{movie.genre} is domestic-heavy (only {im['mean']:.1f}x international)"))
    else:
        factors.append(("International", "neutral", f"Average international performance for {movie.genre}"))

    # Budget risk
    if movie.budget > 200:
        factors.append(("Budget risk", "negative", f"${movie.budget:.0f}M budget requires massive worldwide gross to recoup"))
    elif movie.budget < 30:
        factors.append(("Budget risk", "positive", f"Low ${movie.budget:.0f}M budget means easier path to profitability"))
    else:
        factors.append(("Budget risk", "neutral", f"${movie.budget:.0f}M budget is in the mid-range"))

    return factors


def get_decision(result: SimulationResult, budget: float) -> dict:
    """Return a greenlight decision with reasoning."""
    if result.prob_profit >= 0.70:
        decision = "GREEN LIGHT"
        color = "green"
        reasoning = f"Strong outlook — {result.prob_profit:.0%} chance of profitability with median worldwide gross of ${result.median_worldwide:.0f}M."
    elif result.prob_profit >= 0.45:
        decision = "PROCEED WITH CAUTION"
        color = "orange"
        ceiling = float(np.percentile(result.worldwide_totals, 75))
        reasoning = (
            f"Mixed outlook — {result.prob_profit:.0%} chance of profit. "
            f"Consider reducing budget below ${result.median_worldwide * 0.5:.0f}M for better odds, "
            f"or lean into factors that push the 75th percentile (${ceiling:.0f}M worldwide)."
        )
    else:
        decision = "PASS"
        color = "red"
        reasoning = (
            f"High risk — only {result.prob_profit:.0%} chance of profit. "
            f"{result.prob_flop:.0%} chance of a flop (<50% of budget recovered). "
            f"The numbers don't justify a ${budget:.0f}M investment."
        )

    return {"decision": decision, "color": color, "reasoning": reasoning}
