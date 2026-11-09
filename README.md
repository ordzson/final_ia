# VisionAI — Detector de Objetos en Tiempo Real

Aplicación de escritorio que abre la cámara, detecta objetos en vivo y dibuja sobre el video una caja, la etiqueta en español y el porcentaje de confianza de cada detección.

- **Objetos:** YOLOv8n (preentrenado en COCO), acelerado en CPU con OpenVINO.
- **Rostros:** MediaPipe BlazeFace.
- **Interfaz:** PySide6 (Qt 6).

Tiene dos modos:

- **General:** personas, rostros, celulares, laptops, mochilas, libros, mesas y otros objetos comunes.
- **Listo para la Universidad:** en una ronda de 1 minuto, suma puntos por cada objeto universitario que se muestra frente a la cámara.

---

## 1. Requisitos

- Windows con PowerShell, o Linux con sesión X11.
- Python 3.12 de 64 bits (`python.exe --version` en Windows, `python3 --version` en Linux).
- Una cámara web. Sirve la integrada o una USB.
- Conexión a internet para la instalación. Se descarga de PyPI, `download.pytorch.org`, GitHub y `storage.googleapis.com`.
- **Solo Linux:** el paquete del sistema `libxcb-cursor0`. Sin él, Qt no puede abrir la ventana:

  ```bash
  sudo apt install libxcb-cursor0
  ```

No hace falta GPU: todo corre en la CPU.

## 2. Instalación

### Windows (PowerShell)

Abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe app.py --camera 1
```

El comando permite ejecutar el instalador cuando PowerShell tiene la política `Restricted`. `-ExecutionPolicy Bypass` se aplica solo a ese proceso; no cambia la política del sistema.

En este equipo la cámara integrada quedó en el **índice 1** (`--camera 1`); puede cambiar en otros equipos, así que usa el selector de cámara de la app si hace falta. El instalador crea `.venv` con `python.exe` (Python 3.12 de 64 bits), instala PyTorch para CPU y las dependencias, y conserva solo `opencv-contrib-python-headless`. No necesitas activar el entorno virtual ni permisos de administrador. Si Python está en otra ruta, usa `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -PythonExe "C:\ruta\a\Python312\python.exe"`.

Cuando existe `requirements.windows.lock.txt`, el instalador usa sus versiones verificadas y el índice de PyTorch CPU. Si falta, instala las dependencias de `requirements.txt`. El archivo `requirements.lock.txt` corresponde a Linux y se conserva por separado.

Esta copia ya incluye los modelos de `models/`. Si falta alguno, los comandos de descarga y exportación para Windows son:

```powershell
New-Item -ItemType Directory -Path models -Force | Out-Null
Push-Location models
try {
    ..\.venv\Scripts\python.exe -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='openvino', imgsz=480)"
    Invoke-WebRequest -Uri 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite' -OutFile blaze_face_short_range.tflite
}
finally {
    Pop-Location
}
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

La exportación puede reinstalar otras variantes de OpenCV; volver a ejecutar el instalador restaura la variante headless.

### Linux (Bash)

Las instrucciones siguientes conservan el procedimiento usado en Linux. Las rutas `.venv/bin/`, `sudo` y `/sys/` son exclusivas de ese sistema; en Windows usa `.venv\Scripts\python.exe` y el instalador de arriba.

Ejecuta los comandos desde la carpeta del proyecto. La ruta tiene un espacio (`ia final`), así que va siempre entre comillas:

```bash
cd "/ruta/a/ia final"
./setup.sh
```

`setup.sh` hace cuatro cosas:

1. Crea el entorno virtual `.venv/`.
2. Instala PyTorch en su versión para CPU (así evita descargar unos 3 GB de CUDA).
3. Instala el Plan A de `requirements.txt` con las versiones de `requirements.lock.txt` como constraints. Las dependencias descartadas, como CLIP, no se instalan por aparecer en el lock histórico.
4. Deja instalado **solo** `opencv-contrib-python-headless`, con la versión exacta del lock.

El paso 4 es necesario porque las otras variantes de OpenCV traen plugins de Qt que chocan con PySide6. Puedes ejecutar el script todas las veces que quieras.

El instalador conserva `requirements.lock.txt`; no lo sobrescribe con un nuevo freeze. `pip check` puede indicar que ultralytics pide `opencv-python`: corresponde a la sustitución deliberada por la variante contrib headless. Otros conflictos deben revisarse.

