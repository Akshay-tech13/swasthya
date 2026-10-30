"""Small-cell suppression and role views (SPEC section 8)."""
import numpy as np

NOTICE = "Aggregated data only. Not for individual employment or disciplinary use."
COUNT_SIGNALS = ["clinic_visits", "absence"]


def suppress(df, k=5):
    """Any count below k becomes NaN (shown as '<5' on screen). Returns a copy."""
    out = df.copy()
    mask = out["signal"].isin(COUNT_SIGNALS) & (out["value"] < k)
    out.loc[mask, "value"] = np.nan
    return out


def site_is_hidden(df, site_id, k=5):
    """True if more than half of the site's weekly clinic counts are below k."""
    sub = df[(df["site_id"] == site_id) & (df["signal"] == "clinic_visits")]["value"].dropna()
    if len(sub) == 0:
        return False
    return bool((sub < k).sum() > len(sub) / 2)


def apply_role_view(df, role):
    """health_officer: all. inspector: no clinic values. public: environment only, no site names."""
    out = df.copy()
    if role == "health_officer":
        return out
    if role == "inspector":
        return out[out["signal"] != "clinic_visits"].copy()
    # public (and any unknown role gets the safest view)
    out = out[out["signal"] == "environment"].copy()
    out["site_name"] = out["district"]
    return out


if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so imports work from any folder
    from data.generator import generate_data
    data = generate_data()
    print("S4 hidden:", site_is_hidden(data, "S4"), "| S1 hidden:", site_is_hidden(data, "S1"))
    sup = suppress(data)
    print("values hidden by suppression:", int(sup["value"].isna().sum() - data["value"].isna().sum()))
    print("inspector signals:", apply_role_view(data, "inspector")["signal"].unique().tolist())
    pub = apply_role_view(data, "public")
    print("public signals:", pub["signal"].unique().tolist(), "| names:", pub["site_name"].unique().tolist())
