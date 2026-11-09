"""Contratos de matching; no importa modelos, Qt ni cámara."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from evaluate_detection import evaluate_records, match_image, parse_aliases


def prediction(key="book", box=None, score=0.8):
    return {"key": key, "bbox": box or [0, 0, 10, 10], "score": score}


def main():
    truth = [{"key": "book", "bbox": [0, 0, 10, 10], "iscrowd": False}]
    counts, _, missing = match_image(truth, [prediction(), prediction(score=0.7)])
    assert counts["book"]["tp"] == 1 and counts["book"]["fp"] == 1 and missing == []
    counts, _, _ = match_image(truth, [prediction("laptop")])
    assert counts["laptop"]["fp"] == 1 and counts["book"]["fn"] == 1
    counts, _, _ = match_image([], [prediction()])
    assert counts["book"]["fp"] == 1
    counts, _, _ = match_image(truth, [prediction(box=[0, 0, 5, 10], score=0.35)])
    assert counts["book"]["tp"] == 1  # IoU exactamente .5 y confianza exactamente .35.
    counts, _, _ = match_image(truth, [prediction(score=0.349)])
    assert counts["book"]["tp"] == 0 and counts["book"]["fn"] == 1
    counts, _, _ = match_image(truth, [prediction(box=[0, 0, 4.99, 10])])
    assert counts["book"]["tp"] == 0 and counts["book"]["fp"] == 1
    aliases = parse_aliases(["hardcover notebook=book"])
    counts, _, _ = match_image(truth, [prediction("hardcover notebook")], aliases=aliases)
    assert counts["book"]["tp"] == 1
    try:
        parse_aliases(["laptop=book"])
    except ValueError:
        pass
    else:
        raise AssertionError("No se debe reasignar una clase canónica.")
    records = [{"id": 1, "file": "one.jpg", "annotations": truth},
               {"id": 2, "file": "negative.jpg", "annotations": []}]
    report = evaluate_records(records, [{"image_id": 1, **prediction()},
                                          {"image_id": 2, **prediction("laptop")}])
    assert report["classes"]["book"]["f1"] == 1
    assert report["classes"]["scissors"]["recall"] is None
    assert "scissors" in report["coverage"]["missing_classes"]
    assert report["negative_images"] == report["negative_images_with_fp"] == 1
    assert report["false_positive_images"] == 1 and report["fp_per_100_images"] == 50
    assert report["macro_f1_supported"] == 1
    assert report["images"] == report["micro"]["images"] == 2
    print("OK: matching uno a uno, duplicados, clases, negativos, fronteras, alias y cobertura.")


if __name__ == "__main__":
    main()
