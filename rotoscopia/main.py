import sys
from PySide6 import QtWidgets

try:
    from .canvas import MainWindow
except ImportError:
    # fallback if run directly "python rotoscopia/main.py"
    from canvas import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
