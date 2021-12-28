import time
from enum import IntEnum
import typing
from typing import Optional
from dataclasses import dataclass, field

import cv2 as cv
from PySide2.QtCore import Signal, QObject, QPointF, QPoint, QTimer
from PySide2.QtGui import Qt, QImage, QPixmap
from PySide2.QtWidgets import QWidget, QGraphicsScene, QToolButton, QGroupBox, QVBoxLayout, QSpinBox, QLineEdit, \
    QCheckBox, QGridLayout, QLabel, QSizePolicy, QToolBox, QGraphicsProxyWidget, QGraphicsItem, QListView
import numpy as np
from skimage import io

import tools.tool
from state import State
from colormap_widget import ColormapWidget
from tools.tool import Tool, ToolUserParam, ParamType
from custom_graphics_view import CustomGraphicsView
from canvas_widget import CanvasWidget
from view.ui_mask_edit_view import Ui_MaskEditor
from model.photo import Photo, LabelType


class ToolEntry:
    def __init__(self, tool: Tool, toolbutton: QToolButton, param_widget: typing.Optional[QWidget]=None):
        self.tool = tool
        self.toolbutton = toolbutton
        self.param_widget = param_widget


@dataclass(eq=False)
class LabelChange:
    coords: typing.Tuple[np.ndarray, np.ndarray]
    new_label: int
    old_label: int
    label_type: LabelType

    def swap_labels(self) -> 'LabelChange':
        return LabelChange(self.coords, self.old_label, self.new_label, self.label_type)


class DoType(IntEnum):
    Do = 0,
    Undo = 1,


@dataclass(eq=False)
class CommandEntry:
    change_chain: typing.List[LabelChange] = field(default_factory=list)
    do_type: DoType = DoType.Do

    def add_label_change(self, change: LabelChange):
        self.change_chain.append(change)


