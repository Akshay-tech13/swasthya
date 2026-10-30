"""Back-test results."""
import streamlit as st

import api
from i18n.strings import t
from ui.style import apply_style, privacy_notice, topbar

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
apply_style()
lg = st.session_state.lang
topbar("Back-test")
st.title(t("backtest_title", lg))

bt = api.get_backtest() or {}


def pct(v):
    """0.85 -> '85%' (also accepts 85)."""
    if v is None:
        return "-"
    return f"{v * 100:.0f}%" if v <= 1 else f"{v:.0f}%"


cards = [
    (t("lead_time", lg), bt.get("lead_time_weeks", "-")),
    (t("sensitivity", lg), pct(bt.get("sensitivity"))),
    (t("ppv", lg), pct(bt.get("ppv"))),
    (t("false_alarms", lg), bt.get("false_alarms", "-")),
]
for col, (label, value) in zip(st.columns(4), cards):
    with col:
        with st.container(border=True):
            st.metric(label, value)

st.info(f"**{t('n_scenarios', lg)}:** {bt.get('n_scenarios', '-')}")
st.info(f"**{t('latency_note', lg)}:** {bt.get('data_latency_note', '-')}")
st.info(f"**{t('missing_behavior', lg)}:** {bt.get('missing_data_behavior', '-')}")
st.caption(t("simulated_note", lg))
privacy_notice()
