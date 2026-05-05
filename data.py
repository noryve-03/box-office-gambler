"""
Empirical priors for the Box Office Gambler simulation.

Numbers are calibrated against aggregate domestic + worldwide gross figures
from 2010-2024 wide-release theatrical data. Every distribution here is
sampled from in engine.run_simulation; nothing else uses these tables.
"""

# Total gross as a multiple of production budget, by genre.
GENRE_MULTIPLIERS = {
    "Action":    {"mean": 2.8, "std": 1.2},
    "Adventure": {"mean": 2.9, "std": 1.3},
    "Animation": {"mean": 3.0, "std": 1.0},
    "Comedy":    {"mean": 2.2, "std": 0.9},
    "Drama":     {"mean": 2.0, "std": 1.1},
    "Horror":    {"mean": 3.5, "std": 1.8},
    "Romance":   {"mean": 1.8, "std": 0.7},
    "Sci-Fi":    {"mean": 2.6, "std": 1.4},
    "Thriller":  {"mean": 2.4, "std": 1.0},
    "Fantasy":   {"mean": 2.7, "std": 1.3},
}

# Opening weekend as a fraction of total domestic gross.
# Higher means more front-loaded (horror); lower means longer legs (animation/drama).
LEGS_BY_GENRE = {
    "Action":    {"mean": 0.38, "std": 0.08},
    "Adventure": {"mean": 0.35, "std": 0.07},
    "Animation": {"mean": 0.28, "std": 0.06},
    "Comedy":    {"mean": 0.32, "std": 0.09},
    "Drama":     {"mean": 0.25, "std": 0.10},
    "Horror":    {"mean": 0.52, "std": 0.10},
    "Romance":   {"mean": 0.30, "std": 0.08},
    "Sci-Fi":    {"mean": 0.37, "std": 0.09},
    "Thriller":  {"mean": 0.40, "std": 0.08},
    "Fantasy":   {"mean": 0.34, "std": 0.07},
}

# Seasonal scalar on opening weekend. 1.0 = average release window.
MONTH_FACTORS = {
    "January": 0.65, "February": 0.72, "March":     0.85,
    "April":   0.80, "May":      1.25, "June":      1.30,
    "July":    1.35, "August":   0.90, "September": 0.60,
    "October": 0.75, "November": 1.15, "December":  1.20,
}

# Star-power tier -> additive opening-weekend boost in $M.
STAR_POWER = {
    "Unknown / Indie Cast":    {"boost_mean": 0,  "boost_std": 2},
    "Rising Star":             {"boost_mean": 8,  "boost_std": 5},
    "A-List":                  {"boost_mean": 20, "boost_std": 10},
    "Mega Star (top 10 draw)": {"boost_mean": 35, "boost_std": 15},
}

# Multiplier on overall gross by IP/franchise status.
FRANCHISE_BOOST = {
    "Original IP":               {"mult_mean": 1.0, "mult_std": 0.1},
    "Sequel":                    {"mult_mean": 1.3, "mult_std": 0.2},
    "Established Franchise (3+)":{"mult_mean": 1.6, "mult_std": 0.3},
    "Reboot / Remake":           {"mult_mean": 1.1, "mult_std": 0.2},
}

# International gross as a multiple of domestic gross, by genre.
# Comedies and romances notoriously under-perform overseas; tentpole genres travel.
INTL_MULTIPLIER = {
    "Action":    {"mean": 1.6, "std": 0.5},
    "Adventure": {"mean": 1.7, "std": 0.5},
    "Animation": {"mean": 1.4, "std": 0.4},
    "Comedy":    {"mean": 0.7, "std": 0.3},
    "Drama":     {"mean": 0.9, "std": 0.4},
    "Horror":    {"mean": 1.0, "std": 0.4},
    "Romance":   {"mean": 0.6, "std": 0.3},
    "Sci-Fi":    {"mean": 1.5, "std": 0.5},
    "Thriller":  {"mean": 1.1, "std": 0.4},
    "Fantasy":   {"mean": 1.5, "std": 0.5},
}

GENRES = list(GENRE_MULTIPLIERS.keys())
MONTHS = list(MONTH_FACTORS.keys())
STAR_TIERS = list(STAR_POWER.keys())
FRANCHISE_TYPES = list(FRANCHISE_BOOST.keys())
