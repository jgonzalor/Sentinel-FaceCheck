import os
import json
import tempfile
from datetime import datetime

import streamlit as st


PAGE_TITLE = "Módulo privado"
PAGE_ICON = "🧩"

DATA_DIR = "data"
PRIVATE_LOG = os.path.join(DATA_DIR, "private_module_log.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_private_log():
    _ensure_data_dir()
    if os.path.exists(PRIVATE_LOG):
        try:
            with open(PRIVATE_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_private_log(items):
    _ensure_data_dir()
    with open(PRIVATE_LOG, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _append_private_log(event_type: str, payload: dict):
    items = _load_private_log()
    items.insert(0, {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "payload": payload,
    })
    _save_private_log(items[:100])


def run_external_module(
    uploaded_files,
    enable_batch: bool,
    private_api_key: str,
    case_ref: str,
    threshold: float,
):
    """
    PEGA AQUÍ la lógica del módulo que ya te dio la otra IA.

    Debes usar:
    - uploaded_files: lista de archivos de Streamlit
    - enable_batch: True/False
    - private_api_key: secreto opcional
    - case_ref: referencia del caso
    - threshold: umbral configurable

    Recomendación:
    - guarda temporales con tempfile.NamedTemporaryFile(...)
    - usa st.session_state si ocupas persistencia entre botones
    - regresa una lista de resultados serializables
    """

    st.info("Aquí debes pegar tu módulo privado dentro de run_external_module().")

    # EJEMPLO DE ESTRUCTURA DE SALIDA
    demo_results = []
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name

        demo_results.append({
            "archivo": file.name,
            "ruta_temporal": tmp_path,
            "estado": "pendiente_de_modulo_privado",
            "motor": "privado",
            "coincidencias": [],
        })

    return demo_results


def render_results(results):
    if not results:
        st.warning("No hay resultados.")
        return

    st.subheader("Resultados del módulo privado")
    for idx, item in enumerate(results, start=1):
        with st.expander(f"{idx}. {item.get('archivo', 'Sin nombre')}"):
            st.json(item)


def render_private_module():
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.caption("Page aislada para pegar tu módulo externo sin romper la navegación general.")

    case_ref = st.text_input("Referencia del caso", value=st.session_state.get("case_ref", "CASO-LOCAL-001"))
    threshold = st.slider("Umbral", min_value=0.10, max_value=0.99, value=0.35, step=0.01)
    enable_batch = st.checkbox("Procesamiento por lote", value=True)
    private_api_key = st.text_input("API Key / token opcional", value="", type="password")

    uploaded_files = st.file_uploader(
        "Sube una o varias imágenes",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        run_btn = st.button("Ejecutar módulo privado", type="primary", use_container_width=True)

    with col2:
        if st.button("Ver historial privado", use_container_width=True):
            history = _load_private_log()
            if history:
                st.subheader("Historial del módulo privado")
                st.json(history[:20])
            else:
                st.info("Sin historial todavía.")

    if run_btn:
        if not uploaded_files:
            st.error("Primero sube al menos una imagen.")
            return

        try:
            results = run_external_module(
                uploaded_files=uploaded_files,
                enable_batch=enable_batch,
                private_api_key=private_api_key,
                case_ref=case_ref,
                threshold=threshold,
            )

            st.session_state["private_module_results"] = results
            _append_private_log(
                event_type="private_module_run",
                payload={
                    "case_ref": case_ref,
                    "total_archivos": len(uploaded_files),
                    "threshold": threshold,
                    "enable_batch": enable_batch,
                    "resultados": len(results) if isinstance(results, list) else 0,
                },
            )

        except Exception as e:
            st.exception(e)
            _append_private_log(
                event_type="private_module_error",
                payload={
                    "case_ref": case_ref,
                    "error": str(e),
                },
            )

    if "private_module_results" in st.session_state:
        render_results(st.session_state["private_module_results"])


render_private_module()
