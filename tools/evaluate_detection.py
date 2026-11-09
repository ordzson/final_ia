"""Evalúa cajas de 13 clases sobre el manifest COCO local; nunca descarga datasets.

Ejemplo: python tools/evaluate_detection.py --manifest .venv/candidates/coco_val/manifest.json
  --split validation --model .venv/candidates/exports/yolo11n_384_openvino_model
  --imgsz 384 --out .venv/candidates/reports/yolo11n_validation.json

--predictions permite evaluar JSON [{image_id, key, bbox:[x1,y1,x2,y2], score}]
sin cargar modelos. --alias "hardcover notebook=book" mapea solo nombres nuevos a
clases canónicas. No calcula mAP COCO ni evalúa rostros; es una muestra pequeña.
"""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ("person", "backpack", "handbag", "cell phone", "laptop", "book", "dining table",
           "chair", "bottle", "cup", "keyboard", "mouse", "scissors")


def box_iou(first, second):
    intersection = max(0.0, min(first[2], second[2]) - max(first[0], second[0])) * max(
        0.0, min(first[3], second[3]) - max(first[1], second[1]))
    a = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    b = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    return intersection / (a + b - intersection) if a + b - intersection > 0 else 0.0


def valid_box(box):
    return (len(box) == 4 and all(math.isfinite(float(v)) for v in box)
            and box[2] > box[0] and box[3] > box[1])


def parse_aliases(values):
    aliases = {}
    for value in values:
        if "=" not in value:
            raise ValueError("Cada alias debe tener formato nombre_nuevo=clase_canonica.")
        source, destination = (part.strip() for part in value.split("=", 1))
        if not source or destination not in TARGETS or (source in TARGETS and source != destination):
            raise ValueError(f"Alias no válido: {value}. No se reasignan clases canónicas.")
        if source in aliases and aliases[source] != destination:
            raise ValueError(f"Alias contradictorio: {source}")
        aliases[source] = destination
    return aliases


def match_image(annotations, predictions, confidence=0.35, threshold=0.5, aliases=None):
    """Matching por confianza, misma clase e IoU>=umbral, uno a uno; duplicados son FP."""
    aliases = aliases or {}
    if any(a.get("iscrowd", False) for a in annotations):
        raise ValueError("La muestra debe excluir imágenes con crowd de clases objetivo.")
    truth = [a for a in annotations if a["key"] in TARGETS]
    if any(not valid_box(a["bbox"]) for a in truth):
        raise ValueError("Caja GT inválida; se esperan coordenadas xyxy.")
    accepted = []
    for original in predictions:
        score = float(original["score"])
        if not math.isfinite(score) or not 0 <= score <= 1 or not valid_box(original["bbox"]):
            raise ValueError("Predicción inválida: caja xyxy o confianza fuera de [0,1].")
        key = aliases.get(original["key"], original["key"])
        if key in TARGETS and score >= confidence:
            accepted.append({**original, "key": key, "source_key": original["key"], "score": score})
    accepted.sort(key=lambda p: -p["score"])
    matched = set()
    counts = {key: Counter(tp=0, fp=0, fn=0, gt=0, predictions=0) for key in TARGETS}
    for annotation in truth:
        counts[annotation["key"]]["gt"] += 1
    results = []
    for prediction in accepted:
        candidates = [(box_iou(prediction["bbox"], a["bbox"]), index)
                      for index, a in enumerate(truth)
                      if index not in matched and a["key"] == prediction["key"]]
        overlap, index = max(candidates, default=(0.0, -1))
        hit = index >= 0 and overlap >= threshold
        counts[prediction["key"]]["predictions"] += 1
        counts[prediction["key"]]["tp" if hit else "fp"] += 1
        if hit:
            matched.add(index)
        results.append({**prediction, "status": "tp" if hit else "fp", "iou": overlap,
                        "matched_gt_index": index if hit else None})
    missing = [index for index in range(len(truth)) if index not in matched]
    for index in missing:
        counts[truth[index]["key"]]["fn"] += 1
    return counts, results, missing


