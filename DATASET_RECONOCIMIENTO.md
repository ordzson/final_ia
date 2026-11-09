# Datos para distinguir cuadernos y laptops

**Todavía no se ha reentrenado ningún modelo.** Se han comparado modelos preentrenados y configuraciones de inferencia.

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
