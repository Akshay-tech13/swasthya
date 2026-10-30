"""EWMA detection and fused risk score (SPEC section 6)."""
import numpy as np
import pandas as pd

SIGNALS = ["clinic_visits", "absence", "environment"]
WEIGHTS = {"clinic_visits": 0.5, "absence": 0.25, "environment": 0.25}
LAMBDA = 0.25
BASELINE_WEEKS = 12


def _level(risk):
    if risk >= 70:
        return "High"
    if risk >= 40:
        return "Watch"
    return "Normal"


def _site_scores(site_df):
    """Signal scores (0..1) per week for one site. NaN = signal missing that week."""
    wide = site_df.pivot_table(index="week", columns="signal", values="value", aggfunc="mean", dropna=False)
    wide = wide.reindex(columns=SIGNALS).sort_index()
    scores = pd.DataFrame(index=wide.index, columns=SIGNALS, dtype=float)

    for sig in SIGNALS:
        base = wide.loc[wide.index <= BASELINE_WEEKS, sig].dropna()
        if len(base) == 0:
            continue  # no baseline: this signal stays NaN (treated as missing)
        mean = base.mean()
        std = base.std() if len(base) > 1 else 0.0
        if not std or np.isnan(std):
            std = 1.0
        ewma = mean
        for week, value in wide[sig].items():
            if np.isnan(value):
                continue  # carry EWMA forward, signal missing this week
            ewma = LAMBDA * value + (1 - LAMBDA) * ewma
            scores.loc[week, sig] = float(np.clip((ewma - mean) / (3 * std), 0, 1))
    return scores


def detect(df):
    """df = weekly_signals. Returns week, site_id, risk_score, level + one score column per signal."""
    out = []
    for site_id, site_df in df.groupby("site_id"):
        scores = _site_scores(site_df)
        for week, row in scores.iterrows():
            avail = {s: row[s] for s in SIGNALS if not np.isnan(row[s])}
            if not avail:
                risk, level = np.nan, "Normal"
            else:
                total_w = sum(WEIGHTS[s] for s in avail)
                risk = 100 * sum(WEIGHTS[s] * v for s, v in avail.items()) / total_w
                level = _level(risk)
                # alert-fatigue rule: High needs at least 2 strong signals
                strong = sum(1 for v in avail.values() if v >= 0.5)
                if level == "High" and strong < 2:
                    level = "Watch"
                risk = round(risk, 1)
            out.append({
                "week": int(week), "site_id": site_id, "risk_score": risk, "level": level,
                "clinic_visits": row["clinic_visits"], "absence": row["absence"],
                "environment": row["environment"],
            })
    return pd.DataFrame(out)


if __name__ == "__main__":
    # small made-up data: S1 rises from week 30
    rng = np.random.default_rng(1)
    rows = []
    for week in range(1, 41):
        rise = max(0, week - 29)
        vals = {"clinic_visits": 10 + rng.normal(0, 1) + 2 * rise,
                "absence": 15 + rng.normal(0, 1) + 1 * rise,
                "environment": 38 + rng.normal(0, 1) + 1.5 * rise}
        for sig, v in vals.items():
            rows.append((week, "S1", "Quarry A", "quarry", "North District", sig, v, 80))
    test_df = pd.DataFrame(rows, columns=["week", "site_id", "site_name", "sector", "district",
                                          "signal", "value", "headcount"])
    result = detect(test_df)
    print(result[result.week.isin([10, 29, 32, 35, 38, 40])].to_string(index=False))
