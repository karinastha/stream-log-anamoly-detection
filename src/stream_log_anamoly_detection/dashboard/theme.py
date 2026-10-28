"""Design tokens and global CSS for the dashboard: glassy, neon accents, responsive, with a dark and a light palette."""

from urllib.parse import quote

import streamlit as st

PALETTES = {
    "dark": {
        "text": "#e8ecff", "muted": "#8d97bd", "border": "#2a3158", "line": "rgba(148,163,255,.18)",
        "accent": "#818cf8", "cyan": "#67e8f9", "ok": "#a3e635", "warn": "#fbbf24", "bad": "#fb923c", "crit": "#ff4d6d",
        "grid": "#ffffff12", "edge": "#0d1330", "scheme": "dark",
        "page": "radial-gradient(900px 520px at 10% -6%, rgba(99,102,241,.30), transparent 60%),"
                "radial-gradient(800px 480px at 96% 4%, rgba(34,211,238,.17), transparent 55%),"
                "radial-gradient(700px 520px at 50% 112%, rgba(163,230,53,.07), transparent 60%),"
                "linear-gradient(180deg,#050816,#070b1f)",
        "grid-line": "rgba(129,140,248,.06)",
        "glass-a": "rgba(255,255,255,.075)", "glass-b": "rgba(255,255,255,.02)",
        "shadow": "0 10px 40px rgba(2,6,23,.45)", "edge-hi": "rgba(255,255,255,.09)",
        "soft": "rgba(255,255,255,.03)", "soft-2": "rgba(255,255,255,.05)", "soft-3": "rgba(255,255,255,.045)",
        "title": "#ffffff", "code": "#cbd5ff", "hot-ip": "#ff8fa3", "head-bg": "rgba(9,13,38,.92)",
        "raw-bg": "rgba(0,0,0,.2)", "row-line": "rgba(148,163,255,.10)", "glow": "45%",
        "tab-grad": "linear-gradient(90deg,#818cf8,#67e8f9)", "tab-fg": "#06102a", "tab-glow": "rgba(103,232,249,.38)",
        "flash": "rgba(103,232,249,.30)", "pop-bg": "#121833", "pop-hover": "rgba(129,140,248,.18)",
        "brand-bg": "linear-gradient(100deg,rgba(49,46,129,.85),rgba(30,64,175,.55) 55%,rgba(8,145,178,.45))",
        "brand-shadow": "0 14px 50px rgba(30,41,140,.35)", "brand-sub": "#b4bdf0", "chip-bg": "rgba(8,12,40,.55)",
    },
    "light": {
        "text": "#0f172a", "muted": "#566089", "border": "#c9d0f2", "line": "rgba(79,70,229,.20)",
        "accent": "#4f46e5", "cyan": "#0e7490", "ok": "#4d7c0f", "warn": "#b45309", "bad": "#c2410c", "crit": "#e11d48",
        "grid": "#4f46e520", "edge": "#f1f5ff", "scheme": "light",
        "page": "radial-gradient(900px 520px at 10% -6%, rgba(99,102,241,.22), transparent 60%),"
                "radial-gradient(800px 480px at 96% 4%, rgba(34,211,238,.22), transparent 55%),"
                "radial-gradient(700px 520px at 50% 112%, rgba(163,230,53,.14), transparent 60%),"
                "linear-gradient(180deg,#f5f7ff,#e9eeff)",
        "grid-line": "rgba(79,70,229,.07)",
        "glass-a": "rgba(255,255,255,.82)", "glass-b": "rgba(255,255,255,.48)",
        "shadow": "0 10px 30px rgba(79,70,229,.13)", "edge-hi": "rgba(255,255,255,.95)",
        "soft": "rgba(79,70,229,.045)", "soft-2": "rgba(79,70,229,.08)", "soft-3": "rgba(255,255,255,.6)",
        "title": "#0f172a", "code": "#3730a3", "hot-ip": "#be123c", "head-bg": "rgba(243,245,255,.96)",
        "raw-bg": "rgba(15,23,42,.04)", "row-line": "rgba(79,70,229,.12)", "glow": "0%",
        "tab-grad": "linear-gradient(90deg,#6366f1,#06b6d4)", "tab-fg": "#ffffff", "tab-glow": "rgba(99,102,241,.35)",
        "flash": "rgba(6,182,212,.22)", "pop-bg": "#ffffff", "pop-hover": "rgba(79,70,229,.10)",
        "brand-bg": "linear-gradient(100deg,#4f46e5,#2563eb 55%,#0891b2)",
        "brand-shadow": "0 14px 40px rgba(79,70,229,.30)", "brand-sub": "#e0e7ff", "chip-bg": "rgba(255,255,255,.18)",
    },
}

