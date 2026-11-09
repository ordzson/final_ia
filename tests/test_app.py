"""Integración Qt con cámara, imágenes y detecciones SINTÉTICAS; nunca abre hardware.

Ejecutar: .venv/Scripts/python.exe -B tests/test_app.py
No valida reconocimiento real, FPS, iluminación física ni desconexiones del dispositivo.
Los PNG temporales se crean únicamente dentro de .venv/verification y se eliminan al salir.
"""
import os
import sys
import threading
import time
from contextlib import ExitStack, contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".venv" / "ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv" / "matplotlib"))

import numpy as np
from PySide6.QtCore import QCoreApplication, QEvent, QTimer
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication, QPushButton

import app as vision_app
import config
from detector import Det

FAKE_INDEX = 47
WIDTH, HEIGHT = 640, 360


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        assert seconds >= 0
        self.now += seconds

    def set(self, now):
        assert now >= self.now
        self.now = now


class FakeCamera:
    """Solo devuelve una matriz de píxeles en memoria; read_ok simula pérdida de frames."""
    def __init__(self, brightness=150, read_ok=True):
        self.frame = np.full((HEIGHT, WIDTH, 3), brightness, dtype=np.uint8)
        self.read_ok = read_ok
        self.released = False
        self.read_calls = 0
        self.read_threads = []
        self.copy_on_read = True

    def read(self):
        self.read_calls += 1
        self.read_threads.append(threading.get_ident())
        if self.released or not self.read_ok:
            return False, None
        return True, self.frame.copy() if self.copy_on_read else self.frame

    def get(self, prop):
        return {
            vision_app.cv2.CAP_PROP_FRAME_WIDTH: WIDTH,
            vision_app.cv2.CAP_PROP_FRAME_HEIGHT: HEIGHT,
            vision_app.cv2.CAP_PROP_FPS: 30,
        }.get(prop, 0)

    def release(self):
        self.released = True


class FakeDetector:
    """El filtrado representa datos conocidos, no ejecuta ni evalúa ningún modelo."""
    def __init__(self):
        self.available_keys = set(config.UNI_ITEMS) | {"person", "bottle"}
        self.detections = []
        self.calls = []
        self.started = threading.Event()
        self.allow_finish = threading.Event()
        self.allow_finish.set()
        self.failure = None
        self.thread_ids = []

    def detect(self, frame, conf, groups, only_keys=None):
        detections, failure = list(self.detections), self.failure
        self.thread_ids.append(threading.get_ident())
        self.calls.append(SimpleNamespace(
            conf=conf, groups=set(groups),
            only_keys=None if only_keys is None else set(only_keys),
            shape=frame.shape,
        ))
        self.started.set()
        if not self.allow_finish.wait(5):
            raise RuntimeError("La prueba no liberó el detector sintético")
        if failure is not None:
            raise failure
        return [d for d in detections
                if d.group in groups and d.conf >= conf
                and (only_keys is None or d.key in only_keys)]


def detection(key, conf=0.95):
    face = key == config.FACE_KEY
    group = "rostros" if face else "personas" if key in config.PERSON_KEYS else "objetos"
    label = config.FACE_LABEL if face else config.LABELS_ES[key]
    return Det(key, label, conf, (80, 90, 280, 280), group)


