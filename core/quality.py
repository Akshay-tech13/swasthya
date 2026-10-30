"""Data completeness and missing-data helper (SPEC section 10)."""
import pandas as pd


def completeness(df, site_id):
    """Returns {"pct": float, "missing_weeks": [int], "badge": "good"|"partial"|"poor"}."""
    sub = df[df["site_id"] == site_id]
    if len(sub) == 0:
        return {"pct": 0.0, "missing_weeks": [], "badge": "poor"}
    pct = round(100 * float(sub["value"].notna().mean()), 1)
    missing_weeks = sorted(int(w) for w in sub[sub["value"].isna()]["week"].unique())
    if pct >= 95:
        badge = "good"
    elif pct >= 80:
        badge = "partial"
    else:
        badge = "poor"
    return {"pct": pct, "missing_weeks": missing_weeks, "badge": badge}


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so imports work from any folder
    from data.generator import generate_data
    data = generate_data()
    for sid in ["S1", "S7"]:
        print(sid, completeness(data, sid))
