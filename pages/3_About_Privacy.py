"""About + privacy rules + common health problems by occupation."""
import streamlit as st

from i18n.strings import SECTOR_INFO, t
from ui.style import apply_style, privacy_notice, topbar

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
apply_style()
lg = st.session_state.lang
topbar("About")
st.title(t("privacy_title", lg))

with st.container(border=True):
    for k in ("rule1", "rule2", "rule3", "rule4", "rule5"):
        st.markdown("• " + t(k, lg))

with st.container(border=True):
    st.subheader(t("sector_table", lg))
    rows = [{t("col_sector", lg): t("sector_" + s, lg), t("col_problems", lg): info[lg]}
            for s, info in SECTOR_INFO.items()]
    st.table(rows)
    st.markdown(f"**{t('no_diagnose', lg)}**")

privacy_notice()
