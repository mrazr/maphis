import importlib.resources
import math
import typing
from typing import List, Tuple, Dict

import numpy as np
from PySide2.QtCore import QPoint, QRect
from PySide2.QtGui import QPainter, QColor, QPen, QIcon
import skimage.draw
import skimage.measure
from skimage import io
from skimage.morphology import binary_dilation, disk

from arthropod_describer.common.label_change import LabelChange, CommandEntry
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, EditContext, PaintCommand, line_command
from arthropod_describer.common.user_params import UserParam, ParamType


class Tool_Knife(Tool):
    def __init__(self, state: State):
        Tool.__init__(self, state)
        self._tool_name = "Knife"
        self._active = False
        self._first_endpoint: Tuple[int, int] = (-1, -1)
        self._user_params = {'Cut width': UserParam('Cut width', ParamType.INT, 3, min_val=1, max_val=9, step=2)}
        with importlib.resources.path("tools.icons", "cutter.png") as path:
            self._tool_icon = QIcon(str(path))
        self.pen = QPen()
        self.state = state

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def active(self) -> bool:
        return self._active

    @property
    def viz_active(self) -> bool:
        return self._active

    @property
    def user_params(self) -> typing.Dict[str, UserParam]:
        return self._user_params

    def left_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[
        typing.Optional[CommandEntry], QRect]:
        return None, QRect()

    def left_release(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> Tuple[
        typing.Optional[CommandEntry], QRect]:
        ctx.tool_viz_commands = []
        line_coords = skimage.draw.line(*self._first_endpoint, *(pos.toTuple()[::-1]))

        line_width = self.user_params['Cut width'].value
        if line_width > 1:

            top, left = np.min(line_coords[0]) - line_width // 2, np.min(line_coords[1]) - line_width // 2
            bottom, right = np.max(line_coords[0]) + line_width // 2, np.max(line_coords[1]) + line_width // 2

            line_box = np.zeros((bottom - top + 1, right - left + 1), np.bool)

            local_coords = (line_coords[0] - top, line_coords[1] - left)
            line_box[local_coords[0], local_coords[1]] = 1
            dil = binary_dilation(line_box, disk(line_width // 2))
            line_coords = np.nonzero(dil)
            line_coords = line_coords[0] + top, line_coords[1] + left

        rr_cc = [(r, c) for r, c in zip(line_coords[0], line_coords[1]) if 0 <= r < ctx.label_img.label_image.shape[0] and 0 <= c < ctx.label_img.label_image.shape[1]]
        line_coords = [r for r, c in rr_cc], [c for r, c in rr_cc]

        label_profile = np.where(~ctx.clip_mask > 0, ctx.label_img.label_image, 0)[line_coords]
        labels = np.unique(label_profile)

        if len(labels) < 2:
            return None, QRect()
        #labels = set()

        lab_coords: Dict[int, Tuple[List[int], List[int]]] = {label: ([], []) for label in labels}
        painter = QPainter(ctx.label_viz)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        for i, y, x in zip(range(len(label_profile)), *line_coords):
            label = label_profile[i]
            if label == 0:
                continue
            lab_coords[label][0].append(y)
            lab_coords[label][1].append(x)

            color = QColor.fromRgb(*ctx.colormap[ctx.label])
            if ctx.label == 0:
                color.setAlpha(0)
            painter.setPen(color)
            painter.drawPoint(x, y)
        painter.end()
        if 0 in lab_coords:
            del lab_coords[0]
        cmd = CommandEntry([LabelChange(coords, ctx.label, label, ctx.label_img.label_semantic) for label, coords in lab_coords.items()])
        cmd.source = self.tool_name
        return cmd, cmd.bbox

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, ctx: EditContext) -> List[LabelChange]:
        #ctx.tool_viz_commands = [draw_line(QPoint(*self._first_endpoint[::-1]), new_pos, ctx)]
        return super().mouse_move(painter, new_pos, old_pos, ctx)

    def viz_left_press(self, pos: QPoint) -> List[PaintCommand]:
        self._first_endpoint = pos.toTuple()[::-1]
        color = self.state.label_hierarchy.nodes[self.state.primary_label].color
        self.pen.setColor(QColor(*color, 255))
        self.pen.setWidth(self._user_params['Cut width'].value)
        self._active = True
        return self.viz_mouse_move(pos, pos)

    def viz_mouse_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        return [line_command(QPoint(*self._first_endpoint[::-1]), new_pos, self.pen)]

    def viz_left_release(self, pos: QPoint) -> List[PaintCommand]:
        self._active = False
        return []


def draw_line(pos1: QPoint, pos2: QPoint, ctx: EditContext):
    def draw(painter: QPainter):
        painter.save()
        pen = QPen(QColor.fromRgb(*ctx.colormap[ctx.label]))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(pos1, pos2)
        painter.restore()

    return draw
