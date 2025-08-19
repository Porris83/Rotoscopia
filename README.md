# Rotoscopia – Editor de Rotoscopia Modular

Herramienta de rotoscopia manual para crear y limpiar animaciones cuadro a cuadro a partir de video (inspiración clásica: Prince of Persia). Arquitectura modular con herramientas extensibles y soporte de capas.

## 🎯 Objetivo
Extraer y dibujar siluetas / animaciones cuadro a cuadro para pipelines de pixel‑art o cleanup 2D.

## ✅ Funcionalidades Actuales

### Núcleo
* Carga de video (MP4, MOV, AVI, MKV – mayúsculas/minúsculas)
* Navegación frame a frame (barra de herramientas + atajos)
* Onion Skin (frame anterior y siguiente tintados: azul / rojo) con opacidad ajustable
* Fondo (frame de video) con opacidad configurable y toggle rápido
* Zoom anclado al cursor + Pan (Herramienta Mano y/o botones ratón según configuración)

### Herramientas (Strategy en `rotoscopia/tools.py`)
* Pincel (antialias, color, grosor variable)
* Borrador (limpia a transparencia usando CompositionMode_Clear)
* Línea (previsualización dinámica)
* Mano (pan suave, cursor contextual, no afecta undo)

### Capas (por frame)
* Múltiples capas por frame (creación automática de capa base)
* Composición de capas visibles respetando opacidad individual
* Copiado de capas desde frame anterior
* Renombrado de capa, visibilidad, opacidad (según UI actual)
* Persistencia de capas por frame (`layers.json` + PNGs)

### Edición / Historial
* Undo / Redo por frame (límite configurable `MAX_HISTORY`)
* Copiar dibujo/capas del frame anterior
* Limpiar capa activa o (fallback) overlay simple

### Guardado y Exportación
* Guardar frame/overlay a PNG (carpeta `exports/`)
* Guardar proyecto (frames, capas, metadatos, configuración básica pincel)
* Cargar proyecto (restaura capas, overlays legacy, color y tamaño de pincel)
* Exportar animación a MP4 o secuencia de PNG (compone fondo + capas; excluye onion)

### Estado UI Persistente (parcial)
* Color y tamaño de pincel se guardan en meta
* (Pendiente: guardar estado zoom, herramienta activa, toggles)

### Atajos Centralizados (`settings.py`)
| Categoría | Acción | Atajo |
|-----------|--------|-------|
| Frames | Siguiente frame | Right |
| Frames | Anterior frame | Left |
| Frames | Copiar del anterior | Ctrl+D |
| Guardado | Guardar overlay PNG | Ctrl+S |
| Guardado | Guardar proyecto | Ctrl+Shift+S |
| Export | Exportar animación | Ctrl+E |
| Edición | Undo | Ctrl+Z |
| Edición | Redo | Ctrl+Shift+Z |
| Herramientas | Pincel | B |
| Herramientas | Borrador | E |
| Herramientas | Línea | L |
| Herramientas | Mano (Pan) | H |
| Onion | Toggle Onion Skin | O |
| Fondo | Toggle fondo video | Ctrl+B |
| Zoom | Acercar | Ctrl++ |
| Zoom | Alejar | Ctrl+- |
| Zoom | Reset zoom | Ctrl+0 |

> Todos los atajos se resuelven desde `settings.SHORTCUTS`.

## 🧱 Arquitectura Modular

```
rotoscopia/
	__init__.py
	main.py            # Punto de entrada
	canvas.py          # MainWindow, DrawingCanvas, lógica capas/onion/zoom
	tools.py           # Herramientas (Brush, Eraser, Line, Hand) – Strategy
	project.py         # ProjectManager (persistencia overlays/capas, export)
	settings.py        # Constantes + SHORTCUTS centralizados
	utils.py           # Conversión y utilidades (cv2 -> QImage, etc.)
run_modular.bat       # Lanzador Windows
requirements.txt      # Dependencias
exports/              # PNG exportados
projects/             # Proyectos guardados
```

Patrones aplicados:
* Strategy para herramientas (interfaz `on_mouse_press/move/release`)
* Separación de preocupaciones (persistencia, lógica UI, utilidades)

## 🚀 Ejecución

### Opción rápida (Windows)
```
.\n+run_modular.bat
```

### Manual
```powershell
"C:\Users\Ariel\AppData\Local\Programs\Python\Python313\python.exe" -m pip install -r requirements.txt
"C:\Users\Ariel\AppData\Local\Programs\Python\Python313\python.exe" -c "from rotoscopia.main import main; main()"
```

## 🎬 Flujo de Uso Sugerido
1. Abrir video (barra Archivo)
2. Activar Onion si lo necesitas y ajustar opacidad (barra Vista)
3. Crear / seleccionar capa (si procede) y elegir herramienta (barra Herramientas)
4. Dibujar / limpiar / copiar desde frame anterior
5. Navegar frames y repetir (usar atajos Right / Left)
6. Undo / Redo según sea necesario
7. Guardar proyecto periódicamente (Ctrl+Shift+S) o exportar PNG suelto (Ctrl+S)
8. Exportar animación (Ctrl+E) cuando esté listo

## 🔧 Estado Actual
| Área | Estado |
|------|--------|
| Carga de video | Estable |
| Capas por frame | Estable (básico) |
| Herramientas (Brush/Eraser/Line/Hand) | Estable |
| Undo / Redo | Estable |
| Onion Skin (prev/next tintado) | Estable |
| Guardar PNG | Estable |
| Guardar / Cargar proyecto | Estable (incluye capas) |
| Export MP4 / PNG sequence | Estable |
| Zoom anclado + Pan | Estable |
| Shortcuts centralizados | Estable |
| Color / tamaño pincel persistentes | Estable |
| Guardar estado UI adicional (zoom, herramienta) | Pendiente |
| Herramientas nuevas (fill, selección) | Pendiente |

## 🗺️ Próximos Pasos Propuestos
1. Persistir más estado UI (zoom, herramienta activa, toggles onion/fondo)
2. Herramienta de relleno (flood fill) y/o selección
3. Optimización zoom (cache escalados, fast durante rueda -> smooth al soltar)
4. Mejora de gestión de capas: reordenar, bloquear, duplicar
5. HUD de estado: nombre capa activa, % zoom, indicador onion
6. Export presets (fps, escalado, recortes)

## 📝 Notas Técnicas
* Python 3.10+ (probado en 3.13)
* OpenCV: lectura de frames, export MP4 (cv2.VideoWriter)
* Dibujo: QPainter sobre QPixmap RGBA (antialias + CompositionMode_Clear para borrar)
* Undo: pila por frame (lista de QPixmaps)
* Onion Skin: sólo previo y siguiente; tintado por composición `SourceIn` (no afecta export)
* Atajos: centralizados en `settings.SHORTCUTS` para mantenimiento sencillo

## ⚠️ Limitaciones Actuales
* Faltan herramientas avanzadas (relleno, selección, transformación)
* Reordenamiento / bloqueo de capas no implementado
* No se guarda zoom ni herramienta activa en proyecto
* Sin historial cruzado de capas (undo es por pixmap compuesto)
* Sin UI de ayuda integrada (por ahora sólo este README)

## 📄 Licencia
Pendiente de definir (MIT sugerido).

---
*Desarrollado para rotoscopia y animación 2D — 2025*
