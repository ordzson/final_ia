"""Ejecuta Detector sobre una imagen o un frame de cámara y guarda el resultado dibujado."""
import argparse
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402
from detector import Detector  # noqa: E402

OUT = ROOT / "tools" / "out"


def hex_to_bgr(color: str) -> tuple[int, int, int]:
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return b, g, r


def grab_frame(camera: int):
    cap = cv2.VideoCapture(camera, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_H)
    frame = None
    # Las primeras lecturas pueden salir oscuras mientras la cámara ajusta la exposición
    for _ in range(15):
        ok, frame = cap.read()
        if not ok:
            sys.exit(f"La cámara {camera} no entregó imagen")
    cap.release()
    return cv2.flip(frame, 1) if config.MIRROR else frame


def main() -> None:
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--image")
    src.add_argument("--camera", type=int)
    args = ap.parse_args()

    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            sys.exit(f"No se pudo leer {args.image}")
    else:
        frame = grab_frame(args.camera)

    detector = Detector()
    t0 = time.perf_counter()
    dets = detector.detect(frame, config.CONF_DEFAULT, {"objetos", "personas", "rostros"})
    ms = (time.perf_counter() - t0) * 1000

    for d in dets:
        print(d)
    h, w = frame.shape[:2]
    print(f"{len(dets)} detecciones en {ms:.1f} ms (frame {w}x{h})")

    for d in dets:
        color = hex_to_bgr(config.COLORS[d.group])
        x1, y1, x2, y2 = d.box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{d.key} {d.conf:.2f}", (x1, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "detect_result.jpg"
    cv2.imwrite(str(path), frame)
    print(f"-> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
