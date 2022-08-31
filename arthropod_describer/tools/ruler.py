import importlib
import math
import typing
from typing import Optional, List

from PySide2.QtCore import QPoint, QRect
from PySide2.QtGui import QIcon, QPen, QColor, QPainter
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QToolButton

from arthropod_describer.common.label_change import CommandEntry
from arthropod_describer.common.photo import UpdateContext
from arthropod_describer.common.state import State
from arthropod_describer.common.storage import Storage
from arthropod_describer.common.tool import Tool, PaintCommand, line_command, text_command, EditContext
from arthropod_describer.common.units import BaseUnit, Value, Unit
from arthropod_describer.common.user_params import UserParam, ParamType


class Tool_Ruler(Tool):

    def __init__(self, state: State):
        Tool.__init__(self, state)
        self._tool_name = "Ruler"
        self.state = state
        self._active = False
        with importlib.resources.path('tools.icons', 'ruler.png') as path:
            self._tool_icon = QIcon(str(path))
        self.endpoints: List[QPoint] = []
        self.outline_pen = QPen(QColor(0, 0, 0))
        self.outline_pen.setWidthF(3.5)
        self.line_pen = QPen(QColor(0, 255, 0))
        self.line_pen.setWidthF(2.5)
        self.text_pen = QPen(QColor(0, 255, 0))
        self.text_pen.setWidthF(2.5)
        self._viz_commands: List[PaintCommand] = []

        self.px_measurement: typing.Optional[Value] = None
        self.px_measurements: List[Value] = []

        self.real_measurement: typing.Optional[Value] = None
        self.real_measurements: List[Value] = []

        self._show_real_units: bool = True
        self._px_unit: Unit = self.state.units.units['px']
        self.multi_ruler: UserParam = UserParam('Multiple measurements', ParamType.BOOL, False,
                                                key='multi-ruler')
        self.scale: typing.Optional[Value] = None
        self.out_layout = QGridLayout()
        self.out_value_px_label = QLabel()
        self.out_value_unit_label = QLabel()
        self.out_layout.addWidget(self.out_value_px_label, 0, 0)
        self.out_layout.addWidget(self.out_value_unit_label, 0, 1)

        self.state.storage_changed.connect(self._handle_storage_changed)

    def _handle_storage_changed(self, storage: Storage, old_storage: typing.Optional[Storage]):
        if old_storage is not None:
            old_storage.update_photo.disconnect(self._handle_update_photo)
        storage.update_photo.connect(self._handle_update_photo)

    @property
    def user_params(self) -> typing.Dict[str, UserParam]:
        return {self.multi_ruler.param_key: self.multi_ruler}

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
    def value_storage(self) -> Optional[typing.Any]:
        return self.px_measurements

    # def left_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
    #    if not self._active:
    #        self.endpoints.append(pos)
    #    self._active = True
    #    return self.mouse_move(painter, pos, pos, context)

    def right_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> typing.Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def viz_left_press(self, pos: QPoint) -> List[PaintCommand]:
        if not self.multi_ruler.value:
            self.viz_right_release(pos)
        self.px_measurement = None
        self.scale = self.state.current_photo.image_scale
        self.endpoints.append(pos)
        self._active = True
        return self.viz_mouse_move(pos, pos)

    def viz_mouse_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        if len(self.endpoints) < 1:
            return []
        if new_pos == old_pos:
            return self._viz_commands
        # self.state.viz_layer.clear_layer()
        self.endpoints.append(new_pos)
        cmds: List[PaintCommand] = []
        for i in range(0, len(self.endpoints) - 1, 2):
            # self.state.viz_layer.put_line_segment(self.endpoints[i], self.endpoints[i+1], self.line_pen)
            cmds.append(line_command(self.endpoints[i], self.endpoints[i + 1], self.outline_pen))
            cmds.append(line_command(self.endpoints[i], self.endpoints[i + 1], self.line_pen))
            vec = (self.endpoints[i + 1] - self.endpoints[i])
            length_px = math.sqrt(QPoint.dotProduct(vec, vec))
            self.px_measurement = Value(int(round(length_px)), self._px_unit)
            mid_ = self.endpoints[i] + 0.5 * vec
            # self.state.viz_layer.put_text(mid_, f'{length_px:.2f} px', self.text_pen)
            if self._show_real_units and self.scale is not None and self.scale.value > 0:
                cmds.append(text_command(mid_, f'{self.px_measurement / self.scale} ({self.px_measurement})',
                                         self.outline_pen))
                cmds.append(
                    text_command(mid_, f'{self.px_measurement / self.scale} ({self.px_measurement})', self.text_pen))
            else:
                cmds.append(text_command(mid_, f'{self.px_measurement}', self.outline_pen))
                cmds.append(text_command(mid_, f'{self.px_measurement}', self.text_pen))
        # FIXME self.value_storage is empty although self._measurement is not. Might cause `IndexError: list index out of range`
        if self.px_measurement.value > 0:
            self.current_value.emit(self.px_measurement)
        self.endpoints.pop()
        self._viz_commands = cmds
        return cmds

    def viz_left_release(self, pos: QPoint) -> List[PaintCommand]:
        if pos == self.endpoints[-1]:
            self.endpoints.pop()
            return self._viz_commands
        if self.px_measurement is not None:
            if self.px_measurement.value == 0:
                # Do not place (or emit placement signal of) a zero-length ruler. If it has been started (odd number of endpoints), remove its endpoint and viz commands.
                # TODO: Hopefully, not emitting the signal and keeping self._active = True at the end of the function is ok;
                #       otherwise, self.current_value.emit(0) and self._active = False might be needed, as in Tool_Ruler.viz_right_release().
                if len(self.endpoints) % 2 == 1 and len(self._viz_commands) >= 4:
                    self.endpoints.pop()
                    self._viz_commands.pop()
                    self._viz_commands.pop()
                    self._viz_commands.pop()
                    self._viz_commands.pop()
            else:
                self.endpoints.append(pos)
                self.px_measurements.append(self.px_measurement)
                self._update_out_labels()
                if self.px_measurement.value > 0:
                    self.current_value.emit(self.px_measurement)

        self._active = True
        # self._measurement = Value(0, self._px_unit)
        self.px_measurement = None
        return self._viz_commands

    def viz_right_release(self, pos: QPoint) -> List[PaintCommand]:
        self.endpoints.clear()
        self._viz_commands.clear()
        self.px_measurements.clear()

        self._update_out_labels()

        self.px_measurement = None
        # self.current_value.emit(Value(0, self.state.units.units['px']))
        self.current_value.emit(None)
        # self.state.viz_layer.clear_layer()
        self._active = False
        return []

    def viz_hover_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        return self._viz_commands

    def show_real_units(self, show: bool):
        self._show_real_units = show

    def set_scale(self, scale: typing.Optional[Value]):
        self.scale = scale

    # def left_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[
    #    Optional[CommandEntry], QRect]:
    #    #self.endpoints.append(pos)
    #    #self._active = False
    #    #self.endpoints.clear()
    #    return None, QRect()

    # def right_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
    #    self.endpoints.clear()
    #    self.state.viz_layer.clear_layer()
    #    self._active = False
    #    return None, QRect()

    # def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, context: EditContext) -> Tuple[
    #    Optional[CommandEntry], QRect]:
    #    if len(self.endpoints) < 1:
    #        return None, QRect()
    #    self.state.viz_layer.clear_layer()
    #    self.endpoints.append(new_pos)
    #    for i in range(0, len(self.endpoints) - 1, 2):
    #        self.state.viz_layer.put_line_segment(self.endpoints[i], self.endpoints[i+1], self.line_pen)
    #        vec = (self.endpoints[i+1] - self.endpoints[i])
    #        length_px = math.sqrt(QPoint.dotProduct(vec, vec))
    #        mid_ = self.endpoints[i] + 0.5 * vec
    #        self.state.viz_layer.put_text(mid_, f'{length_px:.2f} px', self.text_pen)
    #    self.endpoints.pop()
    #    return None, QRect()

    def reset_tool(self):
        self._active = False
        self.endpoints.clear()
        self.px_measurement = Value(0, self._px_unit)
        self.px_measurements.clear()
        self._viz_commands.clear()
        # self.state.viz_layer.clear_layer()
        self._update_out_labels()

    @property
    def viz_commands(self) -> List[PaintCommand]:
        return self._viz_commands

    def set_line(self, p1: QPoint, p2: QPoint, reset_others: bool = False):
        if reset_others:
            self.px_measurements.clear()
            self.real_measurements.clear()
            self._viz_commands.clear()
            self.endpoints.clear()
        cmds: List[PaintCommand] = [line_command(p1, p2, self.line_pen)]

        vec = (p2 - p1)
        length_px = math.sqrt(QPoint.dotProduct(vec, vec))
        self.px_measurement = Value(int(round(length_px)), self.state.units.units['px'])

        if self.multi_ruler.value:
            self.px_measurements.append(self.px_measurement)
        else:
            self.px_measurements = [self.px_measurement]

        scale = self.state.current_photo.image_scale
        self._update_out_labels()

        mid_ = p1 + 0.5 * vec
        # self.state.viz_layer.put_text(mid_, f'{length_px:.2f} px', self.text_pen)
        if self._show_real_units and scale is not None and scale.value > 0:
            self.real_measurements.append(self.px_measurements[-1] / scale)
            cmds.append(text_command(mid_, f'{self.px_measurement / self.scale} ({self.px_measurement})',
                                     self.outline_pen))
            cmds.append(
                text_command(mid_, f'{self.px_measurement / self.scale} ({self.px_measurement})', self.text_pen))
        else:
            cmds.append(text_command(mid_, f'{self.px_measurement}', self.outline_pen))
            cmds.append(text_command(mid_, f'{self.px_measurement}', self.text_pen))

        self.endpoints.append(p1)
        self.endpoints.append(p2)
        self._viz_commands = cmds
        self._active = True

    def _update_out_labels(self):
        measurement_sum = 0
        for i, measurement in enumerate(self.px_measurements):
            measurement_sum += measurement.value
        measurement_sum = Value(measurement_sum, self._px_unit)
        self.out_value_px_label.setText(str(measurement_sum))
        if self._show_real_units\
                and self.state is not None\
                and self.state.current_photo is not None\
                and self.state.current_photo.image_scale is not None\
                and self.state.current_photo.image_scale.value != 0:
            real_measurement_sum = measurement_sum / self.state.current_photo.image_scale
            self.out_value_unit_label.setText(str(real_measurement_sum))
        else:
            self.out_value_unit_label.setText('')

    def rotate(self, ccw: bool, origin: typing.Tuple[int, int]):
        for endpoint in self.endpoints:
            #print(f"\nrotating ruler endpoint ({endpoint.x()}, {endpoint.y()}) around ({origin[0]}, {origin[1]}), ccw = {ccw}")
            p1_c = complex(endpoint.x() - origin[0], endpoint.y() - origin[1])
            p1_c = p1_c * complex(0, -1 if ccw else 1)
            p1 = (round(p1_c.real), round(p1_c.imag))
            p1 = (p1[0] + origin[1], p1[1] + origin[0])
            endpoint.setX(p1[0])
            endpoint.setY(p1[1])
            #print(f"rotated to ({endpoint.x()}, {endpoint.y()})\n")
            self.regenerate_viz()

    def set_out_widget(self, widg: typing.Optional[QGroupBox]) -> bool:
        widg.setTitle('Total measurements')
        self._update_out_labels()
        widg.setLayout(self.out_layout)
        return True

    def regenerate_real_measurements(self):
        self.real_measurements.clear()
        scale = self.state.current_photo.image_scale
        if scale is not None and scale.value > 0:
            for px_meas in self.px_measurements:
                self.real_measurements.append(px_meas / scale)
        self.regenerate_viz()

    def regenerate_viz(self):
        # print('regenerating')
        cmds: List[PaintCommand] = []
        scale = self.state.current_photo.image_scale
        for i in range(0, len(self.endpoints) - 1, 2):
            # self.state.viz_layer.put_line_segment(self.endpoints[i], self.endpoints[i+1], self.line_pen)
            cmds.append(line_command(self.endpoints[i], self.endpoints[i + 1], self.outline_pen))
            cmds.append(line_command(self.endpoints[i], self.endpoints[i + 1], self.line_pen))
            vec = (self.endpoints[i + 1] - self.endpoints[i])
            length_px = math.sqrt(QPoint.dotProduct(vec, vec))
            self.px_measurement = Value(int(round(length_px)), self._px_unit)
            mid_ = self.endpoints[i] + 0.5 * vec
            if self._show_real_units and scale is not None and scale.value > 0:
                cmds.append(text_command(mid_, f'{self.px_measurement / scale} ({self.px_measurement})',
                                         self.outline_pen))
                cmds.append(
                    text_command(mid_, f'{self.px_measurement / scale} ({self.px_measurement})', self.text_pen))
            else:
                cmds.append(text_command(mid_, f'{self.px_measurement}', self.outline_pen))
                cmds.append(text_command(mid_, f'{self.px_measurement}', self.text_pen))

        self._viz_commands = cmds
        self.update_viz.emit()

    def _handle_update_photo(self, img_name: str, ctx: UpdateContext, data: typing.Dict[str, typing.Any]):
        if img_name != self.state.current_photo.image_name or ctx != UpdateContext.Photo or 'type' not in data:
            return
        if data['type'] != 'image_scale':
            return

        self.regenerate_real_measurements()
