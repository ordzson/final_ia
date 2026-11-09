# Comparación del modelo — 2026-11-08

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
