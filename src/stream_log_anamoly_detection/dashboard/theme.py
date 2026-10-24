"""Design tokens and global CSS for the dashboard: dark, glassy, neon accents, responsive."""

import streamlit as st
from urllib.parse import quote

TEXT, MUTED, BORDER = "#e8ecff", "#8d97bd", "#2a3158"
ACCENT, CYAN, OK, WARN, BAD, CRIT = "#818cf8", "#67e8f9", "#a3e635", "#fbbf24", "#fb923c", "#ff4d6d"
SEVERITY_COLORS = {"INFO": CYAN, "WARNING": WARN, "ERROR": BAD, "CRITICAL": CRIT}

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


def icon_css() -> str:
    rules = [".ic { display:inline-block; width:1em; height:1em; flex:none; background:currentColor; vertical-align:-.15em;"
             " -webkit-mask:var(--i) center/contain no-repeat; mask:var(--i) center/contain no-repeat; }"]
    for name, body in ICONS.items():
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' "
               f"stroke-linecap='round' stroke-linejoin='round'>{body.replace(chr(34), chr(39))}</svg>")
        rules.append(f'.ic-{name} {{ --i:url("data:image/svg+xml,{quote(svg, safe="")}"); }}')
    return "\n".join(rules)

CSS = """
:root { --bg:#050816; --border:rgba(148,163,255,.18); --text:#e8ecff; --muted:#8d97bd; --accent:#818cf8; --cyan:#67e8f9;
  --ok:#a3e635; --warn:#fbbf24; --bad:#fb923c; --crit:#ff4d6d; }
[data-testid="stElementContainer"]:has(.sl-css) { display:none; }
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] { display:none !important; }
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(900px 520px at 10% -6%, rgba(99,102,241,.30), transparent 60%),
    radial-gradient(800px 480px at 96% 4%, rgba(34,211,238,.17), transparent 55%),
    radial-gradient(700px 520px at 50% 112%, rgba(163,230,53,.07), transparent 60%),
    linear-gradient(180deg,#050816,#070b1f); }
[data-testid="stAppViewContainer"]::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:linear-gradient(rgba(129,140,248,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(129,140,248,.06) 1px,transparent 1px);
  background-size:46px 46px; -webkit-mask-image:radial-gradient(ellipse at 50% 0%,#000 25%,transparent 75%); mask-image:radial-gradient(ellipse at 50% 0%,#000 25%,transparent 75%); }
[data-testid="stHeader"] { background:transparent; }
.block-container { position:relative; z-index:1; max-width:1440px; padding:3.4rem 2rem 3rem; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3 { letter-spacing:-.01em; }

/* glass surfaces */
.sl-card, [data-testid="stVerticalBlockBorderWrapper"] {
  background:linear-gradient(135deg,rgba(255,255,255,.075),rgba(255,255,255,.02)) !important;
  -webkit-backdrop-filter:blur(16px) saturate(150%); backdrop-filter:blur(16px) saturate(150%);
  border:1px solid var(--border) !important; border-radius:16px !important;
  box-shadow:0 10px 40px rgba(2,6,23,.45), inset 0 1px 0 rgba(255,255,255,.09); }
.sl-card { padding:1rem 1.1rem; position:relative; overflow:hidden; }
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] { box-shadow:none; }

/* brand header bar */
.sl-brand { display:flex; flex-wrap:wrap; gap:1rem; align-items:center; justify-content:space-between; padding:.9rem 1.2rem; margin-bottom:1rem;
  border-radius:18px; border:1px solid rgba(165,180,252,.28);
  background:linear-gradient(100deg,rgba(49,46,129,.85),rgba(30,64,175,.55) 55%,rgba(8,145,178,.45));
  -webkit-backdrop-filter:blur(18px); backdrop-filter:blur(18px); box-shadow:0 14px 50px rgba(30,41,140,.35), inset 0 1px 0 rgba(255,255,255,.14); }
.sl-brand-l { display:flex; align-items:center; gap:.9rem; }
.sl-logo { width:46px; height:46px; border-radius:50%; display:grid; place-items:center; color:#a5f3fc;
  background:radial-gradient(circle at 30% 25%,rgba(103,232,249,.35),rgba(79,70,229,.35)); border:1px solid rgba(165,243,252,.4); box-shadow:0 0 24px rgba(103,232,249,.35); }
.sl-title { font-size:clamp(1.15rem,2.2vw,1.55rem); font-weight:800; line-height:1.15; color:#fff; }
.sl-sub { color:#b4bdf0; font-size:.85rem; margin-top:.15rem; }
.sl-chips { display:flex; flex-wrap:wrap; gap:.5rem; }
.sl-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.28rem .75rem; border-radius:999px; font-size:.78rem; color:#dbe2ff;
  background:rgba(8,12,40,.55); border:1px solid rgba(165,180,252,.25); }
.sl-chip b { color:#fff; font-weight:700; }
.sl-chip.alert svg { color:var(--ok); } .sl-chip.crit svg { color:var(--crit); }

/* status ribbon */
.sl-ribbon { display:flex; flex-wrap:wrap; gap:.8rem; align-items:center; justify-content:space-between; margin:.2rem 0 1rem; color:var(--muted); font-size:.82rem; }
.sl-ribbon-l, .sl-ribbon-r { display:flex; flex-wrap:wrap; align-items:center; gap:.7rem; }

/* tabs: glass pill bar with gradient active pill */
[role="tablist"] { gap:.3rem; padding:.35rem; width:fit-content; max-width:100%; overflow-x:auto; margin-bottom:1.1rem;
  background:rgba(255,255,255,.045); border:1px solid var(--border); border-radius:999px; -webkit-backdrop-filter:blur(14px); backdrop-filter:blur(14px); }
[role="tab"] { height:2.4rem; padding:0 1.15rem; border-radius:999px; color:var(--muted); font-weight:600; background:transparent; }
[role="tab"]:hover { color:var(--text); background:rgba(255,255,255,.05); }
[role="tab"][aria-selected="true"] { background:linear-gradient(90deg,#818cf8,#67e8f9) !important; box-shadow:0 6px 24px rgba(103,232,249,.38); }
[role="tab"][aria-selected="true"], [role="tab"][aria-selected="true"] p, [role="tab"][aria-selected="true"] span { color:#06102a !important; }
[role="tab"] .react-aria-SelectionIndicator, [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display:none !important; }

/* inputs */
[data-baseweb="select"] > div { background:rgba(255,255,255,.05) !important; border-color:var(--border) !important; border-radius:12px !important; }
[data-testid="stBaseButton-secondary"] { background:rgba(255,255,255,.06); border:1px solid var(--border); border-radius:12px; color:var(--text); }
[data-testid="stBaseButton-secondary"]:hover { border-color:var(--cyan); color:var(--cyan); }
[data-testid="stWidgetLabel"] p { color:var(--muted); font-size:.74rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase; }

/* badges and tags */
.sl-badge { display:inline-flex; align-items:center; gap:.4rem; padding:.18rem .6rem; border-radius:999px; font-size:.7rem; font-weight:700;
  letter-spacing:.05em; text-transform:uppercase; border:1px solid transparent; white-space:nowrap; }
.sl-badge.info { color:var(--cyan); background:rgba(103,232,249,.10); border-color:rgba(103,232,249,.28); }
.sl-badge.warn { color:var(--warn); background:rgba(251,191,36,.10); border-color:rgba(251,191,36,.28); }
.sl-badge.bad { color:var(--bad); background:rgba(251,146,60,.12); border-color:rgba(251,146,60,.32); }
.sl-badge.crit { color:var(--crit); background:rgba(255,77,109,.14); border-color:rgba(255,77,109,.38); }
.sl-badge.ok { color:var(--ok); background:rgba(163,230,53,.10); border-color:rgba(163,230,53,.30); }
.sl-badge.idle { color:var(--muted); background:rgba(141,151,189,.10); border-color:rgba(141,151,189,.25); }
.sl-dot { width:.55rem; height:.55rem; border-radius:50%; background:currentColor; display:inline-block; }
.sl-badge.ok .sl-dot { animation:sl-pulse 1.6s ease-out infinite; box-shadow:0 0 8px currentColor; }
@keyframes sl-pulse { 0% { box-shadow:0 0 0 0 rgba(163,230,53,.6); } 100% { box-shadow:0 0 0 .6rem rgba(163,230,53,0); } }
.sl-tags { display:flex; flex-wrap:wrap; gap:.7rem; margin:.5rem 0 .4rem; }
.sl-tag { font-size:.68rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); }
.sl-tag.crit { color:var(--crit); } .sl-tag.bad { color:var(--bad); } .sl-tag.warn { color:var(--warn); } .sl-tag.info { color:var(--cyan); }

/* kpis */
.sl-kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.9rem; margin-bottom:1.2rem; }
.sl-kpi-label { color:var(--muted); font-size:.7rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; }
.sl-kpi-value { font-size:1.8rem; font-weight:800; line-height:1.2; margin-top:.2rem; font-variant-numeric:tabular-nums; }
.sl-kpi-sub { color:var(--muted); font-size:.77rem; margin-top:.1rem; }
.sl-kpi.bad .sl-kpi-value { color:var(--crit); text-shadow:0 0 18px rgba(255,77,109,.45); }
.sl-kpi.ok .sl-kpi-value { color:var(--ok); text-shadow:0 0 18px rgba(163,230,53,.35); }
.sl-kpi.warn .sl-kpi-value { color:var(--warn); }
.sl-spark { display:flex; align-items:flex-end; gap:2px; height:30px; margin-top:.5rem; }
.sl-spark i { flex:1; min-height:2px; background:var(--c); opacity:.55; border-radius:2px 2px 0 0; }
.sl-spark i:last-child { opacity:1; }

/* panels */
.sl-panel-title { display:flex; align-items:center; justify-content:space-between; gap:.6rem; font-weight:700; font-size:1.02rem; }
.sl-panel-cap { color:var(--muted); font-size:.8rem; line-height:1.45; margin:.2rem 0 .7rem; }
.sl-section { display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.05rem; margin:1.2rem 0 .7rem; }
.sl-section::after { content:""; flex:1; height:1px; background:linear-gradient(90deg,var(--border),transparent); }
.sl-empty { color:var(--muted); text-align:center; padding:2.2rem 1rem; border:1px dashed var(--border); border-radius:12px; font-size:.9rem; }
.sl-kv { display:flex; justify-content:space-between; gap:1rem; padding:.55rem .7rem; margin-bottom:.4rem; border:1px solid var(--border); border-radius:10px;
  background:rgba(255,255,255,.03); font-size:.88rem; }
.sl-kv span { color:var(--muted); } .sl-kv b { font-weight:600; text-align:right; word-break:break-all; }
.sl-kv b.crit { color:var(--crit); } .sl-kv b.warn { color:var(--warn); } .sl-kv b.ok { color:var(--ok); }
.sl-insight { display:flex; gap:.9rem; align-items:flex-start; padding:.95rem 1.1rem; margin-bottom:1rem; border-radius:16px; font-size:.95rem; line-height:1.55;
  border:1px solid var(--border); border-left:4px solid var(--cyan);
  background:linear-gradient(100deg,rgba(103,232,249,.10),rgba(129,140,248,.05) 60%,transparent); }
.sl-insight svg { flex:none; color:var(--cyan); margin-top:.2rem; } .sl-insight b { color:#fff; } .sl-insight b.crit { color:var(--crit); }

/* incident cards (event management style) */
.sl-incidents { display:grid; grid-template-columns:repeat(auto-fit,minmax(310px,1fr)); gap:.9rem; }
.sl-incident h4 { margin:0; font-size:1.02rem; font-weight:700; color:#fff; }
.sl-incident p { margin:.4rem 0 0; color:var(--muted); font-size:.85rem; line-height:1.45; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.sl-incident-top { display:flex; justify-content:space-between; align-items:flex-start; gap:.6rem; }
.sl-incident-meta { display:flex; flex-wrap:wrap; gap:.4rem 1rem; color:var(--muted); font-size:.75rem; }
.sl-incident code, .sl-hotip code { font-family:ui-monospace,Consolas,monospace; background:none; color:#cbd5ff; }
.sl-incident.hot { border-color:rgba(255,77,109,.75) !important; box-shadow:0 0 0 1px rgba(255,77,109,.25), 0 0 40px rgba(255,77,109,.22), inset 0 1px 0 rgba(255,255,255,.08); }
.sl-hotip { margin-top:.7rem; font-weight:800; color:var(--crit); font-size:1rem; }
.sl-hotip code { color:#ff8fa3; font-size:1.05rem; }

/* incident detail */
.sl-detail-head h2 { margin:.5rem 0 .2rem; font-size:1.5rem; color:#fff; }
.sl-detail-head p { color:var(--muted); margin:0 0 .9rem; }
.sl-meta-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:.8rem; font-size:.8rem; color:var(--muted); }
.sl-meta-row b { display:block; color:var(--text); font-size:.92rem; font-family:ui-monospace,Consolas,monospace; margin-top:.1rem; }
.sl-tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:.7rem; }
.sl-tile { display:flex; align-items:center; gap:.8rem; padding:.8rem .9rem; border:1px solid var(--border); border-radius:12px; background:rgba(255,255,255,.03); }
.sl-ico { width:40px; height:40px; flex:none; display:grid; place-items:center; border-radius:10px; color:var(--ok); background:rgba(163,230,53,.10); border:1px solid rgba(163,230,53,.25); }
.sl-ico.crit { color:var(--crit); background:rgba(255,77,109,.10); border-color:rgba(255,77,109,.3); }
.sl-ico.warn { color:var(--warn); background:rgba(251,191,36,.10); border-color:rgba(251,191,36,.3); }
.sl-tile small { display:block; color:var(--muted); font-size:.72rem; } .sl-tile b { font-size:.95rem; }
.sl-actions .sl-act { display:flex; gap:.7rem; align-items:center; padding:.65rem .8rem; margin-bottom:.45rem; border:1px solid var(--border); border-radius:10px;
  background:rgba(255,255,255,.03); font-size:.88rem; }
.sl-act svg { color:var(--warn); flex:none; }

/* pipeline flow */
.sl-flow { display:flex; align-items:stretch; gap:.6rem; margin:.2rem 0 1rem; }
.sl-stage { flex:1 1 0; min-width:0; }
.sl-step { color:var(--muted); font-size:.7rem; font-weight:800; letter-spacing:.12em; }
.sl-stage-title { font-weight:700; margin:.15rem 0 .5rem; display:flex; align-items:center; gap:.5rem; }
.sl-stage-value { font-size:1.6rem; font-weight:800; font-variant-numeric:tabular-nums; }
.sl-stage-cap { color:var(--muted); font-size:.78rem; }
.sl-stage .sl-dot { color:var(--muted); }
.sl-stage.ok .sl-dot { color:var(--ok); box-shadow:0 0 8px var(--ok); } .sl-stage.warn .sl-dot { color:var(--warn); } .sl-stage.bad .sl-dot { color:var(--crit); }
.sl-stage.ok { border-top:3px solid var(--ok); } .sl-stage.warn { border-top:3px solid var(--warn); }
.sl-stage.bad { border-top:3px solid var(--crit); } .sl-stage.idle { border-top:3px solid var(--border); }
.sl-arrow { display:flex; align-items:center; color:var(--cyan); }
.sl-branch { display:flex; flex-wrap:wrap; gap:.6rem; align-items:center; color:var(--muted); font-size:.85rem; margin-bottom:1rem; }

/* live event table */
.sl-feed { max-height:460px; overflow:auto; font-size:.82rem; border-radius:12px; }
.sl-row { display:grid; grid-template-columns:78px 88px 150px 120px minmax(0,1fr) 52px; gap:.7rem; align-items:center;
  padding:.45rem .6rem; border-bottom:1px solid rgba(148,163,255,.10); border-left:3px solid transparent; }
.sl-row > span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sl-row .t, .sl-row .src { font-family:ui-monospace,Consolas,monospace; color:var(--muted); }
.sl-row .score { text-align:right; font-variant-numeric:tabular-nums; color:var(--muted); }
.sl-row.anomaly { background:rgba(255,77,109,.09); border-left-color:var(--crit); }
.sl-row.anomaly .score { color:var(--crit); font-weight:700; }
.sl-row.new { animation:sl-flash 2.4s ease-out 1; }
@keyframes sl-flash { from { background:rgba(103,232,249,.30); } to { background:transparent; } }
.sl-head { position:sticky; top:0; z-index:1; background:rgba(9,13,38,.92); color:var(--muted); font-size:.68rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.sl-raw { border:1px solid var(--border); border-radius:10px; padding:.55rem .7rem; margin-bottom:.5rem; background:rgba(0,0,0,.2); }
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
    st.html(f"<style>{CSS}\n{icon_css()}</style><span class='sl-css'></span>")
