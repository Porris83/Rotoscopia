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

# Atajos de teclado centralizados
SHORTCUTS = {
    'next_frame': 'Right',
    'prev_frame': 'Left',
    'save_overlay': 'Ctrl+S',
    'undo': 'Ctrl+Z',
    'redo': 'Ctrl+Y',
    'toggle_eraser': 'E',
    'toggle_onion': 'O',
    'zoom_in': '+',
    'zoom_out': '-',
}

# Alias retro-compatibilidad (antiguos nombres usados en código previo)
EXPORT_DIR = EXPORTS_DIR  # evitar romper imports existentes
