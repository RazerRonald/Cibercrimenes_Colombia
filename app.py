import streamlit as st
import streamlit.components.v1 as components

from config import API_DEPTO_EMPTY_TEXT, API_LOADING_TEXT
from styles import apply_styles
from data import (
    cargar_contexto_metricas_globales,
    cargar_contexto_dashboard_principal,
    cargar_contexto_total_casos,
    cargar_contexto_depto_top,
    cargar_contexto_anio_pico,
)
from ui import (
    ejecutar_con_texto_temporal,
    render_target_text,
    render_detail_view,
    render_dashboard_principal,
)

import pandas as pd

# 1. Page config (DEBE ser la primera llamada a Streamlit)
st.set_page_config(
    page_title="Ciberdelitos en Colombia",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Estilos y JS globales
apply_styles()

# 3. Session state
if "active_view" not in st.session_state:
    st.session_state.active_view = None
if "pending_scroll_reset" not in st.session_state:
    st.session_state.pending_scroll_reset = False
if "scroll_reset_nonce" not in st.session_state:
    st.session_state.scroll_reset_nonce = 0


# 4. Funciones de navegación
def _schedule_scroll_reset():
    st.session_state.pending_scroll_reset = True
    st.session_state.scroll_reset_nonce += 1


def _render_pending_scroll_reset():
    if not st.session_state.get("pending_scroll_reset"):
        return

    nonce = st.session_state.get("scroll_reset_nonce", 0)
    components.html(
        f"""
        <script>
            const resetScrollPosition = () => {{
                const parentWindow = window.parent;
                const targets = [
                    window,
                    document.documentElement,
                    document.body,
                    parentWindow,
                    parentWindow?.document?.documentElement,
                    parentWindow?.document?.body,
                    parentWindow?.document?.querySelector('section.main'),
                    parentWindow?.document?.querySelector('[data-testid="stAppViewContainer"]'),
                    parentWindow?.document?.querySelector('[data-testid="block-container"]'),
                ];

                targets.forEach((target) => {{
                    try {{
                        if (!target) return;
                        if (typeof target.scrollTo === "function") {{
                            target.scrollTo(0, 0);
                        }}
                        if ("scrollTop" in target) {{
                            target.scrollTop = 0;
                        }}
                    }} catch (error) {{
                        // Ignore cross-context issues and keep the transition silent.
                    }}
                }});
            }};

            resetScrollPosition();
            requestAnimationFrame(resetScrollPosition);
            setTimeout(resetScrollPosition, 0);
        </script>
        <div data-scroll-reset="{nonce}" style="height:0;"></div>
        """,
        height=0,
    )
    st.session_state.pending_scroll_reset = False


def navigate_to(view_key: str):
    st.session_state.active_view = view_key
    _schedule_scroll_reset()


def navigate_home():
    st.session_state.active_view = None
    _schedule_scroll_reset()


# 5. Carga de datos según la vista activa
geojson_col = None
df_colombia = pd.DataFrame()
df_ciudades_mapa = pd.DataFrame()
df_hist = pd.DataFrame()
df_hist_linea = pd.DataFrame()
lista_deptos = ["TOTAL NACIONAL"]
lista_ciudades = ["TODAS LAS CIUDADES"]
total_nacional = 0
metrica_delito_top_global = {"delito": "—", "casos": 0}
depto_top = {}
delito_top_global = "—"
casos_delito_top_global = 0
anio_top = None

if st.session_state.active_view in {None, "total_casos", "depto_top", "delito_top"}:
    try:
        metricas_contexto = cargar_contexto_metricas_globales()
        total_nacional = int(metricas_contexto["total_nacional"])
        metrica_delito_top_global = metricas_contexto["metrica_delito_top_global"]
    except Exception:
        metricas_contexto = {"total_nacional": 0, "metrica_delito_top_global": {"delito": "—", "casos": 0}}

try:
    if st.session_state.active_view is None:
        dashboard_contexto = ejecutar_con_texto_temporal(
            "Cargando dashboard...",
            cargar_contexto_dashboard_principal,
        )
        geojson_col = dashboard_contexto["geojson_col"]
        df_colombia = dashboard_contexto["df_colombia"]
        df_ciudades_mapa = dashboard_contexto["df_ciudades_mapa"]
        df_hist = dashboard_contexto["df_hist"]
        df_hist_linea = dashboard_contexto["df_hist_linea"]
        lista_deptos = dashboard_contexto["lista_deptos"]
        lista_ciudades = dashboard_contexto["lista_ciudades"]
        depto_top = dashboard_contexto["depto_top"]
        anio_top = dashboard_contexto["anio_top"]
    elif st.session_state.active_view == "total_casos":
        total_contexto = ejecutar_con_texto_temporal(
            API_LOADING_TEXT,
            cargar_contexto_total_casos,
        )
        df_colombia = total_contexto["df_colombia"]
        df_ciudades_mapa = total_contexto["df_ciudades_mapa"]
        df_hist = total_contexto["df_hist"]
        depto_top = total_contexto["depto_top"]
        anio_top = total_contexto["anio_top"]
        if not total_nacional:
            total_nacional = int(df_colombia["Casos"].sum())
    elif st.session_state.active_view == "depto_top":
        depto_contexto = ejecutar_con_texto_temporal(
            API_LOADING_TEXT,
            cargar_contexto_depto_top,
        )
        df_ciudades_mapa = depto_contexto["df_ciudades_mapa"]
        depto_top = depto_contexto["depto_top"]
    elif st.session_state.active_view == "anio_pico":
        historial_contexto = ejecutar_con_texto_temporal(
            API_LOADING_TEXT,
            cargar_contexto_anio_pico,
        )
        df_hist = historial_contexto["df_hist"]
        df_hist_linea = historial_contexto["df_hist_linea"]
        anio_top = historial_contexto["anio_top"]
except Exception as e:
    if str(e) == API_DEPTO_EMPTY_TEXT:
        st.markdown(render_target_text(API_DEPTO_EMPTY_TEXT), unsafe_allow_html=True)
    else:
        st.error(f"No se pudieron cargar los datos desde la API: {e}")
    st.stop()

if not total_nacional and not df_colombia.empty:
    total_nacional = int(df_colombia["Casos"].sum())

delito_top_global = str(metrica_delito_top_global["delito"]).strip() or "—"
casos_delito_top_global = int(metrica_delito_top_global["casos"])

# 6. Renderizado condicional
_render_pending_scroll_reset()

if st.session_state.active_view is not None:
    render_detail_view(
        st.session_state.active_view,
        total_nacional=total_nacional,
        df_colombia=df_colombia,
        df_ciudades_mapa=df_ciudades_mapa,
        df_hist=df_hist,
        df_hist_linea=df_hist_linea,
        depto_top=depto_top,
        anio_top=anio_top,
        delito_top_global=delito_top_global,
        casos_delito_top_global=casos_delito_top_global,
        navigate_home=navigate_home,
    )
else:
    render_dashboard_principal(
        df_colombia=df_colombia,
        df_ciudades_mapa=df_ciudades_mapa,
        df_hist_linea=df_hist_linea,
        lista_deptos=lista_deptos,
        lista_ciudades=lista_ciudades,
        total_nacional=total_nacional,
        delito_top_global=delito_top_global,
        casos_delito_top_global=casos_delito_top_global,
        depto_top=depto_top,
        anio_top=anio_top,
        geojson_col=geojson_col,
        navigate_to=navigate_to,
        navigate_home=navigate_home,
    )
