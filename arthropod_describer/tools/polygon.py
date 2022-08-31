import importlib.resources
import typing
from typing import List, Tuple, Optional

import numpy as np
from PySide2.QtCore import QPoint, QRect, QObject, Qt
from PySide2.QtGui import QPainter, QIcon, QPen, QPainterPath, QBrush, QColor, QBitmap, QImage
import skimage.draw
import qimage2ndarray

from arthropod_describer.common.label_change import CommandEntry, generate_command_from_coordinates
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, PaintCommand, EditContext, fill_path_command, line_command
from arthropod_describer.common.user_params import UserParam, ParamType


class Tool_Polygon(Tool):
    def __init__(self, state: State, parent: QObject = None):
        super().__init__(state, parent)
        self._tool_name: str = "Polygon"
        with importlib.resources.path('tools.icons', 'square.png') as path:
            self._tool_icon = QIcon(str(path))
        self.state = state
        self.pen = QPen()
        self.pen.setWidthF(1.0)

        self.brush: QBrush = QBrush(QColor(0, 0, 0))

        self._active: bool = False
        self._viz_active: bool = False

        self._points: List[QPoint] = []
        self._hovered_point: QPoint = QPoint()

        self._curr_painter_path: QPainterPath = QPainterPath()

        self._viz_commands: List[PaintCommand] = []

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def user_params(self) -> typing.Dict[str, UserParam]:
        return {}

    @property
    def active(self) -> bool:
        return self._active

    @property
    def viz_active(self) -> bool:
        return self._viz_active

    def should_auto_scroll_with_left_button_released(self):
        return len(self._points) > 0

    def _finish_polygon(self, painter: QPainter, pos: QPoint, context: EditContext) \
            -> Tuple[Optional[CommandEntry], QRect]:
        self._active = False
        if len(self._points) == 0:
            self._curr_painter_path = QPainterPath()
            return None, QRect()

        clip_path = QPainterPath()
        clip_path.addRegion(context.clip_region)
        clipped_path = clip_path.intersected(self._curr_painter_path)

        bitmap = QImage(context.label_viz.size(), QImage.Format_Grayscale8)
        bitmap.fill(QColor(0, 0, 0))
        _painter = QPainter(bitmap)
        _painter.fillPath(clipped_path, QBrush(QColor(255, 255, 255)))
        _painter.end()

        bitmap_nd = qimage2ndarray.raw_view(bitmap)

        # r = [point.y() for point in self._points]
        # c = [point.x() for point in self._points]

        # rr, cc = skimage.draw.polygon(r, c)

        rr, cc = np.nonzero(bitmap_nd)

        if len(rr) == 0:
            return None, QRect()

        left, top = np.min(cc), np.min(rr)
        right, bottom = np.max(cc), np.max(rr)

        cmd = generate_command_from_coordinates(context.label_img, cc, rr, context.label)
        cmd.source = self._tool_name

        painter = QPainter(context.label_viz)
        color = QColor(*self.state.colormap[context.label])
        if context.label == 0:
            color = QColor(Qt.transparent)
        brush = QBrush(color)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setBrush(brush)
        painter.fillPath(clipped_path, brush)
        painter.end()

        self._points.clear()
        self._curr_painter_path = QPainterPath()
        return cmd, QRect(QPoint(left, top), QPoint(right, bottom))

    def left_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        self.brush.setColor(QColor(*self.state.colormap[context.label]))
        self.pen.setColor(self.brush.color())
        self._active = True
        return None, QRect()

#    def left_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[
#        Optional[CommandEntry], QRect]:
#        if not self._active:
#            return None, QRect()
#        return None, QRect()

    def right_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> \
        Tuple[Optional[CommandEntry], QRect]:
        self._points.clear()
        self._active = False
        self._viz_commands.clear()
        return None, QRect()

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, context: EditContext) -> Tuple[
        Optional[CommandEntry], QRect]:
        if not self._active:
            return None, QRect()

        if (new_pos != old_pos):
            self._points.append(new_pos)

        return None, QRect()

    def mouse_double_click(self, painter: QPainter, pos: QPoint, context: EditContext) \
            -> Tuple[Optional[CommandEntry], QRect]:
        if not self._active:
            return None, QRect()
        self._active = False
        self._points.append(pos)
        self._curr_painter_path.lineTo(pos)
        ret = self._finish_polygon(painter, pos, context)
        self._points.clear()
        self._viz_commands.clear()
        return ret

    def viz_left_press(self, pos: QPoint) -> List[PaintCommand]:
        self._viz_active = True
        if self._curr_painter_path.elementCount() == 0:
            self._curr_painter_path = QPainterPath(pos)
        self._points.append(pos)
        self._curr_painter_path.lineTo(pos)
        return self._viz_commands

    def viz_left_release(self, pos: QPoint) -> List[PaintCommand]:
        return self._viz_commands

    def viz_mouse_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        if not self._viz_active:
            return []
        if (self._active):
            self._curr_painter_path.lineTo(new_pos)
        return self.viz_hover_move(new_pos, old_pos)

    def viz_hover_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        self._points.append(new_pos)
        path = QPainterPath(self._points[0])
        cmds: List[PaintCommand] = []

        # If there is only the starting point and the cursor so far, draw a line between them.
        if (len(self._points) == 2 or (len(self._points) == 3) and (new_pos == self._points[1])):
            cmds.append(line_command(self._points[0], self._points[1], self.pen))

        for p in self._points[1:]:
            path.lineTo(p)
        path.lineTo(self._points[0])

        self._points.pop()
        cmds.append(fill_path_command(path, self.pen, self.brush))
        self._viz_commands = cmds
        return self._viz_commands

    def viz_right_release(self, pos: QPoint) -> List[PaintCommand]:
        self._curr_painter_path = QPainterPath()
        self._viz_active = False
        return []

    def viz_mouse_double_click(self, pos: QPoint) -> List[PaintCommand]:
        self._viz_active = False
        return []

    @property
    def viz_commands(self) -> List[PaintCommand]:
        return []

    def reset_tool(self):
        self._curr_painter_path = QPainterPath()
        self._points.clear()
        self._active = False
        self._viz_active = False
        self._viz_commands.clear()