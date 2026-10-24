"""HTML snippets for the dashboard. Log content is untrusted, so every dynamic value goes through esc()."""

import html
from collections.abc import Iterable, Sequence

import pandas as pd

from . import incidents

SEVERITY_TONE = {"INFO": "info", "WARNING": "warn", "ERROR": "bad", "CRITICAL": "crit"}

def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def b(value, tone: str = "") -> str:
    return f'<b class="{tone}">{esc(value)}</b>'


def icon(name: str, size: int = 18) -> str:
    """Icon drawn by a CSS mask from theme.ICONS (inline SVG is stripped by Streamlit's sanitizer)."""
    return f'<i class="ic ic-{name}" style="font-size:{size}px"></i>'


def fmt_time(value) -> str:
    return "--:--:--" if value is None or pd.isna(value) else pd.Timestamp(value).strftime("%H:%M:%S")


def ago(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    secs = (pd.Timestamp.now(tz="UTC").tz_localize(None) - pd.Timestamp(value)).total_seconds()
    if secs < 5:
        return "just now"
    if secs < 120:
        return f"{secs:.0f}s ago"
    if secs < 7200:
        return f"{secs / 60:.0f} min ago"
    return f"{secs / 3600:.1f} h ago" if secs < 172800 else f"{secs / 86400:.0f} days ago"


def duration(start, end) -> str:
    secs = max((pd.Timestamp(end) - pd.Timestamp(start)).total_seconds(), 0)
    return f"{secs:.0f} s" if secs < 120 else f"{secs // 60:.0f} min {secs % 60:.0f} s"


def badge(text: str, tone: str = "idle", dot: bool = False) -> str:
    marker = '<span class="sl-dot"></span>' if dot else ""
    return f'<span class="sl-badge {tone}">{marker}{esc(text)}</span>'


def tag(text: str, tone: str = "") -> str:
    return f'<span class="sl-tag {tone}">{esc(text)}</span>'


def sparkline(values: Sequence[float], color: str, bars: int = 28) -> str:
    """Mini bar chart; values are resampled to at most `bars` bars."""
    if len(values) < 2:
        return ""
    size = -(-len(values) // bars)  # ceil: group neighbours so long series still fit
    grouped = [sum(values[i:i + size]) for i in range(0, len(values), size)]
    peak = max(max(grouped), 1)
    cells = "".join(f'<i style="height:{max(grouped_value / peak * 100, 6):.0f}%"></i>' for grouped_value in grouped)
    return f'<div class="sl-spark" style="--c:{color}">{cells}</div>'


def kpi(label: str, value: str, sub: str = "", tone: str = "", series: Sequence[float] | None = None, color: str = "#818cf8") -> str:
    sub_html = f'<div class="sl-kpi-sub">{esc(sub)}</div>' if sub else ""
    spark = sparkline(list(series), color) if series is not None else ""
    return (
        f'<div class="sl-card sl-kpi {tone}"><div class="sl-kpi-label">{esc(label)}</div>'
        f'<div class="sl-kpi-value">{esc(value)}</div>{sub_html}{spark}</div>'
    )


def kpi_grid(cards: Iterable[str]) -> str:
    return f'<div class="sl-kpis">{"".join(cards)}</div>'


def brand_header(title: str, subtitle: str, chips: Iterable[str]) -> str:
    chip_html = "".join(f'<span class="sl-chip">{icon(i, 14)}<b>{esc(t)}</b></span>' for i, t in chips)
    return (
        f'<div class="sl-brand"><div class="sl-brand-l"><div class="sl-logo">{icon("shield", 24)}</div>'
        f'<div><div class="sl-title">{esc(title)}</div><div class="sl-sub">{esc(subtitle)}</div></div></div>'
        f'<div class="sl-chips">{chip_html}</div></div>'
    )


def status_ribbon(state: str, label: str, meta: str, active_alerts: int, critical: int) -> str:
    return (
        f'<div class="sl-ribbon"><div class="sl-ribbon-l">{badge(label, state, dot=True)}<span>{esc(meta)}</span></div>'
        f'<div class="sl-ribbon-r"><span class="sl-chip alert" title="Anomalies flagged in the last 5 minutes">{icon("bell", 14)}'
        f'<b>{active_alerts:,}</b> alerts (5 min)</span>'
        f'<span class="sl-chip crit" title="Critical anomalies in the last 5 minutes">{icon("alert", 14)}<b>{critical:,}</b> critical</span></div></div>'
    )


def section(title: str) -> str:
    return f'<div class="sl-section">{esc(title)}</div>'


def panel_title(title: str, caption: str = "", right: str = "") -> str:
    cap = f'<div class="sl-panel-cap">{esc(caption)}</div>' if caption else ""
    return f'<div class="sl-panel-title"><span>{esc(title)}</span>{right}</div>{cap}'


def kv_list(pairs: Iterable[tuple]) -> str:
    rows = []
    for pair in pairs:
        key, value, *tone = pair
        rows.append(f'<div class="sl-kv"><span>{esc(key)}</span><b class="{tone[0] if tone else ""}">{esc(value)}</b></div>')
    return "".join(rows)


def empty(text: str) -> str:
    return f'<div class="sl-empty">{esc(text)}</div>'


def insight(body_html: str) -> str:
    """`body_html` must already be escaped (build it with esc() and b())."""
    return f'<div class="sl-insight">{icon("activity", 22)}<div>{body_html}</div></div>'


_ARROW = f'<div class="sl-arrow">{icon("arrow", 22)}</div>'


def stage(step: str, title: str, value: str, caption: str, tone: str = "idle") -> str:
    return (
        f'<div class="sl-card sl-stage {tone}"><div class="sl-step">{esc(step)}</div>'
        f'<div class="sl-stage-title"><span class="sl-dot"></span>{esc(title)}</div>'
        f'<div class="sl-stage-value">{esc(value)}</div><div class="sl-stage-cap">{esc(caption)}</div></div>'
    )


def flow(stages: Sequence[str]) -> str:
    return f'<div class="sl-flow">{_ARROW.join(stages)}</div>'


def feed(df: pd.DataFrame, empty_text: str = "No events in this window.", fresh_seconds: float = 0) -> str:
    """Event table. Rows ingested within `fresh_seconds` get a one-off highlight so new arrivals stand out."""
    if df.empty:
        return empty(empty_text)
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)  # ClickHouse returns naive UTC timestamps
    rows = [
        '<div class="sl-row sl-head"><span>Time</span><span>Level</span><span class="type">Event</span>'
        '<span class="src">Source</span><span>Message</span><span class="score">Score</span></div>'
    ]
    for r in df.itertuples():
        fresh = fresh_seconds and (now - pd.Timestamp(r.ingested_at)).total_seconds() <= fresh_seconds
        cls = "sl-row" + (" anomaly" if r.is_anomaly else "") + (" new" if fresh else "")
        rows.append(
            f'<div class="{cls}"><span class="t">{fmt_time(r.event_time)}</span>'
            f'<span>{badge(r.severity, SEVERITY_TONE.get(r.severity, "idle"))}</span>'
            f'<span class="type">{esc(r.event_type)}</span><span class="src">{esc(r.source_ip)}</span>'
            f'<span title="{esc(r.message)}">{esc(r.message)}</span><span class="score">{r.anomaly_score:.2f}</span></div>'
        )
    return f'<div class="sl-feed">{"".join(rows)}</div>'


def rejected_list(df: pd.DataFrame) -> str:
    if df.empty:
        return empty("No rejected records.")
    return "".join(
        f'<div class="sl-raw"><div class="r"><b>{esc(r.reason)}</b><span>{fmt_time(r.rejected_at)}</span></div>'
        f"<code>{esc(str(r.raw)[:300])}</code></div>"
        for r in df.itertuples()
    )


def incident_card(inc: dict, hot: bool = False) -> str:
    tone = SEVERITY_TONE.get(inc["severity"], "idle")
    hot_ip = f'<div class="sl-hotip">Source IP : <code>{esc(inc["source_ip"])}</code></div>' if hot else ""
    source = "" if hot else f'<span>Source: <code>{esc(inc["source_ip"])}</code></span>'
    count_tag, score_tag = tag(f"{inc['events']:,} events"), tag(f"score {inc['max_score']:.2f}", tone)
    return (
        f'<div class="sl-card sl-incident{" hot" if hot else ""}"><div class="sl-incident-top">'
        f'<h4>{esc(incidents.title_for(inc["event_type"]))}</h4>{badge(inc["severity"], tone)}</div>'
        f'<p>{esc(inc["sample"])}</p>{hot_ip}'
        f'<div class="sl-tags">{count_tag}{score_tag}{tag(inc["event_type"])}</div>'
        f'<div class="sl-incident-meta">{source}<span>{esc(inc["country"])}</span><span>{ago(inc["last_seen"])}</span></div></div>'
    )


def incident_grid(cards: Iterable[str]) -> str:
    return f'<div class="sl-incidents">{"".join(cards)}</div>'


def detail_head(inc: dict) -> str:
    tone = SEVERITY_TONE.get(inc["severity"], "idle")
    return (
        f'<div class="sl-card sl-detail-head"><div class="sl-tags">{badge(inc["severity"], tone)}{tag(inc["event_type"])}</div>'
        f'<h2>{esc(incidents.title_for(inc["event_type"]))}</h2><p>{esc(inc["sample"])}</p>'
        f'<div class="sl-meta-row"><div>Source IP<b>{esc(inc["source_ip"])}</b></div>'
        f'<div>First detected<b>{ago(inc["first_seen"])}</b></div>'
        f'<div>Incident ID<b>{incidents.incident_id(inc["source_ip"], inc["event_type"])}</b></div></div></div>'
    )


def tiles(items: Iterable[tuple[str, str, str, str]]) -> str:
    """Each item is (icon name, label, value, tone)."""
    return '<div class="sl-tiles">' + "".join(
        f'<div class="sl-tile"><div class="sl-ico {tone}">{icon(name, 20)}</div><div><small>{esc(label)}</small><b>{esc(value)}</b></div></div>'
        for name, label, value, tone in items
    ) + "</div>"


def actions(items: Iterable[str]) -> str:
    return '<div class="sl-actions">' + "".join(f'<div class="sl-act">{icon("alert", 16)}<span>{esc(a)}</span></div>' for a in items) + "</div>"