class MaskEditor(QObject):
    signal_next_photo = Signal()
    signal_prev_photo = Signal()

    def __init__(self, state: State):
        QObject.__init__(self)
        self.widget = QWidget()
        self.ui = Ui_MaskEditor()
        self.ui.setupUi(self.widget)

        self.ui.tbtnBugMask.toggled.connect(self.handle_bug_mask_checked)
        self.ui.tbtnSegmentsMask.toggled.connect(self.handle_segments_mask_checked)
        self.ui.tbtnReflectionMask.toggled.connect(self.handle_reflection_mask_checked)
        self.ui.btnNext.clicked.connect(lambda: self.signal_next_photo.emit())
        self.ui.btnPrevious.clicked.connect(lambda: self.signal_prev_photo.emit())

        self.state = state
        #self.state.colormap_changed.connect(lambda cmap: self._current_tool.color_map_changed(cmap.colormap))

        self._scene = QGraphicsScene()

        self._tools: typing.List[Tool] = []

        self.photo_view = CustomGraphicsView()
        self.ui.center.addWidget(self.photo_view)
        self.photo_view.setScene(self._scene)

        self.photo_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.photo_view.setInteractive(True)

        self.photo_view.view_changed.connect(self._handle_view_changed)
        self.photo_view.double_shift.connect(self._show_label_search_bar)
        self.photo_view.escape_pressed.connect(self._hide_label_search_bar)

        self.canvas = CanvasWidget(self.state)
        self._scene.addItem(self.canvas)
        self.canvas.initialize()
        self.canvas.left_press.connect(self.handle_left_press)
        self.canvas.label_changed.connect(self.handle_label_changed)
        self.photo_view.view_dragging.connect(self.canvas.handle_view_dragging)

        vbox = QVBoxLayout()

        self.colormap_widget = ColormapWidget()
        self.colormap_widget.primary_label_changed.connect(self._handle_primary_label_changed)
        self.colormap_widget.secondary_label_changed.connect(self._handle_secondary_label_changed)
        vbox.addWidget(self.colormap_widget)

        self.current_photo: Optional[Photo] = None
        self._tool_settings = QGroupBox('Tool settings')
        self._tool_settings.setLayout(QVBoxLayout())
        #self._tools: typing.List[Tool] = self._mock_load_tools()
        self._tool_param_widgets: typing.List[QWidget] = []

        self._current_tool: typing.Optional[Tool] = None

        vbox.addWidget(self._tool_settings)
        self._tool_settings.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        vbox.addStretch(2)

        side_widget = QWidget()
        side_widget.setLayout(vbox)
        side_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.ui.center.addWidget(side_widget)

        #self._current_tool = self._tools[0]
        #self.canvas.set_current_tool(self._tools[0])
        self.ui.tbtnBugMask.animateClick()
        self.handle_reflection_mask_checked(False)
        self.handle_segments_mask_checked(False)

        self.undo_stack: typing.List[CommandEntry] = []
        self.redo_stack: typing.List[CommandEntry] = []

        self.ui.tbtnUndo.clicked.connect(self.handle_undo_clicked)
        self.ui.tbtnRedo.clicked.connect(self.handle_redo_clicked)

        self._label_line_edit = self.colormap_widget.label_search_bar
        #self._label_line_edit.textChanged.connect(lambda _: self._handle_view_changed())
        self._glabel_line_edit = QGraphicsProxyWidget()
        self._glabel_line_edit.setWidget(self._label_line_edit)
        self._scene.addItem(self._glabel_line_edit)

        self.colormap_widget.label_search_finished.connect(self._hide_label_search_bar)

        self._label_list_view = self.colormap_widget.completer.popup()
        self._glabel_list_view = QGraphicsProxyWidget(self._glabel_line_edit)
        self._glabel_list_view.setWidget(self._label_list_view)
        #self._scene.addItem(self._glabel_list_view)

        rect = self.photo_view.viewport().rect()
        point = QPoint(rect.center().x() - self._glabel_line_edit.boundingRect().width() // 2,
                       rect.center().y() - self._glabel_line_edit.boundingRect().height() // 2)
        scene_point = self.photo_view.mapToScene(point)
        self._glabel_line_edit.setPos(scene_point)
        self._glabel_line_edit.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._glabel_line_edit.setVisible(False)


        #point.setY(point.y() + self._glabel_line_edit.boundingRect().y())
        #scene_point = self.photo_view.mapToScene( )
        self._glabel_list_view.setPos(QPoint(0, self._glabel_line_edit.boundingRect().height()))
        self._glabel_list_view.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._glabel_list_view.setVisible(False)

        self.qtimer = QTimer()
        self.qtimer.setInterval(100)
        self.qtimer.setSingleShot(False)
        self.qtimer.timeout.connect(self._handle_view_changed)
        self.qtimer.stop()

    def register_tools(self, tools: typing.List[Tool]):
        for tool in tools:
            self.register_tool(tool)

    def register_tool(self, tool: Tool):
        toolbutton = QToolButton()
        toolbutton.setCheckable(True)
        toolbutton.setAutoExclusive(True)
        toolbutton.setText(tool.tool_name)
        toolbutton.toggled.connect(lambda checked: self.handle_tool_activated(checked, tool.tool_id))
        self.ui.toolBox.layout().addWidget(toolbutton)
        self._tools.append(tool)
        param_widget = self._create_param_widget(tool)
        #self._tool_settings.addItem(param_widget, tool.tool_name)
        self._tool_param_widgets.append(param_widget)

    #def _mock_load_tools(self) -> typing.List[Tool]:
    #    return [self._mock_load_tool(i) for i in range(1)]

    #def _mock_load_tool(self, tool_id: int) -> Tool:
    #    tool = Brush()
    #    tool.set_id(tool_id)
    #    toolbutton = QToolButton()
    #    toolbutton.setCheckable(True)
    #    toolbutton.setAutoExclusive(True)
    #    toolbutton.setText(tool.tool_name)
    #    toolbutton.toggled.connect(lambda checked: self.handle_tool_activated(checked, tool_id))
    #    self.ui.toolBox.layout().addWidget(toolbutton)
    #    return tool

    def _create_param_widgets(self):
        for tool in self._tools:
            param_widget = self._create_param_widget(tool)
            self._tool_param_widgets.append(param_widget)

    def _handle_param_changed(self, tool_id: int):
        tool = self._tools[tool_id]
        param_widget = self._tool_param_widgets[tool_id]
        for param_name, param in tool.user_params.items():
            if param.param_type == ParamType.INT:
                spbox: QSpinBox = param_widget.findChild(QSpinBox, param_name)
                tool.set_user_param(param_name, spbox.value())
            elif param.param_type == ParamType.STR:
                lineedit: QLineEdit = param_widget.findChild(QLineEdit, param_name)
                tool.set_user_param(param_name, lineedit.text())
            else:
                checkbox: QCheckBox = param_widget.findChild(QCheckBox, param_name)
                tool.set_user_param(param_name, checkbox.isChecked())
        self.canvas.set_current_tool(self._current_tool)

    def _create_param_widget(self, tool: Tool):
        params: typing.Dict[str, ToolUserParam] = tool.user_params

        param_widget = QGroupBox()
        param_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        param_widget.setTitle(tool.tool_name)

        lay = QGridLayout()

        param_widget.setLayout(lay)

        for row, (param_name, param) in enumerate(params.items()):
            entry = None
            label = QLabel()
            label.setText(param_name)
            label.setObjectName(f'lbl_{param_name}')
            lay.addWidget(label, row, 0)
            if param.param_type == ParamType.INT:
                entry = QSpinBox()
                entry.setMinimum(param.min_value)
                entry.setMaximum(param.max_value)
                entry.setSingleStep(param.value_step)
                entry.setValue(param.default_value)
                entry.setObjectName(param_name)
                entry.valueChanged.connect(lambda: self._handle_param_changed(tool.tool_id))
                lay.addWidget(entry, row, 1)
                entry = None
            elif param.param_type == ParamType.STR:
                entry = QLineEdit()
                entry.setText(param.default_value)
                entry.setObjectName(param_name)
                entry.textChanged.connect(lambda: self._handle_param_changed(tool.tool_id))
                lay.addWidget(entry, row, 1)
                entry = None
            elif param.param_type == ParamType.BOOL:
                entry = QCheckBox()
                entry.setChecked(param.default_value)
                entry.setObjectName(param_name)
                entry.stateChanged.connect(lambda: self._handle_param_changed(tool.tool_id))
                lay.addWidget(entry, row, 1)
                entry = None
        return param_widget

    def _handle_spinbox_value_changed(self, tool_id: int, spbox: QSpinBox):
        print(f'changing {spbox.objectName()} of {tool_id}. tool')
        tool = self._tools[tool_id]
        tool.set_user_param(spbox.objectName(), spbox.value())

    def _handle_lineedit_text_changed(self, tool_id: int, param_name: str, text: str):
        tool = self._tools[tool_id]
        tool.set_user_param(param_name, text)

    def _handle_checkbox_toggled(self, tool_id: int, param_name: str, checked: Qt.CheckState):
        tool = self._tools[tool_id]
        tool.set_user_param(param_name, checked == Qt.CheckState.Checked)

    def set_photo(self, photo: Photo):
        self.current_photo = photo
        self.canvas.set_photo(self.current_photo)
        self._scene.setSceneRect(self.canvas.sceneBoundingRect())
        self._scene.update()
        self.photo_view.fitInView(self.canvas, Qt.KeepAspectRatio)

        rect = self.photo_view.viewport().rect()
        point = QPoint(rect.center().x() - self._glabel_line_edit.boundingRect().width() // 2,
                       rect.center().y() - self._glabel_line_edit.boundingRect().height() // 2)
        scene_point = self.photo_view.mapToScene(point)
        self._glabel_line_edit.setPos(scene_point)
        #self._glabel_line_edit.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._glabel_line_edit.setZValue(100)

        point.setY(point.y()) # + self._glabel_line_edit.boundingRect().height())
        scene_point = self.photo_view.mapToScene(point)
        self._glabel_list_view.setPos(scene_point)
        #self._glabel_list_view.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._glabel_list_view.setZValue(100)

    def handle_bug_mask_checked(self, checked: bool):
        print(f"bug {checked}")
        self.canvas.set_mask_shown(LabelType.BUG, checked)

    def handle_segments_mask_checked(self, checked: bool):
        print(f"segments {checked}")
        self.canvas.set_mask_shown(LabelType.REGIONS, checked)

    def handle_reflection_mask_checked(self, checked: bool):
        print(f"reflections {checked}")
        self.canvas.set_mask_shown(LabelType.REFLECTION, checked)

    def handle_tool_activated(self, checked: bool, tool_id: int):
        self._current_tool = self._tools[tool_id]
        self._current_tool.color_map_changed(self.state.colormap.colormap)
        self._tool_settings.setTitle(f'{self._current_tool.tool_name} settings')
        self._tool_settings.setVisible(True)
        self._tool_settings.layout().addWidget(self._tool_param_widgets[tool_id])
        self._tool_param_widgets[tool_id].setVisible(checked)
        print(f'{"activated" if checked else "deactivated"} the tool {self._current_tool.tool_name}')

    def handle_left_press(self, pos: QPointF):
        pos = pos.toPoint()

    def handle_label_changed(self, edit_img: np.ndarray):
        label_img = self.state.current_photo.label_dict[self.canvas.current_mask_shown].label_img
        #self.current_photo.label_dict[self.canvas.current_mask_shown].label_img

        new_labels = np.unique(edit_img)[1:] # filter out the -1 label which is the first on in the returned array
        command = CommandEntry()

        for label in new_labels:
            old_and_new = np.where(edit_img == label, label_img, -1)
            old_labels = np.unique(old_and_new)[1:] # filter out -1
            for old_label in old_labels:
                coords = np.nonzero(old_and_new == old_label)
                change = LabelChange(coords, label, old_label, self.canvas.current_mask_shown)
                command.add_label_change(change)
        self.redo_stack.clear() # copying GIMP's behaviour: when the user paints something, the redo stack is cleared
        self.ui.tbtnRedo.setEnabled(False)
        self.do_command(command, update_canvas=False)

    def handle_undo_clicked(self):
        command = self.undo_stack.pop()
        self.do_command(command)
        if len(self.undo_stack) == 0:
            self.ui.tbtnUndo.setEnabled(False)

    def handle_redo_clicked(self):
        command = self.redo_stack.pop()
        self.do_command(command)
        if len(self.redo_stack) == 0:
            self.ui.tbtnRedo.setEnabled(False)

    def change_labels(self, label_img: np.ndarray, change: LabelChange):
        label_img[change.coords[0], change.coords[1]] = change.new_label

    def do_command(self, command: CommandEntry, update_canvas: bool=True):
        reverse_command = CommandEntry()
        labels_changed = set()
        for change in command.change_chain:
            label_img = self.current_photo.label_dict[change.label_type].label_img
            #io.imsave('/home/radoslav/pre_change.png', 255 * label_img.astype(np.uint8))
            self.change_labels(label_img, change)
            reverse_command.add_label_change(change.swap_labels())
            labels_changed.add(change.label_type)
        reverse_command.do_type = DoType.Undo if command.do_type == DoType.Do else DoType.Do
        if reverse_command.do_type == DoType.Undo:
            self.undo_stack.append(reverse_command)
            self.ui.tbtnUndo.setEnabled(True)
        else:
            self.redo_stack.append(reverse_command)
            self.ui.tbtnRedo.setEnabled(True)

        if update_canvas:
            for label_type in labels_changed:
                self.canvas.update_label(label_type)
                #io.imsave(f'/home/radoslav/change_{label_type}.png', 255 * self.current_photo.label_dict[label_type].label_img.astype(np.uint8))
        else:
            if LabelType.BUG in labels_changed:
                self.canvas.update_clip_mask()

    def _handle_primary_label_changed(self, label: int):
        if self._current_tool is None:
            return
        self._current_tool.update_primary_label(label)
        self.canvas.cursor__.set_cursor(self._current_tool.cursor_image)

    def _handle_secondary_label_changed(self, label: int):
        if self._current_tool is None:
            return
        self._current_tool.update_secondary_label(label)
        self.canvas.update()

    def _handle_view_changed(self):
        rect = self.photo_view.viewport().rect()
        point = QPoint(rect.center().x() - self._glabel_line_edit.boundingRect().width() // 2,
                       rect.center().y() - self._glabel_line_edit.boundingRect().height() // 2)
        scene_point = self.photo_view.mapToScene(point)
        self._glabel_line_edit.setPos(scene_point)
        #self._glabel_line_edit.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._glabel_line_edit.setZValue(100)

       # point2 = QPoint(rect.center().x() - self._glabel_list_view.boundingRect().width() // 2,
       #                 point.y() + self._glabel_line_edit.boundingRect().height())
       # #point.setY(point.y()) # + self._glabel_line_edit.boundingRect().height())
       # scene_point = self.photo_view.mapToScene(point2)
        self._glabel_list_view.setPos(QPoint(0, self._glabel_line_edit.boundingRect().height()))
        #self._glabel_list_view.setPos(scene_point)
        #self._glabel_list_view.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._glabel_list_view.setZValue(102)

        self._glabel_line_edit.update()
        self._glabel_list_view.update()
        #self._glabel_list_view.widget().raise_()
        #self._label_line_edit.setFocus()
        #self._label_line_edit.raise_()

    def _show_label_search_bar(self):
        self._glabel_line_edit.setVisible(True)
        self._label_line_edit.setFocus()
        self.photo_view.allow_zoom(False)

    def _hide_label_search_bar(self):
        self.qtimer.stop()
        self._glabel_line_edit.setVisible(False)
        self.photo_view.allow_zoom(True)
