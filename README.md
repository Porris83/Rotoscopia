# Rotoscopia MVP (Modular)

Herramienta de rotoscopia manual para crear sprites desde video (inspiración: Prince of Persia). Ahora refactorizada a arquitectura modular con sistema de herramientas extensible.

## 🎯 Objetivo
Extraer y dibujar siluetas / animaciones cuadro a cuadro para pipelines de pixel‑art o cleanup 2D.

## ✅ Funcionalidades Actuales

### Core
* Carga de video (MP4, MOV, AVI, MKV)
* Navegación frame a frame (botones + ← →)
* Onion skin (frame anterior con opacidad configurable)
* Opacidad del fondo ajustable / ocultar fondo
* Zoom con rueda (limitado por min/max) + desplazamiento (pan) con botón medio/derecho

### Herramientas (Strategy Pattern en `rotoscopia/tools.py`)
* Pincel (suave, antialias)
* Borrador (usa CompositionMode_Clear)
* Línea (vista previa dinámica antes de soltar)
* Cambio rápido vía botones o atajos (E para alternar borrar, próximamente más)

### Edición / Historial
* Undo / Redo por frame (Ctrl+Z / Ctrl+Y) con límite configurable (`MAX_HISTORY`)
* Copiar dibujo del frame anterior
* Limpiar frame actual

### Exportación
* Guardar overlay actual a PNG con transparencia (carpeta `EXPORT/` manejada automáticamente)
* Estructura preparada para batch export posterior

### Proyectos
* Guardado / carga de proyecto (metadatos + overlays individuales)
* Al cambiar de frame guarda automáticamente overlays sucios dentro del proyecto

### Atajos Principales
| Acción | Atajo |
|--------|-------|
| Frame siguiente / anterior | → / ← |
| Guardar frame (PNG) | Ctrl+S |
| Undo / Redo | Ctrl+Z / Ctrl+Y |
| Toggle Onion | O |
| Alternar goma (rápido) | E |
| Zoom in / out | + / - |

## 🧱 Arquitectura Modular

```
rotoscopia/
	__init__.py
	main.py          # Entry point (main())
	canvas.py        # UI principal: MainWindow + DrawingCanvas
	tools.py         # Clases de herramienta (BrushTool, EraserTool, LineTool)
	project.py       # ProjectManager (guardar/cargar overlays + meta)
	settings.py      # Constantes y paths (EXPORT_DIR, PROJECTS_DIR, etc.)
	utils.py         # Conversión cv2 -> QImage, helpers
rotoscopia-mejoras.py  # Versión monolítica original (referencia)
run_modular.bat        # Lanzador conveniente Windows
requirements.txt       # Dependencias
EXPORT/                # Salidas PNG (auto)
PROJECTS/              # Proyectos guardados
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

## 🎬 Flujo de Uso Básico
1. Abrir video
2. (Opcional) Activar Onion y ajustar opacidad
3. Seleccionar herramienta (Pincel / Línea / Borrar)
4. Dibujar frame 1
5. Copiar anterior o avanzar y dibujar variaciones
6. Undo/Redo según necesidad
7. Guardar PNG (o guardar proyecto para continuar luego)

## 🔧 Estado Actual
| Módulo | Estado |
|--------|--------|
| Carga video | Estable |
| Herramientas (brush/eraser/line) | Estable |
| Undo/Redo | Estable |
| Onion skin | Estable |
| Guardar PNG | Estable |
| Guardar/Cargar proyecto | Funcional (básico) |
| Zoom / Pan | Estable |
| Batch export de todos los frames | Pendiente |
| Tool extra (bucket/fill) | Pendiente |
| Guardar estado UI (zoom/herramienta) en proyecto | Pendiente |

## 🗺️ Próximos Pasos Propuestos
1. Exportación masiva (todas las capas no vacías)
2. Persistir herramienta activa y zoom en metadata
3. Herramienta de relleno (flood fill sobre overlay RGBA)
4. Mejora de rendimiento: snapshot undo diferido para herramienta brush (solo al terminar stroke largo)
5. Vista previa porcentaje de zoom en barra superior

## 📝 Notas Técnicas
* Python 3.10+ recomendado (probado en 3.13 local)
* OpenCV solo se usa para lectura de frames (no altera colores al exportar)
* Dibujo sobre `QPixmap` RGBA con composición limpia para el borrador
* Onion: mezcla frame anterior + tintado opcional (overlay violeta ligero)

## ⚠️ Limitaciones Actuales
* Sin multi-layer (solo una capa de dibujo por ahora)
* Sin selección / mover trazos
* Exportación manual por frame

## 📄 Licencia
Pendiente de definir (MIT sugerido).

---
*Desarrollado para rotoscopia de sprites de videojuegos — 2025*
