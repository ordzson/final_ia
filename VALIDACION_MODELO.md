# Comparación del modelo — 2026-11-08

**Actualización:** Windows usa ahora `accurate` (YOLO26s, 640 FP32). El estudio inicial que sigue se conserva como referencia; la nueva comparación y sus límites están al final de este documento.

La confusión de este cuaderno también ocurre en `yolov8n.pt`, antes de exportar. La exportación OpenVINO a **480** conservó las clases y cajas del original en las **35 imágenes** comprobadas. Una confianza difirió en **0.00001**; las demás coincidieron a cinco decimales. Esto no garantiza equivalencia en todas las imágenes posibles.

Se guardaron **35 PNG distintos sin overlays**: 22 fotos del mismo cuaderno de tapa dura y 13 del mismo celular, con distintos ángulos. Las etiquetas se revisaron visualmente porque el selector permaneció en «Cuaderno» durante toda la captura. `samples.original.json` conserva las etiquetas iniciales; no se modificaron las imágenes ni las predicciones.

Se compararon los mismos frames, FP32 y umbral visible **0.35**. La referencia `.pt` usa entrada cuadrada 480 (`rect=False`) para igualar la exportación. El reporte guarda además detecciones desde 0.1.

| Modelo | Cuaderno reconocido como libro | Cuaderno confundido con laptop | Cuaderno sin detectar | Celular correcto | Celular confundido con laptop | Celular sin detectar |
|---|---:|---:|---:|---:|---:|---:|
| `.pt` original, 480 | 0/22 | 18 | 4 | 7/13 | 1 | 5 |
| OpenVINO `detail`, 480 | 0/22 | 18 | 4 | 7/13 | 1 | 5 |
| OpenVINO `fast`, 320 | 0/22 | 7 | 15 | 13/13 | 0 | 0 |

Estos conteos describen solo estas fotos, varias muy parecidas entre sí; no son mAP ni una estimación general de precisión. Se revisó que las cajas correspondieran al objeto mostrado. Cuando hay cajas duplicadas de la misma clase se cuenta una sola imagen.

La confusión **cuaderno → celular** reportada por el usuario no se reprodujo en estas imágenes; sí se reprodujo **cuaderno → laptop**, también en el original. Volver a 480 no resolvió este cuaderno. El modelo COCO no tiene una clase propia «cuaderno»: la etiqueta «Libro / Cuaderno» es el nombre mostrado para `book`, no un entrenamiento adicional.

Se mantiene el rendimiento que el usuario aceptó. No se cambiaron pesos ni umbrales para ocultar el error. La detección fiable de este tipo de cuaderno queda pendiente de trabajo sobre el modelo y de una nueva validación; la captura múltiple ya está corregida.

## Evidencia y reproducción

Todo el material visual permanece fuera de Git, en `.venv/verification/hardcover_samples/`:

- `samples.json`: etiquetas revisadas y nombres de los 35 PNG originales.
- `samples.original.json`: etiquetas iniciales, antes de la revisión.
- `capture_events.jsonl`: cada intento de guardar muestras.
- `contact_sheet.png`: revisión visual de las 35 fotos.
- `comparison.json`: las 105 inferencias, clases, cajas y confianzas.
- `summary.json`: conteos resumidos.

Para repetir la comparación sobre estas imágenes, sin abrir la cámara:

```powershell
.\.venv\Scripts\python.exe tools\compare_models.py --native --input .venv\verification\hardcover_samples
```

Para recoger otras imágenes, usa una carpeta nueva y añade `--capture --camera 1`. Elige el objeto real en el selector antes de guardar. Cada pulsación crea un PNG independiente; el botón y los contadores indican el progreso. La prueba `tests/test_compare_models.py` comprueba cinco capturas distintas, con etiquetas y píxeles correctos, sin hardware.

## Mejora de reconocimiento: prioridad cuaderno frente a laptop

El usuario pidió priorizar distinguir cuaderno y laptop, aunque disminuyan los FPS. Se compararon pesos oficiales COCO de YOLO11n/s/m y YOLO26n/s, distintos tamaños y dos vocabularios experimentales YOLOE. Los modelos más grandes no resolvieron siempre el problema: YOLO11s/m a 640 no reconocieron ninguna de las cuatro fotos de tapa cerrada. YOLOE mejoró algunas del cuaderno, pero perjudicó notablemente el celular y no se adoptó.

Se eligió **YOLO26s a 640**, exportado OpenVINO **FP32**, sin entrenamiento adicional ni cuantización. Los archivos activos son `models/yolo26s.pt` y `models/yolo26s_640_openvino_model/`. SHA256 del `.pt`: `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`. Origen: [pesos oficiales Ultralytics](https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s.pt). Exportación con Ultralytics 8.4.207 / OpenVINO 2026.4.1, `imgsz=640`, `quantize=32`, `half=False`, `dynamic=False`, `batch=1`, `nms=None`.

### Las mismas 35 capturas, confianza 0.35