@contextmanager
def fake_window(mode="general", connected=True, requested=FAKE_INDEX, *, live_scoring=False):
    """Construye la ventana real con todas las entradas externas sustituidas."""
    verification = config.ROOT / ".venv" / "verification"
    verification.mkdir(parents=True, exist_ok=True)
    clock, detector = FakeClock(), FakeDetector()
    camera = FakeCamera() if connected else None
    camera_list = [(FAKE_INDEX, WIDTH, HEIGHT)] if connected else []
    fake_time = SimpleNamespace(**vars(time))
    fake_time.monotonic = clock
    with TemporaryDirectory(prefix="test_app_", dir=verification) as temporary, ExitStack() as stack:
        captures = Path(temporary) / "capturas"
        stack.enter_context(patch.object(config, "CAPTURES_DIR", captures))
        stack.enter_context(patch.object(vision_app, "time", fake_time))
        opened = stack.enter_context(patch.object(vision_app, "open_camera", return_value=camera))
        probed = stack.enter_context(patch.object(vision_app, "probe_cameras", return_value=[]))
        win = vision_app.MainWindow(detector, camera_list, requested, mode, live_scoring=live_scoring)
        # Se emiten los ticks explícitamente: no hay esperas, cámara real ni medidas de FPS.
        for timer in (win.frame_timer, win.panel_timer, win.retry_timer):
            timer.stop()
        win.centralWidget().layout().activate()
        processed = []
        win.frame_processed.connect(lambda groups, size: processed.append(
            (groups, size, threading.get_ident())))
        try:
            yield SimpleNamespace(win=win, clock=clock, detector=detector, camera=camera,
                                  opened=opened, probed=probed, captures=captures, processed=processed)
        finally:
            detector.allow_finish.set()
            win.close()
            assert not win.inference_thread.isRunning()
            win.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def wait_until(predicate, seconds=5):
    deadline = time.monotonic() + seconds
    while not predicate():
        QCoreApplication.processEvents()
        assert time.monotonic() < deadline, "No llegó el resultado asíncrono esperado"
        time.sleep(0.001)


def tick(fixture, seconds=0.05):
    fixture.clock.advance(seconds)
    fixture.win.tick()
    wait_until(lambda: fixture.win._inflight is None)


def button(win, text):
    buttons = [b for b in win.findChildren(QPushButton) if b.text() == text]
    assert len(buttons) == 1, (text, len(buttons))
    return buttons[0]


def same_pixels(left, right):
    fmt = QImage.Format.Format_RGBA8888
    return left.size() == right.size() and left.convertToFormat(fmt) == right.convertToFormat(fmt)


def test_groups_confidence_and_modes():
    with fake_window() as f:
        w = f.win
        f.detector.detections = [detection("person"), detection(config.FACE_KEY, 0.93),
                                 detection("laptop", 0.82), detection("book", 0.65),
                                 detection("bottle", 0.45)]
        tick(f)
        assert {d.group for d in w.last_dets} == set(vision_app.GROUPS)
        for group, check in w.group_checks.items():
            check.click()
            tick(f)
            assert f.detector.calls[-1].groups == set(vision_app.GROUPS) - {group}
            assert all(d.group != group for d in w.last_dets)
            check.click()
        w.conf_slider.setValue(90)
        tick(f)
        assert w.conf == 0.90 and w.conf_label.text() == "90%"
        assert f.detector.calls[-1].conf == 0.90
        assert {d.key for d in w.last_dets} == {"person", config.FACE_KEY}
        w.conf_slider.setValue(35)
        w.mode_buttons["uni"].click()
        assert w.mode == "uni" and w.mode_buttons["uni"].isChecked()
        assert not w.uni_section.isHidden()
        assert all(not c.isEnabled() and c.toolTip() == vision_app.UNI_ONLY_TIP
                   for c in w.group_checks.values())
        tick(f)
        call = f.detector.calls[-1]
        assert call.groups == {"objetos"} and call.only_keys == set(config.UNI_ITEMS)
        assert {d.key for d in w.last_dets} == {"laptop", "book"}
        tick(f, 0.35)
        assert w.uni_state.score == 45 and w.best_score == 45
        w.mode_buttons["general"].click()
        assert w.mode == "general" and w.uni_section.isHidden()
        assert all(c.isEnabled() and c.toolTip() == "" for c in w.group_checks.values())
        w.mode_buttons["uni"].click()
        assert w.uni_state.phase == "waiting" and w.uni_state.score == 0
        assert w.best_score == 45


