# Rotoscopia v0.3.2 - Auto-Calco con IA

# Rotoscopia v0.3.1 - Herramientas de Precisión

Esta versión añade la **Línea Dinámica** (polilínea) a las herramientas de precisión y mantiene el robusto sistema de exportación introducido en la v0.3.0.

## 🆕 Nuevas Características

### 🎸 Auto-Calco Marshall - Detección de Bordes Asistida por IA

La herramienta más avanzada de Rotoscopia hasta la fecha. **Auto-Calco** usa algoritmos de visión por computadora (OpenCV Canny Edge Detection) para detectar automáticamente los bordes de tu video y generar un preview en tiempo real.

#### Características Principales:
- **Captura Inteligente del Viewport**: Captura exactamente el área que estás viendo, considerando zoom y scroll
- **Preview en Tiempo Real**: Ve los bordes detectados superpuestos en tu canvas mientras ajustas parámetros
- **Diales Analógicos Estilo Marshall** (1-11):
  - **DETALLE**: Controla la sensibilidad de detección (1=poco detalle, 11=máximo detalle)
  - **LIMPIEZA**: Elimina ruido y componentes pequeños (1=sin limpiar, 11=solo líneas maestras)
- **Integración Total**: Usa el color y grosor del pincel actual
- **Atajo de Teclado**: `Ctrl+Shift+A` para activar rápidamente

#### Flujo de Trabajo:
1. **Posiciona el viewport** en el área que quieres procesar (usa zoom/scroll)
2. **Presiona `Ctrl+Shift+A`** o el botón **📷 CAPTURAR** en el dock
3. **Ajusta los diales** DETALLE y LIMPIEZA hasta obtener el resultado deseado
4. **Presiona `Enter`** o el botón **⚡ PLASMAR** para transferir a la capa activa

#### Tecnología:
- **Motor de Edge Detection** (`AutoCalcoEngine`):
  - Filtrado bilateral para preservar bordes
  - Canny edge detection con umbrales adaptativos
  - Eliminación de componentes pequeños (morfología)
  - Dilatación para grosor de línea
- **Mapeo de Coordenadas Robusto**: Calcula correctamente la región de interés (ROI) considerando:
  - Scroll horizontal/vertical
  - Nivel de zoom
  - Offset de centrado del canvas

### 🏗️ Refactorización de Arquitectura

#### Código Limpio y Modular:
- **Todas las herramientas en `tools.py`**: Auto-Calco ahora vive junto a Brush, Lasso, Pluma, etc.
- **Eliminada carpeta temporal**: NuevaHerramienta integrada completamente
- **Imports limpios**: Sin dependencias de carpetas externas
- **Listo para PyInstaller**: Estructura preparada para empaquetado .exe

#### Mejoras de Seguridad:
- **Validación de ROI**: Previene crashes por coordenadas fuera de límites
- **Verificación de existencia**: Checks de `window_ref`, `frames`, y `roi_rect`
- **Clamp de coordenadas**: Asegura que el crop esté dentro del frame
- **ROI no vacío**: Evita procesamiento de áreas sin dimensiones

### 🐛 Arreglos de Bugs

- **Arreglado**: Captura de viewport ahora funciona correctamente con scroll y zoom
- **Arreglado**: `mapToOverlay()` usa dimensiones del frame actual en vez de overlay
- **Arreglado**: Orden de colores RGB correcto (antes estaba invertido a BGR)
- **Arreglado**: Warning de jerarquía de widgets eliminado

## 🔧 Implementación Técnica

### Nuevas Clases (todas en `tools.py`):
- **`AutoCalcoEngine`**: Motor de procesamiento con OpenCV
  - `detect_edges_roi()`: Procesa ROI con parámetros analógicos
  - `_remove_small_components()`: Limpieza morfológica
- **`AutoCalcoTool`**: Lógica de captura y preview
  - `activate()`: Captura viewport con scroll bars
  - `update_preview()`: Genera preview con validaciones
  - `commit_to_layer()`: Plasma resultado en capa activa
- **`AutoCalcoDock`**: Panel Marshall con diales
  - `_add_knob()`: Crea QDials con validación estricta (anti wrap-around)
  - Botones: 📷 CAPTURAR (celeste) y ⚡ PLASMAR (dorado)

### Modificaciones en archivos existentes:
- **`canvas.py`**:
  - Import de `AutoCalcoTool` y `AutoCalcoDock` desde `tools`
  - Método `activar_auto_calco()`: Muestra dock, activa tool, da foco
  - Atajo `Ctrl+Shift+A` en `_init_ui()`
  - Preview rendering en `paintEvent()`: dibuja `preview_pixmap` en posición ROI
  - `mapToOverlay()` mejorado: usa dimensiones del frame actual
- **`tools.py`**:
  - Imports de `cv2` y `numpy`
  - ~250 líneas nuevas con Auto-Calco completo

## 📦 Preparado para Distribución

### Nuevos Archivos:
- **`build.py`**: Script automático de empaquetado con PyInstaller
- **`BUILD_INSTRUCTIONS.md`**: Guía completa de empaquetado
- **`requirements.txt`**: Dependencias del proyecto

### Empaquetado Simple:
```bash
python build.py
```
Genera `dist/Rotoscopia.exe` listo para distribución.

## 🎯 Resumen de la Versión

La v0.3.2 representa un **salto cuántico** en las capacidades de Rotoscopia:

1. **Auto-Calco**: Primera herramienta asistida por IA para rotoscopia automática
2. **Arquitectura Profesional**: Código modular, limpio y extensible
3. **Listo para Producción**: Validaciones, error handling, y empaquetado
4. **Sin Bugs Conocidos**: Testing exhaustivo con validaciones robustas

Esta versión transforma Rotoscopia de una herramienta de dibujo frame-por-frame a un **sistema híbrido manual/automático** que acelera dramáticamente el workflow de rotoscopia profesional.

---

## 🔗 Compatibilidad

- **Python**: 3.8+
- **Sistema Operativo**: Windows (primary), Linux, macOS
- **Dependencias**:
  - PySide6 >= 6.5.0
  - opencv-python >= 4.8.0
  - numpy >= 1.24.0
  - Pillow >= 10.0.0

## 📚 Documentación

- Ver `MANUAL_USUARIO.md` para guía de uso

---

**¡Rotoscopia v0.3.2 -!
