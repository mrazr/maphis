import time

from PySide2.QtCore import Signal, QPointF, Qt, QEvent, QPoint
from PySide2.QtGui import QPainter, QWheelEvent, QResizeEvent, QMouseEvent, QKeyEvent, QCursor
from PySide2.QtWidgets import QGraphicsView, QWidget, QSizePolicy


class CustomGraphicsView(QGraphicsView):

    view_changed = Signal()
    rubber_band_started = Signal()
    mouse_move = Signal(QPointF)
    view_dragging = Signal(bool, QPoint)
    double_shift = Signal()
    escape_pressed = Signal()

    def __init__(self, parent: QWidget = None):
        QGraphicsView.__init__(self, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)

        self.verticalScrollBar().valueChanged.connect(lambda _: self.view_changed.emit())
        self.horizontalScrollBar().valueChanged.connect(lambda _: self.view_changed.emit())
        self.time_of_first_shift = -1
        self._allow_zoom: bool = True
        #self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self._allow_zoom:
            QGraphicsView.wheelEvent(self, event)
            return
        delta = 1
        if event.angleDelta().y() < 0:
            delta = -1

        m = self.transform()
        m11 = m.m11() * (1 + delta * 0.05)
        m31 = 0
        m22 = m.m22() * (1 + delta * 0.05)
        m32 = 0

        m.setMatrix(m11, m.m12(), m.m13(), m.m21(), m22, m.m23(),
                    m.m31() + m31, m.m32() + m32, m.m33())
        self.setTransform(m, False)
        srect = self.sceneRect()
        rrect = self.mapToScene(self.rect()).boundingRect()
        if delta < 0 and rrect.height() > srect.height():
            self.fitInView(srect, Qt.KeepAspectRatio)
        self.scene().update()
        self.view_changed.emit()

    def resizeEvent(self, event: QResizeEvent):
        self.view_changed.emit()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MidButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.viewport().setCursor(Qt.ClosedHandCursor)
            self.original_event = event
            handmade_event = QMouseEvent(QEvent.MouseButtonPress, QPointF(event.pos()), Qt.LeftButton, event.buttons(),
                                         Qt.KeyboardModifiers())
            self.view_dragging.emit(True, self.mapToScene(event.pos()))
            self.mousePressEvent(handmade_event)
            return None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            pass
        elif event.button() == Qt.LeftButton:
            pass
        elif event.button() == Qt.MidButton:
            self.viewport().setCursor(Qt.OpenHandCursor)
            handmade_event = QMouseEvent(QEvent.MouseButtonRelease, QPointF(event.pos()), Qt.LeftButton,
                                         event.buttons(), Qt.KeyboardModifiers())
            self.mouseReleaseEvent(handmade_event)
            self.setDragMode(QGraphicsView.NoDrag)
            self.view_dragging.emit(False, self.mapToScene(event.pos()))
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_move.emit(self.mapToScene(event.pos()))
        QGraphicsView.mouseMoveEvent(self, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        elif event.key() == Qt.Key_Shift:
            self.rubber_band_started.emit()
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setRubberBandSelectionMode(Qt.ContainsItemBoundingRect)
        QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control or event.key() == Qt.Key_Shift:
            self.setDragMode(QGraphicsView.NoDrag)
            if self.time_of_first_shift < 0:
                self.time_of_first_shift = time.time() * 1000
            else:
                if 1000 * time.time() - self.time_of_first_shift < 500:
                    self.double_shift.emit()
                    self._allow_zoom = False
                self.time_of_first_shift = -1
        if event.key() == Qt.Key_Escape:
            self.escape_pressed.emit()
            self._allow_zoom = True
        QGraphicsView.keyReleaseEvent(self, event)

    def allow_zoom(self, allow: bool):
        self._allow_zoom = allow
        self.horizontalScrollBar().setEnabled(allow)
        self.verticalScrollBar().setEnabled(allow)
