import streamlit as st
import streamlit.components.v1 as components

CUSTOM_CSS = """
<style>
    /* ── Google Font ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Root variables ──────────────────────────────────────── */
    :root {
        --bg-primary: #ffffff;
        --bg-card: #f4f6f9;
        --bg-card-hover: #ffffff;
        --border-card: rgba(30, 58, 95, 0.1);
        --border-glow: rgba(0, 180, 216, 0.3);
        --text-primary: #111111;
        --text-secondary: #1a1a1a;
        --text-muted: #4b5563;
        --accent-1: #1e3a5f; /* deep blue */
        --accent-2: #00b4d8; /* turquoise */
        --accent-3: #2d9e6b; /* emerald green */
        --accent-4: #6c63ff; /* soft violet */
        --gradient-1: linear-gradient(135deg, #1e3a5f, #6c63ff);
        --gradient-2: linear-gradient(135deg, #00b4d8, #2d9e6b);
        --gradient-3: linear-gradient(135deg, #6c63ff, #f472b6);
        --gradient-4: linear-gradient(135deg, #2d9e6b, #1e3a5f);
        --shadow-soft: 0 4px 12px rgba(0, 0, 0, 0.05);
        --shadow-hover: 0 8px 24px rgba(30, 58, 95, 0.12);
    }

    /* ── Global background ───────────────────────────────────── */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    /* ── Sidebar ─────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #fdfdfd;
        border-right: 1px solid var(--border-card);
    }
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--accent-1) !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    section[data-testid="stSidebar"] .stSelectbox label {
        color: var(--text-secondary) !important;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.75rem;
    }

    /* ── Hide default hamburger & footer ──────────────────────  */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Layout margins ──────────────────────────────────────── */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 1rem !important;
    }

    /* ── Custom scrollbar ────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-card); }
    ::-webkit-scrollbar-thumb { background: var(--border-card); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-2); }

    /* ── Card containers ─────────────────────────────────────── */
    .glass-card {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 16px;
        padding: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-soft);
    }
    .glass-card:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-glow);
        box-shadow: var(--shadow-hover);
    }

    /* ── KPI metric cards ────────────────────────────────────── */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(2, minmax(180px, 1fr));
        gap: 1.2rem;
        margin-bottom: 1.5rem;
        width: min(100%, 980px);
        margin-left: auto;
        margin-right: auto;
    }
    .kpi-card {
        aspect-ratio: 1;
        max-width: 280px;
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.35s ease;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: var(--shadow-soft);
    }

    @media (min-width: 1250px) {
        .kpi-container {
            grid-template-columns: repeat(4, minmax(160px, 1fr));
            width: min(100%, 1200px);
        }
    }
    .kpi-container > .kpi-card:nth-child(odd) {
        margin-right: 0;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: var(--accent-2);
        background: var(--bg-card-hover);
        box-shadow: var(--shadow-hover);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        border-radius: 14px 14px 0 0;
    }
    .kpi-card:nth-child(1)::before { background: var(--gradient-1); }
    .kpi-card:nth-child(2)::before { background: var(--gradient-2); }
    .kpi-card:nth-child(3)::before { background: var(--gradient-3); }
    .kpi-card:nth-child(4)::before { background: var(--gradient-4); }

    .kpi-icon { font-size: 1.6rem; margin-bottom: 0.3rem; }
    .kpi-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
        word-break: break-word;
    }
    .kpi-card:nth-child(1) .kpi-value { color: var(--accent-1); }
    .kpi-card:nth-child(2) .kpi-value { color: var(--accent-2); }
    .kpi-card:nth-child(3) .kpi-value { color: var(--accent-4); }
    .kpi-card:nth-child(4) .kpi-value { color: var(--accent-3); }

    .kpi-sub {
        font-size: 0.72rem;
        color: var(--text-secondary);
        margin-top: 0.35rem;
        font-weight: 500;
    }


    /* ── Section titles ──────────────────────────────────────── */
    .section-title {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.2rem;
    }
    .section-title .icon {
        font-size: 1.2rem;
        width: 2.6rem;
        height: 2.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        flex-shrink: 0;
        box-shadow: var(--shadow-soft);
    }
    .section-title .icon.purple { background: rgba(108, 99, 255, 0.1); color: var(--accent-4); border: 1px solid rgba(108, 99, 255, 0.2); }
    .section-title .icon.cyan   { background: rgba(0, 180, 216, 0.1); color: var(--accent-2); border: 1px solid rgba(0, 180, 216, 0.2); }
    .section-title .icon.pink   { background: rgba(30, 58, 95, 0.1); color: var(--accent-1); border: 1px solid rgba(30, 58, 95, 0.2); }
    .section-title .icon.yellow { background: rgba(45, 158, 107, 0.1); color: var(--accent-3); border: 1px solid rgba(45, 158, 107, 0.2); }

    .section-title h3 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        color: var(--accent-1) !important;
        letter-spacing: -0.01em;
        flex: 1;
        min-width: 150px;
    }
    .section-title .badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        background: rgba(30, 58, 95, 0.08);
        color: var(--accent-1);
        margin-left: auto;
        flex-shrink: 0;
        border: 1px solid rgba(30, 58, 95, 0.15);
    }

    @media (max-width: 768px) {
        .section-title { gap: 0.5rem; margin-bottom: 0.8rem; }
        .section-title .icon { font-size: 1.1rem; width: 2.1rem; height: 2.1rem; }
        .section-title h3 { font-size: 1rem !important; min-width: 120px; }
        .section-title .badge { font-size: 0.6rem; padding: 0.15rem 0.5rem; }
    }

    @media (max-width: 480px) {
        .section-title { gap: 0.4rem; }
        .section-title .icon { font-size: 0.95rem; width: 1.9rem; height: 1.9rem; }
        .section-title h3 { font-size: 0.9rem !important; min-width: auto; }
        .section-title .badge { width: 100%; text-align: center; font-size: 0.55rem; margin-left: 0; margin-top: 0.3rem; }
    }

    /* ── Hero header ─────────────────────────────────────────── */
    .hero {
        text-align: center;
        padding: 2.5rem 0 1.5rem 0;
    }
    .hero h1 {
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        line-height: 1.15;
    }
    .hero p {
        color: var(--text-secondary);
        font-size: 0.95rem;
        font-weight: 400;
        max-width: 650px;
        margin: 0 auto;
        line-height: 1.6;
    }
    .hero .tag {
        display: inline-block;
        margin-top: 0.8rem;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.35rem 1rem;
        border-radius: 999px;
        background: rgba(0, 180, 216, 0.1);
        color: var(--accent-2);
        border: 1px solid rgba(0, 180, 216, 0.25);
    }

    /* ── Plotly chart containers ──────────────────────────────── */
    .stPlotlyChart {
        border-radius: 12px;
        overflow: hidden;
        width: 100% !important;
        box-shadow: var(--shadow-soft);
        background: #0f172a;
    }

    /* ── Dividers ─────────────────────────────────────────────── */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border-card), transparent);
        margin: 2rem 0;
    }

    /* ── Tip box ──────────────────────────────────────────────── */
    .tip-box {
        background: rgba(45, 158, 107, 0.05);
        border: 1px solid rgba(45, 158, 107, 0.2);
        border-radius: 12px;
        padding: 0.8rem 1.2rem;
        font-size: 0.82rem;
        color: var(--text-secondary);
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        box-shadow: var(--shadow-soft);
    }
    .tip-box .tip-icon { font-size: 1.2rem; color: var(--accent-3); }

    /* ── Streamlit Native UI Adjustments ──────────────────────── */
    div.stButton > button {
        background: var(--bg-card);
        color: var(--accent-1);
        border: 1px solid var(--border-card);
        box-shadow: var(--shadow-soft);
        font-weight: 600;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background: var(--accent-1);
        color: #fff;
        border-color: var(--accent-1);
        box-shadow: var(--shadow-hover);
    }

    /* ── Footer / Glossary ────────────────────────────────────── */
    .glossary-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1.2rem;
        margin-top: 1rem;
    }
    .glossary-card {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 16px;
        padding: 1.5rem;
        min-height: 142px;
        box-shadow: var(--shadow-soft);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .glossary-card:hover {
        transform: translateY(-4px);
        background: var(--bg-card-hover);
        border-color: var(--accent-2);
        box-shadow: var(--shadow-hover);
    }
    .glossary-card-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 1rem;
    }
    .glossary-card-icon {
        font-size: 1.1rem;
        line-height: 1;
        color: var(--accent-1);
    }
    .glossary-card h4 {
        margin: 0 !important;
        font-size: 1rem !important;
        font-weight: 800 !important;
        line-height: 1.3;
        color: var(--accent-1) !important;
        letter-spacing: -0.01em;
    }
    .glossary-card p {
        margin: 0 !important;
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
        line-height: 1.6;
    }

    @media (max-width: 1100px) {
        .glossary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

    @media (max-width: 768px) {
        .glossary-grid { grid-template-columns: 1fr; gap: 1rem; }
        .glossary-card { min-height: auto; padding: 1.2rem; }
        .glossary-card h4 { font-size: 0.95rem !important; }
        .glossary-card p { font-size: 0.85rem !important; }
    }

    @media (max-width: 480px) {
        .glossary-card-icon { font-size: 0.9rem; }
        .glossary-card h4 { font-size: 0.9rem !important; }
        .glossary-card p { font-size: 0.85rem !important; line-height: 1.5; }
    }

    /* ── Responsive adjustments ──────────────────────────────── */
    @media (max-width: 768px) {
        .tip-box { padding: 0.7rem 1rem; font-size: 0.75rem; gap: 0.5rem; }
        .tip-box .tip-icon { font-size: 1rem; flex-shrink: 0; }
    }
    @media (max-width: 480px) {
        .tip-box { padding: 0.6rem 0.8rem; font-size: 0.7rem; }
        .tip-box .tip-icon { font-size: 0.9rem; }
    }
    @media (max-width: 768px) {
        .block-container { padding-top: 1.5rem !important; padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
    }
    @media (max-width: 480px) {
        .block-container { padding-top: 1rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    }

    .dashboard-footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: var(--text-muted);
        font-size: 0.75rem;
    }
    .dashboard-footer a { color: var(--accent-1); text-decoration: none; font-weight: 600; }

    @media (max-width: 768px) {
        .dashboard-footer { padding: 1.5rem 0 0.75rem 0; font-size: 0.7rem; }
    }
    @media (max-width: 480px) {
        .dashboard-footer { padding: 1rem 0 0.5rem 0; font-size: 0.65rem; }
    }

    .startup-target-text { color: #000000; }

    /* ═══════════════════════════════════════════════��══════════
       ── DETAIL VIEW – navegación interna dinámica ───────────
       ══════════════════════════════════════════════════════════ */

    /* Breadcrumb / back-bar */
    .detail-breadcrumb {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.78rem;
        color: var(--text-muted);
        margin-bottom: 1.6rem;
        flex-wrap: wrap;
    }
    .detail-breadcrumb .bc-home {
        color: var(--accent-1);
        font-weight: 600;
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 2px;
    }
    .detail-breadcrumb .bc-sep { opacity: 0.45; }
    .detail-breadcrumb .bc-current {
        font-weight: 700;
        color: var(--text-primary);
    }

    /* Detail hero strip */
    .detail-hero {
        background: linear-gradient(135deg, #1e3a5f 0%, #6c63ff 100%);
        border-radius: 18px;
        padding: 2rem 2.4rem;
        margin-bottom: 1.8rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        box-shadow: 0 8px 32px rgba(30, 58, 95, 0.18);
    }
    .detail-hero.cyan  { background: linear-gradient(135deg, #00b4d8 0%, #2d9e6b 100%); }
    .detail-hero.violet { background: linear-gradient(135deg, #6c63ff 0%, #f472b6 100%); }
    .detail-hero.green  { background: linear-gradient(135deg, #2d9e6b 0%, #1e3a5f 100%); }

    .detail-hero .dh-eyebrow {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.7);
    }
    .detail-hero .dh-title {
        font-size: 2rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        color: #ffffff;
        line-height: 1.15;
    }
    .detail-hero .dh-value {
        font-size: 3rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        color: #ffffff;
        line-height: 1;
        margin-top: 0.3rem;
    }
    .detail-hero .dh-sub {
        font-size: 0.88rem;
        color: rgba(255,255,255,0.75);
        font-weight: 500;
        margin-top: 0.15rem;
    }

    @media (max-width: 768px) {
        .detail-hero { padding: 1.5rem 1.6rem; }
        .detail-hero .dh-title { font-size: 1.4rem; }
        .detail-hero .dh-value { font-size: 2.2rem; }
    }

    /* Stats grid inside detail */
    .detail-stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.6rem;
    }
    @media (max-width: 900px) {
        .detail-stats-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 560px) {
        .detail-stats-grid { grid-template-columns: 1fr; }
    }

    .detail-stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border-card);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        box-shadow: var(--shadow-soft);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .detail-stat-card:hover {
        transform: translateY(-3px);
        box-shadow: var(--shadow-hover);
        border-color: var(--border-glow);
    }
    .detail-stat-card .dsc-label {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 0.45rem;
    }
    .detail-stat-card .dsc-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--accent-1);
        line-height: 1.15;
        letter-spacing: -0.02em;
    }
    .detail-stat-card .dsc-note {
        font-size: 0.72rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }

    /* Insight box */
    .detail-insight {
        background: rgba(0, 180, 216, 0.04);
        border: 1px solid rgba(0, 180, 216, 0.2);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.6rem;
        display: flex;
        gap: 0.8rem;
        align-items: flex-start;
    }
    .detail-insight .di-icon {
        font-size: 1.4rem;
        flex-shrink: 0;
        margin-top: 0.1rem;
    }
    .detail-insight .di-body { flex: 1; }
    .detail-insight .di-body strong {
        display: block;
        font-size: 0.88rem;
        font-weight: 800;
        color: var(--accent-1);
        margin-bottom: 0.3rem;
    }
    .detail-insight .di-body p {
        margin: 0;
        font-size: 0.84rem;
        color: var(--text-secondary);
        line-height: 1.55;
    }

    div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] {
        max-width: 100%;
        overflow-x: hidden;
    }
    div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] div[data-testid="stPlotlyChart"] {
        width: 100% !important;
        max-width: 100%;
        overflow-x: hidden;
    }
    div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] div[data-testid="stPlotlyChart"] > div,
    div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .js-plotly-plot,
    div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .plotly,
    div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .plot-container {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }

    @media (max-width: 480px) {
        div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .xtick text,
        div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .ytick text,
        div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .legendtext,
        div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .annotation-text,
        div[data-testid="element-container"]:has(.detail-chart-anchor) + div[data-testid="element-container"] .textpoint text {
            font-size: 10px !important;
        }
    }
</style>
"""


