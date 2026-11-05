"""Constantes del proyecto VisionAI. Única fuente de verdad para clases, puntos y umbrales."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- Modelos ---
MODEL_PATH = ROOT / "models" / "yolov8n_openvino_model"
FACE_MODEL_PATH = ROOT / "models" / "blaze_face_short_range.tflite"
IMGSZ = 480               # debe coincidir con el imgsz usado al exportar a OpenVINO
CONF_DEFAULT = 0.35
FACE_MIN_CONF = 0.5

# --- Cámara ---
CAMERA_INDEX_DEFAULT = 2  # cámara USB externa; si no está conectada, la app abre la primera que encuentre
FRAME_W, FRAME_H = 1280, 720
MIRROR = True

# --- Clases: clave = nombre EXACTO en model.names → etiqueta en español ---
# Las claves que no existan en el modelo se ignoran solas (Detector.available_keys).
LABELS_ES = {
    "person": "Persona",
    "backpack": "Mochila",
    "handbag": "Bolso",
    "cell phone": "Celular",
    "laptop": "Laptop",
    "book": "Libro / Cuaderno",  # COCO no tiene cuaderno: el modelo lo detecta como book
    "dining table": "Mesa / Escritorio",
    "chair": "Silla",
    "bottle": "Botella",
    "cup": "Taza",
    "keyboard": "Teclado",
    "mouse": "Mouse",
    "scissors": "Tijeras",
    # Solo existen en Plan B (las claves deben ser idénticas a los textos usados en set_classes):
    "spiral notebook": "Cuaderno",
    "pen": "Lapicero",
    "desk": "Escritorio",
}
FACE_KEY = "face"
FACE_LABEL = "Rostro"
PERSON_KEYS = {"person"}  # grupo "personas"; el resto de LABELS_ES pertenece al grupo "objetos"

# --- Modo universitario: clave → (título de nivel, puntos). El orden define el orden de los chips. ---
UNI_ITEMS = {
    "backpack": ("Acceso a campus", 10),
    "book": ("Estudiante dedicado", 20),
    "laptop": ("Listo para el aula", 25),
    "cell phone": ("Siempre conectado", 5),
}
UNI_THRESHOLD = 50
NO_ITEMS_TEXT = "Aún no estás listo..."
UNI_BADGE_TEXT = "NIVEL UNIVERSITARIO"
UNI_ROUND_S = 60          # ronda: segundos para mostrar todos los objetos; arranca con el primero que se detecta
UNI_RESULT_S = 5          # segundos que se muestra el resultado antes de volver a 0

# --- Antiparpadeo ---
PRESENCE_ENTER_S = 0.3    # tiempo visible de forma estable para contar como presente
PRESENCE_HOLD_S = 0.7     # tiempo que sigue contando como presente tras dejar de verse

# --- Poca luz ---
LOW_LIGHT_MEAN = 60       # brillo medio en gris (0-255) por debajo del cual se avisa

# --- Colores (hex) ---
COLORS = {"personas": "#4f8cff", "rostros": "#ff5fa2", "objetos": "#3ddc97", "uni": "#ffc94d"}
THEME = {
    "bg": "#0f1220", "panel": "#171a2b", "accent": "#4f8cff",
    "gold": "#ffc94d", "text": "#e8eaf6", "muted": "#8a90b3",
}

CAPTURES_DIR = ROOT / "capturas"
