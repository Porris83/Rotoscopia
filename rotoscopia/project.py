import json, os
from pathlib import Path
from PySide6 import QtWidgets, QtGui
import numpy as np
from PIL import Image
import cv2

from .settings import PROJECTS_DIR, EXPORT_DIR, MAX_BRUSH_SIZE
from .utils import cvimg_to_qimage, qpixmap_to_pil

# Modos de exportación de fondo
EXPORT_BG_TRANSPARENT = 0
EXPORT_BG_VIDEO = 1
EXPORT_BG_CROMA = 2

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
        self.meta = {}  # almacena la última metadata cargada/guardada
        self.total_frames = 0  # número de frames realmente cargados (tras subsampling)

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
        
        for frame_idx in self.window.frame_layers:
            self.save_frame_layers(frame_idx)
        
        # Fallback: save old overlay system for compatibility
        for idx, pix in self.window.overlays.items():
            if pix is not None and idx not in self.window.frame_layers:
                self.save_project_overlay(idx)
        
        self.write_meta()
        QtWidgets.QMessageBox.information(self.window, "Proyecto", f"Proyecto guardado en {self.window.project_path}")

    def save_frame_layers(self, frame_idx):
        """Save all layers for a specific frame."""
        if not self.window.project_path or frame_idx not in self.window.frame_layers:
            return
        
        layers = self.window.frame_layers[frame_idx]
        if not layers:
            return
        
        # Create frame directory
        frame_dir = self.window.project_path / 'frames' / f'frame_{frame_idx:05d}'
        frame_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each layer
        layer_metadata = []
        for i, layer in enumerate(layers):
            if not layer.pixmap.isNull():
                # Save layer image
                layer_path = frame_dir / f'layer_{i:02d}.png'
                pil = qpixmap_to_pil(layer.pixmap)
                pil.save(str(layer_path))
                
                # Store layer metadata
                layer_metadata.append({
                    'name': layer.name,
                    'visible': layer.visible,
                    'opacity': layer.opacity,
                    'file': f'layer_{i:02d}.png'
                })
        
        # Save layer metadata
        if layer_metadata:
            meta_path = frame_dir / 'layers.json'
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(layer_metadata, f, ensure_ascii=False, indent=2)

    def load_frame_layers(self, frame_idx):
        """Load all layers for a specific frame."""
        if not self.window.project_path:
            return []
        
        frame_dir = self.window.project_path / 'frames' / f'frame_{frame_idx:05d}'
        meta_path = frame_dir / 'layers.json'
        
        if not frame_dir.exists() or not meta_path.exists():
            return []
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                layer_metadata = json.load(f)
        except Exception:
            return []
        
        layers = []
        for layer_info in layer_metadata:
            layer_path = frame_dir / layer_info['file']
            if layer_path.exists():
                qimg = QtGui.QImage(str(layer_path))
                if not qimg.isNull():
                    # Import Layer class locally to avoid circular imports
                    from .canvas import Layer
                    layer = Layer(layer_info['name'], qimg.width(), qimg.height())
                    layer.pixmap = QtGui.QPixmap.fromImage(qimg)
                    layer.visible = layer_info.get('visible', True)
                    layer.opacity = layer_info.get('opacity', 1.0)
                    layers.append(layer)
        
        return layers

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

    def export_animation(self, frames, path=None, fps=12, background_mode: int = EXPORT_BG_VIDEO):
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
            h, w = frame.shape[:2]
            if background_mode == EXPORT_BG_VIDEO:
                bg = frame.copy()  # BGR (3 canales)
            elif background_mode == EXPORT_BG_CROMA:
                bg = np.zeros((h, w, 3), dtype=np.uint8)  # BGR
                bg[:, :] = (0, 255, 0)  # Verde Croma (BGR)
            else:  # EXPORT_BG_TRANSPARENT
                # ¡Esta es la corrección! 4 canales (BGRA)
                bg = np.zeros((h, w, 4), dtype=np.uint8)  # BGRA
            
            if idx in self.window.frame_layers:
                overlay_pix = self.window.compose_layers_for_frame(idx)
            else:
                overlay_pix = self.window.overlays.get(idx)
            
            if overlay_pix is not None and not overlay_pix.isNull():
                qimg = overlay_pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
                w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
                try:
                    bc = qimg.sizeInBytes()
                except AttributeError:
                    bc = qimg.byteCount()
                arr = np.frombuffer(ptr, np.uint8, count=bc).reshape((h, w, 4))
                # Alpha blend manual sobre bg
                if bg.shape[2] == 3:  # El fondo es BGR (Video o Croma)
                    bg_rgba = np.concatenate([bg, np.full((h, w, 1), 255, dtype=np.uint8)], axis=2)
                else:  # El fondo ya es BGRA (Transparente)
                    bg_rgba = bg
                alpha = arr[..., 3:4].astype(np.float32) / 255.0
                inv_alpha = 1.0 - alpha
                # Componer el dibujo (arr) sobre el fondo (bg_rgba)
                bg_rgba[..., :3] = (arr[..., :3].astype(np.float32) * alpha + bg_rgba[..., :3].astype(np.float32) * inv_alpha).astype(np.uint8)
                # Actualizar el canal alpha del fondo SOLO si estábamos en modo transparente
                if background_mode == EXPORT_BG_TRANSPARENT:
                    bg_rgba[..., 3:4] = np.maximum(arr[..., 3:4], bg_rgba[..., 3:4])
            composed.append(bg_rgba if background_mode == EXPORT_BG_TRANSPARENT else bg_rgba[..., :3])
        if path.suffix.lower() == '.mp4':
            h, w = composed[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(path), fourcc, fps, (w,h))
            for img in composed:
                writer.write(img)
            writer.release()
        else:
            out_dir = path
            out_dir.mkdir(exist_ok=True, parents=True)
            for i, img in enumerate(composed):
                if img.shape[2] == 4:  # Es BGRA (transparente)
                    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)).save(str(out_dir / f'frame_{i:05d}.png'))
                else:  # Es BGR (video o croma)
                    Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).save(str(out_dir / f'frame_{i:05d}.png'))

    def write_meta(self):
        if not self.window.project_path:
            return

        frames_with_layers = {}
        for frame_idx, layers in self.window.frame_layers.items():
            if layers:
                frames_with_layers[str(frame_idx)] = {
                    'layer_count': len(layers),
                    'active_layer': getattr(self.window, 'current_layer_idx', 0)
                }

        fps_original = getattr(self.window, 'fps_original', None)
        fps_target = getattr(self.window, 'fps_target', None)
        # Inferir source_type si no existe
        source_type = self.meta.get('source_type') or (
            'image' if (len(self.window.frames) == 1 and fps_original == 1) else 'video'
        )
        meta = {
            "version": 2,
            "video_path": self.window.video_path,
            "frame_width": self.window.frames[0].shape[1] if self.window.frames else None,
            "frame_height": self.window.frames[0].shape[0] if self.window.frames else None,
            "frame_count": len(self.window.frames),
            "fps": fps_target if fps_target else 12,
            "fps_original": fps_original,
            "fps_target": fps_target,
            "source_type": source_type,
            "frames_with_overlay": sorted([i for i,o in self.window.overlays.items() if o is not None]),
            "frames_with_layers": frames_with_layers,
            "settings": {
                "brush_color": self.window.canvas.pen_color.name(QtGui.QColor.HexArgb),
                "brush_size": self.window.canvas.pen_width
            }
        }
        self.meta = meta
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
            self.meta = meta
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, "Error", f"No se pudo leer meta.json: {e}")
            return
        video_path = meta.get('video_path')
        if not video_path or not os.path.exists(video_path):
            QtWidgets.QMessageBox.warning(self.window, "Proyecto", "Recurso original no encontrado. Selecciona manualmente.")
            video_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Recurso del proyecto", "", "Videos/Imagenes (*.mp4 *.mov *.avi *.mkv *.png *.jpg *.jpeg *.bmp)")
            if not video_path:
                return
        source_type = meta.get('source_type')
        ext = Path(video_path).suffix.lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
        frames = []
        if source_type == 'image' or ext in image_exts:
            # Carga de imagen única
            img = cv2.imread(video_path, cv2.IMREAD_COLOR)
            if img is None:
                QtWidgets.QMessageBox.critical(self.window, 'Error', f'No se pudo leer la imagen: {video_path}')
                return
            frames = [img]
            self.window.fps_original = 1
            self.window.fps_target = 1
            source_type = 'image'
        else:
            # Carga de video (con posible subsampling)
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                QtWidgets.QMessageBox.critical(self.window, 'Error', 'No se pudo abrir el video del proyecto.')
                return
            meta_fps_original = meta.get('fps_original')
            meta_fps_target = meta.get('fps_target')
            if meta_fps_original and meta_fps_target:
                fps_original_val = meta_fps_original
                target_fps_val = meta_fps_target if meta_fps_target > 0 else 12
                real_fps = cap.get(cv2.CAP_PROP_FPS) or fps_original_val or 12.0
                if fps_original_val <= 0:
                    fps_original_val = real_fps
                step = max(1, int(round(float(fps_original_val) / max(1,float(target_fps_val)))))
                frame_idx_cap = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if frame_idx_cap % step == 0:
                        frames.append(frame)
                    frame_idx_cap += 1
                self.window.fps_original = int(round(fps_original_val))
                self.window.fps_target = int(round(target_fps_val))
            else:
                # Proyecto antiguo: todos los frames
                fps_original_val = cap.get(cv2.CAP_PROP_FPS) or 12.0
                if fps_original_val <= 0:
                    fps_original_val = 12.0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
                self.window.fps_original = int(round(fps_original_val))
                self.window.fps_target = meta.get('fps', 12)
            cap.release()
            source_type = 'video'
        if not frames:
            QtWidgets.QMessageBox.warning(self.window, 'Proyecto', 'El recurso no contiene frames (tras subsampling).')
            return
        # Actualizar estado de ventana
        self.window.frames = frames
        self.window.video_path = video_path
        self.window.current_frame_idx = 0
        self.window.overlays.clear()
        self.window.frame_layers.clear()
        self.window.undo_stacks.clear()
        self.window.redo_stacks.clear()
        self.window.dirty_frames.clear()
        self.window.project_path = Path(path).parent
        self.window.project_name = self.window.project_path.name
        # Cargar capas (solo si video / multiframe)
        version = meta.get('version', 1)
        if version >= 2 and source_type != 'image' and 'frames_with_layers' in meta:
            for frame_idx_str in meta['frames_with_layers'].keys():
                frame_idx = int(frame_idx_str)
                layers = self.load_frame_layers(frame_idx)
                if layers:
                    self.window.frame_layers[frame_idx] = layers
        # Overlays antiguos
        if source_type != 'image':
            for idx in meta.get('frames_with_overlay', []):
                if idx not in self.window.frame_layers:
                    loaded = self.load_frame(idx)
                    if loaded is not None:
                        self.window.overlays[idx] = loaded
        # Ajustes
        settings = meta.get('settings', {})
        brush_size = settings.get('brush_size')
        if isinstance(brush_size, int):
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
        self.total_frames = len(frames)
        try:
            self.window.canvas.clear_onion_cache()
        except Exception:
            pass
        QtWidgets.QMessageBox.information(self.window, 'Proyecto', f'Proyecto cargado: {self.window.project_name}')

    def load_video(self, video_path: str, target_fps: int = 12):
        """Carga un video (subsampling) o una imagen estática."""
        ext = Path(video_path).suffix.lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
        source_type = 'video'
        if ext in image_exts:
            img = cv2.imread(video_path, cv2.IMREAD_COLOR)
            if img is None:
                QtWidgets.QMessageBox.critical(self.window, 'Error', f'No se pudo leer la imagen:\n{video_path}')
                return False
            frames = [img]
            fps_original = 1.0
            target_fps = 1
            step = 1
            source_type = 'image'
        else:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                QtWidgets.QMessageBox.critical(self.window, 'Error', f'No se pudo abrir el video:\n{video_path}')
                return False
            fps_original = cap.get(cv2.CAP_PROP_FPS) or 12.0
            if fps_original <= 0:
                fps_original = 12.0
            step = max(1, int(round(fps_original / max(1, target_fps))))
            frames = []
            idx_cap = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if idx_cap % step == 0:
                    frames.append(frame)
                idx_cap += 1
            cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self.window, 'Video', f'El recurso no contiene frames.\nRuta: {video_path}')
            return False
        # Estado ventana
        self.window.frames = frames
        self.window.video_path = video_path
        self.window.current_frame_idx = 0
        self.window.overlays.clear()
        self.window.frame_layers.clear()
        self.window.current_layer_idx = 0
        self.window.undo_stacks.clear()
        self.window.redo_stacks.clear()
        self.window.dirty_frames.clear()
        self.window.is_dirty = False
        self.window.fps_original = int(round(fps_original))
        self.window.fps_target = int(target_fps)
        self.total_frames = len(frames)
        self.meta.update({
            'fps_original': self.window.fps_original,
            'fps_target': self.window.fps_target,
            'frame_count': len(frames),
            'source_type': source_type
        })
        h, w = frames[0].shape[:2]
        self.window.canvas.set_size(w, h)
        # Asegurar al menos una capa
        try:
            self.window.ensure_frame_has_layers(0, w, h)
        except Exception:
            pass
        self.window.refresh_view()
        try:
            self.window.canvas.clear_onion_cache()
        except Exception:
            pass
        from pathlib import Path as _P
        if source_type == 'image':
            self.window.statusBar().showMessage(f'Imagen cargada: {_P(video_path).name} (1 frame)', 5000)
        else:
            self.window.statusBar().showMessage(f'Video cargado: {_P(video_path).name} ({len(frames)} frames, fps {fps_original:.1f}→{target_fps}, step={step})', 5000)
        return True
