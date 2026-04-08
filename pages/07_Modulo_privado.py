from __future__ import annotations

import os
import io
import json
import base64
import tempfile
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
import numpy as np
import cv2
import requests
from PIL import Image
from fpdf import FPDF

# Dependencias opcionales
try:
    from deepface import DeepFace
    _DEEPFACE_OK = True
except Exception:
    _DEEPFACE_OK = False

try:
    from googlelens import GoogleLens
    _GOOGLE_LENS_OK = True
except Exception:
    _GOOGLE_LENS_OK = False

# ---------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------
PAGE_TITLE = "Módulo privado"
PAGE_ICON = "🧩"

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(DATA_DIR, "rostros_db.json")
HISTORIAL_FILE = os.path.join(DATA_DIR, "historial.json")
PRIVATE_LOG = os.path.join(DATA_DIR, "private_module_log.json")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")

SOCIAL_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "linkedin.com",
    "tiktok.com",
]

# ---------------------------------------------------------------------
# Integración con auditoría central del core (opcional)
# ---------------------------------------------------------------------
try:
    from core.storage import add_history as _core_add_history
    _CORE_HISTORY_OK = True
except Exception:
    _CORE_HISTORY_OK = False


def _add_to_core_history(event: str, payload: Dict[str, Any]) -> None:
    if not _CORE_HISTORY_OK:
        return
    try:
        _core_add_history(
            event,
            {
                "file": payload.get("case_ref", ""),
                "summary": payload.get("summary", str(payload)),
            },
        )
    except Exception:
        pass


# ---------------------------------------------------------------------
# Helpers de archivos / JSON
# ---------------------------------------------------------------------
def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _safe_load_json(path: str, default):
    _ensure_dirs()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _safe_save_json(path: str, payload) -> None:
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _load_db() -> List[Dict[str, Any]]:
    return _safe_load_json(DB_FILE, [])


def _save_db(items: List[Dict[str, Any]]) -> None:
    _safe_save_json(DB_FILE, items)


def _load_historial() -> List[Dict[str, Any]]:
    return _safe_load_json(HISTORIAL_FILE, [])


def _save_historial(items: List[Dict[str, Any]]) -> None:
    _safe_save_json(HISTORIAL_FILE, items)


def _load_private_log() -> List[Dict[str, Any]]:
    return _safe_load_json(PRIVATE_LOG, [])


def _save_private_log(items: List[Dict[str, Any]]) -> None:
    _safe_save_json(PRIVATE_LOG, items)


def _append_private_log(event_type: str, payload: Dict[str, Any]) -> None:
    items = _load_private_log()
    items.insert(
        0,
        {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "payload": payload,
        },
    )
    _save_private_log(items[:100])


# ---------------------------------------------------------------------
# API keys / secrets
# ---------------------------------------------------------------------
def _get_secret(name: str, fallback: str = "") -> str:
    try:
        return st.secrets.get(name, os.getenv(name, fallback))
    except Exception:
        return os.getenv(name, fallback)


def _get_lenso_api_key(widget_value: str) -> str:
    if widget_value.strip():
        return widget_value.strip()
    return _get_secret("LENSO_API_KEY", "")


# ---------------------------------------------------------------------
# Session bootstrap
# ---------------------------------------------------------------------
if "rb_db" not in st.session_state:
    st.session_state.rb_db = _load_db()

if "rb_historial" not in st.session_state:
    st.session_state.rb_historial = _load_historial()


# ---------------------------------------------------------------------
# Utilidades base local
# ---------------------------------------------------------------------
def guardar_db(embedding: np.ndarray, nombre: str = "Desconocido") -> None:
    item = {
        "embedding": embedding.tolist(),
        "nombre": nombre,
        "fecha": datetime.now().isoformat(),
    }
    st.session_state.rb_db.append(item)
    _save_db(st.session_state.rb_db)