# Streamlit's HTML sanitizer drops inline <svg>, so icons are CSS masks defined here (see icon_css).
ICONS = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>'
             '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "timer": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20z"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "server": '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/>'
              '<line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
}


def mode() -> str:
    return st.session_state.get("theme", "dark")


def palette() -> dict:
    return PALETTES[mode()]


def severity_colors() -> dict:
    p = palette()
    return {"INFO": p["cyan"], "WARNING": p["warn"], "ERROR": p["bad"], "CRITICAL": p["crit"]}


def init() -> None:
    """Start in the mode from `?theme=light|dark` so a reload keeps the choice."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light" if st.query_params.get("theme") == "light" else "dark"


def toggle() -> None:
    st.session_state["theme"] = "light" if mode() == "dark" else "dark"
    st.query_params["theme"] = st.session_state["theme"]


def icon_css() -> str:
    rules = [".ic { display:inline-block; width:1em; height:1em; flex:none; background:currentColor; vertical-align:-.15em;"
             " -webkit-mask:var(--i) center/contain no-repeat; mask:var(--i) center/contain no-repeat; }"]
    for name, body in ICONS.items():
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' "
               f"stroke-linecap='round' stroke-linejoin='round'>{body.replace(chr(34), chr(39))}</svg>")
        rules.append(f'.ic-{name} {{ --i:url("data:image/svg+xml,{quote(svg, safe="")}"); }}')
    return "\n".join(rules)


def _variables(p: dict) -> str:
    skip = {"scheme", "grid", "edge"}
    body = ";".join(f"--{k}:{v}" for k, v in p.items() if k not in skip)
    return f":root {{ {body}; color-scheme:{p['scheme']}; }}"


CSS = """
[data-testid="stElementContainer"]:has(.sl-css) { display:none; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] { display:none !important; }
[data-testid="stAppViewContainer"] { background:var(--page); color:var(--text); }
[data-testid="stAppViewContainer"]::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:linear-gradient(var(--grid-line) 1px,transparent 1px),linear-gradient(90deg,var(--grid-line) 1px,transparent 1px);
  background-size:46px 46px; -webkit-mask-image:radial-gradient(ellipse at 50% 0%,#000 25%,transparent 75%); mask-image:radial-gradient(ellipse at 50% 0%,#000 25%,transparent 75%); }
[data-testid="stHeader"] { background:transparent; color:var(--text); }
[data-testid="stHeader"] button, [data-testid="stHeader"] a, [data-testid="stStatusWidget"] { color:var(--text); }
.block-container { position:relative; z-index:1; max-width:1440px; padding:3.4rem 2rem 3rem; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3 { letter-spacing:-.01em; }
[data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label { color:inherit; }

/* glass surfaces */
.sl-card, [data-testid="stVerticalBlockBorderWrapper"] {
  background:linear-gradient(135deg,var(--glass-a),var(--glass-b)) !important;
  -webkit-backdrop-filter:blur(16px) saturate(150%); backdrop-filter:blur(16px) saturate(150%);
  border:1px solid var(--line) !important; border-radius:16px !important;
  box-shadow:var(--shadow), inset 0 1px 0 var(--edge-hi); }
.sl-card { padding:1rem 1.1rem; position:relative; overflow:hidden; }
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] { box-shadow:none; }

/* brand header bar */
.sl-brand { display:flex; flex-wrap:wrap; gap:1rem; align-items:center; justify-content:space-between; padding:.9rem 1.2rem;
  border-radius:18px; border:1px solid rgba(165,180,252,.35); background:var(--brand-bg);
  -webkit-backdrop-filter:blur(18px); backdrop-filter:blur(18px); box-shadow:var(--brand-shadow), inset 0 1px 0 rgba(255,255,255,.18); }
.sl-brand-l { display:flex; align-items:center; gap:.9rem; }
.sl-logo { width:46px; height:46px; border-radius:50%; display:grid; place-items:center; color:#a5f3fc;
  background:radial-gradient(circle at 30% 25%,rgba(103,232,249,.35),rgba(79,70,229,.35)); border:1px solid rgba(165,243,252,.4); box-shadow:0 0 24px rgba(103,232,249,.35); }
.sl-title { font-size:clamp(1.15rem,2.2vw,1.55rem); font-weight:800; line-height:1.15; color:#fff; }
.sl-sub { color:var(--brand-sub); font-size:.85rem; margin-top:.15rem; }
.sl-chips { display:flex; flex-wrap:wrap; gap:.5rem; }
.sl-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.28rem .75rem; border-radius:999px; font-size:.78rem; color:var(--text);
  background:var(--soft-3); border:1px solid var(--line); }
.sl-chip b { color:var(--title); font-weight:700; }
.sl-brand .sl-chip { color:#e5eaff; background:var(--chip-bg); border-color:rgba(165,180,252,.3); }
.sl-brand .sl-chip b { color:#fff; }
.sl-chip.alert .ic { color:var(--ok); } .sl-chip.crit .ic { color:var(--crit); }

/* theme toggle (top right, next to the brand bar) */
.st-key-theme_toggle button { border-radius:999px; min-height:2.7rem; font-weight:700; white-space:nowrap;
  background:linear-gradient(135deg,var(--glass-a),var(--glass-b)); border:1px solid var(--line); color:var(--text);
  -webkit-backdrop-filter:blur(14px); backdrop-filter:blur(14px); box-shadow:var(--shadow), inset 0 1px 0 var(--edge-hi); }
.st-key-theme_toggle button:hover { border-color:var(--cyan); color:var(--cyan); }
.st-key-theme_toggle button p { color:inherit; }

/* status ribbon */
.sl-ribbon { display:flex; flex-wrap:wrap; gap:.8rem; align-items:center; justify-content:space-between; margin:.2rem 0 1rem; color:var(--muted); font-size:.82rem; }
.sl-ribbon-l, .sl-ribbon-r { display:flex; flex-wrap:wrap; align-items:center; gap:.7rem; }

/* tabs: glass pill bar with gradient active pill */
[role="tablist"] { gap:.3rem; padding:.35rem; width:fit-content; max-width:100%; overflow-x:auto; margin-bottom:1.1rem;
  background:var(--soft-3); border:1px solid var(--line); border-radius:999px; -webkit-backdrop-filter:blur(14px); backdrop-filter:blur(14px); }
[role="tab"] { height:2.4rem; padding:0 1.15rem; border-radius:999px; color:var(--muted); font-weight:600; background:transparent; }
[role="tab"] p { color:inherit; }
[role="tab"]:hover { color:var(--text); background:var(--soft-2); }
[role="tab"][aria-selected="true"] { background:var(--tab-grad) !important; box-shadow:0 6px 24px var(--tab-glow); }
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] p, [role="tab"][aria-selected="true"] span { color:var(--tab-fg) !important; }
[role="tab"] .react-aria-SelectionIndicator, [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; }

/* inputs */
[data-baseweb="select"] > div { background:var(--soft-2) !important; border-color:var(--line) !important; border-radius:12px !important; color:var(--text); }
[data-baseweb="select"] div, [data-baseweb="select"] input, [data-baseweb="select"] span { color:var(--text) !important; }
[data-baseweb="select"] svg { fill:var(--muted); }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul { background:var(--pop-bg) !important; }
[data-baseweb="popover"] li, [data-baseweb="popover"] li * { color:var(--text) !important; background:transparent; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background:var(--pop-hover) !important; }
[data-testid="stBaseButton-secondary"] { background:var(--soft-2); border:1px solid var(--line); border-radius:12px; color:var(--text); }
[data-testid="stBaseButton-secondary"]:hover { border-color:var(--cyan); color:var(--cyan); }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color:var(--muted) !important; font-size:.74rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }
[data-testid="stSegmentedControl"] button { color:var(--text); background:var(--soft-3); border-color:var(--line); }
[data-testid="stSegmentedControl"] button p { color:inherit; }
[data-testid="stAlert"] { background:var(--soft-2); border:1px solid var(--line); border-radius:12px; color:var(--text); }

/* badges and tags */
.sl-badge { display:inline-flex; align-items:center; gap:.4rem; padding:.18rem .6rem; border-radius:999px; font-size:.7rem; font-weight:700;
  letter-spacing:.05em; text-transform:uppercase; border:1px solid transparent; white-space:nowrap; }
.sl-badge.info { color:var(--cyan); background:color-mix(in srgb,var(--cyan) 12%,transparent); border-color:color-mix(in srgb,var(--cyan) 32%,transparent); }
.sl-badge.warn { color:var(--warn); background:color-mix(in srgb,var(--warn) 12%,transparent); border-color:color-mix(in srgb,var(--warn) 32%,transparent); }
.sl-badge.bad { color:var(--bad); background:color-mix(in srgb,var(--bad) 12%,transparent); border-color:color-mix(in srgb,var(--bad) 34%,transparent); }
.sl-badge.crit { color:var(--crit); background:color-mix(in srgb,var(--crit) 14%,transparent); border-color:color-mix(in srgb,var(--crit) 38%,transparent); }
.sl-badge.ok { color:var(--ok); background:color-mix(in srgb,var(--ok) 12%,transparent); border-color:color-mix(in srgb,var(--ok) 34%,transparent); }
.sl-badge.idle { color:var(--muted); background:color-mix(in srgb,var(--muted) 12%,transparent); border-color:color-mix(in srgb,var(--muted) 28%,transparent); }
.sl-dot { width:.55rem; height:.55rem; border-radius:50%; background:currentColor; display:inline-block; }
.sl-badge.ok .sl-dot { animation:sl-pulse 1.6s ease-out infinite; box-shadow:0 0 8px currentColor; }
@keyframes sl-pulse { 0% { box-shadow:0 0 0 0 color-mix(in srgb,var(--ok) 60%,transparent); } 100% { box-shadow:0 0 0 .6rem transparent; } }
.sl-tags { display:flex; flex-wrap:wrap; gap:.7rem; margin:.5rem 0 .4rem; }
.sl-tag { font-size:.68rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); }
.sl-tag.crit { color:var(--crit); } .sl-tag.bad { color:var(--bad); } .sl-tag.warn { color:var(--warn); } .sl-tag.info { color:var(--cyan); }

/* kpis */
.sl-kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.9rem; margin-bottom:1.2rem; }
.sl-kpi-label { color:var(--muted); font-size:.7rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; }
.sl-kpi-value { font-size:1.8rem; font-weight:800; line-height:1.2; margin-top:.2rem; font-variant-numeric:tabular-nums; color:var(--title); }
.sl-kpi-sub { color:var(--muted); font-size:.77rem; margin-top:.1rem; }
.sl-kpi.bad .sl-kpi-value { color:var(--crit); text-shadow:0 0 18px color-mix(in srgb,var(--crit) var(--glow),transparent); }
.sl-kpi.ok .sl-kpi-value { color:var(--ok); text-shadow:0 0 18px color-mix(in srgb,var(--ok) var(--glow),transparent); }
.sl-kpi.warn .sl-kpi-value { color:var(--warn); }
.sl-spark { display:flex; align-items:flex-end; gap:2px; height:30px; margin-top:.5rem; }
.sl-spark i { flex:1; min-height:2px; background:var(--c); opacity:.55; border-radius:2px 2px 0 0; }
.sl-spark i:last-child { opacity:1; }