## 3. Modelos (Linux)

Si la carpeta `models/` ya trae los modelos, sáltate este paso. Si no, descárgalos y expórtalos:

```bash
mkdir -p models && cd models
../.venv/bin/python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='openvino', imgsz=480)"
curl -L -o blaze_face_short_range.tflite https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
cd ..
```

Debes terminar con:

- `models/yolov8n.pt`
- `models/yolov8n_openvino_model/`
- `models/blaze_face_short_range.tflite`

El `imgsz=480` corresponde al perfil `detail`. El perfil opcional `fast` usa una exportación separada, `models/yolov8n_320_openvino_model/`, creada con los mismos pesos en FP32 y entrada 320. Conserva el modelo 480 original.

Para regenerar el perfil 320 sin sobrescribir el original, copia `models/yolov8n.pt` como `.venv/export/yolov8n_320.pt` y exporta esa copia con `imgsz=320`, sin cuantización ni conversión a FP16. Ultralytics genera entonces `.venv/export/yolov8n_320_openvino_model/`; guarda esa exportación en `models/yolov8n_320_openvino_model/`. No exportes la entrada 320 sobre la carpeta del modelo 480. Los archivos del modelo y el tamaño de su perfil deben coincidir.

La exportación puede instalar paquetes por su cuenta. Comprueba después que siga habiendo un solo OpenCV:

```bash
.venv/bin/pip list 2>/dev/null | grep -i opencv   # solo debe salir opencv-contrib-python-headless
```

Si sale otro, vuelve a ejecutar `./setup.sh`.

Los modelos descartados de YOLO-World y CLIP se archivaron de forma reversible en `.venv/archive/plan-b/`. El manifiesto `manifest.json` registra rutas originales, destinos, **6 archivos** y **457,125,812 bytes**. Git muestra eliminaciones de sus rutas anteriores, pero las copias locales se conservaron. Este archivo local está dentro de `.venv`, que no se versiona. El Plan A mantiene `yolov8n.pt`, la exportación original 480, el perfil 320 y BlazeFace en `models/`.

## 4. Antes de ejecutar: rendimiento

La meta es **15 FPS o más de resultados nuevos detectados y dibujados**. Conecta el cargador, usa buena luz y cierra aplicaciones que estén usando la cámara.

### Windows actual

Esta laptop usa **AMD Ryzen 7 3700U** (4 núcleos/8 hilos), cámara integrada 1 mediante DirectShow y plan de energía Equilibrado. Se comprobó cargador conectado y batería al 100 %; no se cambió el plan de energía global.

La cámara entrega unos **10 FPS a 1280×720** y unos **30 FPS a 640×480**; que el driver acepte pedir 30 FPS no garantiza que los entregue. Windows usa ahora 640×480 por defecto. La resolución de captura es independiente del perfil del detector.

La línea base anterior, a 1280×720, fue **7.5 FPS General** y **9.3 Universitario** (2026-11-07). Reducir solo la captura a VGA con el modelo 480 midió **7.52 y 8.25 FPS**; la inferencia seguía siendo el principal coste.

Con los ajustes de CPU, el hilo de inferencia y el perfil opcional `fast` 320, una medición posterior dio **17.90 FPS General** (30 s) y **19.01 FPS Universitario** (20 s), con captura real 640×480 y 2 s iniciales excluidos. Cuenta resultados nuevos aceptados y dibujados. Hubo variación entre corridas: un primer ensayo asíncrono dio 6.54/15.68 FPS.

La sesión posterior de **diez minutos** terminó con **10,513 resultados** y ningún error registrado, pico RSS **649.36 MiB**. El promedio Uni fue **17.71 FPS**; General ocupó solo 27 s entre cambios de modo y promedió **14.89 FPS**. Hubo intervalos de Uni inferiores a 15 mientras se grababa. El usuario pidió conservar estos ajustes; no se garantiza ≥15 sostenidos con grabación. Estos FPS del perfil `fast` no se atribuyen al perfil predeterminado `detail`. La prueba con objetos llegó a 50 puntos e insignia; el resultado 60/60 y la revisión de cuadernos de tapa dura confundidos con celulares siguen abiertos.

