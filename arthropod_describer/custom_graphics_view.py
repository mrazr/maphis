import time
import mouse

from PySide2.QtCore import Signal, QPointF, Qt, QEvent, QPoint
from PySide2.QtGui import QPainter, QWheelEvent, QResizeEvent, QMouseEvent, QKeyEvent, QCursor
from PySide2.QtWidgets import QGraphicsView, QWidget, QSizePolicy

from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool


class CustomGraphicsView(QGraphicsView):

    view_changed = Signal()
    rubber_band_started = Signal()
    mouse_move = Signal(QPointF)
    view_dragging = Signal(bool, QPoint)
    double_shift = Signal()
    escape_pressed = Signal()
    space_pressed = Signal()
    tab_pressed = Signal()

    def __init__(self, state: State, parent: QWidget = None):
        QGraphicsView.__init__(self, parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)

        self.verticalScrollBar().valueChanged.connect(lambda _: self.view_changed.emit())
        self.horizontalScrollBar().valueChanged.connect(lambda _: self.view_changed.emit())
        self.time_of_first_shift = -1
        self._allow_zoom: bool = True
        self.state = state
        #self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        
    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.ControlModifier > 0:
            self.state.key_modifier = Qt.Key_Control
            QGraphicsView.wheelEvent(self, event)
            return
        else:
            self.state.key_modifier = None
        if event.modifiers() & Qt.ShiftModifier > 0:
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
        if delta < 0 and rrect.height() > srect.height() and rrect.width() > srect.width():
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

        # Auto scrolling near viewport edges.
        if (event.buttons() & Qt.LeftButton) or (self.state.current_tool is not None and self.state.current_tool.should_auto_scroll_with_left_button_released()):
            auto_scroll_edge_width = min(self.state.current_tool.get_auto_scroll_distance() if self.state.current_tool is not None else Tool.DEFAULT_AUTO_SCROLL_DISTANCE,
                                         self.width() / 3, self.height() / 3)
            # Auto scroll left.
            displacement = int(auto_scroll_edge_width - event.pos().x())
            if self.horizontalScrollBar().value() > 0 and displacement > 0:
                mouse.move(displacement, 0, False)
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - displacement)
            # Auto scroll up.
            displacement = int(auto_scroll_edge_width - event.pos().y())
            if self.verticalScrollBar().value() > 0 and displacement > 0:
                mouse.move(0, displacement, False)
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - displacement)
            # Auto scroll right.
            displacement = int(self.viewport().width() - auto_scroll_edge_width - event.pos().x())
            if self.horizontalScrollBar().value() < self.horizontalScrollBar().maximum() and displacement < 0:
                mouse.move(displacement, 0, False)
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - displacement)
            # Auto scroll down.
            displacement = int(self.viewport().height() - auto_scroll_edge_width - event.pos().y())
            if self.verticalScrollBar().value() < self.verticalScrollBar().maximum() and displacement < 0:
                mouse.move(0, displacement, False)
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - displacement)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            # self.setDragMode(QGraphicsView.ScrollHandDrag)
            pass
        elif event.key() == Qt.Key_Shift:
            self.rubber_band_started.emit()
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setRubberBandSelectionMode(Qt.ContainsItemBoundingRect)
        QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control or event.key() == Qt.Key_Shift:
            # self.setDragMode(QGraphicsView.NoDrag)
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
        elif event.key() == Qt.Key_Space:
            self.space_pressed.emit()
        elif event.key() == Qt.Key_Tab:
            self.tab_pressed.emit()
        QGraphicsView.keyReleaseEvent(self, event)

    # def allow_zoom(self, allow: bool):
    #     self._allow_zoom = allow
    #     self.horizontalScrollBar().setEnabled(allow)
    #     self.verticalScrollBar().setEnabled(allow)
