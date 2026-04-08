from __future__ import annotations
from dataclasses import dataclass
from io import BytesIO
import tempfile
from typing import Any
import numpy as np
from PIL import Image

DEEPFACE_OK = True
DEEPFACE_ERROR = ""
try:
    from deepface import DeepFace
except Exception as exc:  # pragma: no cover
    DEEPFACE_OK = False
    DEEPFACE_ERROR = str(exc)
    DeepFace = None


@dataclass
class FaceResult:
    image: Image.Image
    confidence: float
    facial_area: dict[str, Any]


def pil_to_tempfile(img: Image.Image) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.convert("RGB").save(tmp.name)
    return tmp.name


def uploaded_to_pil(uploaded_file) -> Image.Image:
    return Image.open(BytesIO(uploaded_file.getvalue())).convert("RGB")


def extract_faces_from_pil(img: Image.Image, detector: str = "retinaface") -> list[FaceResult]:
    if not DEEPFACE_OK:
        raise RuntimeError(f"DeepFace no disponible: {DEEPFACE_ERROR}")
    path = pil_to_tempfile(img)
    faces = DeepFace.extract_faces(img_path=path, detector_backend=detector, enforce_detection=False)
    results: list[FaceResult] = []
    for face in faces or []:
        arr = np.clip(np.array(face["face"]) * 255, 0, 255).astype(np.uint8)
        pil = Image.fromarray(arr)
        results.append(FaceResult(
            image=pil,
            confidence=float(face.get("confidence", 0.0)),
            facial_area=face.get("facial_area", {}),
        ))
    return results


def analyze_face(face_img: Image.Image) -> dict[str, Any]:
    if not DEEPFACE_OK:
        raise RuntimeError(f"DeepFace no disponible: {DEEPFACE_ERROR}")
    path = pil_to_tempfile(face_img)
    data = DeepFace.analyze(img_path=path, actions=["age", "gender", "emotion"], enforce_detection=False)
    if isinstance(data, list):
        data = data[0]
    return data


def represent_face(face_img: Image.Image, model_name: str = "Facenet512") -> np.ndarray:
    if not DEEPFACE_OK:
        raise RuntimeError(f"DeepFace no disponible: {DEEPFACE_ERROR}")
    path = pil_to_tempfile(face_img)
    data = DeepFace.represent(img_path=path, model_name=model_name, detector_backend="skip", enforce_detection=False)
    if isinstance(data, list):
        data = data[0]
    return np.array(data["embedding"], dtype=float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