def test_uni_round_toggle_accumulates_sequential_objects():
    with fake_window(mode="uni", live_scoring=True) as f:
        w = f.win
        assert not w.uni_round_check.isChecked() and w.round_row.isHidden()
        assert w.collected_title.text() == "ÍTEMS VISIBLES"
        f.detector.detections = [detection("laptop")]
        tick(f)
        tick(f, 0.35)
        assert w.uni_state.score == 25
        f.detector.detections = []
        tick(f, 0.8)
        assert w.uni_state.score == 0
        session_start = w.session_start
        appearances = dict(w.appearances)
        w.uni_round_check.click()
        assert not w.live_scoring and not w.uni_scorer.live
        assert not w.round_row.isHidden() and w.round_value.text() == "Esperando"
        assert w.collected_title.text() == "ÍTEMS GUARDADOS"
        assert w.uni_state.score == 0 and w.uni_state.time_left == config.UNI_ROUND_S
        assert w.best_score == 25 and w.session_start == session_start and w.appearances == appearances

        for key, expected in (("laptop", 25), ("book", 45), ("cell phone", 50)):
            f.detector.detections = [detection(key)]
            tick(f)
            tick(f, 0.35)
            assert w.uni_state.score == expected
            f.detector.detections = []
            tick(f, 0.8)
            assert w.uni_state.score == expected and w.uni_state.present == []
        assert w.uni_state.badge and w.uni_state.phase == "running"
        deadline = w.uni_scorer._start + config.UNI_ROUND_S
        f.clock.set(deadline + 0.1)
        w.update_panel()
        assert w.uni_state.phase == "result" and w.uni_state.score == 50
        assert w.round_value.text() == "Terminada"
        f.clock.set(deadline + config.UNI_RESULT_S + 0.1)
        w.update_panel()
        assert w.uni_state.phase == "waiting" and w.uni_state.score == 0

        w.toggle_mode()
        assert w.uni_section.isHidden()
        w.toggle_mode()
        assert w.uni_round_check.isChecked() and not w.live_scoring
        w.uni_round_check.click()
        assert w.live_scoring and w.uni_scorer.live and w.round_row.isHidden()
        assert w.uni_state.score == 0 and w.best_score == 50
        f.detector.detections = [detection("laptop")]
        tick(f)
        tick(f, 0.35)
        assert w.uni_state.score == 25
        f.detector.detections = []
        tick(f, 0.8)
        assert w.uni_state.score == 0