La optimización conserva la inferencia FP32 y todas las funciones. Windows fija OpenVINO a CPU y un hilo PyTorch para evitar competencia entre motores. YOLO y BlazeFace se ejecutan en un `QThread`, con una sola inferencia en curso; captura, puntaje y widgets permanecen en la interfaz. Al cambiar controles se descartan resultados de configuraciones anteriores. El dibujo RGB32 conserva los canales de color de 8 bits. Un repintado de la misma imagen no cuenta como otro resultado procesado.

### Referencia histórica Linux

Los números siguientes se midieron en el equipo Linux anterior (Intel Core i5-1235U, sin GPU NVIDIA); el rendimiento de esta laptop Windows debe medirse por separado. En aquel equipo se necesitaron estas dos condiciones:

1. **La laptop está enchufada.** Con batería, la CPU baja de frecuencia y la detección tarda el doble (unos 10 FPS).
2. **El turbo de la CPU está activo.** Compruébalo:

   ```bash
   cat /sys/devices/system/cpu/intel_pstate/no_turbo   # debe dar 0
   ```

   Si da `1`, actívalo. El cambio se pierde al reiniciar el equipo, así que repítelo antes de cada demo:

   ```bash
   echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
   echo performance | sudo tee /sys/firmware/acpi/platform_profile
   ```

Estas rutas existen en laptops Intel con el driver `intel_pstate`. En otro equipo pueden no existir: en ese caso, sáltate este paso.

## 5. Ejecutar

En Windows, para usar la cámara integrada:

```powershell
.\.venv\Scripts\python.exe app.py --camera 1
.\.venv\Scripts\python.exe app.py --camera 1 --mode uni
.\.venv\Scripts\python.exe tests\test_scoring.py
.\.venv\Scripts\python.exe tests\test_app.py
.\.venv\Scripts\python.exe tests\test_compare_models.py
```

Hay **29 pruebas del producto verificadas**: 17 de puntaje/reloj y 12 de interfaz Qt, más una prueba de captura múltiple de la herramienta de comparación. Las de Qt usan cámara y detecciones sintéticas; no acreditan detección con objetos reales.

### Perfiles de detección

| Perfil | Entrada | Uso |
|---|---|---|
| `detail` | 480×480 | Predeterminado; conserva la exportación original |
| `fast` | 320×320 | Opcional para reducir cálculo; puede perder objetos pequeños o lejanos |

Los perfiles conservan los mismos pesos YOLOv8n y clases, FP32 sin cuantización, BlazeFace, controles y reglas de puntaje. Reducir la entrada **puede reducir la precisión** aunque las funciones sigan disponibles. El perfil rápido no se activa por defecto hasta validar sus FPS y los objetos reales.

```powershell
.\.venv\Scripts\python.exe app.py --camera 1 --quality detail --resolution 640x480
.\.venv\Scripts\python.exe app.py --camera 1 --quality fast --resolution 640x480
```

`--resolution 640x480|1280x720` cambia la resolución solicitada a la cámara. `--quality detail|fast` cambia la entrada del detector; son ajustes independientes. Comprueba siempre qué resolución entrega el driver.

En Linux:

```bash
.venv/bin/python app.py                 # cámara USB (índice 2) o, si no está, la primera disponible
.venv/bin/python app.py --camera 2      # otra cámara, p. ej. una USB externa
.venv/bin/python app.py --mode uni      # arranca en modo Universitario
```

La ventana tarda unos segundos en abrir, porque carga los modelos al iniciar.

Hay una opción extra para verificar sin interactuar: `--autoshot SEG`. A los SEG segundos guarda la ventana en `capturas/autoshot.png`, imprime los FPS promedio de resultados nuevos aceptados y dibujados después de los primeros 2 s, y se cierra.

### Medición y verificación en vivo

`tools/profile_app.py` separa los tiempos de captura, detección y dibujo. `tools/verify_live.py` registra una sesión interactiva, eventos de controles/rondas, FPS por intervalos y memoria. Ambas herramientas cuentan resultados nuevos dibujados; la captura sola se mide por separado y no acredita FPS de detección. La evidencia de la verificación se guarda dentro de `.venv/verification/`, fuera de Git.

```powershell
.\.venv\Scripts\python.exe tools\profile_app.py --camera 1 --quality detail --mode general --seconds 20
.\.venv\Scripts\python.exe tools\verify_live.py --camera 1 --quality detail --resolution 640x480 --seconds 600
```

