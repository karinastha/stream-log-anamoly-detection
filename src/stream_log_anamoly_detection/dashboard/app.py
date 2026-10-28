"""Streamlit dashboard for the security-log ETL and anomaly detection pipeline.

Run with: uv run app   (or: python -m stream_log_anamoly_detection dashboard)
"""

import ipaddress
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from stream_log_anamoly_detection.config import Settings
from stream_log_anamoly_detection.dashboard import charts, components as ui, incidents, theme
from stream_log_anamoly_detection.dashboard.queries import Queries, WINDOWS, bucket_seconds, window_start
from stream_log_anamoly_detection.storage import get_client

st.set_page_config(page_title="Security log ETL", page_icon=":material/shield:", layout="wide",
                   initial_sidebar_state="collapsed")
settings = Settings.from_env()
theme.init()
theme.inject()

LIVE_WITHIN_SECONDS = 30
SUMMARY_SECONDS = 300
FEED_ROWS = 40
LEVEL_NAMES = {0: "none", 1: "INFO", 2: "WARNING", 3: "ERROR", 4: "CRITICAL"}

HELP = {
    "feed": "Every row is one log event as it is loaded. Red rows were flagged by the model; Score is its anomaly "
            "probability from 0 to 1 (flagged at or above {thr}).",
    "tracking": "Events per time bucket, one line per severity. A rise in the WARNING, ERROR or CRITICAL lines means more "
                "suspicious activity. Log scale, so small lines stay visible. Hover for exact counts.",
    "throughput": "How many logs the pipeline loaded in each bucket. A steady line near the dashed average is healthy; "
                  "a drop to zero means the ETL stopped.",
    "bursts": "Events the model flagged in each bucket. Tall bars are attack bursts such as brute-force logins or port scans.",
    "severity": "Share of events per severity. Mostly INFO is healthy; growing ERROR or CRITICAL slices need attention.",
    "types": "Which kinds of activity get flagged. Blue is normal, red is anomalous. Log scale keeps small red bars visible.",
    "scores": "Model score of every event. Events right of the dashed threshold are flagged. Two clearly separated groups "
              "mean the model tells normal and attack traffic apart well.",
    "reasons": "Records that failed validation and were not loaded, grouped by cause.",
}


@st.cache_resource
def _client():
    # One session per query: the Streamlit fragments may run concurrently.
    return get_client(settings, autogenerate_session_id=False)


def _queries() -> Queries:
    return Queries(_client(), settings.clickhouse_db)


def _source_status() -> dict | None:
    try:
        resp = requests.get(f"{settings.api_url}/datasets/{settings.dataset}", timeout=2)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def _model_info() -> dict:
    results = Path(settings.model_path).parent / "model_results.json"
    info = {"threshold": settings.anomaly_threshold, "model": Path(settings.model_path).name, "type": None}
    if results.is_file():
        data = json.loads(results.read_text(encoding="utf-8")).get("message_model", {})
        info["type"] = data.get("type")
        if info["threshold"] is None:
            info["threshold"] = data.get("alert_threshold")
    return info


def _age_seconds(last) -> float | None:
    if last is None or pd.isna(last):
        return None
    stamp = pd.Timestamp(last)  # ClickHouse returns UTC values without tzinfo
    stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
    return (datetime.now(timezone.utc) - stamp.to_pydatetime()).total_seconds()


def _age_text(age: float | None) -> str:
    if age is None:
        return "no data"
    return f"{age:.0f}s ago" if age < 120 else f"{age / 60:.0f} min ago" if age < 7200 else f"{age / 3600:.1f} h ago"


def _chart(frame: pd.DataFrame, build, message: str) -> None:
    if frame.empty:
        st.html(ui.empty(message))
    else:
        st.altair_chart(build(frame), width="stretch", theme=None)


def _panel(title: str, caption: str):
    box = st.container(border=True)
    with box:
        st.html(ui.panel_title(title, caption))
    return box


def _live_summary(summary: pd.Series) -> str:
    events, anomalies = int(summary["events"]), int(summary["anomalies"])
    if not events:
        return (f"No events arrived in the last 5 minutes. Start the ETL with {ui.b('uv run app run')} "
                "and make sure the source API is streaming.")
    sources = int(summary["sources"])
    text = (f"In the last 5 minutes the pipeline loaded {ui.b(f'{events:,}')} events ({events / SUMMARY_SECONDS:.1f}/s) "
            f"from {ui.b(f'{sources:,}')} source IPs. ")
    if anomalies:
        level = LEVEL_NAMES.get(int(summary["max_level"]), "-")
        text += (f"{ui.b(f'{anomalies:,}', 'crit')} were flagged as anomalous ({anomalies / events:.1%}), highest severity "
                 f"{ui.b(level)}; most flagged activity: {ui.b(summary['top_flagged_type'])}. ")
    else:
        text += "No anomalies were flagged, traffic looks normal. "
    return text + f"Most active source {ui.b(summary['top_source'])}, most common event {ui.b(summary['top_type'])}."


