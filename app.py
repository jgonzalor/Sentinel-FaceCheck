from __future__ import annotations
import streamlit as st
from core.config import APP_ICON, APP_TITLE, DATA_DIR, external_mode
from core.faces import DEEPFACE_OK, DEEPFACE_ERROR
from core.storage import load_db, load_history

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

st.title(f"{APP_ICON} {APP_TITLE}")
st.caption("Dashboard central con app.py como controlador y páginas clásicas en /pages")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Registros base local", len(load_db()))
col2.metric("Eventos historial", len(load_history()))
col3.metric("Modo búsqueda externa", external_mode())
col4.metric("Motor facial", "Disponible" if DEEPFACE_OK else "No disponible")

if not DEEPFACE_OK:
    st.warning(f"DeepFace no está disponible: {DEEPFACE_ERROR}")

st.markdown("""
### Qué hace esta app
- **Detección**: localiza y recorta rostros en imágenes.
- **Verificación 1:1**: compara dos rostros.
- **Búsqueda 1:N**: busca coincidencias en tu base local.
- **Lote**: procesa varias imágenes.
- **Búsqueda visual externa**: centraliza motores externos sobre **imagen completa** y registra resultados.
- **Auditoría**: historial persistente y exportación PDF/JSON.

### Navegación
Usa el menú lateral automático de Streamlit para abrir las páginas dentro de `pages/`.

### Integración privada
La page `07_Modulo_privado.py` está aislada para que pegues tu módulo privado sin tocar el resto de la app.
""")

with st.sidebar:
    st.header("Estado")
    st.write(f"Data dir: `{DATA_DIR}`")
    st.info("Las páginas se cargan automáticamente desde la carpeta pages.")
