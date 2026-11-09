"""Prueba muestras de cuaderno/celular/laptop con frames sinteticos, sin camara/modelos."""
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from test_app import (FAKE_INDEX, FakeCamera, FakeDetector, QCoreApplication,
                      QEvent, QApplication, config, vision_app, wait_until)
from tools import compare_models
from tools.compare_models import SAMPLE_LABELS, build_sample_window
from PySide6.QtGui import QShortcut
import cv2
import numpy as np


@contextmanager
def sample_window(auto_close=False):
    directory = config.ROOT / ".venv/verification"
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="test_samples_", dir=directory) as temporary:
        output, samples = Path(temporary), []
        camera, detector = FakeCamera(), FakeDetector()
        with patch.object(vision_app, "open_camera", return_value=camera):
            window = build_sample_window(detector, FAKE_INDEX, output, samples, 0.35, auto_close=auto_close)
            for timer in (window.frame_timer, window.panel_timer, window.retry_timer):
                timer.stop()
            try:
                yield window, camera, output, samples
            finally:
                window.close()
                window.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_multiple_samples_include_laptop():
    expected = ["book"] * 3 + ["cell phone"] * 2 + ["laptop"] * 2
    with sample_window() as (window, camera, output, samples):
        with patch.object(vision_app.QTimer, "singleShot") as scheduled:
            window.sample_button.click()
            assert not samples, "No guardar un objeto antes de recibir un frame"
            laptop_shortcut = next(s for s in window.findChildren(QShortcut) if s.key().toString() == "L")
            for index, key in enumerate(expected):
                color = 80 + index * 25
                camera.frame.fill(color)
                window.tick()
                wait_until(lambda: window._inflight is None)
                assert window.raw_frame is not None
                if key == "laptop":
                    laptop_shortcut.activated.emit()
                else:
                    window.sample_selector.setCurrentIndex(window.sample_selector.findData(key))
                assert window.expected == key
                window.sample_button.click()
                assert len(samples) == index + 1
                saved = cv2.imread(str(output / samples[-1]["file"]))
                assert np.all(saved == color), "La muestra debe ser nueva y no contener overlays"
                assert f"({index + 1})" in window.sample_button.text()
                assert samples[-1]["expected"] == key
                assert samples[-1]["description"] == SAMPLE_LABELS[key].lower()
                assert samples[-1]["preview_conf"] == 0.35
                assert samples[-1]["file"].startswith(key.replace(" ", "_") + "_")
                counts = {k: expected[:index + 1].count(k) for k in SAMPLE_LABELS}
                assert window.sample_progress.text().strip() == (
                    f"Cuadernos: {counts['book']} · Celulares: {counts['cell phone']} · Laptops: {counts['laptop']}")
            scheduled.assert_not_called()  # Incluso tras 3 cuadernos + 2 celulares, sigue capturando.
            persisted = json.loads((output / "samples.json").read_text(encoding="utf-8"))
            assert len({s["file"] for s in persisted}) == 7
            assert [s["expected"] for s in persisted] == expected
            assert [s["description"] for s in persisted] == [SAMPLE_LABELS[k].lower() for k in expected]
            assert persisted[-1]["description"] == "laptop real"
            assert len(list(output.glob("*.png"))) == 7
            events = [json.loads(line) for line in (output / "capture_events.jsonl").read_text(encoding="utf-8").splitlines()]
            assert [e["status"] for e in events] == ["waiting_for_frame"] + ["saved"] * 7
            assert [e["expected"] for e in events[1:]] == expected
            assert "Laptop real" in window.windowTitle()


