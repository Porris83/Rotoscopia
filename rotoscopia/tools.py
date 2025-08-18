from PySide6 import QtCore, QtGui, QtWidgets

class BaseTool:
    name = "base"
    requires_snapshot = True  # usado por canvas para decidir si toma undo al presionar

    def __init__(self, canvas):
        self.canvas = canvas

    # Helpers comunes
    def _overlay_point(self, event):
        try:
            p = event.position().toPoint()
        except AttributeError:
            p = event.pos()
        return self.canvas.mapToOverlay(p)

    def _get_active_layer_pixmap(self):
        """Get the pixmap of the active layer for drawing operations."""
        if not self.canvas.window_ref:
            return self.canvas.overlay
        
        active_layer = self.canvas.window_ref.get_active_layer()
        if active_layer:
            return active_layer.pixmap
        
        # Fallback to canvas overlay if no active layer
        return self.canvas.overlay

    def _update_after_draw(self):
        """Update display after drawing operation."""
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'compose_layers'):
            self.canvas.window_ref.compose_layers()
        else:
            self.canvas.update_display()

    # Nuevas firmas solicitadas
    def on_mouse_press(self, event):
        pass

    def on_mouse_move(self, event):
        pass

    def on_mouse_release(self, event):
        pass

class BrushTool(BaseTool):
    name = "brush"

    def on_mouse_press(self, event):
        self.canvas.last_point = self._overlay_point(event)

    def on_mouse_move(self, event):
        target_pixmap = self._get_active_layer_pixmap()
        if target_pixmap is None:
            return
            
        pt = self._overlay_point(event)
        if self.canvas.last_point is None:
            self.canvas.last_point = pt
            
        painter = QtGui.QPainter(target_pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.canvas.last_point, pt)
        painter.end()
        
        self.canvas.last_point = pt
        self._update_after_draw()

    def on_mouse_release(self, event):
        self.canvas.last_point = None

class EraserTool(BaseTool):
    name = "eraser"

    def on_mouse_press(self, event):
        self.canvas.last_point = self._overlay_point(event)

    def on_mouse_move(self, event):
        target_pixmap = self._get_active_layer_pixmap()
        if target_pixmap is None:
            return
            
        pt = self._overlay_point(event)
        if self.canvas.last_point is None:
            self.canvas.last_point = pt
            
        painter = QtGui.QPainter(target_pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
        pen = QtGui.QPen(QtGui.QColor(0,0,0,0), self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.canvas.last_point, pt)
        painter.end()
        
        self.canvas.last_point = pt
        self._update_after_draw()

    def on_mouse_release(self, event):
        self.canvas.last_point = None

class LineTool(BaseTool):
    name = "line"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._start = None
        self._base = None

    def on_mouse_press(self, event):
        self._start = self._overlay_point(event)
        target_pixmap = self._get_active_layer_pixmap()
        self._base = QtGui.QPixmap(target_pixmap) if target_pixmap else None

    def on_mouse_move(self, event):
        if self._start is None or self._base is None:
            return
            
        target_pixmap = self._get_active_layer_pixmap()
        if target_pixmap is None:
            return
            
        pt = self._overlay_point(event)
        temp = QtGui.QPixmap(self._base)
        painter = QtGui.QPainter(temp)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self._start, pt)
        painter.end()
        
        # Update the active layer with preview
        if self.canvas.window_ref:
            active_layer = self.canvas.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap = temp
        else:
            self.canvas.overlay = temp
            
        self._update_after_draw()

    def on_mouse_release(self, event):
        if self._start is None or self._base is None:
            self._start = None; self._base = None; return
            
        pt = self._overlay_point(event)
        painter = QtGui.QPainter(self._base)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self._start, pt)
        painter.end()
        
        # Update the active layer with final result
        if self.canvas.window_ref:
            active_layer = self.canvas.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap = self._base
        else:
            self.canvas.overlay = self._base
            
        self._update_after_draw()
        self._start = None; self._base = None

class HandTool(BaseTool):
    name = "hand"
    requires_snapshot = False  # No modifica el lienzo

    def __init__(self, canvas):
        super().__init__(canvas)
        self.dragging = False
        self.last_pos = None
        self.original_cursor = None

    def activate(self):
        """Cambiar cursor a mano abierta al activar."""
        self.original_cursor = self.canvas.cursor()
        self.canvas.setCursor(QtCore.Qt.OpenHandCursor)

    def deactivate(self):
        """Restaurar cursor original al desactivar."""
        if self.original_cursor is not None:
            self.canvas.setCursor(self.original_cursor)
        self.dragging = False
        self.last_pos = None

    def on_mouse_press(self, event):
        """Iniciar pan con botón izquierdo."""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            if hasattr(event, 'globalPosition'):
                self.last_pos = event.globalPosition().toPoint()
            else:
                self.last_pos = event.globalPos()
            self.canvas.setCursor(QtCore.Qt.ClosedHandCursor)

    def on_mouse_move(self, event):
        """Realizar pan mientras se arrastra."""
        if not self.dragging or self.last_pos is None:
            return

        parent = self.canvas.parent()
        while parent and not isinstance(parent, QtWidgets.QScrollArea):
            parent = parent.parent()
        
        if not isinstance(parent, QtWidgets.QScrollArea):
            return

        if hasattr(event, 'globalPosition'):
            current_pos = event.globalPosition().toPoint()
        else:
            current_pos = event.globalPos()

        # Calculate delta movement
        dx = current_pos.x() - self.last_pos.x()
        dy = current_pos.y() - self.last_pos.y()

        h_bar = parent.horizontalScrollBar()
        v_bar = parent.verticalScrollBar()
        
        new_h = h_bar.value() - dx
        new_v = v_bar.value() - dy
        
        h_bar.setValue(new_h)
        v_bar.setValue(new_v)

        # Update last position
        self.last_pos = current_pos

    def on_mouse_release(self, event):
        """Finalizar pan."""
        if event.button() == QtCore.Qt.LeftButton and self.dragging:
            self.dragging = False
            self.last_pos = None
            self.canvas.setCursor(QtCore.Qt.OpenHandCursor)
