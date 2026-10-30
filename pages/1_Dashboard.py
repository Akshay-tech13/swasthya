"""Dashboard: sites | trend | why this alert + bottom cards."""
import streamlit as st 
from ui.cards import apply_cards_style

import api
from i18n.strings import t
from ui.style import apply_style, badge, privacy_notice, topbar, trend_figure

st.set_page_config(layout="wide", initial_sidebar_state="collapsed")
apply_style()
apply_cards_style()
lg = st.session_state.lang
role = st.session_state.role


def g(d, *keys, default=None):
    """First non-None value among keys of dict d."""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if d.get(k) is not None:
            return d[k]
    return default


def pick_site(sid):
    st.session_state.site_id = sid


# ---- load sites for the chosen sector, pick default site ----
keys = ["all", "farm", "quarry", "construction", "waste", "textile"]
choice = st.session_state.get("sector_radio", "all")
sector = None if choice == "all" else choice  # lowercase, None for All
st.session_state.sector = sector
sites = api.get_sites(role, sector) or []
ids = [g(s, "site_id", "id") for s in sites]
if st.session_state.site_id not in ids:
    st.session_state.site_id = ids[0] if ids else None  # first site by default
site_id = st.session_state.site_id
site = next((s for s in sites if g(s, "site_id", "id") == site_id), {})
site_name = g(site, "name", "site_name", default=site_id)

topbar("Dashboard")
st.radio("sector", keys, key="sector_radio", horizontal=True, label_visibility="collapsed",
         format_func=lambda k: t("sector_" + k, lg))

left, centre, right = st.columns([1, 2, 1.3])

# ---- LEFT: sites list ----
with left:
    with st.container(border=True):
        st.subheader(t("sites", lg))
        if not sites:
            st.write(t("no_sites", lg))
        for s in sites:
            sid = g(s, "site_id", "id")
            name = g(s, "name", "site_name", default=sid)
            risk = g(s, "risk_score")
            c1, c2 = st.columns([3, 2])
            c1.button(("● " if sid == site_id else "") + str(name), key=f"site_{sid}",
                      on_click=pick_site, args=(sid,))
            if risk is None:
                c2.caption(t("hidden_small", lg))
            else:
                c2.markdown(badge(g(s, "level", "risk_level"), f"{t('risk', lg)} {risk}"),
                            unsafe_allow_html=True)

# ---- data for centre + right ----
alert = api.get_alert(site_id, role, lg) if site_id else None
alert_week = g(alert, "alert_week", "week")

# ---- CENTRE: trend chart ----
with centre:
    with st.container(border=True):
        st.subheader(f"{t('trend', lg)}: {site_name}")
        if site_id:
            st.plotly_chart(trend_figure(api.get_trends(site_id, role), alert_week))

# ---- RIGHT: why this alert ----
with right:
    with st.container(border=True):
        st.subheader(t("why_alert", lg))
        if not alert:
            st.write(t("no_alert", lg))
        else:
            lvl = g(alert, "level", "risk_level")
            if lvl:
                st.markdown(badge(lvl), unsafe_allow_html=True)
            st.markdown(f"**{t('signals', lg)}**")
            for sg in g(alert, "signals", "contributing_signals", default=[]) or []:
                st.markdown(f"• {g(sg, 'signal')}: {g(sg, 'change_pct')}% ({g(sg, 'weeks')} {t('weeks', lg)})")
            st.markdown(f"**{t('evidence', lg)}**")
            for ev in g(alert, "evidence", default=[]) or []:
                st.markdown(f"• {ev}")
            with st.expander(t("assumptions", lg)):
                for a in g(alert, "assumptions", default=[]) or []:
                    st.markdown(f"• {a}")
            act = g(alert, "action", "recommended_action")
            resp = g(alert, "responsible_role")
            if isinstance(act, dict):
                resp = resp or g(act, "responsible_role")
                act = g(act, "action", "text")
            st.markdown(f"**{t('rec_action', lg)}**")
            st.write(act or "-")
            st.caption(f"{t('responsible', lg)}: {resp or '-'}")
            st.markdown(f"**{t('summary', lg)}**")
            st.write(g(alert, "summary", "plain_summary", "plain_language_summary", default="-"))

# ---- BOTTOM: 3 cards ----
b1, b2, b3 = st.columns(3)

with b1:
    with st.container(border=True):
        comp = api.get_completeness(site_id, role) if site_id else None
        val = g(comp, "pct", "percent", "score", "completeness")
        if val is not None and val <= 1:
            val = val * 100
        pct = f"{val:.0f}%" if val is not None else "-"
        st.subheader(f"{t('completeness', lg)}: {pct}")
        status = str(g(comp, "status", "level", default="")).lower()
        cls = {"good": "normal", "partial": "watch", "poor": "high"}.get(status, "none")
        label = t("completeness_" + status, lg) if status in ("good", "partial", "poor") else status or "-"
        st.markdown(badge(cls, label), unsafe_allow_html=True)
        mw = g(comp, "missing_weeks", default=[])
        mw = ", ".join(map(str, mw)) if isinstance(mw, (list, tuple)) else mw
        st.caption(f"{t('missing_weeks', lg)}: {mw or '-'}")

with b2:
    with st.container(border=True):
        st.subheader(t("what_if", lg))
        dust = st.slider(t("dust_delta", lg), -30, 50, 0, key="dust_delta")
        heat = st.slider(t("heat_delta", lg), -30, 50, 0, key="heat_delta")
        if site_id:
            try:
                res = api.what_if(site_id, role, dust, heat)
                st.metric(t("new_risk", lg), g(res, "new_risk_score", default="-"))
                st.markdown(badge(g(res, "new_level")), unsafe_allow_html=True)
            except Exception as e:
                st.warning(str(e))

with b3:
    with st.container(border=True):
        privacy_notice()
