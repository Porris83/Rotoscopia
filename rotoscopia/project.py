import json, os
from pathlib import Path
from PySide6 import QtWidgets, QtGui
import numpy as np
from PIL import Image
import cv2

from .settings import PROJECTS_DIR, EXPORT_DIR, MAX_BRUSH_SIZE
from .utils import cvimg_to_qimage, qpixmap_to_pil

class ProjectManager:
    """Centraliza toda la lógica de manejo de archivos del proyecto y exportaciones.

    Responsabilidades:
    - Guardar/cargar overlays dentro de un proyecto (carpeta frames/).
    - Guardar frames sueltos en la carpeta global de exports/.
    - Exportar una animación compuesta (video o secuencia) desde las capas existentes.
    - Persistir metadatos (meta.json).
    """

    def __init__(self, window):
        self.window = window  # referencia a MainWindow

    def save_project_dialog(self):
        if not self.window.frames:
            QtWidgets.QMessageBox.information(self.window, "Info", "Carga un video antes de guardar un proyecto.")
            return
        name, ok = QtWidgets.QInputDialog.getText(self.window, "Nombre del Proyecto", "Nombre:")
        if not ok or not name.strip():
            return
        self.window.project_name = name.strip()
        self.window.project_path = PROJECTS_DIR / self.window.project_name
        (self.window.project_path / 'frames').mkdir(parents=True, exist_ok=True)
        for idx, pix in self.window.overlays.items():
            if pix is not None:
                self.save_project_overlay(idx)
        self.write_meta()
        QtWidgets.QMessageBox.information(self.window, "Proyecto", f"Proyecto guardado en {self.window.project_path}")

    # --- Proyecto (persistencia interna) ---
    def save_project_overlay(self, idx):
        """Guarda el overlay de un frame dentro de la carpeta del proyecto.

        Se usa para autosave y guardado manual del proyecto.
        """
        if not self.window.project_path:
            return
        pix = self.window.overlays.get(idx)
        if pix is None:
            return
        pil = qpixmap_to_pil(pix)
        out_dir = self.window.project_path / 'frames'
        out_dir.mkdir(exist_ok=True, parents=True)
        out_path = out_dir / f"frame_{idx:05d}.png"
        pil.save(str(out_path))

    def load_frame(self, frame_index):
        """Carga (solo overlay) desde frames/ del proyecto actual.

        Devuelve QPixmap o None.
        """
        if not self.window.project_path:
            return None
        frame_file = self.window.project_path / 'frames' / f"frame_{frame_index:05d}.png"
        if not frame_file.exists():
            return None
        qimg = QtGui.QImage(str(frame_file))
        if qimg.isNull():
            return None
        return QtGui.QPixmap.fromImage(qimg)

    # --- Exportaciones externas ---
    def save_frame(self, frame_index, image):
        """Guarda un overlay suelto como PNG en exports/ (equivalente al antiguo Guardar PNG).

        image puede ser QPixmap, QImage, PIL.Image, ndarray (RGBA o RGB) para flexibilidad.
        """
        EXPORT_DIR.mkdir(exist_ok=True, parents=True)
        out_path = EXPORT_DIR / f"frame_{frame_index:05d}.png"
        try:
            if isinstance(image, QtGui.QPixmap):
                pil = qpixmap_to_pil(image)
            elif isinstance(image, QtGui.QImage):
                pix = QtGui.QPixmap.fromImage(image)
                pil = qpixmap_to_pil(pix)
            elif isinstance(image, Image.Image):
                pil = image
            else:
                # asumimos ndarray
                arr = np.asarray(image)
                if arr.ndim == 3 and arr.shape[2] == 3:
                    pil = Image.fromarray(arr, mode='RGB')
                elif arr.ndim == 3 and arr.shape[2] == 4:
                    pil = Image.fromarray(arr, mode='RGBA')
                else:
                    raise ValueError('Formato de array no soportado para guardar PNG')
            pil.save(str(out_path))
            QtWidgets.QMessageBox.information(self.window, 'Guardado', f'Guardado {out_path}')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, 'Error', f'Error al guardar: {e}')

    def export_animation(self, frames, path=None, fps=12, include_background=True):
        """Exporta una animación combinando frames base y overlays.

        Si path termina en .mp4 exporta video, en caso contrario exporta secuencia PNG en carpeta.
        Si no se pasa path, se genera uno por defecto en exports/.
        """
        if not frames:
            QtWidgets.QMessageBox.information(self.window, 'Exportar', 'No hay frames para exportar.')
            return
        EXPORT_DIR.mkdir(exist_ok=True, parents=True)
        if path is None:
            base_name = (self.window.project_name or 'animacion') + '.mp4'
            path = EXPORT_DIR / base_name
        path = Path(path)
        # Preparamos composición
        composed = []
        for idx, frame in enumerate(frames):
            bg = frame.copy() if include_background else np.zeros_like(frame)
            overlay_pix = self.window.overlays.get(idx)
            if overlay_pix is not None:
                qimg = overlay_pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
                w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
                try:
                    bc = qimg.sizeInBytes()
                except AttributeError:
                    bc = qimg.byteCount()
                arr = np.frombuffer(ptr, np.uint8, count=bc).reshape((h, w, 4))
                # Alpha blend manual sobre bg (BGR) => convert to BGRA
                if bg.shape[2] == 3:
                    bg_rgba = np.concatenate([bg, np.full((h,w,1),255,dtype=np.uint8)], axis=2)
                else:
                    bg_rgba = bg
                alpha = arr[...,3:4].astype(np.float32)/255.0
                inv_alpha = 1.0 - alpha
                bg_rgba[...,:3] = (arr[...,:3].astype(np.float32)*alpha + bg_rgba[...,:3].astype(np.float32)*inv_alpha).astype(np.uint8)
                bg = bg_rgba[...,:3]
            composed.append(bg)
        if path.suffix.lower() == '.mp4':
            h, w = composed[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(path), fourcc, fps, (w,h))
            for img in composed:
                writer.write(img)
            writer.release()
            QtWidgets.QMessageBox.information(self.window, 'Exportar', f'Video exportado: {path}')
        else:
            out_dir = path
            out_dir.mkdir(exist_ok=True, parents=True)
            for i,img in enumerate(composed):
                Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(str(out_dir / f'frame_{i:05d}.png'))
            QtWidgets.QMessageBox.information(self.window, 'Exportar', f'Secuencia exportada en: {out_dir}')

    def write_meta(self):
        if not self.window.project_path:
            return
        meta = {
            "version": 1,
            "video_path": self.window.video_path,
            "frame_width": self.window.frames[0].shape[1] if self.window.frames else None,
            "frame_height": self.window.frames[0].shape[0] if self.window.frames else None,
            "frame_count": len(self.window.frames),
            "fps": 12,
            "frames_with_overlay": sorted([i for i,o in self.window.overlays.items() if o is not None]),
            "settings": {
                "brush_color": self.window.canvas.pen_color.name(QtGui.QColor.HexArgb),
                "brush_size": self.window.canvas.pen_width
            }
        }
        tmp_path = self.window.project_path / 'meta.tmp'
        final_path = self.window.project_path / 'meta.json'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, final_path)

    def load_project_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Seleccionar meta.json", str(PROJECTS_DIR), "meta.json (meta.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, "Error", f"No se pudo leer meta.json: {e}")
            return
        video_path = meta.get('video_path')
        if not video_path or not os.path.exists(video_path):
            QtWidgets.QMessageBox.warning(self.window, "Proyecto", "Video original no encontrado. Selecciona manualmente.")
            video_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Video del proyecto", "", "Videos (*.mp4 *.mov *.avi *.mkv)")
            if not video_path:
                return
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self.window, "Error", "No se pudo abrir el video del proyecto.")
            return
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self.window, "Proyecto", "El video no contiene frames.")
            return
        self.window.frames = frames
        self.window.video_path = video_path
        self.window.current_frame_idx = 0
        self.window.overlays.clear()
        self.window.undo_stacks.clear()
        self.window.redo_stacks.clear()
        self.window.dirty_frames.clear()
        self.window.project_path = Path(path).parent
        self.window.project_name = self.window.project_path.name
        frames_with_overlay = meta.get('frames_with_overlay', [])
        for idx in frames_with_overlay:
            loaded = self.load_frame(idx)
            if loaded is not None:
                self.window.overlays[idx] = loaded
        settings = meta.get('settings', {})
        brush_size = settings.get('brush_size')
        if isinstance(brush_size, int):
            # clamp usando constante centralizada
            clamped = max(1, min(MAX_BRUSH_SIZE, brush_size))
            self.window.brush_slider.setValue(clamped)
            self.window.canvas.pen_width = clamped
        brush_color = settings.get('brush_color')
        if brush_color:
            col = QtGui.QColor(brush_color)
            if col.isValid():
                self.window.canvas.pen_color = col
        h, w = self.window.frames[0].shape[:2]
        self.window.canvas.set_size(w, h)
        self.window.refresh_view()
        QtWidgets.QMessageBox.information(self.window, "Proyecto", f"Proyecto cargado: {self.window.project_name}")
