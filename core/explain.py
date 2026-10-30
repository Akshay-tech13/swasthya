"""'Why this alert' (SPEC section 7)."""
import numpy as np

SIGNALS = ["clinic_visits", "absence", "environment"]
PRETTY = {"clinic_visits": "Clinic visits", "absence": "Sickness absence", "environment": "Heat and dust level"}
ASSUMPTIONS = ["Baseline = first 12 weeks", "EWMA lambda 0.25", "Data is simulated"]


def explain(site_id, week, scores_df, df):
    """Returns {contributing_signals, evidence, assumptions} for one site and week."""
    row = scores_df[(scores_df["site_id"] == site_id) & (scores_df["week"] == week)]
    site = df[df["site_id"] == site_id]
    contributing, evidence = [], []
    if len(row):
        row = row.iloc[0]
        found = []
        for sig in SIGNALS:
            score = row[sig]
            if np.isnan(score) or score <= 0:
                continue
            values = site[site["signal"] == sig].sort_values("week")
            base_mean = values[values["week"] <= 12]["value"].mean()
            upto = values[values["week"] <= week]
            recent = upto["value"].dropna().tail(3).mean()  # last 3 weeks with data
            change = round(float((recent - base_mean) / base_mean * 100), 1) if base_mean else 0.0
            weeks_above = 0  # weeks in a row above baseline, counting back from `week`
            for v in reversed(upto["value"].tolist()):
                if np.isnan(v) or v <= base_mean:
                    break
                weeks_above += 1
            found.append((score, {"signal": sig, "change_pct": change, "weeks": weeks_above}))
        found.sort(key=lambda x: -x[0])
        for _, item in found:
            contributing.append(item)
            evidence.append(f"{PRETTY[item['signal']]}: {item['change_pct']}% above normal "
                            f"(above baseline for {item['weeks']} weeks in a row).")
    return {"contributing_signals": contributing, "evidence": evidence, "assumptions": list(ASSUMPTIONS)}


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so imports work from any folder
    from data.generator import generate_data
    from core.detect import detect
    data = generate_data()
    scores = detect(data)
    result = explain("S1", 40, scores, data)
    for item in result["contributing_signals"]:
        print(item)
    print(*result["evidence"], sep="\n")
    print(result["assumptions"])