def _inject_plotly_hover_close_bridge():
    """Agrega un botón de cierre a los tooltips nativos de Plotly sin tocar cada gráfico."""
    components.html(
        """
        <style>
            html, body {
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
        </style>
        <script>
            (() => {
                let hostWindow = window;
                let hostDocument = document;

                try {
                    if (window.parent && window.parent !== window && window.parent.document) {
                        hostWindow = window.parent;
                        hostDocument = window.parent.document;
                    }
                } catch (error) {
                    return;
                }

                if (hostWindow.__plotlyHoverCloseBridgeInstalled) {
                    return;
                }
                hostWindow.__plotlyHoverCloseBridgeInstalled = true;

                const STYLE_ID = "plotly-hover-close-bridge-style";
                if (!hostDocument.getElementById(STYLE_ID)) {
                    const style = hostDocument.createElement("style");
                    style.id = STYLE_ID;
                    style.textContent = `
                        .plotly-hover-close-btn {
                            position: absolute;
                            z-index: 30;
                            width: 22px;
                            height: 22px;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            border: 1px solid rgba(148, 163, 184, 0.85);
                            border-radius: 999px;
                            background: rgba(255, 255, 255, 0.98);
                            color: #0f172a;
                            font-size: 14px;
                            font-weight: 700;
                            line-height: 1;
                            cursor: pointer;
                            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.16);
                            opacity: 0;
                            pointer-events: none;
                            padding: 0;
                            transform: translate(-9999px, -9999px);
                            transition: opacity 0.12s ease;
                        }
                        .plotly-hover-close-btn:hover {
                            background: #f8fafc;
                            border-color: rgba(100, 116, 139, 0.9);
                        }
                        .plotly-hover-close-btn:focus-visible {
                            outline: 2px solid rgba(59, 130, 246, 0.65);
                            outline-offset: 1px;
                        }
                    `;
                    hostDocument.head.appendChild(style);
                }

                const hideButton = (button) => {
                    if (!button) return;
                    button.style.opacity = "0";
                    button.style.pointerEvents = "none";
                    button.style.transform = "translate(-9999px, -9999px)";
                };

                const getVisibleHoverLabels = (plot) =>
                    Array.from(plot.querySelectorAll(".hoverlayer .hovertext")).filter((node) => {
                        const rect = node.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    });

                const syncButton = (plot) => {
                    const button = plot.__plotlyHoverCloseButton;
                    if (!button) return;

                    const labels = getVisibleHoverLabels(plot);
                    if (!labels.length) {
                        hideButton(button);
                        return;
                    }

                    const plotRect = plot.getBoundingClientRect();
                    const bounds = labels.reduce((acc, node) => {
                        const rect = node.getBoundingClientRect();
                        return {
                            top: Math.min(acc.top, rect.top),
                            right: Math.max(acc.right, rect.right),
                            bottom: Math.max(acc.bottom, rect.bottom),
                            left: Math.min(acc.left, rect.left),
                        };
                    }, {
                        top: Number.POSITIVE_INFINITY,
                        right: Number.NEGATIVE_INFINITY,
                        bottom: Number.NEGATIVE_INFINITY,
                        left: Number.POSITIVE_INFINITY,
                    });

                    const buttonSize = 22;
                    const left = Math.min(
                        Math.max(plotRect.width - buttonSize - 6, 6),
                        Math.max(bounds.right - plotRect.left - buttonSize - 4, 6),
                    );
                    const top = Math.max(bounds.top - plotRect.top + 4, 6);

                    button.style.transform = `translate(${left}px, ${top}px)`;
                    button.style.opacity = "1";
                    button.style.pointerEvents = "auto";
                };

                const bindPlot = (plot) => {
                    if (!plot || plot.dataset.hoverCloseBound === "1") {
                        return;
                    }

                    if (typeof plot.on !== "function") {
                        hostWindow.requestAnimationFrame(() => bindPlot(plot));
                        return;
                    }

                    plot.dataset.hoverCloseBound = "1";
                    if (hostWindow.getComputedStyle(plot).position === "static") {
                        plot.style.position = "relative";
                    }

                    const button = hostDocument.createElement("button");
                    button.type = "button";
                    button.className = "plotly-hover-close-btn";
                    button.innerHTML = "&times;";
                    button.setAttribute("aria-label", "Cerrar tooltip");
                    button.title = "Cerrar";
                    button.addEventListener("click", (event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        try {
                            hostWindow.Plotly?.Fx?.unhover?.(plot);
                        } catch (error) {
                            // No-op: el botón debe ser seguro aunque Plotly cambie.
                        }
                        hideButton(button);
                    });

                    plot.appendChild(button);
                    plot.__plotlyHoverCloseButton = button;

                    const scheduleSync = () => hostWindow.requestAnimationFrame(() => syncButton(plot));

                    plot.on("plotly_hover", scheduleSync);
                    plot.on("plotly_click", scheduleSync);
                    plot.on("plotly_afterplot", scheduleSync);
                    plot.on("plotly_redraw", scheduleSync);
                    plot.on("plotly_relayout", scheduleSync);
                    plot.on("plotly_unhover", () => hostWindow.setTimeout(() => syncButton(plot), 0));
                    plot.addEventListener("mouseleave", () => hostWindow.setTimeout(() => syncButton(plot), 0), {
                        passive: true,
                    });

                    scheduleSync();
                };

                const scanPlots = () => {
                    hostDocument.querySelectorAll(".js-plotly-plot").forEach(bindPlot);
                };

                scanPlots();

                const observer = new hostWindow.MutationObserver(() => scanPlots());
                observer.observe(hostDocument.body, { childList: true, subtree: true });
            })();
        </script>
        """,
        height=0,
    )


def apply_styles():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _inject_plotly_hover_close_bridge()