/* panels */
.sl-panel-title { display:flex; align-items:center; justify-content:space-between; gap:.6rem; font-weight:700; font-size:1.02rem; color:var(--title); }
.sl-panel-cap { color:var(--muted); font-size:.8rem; line-height:1.45; margin:.2rem 0 .7rem; }
.sl-section { display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.05rem; margin:1.2rem 0 .7rem; color:var(--title); }
.sl-section::after { content:""; flex:1; height:1px; background:linear-gradient(90deg,var(--line),transparent); }
.sl-empty { color:var(--muted); text-align:center; padding:2.2rem 1rem; border:1px dashed var(--line); border-radius:12px; font-size:.9rem; }
.sl-kv { display:flex; justify-content:space-between; gap:1rem; padding:.55rem .7rem; margin-bottom:.4rem; border:1px solid var(--line); border-radius:10px;
  background:var(--soft); font-size:.88rem; }
.sl-kv span { color:var(--muted); } .sl-kv b { font-weight:600; text-align:right; word-break:break-all; color:var(--text); }
.sl-kv b.crit { color:var(--crit); } .sl-kv b.warn { color:var(--warn); } .sl-kv b.ok { color:var(--ok); }
.sl-insight { display:flex; gap:.9rem; align-items:flex-start; padding:.95rem 1.1rem; margin-bottom:1rem; border-radius:16px; font-size:.95rem; line-height:1.55;
  border:1px solid var(--line); border-left:4px solid var(--cyan); color:var(--text);
  background:linear-gradient(100deg,color-mix(in srgb,var(--cyan) 12%,transparent),color-mix(in srgb,var(--accent) 6%,transparent) 60%,transparent); }
