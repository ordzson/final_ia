"""Constantes del proyecto VisionAI. Única fuente de verdad para clases, puntos y umbrales."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- Modelos ---
#esta variable define la ruta de los modelos de detección de objetos y rostros, 
# así como los pesos del modelo de útiles escolares.
MODEL_PROFILES = {
    "accurate": (ROOT / "models" / "yolo26s_640_openvino_model", 640),
    "detail": (ROOT / "models" / "yolov8n_openvino_model", 480),
    #esto es útil para pruebas rápidas en CPU, pero no detecta objetos pequeños como lápices y cuadernos
    "fast": (ROOT / "models" / "yolov8n_320_openvino_model", 320),
}
STATIONERY_MODEL_PATH = ROOT / "models" / "stationery_openvino_model"
# Con el detector de útiles, detail equilibra el coste de las dos inferencias.
DEFAULT_QUALITY = "accurate" if sys.platform == "win32" and not STATIONERY_MODEL_PATH.is_dir() else "detail"
MODEL_PATH, IMGSZ = MODEL_PROFILES[DEFAULT_QUALITY]
STATIONERY_IMGSZ = 640
STATIONERY_KEYS = frozenset({"pencil", "notebook"})
FACE_MODEL_PATH = ROOT / "models" / "blaze_face_short_range.tflite"
# --- Inferencia ---
#el 0.35 es un buen compromiso entre precisión y detección de objetos pequeños, como lápices y cuadernos

CONF_DEFAULT = 0.35
FACE_MIN_CONF = 0.5

# --- Cámara ---
#esto es útil para pruebas rápidas en CPU, pero no detecta objetos pequeños como lápices y cuadernos
CAMERA_INDEX_DEFAULT = 1 if sys.platform == "win32" else 2  # integrada verificada en esta laptop Windows; USB en Linux
FRAME_W, FRAME_H = (640, 480) if sys.platform == "win32" else (1280, 720)
MIRROR = True

# --- Clases: clave = nombre EXACTO en model.names → etiqueta en español ---
# Las claves que no existan en el modelo se ignoran solas (Detector.available_keys).
#hi
LABELS_ES = {
    "person": "Persona",
    "backpack": "Mochila",
    "handbag": "Bolso",
    "cell phone": "Celular",
    "laptop": "Laptop",
    "book": "Libro",
    "dining table": "Mesa / Escritorio",
    "chair": "Silla",
    "bottle": "Botella",
    "cup": "Taza",
    "keyboard": "Teclado",
    "mouse": "Mouse",
    "scissors": "Tijeras",
    "pencil": "Lápiz",
    "notebook": "Cuaderno",
    # Solo existen en Plan B (las claves deben ser idénticas a los textos usados en set_classes):
    "spiral notebook": "Cuaderno",
    "pen": "Lapicero",
    "desk": "Escritorio",
}
#esto es útil para agrupar las clases en la interfaz de usuario: "personas" = persona, "rostros" = rostro, "objetos" = resto
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
UNI_LIVE_ITEMS = {
#esto es lo que se muestra en la parte superior de la ventana cuando se alcanza el umbral de nivel universitario
    "backpack": ("Acceso a campus", 10),
    "notebook": ("Alumno responsable", 15),
    "book": ("Estudiante dedicado", 20),
    "laptop": ("Listo para el aula", 25),
    "pen": ("Siempre preparado", 5),
}
UNI_THRESHOLD = 50
NO_ITEMS_TEXT = "Aún no estás listo..."
#esto es lo que se muestra en la parte superior de la ventana cuando se alcanza el umbral de nivel universitario
UNI_BADGE_TEXT = "NIVEL UNIVERSITARIO"
UNI_ROUND_S = 60          # ronda: segundos para mostrar todos los objetos; arranca con el primero que se detecta
UNI_RESULT_S = 5          # segundos que se muestra el resultado antes de volver a 0

# --- Antiparpadeo ---
#se puede usar para contar objetos que entran y salen de la vista, como lápices y cuadernos, 
# sin que el parpadeo de la detección afecte el puntaje.
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
