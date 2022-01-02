import abc
import typing
from typing import Dict, Tuple, List, Any

import numpy as np
from PySide2.QtCore import QPoint, Slot, QObject, Signal
from PySide2.QtGui import QPainter, QImage

from arthropod_describer.common.label_change import LabelChange
from arthropod_describer.common.photo import LabelImg
from arthropod_describer.common.state import State
from arthropod_describer.common.user_params import ToolUserParam


class EditContext:
    def __init__(self, label_img: LabelImg, label: int, image: QImage, colormap: Dict[int, Tuple[int, int, int]],
                 label_viz: QImage):
        self.label_img: LabelImg = label_img
        self.image = image
        self.label = label
        self.colormap = colormap
        self.label_viz = label_viz
        self.tool_viz_commands: List[Any] = []


class Tool(QObject):
    cursor_changed = Signal([int, QImage])

    def __init__(self, state: State, parent: QObject = None):
        QObject.__init__(self, parent)
        self.tool_id = -42

    def set_tool_id(self, tool_id: int):
        self.tool_id = tool_id

    @property
    @abc.abstractmethod
    def tool_name(self) -> str:
        pass

    @property
    def cursor_image(self) -> QImage:
        return QImage()

    @property
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        return {}

    def set_user_param(self, param_name: str, value: typing.Any):
        pass

    @property
    def active(self) -> bool:
        return False

    def left_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> List[LabelChange]:
        return []

    def left_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> List[LabelChange]:
        return []

    def right_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> List[LabelChange]:
        return []

    def right_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> List[LabelChange]:
        return []

    def middle_click(self, painter: QPainter, pos: QPoint, context: EditContext) -> List[LabelChange]:
        return []

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, context: EditContext) -> List[
        LabelChange]:
        return []

    @Slot(int)
    def update_primary_label(self, label: int):
        pass

    @Slot(int)
    def update_secondary_label(self, label: int):
        pass

    @Slot(dict)
    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        pass


def qimage2ndarray(img: QImage) -> np.ndarray:
    img_ = img
    dtype = np.uint8
    shape = img_.size().toTuple()[::-1]
    if img.format() == QImage.Format_ARGB32:
        img_ = img.convertToFormat(QImage.Format_RGB32)
        dtype = np.uint32
    elif img.format() == QImage.Format_RGB32:
        img_ = QImage.convertToFormat(img_, QImage.Format_RGB888)
        dtype = np.uint8
        shape = shape + (3,)
    return np.reshape(np.frombuffer(img_.constBits(), dtype), shape).astype(dtype)
