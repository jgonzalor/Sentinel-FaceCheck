from __future__ import annotations
import streamlit as st
from core.faces import DEEPFACE_OK, analyze_face, extract_faces_from_pil, uploaded_to_pil
from core.storage import add_history

st.title("📷 Detección y extracción")
if not DEEPFACE_OK:
    st.error("DeepFace no está disponible en este entorno.")
    st.stop()

detector = st.selectbox("Detector", ["retinaface", "opencv", "mtcnn"], index=0)
uploaded = st.file_uploader("Sube una imagen", type=["jpg", "jpeg", "png", "webp"])

if uploaded:
    img = uploaded_to_pil(uploaded)
    st.image(img, caption="Imagen original", use_container_width=True)
    if st.button("Analizar", type="primary"):
        faces = extract_faces_from_pil(img, detector=detector)
        add_history("deteccion", {"file": uploaded.name, "summary": f"rostros={len(faces)}"})
        if not faces:
            st.warning("No se detectaron rostros.")
        for idx, face in enumerate(faces, start=1):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(face.image, caption=f"Rostro {idx}", use_container_width=True)
            with col2:
                st.json({"confidence": round(face.confidence, 4), "facial_area": face.facial_area})
                try:
                    info = analyze_face(face.image)
                    st.write({
                        "age": int(info.get("age", 0)),
                        "gender": info.get("dominant_gender", "?"),
                        "emotion": info.get("dominant_emotion", "?"),
                    })
                except Exception as exc:
                    st.error(f"No se pudo analizar el rostro: {exc}")
