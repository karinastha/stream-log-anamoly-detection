"""Altair charts with in-chart annotations (peaks, averages, thresholds) that follow the active light/dark palette."""

import altair as alt
import pandas as pd

from . import theme


def _legend(p: dict) -> dict:
    return {"labelColor": p["muted"], "titleColor": p["muted"], "labelFontSize": 11}


def _style(chart: alt.TopLevelMixin, height: int) -> alt.TopLevelMixin:
    p = theme.palette()
    return (
        chart.properties(height=height, width="container")
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(gridColor=p["grid"], domainColor=p["border"], tickColor=p["border"], labelColor=p["muted"],
                        titleColor=p["muted"], labelFontSize=11, titleFontSize=11, titleFontWeight="normal")
        .configure_legend(orient="top", title=None, symbolType="stroke", **_legend(p))
    )


def _tip(*fields) -> list:
    return [alt.Tooltip("ts:T", title="Time (UTC)", format="%H:%M:%S"), *fields]


def throughput(series: pd.DataFrame, height: int = 220) -> alt.TopLevelMixin:
    """Events loaded per bucket, with the average and the peak marked."""
    p = theme.palette()
    peak = series.loc[[series["events"].idxmax()]].assign(label=lambda d: d["events"].map(lambda v: f"peak {v:,}"))
    mean = float(series["events"].mean())
    top = max(float(series["events"].max()) * 1.2, 1.0)
    fill = alt.Gradient(gradient="linear", x1=1, x2=1, y1=1, y2=0,
                        stops=[alt.GradientStop(color=p["accent"] + "05", offset=0), alt.GradientStop(color=p["accent"] + "77", offset=1)])
    x = alt.X("ts:T", title="Time (UTC)")
    y = alt.Y("events:Q", title="Events loaded per bucket", scale=alt.Scale(domain=[0, top]))
    area = alt.Chart(series).mark_area(line={"color": p["accent"], "strokeWidth": 2}, color=fill, interpolate="monotone").encode(
        x=x, y=y, tooltip=_tip("events:Q", "anomalies:Q"))
    avg_rule = alt.Chart(pd.DataFrame({"v": [mean]})).mark_rule(color=p["muted"], strokeDash=[5, 4]).encode(y="v:Q")
    avg_text = alt.Chart(pd.DataFrame({"v": [mean], "t": [f"average {mean:,.0f}"]})).mark_text(
        align="left", dx=4, dy=-6, color=p["muted"], fontSize=11).encode(y="v:Q", text="t:N", x=alt.value(4))
    dot = alt.Chart(peak).mark_point(filled=True, color=p["cyan"], size=70).encode(x="ts:T", y="events:Q")
    label = alt.Chart(peak).mark_text(dy=-12, color=p["text"], fontWeight="bold", fontSize=11).encode(x="ts:T", y="events:Q", text="label:N")
    return _style(alt.layer(area, avg_rule, avg_text, dot, label), height)


def event_tracking(df: pd.DataFrame, height: int = 220) -> alt.TopLevelMixin:
    """One line per severity so a rise in WARNING/ERROR/CRITICAL is easy to spot."""
    colors = theme.severity_colors()
    wide = df.pivot_table(index="ts", columns="severity", values="events", aggfunc="sum", fill_value=0)
    long = wide.reset_index().melt(id_vars="ts", var_name="severity", value_name="events")
    scale = alt.Scale(domain=list(colors), range=list(colors.values()))
    chart = alt.Chart(long).mark_line(point=alt.OverlayMarkDef(size=36, filled=True), interpolate="monotone", strokeWidth=2.2).encode(
        x=alt.X("ts:T", title="Time (UTC)"),
        y=alt.Y("events:Q", title="Events per bucket (log scale)", scale=alt.Scale(type="symlog")),
        color=alt.Color("severity:N", scale=scale, sort=list(colors)),
        tooltip=_tip("severity:N", "events:Q"),
    )
    return _style(chart, height)


def anomaly_bars(series: pd.DataFrame, height: int = 180) -> alt.TopLevelMixin:
    """Flagged events per bucket; the biggest burst is labelled."""
    p = theme.palette()
    worst = series.loc[[series["anomalies"].idxmax()]]
    worst = worst[worst["anomalies"] > 0].assign(label=lambda d: d["anomalies"].map(lambda v: f"largest burst: {v:,}"))
    top = max(float(series["anomalies"].max()) * 1.25, 1.0)
    bars = alt.Chart(series).mark_bar(color=p["crit"], cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("ts:T", title="Time (UTC)"),
        y=alt.Y("anomalies:Q", title="Anomalies flagged", scale=alt.Scale(domain=[0, top])),
        tooltip=_tip("anomalies:Q", "events:Q"),
    )
    label = alt.Chart(worst).mark_text(dy=-8, color=p["text"], fontWeight="bold", fontSize=11).encode(x="ts:T", y="anomalies:Q", text="label:N")
    return _style(alt.layer(bars, label), height)