.sl-insight .ic { flex:none; color:var(--cyan); margin-top:.2rem; } .sl-insight b { color:var(--title); } .sl-insight b.crit { color:var(--crit); }

/* tables */
.sl-table-wrap { overflow:auto; border-radius:12px; border:1px solid var(--line); }
.sl-table { width:100%; border-collapse:collapse; font-size:.82rem; }
.sl-table th { text-align:left; padding:.5rem .7rem; background:var(--head-bg); color:var(--muted); font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; }
.sl-table td { padding:.5rem .7rem; border-top:1px solid var(--row-line); color:var(--text); white-space:nowrap; }
.sl-table td.num { text-align:right; font-variant-numeric:tabular-nums; } .sl-table td.mono { font-family:ui-monospace,Consolas,monospace; color:var(--code); }
.sl-table tr:hover td { background:var(--soft); }

/* incident cards (event management style) */
.sl-incidents { display:grid; grid-template-columns:repeat(auto-fit,minmax(310px,1fr)); gap:.9rem; }
.sl-incident h4 { margin:0; font-size:1.02rem; font-weight:700; color:var(--title); }
.sl-incident p { margin:.4rem 0 0; color:var(--muted); font-size:.85rem; line-height:1.45; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.sl-incident-top { display:flex; justify-content:space-between; align-items:flex-start; gap:.6rem; }
.sl-incident-meta { display:flex; flex-wrap:wrap; gap:.4rem 1rem; color:var(--muted); font-size:.75rem; }
.sl-incident code, .sl-hotip code { font-family:ui-monospace,Consolas,monospace; background:none; color:var(--code); }
.sl-incident.hot { border-color:color-mix(in srgb,var(--crit) 75%,transparent) !important;
  box-shadow:0 0 0 1px color-mix(in srgb,var(--crit) 25%,transparent), 0 0 40px color-mix(in srgb,var(--crit) 22%,transparent), inset 0 1px 0 var(--edge-hi); }
.sl-hotip { margin-top:.7rem; font-weight:800; color:var(--crit); font-size:1rem; }
.sl-hotip code { color:var(--hot-ip); font-size:1.05rem; }

/* incident detail */
.sl-detail-head h2 { margin:.5rem 0 .2rem; font-size:1.5rem; color:var(--title); }
.sl-detail-head p { color:var(--muted); margin:0 0 .9rem; }
.sl-meta-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:.8rem; font-size:.8rem; color:var(--muted); }
.sl-meta-row b { display:block; color:var(--text); font-size:.92rem; font-family:ui-monospace,Consolas,monospace; margin-top:.1rem; }
.sl-tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:.7rem; }
.sl-tile { display:flex; align-items:center; gap:.8rem; padding:.8rem .9rem; border:1px solid var(--line); border-radius:12px; background:var(--soft); }
.sl-ico { width:40px; height:40px; flex:none; display:grid; place-items:center; border-radius:10px; color:var(--ok);
  background:color-mix(in srgb,var(--ok) 12%,transparent); border:1px solid color-mix(in srgb,var(--ok) 28%,transparent); }
