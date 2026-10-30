"""ui/charts.py: a cleaner trend chart (trend_figure_v2) and a tidy data table (pretty_trends).

trend_figure_v2 fixes three things in the old chart:
  1. Signals hidden for the role (all NaN) no longer appear in the legend.
  2. Every signal is shown as an index where the first-12-weeks baseline = 100, so three signals with
     different units share one honest axis and small noise is not zoomed into big swings.
  3. Hover shows the real raw value; missing weeks stay as gaps instead of being joined by a line.
"""
import pandas as pd
import plotly.graph_objects as go

SIGNALS = [
    ("clinic_visits", "Clinic visits", "क्लिनिक विज़िट", "#6D5BD0"),
    ("absence", "Absence", "अनुपस्थिति", "#E08A00"),
    ("environment", "Dust and heat", "धूल और गर्मी", "#0F8A6B"),
]


def trend_figure_v2(df, alert_week=None, lang="en", normalize=True, height=380):
    """df = api.get_trends(...). alert_week = api alert["week"] (optional)."""
    hi = lang == "hi"
    fig = go.Figure()
    ymax = 100.0
    shown = 0

    for col, en, hi_label, color in SIGNALS:
        if col not in df.columns:
            continue
        raw = pd.to_numeric(df[col], errors="coerce")
        if raw.notna().sum() == 0:
            continue  # hidden for this role: no empty legend entry
        y = raw
        if normalize:
            base = raw.iloc[:12].mean()
            if pd.isna(base) or base <= 0:
                continue
            y = raw / base * 100.0
        label = hi_label if hi else en
        fig.add_trace(go.Scatter(
            x=df["week"], y=y, mode="lines", name=label, line=dict(color=color, width=2.5),
            connectgaps=False, customdata=raw,
            hovertemplate=label + ": %{y:.0f} (raw %{customdata:.1f})<extra></extra>" if normalize
            else label + ": %{y:.1f}<extra></extra>",
        ))
        shown += 1
        if y.notna().any():
            ymax = max(ymax, float(y.max()))

    if normalize and shown:
        fig.add_hline(y=100, line_dash="dot", line_color="#9CA3AF",
                      annotation_text="सामान्य = 100" if hi else "Normal = 100",
                      annotation_position="bottom right", annotation_font_color="#6B7280")
    if alert_week:
        fig.add_vline(x=alert_week, line_dash="dash", line_color="#D64545",
                      annotation_text="अलर्ट" if hi else "alert fired",
                      annotation_font_color="#D64545")
    if shown == 0:
        fig.add_annotation(text="इस भूमिका के लिए डेटा उपलब्ध नहीं" if hi else "No data visible for this role",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#6B7280", size=14))

    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#374151"), hovermode="x unified",
        legend=dict(orientation="h", y=-0.22),
        xaxis=dict(title="सप्ताह" if hi else "Week", gridcolor="#E5E7EB", zeroline=False),
        yaxis=dict(title=("सूचकांक (सामान्य = 100)" if hi else "Index (normal = 100)") if normalize else None,
                   gridcolor="#E5E7EB", zeroline=False,
                   range=[0, max(150.0, ymax * 1.1)] if normalize else None, rangemode="tozero"),
    )
    return fig


def pretty_trends(df, lang="en"):
    """Tidy table for the white data box: nice column names, 1 decimal, hidden signals dropped."""
    hi = lang == "hi"
    keep = [c for c in ["week"] if c in df.columns]
    keep += [c for c, *_ in SIGNALS if c in df.columns and df[c].notna().any()]
    names = {c: (hi_label if hi else en) for c, en, hi_label, _ in SIGNALS}
    names["week"] = "सप्ताह" if hi else "Week"
    return df[keep].round(1).rename(columns=names)