def test_default_targets_ignore_laptop_count():
    expected = ["laptop"] * 2 + ["book"] * 3 + ["cell phone"] * 2
    with sample_window(auto_close=True) as (window, camera, _output, samples):
        window.raw_frame = camera.frame.copy()
        with patch.object(vision_app.QTimer, "singleShot") as scheduled:
            for index, key in enumerate(expected):
                window.sample_selector.setCurrentIndex(window.sample_selector.findData(key))
                window.sample_button.click()
                assert len(samples) == index + 1
                if index < len(expected) - 1:
                    scheduled.assert_not_called()
            scheduled.assert_called_once()
            assert scheduled.call_args.args[0] == 300
        assert window.sample_progress.text().strip() == "Cuadernos: 3/3 · Celulares: 2/2 · Laptops: 2"


def test_capture_only_exits_without_comparing():
    directory = config.ROOT / ".venv/verification"
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="test_capture_only_", dir=directory) as temporary:
        output = Path(temporary)
        application, window = Mock(), Mock()
        detector = SimpleNamespace(face=SimpleNamespace(close=Mock()))
        captured_profiles = []
        with (patch.object(sys, "argv", ["compare_models.py", "--capture-only", "--camera", str(FAKE_INDEX),
                                         "--input", str(output)]),
              patch("PySide6.QtWidgets.QApplication", return_value=application),
              patch("detector.Detector", return_value=detector) as detector_factory,
              patch.object(vision_app, "apply_theme"),
              patch.object(compare_models, "build_sample_window", return_value=window) as window_factory,
              patch.multiple(config, MODEL_PATH=config.MODEL_PATH, IMGSZ=config.IMGSZ,
                             FRAME_W=config.FRAME_W, FRAME_H=config.FRAME_H)):
            detector_factory.side_effect = lambda: captured_profiles.append((config.MODEL_PATH, config.IMGSZ)) or detector
            compare_models.main()
        window_factory.assert_called_once_with(detector, FAKE_INDEX, output, [], config.CONF_DEFAULT,
                                               auto_close=False)
        detector_factory.assert_called_once()
        application.exec.assert_called_once()
        window.show.assert_called_once()
        detector.face.close.assert_called_once()
        assert captured_profiles == [config.MODEL_PROFILES[config.DEFAULT_QUALITY]]
        assert not (output / "comparison.json").exists()


def test_comparison_uses_all_configured_profiles():
    directory = config.ROOT / ".venv/verification"
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="test_compare_profiles_", dir=directory) as temporary:
        output = Path(temporary)
        profiles = {"detail": (output / "detail", 480), "fast": (output / "fast", 320),
                    "accurate": (output / "accurate", 384)}
        (output / "samples.json").write_text(json.dumps([{"file": "laptop.png", "expected": "laptop"}]),
                                             encoding="utf-8")
        created_profiles, detectors = [], []

        def detector_factory():
            created_profiles.append((config.MODEL_PATH, config.IMGSZ))
            detector = SimpleNamespace(detect=Mock(return_value=[]), face=SimpleNamespace(close=Mock()))
            detectors.append(detector)
            return detector

        with (patch.object(sys, "argv", ["compare_models.py", "--input", str(output)]),
              patch.dict(config.MODEL_PROFILES, profiles, clear=True),
              patch.multiple(config, DEFAULT_QUALITY="detail", MODEL_PATH=config.MODEL_PATH, IMGSZ=config.IMGSZ),
              patch("detector.Detector", side_effect=detector_factory),
              patch.object(cv2, "imread", return_value=np.zeros((4, 4, 3), dtype=np.uint8))):
            compare_models.main()
        assert created_profiles == list(profiles.values())
        report = json.loads((output / "comparison.json").read_text(encoding="utf-8"))
        assert [row["quality"] for row in report["results"]] == list(profiles)
        assert [row["inference_size"] for row in report["results"]] == [480, 320, 384]
        for detector in detectors:
            detector.detect.assert_called_once()
            detector.face.close.assert_called_once()


def main():
    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    test_multiple_samples_include_laptop()
    test_default_targets_ignore_laptop_count()
    test_capture_only_exits_without_comparing()
    test_comparison_uses_all_configured_profiles()
    print("OK: 4 pruebas; laptop, metas originales, captura indefinida y comparacion de todos los perfiles.")


if __name__ == "__main__":
    main()
