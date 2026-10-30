"""api.py: the ONLY file the frontend imports from. Shapes follow SPEC section 5.

The dashboard is shown "as of" DEMO_WEEK, so the S1 outbreak is visible.
The public role sees districts (ids like "D:North District"), not site names.
"""

from ui.cards import apply_cards_style

import copy

import numpy as np
import pandas as pd

from data.generator import generate_data
from core.detect import detect
from core.explain import explain
from core.actions import recommend
from core.quality import completeness
from core.privacy import NOTICE, suppress, site_is_hidden, apply_role_view
from core.backtest import run_backtest
from ai.summarize import summarize, ACTION_HI, ROLE_HI

DEMO_WEEK = 40
SIGNALS = ["clinic_visits", "absence", "environment"]
RANK = {"Normal": 0, "Watch": 1, "High": 2}
VISIBLE_SIGNALS = {"health_officer": SIGNALS, "inspector": ["absence", "environment"], "public": ["environment"]}
NOTICE_HI = "केवल समूह स्तर का डेटा। किसी व्यक्ति के रोज़गार या अनुशासन के फ़ैसले के लिए नहीं।"

_cache = {}  # data is built once and reused, so pages stay fast


def _load():
    if "df" not in _cache:
        df = generate_data()
        scores = detect(df)
        _cache["df"] = df
        _cache["scores"] = scores
        _cache["idx"] = scores.set_index(["site_id", "week"])
    return _cache["df"], _cache["scores"]


def _sites_of(site_id):
    """A real site id gives [site_id]; a district id ("D:North District") gives its sites."""
    df, _ = _load()
    if site_id.startswith("D:"):
        return sorted(df[df["district"] == site_id[2:]]["site_id"].unique())
    return [site_id]


def _risk_at(site_id, week=DEMO_WEEK):
    """(risk or None, level) for one site at one week."""
    _load()
    row = _cache["idx"].loc[(site_id, week)]
    risk = None if pd.isna(row["risk_score"]) else float(row["risk_score"])
    return risk, row["level"]


def _name(site_id, role):
    df, _ = _load()
    if site_id.startswith("D:"):
        return site_id[2:]
    row = df[df["site_id"] == site_id].iloc[0]
    return row["district"] if role == "public" else row["site_name"]


def _completeness_for(ids):
    df, _ = _load()
    sub = df[df["site_id"].isin(ids)].copy()
    sub["site_id"] = "X"  # treat the group as one site
    return completeness(sub, "X")


def get_sites(role, sector=None):
    df, _ = _load()
    meta = df[["site_id", "site_name", "sector", "district"]].drop_duplicates()
    if sector:
        meta = meta[meta["sector"] == sector]
    rows = []

    if role == "public":  # district level only, no site names
        for district, grp in meta.groupby("district"):
            ids = list(grp["site_id"])
            shown = [i for i in ids if not site_is_hidden(df, i)]
            risks = [_risk_at(i) for i in shown]
            best_risk = max((r for r, _ in risks if r is not None), default=None)
            level = max((lv for _, lv in risks), key=lambda x: RANK[x], default="Normal")
            sectors = grp["sector"].unique()
            rows.append({
                "site_id": "D:" + district, "site_name": district,
                "sector": sectors[0] if len(sectors) == 1 else "mixed", "district": district,
                "risk_score": None if best_risk is None else int(round(best_risk)),
                "level": level, "completeness_pct": _completeness_for(ids)["pct"],
            })
    else:
        for r in meta.itertuples():
            risk, level = _risk_at(r.site_id)
            if site_is_hidden(df, r.site_id):  # small-cell rule: hide the score
                risk, level = None, "Normal"
            rows.append({
                "site_id": r.site_id, "site_name": r.site_name, "sector": r.sector, "district": r.district,
                "risk_score": None if risk is None else int(round(risk)),
                "level": level, "completeness_pct": _completeness_for([r.site_id])["pct"],
            })

    rows.sort(key=lambda x: -1 if x["risk_score"] is None else -x["risk_score"])
    return rows


def get_trends(site_id, role):
    df, _ = _load()
    sub = df[df["site_id"].isin(_sites_of(site_id))]
    view = apply_role_view(suppress(sub), role)  # small counts hidden, then role view
    wide = view.groupby(["week", "signal"])["value"].mean().unstack()
    wide = wide.reindex(index=range(1, 53), columns=SIGNALS)  # missing signals stay NaN
    wide.index.name = "week"
    wide.columns.name = None
    return wide.reset_index()


