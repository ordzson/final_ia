"""Selección CPU/CUDA y pesos; no requiere GPU, cámara ni carga de modelos."""
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from detector import Detector, inference_backend


class BackendTests(unittest.TestCase):
    def test_auto_without_cuda(self):
        with patch("detector.torch.cuda.is_available", return_value=False):
            self.assertEqual(inference_backend("auto"), "cpu")
            with self.assertRaisesRegex(RuntimeError, "CUDA no está disponible"):
                inference_backend("cuda")

    def test_force_cpu_with_gpu(self):
        with patch("detector.torch.cuda.is_available", return_value=True):
            self.assertEqual(inference_backend("cpu"), "cpu")
            self.assertEqual(inference_backend("auto"), "cuda")

    def test_cuda_loads_native_weights_for_both_models(self):
        for quality in config.MODEL_PROFILES:
            with self.subTest(quality=quality), \
                 patch.object(config, "MODEL_PATH", config.MODEL_PROFILES[quality][0]), \
                 patch.object(config, "IMGSZ", config.MODEL_PROFILES[quality][1]), \
                 patch("detector.torch.cuda.is_available", return_value=True), \
                 patch("detector.YOLO") as yolo, \
                 patch("detector.vision.FaceDetector.create_from_options"):
                coco = MagicMock(names={0: "person"})
                stationery = MagicMock(names={0: "pencil", 1: "notebook", 2: "pen"})
                yolo.side_effect = [coco, stationery]
                detector = Detector(config.STATIONERY_MODEL_PATH, half=True)
                expected = "yolo26s.pt" if quality == "accurate" else "yolov8n.pt"
                self.assertEqual(Path(yolo.call_args_list[0].args[0]).name, expected)
                self.assertEqual(Path(yolo.call_args_list[1].args[0]).name, "stationery.pt")
                self.assertEqual(detector._predict_options, {"device": 0, "half": True})
                self.assertEqual(coco.predict.call_args.kwargs["device"], 0)
                self.assertEqual(stationery.predict.call_args.kwargs["device"], 0)
                self.assertIn("notebook", detector.available_keys)

    def test_cpu_preserves_openvino(self):
        with patch("detector.YOLO") as yolo, \
             patch("detector.vision.FaceDetector.create_from_options"):
            yolo.return_value.names = {0: "person"}
            detector = Detector(device="cpu")
            self.assertEqual(detector.device, "cpu")
            self.assertEqual(Path(yolo.call_args.args[0]), config.MODEL_PATH)

    def test_cuda_rejects_custom_openvino(self):
        with patch("detector.torch.cuda.is_available", return_value=True):
            with self.assertRaisesRegex(ValueError, "pesos .pt"):
                Detector(Path("custom_openvino_model"), device="cuda")


if __name__ == "__main__":
    unittest.main()
