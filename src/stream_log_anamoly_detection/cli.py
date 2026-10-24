"""Command line entry point: `migrate`, `run` and `dashboard` (the default)."""

import argparse
import logging
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from .config import Settings
from .pipeline import check_source, run
from .storage import run_goose

log = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stream-log-anamoly-detection", description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command")  # no command: open the dashboard
    migrate = sub.add_parser("migrate", help="run goose migrations against ClickHouse")
    migrate.add_argument("goose_command", nargs="?", default="up", help="goose command: up, down, status, version, ...")
    migrate.add_argument("goose_args", nargs="*", help="extra goose arguments, e.g. up-to 2")
    run_cmd = sub.add_parser("run", help="stream security logs into ClickHouse and score them")
    run_cmd.add_argument("--max-events", type=int, default=None, help="stop after reading this many events")
    run_cmd.add_argument("--batch-size", type=int, default=None, help="rows per ClickHouse insert")
    run_cmd.add_argument("--no-detection", action="store_true", help="skip anomaly scoring")
    sub.add_parser("dashboard", help="open the Streamlit dashboard")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()

    if args.command == "migrate":
        return run_goose(settings, args.goose_command, *args.goose_args)

    if args.command in (None, "dashboard"):
        app = Path(__file__).parent / "dashboard" / "app.py"
        project_root = Path(__file__).resolve().parents[2]  # holds .streamlit/config.toml (dark theme)
        cwd = project_root if (project_root / ".streamlit").is_dir() else None
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)], cwd=cwd)

    if args.batch_size:
        settings = replace(settings, batch_size=args.batch_size)
    if args.no_detection:
        settings = replace(settings, detection_enabled=False)
    if not check_source(settings):
        return 1
    stats = run(settings, max_events=args.max_events)
    log.info("done: read=%d loaded=%d rejected=%d anomalies=%d", stats.read, stats.loaded, stats.rejected, stats.anomalies)
    return 0


if __name__ == "__main__":
    sys.exit(main())
