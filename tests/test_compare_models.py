"""Prueba cinco capturas reales del widget con frames sintéticos; sin cámara/modelos."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from test_app import (FAKE_INDEX, FakeCamera, FakeDetector, QCoreApplication,
                      QEvent, QApplication, config, vision_app, wait_until)
from tools.compare_models import build_sample_window
import cv2
import numpy as np


def main():
    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    directory = config.ROOT / ".venv/verification"
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="test_samples_", dir=directory) as temporary:
        output, samples = Path(temporary), []
        camera, detector = FakeCamera(), FakeDetector()
        with patch.object(vision_app, "open_camera", return_value=camera):
            window = build_sample_window(detector, FAKE_INDEX, output, samples, 0.35, auto_close=False)
            for timer in (window.frame_timer, window.panel_timer, window.retry_timer):
                timer.stop()
            try:
                window.sample_button.click()
                assert not samples, "No guardar un objeto antes de recibir un frame"
                for index in range(5):
                    color = 80 + index * 25
                    camera.frame.fill(color)
                    window.tick()
                    wait_until(lambda: window._inflight is None)
                    assert window.raw_frame is not None
                    window.sample_selector.setCurrentIndex(0 if index < 3 else 1)
                    window.sample_button.click()
                    assert len(samples) == index + 1
                    saved = cv2.imread(str(output / samples[-1]["file"]))
                    assert np.all(saved == color), "La muestra debe ser nueva y no contener overlays"
                    assert f"({index + 1})" in window.sample_button.text()
                persisted = json.loads((output / "samples.json").read_text(encoding="utf-8"))
                assert len({s["file"] for s in persisted}) == 5
                assert [s["expected"] for s in persisted] == ["book"] * 3 + ["cell phone"] * 2
                assert len(list(output.glob("*.png"))) == 5
                events = [json.loads(line) for line in (output / "capture_events.jsonl").read_text(encoding="utf-8").splitlines()]
                assert [e["status"] for e in events] == ["waiting_for_frame"] + ["saved"] * 5
                print("OK: cinco pulsaciones guardan cinco PNG distintos, sin overlays y con etiquetas correctas.")
            finally:
                window.close()
                window.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


if __name__ == "__main__":
    main()