| Vista real | Fotos | `fast` anterior: etiqueta más fuerte | `accurate`: etiqueta más fuerte |
|---|---:|---|---|
| Cuaderno con tapa cerrada | 4 | 3 laptop, 1 sin detectar | **4 libro** |
| Cuaderno con tapa levantada | 8 | 8 sin detectar | **7 libro**, 1 laptop |
| Páginas visibles | 10 | 4 laptop, 6 sin detectar | **10 sin detectar** |
| Celular | 13 | **13 celular** | **13 celular** |

En conjunto, el cuaderno pasó de **0/22 a 11/22** fotos reconocidas como libro; las confusiones con laptop bajaron de **7 a 1**, con **15 a 10** omisiones. La exportación nueva conservó esos conteos por vista respecto al `.pt` de YOLO26s. No se asegura equivalencia numérica en todas las imágenes. Las cuatro fotos de tapa cerrada pertenecen al mismo objeto, por lo que **4/4 no es una tasa general de precisión**. Las páginas abiertas siguen siendo un fallo importante. No se cambió `laptop` por `book` mediante reglas de forma ni se alteraron etiquetas de predicciones.

### Evaluación con cajas de referencia en imágenes públicas

Se seleccionaron **90 imágenes COCO val2017**: 45 de validación y 45 de prueba reservada, disjuntas por `image_id`. Cada grupo contiene las 13 clases de la app y seis imágenes sin ninguna de ellas. Se conservaron todas las cajas objetivo de cada imagen; se excluyeron imágenes con anotaciones crowd objetivo. Semilla `20261108`; tres imágenes nuevas por categoría y grupo, más seis negativas. No son muestras de entrenamiento ni el test oficial COCO.

Matching de la misma clase, uno a uno, **IoU ≥ 0.5**, confianza **0.35** y NMS IoU 0.7. Los duplicados son falsos positivos. No se calculó mAP oficial. El grupo reservado se evaluó después de seleccionar el candidato; no se usó para ajustar umbrales.

| Prueba reservada: 45 imágenes, 294 objetos | `fast` YOLOv8n 320 | `accurate` YOLO26s 640 |
|---|---:|---:|
| Laptops correctas / 23 | 12 | **16** |
| Falsos positivos laptop | 5 | **4** |
| Libros correctos / 43 | 0 | **12** |
| Falsos positivos libro | 0 | **2** |
| Recall global | 32.3 % | **53.7 %** |
| Precisión global | **82.6 %** | 78.2 % |
| F1 macro de las 13 clases | 39.3 % | **61.4 %** |
| Falsos positivos totales | **20** | 44 |
| Imágenes negativas con falsos positivos / 6 | 0 | 0 |

Detecta más objetos, pero también produce más falsos positivos; **no mejoró todas las clases**. El F1 de teclado bajó de 0.667 a 0.519 y el de celular público de 0.571 a 0.545. En validación el F1 macro fue 0.368 → 0.552. Todos los conteos por clase, cajas, scores y omisiones quedan en los reportes JSON. Esta muestra pequeña no acredita fiabilidad universal ni resuelve por completo cuadernos, objetos pequeños o lejanos.

### Configuración y evidencia

- `accurate` es el perfil predeterminado **Windows**; Linux conserva `detail`, sin atribuirle nuevas mediciones. `fast` y `detail` originales permanecen disponibles.
- Se mantienen las 13 categorías, BlazeFace con mínimo 0.5, confianza inicial 0.35, controles y puntos. No hubo reentrenamiento.
- Los seis paquetes instalados solo para preparar YOLOE se retiraron al descartarlo. El entorno vuelve al lock Windows de 53 paquetes.
- `.venv/candidates/large_comparison.json`: comparación nativa y desglose por vista.
- `.venv/candidates/priority_local_openvino.json`: 35 inferencias del modelo exportado.
- `.venv/candidates/coco_val/manifest.json`: selección, anotaciones y procedencia de las 90 imágenes.
- `.venv/candidates/reports/{baseline,priority}_{validation,test}.json`: métricas y predicciones completas.
- `tools/evaluate_detection.py` y `tests/test_evaluate_detection.py`: evaluación reproducible y contratos de matching, sin descargas automáticas.

```powershell
.\.venv\Scripts\python.exe tools\evaluate_detection.py --manifest .venv\candidates\coco_val\manifest.json --split test --model models\yolo26s_640_openvino_model --imgsz 640 --out .venv\verification\accurate_test.json
.\.venv\Scripts\python.exe tools\compare_models.py --capture-only --camera 1 --quality accurate --input .venv\verification\hardcover_holdout
```

La segunda herramienta guarda varias muestras sin cerrarse por alcanzar una meta. **B** selecciona cuaderno, **L** laptop y **C** celular; cada clic guarda un PNG sin overlays. Cerrar termina la captura sin ejecutar comparaciones. Las muestras nuevas requieren revisión de sus etiquetas; no se consideran automáticamente datos de entrenamiento. Recomendaciones para un dataset propio en `DATASET_RECONOCIMIENTO.md`.
