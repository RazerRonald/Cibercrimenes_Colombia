import json
from urllib.parse import urlencode

import pandas as pd
import requests
import streamlit as st

from config import (
    BASE_API,
    MAPA_URL,
    MAPA_MUNICIPIOS_URL,
    HISTORICAL_YEAR_START,
    HISTORICAL_YEAR_END,
    PLOTLY_LAYOUT,
    CACHE_TTL,
)


# ============================================================================
# TOPOJSON -> GEOJSON
# ============================================================================

def _decode_delta(arcs_encoded):
    result = []
    x, y = 0, 0
    for dx, dy in arcs_encoded:
        x += dx
        y += dy
        result.append([x, y])
    return result


def _transform_point(point, transform):
    scale = transform["scale"]
    translate = transform["translate"]
    return [
        point[0] * scale[0] + translate[0],
        point[1] * scale[1] + translate[1],
    ]


def _arc_to_coords(arc_index, arcs_raw, transform):
    if arc_index < 0:
        arc_index = ~arc_index
        pts = [_transform_point(p, transform) for p in _decode_delta(arcs_raw[arc_index])]
        pts.reverse()
    else:
        pts = [_transform_point(p, transform) for p in _decode_delta(arcs_raw[arc_index])]
    return pts


def _ring_coords(ring, arcs_raw, transform):
    coords = []
    for i, arc_idx in enumerate(ring):
        pts = _arc_to_coords(arc_idx, arcs_raw, transform)
        if i == 0:
            coords.extend(pts)
        else:
            coords.extend(pts[1:])
    return coords


