"""Simulated weekly data for Sanket. All data is FAKE and aggregated.

generate_data() -> DataFrame with columns:
week, site_id, site_name, sector, district, signal, value, headcount
"""
import numpy as np
import pandas as pd

WEEKS = 52
SIGNALS = ["clinic_visits", "absence", "environment"]

# site_id, name, sector, district, headcount, clinic mean, absence mean, environment mean
SITES = [
    ("S1", "Quarry A", "quarry", "North District", 80, 10, 18, 38),
    ("S2", "Quarry B", "quarry", "North District", 60, 11, 16, 40),
    ("S3", "Kiln C", "construction", "East District", 70, 9, 15, 35),
    ("S4", "Site D", "construction", "East District", 12, 1.5, 3, 33),  # tiny site, tests suppression
    ("S5", "Farm E", "farm", "South District", 90, 12, 20, 36),
    ("S6", "Farm F", "farm", "South District", 75, 10, 17, 34),
    ("S7", "Waste G", "waste", "West District", 50, 9, 14, 42),
    ("S8", "Mill H", "textile", "West District", 100, 14, 24, 39),
]

# Ground truth. "real" = a true event the system should catch.
# end_week = last week the event is still going (used by the back-test).
EVENTS = [
    {"site_id": "S1", "type": "outbreak", "start_week": 30, "peak_week": 40, "end_week": 46, "real": True},
    {"site_id": "S5", "type": "heat", "start_week": 20, "peak_week": 28, "end_week": 52, "real": True},
    {"site_id": "S7", "type": "data_gap", "start_week": 10, "peak_week": 14, "end_week": 14, "real": False},
    {"site_id": "S2", "type": "noise_spike", "start_week": 15, "peak_week": 15, "end_week": 15, "real": False},
]


def _ramp(week, start, peak):
    """0 before start, goes up to 1 at peak."""
    if week < start:
        return 0.0
    if week >= peak:
        return 1.0
    return (week - start + 1) / (peak - start + 1)


def generate_data(seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for site_id, name, sector, district, headcount, c_mean, a_mean, e_mean in SITES:
        for week in range(1, WEEKS + 1):
            clinic = rng.poisson(c_mean)
            absence = rng.poisson(a_mean)
            env = rng.normal(e_mean, 2.5)

            if site_id == "S1":  # outbreak: weeks 30-40, then slowly fades
                if 30 <= week <= 40:
                    r = _ramp(week, 30, 40)
                elif week > 40:
                    r = max(0.0, 1 - (week - 40) / 6)
                else:
                    r = 0.0
                clinic = rng.poisson(c_mean * (1 + 1.5 * r))
                absence = rng.poisson(a_mean * (1 + 0.5 * r))
                env = env + 9 * r

            if site_id == "S5":  # heat ramp weeks 20-28, then stays high
                r = _ramp(week, 20, 28)
                r_clinic = _ramp(week, 22, 28)
                env = e_mean + (88 - e_mean) * r + rng.normal(0, 2.5)
                clinic = rng.poisson(c_mean * (1 + 0.8 * r_clinic))
                absence = rng.poisson(a_mean * (1 + 0.25 * r_clinic))

            if site_id == "S2" and week == 15:  # one noisy spike, NOT a real outbreak
                clinic = clinic * 4

            if site_id == "S4":  # very small counts
                clinic = min(clinic, 4)

            env = float(np.clip(env, 0, 100))
            values = {"clinic_visits": float(clinic), "absence": float(absence), "environment": env}

            if site_id == "S7" and 10 <= week <= 14:  # data gap
                values = {k: np.nan for k in values}

            for signal in SIGNALS:
                rows.append((week, site_id, name, sector, district, signal, values[signal], headcount))

    df = pd.DataFrame(
        rows,
        columns=["week", "site_id", "site_name", "sector", "district", "signal", "value", "headcount"],
    )
    df["week"] = df["week"].astype(int)
    df["headcount"] = df["headcount"].astype(int)
    return df


if __name__ == "__main__":
    data = generate_data()
    print("shape:", data.shape)
    print("NaN count per site:")
    print(data[data["value"].isna()].groupby("site_id").size())
    s1 = data[(data.site_id == "S1") & (data.signal == "clinic_visits")]
    print("S1 clinic mean weeks 1-12 :", round(s1[s1.week <= 12]["value"].mean(), 1))
    print("S1 clinic mean weeks 38-40:", round(s1[s1.week.between(38, 40)]["value"].mean(), 1))
    print("Same seed gives same data:", data.equals(generate_data()))
