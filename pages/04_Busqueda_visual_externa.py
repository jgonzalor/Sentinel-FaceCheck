from __future__ import annotations
import tempfile
import streamlit as st
from PIL import Image
from core.config import external_mode, google_lens_enabled, lenso_api_key, yandex_enabled
from core.external_search import google_lens_search, lenso_search, manual_provider_links, yandex_search_url
from core.storage import add_history

st.title("🌐 Búsqueda visual externa")
st.caption("Motor externo sobre imagen completa. No identifica personas por rostro ni devuelve perfiles sociales automáticamente.")

uploaded = st.file_uploader("Sube una imagen para búsqueda visual externa", type=["jpg", "jpeg", "png", "webp"])
mode = external_mode()

c1, c2, c3 = st.columns(3)
c1.metric("Modo", mode)
c2.metric("Google Lens wrapper", "ON" if google_lens_enabled() else "OFF")
c3.metric("Yandex web", "ON" if yandex_enabled() else "OFF")

st.info("Automático: Google Lens wrapper y/o Lenso API si los configuraste. Semiautomático: Yandex devuelve URL de resultados. Manual: TinEye/Baidu/Bing/Lens web/Lenso web.")

if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, caption="Imagen consulta", use_container_width=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(tmp.name)

    tab1, tab2, tab3 = st.tabs(["Automático / configurable", "Semiautomático", "Manual"])

    with tab1:
        if st.button("Consultar proveedores configurados", type="primary"):
            total = 0
            try:
                gl = google_lens_search(tmp.name)
                if gl:
                    st.subheader("Google Lens")
                    for row in gl:
                        st.markdown(f"- [{row.title}]({row.url})")
                    total += len(gl)
            except Exception as exc:
                st.error(f"Google Lens: {exc}")
            try:
                le = lenso_search(tmp.name) if lenso_api_key().strip() else []
                if le:
                    st.subheader("Lenso.ai API")
                    for row in le:
                        st.markdown(f"- [{row.title}]({row.url})")
                    total += len(le)
            except Exception as exc:
                st.error(f"Lenso.ai: {exc}")
            add_history("busqueda_visual_externa_auto", {"file": uploaded.name, "summary": f"resultados={total}"})
            if total == 0:
                st.warning("No hubo resultados automáticos configurados o disponibles.")

    with tab2:
        if st.button("Generar búsqueda Yandex"):
            try:
                url = yandex_search_url(tmp.name)
                st.success("URL generada")
                st.markdown(f"[Abrir resultados Yandex]({url})")
                add_history("busqueda_visual_externa_yandex", {"file": uploaded.name, "summary": "url_generada"})
            except Exception as exc:
                st.error(f"Yandex: {exc}")

    with tab3:
        st.write("Motores manuales / asistidos")
        for name, url in manual_provider_links().items():
            st.markdown(f"- [{name}]({url})")
        add_history("busqueda_visual_externa_manual", {"file": uploaded.name, "summary": "links_mostrados"})
