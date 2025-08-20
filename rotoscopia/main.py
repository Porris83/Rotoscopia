"""Punto de entrada de la aplicación de rotoscopia.

Ejecución recomendada (como paquete):
    python -m rotoscopia.main

También soporta ejecución directa del archivo:
    python rotoscopia/main.py
"""

import sys
import os
from PySide6 import QtWidgets

# Agregar el directorio padre al path para imports cuando se ejecuta directamente
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import que funciona tanto como módulo como script directo
try:
    from .canvas import MainWindow  # Import relativo (cuando se ejecuta como módulo)
except ImportError:
    from rotoscopia.canvas import MainWindow  # Import absoluto (cuando se ejecuta directamente)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # permite ejecución directa del archivo
    # Ajusta sys.path si fuera necesario cuando se ejecuta directamente
    # (normalmente Python añade el directorio raíz del proyecto, por lo que
    # los imports relativos funcionan al estar dentro de un paquete con __init__).
    main()
