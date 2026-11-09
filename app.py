"""VisionAI — interfaz gráfica: cámara en vivo, detección de objetos y estadísticas de sesión."""
import argparse
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
from PySide6.QtCore import QObject, QRectF, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QFontMetrics, QImage, QKeySequence, QPainter,
                           QPalette, QPen, QPixmap, QShortcut)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton, QSizePolicy, QSlider,
                               QVBoxLayout, QWidget)

import config
from detector import Detector
from scoring import PresenceTracker, UniScorer

GROUPS = {"objetos": "Objetos", "personas": "Personas", "rostros": "Rostros"}
MODE_NAMES = {"general": "General", "uni": "Universitario"}
NO_CAMERA_TEXT = "Cámara no disponible — conecta una cámara o elige otra en el selector"
MAX_READ_FAILS = 15
FPS_ALPHA = 0.1
FLASH_S = 0.25
AUTOSHOT_WARMUP_S = 2.0
UNI_ONLY_TIP = "Solo en modo General"
SCORE_EASE = 0.15                  # animación de la barra: disp += (score - disp) * SCORE_EASE
FLOAT_S = 1.0                      # duración de los "+X pts" flotantes
HUD_H = 120                        # alto del HUD a 720 px; se escala con s
DARK_TEXT = config.THEME["bg"]     # texto oscuro sobre fondos dorados
CHIP_OFF_BG = "#2b2f45"
LOW_LIGHT_S = 1.0                  # segundos seguidos con poca luz antes de avisar
LOW_LIGHT_TEXT = "Poca luz: la detección puede fallar. Acerca una lámpara."
LOW_LIGHT_BG = "#ffd23f"
RETRY_MS = 2000                    # sin cámara: cada cuánto se reintenta abrirla
CROP_TOP = 0 if sys.platform == "win32" else 4  # solo la cámara USB de Linux necesita quitar la franja superior
WARN_S = 10                        # últimos segundos de la ronda: el reloj se pone rojo
WARN_COLOR = "#ff6b6b"
ROUND_CAPTIONS = {"waiting": "Muestra un objeto", "running": "restantes", "result": "ronda terminada"}
ROUND_STATUS = {"waiting": "Esperando", "result": "Terminada"}  # panel; en "running" se muestra el reloj

# Evita los avisos repetidos de cámara; la API de logging cambia entre OpenCV 4 y 5.
if hasattr(cv2, "setLogLevel"):
    cv2.setLogLevel(2)  # LOG_LEVEL_ERROR
else:
    cv_logging = getattr(getattr(cv2, "utils", None), "logging", None)
    if cv_logging is not None:
        cv_logging.setLogLevel(cv_logging.LOG_LEVEL_ERROR)


def open_camera(idx: int) -> cv2.VideoCapture | None:
    """Abre la cámara en MJPG a FRAME_W×FRAME_H (si no la soporta, queda la que entregue). None si no abre."""
    backends = (cv2.CAP_DSHOW, cv2.CAP_MSMF) if sys.platform == "win32" else (cv2.CAP_V4L2,)
    for backend in backends:
        cap = cv2.VideoCapture(idx, backend)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_W)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_H)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        cap.release()
    return None


def probe_cameras(skip: int | None = None) -> list[tuple[int, int, int]]:
    """Prueba los índices 0-5 (menos skip) y devuelve (índice, ancho, alto) de los que entregan imagen."""
    found = []
    for i in range(6):
        if i == skip:
            continue
        cap = open_camera(i)
        if cap is None:
            continue
        ok, frame = cap.read()
        cap.release()
        if ok and frame is not None:
            h, w = frame.shape[:2]
            found.append((i, w, h))
    return found


def key_label(key: str) -> str:
    return config.FACE_LABEL if key == config.FACE_KEY else config.LABELS_ES[key]


def key_group(key: str) -> str:
    if key == config.FACE_KEY:
        return "rostros"
    return "personas" if key in config.PERSON_KEYS else "objetos"


def to_qimage(frame_bgr) -> QImage:
    h, w, _ = frame_bgr.shape
    image = QImage(frame_bgr.data, w, h, frame_bgr.strides[0], QImage.Format.Format_BGR888)
    # RGB32 acelera QPainter/QPixmap y crea un buffer propio, sin perder color de 8 bits.
    return image.convertToFormat(QImage.Format.Format_RGB32)


def px_font(px: float, bold: bool = True) -> QFont:
    font = QFont()
    font.setBold(bold)
    font.setPixelSize(max(1, round(px)))
    return font


def clock(seconds: float) -> str:
    """Segundos → "m:ss", redondeando hacia arriba: la ronda muestra 1:00 al empezar y 0:00 solo al final."""
    total = math.ceil(round(max(0.0, seconds), 3))
    return f"{total // 60}:{total % 60:02d}"


def draw_box(p: QPainter, box: tuple[int, int, int, int], color: QColor, text: str,
             font: QFont, s: float, img_w: int, text_color: str = "white", top: float = 0,
             taken: list[QRectF] | None = None) -> None:
    """Rectángulo del color del grupo con una píldora rellena encima (o dentro si no cabe arriba).
    top: la píldora nunca sube de esta y (el HUD del modo Universitario la taparía).
    taken: píldoras ya dibujadas en este frame; si la nueva choca con alguna, baja justo debajo de ella."""
    x1, y1, x2, y2 = box
    p.setPen(QPen(color, 3 * s))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(QRectF(x1, y1, x2 - x1, y2 - y1))

    fm = QFontMetrics(font)
    w = fm.horizontalAdvance(text) + 20 * s
    h = fm.height() + 8 * s
    x = max(0.0, min(float(x1), img_w - w))
    y = y1 - h if y1 - h >= top else max(y1, top) + 3 * s
    rect = QRectF(x, y, w, h)
    if taken is not None:
        # Termina: cada paso baja la píldora por debajo de otra ya dibujada
        while hits := [r for r in taken if rect.intersects(r)]:
            rect.moveTop(max(r.bottom() for r in hits) + 2 * s)
        taken.append(rect)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    p.drawRoundedRect(rect, h / 2, h / 2)
    p.setFont(font)
    p.setPen(QColor(text_color))
    p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