def score_histogram(hist: pd.DataFrame, threshold: float | None, height: int = 220) -> alt.TopLevelMixin:
    """Model score of every event; the alert threshold splits normal from flagged."""
    p = theme.palette()
    hist = hist.assign(score_end=hist["score_bucket"] + 0.05)
    cut = threshold if threshold is not None else 1.0
    color = alt.condition(alt.datum.score_bucket >= (cut // 0.05) * 0.05 - 1e-9, alt.value(p["crit"]), alt.value(p["cyan"]))
    bars = alt.Chart(hist).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X("score_bucket:Q", title="Anomaly score (0 = normal, 1 = certain attack)", scale=alt.Scale(domain=[0, 1])),
        x2="score_end:Q",
        y=alt.Y("events:Q", title="Events (log scale)", scale=alt.Scale(type="symlog")),
        color=color, tooltip=[alt.Tooltip("score_bucket:Q", title="Score from"), "events:Q"],
    )
    layers = [bars]
    if threshold is not None:
        frame = pd.DataFrame({"x": [threshold]})
        layers.append(alt.Chart(frame).mark_rule(color=p["warn"], strokeDash=[6, 4], size=2).encode(x="x:Q"))
        for text, align, dx in ("< normal", "right", -6), (f"flagged >  (threshold {threshold:.2f})", "left", 6):
            note = pd.DataFrame({"x": [threshold], "t": [text]})
            layers.append(alt.Chart(note).mark_text(align=align, dx=dx, color=p["warn"], fontSize=11, baseline="top").encode(
                x="x:Q", y=alt.value(4), text="t:N"))
    return _style(alt.layer(*layers), height)


def severity_donut(df: pd.DataFrame, height: int = 220) -> alt.TopLevelMixin:
    """Share of events per severity with the total in the centre."""
    p = theme.palette()
    colors = theme.severity_colors()
    df = df.assign(label=lambda d: d["severity"] + "  " + d["events"].map("{:,}".format))
    order = [s for s in colors if s in set(df["severity"])]
    labels = [df.loc[df["severity"] == s, "label"].iloc[0] for s in order]
    scale = alt.Scale(domain=labels, range=[colors[s] for s in order])
    arc = alt.Chart(df).mark_arc(innerRadius=58, stroke=p["edge"], strokeWidth=2).encode(
        theta=alt.Theta("events:Q"), color=alt.Color("label:N", scale=scale, legend=alt.Legend(orient="right")),
        tooltip=["severity:N", "events:Q", "anomalies:Q"],
    )
    centre = alt.Chart(pd.DataFrame({"t": [f"{int(df['events'].sum()):,}"]})).mark_text(
        fontSize=22, fontWeight="bold", color=p["text"], dy=-6).encode(text="t:N")
    sub = alt.Chart(pd.DataFrame({"t": ["events"]})).mark_text(fontSize=11, color=p["muted"], dy=14).encode(text="t:N")
    return _style(alt.layer(arc, centre, sub), height).configure_legend(orient="right", title=None, **_legend(p))


def by_event_type(df: pd.DataFrame, height: int = 260) -> alt.TopLevelMixin:
    """Normal vs flagged events for each kind of activity."""
    p = theme.palette()
    long = pd.concat([
        pd.DataFrame({"event_type": df["event_type"], "kind": "normal", "events": df["events"] - df["anomalies"]}),
        pd.DataFrame({"event_type": df["event_type"], "kind": "anomaly", "events": df["anomalies"]}),
    ])
    chart = alt.Chart(long).mark_bar().encode(
        y=alt.Y("event_type:N", sort="-x", title="Event type"),
        x=alt.X("events:Q", title="Events (log scale)", scale=alt.Scale(type="symlog")),
        color=alt.Color("kind:N", scale=alt.Scale(domain=["normal", "anomaly"], range=[p["accent"], p["crit"]])),
        tooltip=["event_type:N", "kind:N", "events:Q"],
    )
    return _style(chart, height)


def reasons(df: pd.DataFrame, height: int = 200) -> alt.TopLevelMixin:
    p = theme.palette()
    chart = alt.Chart(df).mark_bar(color=p["warn"], cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
        y=alt.Y("reason:N", sort="-x", title="Rejection reason"), x=alt.X("records:Q", title="Rejected records"),
        tooltip=["reason:N", "records:Q"],
    )
    return _style(chart, height)
