import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from config import (
    PLOTLY_LAYOUT,
    HISTORICAL_YEAR_START,
    HISTORICAL_YEAR_END,
    API_LOADING_TEXT,
)
from data import (
    cargar_metrica_delito_comun_participacion,
    cargar_metrica_delito_comun_tipos,
    cargar_chart_delito_comun_rank,
    cargar_datos_departamentos_api,
    cargar_datos_municipios_api,
    cargar_metrica_delito_comun_top,
)


# ============================================================================
# HELPERS DE PRESENTACIÓN
# ============================================================================

def render_target_text(text):
    return f'<div class="startup-target-text">{text}</div>'


def ejecutar_con_texto_temporal(text, callback):
    placeholder = st.empty()
    placeholder.markdown(render_target_text(text), unsafe_allow_html=True)
    try:
        return callback()
    finally:
        placeholder.empty()


# ============================================================================
# HELPERS DE FORMATO DE DATOS
# ============================================================================

def preparar_participacion_geografica(df, casos_col="Casos"):
    df = df.copy()
    total_casos = float(df[casos_col].sum())
    if total_casos <= 0:
        df["Pct_Seleccionado"] = 0.0
        df["Pct_Resto"] = 0.0
    else:
        df["Pct_Seleccionado"] = (df[casos_col] / total_casos) * 100
        df["Pct_Resto"] = 100 - df["Pct_Seleccionado"]
    return df


def formatear_delito_principal_popup(valor):
    if pd.isna(valor):
        return "Sin dato"
    texto = str(valor).strip()
    if not texto:
        return "Sin dato"
    encabezado, separador, _ = texto.partition(".")
    return encabezado.strip() if separador and encabezado.strip() else texto


def truncateArticle(fullText: str) -> str:
    if fullText is None:
        return fullText
    text = str(fullText)
    if not text:
        return fullText
    dotIndex = text.find(".")
    return text[:dotIndex].strip() if dotIndex != -1 else text.strip()


# ============================================================================
# COMPONENTE DE MAPA INTERACTIVO
# ============================================================================