def _render_incident_detail(queries: Queries, since: datetime, incs: list[dict]) -> None:
    labels = {incidents.incident_id(i["source_ip"], i["event_type"]):
              f"{i['severity']}  |  {incidents.title_for(i['event_type'])}  |  {i['source_ip']}  ({i['events']:,} events)" for i in incs}
    picked = st.selectbox("Inspect an incident", list(labels), format_func=labels.get, key="incident_pick")
    inc = next(i for i in incs if incidents.incident_id(i["source_ip"], i["event_type"]) == picked)
    history = queries.ip_history(inc["source_ip"])
    related = queries.incident_events(since, inc["source_ip"], inc["event_type"])
    external = not ipaddress.ip_address(inc["source_ip"]).is_private

    st.html(ui.detail_head(inc))
    with st.container(border=True):
        st.html(ui.panel_title("Attack summary", "What happened, when, and how big it was."))
        st.html(ui.tiles([
            ("clock", "Attack started (UTC)", pd.Timestamp(inc["first_seen"]).strftime("%d %b %H:%M:%S"), ""),
            ("timer", "Duration", ui.duration(inc["first_seen"], inc["last_seen"]), "warn"),
            ("target", "Events flagged", f"{inc['events']:,}", "crit"),
            ("globe", "Targets / ports touched", f"{inc['targets']:,} hosts, {inc['ports']:,} ports", ""),
        ]))
    left, right = st.columns([3, 2], gap="medium")
    with left, st.container(border=True):
        st.html(ui.panel_title("Related events", "Newest events from this source with the same activity type; red rows were flagged."))
        st.html(ui.feed(related, "No events found."))
    with right:
        with st.container(border=True):
            st.html(ui.panel_title("Threat intelligence", "Context gathered from your own logs."))
            st.html(ui.kv_list([
                ("Network", "External (internet)" if external else "Internal", "crit" if external else ""),
                ("Origin country", inc["country"]), ("Account", inc["username"]), ("Host", inc["host"]),
                ("Peak model score", f"{inc['max_score']:.2f}", "crit" if inc["max_score"] >= 0.9 else "warn"),
                ("Flagged from this IP (all time)", f"{int(history['anomalies']):,} of {int(history['events']):,} events", "warn"),
                ("First ever seen", ui.ago(history["first_seen"])),
            ]))
        with st.container(border=True):
            st.html(ui.panel_title("Recommended actions", "Suggested response steps for this type of incident."))
            st.html(ui.actions(incidents.actions_for(inc["event_type"])))


