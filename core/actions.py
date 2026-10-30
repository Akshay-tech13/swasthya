"""Recommended action and responsible role (SPEC section 7)."""

WATCH = ("Increase monitoring and review next week", "Site supervisor")
HIGH_BY_TOP = {
    "environment": ("Dust/heat control audit within 7 days", "Factory inspector"),
    "clinic_visits": ("Targeted screening camp (chest and heat illness)", "District health officer"),
    "absence": ("Review working conditions and share data with inspector", "Labour inspector"),
}
NORMAL = ("No action needed", "none")


def recommend(alert):
    """alert needs: level and contributing_signals (sorted, top contributor first)."""
    level = alert.get("level", "Normal")
    signals = alert.get("contributing_signals") or []
    if level == "High":
        top = signals[0]["signal"] if signals else None
        action, role = HIGH_BY_TOP.get(top, WATCH)
    elif level == "Watch":
        action, role = WATCH
    else:
        action, role = NORMAL
    return {"action": action, "responsible_role": role}


if __name__ == "__main__":
    for lvl, sig in [("High", "environment"), ("High", "clinic_visits"), ("High", "absence"),
                     ("Watch", "absence"), ("Normal", None)]:
        alert = {"level": lvl, "contributing_signals": [{"signal": sig}] if sig else []}
        print(lvl, sig, "->", recommend(alert))