def rows_html(rows: list[tuple[str, str, str]]) -> str:
    """Tabla de filas (color del punto, texto, valor) para las listas del panel."""
    if not rows:
        return f'<span style="color:{config.THEME["muted"]}">—</span>'
    cells = "".join(
        f'<tr><td><span style="color:{color}">●</span>&nbsp;{text}</td>'
        f'<td align="right"><b>{value}</b></td></tr>'
        for color, text, value in rows
    )
    return f'<table width="100%" cellspacing="0" cellpadding="3">{cells}</table>'


class CameraCombo(QComboBox):
    """Selector de cámara que vuelve a buscar cámaras al abrirse (así aparecen las conectadas en caliente)."""

    def __init__(self, refresh) -> None:
        super().__init__()
        self.refresh = refresh

    def showPopup(self) -> None:
        self.refresh()
        super().showPopup()


class InferenceWorker(QObject):
    """Ejecuta solo el detector. La cámara y todos los widgets pertenecen al hilo de la interfaz."""
    finished = Signal(object, object, object)

    def __init__(self, detector: Detector) -> None:
        super().__init__()
        self.detector = detector

    @Slot(object)
    def run(self, job) -> None:
        try:
            dets = self.detector.detect(job["frame"], job["conf"], job["groups"],
                                        only_keys=job["only_keys"])
        except Exception as error:
            self.finished.emit(job, None, f"{type(error).__name__}: {error}")
        else:
            self.finished.emit(job, dets, None)


