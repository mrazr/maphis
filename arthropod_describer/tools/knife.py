from typing import List, Tuple, Dict

import numpy as np
from PySide2.QtCore import QPoint
from PySide2.QtGui import QPainter, QColor, QPen
import skimage.draw
import skimage.measure

from arthropod_describer.common.label_change import LabelChange
from arthropod_describer.common.tool import Tool, EditContext


class Tool_Knife(Tool):
    def __init__(self):
        Tool.__init__(self)
        self._tool_name = "Knife"
        self._active = False
        self._first_endpoint: Tuple[int, int] = (-1, -1)

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def active(self) -> bool:
        return self._active

    def left_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> List[LabelChange]:
        self._first_endpoint = pos.toTuple()[::-1]
        return []

    def left_release(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> List[LabelChange]:
        ctx.tool_viz_commands = []
        line_coords = skimage.draw.line(*self._first_endpoint, *(pos.toTuple()[::-1]))

        label_profile = skimage.measure.profile_line(ctx.label_img.label_img,
                                                     self._first_endpoint,
                                                     pos.toTuple()[::-1],
                                                     order=0,
                                                     linewidth=1).astype(np.uint32)

        labels = np.unique(label_profile)

        if len(labels) < 2:
            return []

        lab_coords: Dict[int, Tuple[List[int], List[int]]] = {label: ([], []) for label in labels}

        for i, y, x in zip(range(len(label_profile)), *line_coords):
            label = label_profile[i]
            if label == 0:
                continue
            lab_coords[label][0].append(y)
            lab_coords[label][1].append(x)

            painter.setPen(QColor.fromRgb(*ctx.colormap[ctx.label]))
            painter.drawPoint(x, y)

        return [LabelChange(coords, ctx.label, label, ctx.label_img.label_type) for label, coords in lab_coords.items()]

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, ctx: EditContext) -> List[LabelChange]:
        ctx.tool_viz_commands = [draw_line(QPoint(*self._first_endpoint[::-1]), new_pos, ctx)]
        return super().mouse_move(painter, new_pos, old_pos, ctx)


def draw_line(pos1: QPoint, pos2: QPoint, ctx: EditContext):
    def draw(painter: QPainter):
        painter.save()
        pen = QPen(QColor.fromRgb(*ctx.colormap[ctx.label]))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(pos1, pos2)
        painter.restore()

    return draw
