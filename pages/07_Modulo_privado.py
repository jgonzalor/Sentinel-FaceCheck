from __future__ import annotations
import streamlit as st
from core.storage import add_history

st.title("🧩 Módulo privado / integración externa")
st.caption("Page aislada para pegar tu módulo privado sin romper la navegación general de Streamlit.")

st.warning(
    "Esta página está reservada para tu integración privada. "
    "Puedes reemplazar este archivo completo por tu propio módulo, o pegar tu lógica dentro de la función render_private_module()."
)

st.markdown("""
### Dónde pegar tu módulo
Tienes dos rutas seguras:

**Ruta 1 — Reemplazo total**
- Sustituye por completo este archivo `pages/07_Modulo_privado.py` con el código que ya tienes.
- Mantén el nombre del archivo para que Streamlit lo siga mostrando en el menú lateral.

**Ruta 2 — Pegado dentro de la función**
- Deja esta estructura.
- Pega tu lógica dentro de `render_private_module()`.
- Usa `st.session_state` para persistir resultados entre clics.
- Si tu módulo necesita librerías nuevas, agrégalas a `requirements.txt`.

### Reglas prácticas para no romper la app
- No uses `st.set_page_config()` dentro de esta page.
- No cambies rutas de `data/` si quieres conservar historial y base local.
- Si guardas archivos temporales, usa `tempfile`.
- Si agregas botones encadenados, persiste salidas en `st.session_state`.
- Si tu módulo guarda eventos, llama a `add_history(...)` para que aparezcan en Auditoría.
""")

with st.expander("Ejemplo mínimo de registro en auditoría"):
    st.code(
        """
from core.storage import add_history

add_history(
    "modulo_privado",
    {
        "file": "ejemplo.jpg",
        "summary": "evento de prueba"
    }
)
        """.strip(),
        language="python",
    )


def render_private_module() -> None:
    st.info("Aquí cae tu módulo privado. Reemplaza este contenido por tu código.")
    demo_name = st.text_input("Prueba rápida", value="modulo_privado_ok")
    if st.button("Registrar evento de prueba"):
        add_history("modulo_privado", {"file": "manual", "summary": demo_name})
        st.success("Evento agregado al historial.")


render_private_module()