.sl-ico.crit { color:var(--crit); background:color-mix(in srgb,var(--crit) 12%,transparent); border-color:color-mix(in srgb,var(--crit) 30%,transparent); }
.sl-ico.warn { color:var(--warn); background:color-mix(in srgb,var(--warn) 12%,transparent); border-color:color-mix(in srgb,var(--warn) 30%,transparent); }
.sl-tile small { display:block; color:var(--muted); font-size:.72rem; } .sl-tile b { font-size:.95rem; color:var(--text); }
.sl-actions .sl-act { display:flex; gap:.7rem; align-items:center; padding:.65rem .8rem; margin-bottom:.45rem; border:1px solid var(--line); border-radius:10px;
  background:var(--soft); font-size:.88rem; color:var(--text); }
.sl-act .ic { color:var(--warn); flex:none; }

/* pipeline flow */
.sl-flow { display:flex; align-items:stretch; gap:.6rem; margin:.2rem 0 1rem; }
.sl-stage { flex:1 1 0; min-width:0; }
.sl-step { color:var(--muted); font-size:.7rem; font-weight:800; letter-spacing:.12em; }
.sl-stage-title { font-weight:700; margin:.15rem 0 .5rem; display:flex; align-items:center; gap:.5rem; color:var(--text); }
.sl-stage-value { font-size:1.6rem; font-weight:800; font-variant-numeric:tabular-nums; color:var(--title); }
.sl-stage-cap { color:var(--muted); font-size:.78rem; }
.sl-stage .sl-dot { color:var(--muted); }
.sl-stage.ok .sl-dot { color:var(--ok); box-shadow:0 0 8px var(--ok); } .sl-stage.warn .sl-dot { color:var(--warn); } .sl-stage.bad .sl-dot { color:var(--crit); }
.sl-stage.ok { border-top:3px solid var(--ok); } .sl-stage.warn { border-top:3px solid var(--warn); }
.sl-stage.bad { border-top:3px solid var(--crit); } .sl-stage.idle { border-top:3px solid var(--line); }
.sl-arrow { display:flex; align-items:center; color:var(--cyan); }
.sl-branch { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; color:var(--muted); font-size:.85rem; margin-bottom:1rem; }

