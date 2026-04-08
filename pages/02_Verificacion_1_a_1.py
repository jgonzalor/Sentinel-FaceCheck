from __future__ import annotations
import streamlit as st
from core.faces import DEEPFACE_OK, cosine_similarity, extract_faces_from_pil, represent_face, uploaded_to_pil
from core.storage import add_history

st.title("✅ Verificación 1:1")
if not DEEPFACE_OK:
    st.error("DeepFace no está disponible en este entorno.")
    st.stop()

threshold = st.slider("Umbral de coincidencia", 0.50, 0.95, 0.72, 0.01)
file_a = st.file_uploader("Imagen A", type=["jpg", "jpeg", "png"], key="a")
file_b = st.file_uploader("Imagen B", type=["jpg", "jpeg", "png"], key="b")

if file_a and file_b and st.button("Comparar", type="primary"):
    img_a = uploaded_to_pil(file_a)
    img_b = uploaded_to_pil(file_b)
    faces_a = extract_faces_from_pil(img_a)
    faces_b = extract_faces_from_pil(img_b)
    if not faces_a or not faces_b:
        st.warning("Se requiere al menos un rostro detectable en ambas imágenes.")
    else:
        emb_a = represent_face(faces_a[0].image)
        emb_b = represent_face(faces_b[0].image)
        score = cosine_similarity(emb_a, emb_b)
        matched = score >= threshold
        add_history("verificacion_1_1", {"file": f"{file_a.name} vs {file_b.name}", "summary": f"score={score:.4f}"})
        c1, c2, c3 = st.columns(3)
        c1.image(faces_a[0].image, caption="Rostro A", use_container_width=True)
        c2.image(faces_b[0].image, caption="Rostro B", use_container_width=True)
        with c3:
            st.metric("Score", f"{score:.4f}")
            st.metric("Umbral", f"{threshold:.2f}")
            st.success("Coincidencia probable") if matched else st.error("No coincide")
