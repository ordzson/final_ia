"""Detección en vivo sin ventana: registra por segundo las clases vistas y guarda imágenes cada 2 s."""
import argparse
import time
from collections import defaultdict
from pathlib import Path

import cv2
from ultralytics import YOLO

OUT = Path(__file__).resolve().parent / "out"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--conf", type=float, default=0.25)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    name = Path(args.model).name.removesuffix("_openvino_model").removesuffix(".pt")
    log = open(OUT / f"live_{name}.txt", "w")

    model = YOLO(args.model, task="detect")
    cap = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    infer_times = []
    seconds_seen = defaultdict(set)  # clase -> segundos en que apareció
    best = {}                        # clase -> mejor confianza del segundo actual
    start = time.monotonic()
    current_sec = 0
    shot = 0
    next_shot = 0.0
    while (elapsed := time.monotonic() - start) < args.seconds:
        ok, frame = cap.read()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)
        t0 = time.perf_counter()
        r = model.predict(frame, imgsz=args.imgsz, conf=args.conf, verbose=False)[0]
        infer_times.append(time.perf_counter() - t0)

        sec = int(elapsed)
        if sec != current_sec:
            line = ", ".join(f"{k} {v:.2f}" for k, v in sorted(best.items(), key=lambda kv: -kv[1]))
            log.write(f"t={current_sec:02d}s  {line or '-'}\n")
            log.flush()
            best = {}
            current_sec = sec
        for c, p in zip(r.boxes.cls.cpu().numpy().astype(int), r.boxes.conf.cpu().numpy()):
            k = r.names[c]
            best[k] = max(best.get(k, 0.0), float(p))
            seconds_seen[k].add(sec)

        if elapsed >= next_shot:
            cv2.imwrite(str(OUT / f"live_{name}_{shot:02d}.jpg"), r.plot())
            shot += 1
            next_shot += 2.0

    line = ", ".join(f"{k} {v:.2f}" for k, v in sorted(best.items(), key=lambda kv: -kv[1]))
    log.write(f"t={current_sec:02d}s  {line or '-'}\n")
    cap.release()

    ms = sum(infer_times) / max(len(infer_times), 1) * 1000
    summary = [f"inferencia promedio: {ms:.1f} ms ({len(infer_times)} frames)"]
    for k, secs in sorted(seconds_seen.items(), key=lambda kv: -len(kv[1])):
        summary.append(f"  {k}: {len(secs)} s  {sorted(secs)}")
    log.write("\n" + "\n".join(summary) + "\n")
    log.close()
    print("\n".join(summary))


if __name__ == "__main__":
    main()
