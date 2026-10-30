"""ui/cards.py: white card boxes, KPI tiles, data table box and privacy bar.

Add-on for ui/style.py. It does NOT replace it: call apply_cards_style() right after apply_style().
"""
import html

import streamlit as st

LABELS = {
    "high": ("High risk", "उच्च जोखिम"),
    "watch": ("Watch", "निगरानी"),
    "complete": ("Data completeness", "डेटा पूर्णता"),
    "week": ("As of week", "सप्ताह तक"),
    "sites": ("sites", "साइटें"),
    "districts": ("districts", "ज़िले"),
    "levels": ("Normal below 40, Watch 40-69, High 70+", "सामान्य 40 से कम, निगरानी 40-69, उच्च 70+"),
    "download": ("Download CSV", "CSV डाउनलोड करें"),
    "no_data": ("No data to show.", "दिखाने के लिए डेटा नहीं है।"),
}

CSS = """
.block-container{padding-top:1.5rem;padding-left:2rem;padding-right:2rem;max-width:1600px}

div[data-testid="stVerticalBlockBorderWrapper"],
div[class*="st-key-card_"]{
  background:#FFFFFF !important;
  border:1px solid rgba(15,118,110,.18) !important;
  border-radius:16px !important;
  box-shadow:0 6px 18px rgba(15,60,55,.12) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] div[class*="st-key-card_"]{
  background:transparent !important;border:none !important;box-shadow:none !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] :is(h1,h2,h3,h4),
div[class*="st-key-card_"] :is(h1,h2,h3,h4){color:#134E4A !important}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p,
div[class*="st-key-card_"] [data-testid="stMarkdownContainer"] p{color:#1F2937}

div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button,
div[class*="st-key-card_"] .stButton > button{
  background:#F1F7F5 !important;border:1px solid #CFE3DE !important;color:#1F2937 !important}
div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover,
div[class*="st-key-card_"] .stButton > button:hover{
  border-color:#0F766E !important;color:#0F766E !important}

.kpi{background:#FFFFFF;border:1px solid rgba(15,118,110,.14);border-radius:14px;
  padding:.8rem 1rem;box-shadow:0 4px 14px rgba(15,60,55,.10);height:100%}
.kpi-label{font-size:.8rem;color:#4B5563;font-weight:500}
.kpi-value{font-size:1.9rem;font-weight:700;line-height:1.25}
.kpi-hint{font-size:.75rem;color:#6B7280}

.notice-bar{background:#FFFFFF;border-left:5px solid #0F766E;border-radius:10px;
  padding:.6rem 1rem;margin-top:1rem;font-size:.85rem;color:#1F2937;
  box-shadow:0 4px 14px rgba(15,60,55,.08)}
"""


def _l(key, lang):
    en, hi = LABELS[key]
    return hi if lang == "hi" else en


def apply_cards_style():
    """Call once per page, right after apply_style()."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def card(name):
    """A white box. Use as: with card("sites"): ...  The name must be unique on the page."""
    try:
        return st.container(border=True, key=f"card_{name}")
    except TypeError:  # older Streamlit has no key=
        return st.container(border=True)


def kpi_row(rows, as_of_week, lang="en", role="health_officer"):
    """Four white tiles above the main panels. rows = api.get_sites(role, sector)."""
    high = sum(1 for r in rows if r.get("level") == "High")
    watch = sum(1 for r in rows if r.get("level") == "Watch")
    pcts = [r["completeness_pct"] for r in rows if r.get("completeness_pct") is not None]
    avg = round(sum(pcts) / len(pcts)) if pcts else 0
    unit = _l("districts" if role == "public" else "sites", lang)
    tiles = [
        (_l("high", lang), str(high), unit, "#C62828"),
        (_l("watch", lang), str(watch), unit, "#B7791F"),
        (_l("complete", lang), f"{avg}%", "", "#0F766E"),
        (_l("week", lang), str(as_of_week), _l("levels", lang), "#1F2937"),
    ]
    for col, (label, value, hint, color) in zip(st.columns(len(tiles)), tiles):
        col.markdown(
            f'<div class="kpi"><div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value" style="color:{color}">{html.escape(value)}</div>'
            f'<div class="kpi-hint">{html.escape(hint)}</div></div>',
            unsafe_allow_html=True,
        )


def data_card(df, title, lang="en", filename="swasthya_symbol_data.csv", name="data"):
    """The data table in a white box, with a CSV download."""
    with card(name):
        st.subheader(title)
        if df is None or len(df) == 0:
            st.write(_l("no_data", lang))
            return
        st.dataframe(df, hide_index=True)
        st.download_button(
            _l("download", lang), df.to_csv(index=False).encode("utf-8"),
            file_name=filename, mime="text/csv", key=f"dl_{name}",
        )


def notice_bar(lang="en"):
    """White privacy strip. Show it at the bottom of every page."""
    import api  # imported here so ui/ never depends on api at import time

    text = getattr(api, "NOTICE_HI", "") if lang == "hi" else getattr(api, "NOTICE", "")
    if not text:
        text = ("केवल समूह स्तर का डेटा। किसी व्यक्ति के रोज़गार या अनुशासन के फ़ैसले के लिए नहीं।" if lang == "hi"
                else "Aggregated data only. Not for individual employment or disciplinary use.")
    st.markdown(f'<div class="notice-bar">{html.escape(text)}</div>', unsafe_allow_html=True)
