import typing

import numpy as np
from PySide2.QtCore import QPoint
from PySide2.QtGui import QImage, QPainter

from .tool import Tool, qimage2ndarray, ToolUserParam

TOOL_CLASS_NAME = 'Bucket'


class Tool_Bucket(Tool):
    def __init__(self):
        Tool.__init__(self)
        self._tool_id = -1
        self.cmap = None
        self._secondary_label = None
        self._primary_label = None
        self._tool_name = 'Bucket'

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cursor_image(self) -> QImage:
        return QImage()

    @property
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        return {}

    def set_user_param(self, param_name: str, value: typing.Any):
        pass

    def left_press(self, painter: QPainter, pos: QPoint, img: QImage, label: int):
        pass

    @property
    def active(self) -> bool:
        return False

    def update_primary_label(self, label: int):
        self._primary_label = label

    def update_secondary_label(self, label: int):
        self._secondary_label = label

    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        if cmap is None:
            return
        self.cmap = cmap

    def left_release(self, painter: QPainter, pos: QPoint, label: int) -> typing.Tuple[np.ndarray, int]:
        pass

    def right_press(self, painter: QPainter, pos: QPoint, img: QImage, label: int):
        pass

    def right_release(self, painter: QPainter, pos: QPoint, label: int):
        pass

    def middle_click(self, painter: QPainter, pos: QPoint, label: int):
        pass

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, label: int):
        pass

    #@property
    #def tool_id(self) -> int:
    #    return self._tool_id

    #def set_tool_id(self, tool_id: int):
    #    self._tool_id = tool_id
