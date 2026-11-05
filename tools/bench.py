"""Mide el tiempo de inferencia de YOLO y de MediaPipe (rostros) sobre frames reales de la cámara."""
import argparse
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
FACE_MODEL = ROOT / "models" / "blaze_face_short_range.tflite"
WARMUP = 5


def grab_frames(camera: int, n: int) -> list:
    cap = cv2.VideoCapture(camera, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    frames = []
    while len(frames) < n:
        ok, frame = cap.read()
        if not ok:
            sys.exit(f"La cámara {camera} no entregó imagen")
        frames.append(cv2.flip(frame, 1))
    cap.release()
    return frames


def report(name: str, times: list[float]) -> None:
    ms = sum(times) / len(times) * 1000
    print(f"{name}: {ms:.1f} ms promedio ({1000 / ms:.1f} FPS)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--frames", type=int, default=100)
    ap.add_argument("--model", required=True)
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()

    frames = grab_frames(args.camera, args.frames)
    h, w = frames[0].shape[:2]
    print(f"{len(frames)} frames de {w}x{h}, modelo={args.model}, imgsz={args.imgsz}")

    model = YOLO(args.model, task="detect")
    for f in frames[:WARMUP]:
        model.predict(f, imgsz=args.imgsz, verbose=False)
    times = []
    for f in frames:
        t0 = time.perf_counter()
        model.predict(f, imgsz=args.imgsz, verbose=False)
        times.append(time.perf_counter() - t0)
    report(f"YOLO {Path(args.model).name}", times)

    options = vision.FaceDetectorOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
        running_mode=vision.RunningMode.VIDEO,
    )
    face = vision.FaceDetector.create_from_options(options)
    ts = 0
    times = []
    for i, f in enumerate(frames):
        rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        ts += 33
        t0 = time.perf_counter()
        face.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
        if i >= WARMUP:
            times.append(time.perf_counter() - t0)
    face.close()
    report("Rostros MediaPipe", times)


if __name__ == "__main__":
    main()
