# Datos para distinguir cuadernos y laptops

## Detector de lápices, cuadernos y lapiceros

El detector incluido parte de `models/yolov8n.pt` y se ajustó con dos datasets a color. [School supplies v3, de AYLA](https://universe.roboflow.com/ayla-cpohc/school-supplies-su2af), incluye etiquetas separadas para lápiz, lapicero y cuaderno. [detector_de_utiles v1, de Elizabeths Workspace](https://universe.roboflow.com/elizabeths-workspace-bd7ii/detector_de_utiles), aporta cuadernos y lapiceros. Ambas fuentes usan [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Se unificaron los nombres, se conservaron las particiones y se comprobó que no hubiera imágenes idénticas entre ellas.

| Partición | Imágenes | Lápiz | Cuaderno | Lapicero |
|---|---:|---:|---:|---:|
| Entrenamiento | 907 | 210 | 214 | 345 |
| Validación | 97 | 20 | 35 | 41 |
| Prueba | 40 | 7 | 9 | 10 |

La app carga la exportación OpenVINO al iniciar. El detector de útiles complementa al perfil COCO y a BlazeFace. El modo Universitario puntúa mochila, cuaderno, libro, laptop y lapicero según las detecciones visibles.

La mejor época obtuvo mAP50 **0.802** en validación. En las 40 imágenes reservadas, los pesos PyTorch obtuvieron mAP50 **0.910** y mAP50–95 **0.678**. La ruta de VisionAI con OpenVINO FP32, confianza 0.35 e IoU mínimo 0.50 acertó **4/7 lápices**, **9/9 cuadernos** y **6/10 lapiceros**. Hubo un falso positivo de lapicero. La prueba cubre pocos ejemplares y faltan tomas con la cámara y los objetos de la demo.

En el Ryzen 5 3600, con imágenes de validación reproducidas a 640 × 480 y ambos detectores activos, la interfaz procesó **17.48 FPS en General** y **18.72 FPS en Universitario** usando `detail`. En General se midieron **21.57 FPS** con `fast` y **7.93 FPS** con `accurate`. Cada corrida duró 10 s y se excluyeron los primeros 2 s. `detail` quedó como perfil predeterminado para usar entrada COCO de 480 y superar 15 FPS en esta prueba. Falta repetir la medición con cámara en el equipo de la demo.

Para reproducir el ajuste, usa Ultralytics 8.4.207, PyTorch CUDA y PyYAML desde la raíz del proyecto. La prueba reservada procede de School supplies v3.

```powershell
.\.venv\Scripts\python.exe tools\merge_stationery_color.py .venv\stationery-color 'C:\ruta\School supplies.v3i.yolo26.zip' 'C:\ruta\detector_de_utiles.v1i.yolo26.zip'
.\.venv\Scripts\yolo.exe detect train model=models/yolov8n.pt data=.venv/stationery-color/data.yaml imgsz=640 device=0 batch=8 epochs=24 freeze=7 workers=2 amp=False seed=42 cache=disk mosaic=0.15 close_mosaic=4 nbs=8 optimizer=AdamW lr0=0.001 warmup_epochs=1 warmup_bias_lr=0.0 cos_lr=True project=.venv/runs name=stationery-color-v8n
.\.venv\Scripts\yolo.exe detect val model=.venv/runs/stationery-color-v8n/weights/best.pt data=.venv/stationery-color/data.yaml split=test imgsz=640 device=0 batch=4
.\.venv\Scripts\yolo.exe export model=.venv/runs/stationery-color-v8n/weights/best.pt format=openvino imgsz=640 batch=1 dynamic=False quantize=32 device=cpu
```

## Experimento anterior en escala de grises

[Stationary Items Dataset v3 — Assignment02](https://universe.roboflow.com/national-university-fast/stationary-items-dataset/dataset/3), de national university fast, usa licencia [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). El ZIP YOLO26 utilizado contiene 1,103 imágenes de 640 × 640 en escala de grises. La preparación conserva la partición del ZIP y solo las etiquetas `pencil` y `notebook`. Convierte sus polígonos en cajas rectangulares. Las imágenes con otros útiles quedan como negativos cuando carecen de ambas clases.

| Partición | Imágenes | Cajas de lápiz | Cajas de cuaderno |
|---|---:|---:|---:|
| Entrenamiento | 825 | 389 | 174 |
| Validación | 168 | 115 | 34 |
| Prueba | 110 | 86 | 18 |

Los siguientes comandos se ejecutan desde la raíz de `final_ia`, con Ultralytics, PyTorch CUDA y PyYAML instalados en el entorno de entrenamiento. El segundo ajuste conserva 347 imágenes anotadas y 84 negativos revisados visualmente. Algunas imágenes descartadas como negativos tenían útiles visibles sin su correspondiente caja.

```powershell
.\.venv\Scripts\python.exe tools\prepare_stationery.py 'C:\ruta\stationery.zip' .venv\stationery-v3
.\.venv\Scripts\yolo.exe detect train model=models/yolo26s.pt data=.venv/stationery-v3/data.yaml imgsz=640 device=0 batch=2 epochs=12 freeze=10 workers=2 amp=False seed=42 cache=disk close_mosaic=4 nbs=16 project=.venv/runs name=stationery-v3
.\.venv\Scripts\python.exe tools\prepare_stationery.py 'C:\ruta\stationery.zip' .venv\stationery-v3-reviewed --reviewed-negatives tools\stationery-reviewed-negatives.txt
.\.venv\Scripts\yolo.exe detect train model=.venv/runs/stationery-v3/weights/best.pt data=.venv/stationery-v3-reviewed/data.yaml imgsz=640 device=0 batch=6 epochs=24 freeze=10 workers=2 amp=False seed=42 cache=disk mosaic=0 degrees=10 translate=0.1 scale=0.35 nbs=6 optimizer=AdamW lr0=0.00045 lrf=0.15 warmup_epochs=1 cos_lr=True project=.venv/runs name=stationery-v3-reviewed
.\.venv\Scripts\yolo.exe detect val model=.venv/runs/stationery-v3-reviewed/weights/best.pt data=.venv/stationery-v3/data.yaml split=test imgsz=640 device=0 batch=4
.\.venv\Scripts\yolo.exe export model=.venv/runs/stationery-v3-reviewed/weights/best.pt format=openvino imgsz=640 batch=1 dynamic=False quantize=32 device=cpu
```

El modelo experimental acertó 2 de 86 lápices y 8 de 18 cuadernos en la prueba reservada con confianza 0.35 e IoU mínimo 0.50. La versión a color lo sustituyó. Hay prefijos de nombres compartidos entre particiones de este ZIP, por lo que podrían repetirse ejemplares o sesiones.

## Referencia anterior al ajuste

## Qué datos existen

| Datos | Estado y uso |
|---|---|
| Modelos preentrenados en COCO | Reconocen 80 categorías de origen; la app muestra un subconjunto de 13. COCO tiene `book`, pero no una clase específica de cuaderno (`notebook`). La etiqueta actual **Libro / Cuaderno** de la interfaz traduce `book`; no añade una capacidad entrenada. |
| Subconjunto público COCO val2017 | 90 imágenes: 45 de validación y 45 de prueba, disjuntas, con cajas de las 13 clases de la app y ejemplos negativos. Se usan para evaluación; no se han usado para entrenar. |
| Capturas propias de diagnóstico | 35 fotos: 22 del mismo cuaderno y 13 del mismo celular. Tienen etiquetas por imagen, sin cajas. Sirven para detectar fallos concretos; **no están listas para entrenar un detector YOLO** y no representan variedad de objetos independientes. |

## Cómo preparar datos propios útiles

1. **Definir las clases antes de etiquetar.** Para corregir esta confusión manteniendo la integración actual, se recomienda agrupar libros y cuadernos en `book` y conservar `laptop` como clase independiente. Una clase propia de cuaderno requeriría adaptar también la integración y el puntaje. Mantener los mismos identificadores en entrenamiento, validación y prueba. No etiquetar una laptop como cuaderno por parecerse visualmente.
2. **Fotografiar las confusiones reales.** Incluir varios cuadernos de tapa dura abiertos y cerrados, laptops abiertas y cerradas, y ambos objetos juntos. Variar fondos, iluminación, distancia, orientación, manos y oclusiones. Añadir escenas sin los objetos buscados para observar falsos positivos.
3. **Conservar las otras clases.** Incluir ejemplos de las clases que se quieren mantener y anotar **todos sus objetos visibles en cada imagen**, no solo el cuaderno. Omitir sus cajas puede enseñar al modelo que esos objetos son fondo. Revisar después si el ajuste perjudica personas, celulares, mochilas u otras clases conservadas.
4. **Separar por objeto y sesión.** Crear conjuntos de entrenamiento, validación y prueba independientes. Las fotos casi iguales, ráfagas o cuadros de un mismo video deben permanecer juntos. Reservar objetos y sesiones distintos para evaluación; cambiar únicamente el nombre del archivo no crea una muestra independiente.
5. **Anotar y revisar las cajas.** Cada objeto necesita su clase y una caja ajustada. Revisar omisiones, clases confundidas y cajas inconsistentes antes de convertir las anotaciones al formato de entrenamiento YOLO. Las 35 etiquetas actuales por imagen no sustituyen ese trabajo.

## Cómo decidir si mejoró

Usar entrenamiento para ajustar pesos, validación para elegir cambios y la prueba reservada para comprobar la decisión final. Comparar cuaderno frente a laptop, sus falsos positivos y las demás clases con el mismo protocolo y umbrales. Si se usa repetidamente la prueba para elegir configuraciones, deja de ser una comprobación independiente.

La cantidad necesaria depende de la variedad y los fallos observados. Reunir muchas fotos repetidas no garantiza mejorar; hacen falta ejemplos distintos, anotaciones completas y evaluación independiente. Tampoco un buen resultado en estas muestras garantiza reconocer todos los cuadernos o laptops.
