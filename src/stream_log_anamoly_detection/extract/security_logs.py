"""Extract: read the NDJSON security-log stream exposed by Mock-Data-Gen."""

import logging
import time
from collections.abc import Iterator

import requests

from ..config import Settings

log = logging.getLogger(__name__)


def ensure_stream(settings: Settings, session: requests.Session | None = None) -> None:
    """Create the dataset if missing and make sure it is streaming."""
    http = session or requests.Session()
    base, name = settings.api_url, settings.dataset

    resp = http.get(f"{base}/datasets/{name}", timeout=10)
    if resp.status_code == 404:
        payload = {
            "name": name,
            "spec": {
                "kind": "generator",
                "generator": "security_logs",
                "options": {"anomalies_per_minute": settings.anomalies_per_minute},
            },
            "eps": settings.events_per_second,
            "stream": True,
        }
        http.post(f"{base}/datasets", json=payload, timeout=10).raise_for_status()
        log.info("created dataset %r and started streaming", name)
        return

    resp.raise_for_status()
    if not resp.json().get("streaming"):
        http.post(f"{base}/datasets/{name}/stream/start", timeout=10).raise_for_status()
        log.info("started streaming for dataset %r", name)


def stream_lines(settings: Settings) -> Iterator[str]:
    """Yield raw NDJSON lines; reconnect with backoff on network errors.

    Returns when the server closes the stream cleanly (the source stopped).
    """
    url = f"{settings.api_url}/datasets/{settings.dataset}/stream"
    params = {"wait": settings.stream_wait_seconds}
    failures = 0

    while True:
        try:
            # Read timeout must exceed the server-side `wait` so an idle stream is not mistaken for a dead one.
            with requests.get(url, params=params, stream=True,
                              timeout=(10, settings.stream_wait_seconds + 30)) as resp:
                resp.raise_for_status()
                log.info("connected to %s", url)
                for line in resp.iter_lines(decode_unicode=True):
                    if line:
                        failures = 0
                        yield line
            log.info("stream closed by the server")
            return
        except requests.RequestException as exc:
            failures += 1
            if failures > settings.max_retries:
                raise
            delay = min(2 ** failures, 30)
            log.warning("stream error (%s); retry %d/%d in %ds", exc, failures, settings.max_retries, delay)
            time.sleep(delay)
