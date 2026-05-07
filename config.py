BASE_API = "https://www.datos.gov.co/resource/4v6r-wu98.json"
MAPA_URL = "https://raw.githubusercontent.com/jacasta2/colombian_map/main/from_shapefiles/departamentos/mapa_departamentos_q3.json"
MAPA_MUNICIPIOS_URL = "https://raw.githubusercontent.com/jacasta2/colombian_map/main/from_shapefiles/municipios/mapa_municipios_q3.json"
HISTORICAL_YEAR_START = 2006
HISTORICAL_YEAR_END = 2025
MAPA_COLOMBIA_LOADING_TEXT = "Cargando mapa de Colombia..."
MAPA_MUNICIPAL_LOADING_TEXT = "Cargando mapa municipal..."
API_LOADING_TEXT = "Consultando datos desde la API..."
API_DEPTO_EMPTY_TEXT = "La API no devolvió datos por departamento."

# TTL del caché de datos (en segundos).
# 3600 = 1 hora. Reduce llamadas a la API y consumo de RAM con muchos usuarios.
CACHE_TTL = 3600

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#cbd5e1"),
    hoverlabel=dict(
        bgcolor="#1e293b",
        font_size=13,
        font_family="Inter, sans-serif",
        font_color="#e2e8f0",
        bordercolor="#334155",
    ),
    margin=dict(t=10, b=40, l=50, r=20),
)
