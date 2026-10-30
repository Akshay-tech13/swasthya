"""Swasthya Symbol - landing page."""
import streamlit as st

import api
from i18n.strings import t
from ui.style import apply_style, lang_toggle, trend_figure
from ui.cards import apply_cards_style

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
apply_style()
apply_cards_style()
lg = st.session_state.lang

# st.dialog (new) or experimental_dialog (older Streamlit)
dialog = getattr(st, "dialog", None) or st.experimental_dialog
ROLES = ["health_officer", "inspector", "public"]


def role_form(key, demo_note=False):
    role = st.selectbox(t("role", lg), ROLES, key=key, format_func=lambda r: t("role_" + r, lg))
    if demo_note:
        st.caption(t("demo_only", lg))
    if st.button(t("continue", lg), key=key + "_go"):
        st.session_state.role = role  # save role, no password
        st.switch_page("pages/1_Dashboard.py")


@dialog(t("sign_in", lg))
def sign_in_dialog():
    role_form("dlg_in")


@dialog(t("sign_up", lg))
def sign_up_dialog():
    role_form("dlg_up", demo_note=True)


# Top row: language toggle (left), Sign in / Sign up (right)
left, _, b1, b2 = st.columns([2, 4, 1, 1])
with left:
    lang_toggle("land")
if b1.button(t("sign_in", lg), key="btn_in"):
    sign_in_dialog()
if b2.button(t("sign_up", lg), key="btn_up"):
    sign_up_dialog()

# Main: project card (left) + chart card (right)
col_l, col_r = st.columns(2)
with col_l:
    st.markdown('<div class="big-symbol">⚕️</div>', unsafe_allow_html=True)
    st.title(t("title", lg))
    with st.container(border=True):
        for k in ("about_l1", "about_l2", "about_l3", "about_l4", "about_l5"):
            st.markdown("• " + t(k, lg))
with col_r:
    with st.container(border=True):
        st.subheader(t("trend", lg))
        try:
            st.plotly_chart(trend_figure(api.get_trends("S1", "health_officer")))
        except Exception as e:
            st.warning(f"Chart unavailable: {e}")

if st.button(t("open_dashboard", lg), key="open_dash"):
    st.switch_page("pages/1_Dashboard.py")
