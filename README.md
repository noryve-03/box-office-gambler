# Box Office Gambler

A Monte Carlo greenlight simulator for film production decisions.
Final project for CS 4580 — Automated Decision Systems.

The full project proposal is in [`proposal.pdf`](proposal.pdf).

## What it does

You describe a hypothetical movie — budget, genre, release month, star
tier, franchise status, MPAA rating — and the app runs thousands of
simulated financial outcomes against empirical priors calibrated to
2010-2024 box office data. The output is:

- A greenlight decision (`GREEN LIGHT` / `PROCEED WITH CAUTION` / `PASS`)
- Probability distributions over worldwide gross, opening weekend, and ROI
- Per-factor attributions explaining what helped or hurt the forecast
- Counterfactual sweeps over genre and release month

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501`.

## Layout

| File          | Purpose                                                   |
| ------------- | --------------------------------------------------------- |
| `data.py`     | Empirical priors (genre, month, star, franchise, intl).   |
| `engine.py`   | Monte Carlo engine, factor attribution, decision rule.    |
| `app.py`      | Streamlit UI: sidebar inputs, charts, counterfactuals.    |
| `Dockerfile`  | Container image for deployment.                           |

## Docker

```bash
docker build -t box-office-gambler .
docker run -p 8501:8501 box-office-gambler
```
