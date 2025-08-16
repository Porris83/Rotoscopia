# Roadmap de Funcionalidades - Rotoscopia MVP

Objetivo central: herramienta rápida y enfocada para rotoscopiar video cuadro a cuadro y generar bases de animación / sprites.

## Principios de Diseño
- Priorizar lo que impacta directamente en la calidad y velocidad de rotoscopia manual.
- Evitar sobrecargar UI temprano (una sola barra de herramientas clara).
- Añadir sólo lo que destraba el siguiente nivel de productividad.
- Mantener guardado simple pero seguro (proyecto > exportaciones).

---
## Fase 1 (COMPLETADA)
- Carga de video y navegación frame a frame.
- Opacidad del fondo.
- Dibujo libre + borrar.
- Copiar dibujo del frame anterior.
- Guardar PNG con transparencia (manual por frame).
- Corrección de alineación cursor y preservación de fondo.

---
## Fase 2 – Productividad Básica (Prioridad Alta)
Lo mínimo para que el flujo "rotoscopio 100+ frames" sea cómodo.

1. Onion Skin (1 frame previo inicialmente)
   - Config: toggle ON/OFF, opacidad (slider 0–100%).
   - Luego ampliable a N previos / próximos.
2. Ajustes de Pincel
   - Grosor (1–12 px).
   - Color (paleta corta: negro, blanco, rojo, azul, verde, personalizado).
3. Undo / Redo por Frame
   - Pila de acciones (líneas) simple (límites: p.ej. 20 pasos).
4. Zoom + Pan
   - Rueda = zoom (centrado en cursor).
   - Barra espaciadora + arrastrar = pan (o botón central).
