"""Observa la app real durante diez minutos y la deja abierta al terminar.

Ejemplo: .venv\\Scripts\\python.exe tools\\verify_live.py --camera 1 --seconds 600
La evidencia y las capturas del usuario se guardan dentro de .venv, fuera de Git.
"""
import argparse
import faulthandler
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
WARMUP_S, WINDOW_S, SAMPLE_S = 2.0, 30.0, 10.0


class Verification:
    def __init__(self, output: Path, seconds: float, metadata: dict) -> None:
        self.output, self.seconds = output, seconds
        self.metadata, self.resolution_observed = metadata, None
        self.evidence = output.parent / f"{output.stem}_evidence_{time.time_ns()}"
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.log = output.with_suffix(".jsonl").open("w", encoding="utf-8", buffering=1)
        self.win = self.timer = self.process = None
        self.start = self.last_account = time.monotonic()
        self.mode, self.status, self.active = "general", "starting", True
        self.previous, self.windows, self.errors, self.samples = {}, {}, [], []
        self.events = self.rounds = self.max_score = self.completed = self.inferred = 0
        self.badge_seen = self.complete_seen = False
        self.next_sample, self.peak_rss = 0.0, 0
        self.write_summary()

    def emit(self, event: str, **fields) -> None:
        self.events += 1
        self.log.write(json.dumps({"event": event, "elapsed_s": round(time.monotonic() - self.start, 3),
                                   **fields}, ensure_ascii=False) + "\n")

    def state(self) -> dict:
        if self.win is None:
            return {}
        w, s = self.win, self.win.uni_state
        return {"mode": w.mode, "score": s.score, "phase": s.phase, "collected": list(s.collected),
                "present": list(s.present), "badge": s.badge, "max_score": s.max_score,
                "time_left": round(s.time_left, 2), "low_light": w.low_light,
                "camera_open": w.cap is not None, "camera": w.camera_idx, "captures": w.captures,
                "inference_error": w._inference_error,
                "inference_error_message": w.statusBar().currentMessage() if w._inference_error else None,
                "conf": w.conf, "groups": {k: cb.isChecked() for k, cb in w.group_checks.items()},
                "session_start": w.session_start}

    def account(self, now: float) -> None:
        end = min(now - self.start, self.seconds)
        begin = max(self.last_account - self.start, WARMUP_S)
        while begin < end:
            index = int((begin - WARMUP_S) / WINDOW_S)
            stop = min(end, WARMUP_S + (index + 1) * WINDOW_S)
            bucket = self.windows.setdefault((index, self.mode), {"seconds": 0.0, "frames": 0,
                                                                 "inference_frames": 0})
            bucket["seconds"] += stop - begin
            begin = stop
        self.last_account = now
        if self.win is not None:
            self.mode = self.win.mode

    def detected(self, groups: set[str]) -> None:
        if not self.active or self.win is None:
            return
        now = time.monotonic()
        self.account(now)
        elapsed = now - self.start
        if WARMUP_S <= elapsed < self.seconds:
            index = int((elapsed - WARMUP_S) / WINDOW_S)
            bucket = self.windows.setdefault((index, self.mode), {"seconds": 0.0, "frames": 0,
                                                                 "inference_frames": 0})
            bucket["frames"] += 1
            self.completed += 1
            if groups:  # Desactivar todos los grupos no equivale a ejecutar inferencia.
                bucket["inference_frames"] += 1
                self.inferred += 1

    def observe(self) -> None:
        if not self.active:
            return
        now, current = time.monotonic(), self.state()
        self.account(now)
        if current.get("inference_error") and not self.previous.get("inference_error"):
            message = current["inference_error_message"] or "Error de deteccion en el hilo de inferencia."
            self.errors.append(message)
            self.emit("inference_error", message=message, state=current)
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
            self.previous = current
            self.finish("error")
            return
        watched = ("mode", "score", "phase", "collected", "badge", "low_light", "camera_open",
                   "camera", "captures", "conf", "groups", "session_start", "inference_error")
        changed = [k for k in watched if current.get(k) != self.previous.get(k)]
        if changed:
            if current["mode"] == "uni":
                if self.previous.get("phase") == "waiting" and current["phase"] != "waiting":
                    self.rounds += 1
                self.max_score = max(self.max_score, current["score"])
                self.badge_seen |= current["badge"]
                self.complete_seen |= (current["phase"] == "result" and current["max_score"] > 0
                                       and current["score"] == current["max_score"])
            capture = ("mode" in changed or "low_light" in changed
                       or current["score"] > self.previous.get("score", 0)
                       or ("badge" in changed and current["badge"])
                       or ("phase" in changed and current["phase"] == "result"))
            path = None
            if capture:
                target = self.evidence / f"{self.events:05d}_{current['mode']}_{current['score']}pts.png"
                if self.win.grab().save(str(target)):
                    path = str(target)
            self.emit("state_change", changed=changed, state=current, round=self.rounds, evidence=path,
                      detections=[{"key": d.key, "conf": round(d.conf, 4)} for d in self.win.last_dets])
        self.previous = current
        if now - self.start >= self.next_sample:
            sample = {"elapsed_s": round(now - self.start, 3), "state": current}
            if self.process is not None:
                sample.update(rss_mb=round(self.process.memory_info().rss / 2**20, 2),
                              cpu_percent=self.process.cpu_percent())
                self.peak_rss = max(self.peak_rss, sample["rss_mb"])
            self.samples.append(sample)
            self.emit("sample", **sample)
            self.next_sample = now - self.start + SAMPLE_S
            self.write_summary()
        if now - self.start >= self.seconds:
            self.finish("complete")

    def write_summary(self) -> None:
        windows = []
        for (index, mode), data in sorted(self.windows.items()):
            span = data["seconds"]
            windows.append({"start_s": WARMUP_S + index * WINDOW_S, "mode": mode, **data,
                            "fps_completed": round(data["frames"] / span, 3) if span else None,
                            "fps_inference": round(data["inference_frames"] / span, 3) if span else None})
        result = {**self.metadata, "resolution_observed": self.resolution_observed,
                  "status": self.status, "requested_seconds": self.seconds,
                  "elapsed_s": round(min(time.monotonic() - self.start, self.seconds), 3),
                  "evidence_dir": str(self.evidence), "events_file": str(self.output.with_suffix(".jsonl")),
                  "warmup_seconds": WARMUP_S, "completed_frames": self.completed,
                  "inference_calls": self.inferred, "windows": windows, "samples": self.samples,
                  "rounds_started": self.rounds, "max_live_score": self.max_score,
                  "badge_observed": self.badge_seen, "complete_observed": self.complete_seen,
                  "peak_rss_mb": self.peak_rss, "errors": self.errors,
                  "notes": "FPS de resultados nuevos aceptados y dibujados; sin grupos activos no cuentan como inferencia. "
                           "CPU del proceso puede superar 100%. El checklist manual requiere confirmacion del usuario."}
        temporary = self.output.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.output)

    def finish(self, reason: str) -> None:
        if self.active:
            if reason == "complete" and self.errors:
                reason = "error"
            self.account(time.monotonic())
            self.active, self.status = False, reason
            if self.timer is not None:
                self.timer.stop()
            self.emit("evaluation_finished", status=reason)
            self.write_summary()
            print(f"LIVE_VERIFY_COMPLETE status={reason} path={self.output}", flush=True)

    def exception(self, kind, value, tb) -> None:
        details = "".join(traceback.format_exception(kind, value, tb))
        sys.stderr.write(details)
        sys.stderr.flush()
        self.errors.append(details)
        self.emit("uncaught_exception", traceback=details)
        self.finish("error")
        self.write_summary()


