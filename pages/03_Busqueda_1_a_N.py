from __future__ import annotations
import streamlit as st
from core.faces import DEEPFACE_OK, extract_faces_from_pil, represent_face, uploaded_to_pil
from core.storage import add_face_to_db, add_history, load_db, search_db

st.title("🔎 Búsqueda 1:N sobre base local")
if not DEEPFACE_OK:
    st.error("DeepFace no está disponible en este entorno.")
    st.stop()

threshold = st.slider("Umbral de búsqueda", 0.50, 0.95, 0.72, 0.01)
uploaded = st.file_uploader("Imagen consulta", type=["jpg", "jpeg", "png"])

if uploaded:
    img = uploaded_to_pil(uploaded)
    st.image(img, caption="Consulta", use_container_width=True)
    faces = extract_faces_from_pil(img)
    if faces:
        face = faces[0]
        st.image(face.image, caption="Rostro normalizado", width=240)
        emb = represent_face(face.image)
        cols = st.columns([2,1])
        with cols[0]:
            if st.button("Buscar en base", type="primary"):
                results = search_db(emb, threshold=threshold)
                add_history("busqueda_1_n", {"file": uploaded.name, "summary": f"matches={len(results)}"})
                if not results:
                    st.info("Sin coincidencias por arriba del umbral.")
                else:
                    for i, r in enumerate(results, start=1):
                        st.success(f"#{i} {r['name']} | score={r['score']:.4f} | {r['created_at']}")
                        if r.get("note"):
                            st.caption(r['note'])
        with cols[1]:
            with st.expander("Guardar en base"):
                name = st.text_input("Etiqueta", value="Persona X")
                note = st.text_area("Nota", value="")
                if st.button("Guardar embedding"):
                    add_face_to_db(emb, name, note)
                    add_history("guardar_base_local", {"file": uploaded.name, "summary": name})
                    st.success("Guardado en base local.")
    else:
        st.warning("No se detectó rostro.")

with st.expander("Ver tamaño actual de la base"):
    st.write(f"Registros: {len(load_db())}")
