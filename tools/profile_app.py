"""Mide captura y etapas de la app sin confundir repintados con detecciones nuevas."""
import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".venv" / "ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv" / "matplotlib"))

import cv2
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import app
import config
from detector import Detector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("capture", "general", "uni"), default="general")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX_DEFAULT)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--width", type=int, default=config.FRAME_W)
    parser.add_argument("--height", type=int, default=config.FRAME_H)
    parser.add_argument("--capture-fps", type=float)
    parser.add_argument("--opencv-threads", type=int)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--quality", choices=list(config.MODEL_PROFILES), default=config.DEFAULT_QUALITY)
    args = parser.parse_args()
    if args.seconds <= 2:
        parser.error("--seconds debe superar los 2 s de calentamiento")
    config.FRAME_W, config.FRAME_H = args.width, args.height
    config.MODEL_PATH, config.IMGSZ = config.MODEL_PROFILES[args.quality]
    if args.opencv_threads is not None:
        cv2.setNumThreads(args.opencv_threads)
    base_open = app.open_camera
    camera_info = {}

    def open_camera(index):
        cap = base_open(index)
        if cap is not None:
            applied = cap.set(cv2.CAP_PROP_FPS, args.capture_fps) if args.capture_fps else None
            camera_info.update(backend=cap.getBackendName(), width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                               height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                               reported_fps=cap.get(cv2.CAP_PROP_FPS), fps_request_applied=applied)
        return cap

    app.open_camera = open_camera

    def report(data):
        data.update(mode=args.mode, camera=args.camera, requested_size=[args.width, args.height],
                    quality=args.quality, inference_size=config.IMGSZ,
                    capture_fps_request=args.capture_fps, opencv_threads=cv2.getNumThreads(),
                    camera_info=camera_info)
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        print(encoded, flush=True)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(encoded + "\n", encoding="utf-8")

    if args.mode == "capture":
        cap = open_camera(args.camera)
        if cap is None:
            raise SystemExit("La camara no abre")
        samples, failed = [], 0
        start = time.perf_counter()
        elapsed = 0.0
        try:
            while time.perf_counter() - start < args.seconds:
                before = time.perf_counter()
                ok, frame = cap.read()
                after = time.perf_counter()
                if ok and frame is not None and frame.size:
                    if before - start >= 2:
                        samples.append((after - before) * 1000)
                else:
                    failed += 1
            elapsed = time.perf_counter() - start - 2
        finally:
            cap.release()
        report(dict(fps=len(samples) / elapsed, frames=len(samples), failures=failed,
                    read_ms=statistics.mean(samples) if samples else None))
        if not samples:
            raise SystemExit("La camara no entrego frames")
        return

    qt_app = QApplication([])
    app.apply_theme(qt_app)
    samples = {key: [] for key in ("read_ms", "detect_ms", "yolo_ms", "face_ms", "qimage_ms", "display_ms")}
    processed = []
    started = None
    inference_failed = False

    def measured(name, function):
        def wrapper(*positional, **keywords):
            before = time.perf_counter()
            result = function(*positional, **keywords)
            if started is not None and before - started >= 2:
                samples[name].append((time.perf_counter() - before) * 1000)
            return result
        return wrapper

    detector = Detector()
    detector.detect = measured("detect_ms", detector.detect)
    detector._detect_yolo = measured("yolo_ms", detector._detect_yolo)
    detector._detect_faces = measured("face_ms", detector._detect_faces)
    app.to_qimage = measured("qimage_ms", app.to_qimage)

    class TimedCapture:
        def __init__(self, capture):
            self.capture = capture
            self.read = measured("read_ms", capture.read)

        def __getattr__(self, name):
            return getattr(self.capture, name)

    class Window(app.MainWindow):
        def use_camera(self, capture):
            super().use_camera(TimedCapture(capture))

        def show_image(self, image, now):
            measured("display_ms", super().show_image)(image, now)

    window = Window(detector, [], args.camera, args.mode)
    def frame_processed(_groups, _size):
        if started is not None and time.perf_counter() - started >= 2:
            processed.append(time.perf_counter())
    window.frame_processed.connect(frame_processed)
    window.show()
    started = time.perf_counter()

    def finish():
        nonlocal inference_failed
        inference_failed = window._inference_error
        elapsed = time.perf_counter() - started - 2
        means = {name: statistics.mean(values) if values else None for name, values in samples.items()}
        report(dict(fps=len(processed) / elapsed, frames=len(processed),
                    seconds=elapsed, mean_stage_ms=means,
                    inference_error=inference_failed,
                    notes="Etapas en paralelo; FPS cuenta resultados nuevos aceptados y dibujados."))
        if args.out and window.last_image is not None:
            window.grab().save(str(args.out.with_suffix(".png")))
        window.close()
        qt_app.quit()

    QTimer.singleShot(round(args.seconds * 1000), finish)
    qt_app.exec()
    if not processed:
        raise SystemExit("No se procesaron frames")
    if inference_failed:
        raise SystemExit("El detector fallo durante la medicion")


if __name__ == "__main__":
    main()