class StderrTee:
    def __init__(self, original, stream) -> None:
        self.original, self.stream = original, stream

    def write(self, text):
        self.stream.write(text)
        return self.original.write(text)

    def flush(self):
        self.stream.flush()
        self.original.flush()

    def __getattr__(self, name):
        return getattr(self.original, name)


def main() -> int:
    import config

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=600)
    parser.add_argument("--quality", choices=list(config.MODEL_PROFILES), default=config.DEFAULT_QUALITY)
    parser.add_argument("--resolution", choices=("640x480", "1280x720"),
                        help="resolucion solicitada a la camara; por defecto usa config")
    parser.add_argument("--out", type=Path, default=ROOT / ".venv/verification/live_run.json")
    args = parser.parse_args()
    output = args.out.resolve()
    if not output.is_relative_to((ROOT / ".venv").resolve()):
        parser.error("--out debe quedar dentro de .venv para mantener la evidencia fuera de Git.")
    if not math.isfinite(args.seconds) or args.seconds <= WARMUP_S:
        parser.error("--seconds debe ser un numero finito mayor de 2.")
    config.MODEL_PATH, config.IMGSZ = config.MODEL_PROFILES[args.quality]
    if args.resolution is not None:
        config.FRAME_W, config.FRAME_H = map(int, args.resolution.split("x"))
    metadata = {"quality": args.quality, "inference_size": config.IMGSZ,
                "resolution": f"{config.FRAME_W}x{config.FRAME_H}", "model_path": str(config.MODEL_PATH)}
    output.parent.mkdir(parents=True, exist_ok=True)
    for variable, folder in (("YOLO_CONFIG_DIR", "ultralytics"), ("MPLCONFIGDIR", "matplotlib")):
        cache = output.parent / "runtime" / folder
        cache.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(cache)
    verify = Verification(output, args.seconds, metadata)
    errors = output.with_suffix(".stderr.log").open("w", encoding="utf-8", buffering=1)
    sys.stderr = StderrTee(sys.stderr, errors)
    sys.excepthook = verify.exception
    faulthandler.enable(file=errors)
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    import app as vision_app
    from detector import Detector

    try:
        import psutil
        verify.process = psutil.Process()
    except ImportError:
        pass
    config.CAPTURES_DIR = verify.evidence / "user_captures"  # Solo cambia el destino de evidencia.
    application = QApplication(sys.argv[:1])
    vision_app.apply_theme(application)
    stationery = config.STATIONERY_MODEL_PATH
    detector = Detector(stationery if stationery.is_dir() else None)

    def observed_frame(groups, size):
        if verify.active:
            verify.resolution_observed = f"{size[0]}x{size[1]}"
        verify.detected(groups)

    win = vision_app.MainWindow(detector, [], args.camera, "general", live_scoring=True)
    verify.win = win
    win.frame_processed.connect(observed_frame)
    verify.start = verify.last_account = time.monotonic()
    verify.status = "running"
    verify.timer = QTimer(win)
    verify.timer.setInterval(100)
    verify.timer.timeout.connect(verify.observe)
    application.aboutToQuit.connect(lambda: verify.finish("closed_early"))
    win.show()
    if verify.process is not None:
        verify.process.cpu_percent()
    verify.emit("started", camera=args.camera, requested_seconds=args.seconds, **metadata)
    verify.observe()
    verify.timer.start()
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
