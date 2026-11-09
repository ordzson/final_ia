"""Compara los perfiles configurados con las mismas muestras reales, sin modificar sus pesos.

--capture abre la app: B etiqueta cuaderno, C celular, L laptop y Espacio guarda
un frame sin cajas. Tras tres cuadernos y dos celulares se comparan todos los perfiles.
--capture-only permite guardar muestras sin limite: cierra la ventana para terminar
sin ejecutar la comparacion. Las laptops no tienen una meta de capturas.
La evidencia permanece dentro de .venv, fuera de Git.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".venv/ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv/matplotlib"))
SAMPLE_LABELS = {"book": "Cuaderno cerrado de tapa dura", "cell phone": "Celular real", "laptop": "Laptop real"}
SAMPLE_SHORTCUTS = {"book": "B", "cell phone": "C", "laptop": "L"}


def build_sample_window(detector, camera, directory, samples, threshold, auto_close=True):
    import cv2
    from PySide6.QtCore import QTimer, Qt, Slot
    from PySide6.QtGui import QKeySequence, QShortcut
    from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QToolBar
    import app

    manifest = directory / "samples.json"

    class SampleWindow(app.MainWindow):
        def __init__(self):
            self.raw_frame = None
            self.expected = "book"
            self.capture_attempts = 0
            super().__init__(detector, [], camera, "uni")
            # Un slot con nombre propio evita resolver el slot Qt heredado al conectar.
            self.inference_worker.finished.disconnect(self.on_inference_finished)
            self.inference_worker.finished.connect(self.on_sample_inference_finished,
                                                  Qt.ConnectionType.QueuedConnection)
            bar = QToolBar("Muestras", self)
            bar.setMovable(False)
            bar.addWidget(QLabel("  Objeto que estás mostrando:  "))
            self.sample_selector = QComboBox()
            for key, label in SAMPLE_LABELS.items():
                self.sample_selector.addItem(label, key)
            bar.addWidget(self.sample_selector)
            self.sample_progress = QLabel()
            bar.addWidget(self.sample_progress)
            self.addToolBar(bar)
            self.sample_selector.currentIndexChanged.connect(
                lambda _index: self.choose(self.sample_selector.currentData()))
            for index, key in enumerate(SAMPLE_LABELS):
                QShortcut(QKeySequence(SAMPLE_SHORTCUTS[key]), self,
                          lambda selected=index: self.sample_selector.setCurrentIndex(selected))
            self.sample_button = next(b for b in self.findChildren(QPushButton) if b.text() == "Capturar")
            self.sample_button.setToolTip("Guarda un frame sin recuadros; puedes pulsar varias veces")
            self.conf_slider.setValue(round(threshold * 100))
            self.choose("book")

        @Slot(object, object, object)
        def on_sample_inference_finished(self, job, detections, error):
            previous_tick = self.last_tick
            super().on_inference_finished(job, detections, error)
            if self.last_tick is not None and self.last_tick != previous_tick:
                # Retiene el último frame aceptado sin depender de un callback temporal.
                self.raw_frame = job["frame"]

        def choose(self, expected):
            self.expected = expected
            label = SAMPLE_LABELS[expected]
            counts = {key: sum(s["expected"] == key for s in samples) for key in SAMPLE_LABELS}
            title = "Comparación" if auto_close else "Captura de muestras"
            self.setWindowTitle(f"{title} — {label} — Espacio o Guardar muestra")
            book_count = f"{counts['book']}/3" if auto_close else str(counts["book"])
            phone_count = f"{counts['cell phone']}/2" if auto_close else str(counts["cell phone"])
            self.sample_progress.setText(f"    Cuadernos: {book_count} · Celulares: {phone_count}"
                                         f" · Laptops: {counts['laptop']}    ")
            self.sample_button.setText(f"Guardar muestra ({len(samples)})")
            ending = "" if auto_close else " Cierra la ventana para terminar sin comparar."
            self.statusBar().showMessage(f"Muestra {label}; B cuaderno, C celular, L laptop."
                                         f" Cada pulsación guarda una foto independiente.{ending}")

        def record_attempt(self, **fields):
            with (directory / "capture_events.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps({"attempt": self.capture_attempts, "expected": self.expected,
                                      "total": len(samples), **fields}, ensure_ascii=False) + "\n")

        def capture(self):
            self.capture_attempts += 1
            if self.raw_frame is None:
                self.statusBar().showMessage("Esperando un frame nuevo de la cámara; vuelve a pulsar Guardar muestra.")
                self.record_attempt(status="waiting_for_frame")
                return
            filename = f"{self.expected.replace(' ', '_')}_{time.time_ns()}.png"
            frame = self.raw_frame.copy()
            if not cv2.imwrite(str(directory / filename), frame):
                self.statusBar().showMessage("No se pudo guardar la muestra.")
                self.record_attempt(status="write_failed")
                return
            samples.append({"file": filename, "expected": self.expected,
                            "description": SAMPLE_LABELS[self.expected].lower(),
                            "preview_conf": self.conf})
            temporary = manifest.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(samples, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(manifest)
            self.captures += 1
            self.choose(self.expected)
            self.record_attempt(status="saved", file=filename)
            if (auto_close and sum(s["expected"] == "book" for s in samples) >= 3
                    and sum(s["expected"] == "cell phone" for s in samples) >= 2):
                QTimer.singleShot(300, self.close)

    return SampleWindow()


def main():
    import config

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="captura 3 cuadernos y 2 celulares y luego compara los perfiles; B/C/L eligen objeto")
    parser.add_argument("--capture-only", action="store_true",
                        help="captura sin limite con B cuaderno, C celular y L laptop; cerrar termina sin comparar")
    parser.add_argument("--quality", choices=list(config.MODEL_PROFILES), default=config.DEFAULT_QUALITY,
                        help="perfil del modelo para la vista previa durante la captura")
    parser.add_argument("--native", action="store_true",
                        help="incluye yolov8n.pt a 480 FP32 para verificar la exportacion")
    parser.add_argument("--camera", type=int, default=config.CAMERA_INDEX_DEFAULT)
    parser.add_argument("--conf", type=float, default=config.CONF_DEFAULT)
    parser.add_argument("--input", type=Path, default=ROOT / ".venv/verification/model_samples")
    args = parser.parse_args()
    directory = args.input.resolve()
    if not directory.is_relative_to((ROOT / ".venv").resolve()):
        parser.error("Las muestras deben quedar dentro de .venv.")
    if not 0.1 <= args.conf <= 0.9:
        parser.error("--conf debe estar entre 0.1 y 0.9, igual que el control de la app.")
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / "samples.json"
    samples = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []

    import cv2
    from detector import Detector

    if args.capture or args.capture_only:
        from PySide6.QtWidgets import QApplication
        import app

        config.MODEL_PATH, config.IMGSZ = config.MODEL_PROFILES[args.quality]
        config.FRAME_W, config.FRAME_H = 640, 480
        application = QApplication([])
        app.apply_theme(application)
        detector = Detector()

        window = build_sample_window(detector, args.camera, directory, samples, args.conf,
                                     auto_close=not args.capture_only)
        window.show()
        application.exec()
        detector.face.close()
        del window, detector
        if args.capture_only:
            print(f"SAMPLE_CAPTURE_COMPLETE count={len(samples)} path={manifest}", flush=True)
            return

    if not samples:
        raise SystemExit("No hay muestras. Usa --capture para obtener imágenes etiquetadas.")

    def read_sample(sample):
        path = (directory / sample["file"]).resolve()
        if not path.is_relative_to(directory):
            raise ValueError("La muestra sale de la carpeta de evidencia.")
        frame = cv2.imread(str(path))
        if frame is None:
            raise ValueError(f"No se puede leer {path.name}")
        return frame

    rows = []
    for quality, profile in config.MODEL_PROFILES.items():
        config.MODEL_PATH, config.IMGSZ = profile
        detector = Detector()
        try:
            for sample in samples:
                frame = read_sample(sample)
                detections = detector.detect(frame, 0.1, {"objetos"}, only_keys=set(config.UNI_ITEMS))
                data = [{"key": d.key, "conf": round(d.conf, 5), "box": list(d.box),
                         "visible_at_threshold": d.conf >= args.conf} for d in detections]
                row = {"file": sample["file"], "expected": sample["expected"], "quality": quality,
                       "inference_size": config.IMGSZ, "detections": data}
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
        finally:
            detector.face.close()
    if args.native:
        import torch
        from ultralytics import YOLO
        from detector import _clip_box

        torch.set_num_threads(4)
        native = YOLO(str(ROOT / "models/yolov8n.pt"), task="detect")
        native.model.float()
        ids = [index for index, name in native.names.items() if name in config.UNI_ITEMS]
        for sample in samples:
            frame = read_sample(sample)
            height, width = frame.shape[:2]
            result = native.predict(frame, imgsz=480, rect=False, conf=0.1,
                                    classes=ids, device="cpu", verbose=False)[0]
            detections = []
            for box in result.boxes:
                bounds = _clip_box(*box.xyxy[0].tolist(), width, height)
                if bounds is not None:
                    confidence = float(box.conf.item())
                    detections.append({"key": native.names[int(box.cls.item())],
                                       "conf": round(confidence, 5), "box": list(bounds),
                                       "visible_at_threshold": confidence >= args.conf})
            row = {"file": sample["file"], "expected": sample["expected"],
                   "quality": "native_pt_480", "inference_size": 480, "detections": detections}
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    report = {"ui_threshold": args.conf, "diagnostic_threshold": 0.1, "samples": samples,
              "native_included": args.native, "results": rows,
              "notes": "Mismos frames BGR sin overlays. .pt a 480 usa rect=False para igualar la entrada cuadrada exportada. Revisar las cajas: una etiqueta presente en otra región no acredita el objeto de interés. No es una medición de mAP."}
    output = directory / "comparison.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MODEL_COMPARISON_COMPLETE path={output}", flush=True)


if __name__ == "__main__":
    main()