def ratios(counts):
    tp, fp, fn = (counts.get(key, 0) for key in ("tp", "fp", "fn"))
    return {"precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def evaluate_records(records, predictions, confidence=0.35, threshold=0.5, aliases=None):
    grouped = {}
    ids = {record["id"] for record in records}
    if len(ids) != len(records) or not records:
        raise ValueError("Se requieren imágenes con ids únicos y un split no vacío.")
    for prediction in predictions:
        if prediction["image_id"] not in ids:
            raise ValueError(f"Predicción ajena al split: {prediction['image_id']}")
        grouped.setdefault(prediction["image_id"], []).append(prediction)
    totals = {key: Counter(tp=0, fp=0, fn=0, gt=0, predictions=0, images=0) for key in TARGETS}
    rows, negatives, negative_fp, fp_images = [], 0, 0, 0
    for record in records:
        counts, accepted, missing = match_image(record["annotations"], grouped.get(record["id"], []),
                                               confidence, threshold, aliases)
        for key, count in counts.items():
            totals[key].update(count)
            totals[key]["images"] += int(count["gt"] > 0)
        false = sum(count["fp"] for count in counts.values())
        negative = not any(a["key"] in TARGETS for a in record["annotations"])
        negatives += int(negative)
        negative_fp += int(negative and false > 0)
        fp_images += int(false > 0)
        rows.append({"id": record["id"], "file": record["file"], "negative": negative,
                     "annotations": record["annotations"], "predictions": accepted,
                     "unmatched_gt_indices": missing,
                     "counts": {key: dict(value) for key, value in counts.items()}})
    classes = {key: {**dict(count), **ratios(count), "covered": count["gt"] > 0}
               for key, count in totals.items()}
    supported = [key for key in TARGETS if totals[key]["gt"] > 0]
    aggregate = Counter()
    for count in totals.values():
        aggregate.update(count)
    return {"images": len(records), "confidence": confidence, "matching_iou": threshold,
            "classes": classes, "micro": {**dict(aggregate), "images": len(records), **ratios(aggregate)},
            "macro_f1_supported": (statistics.mean(classes[key]["f1"] for key in supported)
                                   if supported else None),
            "coverage": {"supported_classes": supported,
                         "missing_classes": [key for key in TARGETS if key not in supported]},
            "false_positive_images": fp_images,
            "fp_per_100_images": aggregate["fp"] * 100 / len(records),
            "negative_images": negatives, "negative_images_with_fp": negative_fp,
            "negative_fp_image_rate": negative_fp / negatives if negatives else None,
            "per_image": rows}


def infer(records, manifest_path, model_path, image_size, device, confidence, nms_iou):
    """Carga solo YOLO local. La latencia excluye carga de archivos, modelo y calentamiento."""
    import cv2
    import numpy as np
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(1)
    path = Path(model_path).resolve()
    if not path.exists():
        raise ValueError(f"No existe el modelo local: {path}")
    started = time.perf_counter()
    model = YOLO(str(path), task="detect")
    options = dict(imgsz=image_size, conf=confidence, iou=nms_iou, device=device,
                   rect=False, nms=None, verbose=False)
    model.predict(np.zeros((image_size, image_size, 3), dtype=np.uint8), **options)
    initialization = (time.perf_counter() - started) * 1000
    predictions, times = [], []
    for number, record in enumerate(records, 1):
        image_path = Path(record["file"])
        if not image_path.is_absolute():
            image_path = manifest_path.parent / image_path
        frame = cv2.imread(str(image_path))
        if frame is None or frame.shape[1::-1] != (record["width"], record["height"]):
            raise ValueError(f"Imagen ausente o tamaño distinto del manifest: {image_path}")
        before = time.perf_counter()
        result = model.predict(frame, **options)[0]
        times.append((time.perf_counter() - before) * 1000)
        for box, score, class_id in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist(),
                                        result.boxes.cls.cpu().tolist()):
            predictions.append({"image_id": record["id"], "key": result.names[int(class_id)],
                                "bbox": box, "score": score})
        print(f"Evaluadas {number}/{len(records)}", flush=True)
    ordered = sorted(times)
    names = model.names
    return predictions, {"model": str(path), "imgsz": image_size, "device": device,
                         "model_names": names, "torch_threads": 1, "nms_iou": nms_iou,
                         "rect": False, "nms": None,
                         "initialization_and_warmup_ms": initialization,
                         "latency_ms": {"mean": statistics.mean(times),
                                        "p50": statistics.median(times),
                                        "p95": ordered[max(0, math.ceil(0.95 * len(times)) - 1)]},
                         "images_per_second_inference_only": 1000 / statistics.mean(times)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--model", type=Path)
    source.add_argument("--predictions", type=Path)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--device", default="intel:CPU")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--iou", type=float, default=0.5, help="IoU de matching, independiente del NMS")
    parser.add_argument("--nms-iou", type=float, default=0.7)
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 0 <= args.conf <= 1 or not 0 < args.iou <= 1 or not 0 < args.nms_iou <= 1 or args.imgsz <= 0:
        parser.error("Confianza/IoU/tamaño no válidos.")
    args.manifest = args.manifest.resolve()
    if args.out.resolve() == args.manifest:
        parser.error("El reporte no puede sobrescribir el manifest.")
    aliases = parse_aliases(args.alias)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    records = [record for record in manifest["images"] if record["split"] == args.split]
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".venv/ultralytics"))
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv/matplotlib"))
    if args.predictions:
        predictions = json.loads(args.predictions.read_text(encoding="utf-8-sig"))
        run = {"prediction_source": str(args.predictions.resolve()), "latency_ms": None}
    else:
        predictions, run = infer(records, args.manifest, args.model, args.imgsz, args.device,
                                 args.conf, args.nms_iou)
    report = evaluate_records(records, predictions, args.conf, args.iou, aliases)
    report.update(split=args.split, manifest=str(args.manifest), run=run, aliases=aliases,
                  dataset_sources={key: manifest.get(key) for key in ("annotations_source", "images_source")},
                  limitations="Muestra pequeña COCO val2017, no mAP oficial ni prueba de rostros. "
                              "Mantener test separado de selección/ajustes; latencia excluye GUI/cámara.")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Clase          GT  TP  FP  FN  Precision Recall F1")
    for key, row in report["classes"].items():
        values = ["-" if row[k] is None else f"{row[k]:.3f}" for k in ("precision", "recall", "f1")]
        print(f"{key:14} {row['gt']:3} {row['tp']:3} {row['fp']:3} {row['fn']:3}  " + " ".join(values))
    print(json.dumps({key: report[key] for key in ("macro_f1_supported", "false_positive_images",
                                                 "negative_images", "negative_images_with_fp", "coverage")}))
    print(f"Reporte: {args.out.resolve()}")


if __name__ == "__main__":
    main()
