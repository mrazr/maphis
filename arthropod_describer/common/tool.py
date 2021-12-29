import abc
import enum
import typing
from typing import Dict, Tuple, List

import numpy as np
from PySide2.QtCore import QPoint, Slot
from PySide2.QtGui import QPainter, QImage

from arthropod_describer.common.label_change import LabelChange


class EditContext:
    def __init__(self, label_nd: np.ndarray, label: int, image: QImage, colormap: Dict[int, Tuple[int, int, int]]):
        self.label_nd = label_nd
        self.image = image
        self.label = label
        self.colormap = colormap


class ParamType(enum.IntEnum):
    INT = 0,
    STR = 1,
    BOOL = 2,


class ToolUserParam:
    def __init__(self, name: str, param_type: ParamType, default_value, min_val: int=-1, max_val: int=-1, step:int=1):
        self.name = name
        self.param_type = param_type
        self.default_value = default_value
        self.value = self.default_value
        if self.param_type == ParamType.INT:
            assert min_val >= 0
            assert max_val >= 0
        self.min_value = min_val
        self.max_value = max_val
        self.value_step = step


class Tool(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        self.tool_id = -42

    def set_tool_id(self, tool_id: int):
        self.tool_id = tool_id

    @property
    @abc.abstractmethod
    def tool_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def cursor_image(self) -> QImage:
        pass

    @property
    @abc.abstractmethod
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        pass

    @abc.abstractmethod
    def set_user_param(self, param_name: str, value: typing.Any):
        pass

    @property
    @abc.abstractmethod
    def active(self) -> bool:
        pass

    @abc.abstractmethod
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

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, context: EditContext) -> List[LabelChange]:
        return []

    @Slot(int)
    @abc.abstractmethod
    def update_primary_label(self, label: int):
        pass

    @Slot(int)
    @abc.abstractmethod
    def update_secondary_label(self, label: int):
        pass

    @Slot(dict)
    @abc.abstractmethod
    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        pass


def qimage2ndarray(img: QImage) -> np.ndarray:
    img_ = img
    dtype = np.uint8
    if img.format() == QImage.Format_ARGB32:
        img_ = img.convertToFormat(QImage.Format_RGB32)
        dtype = np.uint32
    return np.reshape(np.frombuffer(img_.constBits(), dtype), img_.size().toTuple()[::-1]).astype(dtype)