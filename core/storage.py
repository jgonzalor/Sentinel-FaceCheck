from __future__ import annotations
import json
from datetime import datetime
from typing import Any
import numpy as np
from fpdf import FPDF
from .config import DB_FILE, HISTORIAL_FILE


def _read_json(path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _write_json(path, value):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def load_db() -> list[dict[str, Any]]:
    return _read_json(DB_FILE, [])


def save_db(db: list[dict[str, Any]]) -> None:
    _write_json(DB_FILE, db)


def load_history() -> list[dict[str, Any]]:
    return _read_json(HISTORIAL_FILE, [])


def save_history(history: list[dict[str, Any]]) -> None:
    _write_json(HISTORIAL_FILE, history)


def add_history(event: str, details: dict[str, Any]) -> None:
    history = load_history()
    history.insert(0, {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        **details,
    })
    history = history[:200]
    save_history(history)


def add_face_to_db(embedding: np.ndarray, name: str, note: str = "") -> None:
    db = load_db()
    db.append({
        "embedding": embedding.tolist(),
        "name": name,
        "note": note,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_db(db)


def search_db(embedding: np.ndarray, threshold: float = 0.72) -> list[dict[str, Any]]:
    db = load_db()
    results = []
    for entry in db:
        ref = np.array(entry["embedding"], dtype=float)
        denom = (np.linalg.norm(embedding) * np.linalg.norm(ref))
        if denom == 0:
            continue
        sim = float(np.dot(embedding, ref) / denom)
        if sim >= threshold:
            results.append({
                "name": entry["name"],
                "note": entry.get("note", ""),
                "score": round(sim, 4),
                "created_at": entry.get("created_at", ""),
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def build_pdf_report(history: list[dict[str, Any]], output_path: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=15)
    pdf.cell(0, 10, "Sentinel Face Lab - Reporte", ln=1)
    pdf.set_font("Helvetica", size=10)
    for row in history[:40]:
        line = f"{row.get('ts','')} | {row.get('event','')} | {row.get('file','')} | {row.get('summary','')}"
        pdf.multi_cell(0, 7, line)
    pdf.output(output_path)
    return output_path