Durante la sesión larga hay que probar controles y objetos reales. E5 sigue abierta hasta completar sus criterios; E6 requiere además grabar y revisar el video de respaldo. El checklist y la grabación Windows están en `GUION_DEMO.md`.

Para comprobar una confusión del modelo, cierra la otra ventana que use la cámara y ejecuta:

```powershell
.\.venv\Scripts\python.exe tools\compare_models.py --capture --camera 1 --input .venv\verification\model_samples
```

Selecciona el objeto real en la lista superior y guarda tres muestras de cuaderno y dos de celular. Cada pulsación guarda un PNG distinto sin recuadros ni texto, y el botón indica el total. Al completar las muestras se cierra la ventana y se comparan los mismos frames con ambos perfiles. `comparison.json` conserva cajas y confianza desde 0.1 e indica cuáles superarían el umbral visible 0.35; no es una medición de mAP. Para repetir solo la comparación sin cámara, usa el mismo comando sin `--capture`.

Añade `--native` para comprobar también `models/yolov8n.pt` a entrada cuadrada 480 FP32. La prueba con 35 fotos reales reprodujo cuaderno→laptop también en ese original; los resultados y sus límites están en `VALIDACION_MODELO.md`. La etiqueta «Libro / Cuaderno» no crea una clase entrenada de cuaderno.

## 6. Cómo se usa

### Controles

| Control | Qué hace |
|---|---|
| **Cámara** | Elige la cámara. Cada vez que abres la lista, vuelve a buscar cámaras, así que aparecen también las que conectes con la app abierta. |
| **General / Universitario** | Cambia de modo. |
| **Objetos / Personas / Rostros** | Muestran u ocultan cada tipo de detección. Solo funcionan en modo General. |
| **Confianza** | Confianza mínima para mostrar una detección. Más alta: menos detecciones, pero más seguras. |
| **Capturar** | Guarda la imagen con las detecciones en `capturas/AAAAMMDD_HHMMSS.png`. |
| **Reiniciar** | Pone en cero las estadísticas de la sesión. |

### Atajos de teclado

| Tecla | Acción |
|---|---|
| `Espacio` | Capturar |
| `M` | Cambiar de modo |
| `R` | Reiniciar estadísticas |
| `Ctrl+Q` | Salir |

### Modo General

Cada detección se dibuja con el color de su grupo:

- **Azul:** personas.
- **Rosa:** rostros.
- **Verde:** objetos.

El panel lateral muestra:

- FPS, tiempo de sesión, modo y estado de la luz.
- Lo que hay en pantalla ahora.
- Cuántas veces apareció cada cosa en la sesión.
- El número de capturas.

### Modo "Listo para la Universidad"

Es una ronda de **1 minuto**. Los objetos se pueden mostrar uno a uno o de a varios: cada uno suma una sola vez y **queda guardado** aunque se retire (dos libros siguen valiendo +20):

| Objeto | Nivel | Puntos |
|---|---|---|
| Mochila | Acceso a campus | +10 |
| Libro / Cuaderno | Estudiante dedicado | +20 |
| Laptop | Listo para el aula | +25 |
| Celular | Siempre conectado | +5 |

- **Arriba:** el puntaje (máximo 60), una barra de progreso, el nivel alcanzado, un chip por objeto y el reloj de la ronda. Los chips encendidos son los objetos ya guardados; los apagados, los que faltan. En los últimos 10 s el reloj se pone rojo.
- **Ronda:** el reloj arranca con el primer objeto que se detecta al entrar al modo. Termina al acabarse el minuto o, antes, al juntar los 4 objetos. El resultado (**¡TIEMPO!** o **¡COMPLETO!**, con el tiempo que tardó) se muestra 5 s; luego el puntaje vuelve a 0 y espera el siguiente objeto. Los objetos que siguen en cuadro desde la ronda anterior no arrancan otra solos: hay que mostrar uno nuevo, o retirarlo y volver a mostrarlo. Las duraciones están en `config.py` (`UNI_ROUND_S` y `UNI_RESULT_S`).
- **Insignia:** con **50 puntos o más** aparece la insignia **NIVEL UNIVERSITARIO**.
- **Antiparpadeo:** un objeto se guarda solo después de verse 0.3 s seguidos. Así un falso positivo de un frame no suma puntos.
- **Cuadernos y lapiceros:** el modelo está entrenado con COCO, que no tiene esas clases. Por eso un cuaderno se detecta con la clase libro (la etiqueta dice **Libro / Cuaderno**), y el lapicero se reemplazó por el **celular**.