def _render(window_label: str, refresh_seconds: int | None) -> None:
    seconds = WINDOWS[window_label]
    since = window_start(seconds)
    now_text = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    try:
        queries = _queries()
        totals = queries.totals(since)
    except Exception as exc:  # surfaced to the user instead of a stack trace
        st.html(ui.status_ribbon("crit", "ClickHouse offline", now_text, 0, 0))
        st.error(f"Cannot read ClickHouse at {settings.clickhouse_host}:{settings.clickhouse_port}: {exc}")
        st.info("Start ClickHouse (`docker compose up -d`) and run `uv run app migrate`.")
        return

    rejected = queries.rejected_count(since)
    source = _source_status()
    events, anomalies = int(totals["events"]), int(totals["anomalies"])
    extracted = events + rejected
    age = _age_seconds(totals["last_ingested"]) if events else None
    live = age is not None and age < LIVE_WITHIN_SECONDS
    rate = queries.live_rate(LIVE_WITHIN_SECONDS)
    eps = int(rate["events"]) / LIVE_WITHIN_SECONDS
    streaming = bool(source and source.get("streaming"))
    summary = queries.recent_summary(SUMMARY_SECONDS)
    model = _model_info()
    threshold = model["threshold"]
    thr_text = f"{threshold:.2f}" if threshold is not None else "the model threshold"

    bucket = bucket_seconds(seconds)
    series = queries.throughput(since, bucket)
    latest = queries.latest_events(since, FEED_ROWS)
    incs = queries.incidents(since).to_dict("records")
    fresh = refresh_seconds or 0

    state, label = ("ok", "Live") if live else ("idle", "Idle") if events else ("idle", "No data")
    st.html(ui.status_ribbon(state, label, f"{window_label}  |  last load {_age_text(age)}  |  updated {now_text}",
                             int(summary["anomalies"]), int(summary["critical"])))

    st.html(ui.kpi_grid([
        ui.kpi("Source stream", "Streaming" if streaming else "Stopped" if source else "Unreachable",
               f"{source['eps']} events/s configured" if source else settings.api_url, "ok" if streaming else "bad"),
        ui.kpi("Throughput", f"{eps:,.1f}/s", f"avg over the last {LIVE_WITHIN_SECONDS}s", "ok" if live else "",
               series["events"].tolist() if not series.empty else None, "var(--accent)"),
        ui.kpi("Events loaded", f"{events:,}", f"{int(totals['sources']):,} distinct source IPs"),
        ui.kpi("Anomalies", f"{anomalies:,}", f"{anomalies / events:.2%} of events" if events else "",
               "bad" if anomalies else "", series["anomalies"].tolist() if not series.empty else None, "var(--crit)"),
        ui.kpi("Rejected", f"{rejected:,}", "failed validation", "warn" if rejected else ""),
    ]))

    live_tab, incident_tab, analytics_tab, pipeline_tab, quality_tab = st.tabs([
        ":material/sensors: Live stream", ":material/crisis_alert: Incidents", ":material/insights: Analytics",
        ":material/account_tree: Pipeline", ":material/fact_check: Data quality",
    ])

    with live_tab:
        st.html(ui.insight(_live_summary(summary)))
        level = int(summary["max_level"])
        n_events, n_anoms = int(summary["events"]), int(summary["anomalies"])
        st.html(ui.kpi_grid([
            ui.kpi("Events, last 5 min", f"{n_events:,}", f"{n_events / SUMMARY_SECONDS:.1f} per second"),
            ui.kpi("Anomalies, last 5 min", f"{n_anoms:,}", f"{n_anoms / n_events:.1%} of events" if n_events else "",
                   "bad" if n_anoms else "ok"),
            ui.kpi("Highest severity flagged", LEVEL_NAMES.get(level, "-") if n_anoms else "none",
                   "worst anomaly in 5 min", "bad" if level >= 3 else "warn" if level == 2 else ""),
            ui.kpi("Most active source", str(summary["top_source"]) or "-", f"{int(summary['sources']):,} sources seen"),
        ]))
        left, right = st.columns([3, 2], gap="medium")
        with left:
            if incs:
                st.html(ui.incident_card(incs[0], hot=True))
            with _panel("Live event stream", f"Newest {FEED_ROWS} events. " + HELP["feed"].format(thr=thr_text)):
                st.html(ui.feed(latest, fresh_seconds=fresh))
        with right:
            with _panel("Event tracking", HELP["tracking"]):
                _chart(queries.severity_timeline(since, bucket), charts.event_tracking, "No events in this window.")
            with _panel("Throughput", HELP["throughput"]):
                _chart(series, charts.throughput, "No events in this window.")

    with incident_tab:
        st.html(ui.insight(
            "An incident groups anomalous events that share a source IP and activity type. "
            f"The red card is the most severe; there {'is' if len(incs) == 1 else 'are'} {ui.b(len(incs))} "
            f"{'incident' if len(incs) == 1 else 'incidents'} in this window. Pick one below for a full breakdown."))
        if not incs:
            st.html(ui.empty("No incidents in this window. Widen the time window or wait for new anomalies."))
        else:
            st.html(ui.incident_grid([ui.incident_card(i, hot=n == 0) for n, i in enumerate(incs[:6])]))
            st.html(ui.section("Incident details"))
            _render_incident_detail(queries, since, incs)

    with analytics_tab:
        left, right = st.columns([3, 2], gap="medium")
        with left, _panel("Anomalies over time", HELP["bursts"]):
            _chart(series, lambda f: charts.anomaly_bars(f, 230), "No events in this window.")
        with right, _panel("Events by severity", HELP["severity"]):
            _chart(queries.anomalies_by_severity(since), lambda f: charts.severity_donut(f, 230), "No events in this window.")
        left, right = st.columns(2, gap="medium")
        with left, _panel("Flagged vs normal by event type", HELP["types"]):
            _chart(queries.by_event_type(since), charts.by_event_type, "No events in this window.")
        with right, _panel("Anomaly score distribution", HELP["scores"]):
            _chart(queries.score_histogram(since), lambda f: charts.score_histogram(f, threshold), "No scored events.")
        left, right = st.columns([2, 3], gap="medium")
        with left, _panel("Top alerting sources", "Source IPs with the most flagged events, with their strongest model score."):
            top = queries.top_alert_sources(since)
            st.html(ui.table(top, mono=("source_ip",), empty_text="No anomalies in this window."))
        with right, _panel("Latest alerts", "Most recently flagged events, newest first."):
            st.html(ui.feed(queries.recent_alerts(since), "No anomalies in this window.", fresh_seconds=fresh))

    with pipeline_tab:
        st.html(ui.insight("Data flows left to right: the source API streams logs, Extract reads them, Transform validates and "
                           "enriches each record, Detect scores it with the model, and Load writes it to ClickHouse. "
                           "A green top edge means the stage is healthy; amber or red needs attention."))
        st.html(ui.flow([
            ui.stage("01", "Source", f"{source['total_generated']:,}" if source else "-", "events generated",
                     "ok" if streaming else "bad"),
            ui.stage("02", "Extract", f"{extracted:,}", "records read from the stream", "ok" if live else "idle"),
            ui.stage("03", "Transform", f"{events:,}", "valid and enriched",
                     "warn" if rejected else "ok" if events else "idle"),
            ui.stage("04", "Detect", f"{anomalies:,}", "anomalies flagged", "bad" if anomalies else "ok" if events else "idle"),
            ui.stage("05", "Load", f"{events:,}", "rows in ClickHouse", "ok" if live else "idle"),
        ]))
        st.html('<div class="sl-branch">Transform'
                f'{ui.badge(f"{rejected:,} rejected", "warn" if rejected else "idle")}'
                "stored in security_logs_rejected for inspection</div>")
        left, right = st.columns(2, gap="medium")
        with left, _panel("Detection model", "Message classifier trained in anamoly_detection_ml."):
            st.html(ui.kv_list([("Model file", model["model"]), ("Type", model["type"] or "unknown"),
                                ("Alert threshold", f"{threshold:.3f}" if threshold is not None else "stored in model"),
                                ("Detection", "enabled" if settings.detection_enabled else "disabled")]))
        with right, _panel("Source", "Mock-Data-Gen HTTP API that feeds the pipeline."):
            if source:
                st.html(ui.kv_list([("Dataset", source["name"]), ("Endpoint", settings.api_url),
                                    ("Rate", f"{source['eps']} events/s"),
                                    ("Generated so far", f"{source['total_generated']:,}")]))
            else:
                st.html(ui.empty(f"Source API not reachable at {settings.api_url}"))

    with quality_tab:
        valid_pct = events / extracted if extracted else 1.0
        st.html(ui.kpi_grid([
            ui.kpi("Valid records", f"{valid_pct:.2%}", f"{events:,} of {extracted:,} loaded", "ok" if valid_pct == 1 else "warn"),
            ui.kpi("Rejected", f"{rejected:,}", "failed validation", "warn" if rejected else ""),
        ]))
        left, right = st.columns(2, gap="medium")
        with left, _panel("Rejected by reason", HELP["reasons"]):
            _chart(queries.rejected_by_reason(since), charts.reasons, "No rejected records in this window.")
        with right, _panel("Latest rejected records", "The raw lines that were rejected, to help you find the cause."):
            st.html(ui.rejected_list(queries.recent_rejected(since)))