def buscar_en_db(embedding: np.ndarray, threshold: float = 0.35) -> List[Dict[str, Any]]:
    resultados = []
    for entry in st.session_state.rb_db:
        try:
            emb_ref = np.array(entry["embedding"], dtype=np.float32)
            sim = float(
                np.dot(embedding, emb_ref)
                / (np.linalg.norm(embedding) * np.linalg.norm(emb_ref))
            )
            if sim > (1 - threshold):
                resultados.append(
                    {
                        "nombre": entry.get("nombre", "Sin nombre"),
                        "similitud": round(sim * 100, 2),
                        "fecha": entry.get("fecha", ""),
                    }
                )
        except Exception:
            continue

    resultados.sort(key=lambda x: x["similitud"], reverse=True)
    return resultados


def guardar_historial(resultado: Dict[str, Any]) -> None:
    st.session_state.rb_historial.insert(0, resultado)
    if len(st.session_state.rb_historial) > 100:
        st.session_state.rb_historial.pop()
    _save_historial(st.session_state.rb_historial)


# ---------------------------------------------------------------------
# Helpers de imagen / DeepFace
# ---------------------------------------------------------------------
def _save_uploaded_to_temp(uploaded_file, suffix: str = ".jpg") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def _pil_to_temp_jpg(img: Image.Image) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        img.save(tmp.name, format="JPEG")
        return tmp.name


def _extract_primary_face(original_path: str):
    if not _DEEPFACE_OK:
        raise RuntimeError("DeepFace no está disponible en este entorno.")

    faces = DeepFace.extract_faces(
        img_path=original_path,
        detector_backend="retinaface",
        enforce_detection=False,
    )

    if not faces:
        return None, None, []

    face = faces[0]
    face_array = (face["face"] * 255).astype(np.uint8)

    # DeepFace suele devolver RGB en extract_faces, así que evitamos conversión extra
    cropped_pil = Image.fromarray(face_array)

    cropped_path = _pil_to_temp_jpg(cropped_pil)
    return cropped_pil, cropped_path, faces


def _analyze_face(cropped_path: str) -> Dict[str, Any]:
    analysis = DeepFace.analyze(
        img_path=cropped_path,
        actions=["age", "gender", "emotion"],
        enforce_detection=False,
    )
    if isinstance(analysis, list):
        return analysis[0]
    return analysis


def _face_embedding(cropped_path: str) -> np.ndarray:
    rep = DeepFace.represent(
        img_path=cropped_path,
        model_name="Facenet512",
        enforce_detection=False,
    )
    if isinstance(rep, list):
        return np.array(rep[0]["embedding"], dtype=np.float32)
    return np.array(rep["embedding"], dtype=np.float32)