def topojson_to_geojson(topo, object_name):
    transform = topo.get("transform", {"scale": [1, 1], "translate": [0, 0]})
    arcs_raw = topo["arcs"]
    obj = topo["objects"][object_name]
    features = []
    for geom in obj["geometries"]:
        props = geom.get("properties", {})
        gtype = geom["type"]
        if gtype == "Polygon":
            rings = [[_ring_coords(r, arcs_raw, transform)] for r in geom["arcs"]]
            geo = {"type": "Polygon", "coordinates": rings[0]}
        elif gtype == "MultiPolygon":
            polys = []
            for poly_arcs in geom["arcs"]:
                polys.append([_ring_coords(r, arcs_raw, transform) for r in poly_arcs])
            geo = {"type": "MultiPolygon", "coordinates": polys}
        else:
            continue
        features.append({
            "type": "Feature",
            "geometry": geo,
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


# ============================================================================
# HELPERS GEO
# ============================================================================

def extraer_puntos_geometria(geometry):
    gtype = geometry["type"]
    coords = geometry["coordinates"]
    puntos = []
    if gtype == "Polygon":
        for ring in coords:
            puntos.extend(ring)
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                puntos.extend(ring)
    return puntos


def centroid_simple(geometry):
    puntos = extraer_puntos_geometria(geometry)
    if not puntos:
        return 4.5709, -74.2973
    lons = [p[0] for p in puntos]
    lats = [p[1] for p in puntos]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def construir_centroides_por_departamento(geojson_col):
    filas = []
    for feature in geojson_col["features"]:
        props = feature["properties"]
        codigo = props.get("codigo_departamento_n")
        nombre = props.get("departamento")
        lat, lon = centroid_simple(feature["geometry"])
        filas.append({
            "Codigo_DANE": pd.to_numeric(codigo, errors="coerce"),
            "Departamento_geo": str(nombre).upper().strip(),
            "Lat": lat,
            "Lon": lon,
        })
    df = pd.DataFrame(filas).dropna(subset=["Codigo_DANE"])
    df["Codigo_DANE"] = df["Codigo_DANE"].astype(int)
    return df


def construir_centroides_por_municipio(geojson_col):
    filas = []
    for feature in geojson_col["features"]:
        props = feature["properties"]
        codigo = props.get("codigo_municipio_n")
        lat, lon = centroid_simple(feature["geometry"])
        filas.append({
            "Codigo_Municipio": pd.to_numeric(codigo, errors="coerce"),
            "Lat_Ciudad": lat,
            "Lon_Ciudad": lon,
        })
    df = pd.DataFrame(filas).dropna(subset=["Codigo_Municipio"])
    df["Codigo_Municipio"] = df["Codigo_Municipio"].astype(int)
    return df


# ============================================================================
# CONSUMO API
# ============================================================================

def consultar_api(params):
    url = f"{BASE_API}?{urlencode(params)}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def consultar_api_todas_paginas(params, page_size: int = 1000):
    resultados = []
    offset = 0

    while True:
        page_params = dict(params)
        page_params["$limit"] = page_size
        page_params["$offset"] = offset
        batch = consultar_api(page_params)

        if not batch:
            break

        resultados.extend(batch)
        if len(batch) < page_size:
            break

        offset += page_size

    return resultados


@st.cache_data(show_spinner=False)
def cargar_geojson():
    resp = requests.get(MAPA_URL, timeout=30)
    resp.raise_for_status()
    topo = resp.json()
    return topojson_to_geojson(topo, "MGN_DPTO_POLITICO_rJAC")


@st.cache_data(show_spinner=False)
def cargar_geojson_municipios():
    resp = requests.get(MAPA_MUNICIPIOS_URL, timeout=60)
    resp.raise_for_status()
    topo = resp.json()
    return topojson_to_geojson(topo, "MGN_MPIO_POLITICO_rJAC")


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_datos_departamentos_api():
    from config import API_DEPTO_EMPTY_TEXT

    params_depto = {
        "$select": "cod_depto, departamento, count(*) as casos",
        "$where": "cod_depto IS NOT NULL AND departamento IS NOT NULL",
        "$group": "cod_depto, departamento",
        "$order": "count(*) DESC",
    }
    data_depto = consultar_api_todas_paginas(params_depto)
    df_depto = pd.DataFrame(data_depto)
    if df_depto.empty:
        raise ValueError(API_DEPTO_EMPTY_TEXT)
    df_depto["Codigo_DANE"] = pd.to_numeric(df_depto["cod_depto"], errors="coerce")
    df_depto["Departamento"] = df_depto["departamento"].astype(str).str.upper().str.strip()
    df_depto["Casos"] = pd.to_numeric(df_depto["casos"], errors="coerce").fillna(0).astype(int)
    df_depto = df_depto[["Codigo_DANE", "Departamento", "Casos"]].dropna(subset=["Codigo_DANE"])
    df_depto["Codigo_DANE"] = df_depto["Codigo_DANE"].astype(int)

    params_delito_depto = {
        "$select": "cod_depto, departamento, descripcion_conducta, count(*) as casos",
        "$where": "cod_depto IS NOT NULL AND departamento IS NOT NULL AND descripcion_conducta IS NOT NULL",
        "$group": "cod_depto, departamento, descripcion_conducta",
        "$order": "cod_depto ASC, count(*) DESC, descripcion_conducta ASC",
    }
    data_delito_depto = consultar_api_todas_paginas(params_delito_depto)
    df_delito_depto = pd.DataFrame(data_delito_depto)
    if df_delito_depto.empty:
        raise ValueError("La API no devolvió datos de delitos por departamento.")
    df_delito_depto["Codigo_DANE"] = pd.to_numeric(df_delito_depto["cod_depto"], errors="coerce")
    df_delito_depto["Departamento"] = df_delito_depto["departamento"].astype(str).str.upper().str.strip()
    df_delito_depto["Delito_Principal"] = df_delito_depto["descripcion_conducta"].astype(str).str.strip()
    df_delito_depto["Casos_Delito"] = pd.to_numeric(df_delito_depto["casos"], errors="coerce").fillna(0).astype(int)
    df_delito_depto = df_delito_depto.dropna(subset=["Codigo_DANE"])
    df_delito_depto["Codigo_DANE"] = df_delito_depto["Codigo_DANE"].astype(int)
    df_delito_depto = (
        df_delito_depto
        .sort_values(["Codigo_DANE", "Casos_Delito", "Delito_Principal"], ascending=[True, False, True])
        .drop_duplicates(subset=["Codigo_DANE"])
        [["Codigo_DANE", "Delito_Principal"]]
    )

    return df_depto, df_delito_depto


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_datos_municipios_api():
    params_muni = {
        "$select": "cod_muni, municipio, cod_depto, departamento, count(*) as casos",
        "$where": "cod_muni IS NOT NULL AND municipio IS NOT NULL AND cod_depto IS NOT NULL AND departamento IS NOT NULL",
        "$group": "cod_muni, municipio, cod_depto, departamento",
        "$order": "count(*) DESC",
    }
    data_muni = consultar_api_todas_paginas(params_muni)
    df_muni = pd.DataFrame(data_muni)
    if df_muni.empty:
        raise ValueError("La API no devolvio datos por municipio.")
    df_muni["Codigo_Municipio"] = pd.to_numeric(df_muni["cod_muni"], errors="coerce")
    df_muni["Codigo_DANE"] = pd.to_numeric(df_muni["cod_depto"], errors="coerce")
    df_muni["Ciudad"] = df_muni["municipio"].astype(str).str.strip()
    df_muni["Departamento"] = df_muni["departamento"].astype(str).str.upper().str.strip()
    df_muni["Casos"] = pd.to_numeric(df_muni["casos"], errors="coerce").fillna(0).astype(int)
    df_muni = df_muni[["Codigo_Municipio", "Codigo_DANE", "Ciudad", "Departamento", "Casos"]].dropna(
        subset=["Codigo_Municipio", "Codigo_DANE"]
    )
    df_muni["Codigo_Municipio"] = df_muni["Codigo_Municipio"].astype(int)
    df_muni["Codigo_DANE"] = df_muni["Codigo_DANE"].astype(int)

    params_delito_muni = {
        "$select": "cod_muni, municipio, descripcion_conducta, count(*) as casos",
        "$where": "cod_muni IS NOT NULL AND municipio IS NOT NULL AND descripcion_conducta IS NOT NULL",
        "$group": "cod_muni, municipio, descripcion_conducta",
        "$order": "cod_muni ASC, count(*) DESC, descripcion_conducta ASC",
    }
    data_delito_muni = consultar_api_todas_paginas(params_delito_muni)
    df_delito_muni = pd.DataFrame(data_delito_muni)
    if df_delito_muni.empty:
        raise ValueError("La API no devolvio datos de delitos por municipio.")
    df_delito_muni["Codigo_Municipio"] = pd.to_numeric(df_delito_muni["cod_muni"], errors="coerce")
    df_delito_muni["Delito_Principal_Ciudad"] = df_delito_muni["descripcion_conducta"].astype(str).str.strip()
    df_delito_muni["Casos_Delito"] = pd.to_numeric(df_delito_muni["casos"], errors="coerce").fillna(0).astype(int)
    df_delito_muni = df_delito_muni.dropna(subset=["Codigo_Municipio"])
    df_delito_muni["Codigo_Municipio"] = df_delito_muni["Codigo_Municipio"].astype(int)
    df_delito_muni = (
        df_delito_muni
        .sort_values(["Codigo_Municipio", "Casos_Delito", "Delito_Principal_Ciudad"], ascending=[True, False, True])
        .drop_duplicates(subset=["Codigo_Municipio"])
        [["Codigo_Municipio", "Delito_Principal_Ciudad"]]
    )

    return df_muni, df_delito_muni


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_datos_historicos_api():
    params_hist = {
        "$select": "date_extract_y(fecha_hecho) as anio, count(*) as casos",
        "$where": "fecha_hecho IS NOT NULL",
        "$group": "date_extract_y(fecha_hecho)",
        "$order": "date_extract_y(fecha_hecho) ASC",
    }
    data_hist = consultar_api_todas_paginas(params_hist)
    df_hist = pd.DataFrame(data_hist)
    if df_hist.empty:
        raise ValueError("La API no devolvió serie histórica.")
    df_hist["Año"] = pd.to_numeric(df_hist["anio"], errors="coerce")
    df_hist["Casos"] = pd.to_numeric(df_hist["casos"], errors="coerce").fillna(0).astype(int)
    df_hist = df_hist[["Año", "Casos"]].dropna().sort_values("Año")
    df_hist["Año"] = df_hist["Año"].astype(int)

    params_ciudad = {
        "$select": "date_extract_y(fecha_hecho) as anio, municipio, count(*) as casos",
        "$where": "fecha_hecho IS NOT NULL AND municipio IS NOT NULL",
        "$group": "date_extract_y(fecha_hecho), municipio",
        "$order": "date_extract_y(fecha_hecho) ASC, count(*) DESC, municipio ASC",
    }
    data_ciudad = consultar_api_todas_paginas(params_ciudad)
    df_ciudad = pd.DataFrame(data_ciudad)
    if not df_ciudad.empty:
        df_ciudad["Año"] = pd.to_numeric(df_ciudad["anio"], errors="coerce")
        df_ciudad["Ciudad_Top"] = df_ciudad["municipio"].astype(str).str.strip()
        df_ciudad["Casos_Ciudad"] = pd.to_numeric(df_ciudad["casos"], errors="coerce").fillna(0).astype(int)
        df_ciudad = (
            df_ciudad
            .dropna(subset=["Año"])
            .sort_values(["Año", "Casos_Ciudad", "Ciudad_Top"], ascending=[True, False, True])
            .drop_duplicates(subset=["Año"])
            [["Año", "Ciudad_Top"]]
        )
        df_ciudad["Año"] = df_ciudad["Año"].astype(int)
    else:
        df_ciudad = pd.DataFrame(columns=["Año", "Ciudad_Top"])

    params_delito_anio = {
        "$select": "date_extract_y(fecha_hecho) as anio, descripcion_conducta, count(*) as casos",
        "$where": "fecha_hecho IS NOT NULL AND descripcion_conducta IS NOT NULL",
        "$group": "date_extract_y(fecha_hecho), descripcion_conducta",
        "$order": "date_extract_y(fecha_hecho) ASC, count(*) DESC, descripcion_conducta ASC",
    }
    data_delito_anio = consultar_api_todas_paginas(params_delito_anio)
    df_delito_anio = pd.DataFrame(data_delito_anio)
    if not df_delito_anio.empty:
        df_delito_anio["Año"] = pd.to_numeric(df_delito_anio["anio"], errors="coerce")
        df_delito_anio["Delito_Top"] = df_delito_anio["descripcion_conducta"].astype(str).str.strip()
        df_delito_anio["Casos_Delito"] = pd.to_numeric(df_delito_anio["casos"], errors="coerce").fillna(0).astype(int)
        df_delito_anio = (
            df_delito_anio
            .dropna(subset=["Año"])
            .sort_values(["Año", "Casos_Delito", "Delito_Top"], ascending=[True, False, True])
            .drop_duplicates(subset=["Año"])
            [["Año", "Delito_Top"]]
        )
        df_delito_anio["Año"] = df_delito_anio["Año"].astype(int)
    else:
        df_delito_anio = pd.DataFrame(columns=["Año", "Delito_Top"])

    return df_hist, df_ciudad, df_delito_anio


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_datos_api():
    df_depto, df_delito_depto = cargar_datos_departamentos_api()
    df_muni, df_delito_muni = cargar_datos_municipios_api()
    df_hist, df_ciudad, df_delito_anio = cargar_datos_historicos_api()
    return df_depto, df_delito_depto, df_muni, df_delito_muni, df_hist, df_ciudad, df_delito_anio


# ============================================================================
# MÉTRICAS KPI
# ============================================================================

@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_metrica_total_casos_nacional():
    params = {
        "$select": "count(*) as casos",
    }
    data = consultar_api(params)
    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError("La API no devolvió el total nacional de casos.")

    return {"casos": int(pd.to_numeric(df.iloc[0]["casos"], errors="coerce") or 0)}


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_metrica_delito_comun_top():
    params = {
        "$select": "descripcion_conducta, count(*) as casos",
        "$where": "descripcion_conducta IS NOT NULL",
        "$group": "descripcion_conducta",
        "$order": "count(*) DESC, descripcion_conducta ASC",
        "$limit": 1,
    }
    data = consultar_api(params)
    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError("La API no devolvió el delito más frecuente.")

    delito = str(df.iloc[0]["descripcion_conducta"]).strip() or "Sin dato"
    casos = int(pd.to_numeric(df.iloc[0]["casos"], errors="coerce") or 0)
    return {"delito": delito, "casos": casos}


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_metrica_delito_comun_participacion():
    params_top = {
        "$select": "descripcion_conducta, count(*) as casos",
        "$where": "descripcion_conducta IS NOT NULL",
        "$group": "descripcion_conducta",
        "$order": "count(*) DESC, descripcion_conducta ASC",
        "$limit": 1,
    }
    params_total = {
        "$select": "count(*) as casos",
    }
    data_top = consultar_api(params_top)
    data_total = consultar_api(params_total)
    df_top = pd.DataFrame(data_top)
    df_total = pd.DataFrame(data_total)
    if df_top.empty or df_total.empty:
        raise ValueError("La API no devolvió la participación del delito líder.")

    casos_top = int(pd.to_numeric(df_top.iloc[0]["casos"], errors="coerce") or 0)
    casos_total = int(pd.to_numeric(df_total.iloc[0]["casos"], errors="coerce") or 0)
    pct = (casos_top / casos_total * 100) if casos_total else 0
    return {"pct": pct}


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_metrica_delito_comun_tipos():
    params = {
        "$select": "count(distinct descripcion_conducta) as total",
        "$where": "descripcion_conducta IS NOT NULL",
    }
    data = consultar_api(params)
    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError("La API no devolvió el total de tipos de delito.")

    total = int(pd.to_numeric(df.iloc[0]["total"], errors="coerce") or 0)
    return {"total": total}


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_chart_delito_comun_rank():
    params = {
        "$select": "descripcion_conducta, count(*) as casos",
        "$where": "descripcion_conducta IS NOT NULL",
        "$group": "descripcion_conducta",
        "$order": "count(*) DESC, descripcion_conducta ASC",
    }
    data = consultar_api_todas_paginas(params)
    return adaptar_ranking_delitos(pd.DataFrame(data))


# ============================================================================
# BUILDERS DE DATAFRAMES
# ============================================================================

def adaptar_ranking_delitos(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw.empty:
        return pd.DataFrame(columns=["Delito_Principal", "Casos"])

    df = df_raw.copy()
    df["Delito_Principal"] = df["descripcion_conducta"].astype(str).str.strip()
    df["Casos"] = pd.to_numeric(df["casos"], errors="coerce").fillna(0).astype(int)
    return (
        df.loc[df["Delito_Principal"].ne(""), ["Delito_Principal", "Casos"]]
        .sort_values(["Casos", "Delito_Principal"], ascending=[False, True])
        .reset_index(drop=True)
    )


def construir_df_colombia_base(df_depto: pd.DataFrame, df_delito_depto: pd.DataFrame) -> pd.DataFrame:
    df_colombia = df_depto.merge(df_delito_depto, on="Codigo_DANE", how="left")
    df_colombia["Delito_Principal"] = df_colombia["Delito_Principal"].fillna("Sin dato")
    return df_colombia


def construir_df_ciudades_base(df_muni: pd.DataFrame, df_delito_muni: pd.DataFrame) -> pd.DataFrame:
    df_ciudades = df_muni.merge(df_delito_muni, on="Codigo_Municipio", how="left")
    df_ciudades["Delito_Principal_Ciudad"] = df_ciudades["Delito_Principal_Ciudad"].fillna("Sin dato")
    return df_ciudades


def construir_contexto_historico(
    df_hist: pd.DataFrame,
    df_ciudad: pd.DataFrame,
    df_delito_anio: pd.DataFrame,
):
    df_hist = (
        df_hist
        .merge(df_ciudad, on="Año", how="left")
        .merge(df_delito_anio, on="Año", how="left")
    )
    df_hist["Ciudad_Top"] = df_hist["Ciudad_Top"].fillna("Sin dato")
    df_hist["Delito_Top"] = df_hist["Delito_Top"].fillna("Sin dato")
    df_hist_linea = (
        df_hist[
            df_hist["Año"].between(HISTORICAL_YEAR_START, HISTORICAL_YEAR_END)
        ][["Año", "Casos", "Ciudad_Top", "Delito_Top"]]
        .set_index("Año")
        .reindex(range(HISTORICAL_YEAR_START, HISTORICAL_YEAR_END + 1))
        .rename_axis("Año")
        .reset_index()
    )
    df_hist_linea["Casos"] = df_hist_linea["Casos"].fillna(0).astype(int)
    df_hist_linea["Ciudad_Top"] = df_hist_linea["Ciudad_Top"].fillna("Sin dato")
    df_hist_linea["Delito_Top"] = df_hist_linea["Delito_Top"].fillna("Sin dato")
    return df_hist, df_hist_linea


def construir_contexto_principal_desde_base(
    df_colombia_base: pd.DataFrame,
    df_ciudades_base: pd.DataFrame,
    geojson_col,
    geojson_municipios,
):
    df_centroides = construir_centroides_por_departamento(geojson_col)
    df_centroides_municipios = construir_centroides_por_municipio(geojson_municipios)

    df_colombia = (
        df_colombia_base
        .merge(df_centroides[["Codigo_DANE", "Lat", "Lon"]], on="Codigo_DANE", how="left")
    )
    df_colombia["Lat"] = df_colombia["Lat"].fillna(4.5709)
    df_colombia["Lon"] = df_colombia["Lon"].fillna(-74.2973)

    df_ciudades_mapa = (
        df_ciudades_base
        .merge(df_centroides_municipios, on="Codigo_Municipio", how="left")
        .merge(
            df_centroides[["Codigo_DANE", "Lat", "Lon"]].rename(columns={"Lat": "Lat_Depto", "Lon": "Lon_Depto"}),
            on="Codigo_DANE",
            how="left",
        )
    )
    df_ciudades_mapa["Lat_Ciudad"] = df_ciudades_mapa["Lat_Ciudad"].fillna(df_ciudades_mapa["Lat_Depto"]).fillna(4.5709)
    df_ciudades_mapa["Lon_Ciudad"] = df_ciudades_mapa["Lon_Ciudad"].fillna(df_ciudades_mapa["Lon_Depto"]).fillna(-74.2973)
    df_ciudades_mapa = df_ciudades_mapa.drop(columns=["Lat_Depto", "Lon_Depto"])

    df_opciones_ciudad = (
        df_ciudades_mapa[["Ciudad", "Departamento"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["Ciudad", "Departamento"])
        .copy()
    )
    df_opciones_ciudad["Etiqueta_Ciudad"] = (
        df_opciones_ciudad["Ciudad"] + " - " + df_opciones_ciudad["Departamento"]
    )

    return {
        "df_colombia": df_colombia,
        "df_ciudades_mapa": df_ciudades_mapa,
        "lista_deptos": ["TOTAL NACIONAL"] + sorted(df_colombia["Departamento"].dropna().unique().tolist()),
        "lista_ciudades": ["TODAS LAS CIUDADES"] + df_opciones_ciudad["Etiqueta_Ciudad"].tolist(),
    }


# ============================================================================
# FUNCIONES DE CARGA DE CONTEXTO POR VISTA
# ============================================================================

@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_contexto_metricas_globales():
    return {
        "total_nacional": cargar_metrica_total_casos_nacional()["casos"],
        "metrica_delito_top_global": cargar_metrica_delito_comun_top(),
    }


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_contexto_total_casos():
    df_depto, df_delito_depto = cargar_datos_departamentos_api()
    df_muni, df_delito_muni = cargar_datos_municipios_api()
    df_hist_raw, df_ciudad, df_delito_anio = cargar_datos_historicos_api()

    df_colombia = construir_df_colombia_base(df_depto, df_delito_depto)
    df_ciudades_mapa = construir_df_ciudades_base(df_muni, df_delito_muni)
    df_hist, _ = construir_contexto_historico(df_hist_raw, df_ciudad, df_delito_anio)

    depto_top = df_colombia.loc[df_colombia["Casos"].idxmax()].to_dict() if not df_colombia.empty else {}
    anio_top = df_hist.loc[df_hist["Casos"].idxmax()].to_dict() if not df_hist.empty else None

    return {
        "df_colombia": df_colombia,
        "df_ciudades_mapa": df_ciudades_mapa,
        "df_hist": df_hist,
        "depto_top": depto_top,
        "anio_top": anio_top,
    }


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_contexto_depto_top():
    df_depto, df_delito_depto = cargar_datos_departamentos_api()
    df_muni, df_delito_muni = cargar_datos_municipios_api()

    df_colombia = construir_df_colombia_base(df_depto, df_delito_depto)
    df_ciudades_mapa = construir_df_ciudades_base(df_muni, df_delito_muni)
    depto_top = df_colombia.loc[df_colombia["Casos"].idxmax()].to_dict() if not df_colombia.empty else {}

    return {
        "df_ciudades_mapa": df_ciudades_mapa,
        "depto_top": depto_top,
    }


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_contexto_anio_pico():
    df_hist_raw, df_ciudad, df_delito_anio = cargar_datos_historicos_api()
    df_hist, df_hist_linea = construir_contexto_historico(df_hist_raw, df_ciudad, df_delito_anio)
    anio_top = df_hist.loc[df_hist["Casos"].idxmax()].to_dict() if not df_hist.empty else None

    return {
        "df_hist": df_hist,
        "df_hist_linea": df_hist_linea,
        "anio_top": anio_top,
    }


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_contexto_delito_top():
    return {}


@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def cargar_contexto_dashboard_principal():
    df_depto, df_delito_depto = cargar_datos_departamentos_api()
    df_muni, df_delito_muni = cargar_datos_municipios_api()
    df_hist_raw, df_ciudad, df_delito_anio = cargar_datos_historicos_api()

    df_colombia_base = construir_df_colombia_base(df_depto, df_delito_depto)
    df_ciudades_base = construir_df_ciudades_base(df_muni, df_delito_muni)
    df_hist, df_hist_linea = construir_contexto_historico(df_hist_raw, df_ciudad, df_delito_anio)

    geojson_col = cargar_geojson()
    geojson_municipios = cargar_geojson_municipios()
    geo_context = construir_contexto_principal_desde_base(
        df_colombia_base=df_colombia_base,
        df_ciudades_base=df_ciudades_base,
        geojson_col=geojson_col,
        geojson_municipios=geojson_municipios,
    )

    return {
        "geojson_col": geojson_col,
        "geojson_municipios": geojson_municipios,
        "df_colombia": geo_context["df_colombia"],
        "df_ciudades_mapa": geo_context["df_ciudades_mapa"],
        "df_hist": df_hist,
        "df_hist_linea": df_hist_linea,
        "lista_deptos": geo_context["lista_deptos"],
        "lista_ciudades": geo_context["lista_ciudades"],
        "depto_top": df_colombia_base.loc[df_colombia_base["Casos"].idxmax()].to_dict() if not df_colombia_base.empty else {},
        "anio_top": df_hist.loc[df_hist["Casos"].idxmax()].to_dict() if not df_hist.empty else None,
    }
