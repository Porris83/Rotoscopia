import sys
import os
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)


def cvimg_to_qimage(cv_img):
    """Convert BGR/uint8 image (OpenCV) to QImage"""
    if cv_img is None:
        return None
    h, w = cv_img.shape[:2]
    if cv_img.ndim == 2:
        fmt = QtGui.QImage.Format_Grayscale8
        qimg = QtGui.QImage(cv_img.data, w, h, cv_img.strides[0], fmt)
        return qimg.copy()
    if cv_img.shape[2] == 3:
        cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        qimg = QtGui.QImage(cv_img_rgb.data, w, h, cv_img_rgb.strides[0], QtGui.QImage.Format_RGB888)
        return qimg.copy()
    if cv_img.shape[2] == 4:
        cv_img_rgba = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        qimg = QtGui.QImage(cv_img_rgba.data, w, h, cv_img_rgba.strides[0], QtGui.QImage.Format_RGBA8888)
        return qimg.copy()
    return None


class DrawingCanvas(QtWidgets.QLabel):
    """Canvas con fixes Fase 1: cursor alineado y fondo persistente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pen_width = 3
        self.pen_color = QtGui.QColor(0, 0, 0, 255)
        self._drawing = False
        self.last_point = None
        self.overlay = None
        self.mode = "draw"
        self.current_background = None
        self.current_opacity = 0.5

    def set_size(self, w, h):
        if self.overlay is None or self.overlay.size() != QtCore.QSize(w, h):
            pix = QtGui.QPixmap(w, h)
            pix.fill(QtCore.Qt.transparent)
            self.overlay = pix
            self.setPixmap(QtGui.QPixmap(w, h))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.overlay is not None:
            self._drawing = True
            try:
                self.last_point = self.mapToOverlay(event.position().toPoint())
            except AttributeError:
                self.last_point = self.mapToOverlay(event.pos())

    def mouseMoveEvent(self, event):
        if self._drawing and self.overlay is not None:
            try:
                p = self.mapToOverlay(event.position().toPoint())
            except AttributeError:
                p = self.mapToOverlay(event.pos())
            painter = QtGui.QPainter(self.overlay)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pen = QtGui.QPen(self.pen_color, self.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setPen(pen)
            if self.last_point is not None:
                painter.drawLine(self.last_point, p)
            painter.end()
            self.last_point = p
            self.update_display()

    def mapToOverlay(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """Map widget coordinates to overlay coordinates accounting for scaling and centering.
        This replicates the Phase 1 fix ensuring cursor alignment after resize/fit.
        """
        if self.overlay is None:
            return point
        current_pixmap = self.pixmap()
        if current_pixmap is None:
            return point
        widget_size = self.size()
        pixmap_size = current_pixmap.size()
        overlay_size = self.overlay.size()
        # scaling factors
        scale_x = overlay_size.width() / pixmap_size.width() if pixmap_size.width() > 0 else 1.0
        scale_y = overlay_size.height() / pixmap_size.height() if pixmap_size.height() > 0 else 1.0
        # offsets (pixmap centered in label)
        offset_x = (widget_size.width() - pixmap_size.width()) / 2
        offset_y = (widget_size.height() - pixmap_size.height()) / 2
        mapped_x = (point.x() - offset_x) * scale_x
        mapped_y = (point.y() - offset_y) * scale_y
        return QtCore.QPoint(int(mapped_x), int(mapped_y))

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drawing = False

    def clear_overlay(self):
        if self.overlay is not None:
            self.overlay.fill(QtCore.Qt.transparent)
            self.update_display()

    def update_display(self, background_pixmap=None, opacity=0.5):
        if background_pixmap is not None:
            self.current_background = background_pixmap
            self.current_opacity = opacity
        bg = background_pixmap or self.current_background
        op = opacity if background_pixmap is not None else self.current_opacity
        if bg is None:
            if self.overlay is not None:
                comp = QtGui.QPixmap(self.overlay.size())
                comp.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter(comp)
                p.drawPixmap(0, 0, self.overlay)
                p.end()
                self.setPixmap(comp)
            return
        comp = QtGui.QPixmap(bg.size())
        comp.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(comp)
        p.setOpacity(op)
        p.drawPixmap(0, 0, bg)
        p.setOpacity(1.0)
        if self.overlay is not None:
            p.drawPixmap(0, 0, self.overlay)
        p.end()
        self.setPixmap(comp)

    def get_overlay_image(self):
        if self.overlay is None:
            return None
        return self.overlay.toImage()

    def set_overlay_from_image(self, qimg):
        if qimg is None:
            return
        pix = QtGui.QPixmap.fromImage(qimg)
        self.overlay = pix
        self.update_display()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rotoscopia MVP")
        self.resize(1000, 700)

        self.frames = []  # list of BGR numpy arrays
        self.current_frame_idx = 0
        self.video_path = None

        # UI
        open_btn = QtWidgets.QPushButton("Abrir video")
        open_btn.clicked.connect(self.open_video)

        self.prev_btn = QtWidgets.QPushButton("<<")
        self.prev_btn.clicked.connect(self.prev_frame)
        self.next_btn = QtWidgets.QPushButton(">>")
        self.next_btn.clicked.connect(self.next_frame)

        self.copy_prev_btn = QtWidgets.QPushButton("Copiar anterior")
        self.copy_prev_btn.clicked.connect(self.copy_previous_overlay)

        self.save_btn = QtWidgets.QPushButton("Guardar PNG")
        self.save_btn.clicked.connect(self.save_current_overlay)

        self.clear_btn = QtWidgets.QPushButton("Limpiar")
        self.clear_btn.clicked.connect(self.clear_current_overlay)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.refresh_view)

        self.frame_label = QtWidgets.QLabel("Frame: 0 / 0")

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(open_btn)
        top_layout.addWidget(self.prev_btn)
        top_layout.addWidget(self.next_btn)
        top_layout.addWidget(self.copy_prev_btn)
        top_layout.addWidget(self.clear_btn)
        top_layout.addWidget(self.save_btn)
        top_layout.addWidget(QtWidgets.QLabel("Opacidad fondo"))
        top_layout.addWidget(self.opacity_slider)
        top_layout.addWidget(self.frame_label)

        container = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(container)
        main_layout.addLayout(top_layout)

        # Canvas area
        self.canvas = DrawingCanvas()
        self.canvas.setAlignment(QtCore.Qt.AlignCenter)
        self.canvas.setMinimumSize(640, 480)
        self.canvas.setStyleSheet("border: 1px solid black; background-color: white;")

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        main_layout.addWidget(scroll)

        self.setCentralWidget(container)

        # storage for per-frame overlays (QPixmap)
        self.overlays = {}

        # shortcuts
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Right), self, activated=self.next_frame)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Left), self, activated=self.prev_frame)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, activated=self.save_current_overlay)

    def open_video(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Abrir video", "", "Videos (*.mp4 *.mov *.avi *.mkv)")
        if not path:
            return
        self.video_path = path
        self.load_frames(path)
        if len(self.frames) == 0:
            QtWidgets.QMessageBox.warning(self, "Error", "No se pudieron leer frames del video.")
            return
        self.current_frame_idx = 0
        self.overlays = {}
        h, w = self.frames[0].shape[:2]
        self.canvas.set_size(w, h)
        self.refresh_view()

    def load_frames(self, path):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self, "Error", "No se pudo abrir el video")
            return
        self.frames = []
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Cargando {total} frames...")
        # Extraemos todos los frames a memoria. Para clips largos cambiar a lectura por demanda.
        for i in range(total):
            ret, frame = cap.read()
            if not ret:
                break
            self.frames.append(frame.copy())
        cap.release()
        self.frame_label.setText(f"Frame: 1 / {len(self.frames)}")
        print(f"Cargados {len(self.frames)} frames")

    def refresh_view(self):
        if not self.frames:
            return
        idx = self.current_frame_idx
        frame = self.frames[idx]
        qimg = cvimg_to_qimage(frame)
        if qimg is None:
            return
            
        bg_pix = QtGui.QPixmap.fromImage(qimg)
        # ensure canvas overlay has right size
        self.canvas.set_size(bg_pix.width(), bg_pix.height())
        
        # restore overlay if exists
        if idx in self.overlays:
            self.canvas.overlay = self.overlays[idx]
        else:
            # keep existing overlay pixmap (blank) but associate to this idx
            if self.canvas.overlay is None:
                self.canvas.set_size(bg_pix.width(), bg_pix.height())
            # do not overwrite canvas.overlay here: keep current transparent pixmap
            self.overlays[idx] = self.canvas.overlay
            
        opacity = self.opacity_slider.value() / 100.0
        self.canvas.update_display(background_pixmap=bg_pix, opacity=opacity)
        self.frame_label.setText(f"Frame: {idx + 1} / {len(self.frames)}")

    def next_frame(self):
        if not self.frames:
            return
        # save current overlay into overlays dict
        self.store_current_overlay()
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            # set canvas overlay to the stored overlay if exists
            if self.current_frame_idx in self.overlays and self.overlays[self.current_frame_idx] is not None:
                self.canvas.overlay = self.overlays[self.current_frame_idx]
            else:
                # create fresh transparent overlay with same size
                w = self.canvas.overlay.width() if self.canvas.overlay else self.frames[0].shape[1]
                h = self.canvas.overlay.height() if self.canvas.overlay else self.frames[0].shape[0]
                pix = QtGui.QPixmap(w, h)
                pix.fill(QtCore.Qt.transparent)
                self.canvas.overlay = pix
            self.refresh_view()

    def prev_frame(self):
        if not self.frames:
            return
        self.store_current_overlay()
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            if self.current_frame_idx in self.overlays and self.overlays[self.current_frame_idx] is not None:
                self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.refresh_view()

    def store_current_overlay(self):
        if self.canvas.overlay is not None:
            # store a copy
            self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)

    def copy_previous_overlay(self):
        if self.current_frame_idx == 0:
            QtWidgets.QMessageBox.information(self, "Info", "No hay frame anterior para copiar.")
            return
        prev_idx = self.current_frame_idx - 1
        if prev_idx in self.overlays and self.overlays[prev_idx] is not None:
            self.canvas.overlay = QtGui.QPixmap(self.overlays[prev_idx])
            self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)
            self.refresh_view()
        else:
            QtWidgets.QMessageBox.information(self, "Info", "No hay overlay en el frame anterior para copiar.")

    def clear_current_overlay(self):
        """Clear the current frame's overlay"""
        self.canvas.clear_overlay()
        if self.current_frame_idx in self.overlays:
            del self.overlays[self.current_frame_idx]

    def save_current_overlay(self):
        if not self.frames:
            return
        self.store_current_overlay()
        idx = self.current_frame_idx
        overlay_pix = self.overlays.get(idx)
        if overlay_pix is None:
            QtWidgets.QMessageBox.information(self, "Info", "Overlay vacío: nada para guardar en este frame.")
            return
        try:
            qimg = overlay_pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
            w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
            try:
                byte_count = qimg.sizeInBytes()
            except AttributeError:
                byte_count = qimg.byteCount()
            arr = np.frombuffer(ptr, np.uint8, count=byte_count).reshape((h, w, 4)).copy()
            pil = Image.fromarray(arr, mode="RGBA")
            out_path = EXPORT_DIR / f"frame_{idx:05d}.png"
            pil.save(str(out_path))
            QtWidgets.QMessageBox.information(self, "Guardado", f"Guardado {out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al guardar: {e}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