# ---------------------------------------------------------------------
# Motores externos visuales
# ---------------------------------------------------------------------
def _collect_social_profiles(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    social_profiles = []
    for res in results:
        url = (res.get("url") or "").strip()
        title = (res.get("title") or "Sin título").strip()
        if not url:
            continue
        if any(domain in url.lower() for domain in SOCIAL_DOMAINS):
            social_profiles.append(
                {
                    "red": "Social",
                    "url": url,
                    "title": title,
                }
            )
    return social_profiles


def _search_google_lens(cropped_path: str) -> List[Dict[str, Any]]:
    if not _GOOGLE_LENS_OK:
        raise RuntimeError("google-lens-python no está instalado o no cargó correctamente.")

    lens = GoogleLens()
    results = lens.search_by_file(cropped_path)
    parsed = []
    for res in results.get("results", [])[:12]:
        parsed.append(
            {
                "title": res.get("title", "Sin título"),
                "url": res.get("url", ""),
                "source": "Google Lens",
            }
        )
    return parsed


def _search_yandex_url(cropped_path: str) -> Dict[str, Any]:
    with open(cropped_path, "rb") as f:
        files = {"upfile": ("blob", f, "image/jpeg")}
        params = {
            "rpt": "imageview",
            "format": "json",
            "request": '{"blocks":[{"block":"b-page_type_search-by-image__link"}]}',
        }
        r = requests.post("https://yandex.com/images/search", params=params, files=files, timeout=60)
        r.raise_for_status()
        data = json.loads(r.content)
        query = data["blocks"][0]["params"]["url"]
        return {
            "title": "Abrir Yandex completo",
            "url": f"https://yandex.com/images/search?{query}",
            "source": "Yandex",
        }


def _search_lenso_api(cropped_path: str, api_key: str) -> List[Dict[str, Any]]:
    if not api_key:
        raise RuntimeError("No hay API key de Lenso.ai configurada.")

    with open(cropped_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"image": b64}

    r = requests.post("https://api.eyematch.ai/search", json=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Error API Lenso.ai: {r.status_code}")

    data = r.json()
    parsed = []
    for res in data.get("results", [])[:10]:
        parsed.append(
            {
                "title": res.get("title", "Match"),
                "url": res.get("url", "#"),
                "source": "Lenso.ai",
            }
        )
    return parsed


def _render_external_result_list(results: List[Dict[str, Any]]) -> None:
    if not results:
        st.info("Sin resultados.")
        return
    for res in results:
        st.markdown(f"• [{res.get('title', 'Sin título')}]({res.get('url', '#')})")
        src = res.get("source")
        if src:
            st.caption(f"Fuente: {src}")


# ---------------------------------------------------------------------
# Reporte PDF
# ---------------------------------------------------------------------
def _build_pdf_from_history(history: List[Dict[str, Any]]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=14)
    pdf.cell(190, 10, "Reporte RostroBuscador MAX - Modulo Privado", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Arial", size=10)
    pdf.cell(
        190,
        8,
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    for entry in history[:20]:
        line = (
            f"{entry.get('fecha', '')} | {entry.get('archivo', '')} | "
            f"Edad: {entry.get('edad', '')} | Sociales: {entry.get('sociales', 0)}"
        )
        pdf.multi_cell(190, 8, line)

    raw = pdf.output(dest="S")
    if isinstance(raw, bytearray):
        return bytes(raw)
    if isinstance(raw, str):
        return raw.encode("latin-1", errors="ignore")
    return bytes(raw)


# ---------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------
def render_private_module() -> None:
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.caption("Página privada para procesamiento facial local, base local, historial y motores externos visuales.")

    with st.sidebar:
        st.header("Estado del módulo")
        st.metric("DeepFace", "OK" if _DEEPFACE_OK else "No disponible")
        st.metric("Google Lens wrapper", "OK" if _GOOGLE_LENS_OK else "No disponible")
        st.metric("Core history", "OK" if _CORE_HISTORY_OK else "No disponible")
        st.metric("Registros base local", len(st.session_state.rb_db))
        st.metric("Eventos historial", len(st.session_state.rb_historial))

        if st.button("🗑️ Limpiar historial privado", use_container_width=True):
            _save_private_log([])
            st.success("Historial privado limpiado.")
            st.rerun()

    st.subheader("⚙️ Parámetros")

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        case_ref = st.text_input(
            "Referencia del caso",
            value=st.session_state.get("pm_case_ref", "CASO-LOCAL-001"),
        )
        st.session_state["pm_case_ref"] = case_ref

    with col_cfg2:
        threshold = st.slider(
            "Umbral de similitud",
            min_value=0.10,
            max_value=0.99,
            value=st.session_state.get("pm_threshold", 0.35),
            step=0.01,
        )
        st.session_state["pm_threshold"] = threshold

    lenso_api_key_widget = st.text_input(
        "API Key de Lenso.ai (opcional)",
        value="",
        type="password",
        help="Si lo dejas vacío, intentará usar st.secrets['LENSO_API_KEY'] o la variable de entorno.",
    )
    lenso_api_key = _get_lenso_api_key(lenso_api_key_widget)

    st.subheader("📁 Carga de imágenes")
    uploaded_files = st.file_uploader(
        "Sube una o varias imágenes",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )

    if not uploaded_files:
        st.info("Sube al menos una imagen para comenzar.")
        return

    st.caption(f"{len(uploaded_files)} archivo(s) cargado(s).")

    for uploaded_file in uploaded_files:
        original_path = None
        cropped_path = None

        try:
            original_path = _save_uploaded_to_temp(uploaded_file, suffix=".jpg")

            st.divider()
            st.subheader(f"📸 Procesando: {uploaded_file.name}")

            if not _DEEPFACE_OK:
                st.error("DeepFace no está disponible. Revisa requirements.txt.")
                continue

            cropped_pil, cropped_path, faces = _extract_primary_face(original_path)
            if not cropped_pil or not cropped_path:
                st.error("No se detectó rostro.")
                continue

            embedding = _face_embedding(cropped_path)
            analysis = _analyze_face(cropped_path)

            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(uploaded_file, caption="Original", use_container_width=True)
            with col2:
                st.image(cropped_pil, caption="Rostro recortado", use_container_width=True)

            a, b, c = st.columns(3)
            with a:
                st.metric("Edad", f"{int(analysis.get('age', 0))} años")
            with b:
                st.metric("Género", str(analysis.get("dominant_gender", "N/D")))
            with c:
                st.metric("Emoción", str(analysis.get("dominant_emotion", "N/D")).capitalize())

            st.caption(f"Rostros detectados: {len(faces)}")

            # -----------------------------------------------------------------
            # Motores externos
            # -----------------------------------------------------------------
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                ["Google Lens", "Yandex", "TinEye", "Baidu", "Bing", "🔥 Lenso.ai"]
            )

            social_profiles: List[Dict[str, Any]] = []

            with tab1:
                if st.button("Buscar Google Lens", key=f"gl_{uploaded_file.name}"):
                    with st.spinner("Buscando en Google Lens..."):
                        try:
                            results = _search_google_lens(cropped_path)
                            _render_external_result_list(results)
                            social_profiles.extend(_collect_social_profiles(results))
                        except Exception as e:
                            st.error(f"Error Google Lens: {e}")

            with tab2:
                if st.button("Buscar Yandex", key=f"ya_{uploaded_file.name}"):
                    with st.spinner("Generando búsqueda Yandex..."):
                        try:
                            result = _search_yandex_url(cropped_path)
                            _render_external_result_list([result])
                        except Exception as e:
                            st.error(f"Error Yandex: {e}")

            with tab3:
                st.markdown("[Abrir TinEye y subir manualmente](https://tineye.com/)")

            with tab4:
                st.markdown("[Abrir Baidu Images](https://image.baidu.com/)")

            with tab5:
                st.markdown("[Abrir Bing Visual Search](https://www.bing.com/images/search?view=detailv2&iss=sbi)")

            with tab6:
                st.subheader("Lenso.ai")
                if lenso_api_key:
                    if st.button("Buscar con Lenso.ai API", key=f"le_{uploaded_file.name}"):
                        with st.spinner("Consultando Lenso.ai..."):
                            try:
                                results = _search_lenso_api(cropped_path, lenso_api_key)
                                _render_external_result_list(results)
                                social_profiles.extend(_collect_social_profiles(results))
                            except Exception as e:
                                st.error(f"Error Lenso.ai: {e}")
                else:
                    st.info("No hay API key configurada. Puedes usar modo web manual.")
                    st.markdown("[Abrir Lenso.ai y subir](https://lenso.ai)")

            if social_profiles:
                st.subheader("👥 Posibles perfiles sociales encontrados")
                for p in social_profiles[:10]:
                    st.success(f"🔗 [{p['title']}]({p['url']})")

            # -----------------------------------------------------------------
            # Base local
            # -----------------------------------------------------------------
            st.subheader("🗂️ Mi base local")
            nombre = st.text_input(
                "Etiqueta esta persona",
                value="Persona X",
                key=f"name_{uploaded_file.name}",
            )

            col_save1, col_save2 = st.columns([1, 1])
            with col_save1:
                if st.button("Guardar en mi base", key=f"save_{uploaded_file.name}", use_container_width=True):
                    guardar_db(embedding, nombre)
                    st.success("Guardado en base local ✅")

            with col_save2:
                with open(cropped_path, "rb") as f:
                    st.download_button(
                        "⬇️ Descargar rostro recortado",
                        data=f.read(),
                        file_name=f"rostro_{uploaded_file.name}.jpg",
                        mime="image/jpeg",
                        key=f"dl_{uploaded_file.name}",
                        use_container_width=True,
                    )

            coincidencias = buscar_en_db(embedding, threshold=threshold)
            if coincidencias:
                st.write("Coincidencias en tu base:")
                for c in coincidencias[:10]:
                    st.success(f"{c['nombre']} → {c['similitud']}%")
            else:
                st.info("Sin coincidencias en la base local.")

            # -----------------------------------------------------------------
            # Historial
            # -----------------------------------------------------------------
            resultado = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "archivo": uploaded_file.name,
                "edad": int(analysis.get("age", 0)),
                "genero": analysis.get("dominant_gender", "N/D"),
                "sociales": len(social_profiles),
                "case_ref": case_ref,
            }
            guardar_historial(resultado)

            _append_private_log(
                event_type="private_module_run",
                payload={
                    "case_ref": case_ref,
                    "archivo": uploaded_file.name,
                    "sociales": len(social_profiles),
                    "summary": f"archivo={uploaded_file.name} | sociales={len(social_profiles)}",
                },
            )

            _add_to_core_history(
                "modulo_privado",
                {
                    "case_ref": case_ref,
                    "summary": f"archivo={uploaded_file.name} | sociales={len(social_profiles)}",
                },
            )

        except Exception as exc:
            st.error(f"Error procesando {uploaded_file.name}: {exc}")
            _append_private_log(
                event_type="private_module_error",
                payload={
                    "case_ref": case_ref,
                    "archivo": uploaded_file.name,
                    "error": str(exc),
                    "summary": f"ERROR {uploaded_file.name}: {exc}",
                },
            )
        finally:
            for p in [original_path, cropped_path]:
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except Exception:
                        pass

    # -----------------------------------------------------------------
    # Reportes e historial
    # -----------------------------------------------------------------
    st.divider()
    st.subheader("📋 Historial y exportación")

    col_rep1, col_rep2, col_rep3 = st.columns(3)

    with col_rep1:
        history_json = json.dumps(st.session_state.rb_historial, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            "⬇️ Exportar historial JSON",
            data=history_json,
            file_name=f"historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_rep2:
        pdf_bytes = _build_pdf_from_history(st.session_state.rb_historial)
        st.download_button(
            "⬇️ Exportar reporte PDF",
            data=pdf_bytes,
            file_name=f"reporte_privado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col_rep3:
        if st.button("Ver historial privado", use_container_width=True):
            st.session_state["pm_show_history"] = not st.session_state.get("pm_show_history", False)

    if st.session_state.get("pm_show_history", False):
        private_history = _load_private_log()
        if not private_history:
            st.info("Sin historial privado todavía.")
        else:
            for entry in private_history[:20]:
                with st.expander(f"🕐 {entry.get('ts', '')} | {entry.get('event', '')}"):
                    st.json(entry.get("payload", {}))

    st.sidebar.info("💡 Usa fotos frontales y claras. Lenso.ai requiere API key para modo automático.")
    st.caption("Módulo privado • Pages-ready • Estado persistente • Historial + Base local")


render_private_module()