def test_capture_png_flash_counters_and_reset():
    with fake_window() as f:
        w = f.win
        f.camera.frame.fill(40)
        tick(f)
        original = w.last_image.copy()
        expected_height = HEIGHT - vision_app.CROP_TOP
        assert original.width() == WIDTH and original.height() == expected_height
        # Fuerza dos capturas en el mismo segundo para comprobar nombres sin sobrescritura.
        with patch.object(vision_app, "datetime") as stamp:
            stamp.now.return_value = datetime(2026, 11, 8, 12, 0, 0)
            button(w, "Capturar").click()
            w.show_image(w.last_image, f.clock())
            shown = w.video.pixmap().toImage()
            assert shown.pixelColor(shown.width() // 2, shown.height() // 2).red() > 40
            assert same_pixels(w.last_image, original), "El flash alteró la imagen que se guarda"
            button(w, "Capturar").click()
        files = sorted(f.captures.glob("*.png"))
        assert [p.name for p in files] == ["20261108_120000.png", "20261108_120000_1.png"]
        for path in files:
            saved = QImage(str(path))
            assert not saved.isNull() and same_pixels(saved, original)
        w.update_panel()
        assert w.captures == 2 and w.captures_value.text() == "2"
        f.detector.detections = [detection("laptop")]
        w.mode_buttons["uni"].click()
        tick(f)
        tick(f, 0.35)
        assert w.best_score == 25 and w.appearances == {"laptop": 1}
        f.clock.advance(5)
        button(w, "Reiniciar").click()
        assert w.appearances == {} and w.best_score == 0 and w.captures == 0
        assert w.uni_state.phase == "waiting" and w.uni_state.score == 0
        assert w.time_value.text() == "00:00" and w.captures_value.text() == "0"
        assert len(list(f.captures.glob("*.png"))) == 2, "Reiniciar solo limpia contadores"


def test_low_light_with_synthetic_frames():
    for mode in ("general", "uni"):
        with fake_window(mode=mode) as f:
            tick(f)
            assert not f.win.low_light
            f.camera.frame.fill(10)
            tick(f)
            tick(f, vision_app.LOW_LIGHT_S - 0.1)
            assert not f.win.low_light
            tick(f, 0.2)
            f.win.update_panel()
            assert f.win.low_light and "Baja" in f.win.light_value.text()
            image = f.win.last_image
            assert image.pixelColor(8, image.height() - 8) == QColor(vision_app.LOW_LIGHT_BG)
            f.camera.frame.fill(150)
            tick(f)
            f.win.update_panel()
            assert not f.win.low_light and "OK" in f.win.light_value.text()
            image = f.win.last_image
            assert image.pixelColor(8, image.height() - 8) == QColor(150, 150, 150)


def test_missing_camera_retry_disconnect_and_reconnect():
    with fake_window(connected=False) as f:
        w = f.win
        f.opened.assert_called_once_with(FAKE_INDEX)
        assert w.cap is None and w.video.text() == vision_app.NO_CAMERA_TEXT
        button(w, "Capturar").click()
        assert w.captures == 0 and not f.captures.exists()
        assert "No hay imagen" in w.statusBar().currentMessage()
        bad, recovered = FakeCamera(read_ok=False), FakeCamera()
        f.opened.side_effect = [None, bad, recovered]
        w.show_no_camera()
        assert w.retry_timer.isActive()
        w.retry_camera()
        assert w.cap is None and w.retry_timer.isActive()
        w.retry_camera()
        assert bad.released and w.cap is None
        w.retry_camera()
        assert w.cap is recovered and not w.retry_timer.isActive()
        assert w.frame_timer.isActive() and "reconectada" in w.statusBar().currentMessage()
        w.frame_timer.stop()
        tick(f)
        assert w.last_image is not None and not w.video.pixmap().isNull()
        recovered.read_ok = False
        for _ in range(vision_app.MAX_READ_FAILS - 1):
            tick(f)
            assert w.cap is recovered
        tick(f)
        assert recovered.released and w.cap is None and w.retry_timer.isActive()
        assert w.last_image is None and w.last_dets == []
        assert w.video.text() == vision_app.NO_CAMERA_TEXT


def test_camera_discovery_and_selector_without_hardware():
    with fake_window(connected=False, requested=None) as f:
        f.opened.assert_not_called()
        f.probed.return_value = [(FAKE_INDEX, WIDTH, HEIGHT)]
        recovered = FakeCamera()
        f.opened.return_value = recovered
        f.win.retry_camera()
        assert f.win.cap is recovered and f.win.camera_idx == FAKE_INDEX
        assert f.win.camera_combo.currentData() == FAKE_INDEX
        f.win.frame_timer.stop()
    with fake_window() as f:
        alternate_index = FAKE_INDEX + 1
        f.probed.return_value = [(alternate_index, WIDTH, HEIGHT)]
        f.win.refresh_cameras()
        f.probed.assert_called_once_with(skip=FAKE_INDEX)
        combo = f.win.camera_combo
        assert combo.findData(FAKE_INDEX) >= 0 and combo.findData(alternate_index) >= 0
        replacement = FakeCamera()
        f.opened.return_value = replacement
        combo.activated.emit(combo.findData(alternate_index))
        assert f.camera.released and f.win.cap is replacement
        assert f.win.camera_idx == alternate_index and combo.currentData() == alternate_index
        f.win.frame_timer.stop()


def test_panel_clock_without_camera_frames():
    with fake_window(mode="uni") as f:
        w = f.win
        f.detector.detections = [detection("laptop")]
        tick(f)
        tick(f, 0.35)
        assert w.uni_state.phase == "running" and w.uni_state.score == 25
        deadline = f.clock() + config.UNI_ROUND_S
        calls, reads = len(f.detector.calls), f.camera.read_calls
        appearances = dict(w.appearances)
        w.show_no_camera()
        f.clock.set(deadline - 1)
        w.panel_timer.timeout.emit()
        assert abs(w.uni_state.time_left - 1) < 1e-9 and w.round_value.text() == "0:01"
        f.clock.set(deadline + 2)
        w.panel_timer.timeout.emit()
        assert w.uni_state.phase == "result" and w.uni_state.score == 25
        assert abs(w.uni_state.result_left - (config.UNI_RESULT_S - 2)) < 1e-9
        assert w.round_value.text() == vision_app.ROUND_STATUS["result"]
        f.clock.set(deadline + config.UNI_RESULT_S + 0.1)
        w.panel_timer.timeout.emit()
        assert w.uni_state.phase == "waiting" and w.uni_state.score == 0
        assert w.round_value.text() == vision_app.ROUND_STATUS["waiting"]
        assert w.best_score == 25 and w.appearances == appearances
        assert len(f.detector.calls) == calls and f.camera.read_calls == reads
        assert w.uni_state.entered == []
        # Al volver la imagen comienza una racha nueva, sin rescatar puntos de la ronda vencida.
        f.opened.return_value = FakeCamera()
        w.retry_camera()
        w.frame_timer.stop()
        f.detector.detections = [detection("book")]
        tick(f)
        assert w.uni_state.score == 0 and w.uni_state.phase == "waiting"
        tick(f, 0.35)
        assert w.uni_state.score == 20 and w.uni_state.collected == ["book"]


def test_image_colors_and_buffer_ownership():
    frame = np.array([[[19, 53, 201], [255, 0, 0]], [[0, 255, 0], [0, 0, 255]]], dtype=np.uint8)
    image = vision_app.to_qimage(frame)
    frame[:] = 0  # El video reutiliza/libera el frame después de convertirlo.
    assert image.pixelColor(0, 0).getRgb() == (201, 53, 19, 255)
    assert image.pixelColor(1, 0).getRgb() == (0, 0, 255, 255)
    assert image.pixelColor(0, 1).getRgb() == (0, 255, 0, 255)
    assert image.pixelColor(1, 1).getRgb() == (255, 0, 0, 255)


def test_worker_single_job_and_thread_affinity():
    gui_thread = threading.get_ident()
    with fake_window() as f, patch.object(config, "MIRROR", False):
        w = f.win
        f.camera.frame.fill(42)
        f.camera.copy_on_read = False  # simula un backend que reutiliza su buffer
        f.detector.allow_finish.clear()
        w.tick()
        wait_until(f.detector.started.is_set)
        job = w._inflight
        f.camera.frame.fill(0)
        assert int(job["frame"][0, 0, 0]) == 42
        for _ in range(10):
            w.tick()
        assert f.camera.read_calls == 1 and len(f.detector.calls) == 1
        assert w.shot_frames == 0 and f.processed == []
        f.clock.advance(vision_app.AUTOSHOT_WARMUP_S + 0.1)
        w.panel_timer.timeout.emit()  # la GUI responde mientras el detector está bloqueado
        f.detector.allow_finish.set()
        wait_until(lambda: w._inflight is None)
        assert f.camera.read_threads == [gui_thread]
        assert f.detector.thread_ids[0] != gui_thread
        assert f.processed == [(set(vision_app.GROUPS), (WIDTH, HEIGHT - vision_app.CROP_TOP), gui_thread)]
        assert w.shot_frames == 1 and w.last_tick == f.clock()
        w.on_inference_finished(job, [], None)  # una entrega duplicada no vuelve a contar
        assert w.shot_frames == 1 and len(f.processed) == 1


def test_obsolete_generations_are_discarded():
    for action in ("mode", "confidence", "groups", "camera", "reset", "uni_round"):
        with fake_window() as f:
            w = f.win
            f.detector.detections = [detection("laptop")]
            f.detector.allow_finish.clear()
            # Incluso un error de la generación anterior debe descartarse sin detener la nueva.
            if action == "confidence":
                f.detector.failure = RuntimeError("fallo obsoleto")
            f.clock.advance(vision_app.AUTOSHOT_WARMUP_S + 0.1)
            w.tick()
            wait_until(f.detector.started.is_set)
            job = w._inflight
            if action == "mode":
                w.mode_buttons["uni"].click()
            elif action == "confidence":
                w.conf_slider.setValue(90)
            elif action == "groups":
                w.group_checks["personas"].click()
            elif action == "camera":
                f.opened.return_value = FakeCamera()
                w.start_camera(FAKE_INDEX + 1)
                w.frame_timer.stop()
            elif action == "uni_round":
                w.uni_round_check.click()
            else:
                button(w, "Reiniciar").click()
            assert w._inflight is job and w._generation != job["generation"]
            w.tick()
            assert len(f.detector.calls) == 1
            f.detector.allow_finish.set()
            wait_until(lambda: w._inflight is None)
            assert f.processed == [] and w.last_image is None and w.last_dets == []
            assert w.shot_frames == 0 and w.appearances == {} and w.uni_state.score == 0
            assert not w._inference_error and "fallo obsoleto" not in w.statusBar().currentMessage()
            f.detector.failure = None
            tick(f)
            assert len(f.processed) == 1 and w.last_image is not None


def test_inference_error_pauses_until_user_action():
    with fake_window() as f:
        w = f.win
        f.detector.failure = RuntimeError("fallo sintético")
        tick(f)
        assert w._inference_error and not w.frame_timer.isActive()
        assert "fallo sintético" in w.statusBar().currentMessage() and f.processed == []
        for _ in range(10):
            w.tick()
        assert f.camera.read_calls == 1 and len(f.detector.calls) == 1
        f.detector.failure = None
        w.conf_slider.setValue(70)
        w.frame_timer.stop()
        tick(f)
        assert not w._inference_error and len(f.processed) == 1


def test_next_job_is_dispatched_before_render():
    with fake_window() as f:
        w = f.win
        f.detector.allow_finish.clear()
        w.tick()
        wait_until(f.detector.started.is_set)
        order = []
        w.inference_requested.connect(lambda job: order.append("dispatch"))
        show_image = w.show_image

        def render(image, now):
            order.append("render")
            if len(order) == 2:
                assert w._inflight is not None and f.camera.read_calls == 2
            w.frame_timer.stop()  # permite completar el segundo trabajo, sin iniciar un tercero
            show_image(image, now)

        # Se mantiene activo sin disparar por tiempo; el resultado inicia directamente el siguiente.
        w.frame_timer.start(1000000)
        with patch.object(w, "show_image", side_effect=render):
            f.detector.allow_finish.set()
            wait_until(lambda: len(f.processed) == 2 and w._inflight is None)
        assert order[:2] == ["dispatch", "render"]
        assert f.camera.read_calls == 2 and len(f.detector.calls) == 2


def test_shutdown_waits_for_worker_and_application_quit():
    for via_application in (False, True):
        with fake_window() as f:
            w = f.win
            f.detector.allow_finish.clear()
            w.tick()
            wait_until(f.detector.started.is_set)
            release = threading.Timer(0.03, f.detector.allow_finish.set)
            release.start()
            try:
                if via_application:
                    QTimer.singleShot(0, QApplication.instance().quit)
                    assert QApplication.instance().exec() == 0
                else:
                    w.close()
            finally:
                release.join()
            assert w._closing and f.camera.released and not w.inference_thread.isRunning()
            assert w._inflight is None and f.processed == []
            w.shutdown()  # también debe poder llamarse desde más de una ruta de cierre


def main():
    qt_app = QApplication.instance() or QApplication([])
    qt_app.setQuitOnLastWindowClosed(False)
    vision_app.apply_theme(qt_app)
    tests = [test_image_colors_and_buffer_ownership, test_groups_confidence_and_modes,
             test_uni_round_toggle_accumulates_sequential_objects,
             test_capture_png_flash_counters_and_reset,
             test_low_light_with_synthetic_frames, test_missing_camera_retry_disconnect_and_reconnect,
             test_camera_discovery_and_selector_without_hardware, test_panel_clock_without_camera_frames,
             test_worker_single_job_and_thread_affinity, test_obsolete_generations_are_discarded,
             test_inference_error_pauses_until_user_action, test_next_job_is_dispatched_before_render,
             test_shutdown_waits_for_worker_and_application_quit]
    # Una regresión que intente usar el dispositivo o cargar modelos falla de inmediato.
    with patch.object(vision_app.cv2, "VideoCapture", side_effect=AssertionError("Hardware prohibido en test_app")), \
            patch.object(vision_app, "Detector", side_effect=AssertionError("Modelos reales prohibidos en test_app")):
        for test in tests:
            test()
            print(f"OK {test.__name__}", flush=True)
    print(f"OK: {len(tests)} pruebas Qt con datos sintéticos; sin cámara ni modelos reales.")


if __name__ == "__main__":
    main()
