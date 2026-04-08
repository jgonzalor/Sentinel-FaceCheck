from __future__ import annotations
import json
import os
import tempfile
import streamlit as st
from core.storage import build_pdf_report, load_history

st.title("🧾 Auditoría e historial")
history = load_history()
st.metric("Eventos", len(history))

if history:
    st.dataframe(history, use_container_width=True)
    st.download_button(
        "Descargar historial JSON",
        data=json.dumps(history, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="historial.json",
        mime="application/json",
    )
    if st.button("Generar PDF"):
        out = os.path.join(tempfile.gettempdir(), "reporte_historial.pdf")
        build_pdf_report(history, out)
        with open(out, "rb") as f:
            st.download_button("Descargar PDF", f.read(), file_name="reporte_historial.pdf", mime="application/pdf")
else:
    st.info("No hay eventos todavía.")