5. Guardado de Proyecto (.json + imágenes de overlays)
   - Estructura: /projects/nombre/{meta.json, frames/*.png}
   - Meta.json: {video_path, frame_count, overlays_present[], brush_last_used, fps_simulado}.
6. Auto-guardar al cambiar de frame (si hubo cambios).

---
## Fase 3 – Herramientas Intermedias
Para refinamiento de animación y flujo largo.

1. Onion Skin Avanzado
   - Multiframe (configurable previos/próximos 0–3).
   - Colores diferenciados (rojo prev, verde sig). 
2. Reproducción de Preview
   - Play/Stop (limpio). FPS configurable (simulado).
3. Selector de FPS del Proyecto
   - Afecta preview y export secuencial (naming / sheet). No altera frames originales.
4. Herramienta Borrador dedicada (tecla E)
   - Muestra cursor distinto.
5. Estabilizador de Trazo (suavizado simple de puntos – moving average o Chaikin).
6. Paleta Personalizable
   - Guardar hasta 8 colores del usuario.
7. Grid / Guías
   - Toggle (tecla G), opacidad, spacing.

---
## Fase 4 – Exportación y Gestión
Potencia para integrar en pipeline de sprites / animación.

1. Exportación Masiva
   - Todo lo dibujado (solo frames con overlay) a /exports.
2. Export Sprite Sheet
   - Parámetros: columnas automáticas o definidas, padding, orden.
3. Export JSON Manifest
   - {frame_index, filename, duration_ms}.
4. Export Video con Alpha (ffmpeg si está disponible).
5. Re-export rápida (usa caché de overlays ya guardados).

---
## Fase 5 – Avanzado / Opcional
Funcionalidades que suman pero no bloquean el core.

1. Lazo (selección y mover parte del trazo)
2. Relleno (bucket) con threshold
3. Smudge / Blur (pinceles especiales)
4. Time-lapse del proceso (captura incremental)
5. Modo Pixel Art (snap a grid + pincel duro 1px)
6. Múltiples capas de dibujo (máx 3): lineart / relleno / efectos
7. Modo espejo (simetría horizontal)

---
## Fase 6 – Premium / Futuro Lejano
Feature set que puede ir a una versión "Pro".

- Brillos / blending modes.
- Sistema de pinceles avanzados (texturas).
- Animación de opacidad o color por frame.
- Integración con tablet (pressure -> grosor).
- Macro scripting (repetir acciones). 

---
## Tabla de Prioridad (Resumen)
| Feature | Fase | Impacto | Complejidad | Notas |
|---------|------|---------|-------------|-------|
| Onion Skin básico | 2 | Muy alto | Media | Multiplica precisión inmediata.
| Grosor + Color | 2 | Muy alto | Baja | Aumenta control visual.
| Undo/Redo | 2 | Alto | Media | Reduce frustración.
| Zoom/Pan | 2 | Alto | Media | Necesario para detalles.
| Guardado de Proyecto | 2 | Muy alto | Media | Persistencia real.
| Auto-guardar | 2 | Alto | Baja | Seguridad.
| Preview Play | 3 | Medio | Media | Feedback de timing.
| FPS configurado | 3 | Medio | Baja | Contexto de animación.
| Sprite Sheet export | 4 | Alto | Media | Pipeline juegos.
| Export masiva | 4 | Alto | Baja | Simplifica cierre.
| Estabilizador | 3 | Medio | Media | Calidad de línea.
| Paleta personal | 3 | Medio | Baja | Comodidad.
| Grid | 3 | Medio | Baja | Composición.
| Lazo | 5 | Medio | Alta | Complejo de implementar limpio.
| Relleno bucket | 5 | Medio | Media | Requiere threshold.
| Smudge/Blur | 5 | Bajo | Media | No core.
| Multi capas | 5 | Alto | Alta | Cambia modelo de datos.
| Pixel mode | 5 | Nicho | Media | Útil para sprites retro.

---
## Dependencias Técnicas entre Features
- Undo/Redo requiere representación de acciones (lista de trazos) o snapshots por capa.
- Estabilizador necesita capturar puntos antes de rasterizar la línea definitiva.
- Múltiples capas implica refactor de modelo de overlay (lista de QPixmaps + blend order).
- Sprite Sheet export depende del guardado masivo.
- Onion Skin avanzada depende de la versión básica.
- Lazo y Bucket conviene hacerlos luego de capas/más robustez de datos.

---
## Modelo de Datos Propuesto (Fase 2 → base escalable)
```json
project.meta {
  "version": 1,
  "video_path": "...",
  "frame_width": W,
  "frame_height": H,
  "frame_count": N,
  "fps": 12,
  "frames_with_overlay": [0,3,4,10,...],
  "settings": {"brush_color": "#000000", "brush_size": 4}
}
```
Overlays almacenados como PNG RGBA (solo los que tienen trazo) en /projects/nombre/frames/frame_00010.png
```

---
## Atajos Planeados (Acumulativos)
Fase 2:
- Ctrl+S guardar frame
- Z / Ctrl+Z undo, Ctrl+Y redo
- 1–5: presets de grosor
- C: cambiar color rápido (ciclo)
- O: toggle onion skin
- +/- : zoom (o Ctrl + rueda)

Fase 3:
- Barra espaciadora: pan
- P: play/stop preview
- G: grid

Fase 4:
- Shift+E: export masivo
- Shift+P: export sprite sheet

---
## Estrategia de Implementación (Fase 2) Iterativa
1. Brush settings (grosor + color) → UI simple (toolbar pequeña).
2. Onion Skin básico (usa frame anterior raster + composición semitransparente antes de overlay).
3. Undo/Redo (stack de pixmaps o lista de strokes; empezar snapshot simple por rendimiento aceptable en 1080p si límite bajo de steps).
4. Zoom/Pan (usar QGraphicsView o implementar transform manual en paint composition; decisión aquí afecta futuro).
5. Persistencia de proyecto (guardar overlays existentes + meta.json).
6. Auto-save hook al cambiar de frame (si dirty flag true).

---
## Riesgos y Mitigaciones
| Riesgo | Mitigación |
|--------|------------|
| Memoria alta con muchos snapshots (undo) | Límite de historial + compresión opcional PNG temporal |
| Onion skin sobrecarga CPU con varios frames | Cachear QPixmaps precompuestos |
| Zoom/Pan complejiza mapeo cursor | Centralizar transformación en una función reutilizable (ya existe mapToOverlay base) |
| Guardado corrupto si se cierra abrupto | Auto-save + escribir meta.json atómico (tmp + rename) |
| FPS distinto a frames capturados causa confusión | Mostrar aclaración: “FPS sólo afecta preview/export” |

---
## Métricas de Éxito (cuando midamos)
- Tiempo medio para rotoscopiar 10 frames (↓ con Fase 2).
- % de frames guardados sin rehacer (Undo bajo). 
- Crash-free sessions.
- Tamaño promedio del proyecto vs duración del video.

---
## Próximo Paso Inmediato
Elegir orden definitivo de Fase 2 e iniciar por Brush Settings + Onion Skin básico.

---
¿Aprobamos este roadmap? Ajusto lo que quieras y empezamos.