### Poca luz

Si la imagen se mantiene oscura más de 1 segundo:

- Aparece una franja amarilla abajo: *"Poca luz: la detección puede fallar. Acerca una lámpara."*
- El panel muestra **Luz: Baja**.

### Si se desconecta la cámara

Se muestra un aviso en lugar del video y la app sigue abierta. Cada 2 s intenta abrir de nuevo la misma cámara, así que al reconectarla el video vuelve solo.

## 7. Problemas comunes

**Se abre la cámara equivocada o no hay imagen.**
- Prueba otro índice con `--camera N` o con el selector.
- **Windows:** permite el acceso en **Configuración → Privacidad y seguridad → Cámara** (en Windows 10: **Privacidad → Cámara**), incluido el acceso para aplicaciones de escritorio. Cierra Cámara, Teams o cualquier aplicación que pueda tenerla ocupada y vuelve a probar `--camera 1` (índice verificado en esta laptop).
- En el equipo Linux anterior, la integrada era el índice **0**, el índice 1 solo daba metadatos y la USB aparecía como **2**. Los índices pueden cambiar en otro equipo.
- **Solo Linux:** `.venv/bin/python tools/cam_check.py` comprueba qué índices dan imagen y guarda una foto por índice en `tools/out/`. En Windows, prueba `--camera 1` o el selector de cámara de la app.

**Poca luz o detecciones pobres.**
- Acerca una lámpara y evita tener una ventana detrás (contraluz).
- Con poca luz la cámara alarga la exposición y entrega menos cuadros por segundo, así que también bajan los FPS.
- Algunas clases son más difíciles para el modelo:
  - **Mochila:** se detecta mucho mejor **puesta en la espalda** y entera en el cuadro que apoyada en una mesa.
  - **Laptop:** se detecta por la pantalla y el teclado, no por la tapa.

**`Could not load the Qt platform plugin "xcb"` (Linux)**
- Si el mensaje menciona `xcb-cursor`, falta el paquete del sistema: `sudo apt install libxcb-cursor0`.
- Si menciona `cv2/qt/plugins`, quedó instalado un OpenCV con GUI: vuelve a ejecutar `./setup.sh`.
- **Nunca** instales ni actualices `ultralytics` con `pip` por separado: reinstala `opencv-python`. Si lo hiciste, corre `./setup.sh` de nuevo.

En Windows, si instalaste o actualizaste dependencias por separado, ejecuta `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1` para restaurar las versiones verificadas y la variante de OpenCV.

**Menos de 15 FPS.**
- Revisa la sección 4: cargador conectado, buena luz y modo de energía; el ajuste manual de turbo descrito allí corresponde a Linux.
- En el equipo Linux anterior, la cámara integrada entregaba unos 15–16 FPS a 1280×720. La USB externa daba 30 a esa resolución y la app llegaba a 19–22 FPS. Mide el equipo actual con `--autoshot 8`.

**Sin pantalla (por SSH).** `QT_QPA_PLATFORM=offscreen .venv/bin/python app.py --autoshot 8`.

## 8. Archivos

| Archivo | Contenido |
|---|---|
| `app.py` | Interfaz, bucle de video y dibujo |
| `detector.py` | Detección de objetos (YOLO) y de rostros (MediaPipe) |
| `scoring.py` | Antiparpadeo y puntaje del modo Universitario |
| `config.py` | Clases, etiquetas, puntos, umbrales y colores |
| `setup.ps1` | Instalador Windows; usa `requirements.windows.lock.txt` cuando existe |
| `setup.sh` | Instalador Linux |
| `tests/test_scoring.py` | Pruebas del puntaje; comandos para cada sistema en la sección 5 |
| `tests/test_app.py` | Pruebas Qt con cámara y detecciones sintéticas |
| `tools/profile_app.py` | Rendimiento real de captura, inferencia y dibujo |
| `tools/verify_live.py` | Registro de sesión, controles, rondas, FPS y memoria |
| `tools/compare_models.py` | Muestras sin overlays y comparación 480/320 del mismo objeto |
| `tools/` | Incluye herramientas históricas V4L2 exclusivas de Linux |
| `capturas/` | Capturas de pantalla de la app |
