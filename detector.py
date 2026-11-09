"""Detección YOLO en OpenVINO CPU o CUDA y rostros MediaPipe sobre frames BGR."""
import time
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import torch
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision
from ultralytics import YOLO

import config


@dataclass
class Det:
    key: str                         # nombre exacto de la clase en model.names (p. ej. "laptop") o config.FACE_KEY
    label: str                       # etiqueta en español (config.LABELS_ES[key] o config.FACE_LABEL)
    conf: float                      # 0..1
    box: tuple[int, int, int, int]   # x1, y1, x2, y2 en píxeles del frame, recortados a sus bordes
    group: str                       # "objetos" | "personas" | "rostros"


def _group_of(key: str) -> str:
    return "personas" if key in config.PERSON_KEYS else "objetos"


def _clip_box(x1: float, y1: float, x2: float, y2: float,
              w: int, h: int) -> tuple[int, int, int, int] | None:
    """Recorta la caja a los bordes del frame. Devuelve None si queda sin área."""
    x1, x2 = (max(0, min(int(v), w - 1)) for v in (x1, x2))
    y1, y2 = (max(0, min(int(v), h - 1)) for v in (y1, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def _overlaps_notebook(book: Det, notebook: Det) -> bool:
    x1, y1, x2, y2 = book.box
    nx1, ny1, nx2, ny2 = notebook.box
    intersection = max(0, min(x2, nx2) - max(x1, nx1)) * max(0, min(y2, ny2) - max(y1, ny1))
    union = (x2 - x1) * (y2 - y1) + (nx2 - nx1) * (ny2 - ny1) - intersection
    return intersection >= 0.7 * union


def inference_backend(device: str) -> str:
    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError(f"Dispositivo no válido: {device}")
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA no está disponible. Ejecuta setup_cuda.py y comprueba el controlador NVIDIA.")
    return device


class Detector:
    def __init__(self, stationery_path: Path | None = None, device: str = "auto",
                 half: bool = False) -> None:
        """Carga YOLO, BlazeFace y, si se indica, el detector de lápices y cuadernos."""
        # Un hilo para pre/postproceso evita competir con OpenVINO en esta CPU Windows.
        self.device = inference_backend(device)
        self._predict_options = {"device": "intel:CPU"} if sys.platform == "win32" else {}
        model_path = config.MODEL_PATH
        if self.device == "cuda":
            model_path = config.ROOT / "models" / ("yolo26s.pt" if config.IMGSZ == 640 else "yolov8n.pt")
            if stationery_path is not None and stationery_path == config.STATIONERY_MODEL_PATH:
                stationery_path = config.ROOT / "models" / "stationery.pt"
            if stationery_path is not None and stationery_path.suffix != ".pt":
                raise ValueError("CUDA necesita pesos .pt para --stationery-model.")
            for path in (model_path, stationery_path):
                if path is not None and not path.is_file():
                    raise FileNotFoundError(f"Faltan pesos CUDA: {path}")
            self._predict_options = {"device": 0, "half": half}
        if sys.platform == "win32" and self.device == "cpu":
            torch.set_num_threads(1)
        print(f"Inferencia YOLO: {self.device.upper()} | {model_path.name} | "
              f"{'FP16' if half and self.device == 'cuda' else 'FP32'}", flush=True)
        self.model = YOLO(str(model_path), task="detect")
        # Calienta antes de consultar names: evita que Ultralytics compile un predictor temporal.
        dummy = np.zeros((config.FRAME_H, config.FRAME_W, 3), np.uint8)
        self.model.predict(dummy, imgsz=config.IMGSZ, verbose=False, **self._predict_options)
        self._torch_threads = torch.get_num_threads()
        self._torch_thread_id = threading.get_ident()
        self._key_ids = {name: i for i, name in self.model.names.items() if name in config.LABELS_ES}
        self.stationery = None
        self._stationery_ids = {}
        if stationery_path is not None:
            self.stationery = YOLO(str(stationery_path), task="detect")
            self.stationery.predict(dummy, imgsz=config.STATIONERY_IMGSZ, verbose=False,
                                    **self._predict_options)
            self._stationery_ids = {name: i for i, name in self.stationery.names.items()}
            stationery_classes = self._stationery_ids.keys()
            if not config.STATIONERY_KEYS <= stationery_classes <= config.STATIONERY_KEYS | {"pen"}:
                raise ValueError("El modelo de útiles debe tener pencil y notebook. También puede tener pen.")

        options = vision.FaceDetectorOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(config.FACE_MODEL_PATH)),
            running_mode=vision.RunningMode.VIDEO,
            min_detection_confidence=config.FACE_MIN_CONF,
        )
        self.face = vision.FaceDetector.create_from_options(options)
        self._last_ts = -1

    @property
    def available_keys(self) -> set[str]:
        """Claves de config.LABELS_ES que existen en model.names. No incluye FACE_KEY."""
        return self._key_ids.keys() | self._stationery_ids.keys()

    def detect(self, frame_bgr, conf: float, groups: set[str],
               only_keys: set[str] | None = None) -> list[Det]:
        """
        groups: subconjunto de {"objetos", "personas", "rostros"}.
        only_keys: si no es None, restringe las clases YOLO a esas claves (lo usa el modo universitario).
        Devuelve una lista sin orden garantizado. Nunca lanza excepción por un frame vacío.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            return []
        # OpenMP puede iniciar otro contexto al trasladar la inferencia a QThread.
        thread_id = threading.get_ident()
        if thread_id != self._torch_thread_id:
            torch.set_num_threads(self._torch_threads)
            self._torch_thread_id = thread_id
        keys = [k for k in self._key_ids
                if _group_of(k) in groups and (only_keys is None or k in only_keys)]
        dets = []
        # Con la lista vacía no se llama a YOLO: classes=[] o None lo haría detectar todo
        if keys:
            dets += self._detect_yolo(frame_bgr, conf, keys)
        if self.stationery is not None and "objetos" in groups:
            stationery_keys = self._stationery_ids.keys()
            if only_keys is not None:
                stationery_keys = stationery_keys & only_keys
            if stationery_keys:
                ids = {self._stationery_ids[k]: k for k in stationery_keys}
                stationery = self._predict_objects(self.stationery, frame_bgr, conf, config.STATIONERY_IMGSZ, ids)
                notebooks = [det for det in stationery if det.key == "notebook"]
                dets = [det for det in dets if det.key != "book"
                        or not any(_overlaps_notebook(det, notebook) for notebook in notebooks)]
                dets += stationery
        if "rostros" in groups:
            dets += self._detect_faces(frame_bgr, conf)
        return dets

    def _detect_yolo(self, frame_bgr, conf: float, keys: list[str]) -> list[Det]:
        ids = {self._key_ids[k]: k for k in keys}
        return self._predict_objects(self.model, frame_bgr, conf, config.IMGSZ, ids)

    def _predict_objects(self, model, frame_bgr, conf: float, imgsz: int, ids: dict[int, str]) -> list[Det]:
        h, w = frame_bgr.shape[:2]
        r = model.predict(frame_bgr, imgsz=imgsz, conf=conf, classes=list(ids), verbose=False,
                          **self._predict_options)[0]
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        cls = r.boxes.cls.cpu().numpy().astype(int)
        dets = []
        for (x1, y1, x2, y2), c, i in zip(xyxy, confs, cls):
            box = _clip_box(x1, y1, x2, y2, w, h)
            if box is None:
                continue
            key = ids[int(i)]
            dets.append(Det(key, config.LABELS_ES[key], float(c), box, _group_of(key)))
        return dets

    def _detect_faces(self, frame_bgr, conf: float) -> list[Det]:
        h, w = frame_bgr.shape[:2]
        # MediaPipe en modo VIDEO exige timestamps estrictamente crecientes
        ts = int(time.monotonic() * 1000)
        if ts <= self._last_ts:
            ts = self._last_ts + 1
        self._last_ts = ts

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.face.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
        dets = []
        for d in res.detections:
            score = d.categories[0].score
            # El umbral de la interfaz también aplica a rostros (además de FACE_MIN_CONF)
            if score < conf:
                continue
            b = d.bounding_box
            box = _clip_box(b.origin_x, b.origin_y, b.origin_x + b.width, b.origin_y + b.height, w, h)
            if box is not None:
                dets.append(Det(config.FACE_KEY, config.FACE_LABEL, float(score), box, "rostros"))
        return dets