def construir_mapa_con_panel(
    fig,
    component_id,
    height,
    panel_title,
    placeholder_text,
    selected_label,
    other_label,
    selected_color,
    other_color,
    cases_idx,
    crime_idx,
    selected_pct_idx,
    other_pct_idx,
    subtitle_idx=None,
    subtitle_prefix="",
):
    plot_id = f"plot-{component_id}"
    wrapper_id = f"map-wrapper-{component_id}"
    card_id = f"map-card-{component_id}"
    content_id = f"map-content-{component_id}"
    close_id = f"map-close-{component_id}"

    panel_config = {
        "panel_title": panel_title,
        "placeholder": placeholder_text,
        "selected_label": selected_label,
        "other_label": other_label,
        "selected_color": selected_color,
        "other_color": other_color,
        "cases_idx": cases_idx,
        "crime_idx": crime_idx,
        "selected_pct_idx": selected_pct_idx,
        "other_pct_idx": other_pct_idx,
        "subtitle_idx": subtitle_idx,
        "subtitle_prefix": subtitle_prefix,
    }

    plot_html = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={
            "responsive": True,
            "displayModeBar": True,
            "displaylogo": False,
            "scrollZoom": True,
        },
        default_width="100%",
        default_height=f"{height}px",
        div_id=plot_id,
    )

    html = f"""
    <div id="{wrapper_id}" class="map-panel-shell">
        <style>
            #{wrapper_id} {{
                position: relative;
                width: 100%;
            }}
            #{wrapper_id} .map-panel-shell__plot {{
                width: 100%;
            }}
            #{wrapper_id} .map-panel-shell__plot .plotly-graph-div {{
                width: 100% !important;
            }}
            #{card_id} {{
                position: absolute;
                top: 16px;
                right: 16px;
                width: min(260px, calc(100% - 32px));
                padding: 0.95rem 1rem 0.9rem;
                border-radius: 16px;
                border: 1px solid rgba(148, 163, 184, 0.35);
                background: rgba(255, 255, 255, 0.96);
                box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
                backdrop-filter: blur(10px);
                z-index: 6;
                pointer-events: auto;
                opacity: 0;
                visibility: hidden;
            }}
            #{card_id}.is-visible {{
                opacity: 1;
                visibility: visible;
            }}
            #{card_id}.is-empty {{
                border-style: dashed;
            }}
            #{card_id} .map-panel-card__header {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 0.65rem;
            }}
            #{card_id} .map-panel-card__eyebrow {{
                margin-bottom: 0.35rem;
                font-size: 0.68rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #475569;
            }}
            #{card_id} .map-panel-card__close {{
                width: 24px;
                height: 24px;
                flex: 0 0 24px;
                border: 1px solid rgba(148, 163, 184, 0.65);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.96);
                color: #0f172a;
                font-size: 1rem;
                font-weight: 700;
                line-height: 1;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0;
                margin: -0.1rem -0.1rem 0 0;
            }}
            #{card_id} .map-panel-card__close:hover {{
                background: #f8fafc;
            }}
            #{card_id} .map-panel-card__close:focus-visible {{
                outline: 2px solid rgba(59, 130, 246, 0.55);
                outline-offset: 1px;
            }}
            #{card_id} .map-panel-card__title {{
                margin: 0;
                font-size: 1rem;
                font-weight: 800;
                color: #0f172a;
                line-height: 1.2;
            }}
            #{card_id} .map-panel-card__subtitle {{
                margin-top: 0.2rem;
                font-size: 0.78rem;
                color: #475569;
                font-weight: 600;
            }}
            #{card_id} .map-panel-card__placeholder {{
                font-size: 0.82rem;
                line-height: 1.5;
                color: #475569;
            }}
            #{card_id} .map-panel-card__metric {{
                margin-top: 0.7rem;
                display: flex;
                justify-content: space-between;
                gap: 0.8rem;
                align-items: flex-start;
                font-size: 0.82rem;
            }}
            #{card_id} .map-panel-card__metric-label {{
                color: #475569;
                font-weight: 700;
            }}
            #{card_id} .map-panel-card__metric-value {{
                color: #0f172a;
                font-weight: 800;
                text-align: right;
            }}
            #{card_id} .map-panel-card__metric--stack {{
                display: block;
            }}
            #{card_id} .map-panel-card__metric--stack .map-panel-card__metric-value {{
                display: block;
                margin-top: 0.28rem;
                text-align: left;
                font-weight: 700;
                line-height: 1.35;
            }}
            #{card_id} .map-panel-card__pie-block {{
                margin-top: 0.85rem;
                padding-top: 0.75rem;
                border-top: 1px solid rgba(148, 163, 184, 0.28);
                display: flex;
                gap: 0.75rem;
                align-items: center;
            }}
            #{card_id} .map-panel-card__pie-figure {{
                position: relative;
                width: 94px;
                height: 94px;
                flex: 0 0 94px;
            }}
            #{card_id} .map-panel-card__pie-figure svg {{
                width: 94px;
                height: 94px;
                display: block;
            }}
            #{card_id} .map-panel-card__pie-center {{
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                text-align: center;
                font-size: 0.72rem;
                font-weight: 800;
                color: #ffffff;
                line-height: 1.15;
            }}
            #{card_id} .map-panel-card__pie-center span {{
                color: #ffffff !important;
            }}
            #{card_id} .map-panel-card__legend {{
                flex: 1 1 auto;
                display: grid;
                gap: 0.4rem;
            }}
            #{card_id} .map-panel-card__legend-row {{
                display: flex;
                align-items: center;
                gap: 0.45rem;
                font-size: 0.76rem;
                color: #334155;
                line-height: 1.25;
            }}
            #{card_id} .map-panel-card__legend-swatch {{
                width: 10px;
                height: 10px;
                border-radius: 999px;
                flex: 0 0 10px;
            }}
            #{card_id} .map-panel-card__legend-row strong {{
                margin-left: auto;
                color: #0f172a;
                font-size: 0.78rem;
            }}
            #{card_id} .map-panel-card__footnote {{
                margin-top: 0.55rem;
                font-size: 0.72rem;
                color: #64748b;
                line-height: 1.35;
            }}
            @media (max-width: 768px) {{
                #{card_id} {{
                    top: auto;
                    bottom: 12px;
                    right: 12px;
                    left: 12px;
                    width: auto;
                    max-width: none;
                    padding: 0.85rem 0.9rem 0.8rem;
                }}
                #{card_id} .map-panel-card__pie-block {{
                    gap: 0.65rem;
                }}
            }}
        </style>

        <div class="map-panel-shell__plot">
            {plot_html}
        </div>

        <div id="{card_id}" class="map-panel-card is-empty">
            <div class="map-panel-card__header">
                <div class="map-panel-card__eyebrow">{panel_title}</div>
                <button id="{close_id}" type="button" class="map-panel-card__close" aria-label="Cerrar detalle">&times;</button>
            </div>
            <div id="{content_id}">
                <div class="map-panel-card__placeholder">{placeholder_text}</div>
            </div>
        </div>
    </div>

    <script>
        (() => {{
            const plot = document.getElementById("{plot_id}");
            const card = document.getElementById("{card_id}");
            const content = document.getElementById("{content_id}");
            const closeButton = document.getElementById("{close_id}");
            const cfg = {json.dumps(panel_config, ensure_ascii=False)};
            let pinnedPayload = null;

            const escapeHtml = (value) => String(value ?? "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#39;");

            const formatNumber = (value) =>
                new Intl.NumberFormat("es-CO").format(Math.round(Number(value) || 0));

            const formatPercent = (value) => `${{(Number(value) || 0).toFixed(1)}}%`;

            function polarToCartesian(cx, cy, radius, angleDegrees) {{
                const angle = (angleDegrees - 90) * Math.PI / 180.0;
                return {{
                    x: cx + (radius * Math.cos(angle)),
                    y: cy + (radius * Math.sin(angle)),
                }};
            }}

            function buildSlicePath(percentage) {{
                const pct = Math.max(0, Math.min(100, Number(percentage) || 0));
                if (pct <= 0) return "";
                if (pct >= 100) {{
                    return `<circle cx="50" cy="50" r="40" fill="${{cfg.selected_color}}"></circle>`;
                }}
                const start = polarToCartesian(50, 50, 40, 0);
                const end = polarToCartesian(50, 50, 40, (pct / 100) * 360);
                const largeArcFlag = pct > 50 ? 1 : 0;
                return `
                    <path
                        d="M 50 50 L ${{start.x}} ${{start.y}} A 40 40 0 ${{largeArcFlag}} 1 ${{end.x}} ${{end.y}} Z"
                        fill="${{cfg.selected_color}}">
                    </path>
                `;
            }}

            function renderPie(selectedPct, otherPct) {{
                const selected = Math.max(0, Math.min(100, Number(selectedPct) || 0));
                const other = Math.max(0, Math.min(100, Number(otherPct) || 0));
                return `
                    <div class="map-panel-card__pie-block">
                        <div class="map-panel-card__pie-figure">
                            <svg viewBox="0 0 100 100" aria-hidden="true">
                                <circle cx="50" cy="50" r="40" fill="${{cfg.other_color}}"></circle>
                                ${{buildSlicePath(selected)}}
                                <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.7)" stroke-width="1.4"></circle>
                            </svg>
                            <div class="map-panel-card__pie-center">
                                <div>${{formatPercent(selected)}}<br><span style="font-size:0.63rem;font-weight:700;color:#475569;">del total</span></div>
                            </div>
                        </div>
                        <div class="map-panel-card__legend">
                            <div class="map-panel-card__legend-row">
                                <span class="map-panel-card__legend-swatch" style="background:${{cfg.selected_color}};"></span>
                                <span>${{escapeHtml(cfg.selected_label)}}</span>
                                <strong>${{formatPercent(selected)}}</strong>
                            </div>
                            <div class="map-panel-card__legend-row">
                                <span class="map-panel-card__legend-swatch" style="background:${{cfg.other_color}};"></span>
                                <span>${{escapeHtml(cfg.other_label)}}</span>
                                <strong>${{formatPercent(other)}}</strong>
                            </div>
                        </div>
                    </div>
                `;
            }}

            function extractPayload(point) {{
                if (!point) return null;
                const customdata = Array.isArray(point.customdata) ? point.customdata : [];
                return {{
                    title: point.hovertext || point.location || cfg.panel_title,
                    subtitle: cfg.subtitle_idx === null ? "" : String(customdata[cfg.subtitle_idx] ?? ""),
                    cases: Number(customdata[cfg.cases_idx] ?? point.z ?? 0),
                    crime: String(customdata[cfg.crime_idx] ?? "Sin dato"),
                    selectedPct: Number(customdata[cfg.selected_pct_idx] ?? 0),
                    otherPct: Number(customdata[cfg.other_pct_idx] ?? 0),
                }};
            }}

            function renderPayload(payload) {{
                card.classList.remove("is-empty");
                card.classList.add("is-visible");
                const subtitleHtml = payload.subtitle
                    ? `<div class="map-panel-card__subtitle">${{escapeHtml(cfg.subtitle_prefix)}}${{escapeHtml(payload.subtitle)}}</div>`
                    : "";
                content.innerHTML = `
                    <h4 class="map-panel-card__title">${{escapeHtml(payload.title)}}</h4>
                    ${{subtitleHtml}}
                    <div class="map-panel-card__metric">
                        <span class="map-panel-card__metric-label">Casos</span>
                        <strong class="map-panel-card__metric-value">${{formatNumber(payload.cases)}}</strong>
                    </div>
                    <div class="map-panel-card__metric map-panel-card__metric--stack">
                        <span class="map-panel-card__metric-label">Delito principal</span>
                        <strong class="map-panel-card__metric-value">${{escapeHtml(payload.crime || "Sin dato")}}</strong>
                    </div>
                    ${{renderPie(payload.selectedPct, payload.otherPct)}}
                    <div class="map-panel-card__footnote">Participación calculada sobre el total visible en este mapa.</div>
                `;
            }}

            function showPlaceholder() {{
                if (pinnedPayload) {{
                    renderPayload(pinnedPayload);
                    return;
                }}
                card.classList.add("is-empty");
                card.classList.remove("is-visible");
                content.innerHTML = `<div class="map-panel-card__placeholder">${{escapeHtml(cfg.placeholder)}}</div>`;
            }}

            function dismissCard() {{
                pinnedPayload = null;
                card.classList.remove("is-visible");
                card.classList.remove("is-empty");
            }}

            function bindEvents() {{
                if (!plot || typeof plot.on !== "function") {{
                    window.requestAnimationFrame(bindEvents);
                    return;
                }}
                if (closeButton) {{
                    closeButton.addEventListener("click", (event) => {{
                        event.preventDefault();
                        event.stopPropagation();
                        dismissCard();
                    }});
                }}
                plot.on("plotly_hover", (eventData) => {{
                    const payload = extractPayload(eventData?.points?.[0]);
                    if (payload) renderPayload(payload);
                }});
                plot.on("plotly_click", (eventData) => {{
                    const payload = extractPayload(eventData?.points?.[0]);
                    if (payload) {{
                        pinnedPayload = payload;
                        renderPayload(payload);
                    }}
                }});
                plot.on("plotly_unhover", () => {{
                    if (pinnedPayload) renderPayload(pinnedPayload);
                    else showPlaceholder();
                }});
                plot.on("plotly_doubleclick", () => {{
                    pinnedPayload = null;
                    window.setTimeout(showPlaceholder, 0);
                }});
                showPlaceholder();
            }}

            bindEvents();
        }})();
    </script>
    """

    components.html(html, height=height + 20, scrolling=False)


