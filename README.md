# Sentinel Face Lab — Estructura final con page privada

Proyecto Streamlit con `app.py` como inicio y páginas clásicas en `pages/`.

## Qué ya trae
- Detección facial local
- Verificación 1:1
- Búsqueda 1:N sobre base local
- Búsqueda visual externa
- Procesamiento por lote
- Auditoría e historial
- Configuración
- **Page 07 reservada para tu módulo privado**

## Estructura
```text
sentinel_face_lab_option_b_structure/
├─ app.py
├─ requirements.txt
├─ Dockerfile
├─ README.md
├─ core/
│  ├─ config.py
│  ├─ faces.py
│  ├─ external_search.py
│  ├─ storage.py
│  └─ private_module_guide.md
├─ pages/
│  ├─ 01_Deteccion.py
│  ├─ 02_Verificacion_1_a_1.py
│  ├─ 03_Busqueda_1_a_N.py
│  ├─ 04_Busqueda_visual_externa.py
│  ├─ 05_Lote.py
│  ├─ 06_Auditoria.py
│  ├─ 07_Modulo_privado.py
│  └─ 08_Configuracion.py
└─ data/
   ├─ rostros_db.json
   └─ historial.json
```

## Dónde pegar tu módulo
Archivo recomendado:
- `pages/07_Modulo_privado.py`

## Arranque local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Subida a Streamlit Cloud
- Sube esta carpeta completa a GitHub.
- En Streamlit elige `app.py` como archivo principal.
