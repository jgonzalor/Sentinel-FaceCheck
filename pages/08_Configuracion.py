from __future__ import annotations
import streamlit as st
from core.config import external_mode, google_lens_enabled, lenso_api_key, yandex_enabled, DATA_DIR

st.title("⚙️ Configuración")
st.caption("Resumen de estado para motores externos y rutas internas.")

c1, c2 = st.columns(2)
with c1:
    st.metric("Modo búsqueda externa", external_mode())
    st.metric("Google Lens wrapper", "ON" if google_lens_enabled() else "OFF")
    st.metric("Yandex web", "ON" if yandex_enabled() else "OFF")
with c2:
    st.metric("Lenso API key", "Configurada" if lenso_api_key().strip() else "Vacía")
    st.code(f"DATA_DIR = {DATA_DIR}")

st.markdown("""
### Secrets opcionales para Streamlit Cloud
```toml
ENABLE_GOOGLE_LENS=true
ENABLE_YANDEX_WEB=true
EXTERNAL_SEARCH_MODE="assist"
LENSO_API_KEY="tu_key_opcional"
```
""")