# ============================================================================
# HELPERS DE VISTAS DE DETALLE
# ============================================================================

def _detail_title(key: str) -> str:
    return {
        "total_casos": "Total de Denuncias",
        "depto_top":   "Departamento Más Afectado",
        "delito_top":  "Delito Más Común",
        "anio_pico":   "Año Pico",
    }.get(key, "Detalle")


def _render_detail_chart(fig: go.Figure, margin=None):
    fig.update_layout(
        autosize=True,
        margin=margin or dict(t=16, b=48, l=16, r=16),
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    st.markdown('<div class="detail-chart-anchor"></div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})


def _detail_stat_card_html(label: str, value: str, note: str) -> str:
    return f"""
    <div class="detail-stat-card">
        <div class="dsc-label">{label}</div>
        <div class="dsc-value">{value}</div>
        <div class="dsc-note">{note}</div>
    </div>
    """


def _render_delito_comun_stat_card(column, label: str, loader, value_formatter, note_formatter):
    with column:
        placeholder = st.empty()
        placeholder.markdown(
            _detail_stat_card_html(label, "Cargando...", "Consultando API..."),
            unsafe_allow_html=True,
        )
        try:
            data = loader()
            placeholder.markdown(
                _detail_stat_card_html(label, value_formatter(data), note_formatter(data)),
                unsafe_allow_html=True,
            )
        except Exception as exc:
            placeholder.markdown(
                _detail_stat_card_html(label, "Error", f"No se pudo cargar: {exc}"),
                unsafe_allow_html=True,
            )


# ============================================================================
# SUB-VISTAS DE DETALLE
# ============================================================================

def _detail_total_casos(total_nacional, df_colombia, df_ciudades_mapa, df_hist, depto_top, anio_top):
    st.markdown(
        f"""
        <div class="detail-hero">
            <div class="dh-eyebrow">📊 Indicador · Total acumulado nacional</div>
            <div class="dh-title">Total de Denuncias por Cibercrimen</div>
            <div class="dh-value">{total_nacional:,}</div>
            <div class="dh-sub">Registros acumulados en la base de datos de la Policía Nacional</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    num_deptos = df_colombia["Departamento"].nunique()
    num_ciudades = df_ciudades_mapa["Ciudad"].nunique()
    promedio_depto = int(total_nacional / num_deptos) if num_deptos else 0
    años_con_datos = df_hist[df_hist["Casos"] > 0]["Año"].nunique()

    st.markdown(
        f"""
        <div class="detail-stats-grid">
            <div class="detail-stat-card">
                <div class="dsc-label">Departamentos registrados</div>
                <div class="dsc-value">{num_deptos}</div>
                <div class="dsc-note">Con al menos 1 denuncia</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Municipios / Ciudades</div>
                <div class="dsc-value">{num_ciudades:,}</div>
                <div class="dsc-note">Con presencia en el dataset</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Promedio por departamento</div>
                <div class="dsc-value">{promedio_depto:,}</div>
                <div class="dsc-note">Casos / dpto. (media simple)</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Años con datos</div>
                <div class="dsc-value">{años_con_datos}</div>
                <div class="dsc-note">Serie histórica disponible</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Depto. más afectado</div>
                <div class="dsc-value">{str(depto_top['Departamento']).title()}</div>
                <div class="dsc-note">{int(depto_top['Casos']):,} casos</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Año pico</div>
                <div class="dsc-value">{int(anio_top['Año']) if anio_top is not None else '—'}</div>
                <div class="dsc-note">{int(anio_top['Casos']):,} denuncias ese año</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pct_top5 = df_colombia.nlargest(5, "Casos")["Casos"].sum() / total_nacional * 100 if total_nacional else 0
    st.markdown(
        f"""
        <div class="detail-insight">
            <div class="di-icon">🔍</div>
            <div class="di-body">
                <strong>Concentración geográfica</strong>
                <p>Los 5 departamentos con mayor incidencia acumulan el <b>{pct_top5:.1f}%</b>
                del total nacional de denuncias. Esta concentración sugiere que las campañas de
                prevención y respuesta deberían priorizar estas jurisdicciones para mayor impacto.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title"><div class="icon purple">📊</div><h3>Top 10 Departamentos con Mayor Incidencia</h3></div>',
        unsafe_allow_html=True,
    )
    df_top10 = df_colombia.nlargest(10, "Casos").sort_values("Casos", ascending=True)
    fig = px.bar(
        df_top10, y="Departamento", x="Casos", orientation="h",
        text="Casos", color="Casos",
        color_continuous_scale=[[0, "#a8dce7"], [0.5, "#00b4d8"], [1, "#1e3a5f"]],
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(size=12, color="#FFFFFF"),
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<extra></extra>",
    )
    fig.update_layout(**{
        **PLOTLY_LAYOUT,
        "font": dict(family="Inter, sans-serif", color="#FFFFFF"),
        "yaxis": dict(title="", tickfont=dict(size=11, color="#FFFFFF")),
        "xaxis": dict(title="", showgrid=True, gridcolor="rgba(30,58,95,0.08)",
                      zeroline=False, tickfont=dict(size=11, color="#FFFFFF")),
        "showlegend": False, "coloraxis_showscale": False, "height": 420,
    })
    _render_detail_chart(fig)

    st.markdown(
        '<div class="section-title"><div class="icon cyan">🥧</div><h3>Distribución: Top 10 vs. Resto del País</h3></div>',
        unsafe_allow_html=True,
    )
    casos_top10 = int(df_top10["Casos"].sum())
    casos_resto = total_nacional - casos_top10
    fig_pie = px.pie(
        values=[casos_top10, casos_resto],
        names=["Top 10 Departamentos", "Resto del País"],
        color_discrete_sequence=["#1e3a5f", "#00b4d8"],
        hole=0.55,
    )
    fig_pie.update_traces(
        textinfo="percent+label",
        textfont=dict(size=13, color="#FFFFFF"),
        hovertemplate="<b>%{label}</b><br>Casos: %{value:,}<br>(%{percent})<extra></extra>",
    )
    fig_pie.update_layout(**{
        **PLOTLY_LAYOUT,
        "height": 360,
        "showlegend": True,
        "legend": dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#FFFFFF"),
        ),
    })
    _render_detail_chart(fig_pie, margin=dict(t=16, b=84, l=16, r=16))


def _detail_depto_top(total_nacional, df_ciudades_mapa, depto_top):
    nombre_depto = str(depto_top["Departamento"]).title()
    casos_depto = int(depto_top["Casos"])
    delito_depto = truncateArticle(str(depto_top.get("Delito_Principal", "Sin dato")))
    pct_depto = casos_depto / total_nacional * 100 if total_nacional else 0

    st.markdown(
        f"""
        <div class="detail-hero cyan">
            <div class="dh-eyebrow">🏙️ Indicador · Departamento más afectado</div>
            <div class="dh-title">{nombre_depto}</div>
            <div class="dh-value">{casos_depto:,}</div>
            <div class="dh-sub">{pct_depto:.1f}% del total nacional de denuncias</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_muni_depto = df_ciudades_mapa[
        df_ciudades_mapa["Departamento"] == depto_top["Departamento"]
    ].copy()
    num_muni = df_muni_depto["Ciudad"].nunique()
    ciudad_top_depto = (
        df_muni_depto.loc[df_muni_depto["Casos"].idxmax(), "Ciudad"]
        if not df_muni_depto.empty else "Sin dato"
    )
    casos_ciudad_top = (
        int(df_muni_depto["Casos"].max()) if not df_muni_depto.empty else 0
    )

    st.markdown(
        f"""
        <div class="detail-stats-grid">
            <div class="detail-stat-card">
                <div class="dsc-label">Total denuncias</div>
                <div class="dsc-value">{casos_depto:,}</div>
                <div class="dsc-note">Acumulado del departamento</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Participación nacional</div>
                <div class="dsc-value">{pct_depto:.1f}%</div>
                <div class="dsc-note">Del total de Colombia</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Municipios registrados</div>
                <div class="dsc-value">{num_muni}</div>
                <div class="dsc-note">Con al menos 1 denuncia</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Ciudad más afectada</div>
                <div class="dsc-value">{str(ciudad_top_depto).title()}</div>
                <div class="dsc-note">{casos_ciudad_top:,} casos</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Delito principal</div>
                <div class="dsc-value" style="font-size:1rem; line-height:1.3;">{delito_depto}</div>
                <div class="dsc-note">Conducta más denunciada</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Ranking nacional</div>
                <div class="dsc-value">#1</div>
                <div class="dsc-note">Por volumen de denuncias</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="detail-insight">
            <div class="di-icon">⚠️</div>
            <div class="di-body">
                <strong>Concentración interna</strong>
                <p><b>{nombre_depto}</b> concentra el <b>{pct_depto:.1f}%</b> de todas las denuncias del país.
                Su ciudad más reportada, <b>{str(ciudad_top_depto).title()}</b>, acumula
                <b>{casos_ciudad_top:,}</b> casos individuales, lo que apunta a una dinámica urbana
                que demanda atención prioritaria.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_muni_depto.empty:
        st.markdown(
            '<div class="section-title"><div class="icon cyan">📊</div>'
            f'<h3>Top 10 Municipios – {nombre_depto}</h3></div>',
            unsafe_allow_html=True,
        )
        df_top_muni = df_muni_depto.nlargest(10, "Casos").sort_values("Casos", ascending=True)
        fig = px.bar(
            df_top_muni, y="Ciudad", x="Casos", orientation="h",
            text="Casos", color="Casos",
            color_continuous_scale=[[0, "#a8dce7"], [0.5, "#00b4d8"], [1, "#1e3a5f"]],
        )
        fig.update_traces(
            texttemplate="%{text:,}", textposition="outside",
            textfont=dict(size=12, color="#FFFFFF"), marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<extra></extra>",
        )
        fig.update_layout(**{
            **PLOTLY_LAYOUT,
            "font": dict(family="Inter, sans-serif", color="#FFFFFF"),
            "yaxis": dict(title="", tickfont=dict(size=11, color="#FFFFFF")),
            "xaxis": dict(title="", showgrid=True, gridcolor="rgba(30,58,95,0.08)",
                          zeroline=False, tickfont=dict(size=11, color="#FFFFFF")),
            "showlegend": False, "coloraxis_showscale": False, "height": 400,
        })
        _render_detail_chart(fig)


def _detail_delito_top(delito_top_global, casos_delito_top_global, total_nacional):
    try:
        hero_data = cargar_metrica_delito_comun_top()
        hero_pct = cargar_metrica_delito_comun_participacion()
        delito_nombre = str(hero_data["delito"]).title()
        delito_titulo = truncateArticle(str(hero_data["delito"]))
        casos_delito = int(hero_data["casos"])
        pct_delito = float(hero_pct["pct"])
    except Exception:
        delito_nombre = str(delito_top_global).title()
        delito_titulo = truncateArticle(str(delito_top_global))
        casos_delito = int(casos_delito_top_global)
        pct_delito = casos_delito / total_nacional * 100 if total_nacional else 0

    st.markdown(
        f"""
        <div class="detail-hero violet">
            <div class="dh-eyebrow">⚠️ Indicador · Delito más frecuente a nivel nacional</div>
            <div class="dh-title">{delito_titulo}</div>
            <div class="dh-value">{casos_delito:,}</div>
            <div class="dh-sub">{pct_delito:.1f}% del total de denuncias nacionales</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stat_cols = st.columns(3)
    _render_delito_comun_stat_card(
        stat_cols[0],
        "Casos del delito #1",
        cargar_metrica_delito_comun_top,
        lambda data: f"{int(data['casos']):,}",
        lambda _data: "Denuncias acumuladas",
    )
    _render_delito_comun_stat_card(
        stat_cols[1],
        "Participación en total",
        cargar_metrica_delito_comun_participacion,
        lambda data: f"{float(data['pct']):.1f}%",
        lambda _data: "Del total nacional",
    )
    _render_delito_comun_stat_card(
        stat_cols[2],
        "Tipos de delito distintos",
        cargar_metrica_delito_comun_tipos,
        lambda data: f"{int(data['total'])}",
        lambda _data: "Conductas registradas",
    )

    st.markdown(
        f"""
        <div class="detail-insight">
            <div class="di-icon">🎯</div>
            <div class="di-body">
                <strong>Análisis de la conducta líder</strong>
                <p>El delito <b>"{delito_titulo}"</b> representa el <b>{pct_delito:.1f}%</b> de todos los
                casos registrados en el país. Entender sus patrones de ocurrencia por región y año
                es clave para diseñar estrategias de prevención focalizadas.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title"><div class="icon violet">📊</div>'
        '<h3>Ranking de Delitos por Volumen de Denuncias</h3></div>',
        unsafe_allow_html=True,
    )
    chart_placeholder = st.empty()
    chart_placeholder.info("Cargando ranking de delitos desde la API...")
    try:
        df_plot = cargar_chart_delito_comun_rank()
        chart_placeholder.empty()

        if df_plot.empty:
            chart_placeholder.info("Sin datos disponibles")
        else:
            df_plot_display = df_plot.copy()
            df_plot_display["Delito_Principal"] = df_plot_display["Delito_Principal"].map(truncateArticle)
            chart_height = max(320, len(df_plot) * 44)
            chart_max_height = 640
            chart_placeholder.markdown(
                f"""
                <style>
                    div[data-testid="element-container"]:has(.delito-rank-chart-anchor) + div[data-testid="element-container"] {{
                        max-height: {chart_max_height}px;
                        overflow-y: auto;
                        overflow-x: hidden;
                        padding-right: 0.25rem;
                    }}
                </style>
                <div class="delito-rank-chart-anchor"></div>
                """,
                unsafe_allow_html=True,
            )

            fig = px.bar(
                df_plot_display, y="Delito_Principal", x="Casos", orientation="h",
                text="Casos", color="Casos",
                color_continuous_scale=[[0, "#c4b5fd"], [0.5, "#6c63ff"], [1, "#1e3a5f"]],
            )
            fig.update_traces(
                texttemplate="%{text:,}", textposition="outside",
                textfont=dict(size=11, color="#FFFFFF"), marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>Casos: %{x:,}<extra></extra>",
            )
            fig.update_layout(**{
                **PLOTLY_LAYOUT,
                "font": dict(family="Inter, sans-serif", color="#FFFFFF"),
                "yaxis": dict(title="", tickfont=dict(size=10, color="#FFFFFF")),
                "xaxis": dict(title="", showgrid=True, gridcolor="rgba(108,99,255,0.08)",
                              zeroline=False, tickfont=dict(size=10, color="#FFFFFF")),
                "showlegend": False, "coloraxis_showscale": False,
                "height": chart_height,
                "margin": dict(t=10, b=40, l=200, r=60),
            })
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    except Exception as exc:
        chart_placeholder.error(f"No se pudo cargar el ranking de delitos: {exc}")


def _detail_anio_pico(anio_top, df_hist, df_hist_linea):
    if anio_top is None:
        st.warning("No hay datos de serie histórica disponibles.")
        return

    año_valor = int(anio_top["Año"])
    casos_valor = int(anio_top["Casos"])
    ciudad_ese_año = str(anio_top.get("Ciudad_Top", "Sin dato")).title()
    delito_ese_año = str(anio_top.get("Delito_Top", "Sin dato")).title()
    delito_ese_año_titulo = truncateArticle(str(anio_top.get("Delito_Top", "Sin dato")))

    df_hist_ord = df_hist.sort_values("Año")
    idx_pico = df_hist_ord[df_hist_ord["Año"] == año_valor].index
    casos_anterior, año_anterior = None, None
    casos_siguiente, año_siguiente = None, None
    if len(idx_pico):
        pos = df_hist_ord.index.get_loc(idx_pico[0])
        if pos > 0:
            row_ant = df_hist_ord.iloc[pos - 1]
            año_anterior = int(row_ant["Año"])
            casos_anterior = int(row_ant["Casos"])
        if pos < len(df_hist_ord) - 1:
            row_sig = df_hist_ord.iloc[pos + 1]
            año_siguiente = int(row_sig["Año"])
            casos_siguiente = int(row_sig["Casos"])

    var_anterior = (
        f"+{((casos_valor - casos_anterior) / casos_anterior * 100):.1f}% vs {año_anterior}"
        if casos_anterior and casos_anterior > 0 else "—"
    )

    st.markdown(
        f"""
        <div class="detail-hero green">
            <div class="dh-eyebrow">📅 Indicador · Año con mayor número de denuncias</div>
            <div class="dh-title">Año Pico: {año_valor}</div>
            <div class="dh-value">{casos_valor:,}</div>
            <div class="dh-sub">{var_anterior}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    promedio_historico = int(df_hist[df_hist["Casos"] > 0]["Casos"].mean())
    pct_sobre_promedio = (casos_valor - promedio_historico) / promedio_historico * 100 if promedio_historico else 0

    st.markdown(
        f"""
        <div class="detail-stats-grid">
            <div class="detail-stat-card">
                <div class="dsc-label">Denuncias en {año_valor}</div>
                <div class="dsc-value">{casos_valor:,}</div>
                <div class="dsc-note">Máximo histórico registrado</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Promedio histórico anual</div>
                <div class="dsc-value">{promedio_historico:,}</div>
                <div class="dsc-note">Media de todos los años con datos</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">% sobre el promedio</div>
                <div class="dsc-value">+{pct_sobre_promedio:.1f}%</div>
                <div class="dsc-note">Por encima de la media histórica</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Ciudad más afectada ese año</div>
                <div class="dsc-value">{ciudad_ese_año}</div>
                <div class="dsc-note">Mayor volumen de denuncias</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Delito más frecuente ese año</div>
                <div class="dsc-value" style="font-size:0.95rem; line-height:1.3;">{delito_ese_año_titulo}</div>
                <div class="dsc-note">Conducta dominante en {año_valor}</div>
            </div>
            <div class="detail-stat-card">
                <div class="dsc-label">Año siguiente ({año_siguiente or '—'})</div>
                <div class="dsc-value">{f"{casos_siguiente:,}" if casos_siguiente else "—"}</div>
                <div class="dsc-note">{'↓ Disminución post-pico' if casos_siguiente and casos_siguiente < casos_valor else '↑ Continuó en alza'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="detail-insight">
            <div class="di-icon">📈</div>
            <div class="di-body">
                <strong>Contexto del año pico</strong>
                <p>En <b>{año_valor}</b> se registró el máximo histórico de denuncias con <b>{casos_valor:,}</b> casos,
                un <b>{pct_sobre_promedio:.1f}%</b> por encima del promedio histórico anual.
                La ciudad más activa fue <b>{ciudad_ese_año}</b> y el delito preponderante fue
                <b>"{delito_ese_año_titulo}"</b>.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title"><div class="icon pink">📈</div>'
        '<h3>Serie Histórica Nacional (año pico resaltado)</h3></div>',
        unsafe_allow_html=True,
    )

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=df_hist_linea["Año"], y=df_hist_linea["Casos"],
        fill="tozeroy", fillcolor="rgba(99, 102, 241, 0.08)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig_hist.add_trace(go.Scatter(
        x=df_hist_linea["Año"], y=df_hist_linea["Casos"],
        mode="lines+markers",
        line=dict(width=3, color="#818cf8", shape="spline", smoothing=0.8),
        marker=dict(size=9, color="#6366f1", line=dict(width=2, color="#c7d2fe")),
        customdata=list(zip(df_hist_linea["Ciudad_Top"], df_hist_linea["Delito_Top"].map(truncateArticle))),
        hovertemplate=(
            "<b>Año:</b> %{x}<br>"
            "<b>Denuncias:</b> %{y:,}<br>"
            "<b>Ciudad top:</b> %{customdata[0]}<br>"
            "<b>Delito top:</b> %{customdata[1]}<extra></extra>"
        ),
        showlegend=False,
    ))
    df_pico_point = df_hist_linea[df_hist_linea["Año"] == año_valor]
    if not df_pico_point.empty:
        fig_hist.add_trace(go.Scatter(
            x=df_pico_point["Año"], y=df_pico_point["Casos"],
            mode="markers+text",
            marker=dict(size=16, color="#f59e0b", symbol="star",
                        line=dict(width=2, color="#ffffff")),
            text=[f"  Máximo {año_valor}"],
            textposition="top right",
            textfont=dict(size=12, color="#f59e0b"),
            showlegend=False,
            hovertemplate=f"<b>Año pico: {año_valor}</b><br>Casos: {casos_valor:,}<extra></extra>",
        ))

    fig_hist.update_layout(**{
        **PLOTLY_LAYOUT,
        "font": dict(family="Inter, sans-serif", color="#FFFFFF"),
        "xaxis": dict(
            tickmode="linear", dtick=1,
            range=[HISTORICAL_YEAR_START - 0.5, HISTORICAL_YEAR_END + 0.5],
            showgrid=False, tickfont=dict(size=11, color="#FFFFFF"), title="",
        ),
        "yaxis": dict(
            title=dict(text="Denuncias Registradas", font=dict(size=12, color="#FFFFFF")),
            showgrid=True, gridcolor="rgba(99,102,241,0.06)",
            zeroline=False, tickfont=dict(size=11, color="#FFFFFF"),
        ),
        "hovermode": "x unified",
        "height": 360,
    })
    _render_detail_chart(fig_hist)


# ============================================================================
# DISPATCHER DE VISTA DE DETALLE
# ============================================================================

def render_detail_view(view_key, total_nacional, df_colombia, df_ciudades_mapa,
                       df_hist, df_hist_linea, depto_top, anio_top,
                       delito_top_global, casos_delito_top_global, navigate_home):
    try:
        if view_key == "total_casos":
            _detail_total_casos(total_nacional, df_colombia, df_ciudades_mapa, df_hist, depto_top, anio_top)
        elif view_key == "depto_top":
            _detail_depto_top(total_nacional, df_ciudades_mapa, depto_top)
        elif view_key == "delito_top":
            _detail_delito_top(delito_top_global, casos_delito_top_global, total_nacional)
        elif view_key == "anio_pico":
            _detail_anio_pico(anio_top, df_hist, df_hist_linea)
        else:
            st.warning("Vista no reconocida.")
    except Exception as exc:
        st.error(f"No se pudo abrir la sub-vista seleccionada: {exc}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Volver al Dashboard", key="btn_back_bottom"):
        navigate_home()
        st.rerun()


# ============================================================================
# VISTA PRINCIPAL DEL DASHBOARD
# ============================================================================

def render_dashboard_principal(
    df_colombia, df_ciudades_mapa, df_hist_linea,
    lista_deptos, lista_ciudades, total_nacional,
    delito_top_global, casos_delito_top_global,
    depto_top, anio_top, geojson_col, navigate_to, navigate_home,
):
    # ── HERO HEADER ──────────────────────────────────────────���────────────
    st.markdown(
        '<div class="hero">'
        '<h1>Cibercrimen en Colombia</h1>'
        '<p>Análisis interactivo de denuncias por delitos informáticos registrados '
        'ante la Policía Nacional. Explora la distribución geográfica, tendencias '
        'históricas y los delitos más frecuentes en cada departamento.</p>'
        '<span class="tag">🔄 Datos en tiempo real · API Datos Abiertos</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── KPI METRIC CARDS ────────────────────────────────────────────────────
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-icon">📊</div>
            <div class="kpi-label">Total Denuncias</div>
            <div class="kpi-value">{total_nacional:,}</div>
            <div class="kpi-sub">acumulado nacional</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🏙️</div>
            <div class="kpi-label">Depto. Más Afectado</div>
            <div class="kpi-value">{str(depto_top['Departamento']).title()}</div>
            <div class="kpi-sub">{int(depto_top['Casos']):,} casos</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⚠️</div>
            <div class="kpi-label">Delito Más Común</div>
            <div class="kpi-value" style="font-size:0.95rem; line-height:1.3;">{truncateArticle(str(delito_top_global))}</div>
            <div class="kpi-sub">a nivel nacional</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">📅</div>
            <div class="kpi-label">Año Pico</div>
            <div class="kpi-value">{int(anio_top['Año']) if anio_top is not None else '—'}</div>
            <div class="kpi-sub">{int(anio_top['Casos']):,} denuncias</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    btn_cols = st.columns(4)
    kpi_keys = ["total_casos", "depto_top", "delito_top", "anio_pico"]
    kpi_labels = ["📊 Total de Casos", "🏙️ Depto. Afectado", "⚠️ Delito Común", "📅 Año Pico"]

    for col, key, label in zip(btn_cols, kpi_keys, kpi_labels):
        with col:
            if st.button(label, key=f"kpi_btn_{key}", use_container_width=True):
                navigate_to(key)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── GLOSARIO ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title"><div class="icon yellow">📚</div>'
        '<a href="https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=34492" '
        'target="_blank" rel="noopener noreferrer" '
        'style="color: inherit; text-decoration: none; display: inline-flex; align-items: center;"><h3 style="margin: 0;">Glosario de Delitos (Ley 1273 de 2009)</h3></a></div>',
        unsafe_allow_html=True,
    )

    st.markdown("""
    <div class="glossary-grid">
        <div class="glossary-card"><h4>🛡️ Art. 269I – Robo Cibernético (Cybertheft)</h4><p>Hurtar dinero o bienes manipulando sistemas informáticos o suplantando identidades ante sistemas de autenticación, como el clonado de tarjetas o el fraude en cajeros.</p></div>
        <div class="glossary-card"><h4>🔓 Art. 269A – Acceso No Autorizado / Hackeo (Unauthorized Access)</h4><p>Ingresar a un sistema informático sin permiso, ya sea saltando medidas de seguridad o permaneciendo en él contra la voluntad del propietario.</p></div>
        <div class="glossary-card"><h4>🗃️ Art. 269F – Violación de Privacidad / Fuga de Datos (Data Breach)</h4><p>Obtener, vender, intercambiar o divulgar datos personales de terceros sin autorización, con fines de lucro propio o ajeno.</p></div>
        <div class="glossary-card"><h4>🎣 Art. 269G – Phishing / Suplantación de Identidad Digital (Phishing)</h4><p>Crear páginas web o enlaces falsos que imitan sitios legítimos (bancos, redes sociales) para engañar a usuarios y robarles sus credenciales o datos.</p></div>
        <div class="glossary-card"><h4>💸 Art. 269J – Fraude Bancario Electrónico (Wire Fraud)</h4><p>Transferir activos de una víctima sin su consentimiento mediante manipulación de sistemas financieros. Es el delito con la pena más alta de la ley: hasta 10 años de prisión.</p></div>
        <div class="glossary-card"><h4>🎧 Art. 269C – Interceptación de Comunicaciones / Espionaje Digital (Wiretapping / Sniffing)</h4><p>Capturar o "escuchar" datos mientras viajan por una red sin autorización judicial, como espiar correos, mensajes o tráfico web en tiempo real.</p></div>
        <div class="glossary-card"><h4>💥 Art. 269D – Sabotaje Informático (Cyber Sabotage)</h4><p>Destruir, borrar, alterar o dañar datos o sistemas de forma intencional, inutilizándolos total o parcialmente.</p></div>
        <div class="glossary-card"><h4>🦠 Art. 269E – Uso de Malware (Malware Deployment)</h4><p>Crear, distribuir o introducir software diseñado para causar daño: virus, ransomware, spyware, troyanos, entre otros.</p></div>
        <div class="glossary-card"><h4>⛔ Art. 269B – Ataque de Denegación de Servicio (DoS / DDoS Attack)</h4><p>Bloquear o interrumpir deliberadamente el funcionamiento de un sistema, red o servicio para que usuarios legítimos no puedan acceder a él.</p></div>
    </div>

    <div style="margin-top: 1.5rem; padding: 1.2rem; background-color: rgba(245, 158, 11, 0.08); border-left: 4px solid #f59e0b; border-radius: 8px; width: 100%; box-sizing: border-box; display: flex; align-items: flex-start; gap: 0.8rem;">
        <span style="font-size: 1.5rem; flex-shrink: 0; line-height: 1;">⚠️</span>
        <div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 0.95rem; color: #111111; font-weight: 700;">Nota – Art. 269H | Circunstancias Agravantes Cibernéticas (Cybercrime Aggravating Factors)</h4>
            <p style="margin: 0; font-size: 0.85rem; color: #334155; line-height: 1.5;">No es un delito en sí, sino un conjunto de condiciones que aumentan la pena entre un 50% y un 75% cuando el crimen afecta al Estado, involucra funcionarios públicos o tiene fines terroristas, entre otros.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TIP ───────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="tip-box">'
        '<span class="tip-icon">💡</span>'
        'Pasa el cursor o haz clic sobre un departamento o ciudad para ver su detalle y la concentración relativa frente al resto del mapa.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── SECCIÓN 1: CONCENTRACIÓN GEOGRÁFICA ──────────────────────────────
    col_map1_title, col_map1_filter = st.columns([3, 1])
    with col_map1_title:
        st.markdown(
            '<div class="section-title">'
            '<div class="icon purple">🗺️</div>'
            '<h3>Concentración Geográfica</h3>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_map1_filter:
        seleccion = st.selectbox("Filtrar por región", lista_deptos)

    if seleccion == "TOTAL NACIONAL":
        df_mapa = df_colombia.copy()
        df_barras = df_mapa
        zoom_mapa = 4.5
        centro_lat, centro_lon = 4.5709, -74.2973
        titulo_barras = "Departamentos con Mayor Incidencia"
    else:
        df_mapa = df_colombia[df_colombia["Departamento"] == seleccion].copy()
        df_barras = df_mapa
        zoom_mapa = 6.0
        centro_lat = float(df_mapa["Lat"].iloc[0])
        centro_lon = float(df_mapa["Lon"].iloc[0])
        titulo_barras = f"Detalle — {seleccion.title()}"

    df_mapa = preparar_participacion_geografica(df_mapa)

    fig_mapa = px.choropleth_map(
        df_mapa,
        geojson=geojson_col,
        locations="Codigo_DANE",
        featureidkey="properties.codigo_departamento_n",
        color="Casos",
        hover_name="Departamento",
        custom_data=["Casos", "Delito_Principal", "Pct_Seleccionado", "Pct_Resto"],
        color_continuous_scale=[
            [0, "#f4f6f9"], [0.5, "#00b4d8"], [1, "#1e3a5f"],
        ],
        range_color=(df_colombia["Casos"].min(), df_colombia["Casos"].max()),
        map_style="carto-darkmatter",
        zoom=zoom_mapa,
        center={"lat": centro_lat, "lon": centro_lon},
        opacity=0.82,
    )
    customdata_departamentos = list(
        zip(
            df_mapa["Casos"],
            df_mapa["Delito_Principal"].map(formatear_delito_principal_popup),
            df_mapa["Pct_Seleccionado"],
            df_mapa["Pct_Resto"],
        )
    )
    fig_mapa.update_traces(
        customdata=customdata_departamentos,
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "<b>Casos:</b> %{customdata[0]:,}<br>"
            "<b>Delito principal:</b> %{customdata[1]}<br>"
            "<b>Participación:</b> %{customdata[2]:.1f}%<extra></extra>"
        ),
    )
    fig_mapa.update_traces(hoverinfo="none", hovertemplate=None)
    layout_mapa = {
        **PLOTLY_LAYOUT,
        "coloraxis_colorbar": dict(
            title=dict(text="Casos", font=dict(size=12, color="#1a1a1a")),
            tickfont=dict(size=10, color="#111111"),
            bgcolor="rgba(255,255,255,0.7)",
            borderwidth=0, len=0.6, thickness=12, x=0.02, xanchor="left",
        ),
        "hoverlabel": dict(
            bgcolor="#ffffff", font_size=13, font_family="Inter, sans-serif",
            font_color="#111111", bordercolor="#cbd5e1",
        ),
        "height": 480,
    }
    fig_mapa.update_layout(**layout_mapa)
    construir_mapa_con_panel(
        fig=fig_mapa, component_id="departamentos", height=480,
        panel_title="Detalle interactivo",
        placeholder_text="Pasa el cursor o haz clic sobre un departamento para ver su participación frente al resto del país.",
        selected_label="Departamento", other_label="Otros departamentos",
        selected_color="#00b4d8", other_color="#1e3a5f",
        cases_idx=0, crime_idx=1, selected_pct_idx=2, other_pct_idx=3,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 2: CIUDADES ───────────────────────────────────────────────
    col_map2_title, col_map2_filter = st.columns([3, 1])
    with col_map2_title:
        st.markdown(
            '<div class="section-title">'
            '<div class="icon cyan">📍</div>'
            '<h3>Las 30 Ciudades con Mayor Incidencia de Ataques</h3>'
            '</div>',
            unsafe_allow_html=True,
        )
    with col_map2_filter:
        seleccion_ciudad = st.selectbox("Filtrar mapa de ciudades", lista_ciudades)

    df_ciudades_base = df_ciudades_mapa.copy()
    zoom_ciudades = 4.5
    centro_lat_ciudades, centro_lon_ciudades = 4.5709, -74.2973

    if seleccion_ciudad == "TODAS LAS CIUDADES":
        limite_ciudades = 30
        df_ciudades = df_ciudades_base.nlargest(limite_ciudades, "Casos").copy()
    else:
        ciudad_filtrada, departamento_filtrado = seleccion_ciudad.rsplit(" - ", 1)
        df_ciudades = df_ciudades_base[
            (df_ciudades_base["Ciudad"] == ciudad_filtrada)
            & (df_ciudades_base["Departamento"] == departamento_filtrado)
        ].copy()
        if not df_ciudades.empty:
            centro_lat_ciudades = float(df_ciudades["Lat_Ciudad"].iloc[0])
            centro_lon_ciudades = float(df_ciudades["Lon_Ciudad"].iloc[0])
            zoom_ciudades = 8.5

    df_ciudades = preparar_participacion_geografica(df_ciudades)

    fig_mapa_ciudades = px.scatter_map(
        df_ciudades, lat="Lat_Ciudad", lon="Lon_Ciudad",
        size="Casos", color="Casos", hover_name="Ciudad",
        custom_data=["Departamento", "Casos", "Delito_Principal_Ciudad", "Pct_Seleccionado", "Pct_Resto"],
        color_continuous_scale=[[0, "#f4f6f9"], [0.5, "#6c63ff"], [1, "#1e3a5f"]],
        range_color=(0, max(int(df_ciudades_mapa["Casos"].max()), 1)),
        size_max=34, zoom=zoom_ciudades,
        center={"lat": centro_lat_ciudades, "lon": centro_lon_ciudades},
        opacity=0.88, map_style="carto-darkmatter",
    )
    customdata_ciudades = list(
        zip(
            df_ciudades["Departamento"],
            df_ciudades["Casos"],
            df_ciudades["Delito_Principal_Ciudad"].map(formatear_delito_principal_popup),
            df_ciudades["Pct_Seleccionado"],
            df_ciudades["Pct_Resto"],
        )
    )
    fig_mapa_ciudades.update_traces(
        customdata=customdata_ciudades,
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "<b>Departamento:</b> %{customdata[0]}<br>"
            "<b>Casos:</b> %{customdata[1]:,}<br>"
            "<b>Delito principal:</b> %{customdata[2]}<br>"
            "<b>Participación:</b> %{customdata[3]:.1f}%<extra></extra>"
        ),
    )
    fig_mapa_ciudades.update_traces(hoverinfo="none", hovertemplate=None)
    layout_ciudades = {
        **PLOTLY_LAYOUT,
        "coloraxis_colorbar": dict(
            title=dict(text="Casos", font=dict(size=12, color="#1a1a1a")),
            tickfont=dict(size=10, color="#111111"),
            bgcolor="rgba(255,255,255,0.7)",
            borderwidth=0, len=0.6, thickness=12, x=0.02, xanchor="left",
        ),
        "hoverlabel": dict(
            bgcolor="#ffffff", font_size=13, font_family="Inter, sans-serif",
            font_color="#111111", bordercolor="#cbd5e1",
        ),
        "height": 420,
    }
    fig_mapa_ciudades.update_layout(**layout_ciudades)
    construir_mapa_con_panel(
        fig=fig_mapa_ciudades, component_id="ciudades", height=420,
        panel_title="Detalle interactivo",
        placeholder_text="Pasa el cursor sobre una ciudad para ver su participación frente al resto de ciudades visibles.",
        selected_label="Ciudad", other_label="Otras ciudades",
        selected_color="#6c63ff", other_color="#1e3a5f",
        cases_idx=1, crime_idx=2, selected_pct_idx=3, other_pct_idx=4,
        subtitle_idx=0, subtitle_prefix="Departamento: ",
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECCIÓN 3: BARRAS ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">'
        '<div class="icon cyan">📊</div>'
        f'<h3>{titulo_barras}</h3>'
        f'<span class="badge">{seleccion.title()}</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    df_top = df_barras.nlargest(5, "Casos").sort_values("Casos", ascending=True)
    df_top_display = df_top.copy()
    df_top_display["Delito_Principal_Display"] = df_top_display["Delito_Principal"].map(truncateArticle)
    fig_barras = px.bar(
        df_top_display, y="Departamento", x="Casos", text="Casos", orientation="h",
        color="Casos",
        color_continuous_scale=[[0, "#a8dce7"], [0.5, "#00b4d8"], [1, "#1e3a5f"]],
        custom_data=["Delito_Principal_Display"],
    )
    fig_barras.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(size=12, color="#FFFFFF", family="Inter"),
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "<b>Casos:</b> %{x:,}<br>"
            "<b>Delito Principal:</b> %{customdata[0]}<extra></extra>"
        ),
    )
    layout_barras = {
        **PLOTLY_LAYOUT,
        "font": dict(family="Inter, sans-serif", color="#FFFFFF"),
        "yaxis": dict(title="", tickfont=dict(size=11, color="#FFFFFF")),
        "xaxis": dict(
            title="", showgrid=True, gridcolor="rgba(30,58,95,0.08)",
            zeroline=False, tickfont=dict(size=11, color="#FFFFFF"),
        ),
        "hoverlabel": dict(
            bgcolor="#ffffff", font_size=13, font_family="Inter, sans-serif",
            font_color="#111111", bordercolor="#cbd5e1",
        ),
        "showlegend": False, "coloraxis_showscale": False, "height": 360,
    }
    fig_barras.update_layout(**layout_barras)
    st.plotly_chart(fig_barras, use_container_width=True)

    # ── DIVIDER ───────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)

    # ── LÍNEA HISTÓRICA ───────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">'
        '<div class="icon pink">📈</div>'
        '<h3>Evolución Histórica Nacional</h3>'
        '<span class="badge">Serie temporal</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(
        x=df_hist_linea["Año"], y=df_hist_linea["Casos"],
        fill="tozeroy", fillcolor="rgba(99, 102, 241, 0.08)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig_linea.add_trace(go.Scatter(
        x=df_hist_linea["Año"], y=df_hist_linea["Casos"],
        mode="lines+markers",
        line=dict(width=3, color="#818cf8", shape="spline", smoothing=0.8),
        marker=dict(size=10, color="#6366f1", line=dict(width=2, color="#c7d2fe"), symbol="circle"),
        customdata=list(zip(df_hist_linea["Ciudad_Top"], df_hist_linea["Delito_Top"].map(truncateArticle))),
        hovertemplate=(
            "<b>Año:</b> %{x}<br>"
            "<b>Denuncias:</b> %{y:,}<br>"
            "<b>Ciudad más afectada:</b> %{customdata[0]}<br>"
            "<b>Delito más frecuente:</b> %{customdata[1]}<extra></extra>"
        ),
        showlegend=False,
    ))
    layout_linea = {
        **PLOTLY_LAYOUT,
        "font": dict(family="Inter, sans-serif", color="#FFFFFF"),
        "xaxis": dict(
            tickmode="linear", dtick=1,
            range=[HISTORICAL_YEAR_START - 0.5, HISTORICAL_YEAR_END + 0.5],
            showgrid=False, tickfont=dict(size=11, color="#FFFFFF"), title="",
        ),
        "yaxis": dict(
            title=dict(text="Denuncias Registradas", font=dict(size=12, color="#FFFFFF")),
            showgrid=True, gridcolor="rgba(99,102,241,0.06)",
            zeroline=False, tickfont=dict(size=11, color="#FFFFFF"),
        ),
        "hovermode": "x unified",
        "height": 340,
    }
    fig_linea.update_layout(**layout_linea)
    st.plotly_chart(fig_linea, use_container_width=True)

    st.divider()

    # ── FOOTER ────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="dashboard-footer">'
        'Dashboard Cibercrimen Colombia · Datos: '
        '<a href="https://www.datos.gov.co/" target="_blank">datos.gov.co</a> · '
        'Policía Nacional de Colombia'
        '</div>',
        unsafe_allow_html=True,
    )
