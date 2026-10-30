"""Plain-language alert summary. Uses the AI if possible, else a fixed template."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so imports work from any folder

from ai.client import ask_ai

SIGNAL_EN = {"clinic_visits": "clinic visits", "absence": "sickness absence", "environment": "heat and dust level"}
SIGNAL_HI = {"clinic_visits": "क्लिनिक में आने वाले मरीज़", "absence": "बीमारी की छुट्टियाँ",
             "environment": "गर्मी और धूल का स्तर"}
LEVEL_HI = {"Normal": "सामान्य", "Watch": "निगरानी", "High": "उच्च"}
ACTION_HI = {
    "Dust/heat control audit within 7 days": "7 दिन के अंदर धूल/गर्मी नियंत्रण की जाँच",
    "Targeted screening camp (chest and heat illness)": "चुने हुए समूह के लिए जाँच शिविर (छाती और गर्मी की बीमारी)",
    "Review working conditions and share data with inspector": "काम की स्थिति की समीक्षा और इंस्पेक्टर के साथ डेटा साझा करना",
    "Increase monitoring and review next week": "निगरानी बढ़ाएँ और अगले हफ़्ते दोबारा देखें",
    "No action needed": "कोई कदम ज़रूरी नहीं",
}
ROLE_HI = {
    "Factory inspector": "फैक्ट्री इंस्पेक्टर", "District health officer": "ज़िला स्वास्थ्य अधिकारी",
    "Labour inspector": "श्रम निरीक्षक", "Site supervisor": "साइट सुपरवाइज़र", "none": "कोई नहीं",
}


def _join(items, word):
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {word} " + items[-1]


def _template(alert, lang):
    site = alert.get("site_name") or alert.get("site_id", "")
    level = alert.get("level", "Normal")
    names = [s["signal"] for s in alert.get("contributing_signals", [])]
    action, role = alert.get("action", ""), alert.get("responsible_role", "")
    if lang == "hi":
        sig = _join([SIGNAL_HI.get(n, n) for n in names], "और") or "कोई संकेत नहीं"
        return (f"{site} में {sig} सामान्य से ज़्यादा हैं, इसलिए जोखिम स्तर {LEVEL_HI.get(level, level)} है। "
                f"यह किसी एक कर्मचारी के लिए नहीं, पूरे समूह के लिए चेतावनी है। "
                f"सुझाया गया कदम: {ACTION_HI.get(action, action)} ({ROLE_HI.get(role, role)})।")
    sig = _join([SIGNAL_EN.get(n, n) for n in names], "and") or "no signals"
    return (f"At {site}, {sig} are higher than normal, so the risk level is {level}. "
            f"This is a warning for the whole group, not about any one worker. "
            f"Suggested step: {action} (owner: {role}).")


def summarize(alert, lang="en"):
    """Short 3-sentence summary in English or Hindi. Never fails."""
    language = "Hindi (Devanagari script)" if lang == "hi" else "English"
    names = [s["signal"] for s in alert.get("contributing_signals", [])]
    prompt = (
        f"Write exactly 3 short sentences in simple plain words in {language}. "
        f"Site: {alert.get('site_name') or alert.get('site_id')}. Risk level: {alert.get('level')}. "
        f"Signals that rose: {', '.join(names) or 'none'}. Suggested action: {alert.get('action')} "
        f"(owner: {alert.get('responsible_role')}). "
        "Say which signals rose and what to do. Say this is a group-level warning. "
        "Do NOT give any medical diagnosis. Do not mention individual workers."
    )
    text = ask_ai(prompt)
    return text if text else _template(alert, lang)


if __name__ == "__main__":
    demo = {"site_id": "S1", "site_name": "Quarry A", "level": "High",
            "contributing_signals": [{"signal": "clinic_visits"}, {"signal": "environment"}],
            "action": "Dust/heat control audit within 7 days", "responsible_role": "Factory inspector"}
    print("AI_API_KEY set:", bool(os.environ.get("AI_API_KEY")))
    print("EN:", summarize(demo, "en"))
    print("HI:", summarize(demo, "hi"))
