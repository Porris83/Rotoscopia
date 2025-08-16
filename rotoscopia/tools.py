from PySide6 import QtCore, QtGui

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
        if self.canvas.overlay is None:
            return
        pt = self._overlay_point(event)
        if self.canvas.last_point is None:
            self.canvas.last_point = pt
        painter = QtGui.QPainter(self.canvas.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.canvas.last_point, pt)
        painter.end()
        self.canvas.last_point = pt
        self.canvas.update_display()

    def on_mouse_release(self, event):
        self.canvas.last_point = None

class EraserTool(BaseTool):
    name = "eraser"

    def on_mouse_press(self, event):
        self.canvas.last_point = self._overlay_point(event)

    def on_mouse_move(self, event):
        if self.canvas.overlay is None:
            return
        pt = self._overlay_point(event)
        if self.canvas.last_point is None:
            self.canvas.last_point = pt
        painter = QtGui.QPainter(self.canvas.overlay)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
        pen = QtGui.QPen(QtGui.QColor(0,0,0,0), self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.canvas.last_point, pt)
        painter.end()
        self.canvas.last_point = pt
        self.canvas.update_display()

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
        self._base = QtGui.QPixmap(self.canvas.overlay) if self.canvas.overlay else None

    def on_mouse_move(self, event):
        if self._start is None or self._base is None:
            return
        pt = self._overlay_point(event)
        temp = QtGui.QPixmap(self._base)
        painter = QtGui.QPainter(temp)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self._start, pt)
        painter.end()
        self.canvas.overlay = temp
        self.canvas.update_display()

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
        self.canvas.overlay = self._base
        self.canvas.update_display()
        self._start = None; self._base = None