def get_alert(site_id, role, lang="en"):
    key = ("alert", site_id, role, lang)
    if key in _cache:
        return copy.deepcopy(_cache[key])
    df, scores = _load()
    candidates = [i for i in _sites_of(site_id) if not site_is_hidden(df, i)]
    if not candidates:
        return None
    best = max(candidates, key=lambda i: _risk_at(i)[0] or 0)
    risk, level = _risk_at(best)
    if risk is None or level == "Normal":
        _cache[key] = None
        return None

    s = scores[(scores["site_id"] == best) & (scores["week"] <= DEMO_WEEK)]
    high = s[s["level"] == "High"]
    week = int(high["week"].min()) if len(high) else DEMO_WEEK  # week the alert fired

    exp = explain(best, DEMO_WEEK, scores, df)
    keep = VISIBLE_SIGNALS.get(role, ["environment"])
    pairs = [(c, e) for c, e in zip(exp["contributing_signals"], exp["evidence"]) if c["signal"] in keep]
    alert = {
        "site_id": site_id, "week": week, "level": level, "risk_score": int(round(risk)),
        "contributing_signals": [c for c, _ in pairs], "evidence": [e for _, e in pairs],
        "assumptions": exp["assumptions"],
    }
    alert.update(recommend(alert))
    alert["summary"] = summarize({**alert, "site_name": _name(site_id, role)}, lang)
    if lang == "hi":
        alert["action"] = ACTION_HI.get(alert["action"], alert["action"])
        alert["responsible_role"] = ROLE_HI.get(alert["responsible_role"], alert["responsible_role"])
    _cache[key] = alert
    return copy.deepcopy(alert)


def get_backtest():
    if "backtest" not in _cache:
        _cache["backtest"] = run_backtest()
    return dict(_cache["backtest"])


def get_completeness(site_id):
    return _completeness_for(_sites_of(site_id))


def what_if(site_id, dust_delta, heat_delta):
    """Add dust_delta + heat_delta to the environment index for the last 3 weeks, re-run detection."""
    df, _ = _load()
    ids = [i for i in _sites_of(site_id) if not site_is_hidden(df, i)]
    if not ids:
        return {"new_risk_score": None, "new_level": "Normal"}
    sub = df[df["site_id"].isin(ids)].copy()
    mask = (sub["signal"] == "environment") & sub["week"].between(DEMO_WEEK - 2, DEMO_WEEK)
    sub.loc[mask, "value"] = (sub.loc[mask, "value"] + float(dust_delta) + float(heat_delta)).clip(0, 100)
    now = detect(sub)
    now = now[(now["week"] == DEMO_WEEK)].dropna(subset=["risk_score"])
    if now.empty:
        return {"new_risk_score": None, "new_level": "Normal"}
    top = now.sort_values("risk_score", ascending=False).iloc[0]
    return {"new_risk_score": int(round(top["risk_score"])), "new_level": top["level"]}


def export_report(site_id, role, lang="en"):
    hi = lang == "hi"
    L = {
        "title": "संकेत: अलर्ट रिपोर्ट" if hi else "Sanket: Alert report",
        "site": "साइट" if hi else "Site", "role": "भूमिका" if hi else "Role",
        "asof": "सप्ताह" if hi else "As of week", "level": "स्तर" if hi else "Level",
        "risk": "जोखिम स्कोर" if hi else "Risk score", "why": "यह अलर्ट क्यों" if hi else "Why this alert",
        "action": "सुझाया गया कदम" if hi else "Recommended action", "owner": "ज़िम्मेदार" if hi else "Owner",
        "summary": "सारांश" if hi else "Summary", "data": "डेटा पूर्णता" if hi else "Data completeness",
        "none": "इस साइट के लिए कोई अलर्ट नहीं।" if hi else "No active alert for this site.",
        "assume": "मान्यताएँ" if hi else "Assumptions",
    }
    alert = get_alert(site_id, role, lang)
    comp = get_completeness(site_id)
    lines = [f"# {L['title']}", "",
             f"- **{L['site']}:** {_name(site_id, role)}", f"- **{L['role']}:** {role}",
             f"- **{L['asof']}:** {DEMO_WEEK}",
             f"- **{L['data']}:** {comp['pct']}% ({comp['badge']})", ""]
    if alert is None:
        lines += [L["none"], ""]
    else:
        lines += [f"- **{L['level']}:** {alert['level']}", f"- **{L['risk']}:** {alert['risk_score']}", "",
                  f"## {L['why']}"] + [f"- {e}" for e in alert["evidence"]] + [
                  "", f"## {L['action']}", f"{alert['action']}", f"**{L['owner']}:** {alert['responsible_role']}", "",
                  f"## {L['summary']}", alert["summary"], "",
                  f"## {L['assume']}"] + [f"- {a}" for a in alert["assumptions"]] + [""]
    lines += ["---", NOTICE_HI if hi else NOTICE]
    return "\n".join(lines)


if __name__ == "__main__":
    sites = get_sites("health_officer")
    for s in sites:
        print(s)
    print("\nInspector first row:", get_sites("inspector")[0]["site_name"])
    print("Public rows:", [(s["site_name"], s["level"], s["risk_score"]) for s in get_sites("public")])
    print("\nTrends head:\n", get_trends("S1", "health_officer").iloc[[0, 39, 51]])
    print("Public trends NaN cols:", get_trends("S1", "public")[["clinic_visits", "absence"]].isna().all().tolist())
    a = get_alert("S1", "health_officer", "en")
    print("\nAlert:", {k: a[k] for k in ["site_id", "week", "level", "risk_score", "action", "responsible_role"]})
    print("Hidden site alert (S4):", get_alert("S4", "health_officer"))
    print("Completeness S7:", get_completeness("S7"))
    print("What-if S1 -30/-10:", what_if("S1", -30, -10), "| 0/0:", what_if("S1", 0, 0))
    print("Backtest:", get_backtest())
    print("\n" + export_report("S1", "health_officer", "en"))
