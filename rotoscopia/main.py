"""Punto de entrada de la aplicación de rotoscopia.

Ejecución recomendada (como paquete):
    python -m rotoscopia.main

También soporta ejecución directa del archivo:
    python rotoscopia/main.py
"""

import sys
from PySide6 import QtWidgets

from .canvas import MainWindow


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
