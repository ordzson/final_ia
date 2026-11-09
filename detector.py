"""Detección de objetos (YOLO en OpenVINO) y de rostros (MediaPipe) sobre frames BGR."""
import time
import sys
import threading
from dataclasses import dataclass

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


class Detector:
    def __init__(self) -> None:
        """Carga YOLO desde config.MODEL_PATH y el detector de rostros desde config.FACE_MODEL_PATH."""
        # Un hilo para pre/postproceso evita competir con OpenVINO en esta CPU Windows.
        self._predict_options = {"device": "intel:CPU"} if sys.platform == "win32" else {}
        if sys.platform == "win32":
            torch.set_num_threads(1)
        self.model = YOLO(str(config.MODEL_PATH), task="detect")
        # Calienta antes de consultar names: evita que Ultralytics compile un predictor temporal.
        dummy = np.zeros((config.FRAME_H, config.FRAME_W, 3), np.uint8)
        self.model.predict(dummy, imgsz=config.IMGSZ, verbose=False, **self._predict_options)
        self._torch_threads = torch.get_num_threads()
        self._torch_thread_id = threading.get_ident()
        self._key_ids = {name: i for i, name in self.model.names.items() if name in config.LABELS_ES}
        self._id_keys = {i: name for name, i in self._key_ids.items()}

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
        return set(self._key_ids)

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
        if "rostros" in groups:
            dets += self._detect_faces(frame_bgr, conf)
        return dets

    def _detect_yolo(self, frame_bgr, conf: float, keys: list[str]) -> list[Det]:
        h, w = frame_bgr.shape[:2]
        ids = [self._key_ids[k] for k in keys]
        r = self.model.predict(frame_bgr, imgsz=config.IMGSZ, conf=conf, classes=ids, verbose=False,
                               **self._predict_options)[0]
        xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        cls = r.boxes.cls.cpu().numpy().astype(int)
        dets = []
        for (x1, y1, x2, y2), c, i in zip(xyxy, confs, cls):
            box = _clip_box(x1, y1, x2, y2, w, h)
            if box is None:
                continue
            key = self._id_keys[int(i)]
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
