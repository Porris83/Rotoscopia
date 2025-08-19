from pathlib import Path
from PySide6.QtCore import Qt

BASE_DIR = Path(__file__).resolve().parent.parent

# Nombres de directorios
PROJECTS_DIR_NAME = "projects"
EXPORTS_DIR_NAME = "exports"

# Rutas de directorios (usadas por el código)
PROJECTS_DIR = BASE_DIR / PROJECTS_DIR_NAME
EXPORTS_DIR = BASE_DIR / EXPORTS_DIR_NAME
PROJECTS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Valores por defecto centralizados
DEFAULT_ONION_OPACITY = 0.3
DEFAULT_BG_OPACITY = 0.5
DEFAULT_BRUSH_SIZE = 3
DEFAULT_BRUSH_COLOR = Qt.black  # QColor base para pincel
MAX_BRUSH_SIZE = 50
DEFAULT_ZOOM_MIN = 0.25
DEFAULT_ZOOM_MAX = 6.0
MAX_HISTORY = 20

# Paleta de colores por defecto (hex)
PALETTE_COLORS = ['#000000', '#FFFFFF', '#FF0000', '#0066FF', '#00AA00']

# Tools defaults
BUCKET_TOLERANCE = 30  # flood fill color similarity (0 = exact match, higher = looser)
ALPHA_PASS = 10        # píxeles con alpha <= 10 se consideran "vacío" para flood sobre transparencias

# Atajos de teclado centralizados
SHORTCUTS = {
    # Navegación de frames
    "next_frame": "Right",
    "prev_frame": "Left",
    "copy_prev_frame": "Ctrl+D",  # copiar dibujo/capas del frame anterior

    # Guardado y exportación
    "save_overlay": "Ctrl+S",
    "save_project": "Ctrl+Shift+S",
    "export_animation": "Ctrl+E",

    # Undo / Redo
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Shift+Z",

    # Herramientas principales (selección directa)
    "brush_tool": "B",
    "eraser_tool": "E",
    # Reasignado: Line pasa a Shift+L para liberar 'L' para Lazo
    "line_tool": "Shift+L",
    "lasso_tool": "L",
    "hand_tool": "H",
    "bucket_tool": "G",
    # Nuevas herramientas geométricas
    "rectangle_tool": "R",
    "ellipse_tool": "C",  # 'C' de círculo (Shift mantiene proporción 1:1)
    # Modos de pincel (cuando herramienta pincel activa)
    "brush_mode_1": "1",
    "brush_mode_2": "2",
    "brush_mode_3": "3",
    # Modos de borrador (cuando herramienta borrador activa)
    "eraser_mode_1": "Ctrl+1",
    "eraser_mode_2": "Ctrl+2",
    "eraser_mode_3": "Ctrl+3",

    # Operaciones de selección (Lasso)
    "copy_selection": "Ctrl+C",
    "paste_selection": "Ctrl+V",
    "invert_selection": "Ctrl+Shift+I",
    "select_all": "Ctrl+A",

    # Onion skin
    "toggle_onion": "O",

    # Fondo (video)
    "toggle_background": "Ctrl+B",

    # Zoom
    "zoom_in": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "reset_zoom": "Ctrl+0",
}

# Alias retro-compatibilidad (antiguos nombres usados en código previo)
EXPORT_DIR = EXPORTS_DIR  # evitar romper imports existentes
