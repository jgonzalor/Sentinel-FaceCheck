# Guía rápida para pegar tu módulo privado

## Archivo recomendado
Pega tu módulo en:

- `pages/07_Modulo_privado.py`

## Dos formas seguras

### Opción A — Reemplazo completo
Sustituye todo el archivo `pages/07_Modulo_privado.py` por tu módulo.

### Opción B — Pegar dentro de la función
Conserva la estructura actual y pega tu lógica dentro de `render_private_module()`.

## Cosas que no debes tocar
- `app.py`
- `core/storage.py`
- `data/rostros_db.json`
- `data/historial.json`

## Si tu módulo necesita dependencias nuevas
Agrega los paquetes en `requirements.txt`.

## Si tu módulo genera eventos
Usa:

```python
from core.storage import add_history
add_history("modulo_privado", {"file": "archivo.ext", "summary": "detalle"})
```

## Si tu módulo guarda resultados entre clics
Usa `st.session_state`.
