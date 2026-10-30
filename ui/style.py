"""Shared look + small UI helpers (style, top bar, badges, trend chart)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from i18n.strings import t

CSS = """
<style>
.stApp { background: linear-gradient(90deg, #47C8B0 0%, #F7FDB4 100%); }
/* cards = bordered containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.9);
    border-radius: 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.10);
    padding: 16px;
}
.stButton > button, .stDownloadButton > button { width: 100%; border-radius: 10px; }
.badge { display:inline-block; padding:2px 10px; border-radius:999px;
         color:#fff; font-weight:600; font-size:0.85rem; white-space:nowrap; }
.badge-normal { background:#2E9E5B; }
.badge-watch  { background:#F0A020; }
.badge-high   { background:#D64545; }
.badge-none   { background:#888; }
.big-symbol { font-size: 90px; line-height: 1; }
</style>
"""


def init_state():
    """Default session_state values."""
    st.session_state.setdefault("role", "public")
    st.session_state.setdefault("lang", "en")
    st.session_state.setdefault("site_id", None)
    st.session_state.setdefault("sector", None)


def apply_style():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)


def lang():
    return st.session_state.get("lang", "en")


def badge(level, text=None):
    """Return HTML for a coloured level badge (Normal/Watch/High)."""
    lv = str(level or "").lower()
    cls = {"normal": "badge-normal", "watch": "badge-watch", "high": "badge-high"}.get(lv, "badge-none")
    label = text if text is not None else (t("level_" + lv, lang()) if lv in ("normal", "watch", "high") else str(level or "-"))
    return f'<span class="badge {cls}">{label}</span>'


def privacy_notice():
    st.info("🔒 " + t("privacy_notice", lang()))


def _set_lang(code):
    st.session_state.lang = code


def lang_toggle(key_prefix="lt"):
    """Two small buttons: Hindi | English."""
    c1, c2 = st.columns(2)
    cur = lang()
    c1.button(t("lang_hi", "en"), key=f"{key_prefix}_hi", on_click=_set_lang, args=("hi",),
              type="primary" if cur == "hi" else "secondary")
    c2.button(t("lang_en", "en"), key=f"{key_prefix}_en", on_click=_set_lang, args=("en",),
              type="primary" if cur == "en" else "secondary")


def _role_changed():
    st.session_state.role = st.session_state.role_sel


def topbar(page_name):
    """Top bar for inner pages: brand, links, role, language, download (Dashboard only)."""
    lg = lang()
    roles = ["health_officer", "inspector", "public"]
    c = st.columns([2, 1, 1, 1, 1.7, 1.4, 1.6])
    c[0].markdown(f"### ⚕️ {t('app_name', lg)}")
    c[1].page_link("pages/1_Dashboard.py", label=t("nav_dashboard", lg))
    c[2].page_link("pages/2_Back-test.py", label=t("nav_backtest", lg))
    c[3].page_link("pages/3_About_Privacy.py", label=t("nav_about", lg))
    # keep widget value in sync with the saved role
    st.session_state["role_sel"] = st.session_state.role
    c[4].selectbox("role", roles, key="role_sel", on_change=_role_changed,
                   format_func=lambda r: t("role_" + r, lg), label_visibility="collapsed")
    with c[5]:
        lang_toggle("top")
    if page_name == "Dashboard":
        sid = st.session_state.get("site_id")
        data = ""
        if sid:
            try:
                import api  # data comes only from api.py
                data = api.export_report(sid, st.session_state.role, lg)
            except Exception:
                data = ""
        c[6].download_button(t("download_report", lg), data=data or "", file_name=f"swasthya_symbol_{sid}.md",
                             mime="text/markdown", disabled=not (sid and data))


def trend_figure(df, alert_week=None, height=380):
    """3-line trend chart. Handles NaN gaps and missing columns (public role)."""
    lg = lang()
    fig = go.Figure()
    df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    if df.empty:
        return fig
    xcol = next((c for c in df.columns if str(c).lower() in ("week", "date", "week_start")), None)
    x = df[xcol] if xcol else df.index

    # (keywords in column name, label key, colour)
    groups = [
        (("clinic",), "series_clinic", "#7B4FD6"),
        (("absen",), "series_absence", "#F28C28"),
        (("env", "dust", "heat"), "series_env", "#2E9E5B"),
    ]
    used = set()
    for words, label_key, colour in groups:
        cols = [c for c in df.columns if c != xcol and c not in used
                and any(w in str(c).lower() for w in words)]
        for i, col in enumerate(cols):
            used.add(col)
            y = pd.to_numeric(df[col], errors="coerce")  # NaN -> gap
            name = t(label_key, lg) if len(cols) == 1 else str(col)
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name, connectgaps=False,
                                     line=dict(color=colour, dash="solid" if i == 0 else "dot")))

    if alert_week is not None:
        fig.add_shape(type="line", x0=alert_week, x1=alert_week, y0=0, y1=1, yref="paper",
                      line=dict(color="#D64545", dash="dash", width=2))
        fig.add_annotation(x=alert_week, y=1, yref="paper", text=t("alert_fired", lg),
                           showarrow=False, yanchor="bottom", font=dict(color="#D64545"))
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", y=-0.2),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig
