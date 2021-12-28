import typing

import numpy as np
from PySide2.QtCore import QPoint, Slot
from PySide2.QtGui import QImage, QPainter, QColor, QBrush
from skimage import draw
import skimage.morphology as M

from arthropod_describer.tools.tool import Tool, qimage2ndarray, ToolUserParam, ParamType

TOOL_CLASS_NAME = 'Brush'


class Tool_Brush(Tool):
    def __init__(self):
        Tool.__init__(self)
        self._tool_name = "Brush"
        self._user_params = {'radius': ToolUserParam('radius', ParamType.INT, 9, min_val=1, max_val=75, step=2)}
        self._current_img = None
        self.edit_mask = QImage()
        self.edit_painter = QPainter(self.edit_mask)
        radius = self._user_params['radius'].value

        self._primary_label: int = 1000
        self._secondary_label: int = 0

        self._brush_mask: np.ndarray = M.disk(radius, np.uint16)
        self._brush_icon = QImage()
        self._brush_center = np.array([radius, radius])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center
        self.modified_coords: typing.List[np.ndarray] = []
        self._active = False

        self.cmap: typing.Dict[int, typing.Tuple[int, int, int]] = dict()

        self._update_icon()

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cursor_image(self) -> QImage:
        radius = self._user_params['radius'].value
        self._brush_mask = M.disk(radius, np.uint16)
        self._brush_center = np.array([radius, radius])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center
        self._update_icon()
        return self._brush_icon

    @property
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        return self._user_params

    def set_user_param(self, param_name: str, value: typing.Any) -> typing.Any:
        if param_name not in self._user_params.keys():
            return None
        param: ToolUserParam = self._user_params[param_name]
        if param.param_type == ParamType.INT:
            if value % 2 == 0:
                value += 1
            self._user_params[param_name].value = value
        elif param.param_type == ParamType.BOOL:
            pass
        self._user_params[param_name].value = value
        return value

    def left_press(self, painter: QPainter, pos: QPoint, img: QImage, label: int) -> typing.List[np.ndarray]:
        self._active = True
        self._current_img = img
        if self.edit_mask.size() == img.size():
            self.edit_mask.fill(QColor(0, 0, 0))
        else:
            self.edit_mask = QImage(img.width(), img.height(), QImage.Format_Grayscale8)
            self.edit_mask.fill(QColor(0, 0, 0))
        return self.mouse_move(painter, pos, pos, label)

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, label: int) -> typing.List[np.ndarray]:
        if not self.active:
            return []
        painter.save()
        brush_color = QColor.fromRgb(*self.cmap[self._primary_label])
        painter.setPen(brush_color)
        painter.setBrush(QBrush(brush_color))
        rr, cc = draw.line(old_pos.y(), old_pos.x(),
                           new_pos.y(), new_pos.x())

        self.edit_painter.save()
        self.edit_painter.begin(self.edit_mask)
        self.edit_painter.setBrush(QBrush(QColor(255, 255, 255)))
        self.edit_painter.setPen(QColor(255, 255, 255))
        if painter.hasClipping():
            self.edit_painter.setClipRegion(painter.clipRegion())
        for x, y in zip(cc, rr):
            painter.drawEllipse(QPoint(x, y), self.user_params['radius'].value,
                                self.user_params['radius'].value)
            self.edit_painter.drawEllipse(QPoint(x, y), self.user_params['radius'].value,
                                          self.user_params['radius'].value)
        self.edit_painter.end()
        self.edit_painter.restore()
        painter.restore()
        return []

    def left_release(self, painter: QPainter, pos: QPoint, label: int) -> typing.Tuple[np.ndarray, int]:
        self._active = False
        return np.where(qimage2ndarray(self.edit_mask) > 0, self._primary_label, -1), self._primary_label

    def right_press(self, painter: QPainter, pos: QPoint, img: QImage, label: int) -> typing.Tuple[np.ndarray, int]:
        return np.array([]), -1

    def right_release(self, painter: QPainter, pos: QPoint, label: int) -> typing.Tuple[np.ndarray, int]:
        return np.array([]), -1

    def middle_click(self, painter: QPainter, pos: QPoint, label: int):
        pass

    @property
    def active(self) -> bool:
        return self._active

    @Slot(int)
    def update_primary_label(self, label: int):
        self._primary_label = label
        self._update_icon()

    @Slot(int)
    def update_secondary_label(self, label: int):
        self._secondary_label = label

    def _update_icon(self):
        if len(self.cmap.keys()) > 0:
            sz = self._brush_mask.shape
            self._brush_mask = self._primary_label * self._brush_mask
            self._brush_icon = QImage(sz[1], sz[0], QImage.Format_ARGB32)
            self._brush_icon.fill(QColor(0, 0, 0, 0))
            brush_color = QColor.fromRgb(*self.cmap[self._primary_label])
            painter = QPainter(self._brush_icon)
            painter.setPen(brush_color)
            radius = self.user_params['radius'].value
            painter.setBrush(QBrush(brush_color))
            painter.drawEllipse(QPoint(radius, radius), radius, radius)

    @Slot(dict)
    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        if cmap is None:
            return
        self.cmap = cmap
        self._update_icon()

    #@property
    #def tool_id(self) -> int:
    #    return self._tool_id

    #def set_tool_id(self, tool_id: int):
    #    self._tool_id = tool_id
