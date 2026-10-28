"""Entry point for Streamlit Community Cloud (and `streamlit run streamlit_app.py`).

Adds `src/` to the import path so the dashboard works even if the project itself is not installed
in the deployment environment, then runs the dashboard script fresh on every Streamlit rerun.
"""

import runpy
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

runpy.run_path(str(SRC / "stream_log_anamoly_detection" / "dashboard" / "app.py"), run_name="__main__")