/* live event table */
.sl-feed { max-height:460px; overflow:auto; font-size:.82rem; border-radius:12px; color:var(--text); }
.sl-row { display:grid; grid-template-columns:78px 88px 150px 120px minmax(0,1fr) 52px; gap:.7rem; align-items:center;
  padding:.45rem .6rem; border-bottom:1px solid var(--row-line); border-left:3px solid transparent; }
.sl-row > span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sl-row .t, .sl-row .src { font-family:ui-monospace,Consolas,monospace; color:var(--muted); }
.sl-row .score { text-align:right; font-variant-numeric:tabular-nums; color:var(--muted); }
.sl-row.anomaly { background:color-mix(in srgb,var(--crit) 9%,transparent); border-left-color:var(--crit); }
.sl-row.anomaly .score { color:var(--crit); font-weight:700; }
.sl-row.new { animation:sl-flash 2.4s ease-out 1; }
@keyframes sl-flash { from { background:var(--flash); } to { background:transparent; } }
.sl-head { position:sticky; top:0; z-index:1; background:var(--head-bg); color:var(--muted); font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.sl-raw { border:1px solid var(--line); border-radius:10px; padding:.55rem .7rem; margin-bottom:.5rem; background:var(--raw-bg); }
.sl-raw .r { display:flex; justify-content:space-between; gap:.5rem; font-size:.8rem; margin-bottom:.3rem; color:var(--muted); }
.sl-raw code { display:block; white-space:pre-wrap; word-break:break-all; font-size:.76rem; color:var(--text); background:none; }

/* responsive */
@media (max-width: 900px) {
  .block-container { padding:3.2rem .9rem 2rem; }
  .sl-flow { flex-direction:column; } .sl-stage { flex:0 0 auto; }
  .sl-arrow { justify-content:center; transform:rotate(90deg); height:1.4rem; }
  .sl-row { grid-template-columns:64px 78px minmax(0,1fr) 44px; gap:.5rem; }
  .sl-row .type, .sl-row .src { display:none; }
  [role="tablist"] { border-radius:18px; }
}
@media (max-width: 520px) {
  .sl-kpis { grid-template-columns:repeat(2,minmax(0,1fr)); gap:.6rem; }
  .sl-kpi-value { font-size:1.4rem; } .sl-card { padding:.8rem; }
  .sl-incidents { grid-template-columns:1fr; }
}
"""


def inject() -> None:
    st.html(f"<style>{_variables(palette())}\n{CSS}\n{icon_css()}</style><span class='sl-css'></span>")