head, switch = st.columns([10, 1.7], gap="medium", vertical_alignment="center")
head.html(ui.brand_header("Security Log ETL", "Streaming ETL and anomaly detection | SOC view", [
    ("server", f"ClickHouse {settings.clickhouse_host}:{settings.clickhouse_port}/{settings.clickhouse_db}"),
    ("activity", f"Source {settings.api_url}"),
]))
light = theme.mode() == "light"
switch.button("Dark mode" if light else "Light mode", key="theme_toggle", on_click=theme.toggle, width="stretch",
              icon=":material/dark_mode:" if light else ":material/light_mode:",
              help="Switch to the dark theme" if light else "Switch to the light theme")

with st.container(border=True):
    c_window, c_live, c_interval, c_refresh = st.columns([2.2, 1.3, 2.6, 1.2], gap="medium", vertical_alignment="bottom")
    window = c_window.selectbox("Time window", list(WINDOWS), index=1)
    live_updates = c_live.toggle("Live updates", value=True)
    interval = c_interval.segmented_control("Refresh every", [2, 5, 10, 30], default=5, format_func=lambda s: f"{s}s",
                                            disabled=not live_updates) or 5
    c_refresh.button("Refresh now", width="stretch")

refresh = interval if live_updates else None
st.fragment(run_every=refresh)(_render)(window, refresh)
