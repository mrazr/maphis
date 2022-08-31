import abc
import typing
from typing import Optional

import PySide2
from PySide2.QtCore import QRectF, Qt
from PySide2.QtWidgets import QGraphicsObject, QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent

from arthropod_describer.common.photo import Photo
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, EditContext


class Layer(QGraphicsObject):
    def __init__(self, state: State, parent: Optional[PySide2.QtWidgets.QGraphicsItem] = None):
        super().__init__(parent)

    @abc.abstractmethod
    def set_tool(self, tool: Optional[Tool], reset_current: bool = True):
        pass

    @abc.abstractmethod
    def _create_context(self) -> Optional[EditContext]:
        pass

    @abc.abstractmethod
    def set_photo(self, photo: typing.Optional[Photo], reset_tool: bool = True):
        pass

    def initialize(self):
        pass

    def boundingRect(self) -> PySide2.QtCore.QRectF:
        return QRectF()

    def paint(self, painter: PySide2.QtGui.QPainter, option: PySide2.QtWidgets.QStyleOptionGraphicsItem,
              widget: typing.Optional[PySide2.QtWidgets.QWidget] = ...):
        pass

    def mouse_press(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouse_release(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouse_move(self, event: QGraphicsSceneMouseEvent):
        pass

    def mouse_double_click(self, event: QGraphicsSceneMouseEvent):
        pass

    def hover_enter(self, event: QGraphicsSceneHoverEvent):
        pass

    def hover_move(self, event: QGraphicsSceneHoverEvent):
        pass

    def hover_leave(self, event: QGraphicsSceneHoverEvent):
        pass

    def reset(self):
        pass


class MouseEventLayer(Layer):
    def __init__(self, state: State, parent: Optional[PySide2.QtWidgets.QGraphicsItem] = None):
        super().__init__(state, parent)
        self.layers: typing.List[Layer] = []

    def initialize(self):
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setAcceptHoverEvents(True)

    def set_photo(self, photo: Photo, reset_tool: bool = True):
        self.prepareGeometryChange()

    def _create_context(self) -> Optional[EditContext]:
        return None

    def set_tool(self, tool: Tool, reset_current: bool = True):
        pass

    def boundingRect(self) -> PySide2.QtCore.QRectF:
        if len(self.layers) == 0:
            return QRectF()
        return self.layers[0].boundingRect()

    def hoverEnterEvent(self, event: PySide2.QtWidgets.QGraphicsSceneHoverEvent):
        for layer in self.layers:
            layer.hover_enter(event)

    def hoverLeaveEvent(self, event: PySide2.QtWidgets.QGraphicsSceneHoverEvent):
        for layer in self.layers:
            layer.hover_leave(event)

    def hoverMoveEvent(self, event: PySide2.QtWidgets.QGraphicsSceneHoverEvent):
        for layer in self.layers:
            layer.hover_move(event)

    def mouseMoveEvent(self, event: PySide2.QtWidgets.QGraphicsSceneMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            event.ignore()
            return
        for layer in self.layers:
            layer.mouse_move(event)

    def mousePressEvent(self, event: PySide2.QtWidgets.QGraphicsSceneMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            event.ignore()
            return
        for layer in self.layers:
            layer.mouse_press(event)

    def mouseReleaseEvent(self, event: PySide2.QtWidgets.QGraphicsSceneMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            event.ignore()
            return
        for layer in self.layers:
            layer.mouse_release(event)

    def mouseDoubleClickEvent(self, event:PySide2.QtWidgets.QGraphicsSceneMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            event.ignore()
            return
        for layer in self.layers:
            layer.mouse_double_click(event)
