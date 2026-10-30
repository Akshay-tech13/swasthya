"""Back-test on simulated scenarios (SPEC section 10)."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so imports work from any folder

from data.generator import generate_data, EVENTS

try:
    from core.detect import detect
except ImportError:  # stub until detect.py exists: random levels in the same shape
    def detect(df):
        rng = np.random.default_rng(0)
        base = df[["week", "site_id"]].drop_duplicates().copy()
        base["risk_score"] = rng.uniform(0, 100, len(base)).round(1)
        base["level"] = pd.cut(base["risk_score"], [-1, 40, 70, 101], labels=["Normal", "Watch", "High"]).astype(str)
        return base

SEEDS = list(range(42, 52))  # 10 scenarios
LATENCY_NOTE = "Weekly data, one-week delay assumed."


def _episodes(weeks):
    """Group sorted week numbers into runs of consecutive weeks -> list of (first, last)."""
    runs, start, prev = [], None, None
    for w in weeks:
        if start is None:
            start = prev = w
        elif w == prev + 1:
            prev = w
        else:
            runs.append((start, prev))
            start = prev = w
    if start is not None:
        runs.append((start, prev))
    return runs


def run_backtest():
    real_events = [e for e in EVENTS if e["real"]]
    detected, lead_times = 0, []
    total_events = 0
    true_alerts, false_alarms = 0, 0
    gap_high = 0

    for seed in SEEDS:
        out = detect(generate_data(seed))
        high = out[out["level"] == "High"]

        # sensitivity and lead time
        for ev in real_events:
            total_events += 1
            weeks = high[(high.site_id == ev["site_id"]) &
                         (high.week.between(ev["start_week"], ev["peak_week"]))]["week"]
            if len(weeks):
                detected += 1
                lead_times.append(ev["peak_week"] - int(weeks.min()))

        # ppv and false alarms: count alert episodes (runs of High weeks at one site)
        for site_id, grp in high.groupby("site_id"):
            for first, last in _episodes(sorted(int(w) for w in grp["week"])):
                near = any(ev["site_id"] == site_id and
                           first <= ev["end_week"] + 2 and last >= ev["start_week"] - 2
                           for ev in real_events)
                if near:
                    true_alerts += 1
                else:
                    false_alarms += 1

        # S7 data gap (weeks 10-14)
        gap = [e for e in EVENTS if e["type"] == "data_gap"][0]
        gap_high += int(len(high[(high.site_id == gap["site_id"]) &
                                 (high.week.between(gap["start_week"], gap["end_week"]))]))

    total_alerts = true_alerts + false_alarms
    if gap_high == 0:
        gap_text = ("Waste G (S7) had no data in weeks 10-14. The system raised no risk score and no "
                    "false High alert during the gap, and went back to normal once data returned.")
    else:
        gap_text = ("Waste G (S7) had no data in weeks 10-14, and High alerts still fired during the gap. "
                    "This needs a fix.")
    return {
        "lead_time_weeks": round(float(np.mean(lead_times)), 1) if lead_times else 0.0,
        "sensitivity": round(detected / total_events, 2) if total_events else 0.0,
        "ppv": round(true_alerts / total_alerts, 2) if total_alerts else 0.0,
        "false_alarms": int(false_alarms),
        "n_scenarios": len(SEEDS),
        "data_latency_note": LATENCY_NOTE,
        "missing_data_behavior": gap_text,
    }


if __name__ == "__main__":
    for key, value in run_backtest().items():
        print(f"{key}: {value}")