class MainWindow(QMainWindow):
    frame_processed = Signal(object, object)  # (grupos del frame aceptado, (ancho, alto))
    inference_requested = Signal(object)

    def __init__(self, detector: Detector, cameras: list[tuple[int, int, int]],
                 camera_idx: int | None, mode: str, *, live_scoring: bool = False) -> None:
        super().__init__()
        self.detector = detector
        self.stats_tracker = PresenceTracker()
        self.uni_scorer = UniScorer(detector.available_keys, live=live_scoring)
        self.live_scoring = live_scoring
        self.cap: cv2.VideoCapture | None = None
        self.camera_idx: int | None = None      # cámara elegida; se reintenta si se pierde
        self.mode = mode
        self.conf = config.CONF_DEFAULT
        self.last_image: QImage | None = None   # último frame dibujado a resolución completa (lo guarda Capturar)
        self.last_dets = []
        self.read_fails = 0
        self.fps_dt: float | None = None        # media móvil del tiempo entre ticks
        self.last_tick: float | None = None
        self.flash_start: float | None = None
        self.dark_since: float | None = None    # inicio de la racha actual con poca luz
        self.low_light = False
        self.loop_start = time.monotonic()
        self.shot_frames = 0
        self._generation = 0
        self._inflight = None               # permanece ocupado aunque se invalide su generación
        self._inference_error = False
        self._closing = False
        self.reset_session()

        self.setWindowTitle("VisionAI — Detector de Objetos en Tiempo Real")
        self.resize(1440, 860)
        self.setMinimumSize(1100, 700)
        self._build_ui(cameras)
        self._build_shortcuts()

        self.frame_timer = QTimer(self)
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.frame_timer.setInterval(1)
        self.frame_timer.timeout.connect(self.tick)
        self.panel_timer = QTimer(self)
        self.panel_timer.setInterval(250)
        self.panel_timer.timeout.connect(self.update_panel)
        self.panel_timer.start()
        self.retry_timer = QTimer(self)
        self.retry_timer.setInterval(RETRY_MS)
        self.retry_timer.timeout.connect(self.retry_camera)

        self.inference_thread = QThread(self)
        self.inference_thread.setObjectName("VisionAIInference")
        self.inference_worker = InferenceWorker(detector)
        self.inference_worker.moveToThread(self.inference_thread)
        self.inference_requested.connect(self.inference_worker.run, Qt.ConnectionType.QueuedConnection)
        self.inference_worker.finished.connect(self.on_inference_finished, Qt.ConnectionType.QueuedConnection)
        self.inference_thread.finished.connect(self.inference_worker.deleteLater)
        self.inference_thread.start()
        QApplication.instance().aboutToQuit.connect(self.shutdown)

        self._select_initial_camera(cameras, camera_idx)
        self.set_mode(mode)

    # --- Construcción de la interfaz ---

    def _build_ui(self, cameras: list[tuple[int, int, int]]) -> None:
        central = QWidget(objectName="central")
        root = QHBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addLayout(self._build_top_row(cameras))
        left.addLayout(self._build_controls_row())

        self.video = QLabel(objectName="video")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video.setWordWrap(True)
        # Ignored: si no, cada pixmap escalado agranda el layout y la ventana crece sin fin
        self.video.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.video.setMinimumSize(640, 360)
        left.addWidget(self.video, 1)

        root.addLayout(left, 1)
        root.addWidget(self._build_panel())
        self.setCentralWidget(central)

        # Sin foco en los controles: así Espacio, M y R siempre llegan a los atajos
        for w in central.findChildren(QWidget):
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def _build_top_row(self, cameras: list[tuple[int, int, int]]) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(QLabel("VisionAI", objectName="brand"))
        row.addSpacing(16)

        row.addWidget(QLabel("Cámara"))
        self.camera_combo = CameraCombo(self.refresh_cameras)
        self.camera_combo.setMinimumWidth(200)
        self.camera_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fill_camera_combo(cameras)
        row.addWidget(self.camera_combo)
        row.addSpacing(16)

        # Botón segmentado: dos botones pegados en un grupo exclusivo
        seg = QHBoxLayout()
        seg.setSpacing(0)
        self.mode_group = QButtonGroup(self)
        self.mode_buttons = {}
        for mode, name in MODE_NAMES.items():
            btn = QPushButton(name, objectName="segLeft" if mode == "general" else "segRight")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # El botón activo va en negrita (QSS :checked) y su sizeHint no lo contempla
            bold = QFont(btn.font())
            bold.setBold(True)
            btn.setMinimumWidth(QFontMetrics(bold).horizontalAdvance(name) + 40)
            self.mode_group.addButton(btn)
            self.mode_buttons[mode] = btn
            btn.clicked.connect(lambda _=False, m=mode: self.set_mode(m))
            seg.addWidget(btn)
        row.addLayout(seg)
        row.addStretch(1)
        return row

    def _build_controls_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        self.group_checks = {}
        for group, name in GROUPS.items():
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.toggled.connect(self.invalidate_inference)
            self.group_checks[group] = cb
            row.addWidget(cb)
        row.addSpacing(16)

        row.addWidget(QLabel("Confianza"))
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(10, 90)
        self.conf_slider.setValue(round(config.CONF_DEFAULT * 100))
        self.conf_slider.setFixedWidth(180)
        self.conf_label = QLabel()
        self.conf_label.setMinimumWidth(40)
        self.conf_slider.valueChanged.connect(self.on_conf_changed)
        self.on_conf_changed(self.conf_slider.value())
        row.addWidget(self.conf_slider)
        row.addWidget(self.conf_label)
        row.addStretch(1)

        capture_btn = QPushButton("Capturar")
        capture_btn.setToolTip("Guarda la imagen con las detecciones (Espacio)")
        capture_btn.clicked.connect(self.capture)
        reset_btn = QPushButton("Reiniciar")
        reset_btn.setToolTip("Pone en cero las estadísticas de la sesión (R)")
        reset_btn.clicked.connect(self.reset_clicked)
        for btn in (capture_btn, reset_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            row.addWidget(btn)
        return row

    def _build_panel(self) -> QFrame:
        panel = QFrame(objectName="panel")
        panel.setFixedWidth(320)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(8)

        def title(lay: QVBoxLayout, text: str) -> QLabel:
            lay.addSpacing(10)
            label = QLabel(text.upper(), objectName="panelTitle")
            lay.addWidget(label)
            return label

        def value_grid(lay: QVBoxLayout, names: list[str]) -> list[QLabel]:
            grid = QGridLayout()
            grid.setVerticalSpacing(6)
            values = []
            for r, name in enumerate(names):
                grid.addWidget(QLabel(name, objectName="muted"), r, 0)
                val = QLabel(objectName="value")
                val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                grid.addWidget(val, r, 1)
                values.append(val)
            lay.addLayout(grid)
            return values

        title(lay, "Sesión")
        self.fps_value, self.time_value, self.mode_value, self.light_value = value_grid(
            lay, ["FPS", "Tiempo", "Modo", "Luz"])

        # Sección que solo se muestra en modo Universitario
        self.uni_section = QWidget()
        uni_lay = QVBoxLayout(self.uni_section)
        uni_lay.setContentsMargins(0, 0, 0, 0)
        uni_lay.setSpacing(8)
        title(uni_lay, "Puntaje")
        self.uni_round_check = QCheckBox("Ronda de 60 s")
        self.uni_round_check.setChecked(not self.live_scoring)
        self.uni_round_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.uni_round_check.setToolTip("Alterna entre puntaje en vivo y acumulativo. Reinicia el puntaje actual.")
        self.uni_round_check.toggled.connect(self.set_uni_round)
        uni_lay.addWidget(self.uni_round_check)
        self.uni_scoring_hint = QLabel(objectName="muted")
        self.uni_scoring_hint.setWordWrap(True)
        uni_lay.addWidget(self.uni_scoring_hint)
        self.score_value, self.best_value = value_grid(
            uni_lay, ["Puntaje actual", "Mejor puntaje de la sesión"])
        self.round_row = QWidget()
        round_lay = QVBoxLayout(self.round_row)
        round_lay.setContentsMargins(0, 0, 0, 0)
        (self.round_value,) = value_grid(round_lay, ["Tiempo de la ronda"])
        uni_lay.addWidget(self.round_row)
        self.collected_title = title(uni_lay, "Ítems guardados")
        self.collected_label = QLabel(textFormat=Qt.TextFormat.RichText)
        uni_lay.addWidget(self.collected_label)
        lay.addWidget(self.uni_section)

        title(lay, "En pantalla")
        self.on_screen_label = QLabel(textFormat=Qt.TextFormat.RichText)
        lay.addWidget(self.on_screen_label)
        title(lay, "Apariciones en la sesión")
        self.appear_label = QLabel(textFormat=Qt.TextFormat.RichText)
        lay.addWidget(self.appear_label)
        lay.addSpacing(10)
        (self.captures_value,) = value_grid(lay, ["Capturas"])
        lay.addStretch(1)
        return panel

    def _build_shortcuts(self) -> None:
        for keys, slot in (("Space", self.capture), ("M", self.toggle_mode),
                           ("R", self.reset_clicked), ("Ctrl+Q", self.close)):
            QShortcut(QKeySequence(keys), self, slot)

    # --- Cámara ---

    def _select_initial_camera(self, cameras: list[tuple[int, int, int]], requested: int | None) -> None:
        indices = [idx for idx, _, _ in cameras]
        if requested is None:
            requested = config.CAMERA_INDEX_DEFAULT if config.CAMERA_INDEX_DEFAULT in indices else (
                indices[0] if indices else None)
        # activated solo lo emite el usuario; los cambios hechos por código no reabren la cámara.
        # Un --camera explícito se intenta abrir aunque no haya pasado la prueba inicial.
        self.camera_combo.activated.connect(self.on_camera_changed)
        self.start_camera(requested)

    def on_camera_changed(self, i: int) -> None:
        idx = self.camera_combo.itemData(i)
        if i >= 0 and not (idx == self.camera_idx and self.cap is not None):
            self.start_camera(idx)

    def fill_camera_combo(self, cameras: list[tuple[int, int, int]]) -> None:
        combo = self.camera_combo
        combo.clear()
        for idx, w, h in cameras:
            combo.addItem(f"Cámara {idx} ({w}×{h})", idx)
        combo.setPlaceholderText("Elige una cámara" if cameras else "Sin cámaras")
        self.sync_camera_combo()

    def sync_camera_combo(self) -> None:
        """Marca en el selector la cámara elegida (o ninguna si no está en la lista)."""
        combo = self.camera_combo
        combo.setCurrentIndex(combo.findData(self.camera_idx) if self.camera_idx is not None else -1)

    def refresh_cameras(self) -> None:
        """Vuelve a buscar cámaras sin tocar la que está en uso."""
        open_idx = self.camera_idx if self.cap is not None else None
        cameras = probe_cameras(skip=open_idx)
        if open_idx is not None:
            # La cámara en uso no se puede reabrir para probarla: conserva su entrada
            w, h = (int(self.cap.get(p)) for p in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT))
            cameras = sorted(cameras + [(open_idx, w, h)])
        self.fill_camera_combo(cameras)

    def start_camera(self, idx: int | None) -> None:
        self.close_camera()
        self.camera_idx = idx
        self.sync_camera_combo()
        cap = open_camera(idx) if idx is not None else None
        if cap is None:
            self.show_no_camera()
        else:
            self.use_camera(cap)

    def use_camera(self, cap: cv2.VideoCapture) -> None:
        self.invalidate_inference()
        self.retry_timer.stop()
        self.cap = cap
        # --camera abre directamente, sin sondear las demás; conserva su entrada en el selector.
        if self.camera_combo.findData(self.camera_idx) < 0:
            w, h = (int(cap.get(p)) for p in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT))
            self.camera_combo.addItem(f"Cámara {self.camera_idx} ({w}×{h})", self.camera_idx)
            self.camera_combo.setPlaceholderText("Elige una cámara")
        self.sync_camera_combo()
        self.read_fails = 0
        self.fps_dt = self.last_tick = None
        self.dark_since = None
        self.low_light = False
        self.frame_timer.start()

    def close_camera(self) -> None:
        self.invalidate_inference()
        self.frame_timer.stop()
        self.retry_timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def show_no_camera(self) -> None:
        self.close_camera()
        self.last_image = None
        self.last_dets = []
        self.low_light = False
        self.video.setText(NO_CAMERA_TEXT)
        # Se sigue intentando: al reconectar la cámara el video vuelve solo
        self.retry_timer.start()

    def retry_camera(self) -> None:
        """Sin cámara: reintenta abrir la elegida o, si nunca hubo una, busca cualquiera."""
        if self.camera_idx is None:
            cameras = probe_cameras()
            self.fill_camera_combo(cameras)
            if cameras:
                self.start_camera(cameras[0][0])
            return
        cap = open_camera(self.camera_idx)
        if cap is None:
            return
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.release()
            return
        self.use_camera(cap)
        self.statusBar().showMessage(f"Cámara {self.camera_idx} reconectada", 3000)

    # --- Bucle de video ---

    def invalidate_inference(self, _checked=False) -> None:
        """Los controles invalidan el resultado pendiente, sin crear una segunda inferencia en cola."""
        self._generation += 1
        if self._inference_error:
            self._inference_error = False
            if not self._closing and self.cap is not None and hasattr(self, "frame_timer"):
                self.frame_timer.start()

    def tick(self) -> None:
        if self._closing or self._inference_error or self.cap is None or self._inflight is not None:
            return
        ok, frame = self.cap.read()
        if not ok or frame is None or frame.size == 0:
            self.read_fails += 1
            if self.read_fails >= MAX_READ_FAILS:
                self.show_no_camera()
            return
        self.read_fails = 0
        frame = frame[CROP_TOP:]
        if config.MIRROR:
            frame = cv2.flip(frame, 1)
        else:
            frame = frame.copy()  # el siguiente read no puede alterar el buffer que recibe el worker
        # Brillo medio sobre una miniatura en gris: barato y suficiente para avisar de poca luz
        brightness = float(cv2.cvtColor(cv2.resize(frame, (64, 36)), cv2.COLOR_BGR2GRAY).mean())

        uni = self.mode == "uni"
        groups = {"objetos"} if uni else {g for g, cb in self.group_checks.items() if cb.isChecked()}
        job = {"generation": self._generation, "frame": frame, "conf": self.conf,
               "groups": frozenset(groups), "only_keys": frozenset(self.uni_scorer.items) if uni else None,
               "mode": self.mode, "brightness": brightness}
        self._inflight = job
        self.inference_requested.emit(job)

    @Slot(object, object, object)
    def on_inference_finished(self, job, dets, error) -> None:
        if self._inflight is not job:
            return  # una entrega duplicada nunca cuenta como otro frame
        self._inflight = None
        if self._closing:
            return
        if job["generation"] != self._generation or self.cap is None:
            if self.frame_timer.isActive():
                self.tick()
            return
        if error is not None:
            self._inference_error = True
            self.frame_timer.stop()
            self.fps_dt = self.last_tick = None
            self.statusBar().showMessage(f"Error de detección: {error}. Cambia un control o reinicia para reintentar.")
            return
        # La siguiente inferencia avanza mientras la interfaz dibuja este resultado.
        if self.frame_timer.isActive():
            self.tick()
        if self._closing or job["generation"] != self._generation or self.cap is None:
            return
        frame, uni = job["frame"], job["mode"] == "uni"
        # Scoring siempre usa el reloj actual de la GUI, nunca un timestamp del worker.
        now = time.monotonic()
        _, entered = self.stats_tracker.update({d.key for d in dets}, now)
        for k in entered:
            self.appearances[k] = self.appearances.get(k, 0) + 1
        self.last_dets = dets
        self.update_light(job["brightness"], now)
        if uni:
            self.update_uni(dets, now)

        # Se dibuja a la resolución del frame, antes de escalar
        img = to_qimage(frame)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if uni:
            self.draw_uni(p, dets, img.width(), img.height(), now)
        else:
            self.draw_general(p, dets, img.width(), img.height())
        if self.low_light:
            self.draw_low_light(p, img.width(), img.height())
        p.end()
        self.last_image = img
        self.show_image(img, now)

        displayed_at = time.monotonic()
        if self.last_tick is not None:
            dt = displayed_at - self.last_tick
            self.fps_dt = dt if self.fps_dt is None else self.fps_dt + FPS_ALPHA * (dt - self.fps_dt)
        self.last_tick = displayed_at
        if displayed_at - self.loop_start >= AUTOSHOT_WARMUP_S:
            self.shot_frames += 1
        self.frame_processed.emit(set(job["groups"]), (img.width(), img.height()))

    def update_light(self, brightness: float, now: float) -> None:
        """Poca luz = brillo medio bajo LOW_LIGHT_MEAN durante más de LOW_LIGHT_S seguidos."""
        if brightness >= config.LOW_LIGHT_MEAN:
            self.dark_since = None
        elif self.dark_since is None:
            self.dark_since = now
        self.low_light = self.dark_since is not None and now - self.dark_since > LOW_LIGHT_S

    def update_uni(self, dets, now: float) -> None:
        state = self.uni_scorer.update({d.key for d in dets}, now)
        self.uni_state = state
        self.best_score = max(self.best_score, state.score)
        self.score_disp += (state.score - self.score_disp) * SCORE_EASE
        for k in state.entered:
            best = max((d for d in dets if d.key == k), key=lambda d: d.conf, default=None)
            if best is not None:
                x1, y1, x2, _ = best.box
                self.floaters.append((now, (x1 + x2) / 2, y1, f"+{self.uni_scorer.items[k][1]} pts"))
        self.floaters = [f for f in self.floaters if now - f[0] < FLOAT_S]

    def draw_general(self, p: QPainter, dets, img_w: int, img_h: int) -> None:
        s = img_h / 720
        font = px_font(16 * s)
        taken: list[QRectF] = []
        # Mayor confianza primero: esa píldora queda en su sitio y las demás se apartan
        for d in sorted(dets, key=lambda d: d.conf, reverse=True):
            draw_box(p, d.box, QColor(config.COLORS[d.group]), f"{d.label} {d.conf:.0%}", font, s, img_w,
                     taken=taken)

    def draw_uni(self, p: QPainter, dets, img_w: int, img_h: int, now: float) -> None:
        s = img_h / 720
        font = px_font(16 * s)
        taken: list[QRectF] = []
        for d in sorted(dets, key=lambda d: d.conf, reverse=True):
            text = f"{d.label} +{self.uni_scorer.items[d.key][1]} · {d.conf:.0%}"
            draw_box(p, d.box, QColor(config.COLORS["uni"]), text, font, s, img_w, DARK_TEXT, HUD_H * s, taken)
        self.draw_hud(p, img_w, s)
        if self.uni_state.badge:
            self.draw_badge(p, img_w, img_h, s, now)
        if self.uni_state.phase == "result":
            self.draw_result(p, img_w, img_h, s)
        self.draw_floaters(p, img_w, s, now)

    def draw_hud(self, p: QPainter, img_w: int, s: float) -> None:
        """Franja superior: puntaje, barra de progreso con el nivel, chips de los ítems y reloj de la ronda."""
        st = self.uni_state
        t = config.THEME
        gold = QColor(t["gold"])
        p.fillRect(QRectF(0, 0, img_w, HUD_H * s), QColor(0, 0, 0, 160))

        # Izquierda: puntaje
        left = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        p.setFont(px_font(44 * s))
        p.setPen(gold if st.badge else QColor(t["text"]))
        p.drawText(QRectF(28 * s, 10 * s, 260 * s, 60 * s), left, str(st.score))
        p.setFont(px_font(18 * s, bold=False))
        p.setPen(QColor(t["muted"]))
        p.drawText(QRectF(28 * s, 70 * s, 260 * s, 26 * s), left, f"de {st.max_score} pts")

        if not self.live_scoring:
            right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            clock_color = t["muted"] if st.phase == "result" else t["text"]
            if st.phase == "running" and st.time_left <= WARN_S:
                clock_color = WARN_COLOR
            p.setFont(px_font(44 * s))
            p.setPen(QColor(clock_color))
            p.drawText(QRectF(img_w - 288 * s, 10 * s, 260 * s, 60 * s), right, clock(st.time_left))
            p.setFont(px_font(18 * s, bold=False))
            p.setPen(QColor(t["muted"]))
            p.drawText(QRectF(img_w - 288 * s, 70 * s, 260 * s, 26 * s), right, ROUND_CAPTIONS[st.phase])

        # Centro: barra de progreso animada
        bar_w, bar_h = img_w * 0.5, 18 * s
        bar = QRectF((img_w - bar_w) / 2, 16 * s, bar_w, bar_h)
        r = bar_h / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 45))
        p.drawRoundedRect(bar, r, r)
        frac = min(1.0, self.score_disp / st.max_score) if st.max_score else 0.0
        if bar_w * frac >= 1:
            p.setBrush(gold if st.score >= config.UNI_THRESHOLD else QColor(t["accent"]))
            # Ancho mínimo bar_h para que el relleno conserve sus extremos redondeados
            p.drawRoundedRect(QRectF(bar.x(), bar.y(), max(bar_h, bar_w * frac), bar_h), r, r)
        if 0 < config.UNI_THRESHOLD < st.max_score:
            # Marca de la meta: desde ahí se gana el badge
            x = bar.x() + bar_w * config.UNI_THRESHOLD / st.max_score
            p.fillRect(QRectF(x - 1.5 * s, bar.y() - 4 * s, 3 * s, bar_h + 8 * s), QColor(255, 255, 255, 170))
        p.setFont(px_font(22 * s))
        p.setPen(gold if st.badge else QColor(t["text"]))
        p.drawText(QRectF(bar.x(), 38 * s, bar_w, 32 * s), Qt.AlignmentFlag.AlignCenter, st.level_text)

        # Chips: encendidos los guardados en la ronda, apagados los que faltan
        font = px_font(15 * s)
        fm = QFontMetrics(font)
        chips = [(f"{config.LABELS_ES[k]} +{pts}", k in st.collected)
                 for k, (_, pts) in self.uni_scorer.items.items()]
        pad, gap, chip_h = 12 * s, 8 * s, 28 * s
        widths = [fm.horizontalAdvance(text) + 2 * pad for text, _ in chips]
        x = (img_w - sum(widths) - gap * (len(chips) - 1)) / 2
        p.setFont(font)
        for (text, on), cw in zip(chips, widths):
            rect = QRectF(x, 76 * s, cw, chip_h)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(gold if on else QColor(CHIP_OFF_BG))
            p.drawRoundedRect(rect, chip_h / 2, chip_h / 2)
            p.setPen(QColor(DARK_TEXT if on else t["muted"]))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            x += cw + gap

    def draw_badge(self, p: QPainter, img_w: int, img_h: int, s: float, now: float) -> None:
        font = px_font(44 * s)
        fm = QFontMetrics(font)
        w = fm.horizontalAdvance(config.UNI_BADGE_TEXT) + 64 * s
        h = fm.height() + 28 * s
        rect = QRectF((img_w - w) / 2, img_h * 5 / 6 - h / 2, w, h)
        # La opacidad pulsa entre 145 y 255
        p.setOpacity((200 + 55 * math.sin(now * 4)) / 255)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(config.THEME["gold"]))
        p.drawRoundedRect(rect, 16 * s, 16 * s)
        p.setFont(font)
        p.setPen(QColor(DARK_TEXT))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, config.UNI_BADGE_TEXT)
        p.setOpacity(1.0)

    def draw_result(self, p: QPainter, img_w: int, img_h: int, s: float) -> None:
        """Tarjeta central con el resultado de la ronda, mientras dura la fase "result"."""
        st = self.uni_state
        t = config.THEME
        complete = len(st.collected) == len(self.uni_scorer.items)
        used = math.ceil(round(config.UNI_ROUND_S - st.time_left, 3))
        footer = f"Nueva ronda en {math.ceil(st.result_left)} s"
        rows = [
            ("¡COMPLETO!" if complete else "¡TIEMPO!", px_font(44 * s), t["gold"] if complete else t["text"], 64),
            (f"{st.score} de {st.max_score} pts · {st.level_text}", px_font(24 * s), t["text"], 40),
            (f"en {used} s · {footer}" if complete else footer, px_font(18 * s, bold=False), t["muted"], 30),
        ]
        w, h = 620 * s, (sum(row_h for *_, row_h in rows) + 36) * s
        rect = QRectF((img_w - w) / 2, img_h * 0.47 - h / 2, w, h)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 190))
        p.drawRoundedRect(rect, 16 * s, 16 * s)
        y = rect.y() + 18 * s
        for text, font, color, row_h in rows:
            p.setFont(font)
            p.setPen(QColor(color))
            p.drawText(QRectF(rect.x(), y, w, row_h * s), Qt.AlignmentFlag.AlignCenter, text)
            y += row_h * s

    def draw_floaters(self, p: QPainter, img_w: int, s: float, now: float) -> None:
        """Los "+X pts" suben 60·s px y se desvanecen en FLOAT_S segundos."""
        font = px_font(32 * s)
        fm = QFontMetrics(font)
        p.setFont(font)
        gold = QColor(config.THEME["gold"])
        for start, x, y, text in self.floaters:
            k = (now - start) / FLOAT_S
            if not 0 <= k < 1:
                continue
            tw = fm.horizontalAdvance(text)
            cx = min(max(x, tw / 2), img_w - tw / 2)
            # Arranca sobre la píldora de la caja; si la caja llega hasta el HUD, justo debajo de él
            base = max(y - 36 * s, (HUD_H + 40) * s) - 60 * s * k
            rect = QRectF(cx - tw, base - fm.height(), 2 * tw, fm.height())
            alpha = round(255 * (1 - k))
            p.setPen(QColor(0, 0, 0, alpha))
            p.drawText(rect.translated(2, 2), Qt.AlignmentFlag.AlignCenter, text)
            gold.setAlpha(alpha)
            p.setPen(gold)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def draw_low_light(self, p: QPainter, img_w: int, img_h: int) -> None:
        """Franja inferior amarilla con el aviso de poca luz."""
        s = img_h / 720
        rect = QRectF(0, img_h - 52 * s, img_w, 52 * s)
        p.fillRect(rect, QColor(LOW_LIGHT_BG))
        p.setFont(px_font(22 * s))
        p.setPen(QColor(DARK_TEXT))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, LOW_LIGHT_TEXT)

    def show_image(self, img: QImage, now: float) -> None:
        pix = QPixmap.fromImage(img).scaled(self.video.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
        # El destello va sobre el pixmap mostrado, nunca sobre last_image (no debe salir en el PNG)
        if self.flash_start is not None:
            k = (now - self.flash_start) / FLASH_S
            if k < 1:
                p = QPainter(pix)
                p.fillRect(pix.rect(), QColor(255, 255, 255, round(180 * (1 - k))))
                p.end()
            else:
                self.flash_start = None
        self.video.setPixmap(pix)

    # --- Acciones ---

    def set_mode(self, mode: str) -> None:
        entering_uni = mode == "uni" and self.mode != "uni"
        if mode != self.mode:
            self.invalidate_inference()
        self.mode = mode
        self.mode_buttons[mode].setChecked(True)
        uni = mode == "uni"
        # En modo Universitario solo se detectan objetos universitarios: los interruptores no aplican
        for cb in self.group_checks.values():
            cb.setEnabled(not uni)
            cb.setToolTip(UNI_ONLY_TIP if uni else "")
        self.uni_section.setVisible(uni)
        if entering_uni:
            self.reset_uni()
        self.update_panel()

    def toggle_mode(self) -> None:
        self.set_mode("uni" if self.mode == "general" else "general")

    def set_uni_round(self, enabled: bool) -> None:
        live = not enabled
        if live == self.live_scoring:
            return
        self.live_scoring = live
        self.uni_scorer = UniScorer(self.detector.available_keys, live=live)
        self.reset_uni()
        self.last_dets = []
        self.update_panel()
        self.statusBar().showMessage("Puntaje actual reiniciado al cambiar la ronda de 60 s", 3000)

    def on_conf_changed(self, value: int) -> None:
        if self.conf != value / 100:
            self.invalidate_inference()
        self.conf = value / 100
        self.conf_label.setText(f"{value}%")

    def capture(self) -> None:
        if self.last_image is None:
            self.statusBar().showMessage("No hay imagen para capturar", 3000)
            return
        config.CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = config.CAPTURES_DIR / f"{stamp}.png"
        n = 1
        while path.exists():  # dos capturas en el mismo segundo
            path = config.CAPTURES_DIR / f"{stamp}_{n}.png"
            n += 1
        if not self.last_image.save(str(path)):
            self.statusBar().showMessage(f"No se pudo guardar la captura en {path}", 3000)
            return
        self.captures += 1
        self.statusBar().showMessage(f"Captura guardada: {path.relative_to(config.ROOT)}", 3000)
        self.flash_start = time.monotonic()

    def reset_session(self) -> None:
        self.session_start = time.monotonic()
        self.appearances: dict[str, int] = {}
        self.best_score = 0
        self.captures = 0
        self.stats_tracker.reset()
        self.reset_uni()

    def reset_uni(self) -> None:
        self.invalidate_inference()
        self.uni_scorer.reset()
        self.uni_state = self.uni_scorer.update(set(), time.monotonic())
        self.score_disp = 0.0                    # valor animado que muestra la barra
        self.floaters: list[tuple[float, float, float, str]] = []  # (inicio, x, y, texto) en px del frame

    def reset_clicked(self) -> None:
        self.reset_session()
        self.update_panel()
        self.statusBar().showMessage("Estadísticas de la sesión reiniciadas", 3000)

    # --- Panel lateral ---

    def update_panel(self) -> None:
        now = time.monotonic()
        self.round_row.setVisible(not self.live_scoring)
        self.collected_title.setText("ÍTEMS VISIBLES" if self.live_scoring else "ÍTEMS GUARDADOS")
        self.uni_scoring_hint.setText(
            "Suma mientras los objetos estén visibles." if self.live_scoring else
            "Muestra los objetos uno por uno; los puntos se guardan durante la ronda.")
        self.fps_value.setText(f"{1 / self.fps_dt:.1f}" if self.cap is not None and self.fps_dt else "—")
        elapsed = int(now - self.session_start)
        self.time_value.setText(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
        self.mode_value.setText(MODE_NAMES[self.mode])
        if self.cap is None:
            self.light_value.setText("—")
        else:
            color, text = (LOW_LIGHT_BG, "Baja") if self.low_light else (config.COLORS["objetos"], "OK")
            self.light_value.setText(f'<span style="color:{color}">{text}</span>')

        uni = self.mode == "uni"
        if uni:
            # El reloj sigue avanzando sin cámara, sin simular detecciones ni reiniciar sus rachas.
            self.uni_state = self.uni_scorer.advance(now)
            st = self.uni_state
            self.score_value.setText(f"{st.score} / {st.max_score}")
            if not self.live_scoring:
                self.round_value.setText(clock(st.time_left) if st.phase == "running" else ROUND_STATUS[st.phase])
            self.best_value.setText(str(self.best_score))
            self.collected_label.setText(rows_html(
                [(config.COLORS["uni"], config.LABELS_ES[k], self.uni_scorer.items[k][0]) for k in st.collected]))

        on_screen = sorted(self.last_dets, key=lambda d: d.conf, reverse=True)[:8]
        self.on_screen_label.setText(rows_html(
            [(config.COLORS["uni" if uni else d.group], d.label, f"{d.conf:.0%}") for d in on_screen]))
        appearances = sorted(self.appearances.items(), key=lambda kv: kv[1], reverse=True)
        self.appear_label.setText(rows_html(
            [(config.COLORS[key_group(k)], key_label(k), str(n)) for k, n in appearances]))
        self.captures_value.setText(str(self.captures))

    # --- Verificación automática ---

    def schedule_autoshot(self, seconds: float) -> None:
        self.loop_start = time.monotonic()
        self.shot_frames = 0
        QTimer.singleShot(round(seconds * 1000), self.autoshot)

    def autoshot(self) -> None:
        span = time.monotonic() - self.loop_start - AUTOSHOT_WARMUP_S
        fps = self.shot_frames / span if span > 0 else 0.0
        self.update_panel()
        config.CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        path = config.CAPTURES_DIR / "autoshot.png"
        self.grab().save(str(path))
        print(f"AUTOSHOT fps={fps:.1f} frames={self.shot_frames} path={path.relative_to(config.ROOT)}",
              flush=True)
        QApplication.quit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Con la cámara activa el siguiente frame ya se escala al nuevo tamaño
        if self.cap is None and self.last_image is not None:
            self.show_image(self.last_image, time.monotonic())

    @Slot()
    def shutdown(self) -> None:
        """Cierre idempotente para la ventana y para QApplication.quit() (incluido --autoshot)."""
        if self._closing:
            return
        self._closing = True
        self.panel_timer.stop()
        self.close_camera()
        self.inference_thread.requestInterruption()
        self.inference_thread.quit()
        self.inference_thread.wait()
        self._inflight = None

    def closeEvent(self, event) -> None:
        self.shutdown()
        super().closeEvent(event)


def apply_theme(app: QApplication) -> None:
    """Tema oscuro base (Fusion + paleta + QSS) con los colores de config.THEME."""
    t = config.THEME
    app.setStyle("Fusion")
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSize(11)
    app.setFont(font)
    pal = QPalette()
    for role, color in ((QPalette.ColorRole.Window, t["bg"]), (QPalette.ColorRole.WindowText, t["text"]),
                        (QPalette.ColorRole.Base, t["panel"]), (QPalette.ColorRole.AlternateBase, t["bg"]),
                        (QPalette.ColorRole.Text, t["text"]), (QPalette.ColorRole.Button, "#242842"),
                        (QPalette.ColorRole.ButtonText, t["text"]), (QPalette.ColorRole.Highlight, t["accent"]),
                        (QPalette.ColorRole.HighlightedText, "#ffffff"),
                        (QPalette.ColorRole.ToolTipBase, t["panel"]), (QPalette.ColorRole.ToolTipText, t["text"]),
                        (QPalette.ColorRole.PlaceholderText, t["muted"])):
        pal.setColor(role, QColor(color))
    # Controles deshabilitados (interruptores en modo Universitario): texto e indicador apagados
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        pal.setColor(QPalette.ColorGroup.Disabled, role, QColor("#4a4f6e"))
    app.setPalette(pal)
    app.setStyleSheet(f"""
        QMainWindow, QWidget#central {{ background: {t['bg']}; }}
        QLabel#brand {{ color: {t['accent']}; font-size: 20pt; font-weight: bold; }}
        QLabel#muted {{ color: {t['muted']}; }}
        QLabel#value {{ font-size: 14pt; font-weight: bold; }}
        QLabel#panelTitle {{ color: {t['muted']}; font-size: 9pt; font-weight: bold; }}
        QLabel#video {{ background: #000000; border-radius: 12px; color: {t['muted']}; font-size: 16pt; }}
        QPushButton {{
            background: #242842; color: {t['text']}; border: 1px solid #2f3456;
            border-radius: 8px; padding: 6px 18px;
        }}
        QPushButton:hover {{ background: #2e3356; border-color: {t['accent']}; }}
        QPushButton:pressed {{ background: #1c2036; }}
        QPushButton:checked {{ background: {t['accent']}; border-color: {t['accent']}; color: #ffffff;
                               font-weight: bold; }}
        QPushButton:checked:hover {{ background: #6a9dff; border-color: #6a9dff; }}
        QPushButton#segLeft {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}
        QPushButton#segRight {{ border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; }}
        QComboBox {{ background: #242842; border: 1px solid #2f3456; border-radius: 8px; padding: 5px 10px; }}
        QComboBox:hover {{ border-color: {t['accent']}; }}
        QComboBox QAbstractItemView {{ background: {t['panel']}; border: 1px solid #2f3456;
                                       selection-background-color: {t['accent']}; }}
        QCheckBox {{ spacing: 8px; }}
        QCheckBox:hover {{ color: #ffffff; }}
        QSlider::groove:horizontal {{ height: 6px; background: #2b2f45; border-radius: 3px; }}
        QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 3px; }}
        QSlider::handle:horizontal {{
            background: #ffffff; border: 3px solid {t['accent']}; width: 12px; height: 12px;
            margin: -6px 0; border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{ background: {t['accent']}; border-color: #ffffff; }}
        QFrame#panel {{ background: {t['panel']}; border-radius: 12px; }}
        QToolTip {{ background: {t['panel']}; color: {t['text']}; border: 1px solid #2f3456; padding: 4px; }}
        QStatusBar {{ color: {t['muted']}; }}
    """)


def main() -> None:
    ap = argparse.ArgumentParser(description="VisionAI — detector de objetos en tiempo real")
    ap.add_argument("--camera", type=int, metavar="N", help="índice inicial de la cámara")
    ap.add_argument("--mode", choices=list(MODE_NAMES), default="general", help="modo inicial")
    ap.add_argument("--uni-round", action="store_true", help="usa la ronda acumulativa de 60 s en Universitario")
    ap.add_argument("--quality", choices=list(config.MODEL_PROFILES), default=config.DEFAULT_QUALITY,
                    help="accurate: YOLO26s 640, prioriza reconocimiento; detail: YOLOv8n 480; fast: YOLOv8n 320")
    ap.add_argument("--stationery-model", type=Path, metavar="DIR",
                    help="otro detector de útiles: directorio OpenVINO en CPU o pesos .pt en CUDA")
    ap.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto",
                    help="auto usa NVIDIA CUDA si está disponible; cpu conserva OpenVINO")
    ap.add_argument("--half", action="store_true", help="usa FP16 en CUDA para reducir el coste de inferencia")
    ap.add_argument("--resolution", choices=("640x480", "1280x720"),
                    help="resolución solicitada a la cámara; 720p limita esta cámara a unos 10 FPS")
    ap.add_argument("--autoshot", type=float, metavar="SEG",
                    help="a los SEG segundos guarda capturas/autoshot.png, imprime los FPS y sale")
    args = ap.parse_args()
    if args.stationery_model is not None and not args.stationery_model.exists():
        ap.error("--stationery-model no existe")

    config.MODEL_PATH, config.IMGSZ = config.MODEL_PROFILES[args.quality]
    if args.resolution:
        config.FRAME_W, config.FRAME_H = map(int, args.resolution.split("x"))

    app = QApplication(sys.argv[:1])
    apply_theme(app)
    stationery_model = args.stationery_model
    if stationery_model is None and config.STATIONERY_MODEL_PATH.is_dir():
        stationery_model = config.STATIONERY_MODEL_PATH
    detector = Detector(stationery_model, device=args.device, half=args.half)
    cameras = probe_cameras() if args.camera is None else []
    win = MainWindow(detector, cameras, args.camera, args.mode, live_scoring=not args.uni_round)
    win.show()
    if args.autoshot is not None:
        win.schedule_autoshot(args.autoshot)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
