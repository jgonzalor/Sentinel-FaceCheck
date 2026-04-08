from __future__ import annotations
import streamlit as st
from core.faces import DEEPFACE_OK, extract_faces_from_pil, uploaded_to_pil
from core.storage import add_history

st.title("🗂️ Procesamiento por lote")
if not DEEPFACE_OK:
    st.error("DeepFace no está disponible en este entorno.")
    st.stop()

files = st.file_uploader("Sube varias imágenes", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
if files and st.button("Procesar lote", type="primary"):
    rows = []
    total_faces = 0
    for uf in files:
        img = uploaded_to_pil(uf)
        faces = extract_faces_from_pil(img)
        total_faces += len(faces)
        rows.append({"archivo": uf.name, "rostros": len(faces)})
    st.dataframe(rows, use_container_width=True)
    add_history("lote", {"file": f"{len(files)} archivos", "summary": f"rostros={total_faces}"})
