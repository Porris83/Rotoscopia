from pathlib import Path

# Directorios base
BASE_DIR = Path(__file__).resolve().parent.parent
EXPORT_DIR = BASE_DIR / 'exports'
PROJECTS_DIR = BASE_DIR / 'projects'
EXPORT_DIR.mkdir(exist_ok=True)
PROJECTS_DIR.mkdir(exist_ok=True)

# Valores por defecto
DEFAULT_ONION_OPACITY = 0.3
DEFAULT_BG_OPACITY = 0.5
DEFAULT_BRUSH_SIZE = 3
DEFAULT_ZOOM_MIN = 0.25
DEFAULT_ZOOM_MAX = 6.0
MAX_HISTORY = 20

# Atajos (pueden usarse más tarde para centralizar)
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
