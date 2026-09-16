# Cibercrímenes en Colombia

Dashboard interactivo desarrollado con Streamlit para explorar casos de cibercrimen en Colombia mediante indicadores, mapas por departamento y municipio, y gráficos históricos. El período histórico configurado es 2006–2025.

## Requisitos

- Python 3.12 (entorno preparado con Python 3.12.10 de 64 bits).
- Conexión a internet para instalar dependencias y consultar los datos y mapas.

Las dependencias se encuentran en `requirements.txt`: Streamlit, pandas, Plotly y requests. La configuración actual no requiere claves de API ni un archivo `.env`.

> Entorno preparado el 16 de septiembre de 2026 en `.venv`: Python 3.12.10, Streamlit 1.56.0, pandas 3.0.5, Plotly 7.1.0 y requests 2.34.2. Se verificaron las dependencias con `pip check`, la importación de los módulos y el arranque del servidor Streamlit. No se verificó la carga completa de los datos externos ni todas las vistas. El servidor de comprobación se detuvo al finalizar.

## Instalación en Windows (PowerShell)

Abre una terminal en la carpeta del proyecto:

```powershell
cd "C:\Users\Ronald\Documents\Dashboard\Cibercrimenes_Colombia"
```

Para preparar el proyecto desde cero, crea el entorno virtual e instala las dependencias:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si acabas de instalar Python, abre una terminal nueva para que se actualice el PATH. Si utilizas el administrador de instalación de Python y aún no tienes la versión 3.12, instálala antes de crear el entorno:

```powershell
py install 3.12
```

## Ejecutar

Si el entorno `.venv` ya está preparado, solo necesitas ejecutar este comando desde la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abre [http://localhost:8501](http://localhost:8501) en el navegador. Para detener el servidor, presiona `Ctrl+C` en la terminal.

Los comandos usan directamente el Python del entorno virtual; no es necesario activarlo ni cambiar la política de ejecución de PowerShell.

## Datos y configuración

- Los casos se consultan en la API pública de Datos Abiertos de Colombia: `https://www.datos.gov.co/resource/4v6r-wu98.json`.
- Los mapas se descargan del repositorio `jacasta2/colombian_map` en GitHub.
- `config.py` define las fuentes, el rango de años, los estilos de gráficos y el tiempo de caché (una hora por defecto).
- La primera carga puede tardar mientras se consultan los servicios externos. La disponibilidad y actualización de los datos dependen de estas fuentes.

## Estructura

| Archivo | Función |
| --- | --- |
| `app.py` | Punto de entrada y navegación entre vistas. |
| `data.py` | Consultas, transformación de datos y procesamiento de mapas. |
| `ui.py` | Indicadores, gráficos y vistas del dashboard. |
| `styles.py` | Estilos visuales. |
| `config.py` | Configuración general. |
| `requirements.txt` | Dependencias de Python. |

## Problemas frecuentes

- **No se encuentra un módulo:** ejecuta nuevamente `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` y usa el comando de ejecución indicado arriba.
- **No se pueden cargar datos desde la API:** verifica tu conexión y el acceso a `www.datos.gov.co` y `raw.githubusercontent.com`; si el servicio externo falla, vuelve a intentarlo más tarde.
- **El puerto 8501 está ocupado:** ejecuta `.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502` y abre [http://localhost:8502](http://localhost:8502).

Para comprobar la compatibilidad de las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -m pip check
```
