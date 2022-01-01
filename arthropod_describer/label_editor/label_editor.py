import typing
from typing import Optional, List
import logging

from PySide2.QtCore import Signal, QObject, QPointF, QPoint, QTimer
from PySide2.QtGui import Qt, QImage
from PySide2.QtWidgets import QWidget, QGraphicsScene, QToolButton, QGroupBox, QVBoxLayout, QSpinBox, QLineEdit, \
    QCheckBox, QGridLayout, QLabel, QSizePolicy, QGraphicsProxyWidget, QGraphicsItem
import numpy as np
from skimage import io

from arthropod_describer.common.label_change import LabelChange, DoType, CommandEntry, propagate_mask_changes_to
from arthropod_describer.common.state import State
from arthropod_describer.label_editor.colormap_widget import ColormapWidget
from arthropod_describer.common.tool import Tool
from arthropod_describer.common.user_params import ToolUserParam, ParamType
from arthropod_describer.custom_graphics_view import CustomGraphicsView
from arthropod_describer.label_editor.canvas_widget import CanvasWidget
from arthropod_describer.label_editor.ui_label_editor import Ui_LabelEditor
from arthropod_describer.common.photo import Photo, LabelType, LabelImg


class ToolEntry:
    def __init__(self, tool: Tool, toolbutton: QToolButton, param_widget: typing.Optional[QWidget]=None):
        self.tool = tool
        self.toolbutton = toolbutton
        self.param_widget = param_widget


class LabelEditor(QObject):
    signal_next_photo = Signal()
    signal_prev_photo = Signal()

    def __init__(self, state: State):
        QObject.__init__(self)
        self.widget = QWidget()
        self.ui = Ui_LabelEditor()
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

        self._tools_: typing.List[ToolEntry] = []

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
        self.canvas.label_changed.connect(self.handle_label_changed)
        self.photo_view.view_dragging.connect(self.canvas.handle_view_dragging)

        vbox = QVBoxLayout()

        self.colormap_widget = ColormapWidget()
        self.colormap_widget.primary_label_changed.connect(self._handle_primary_label_changed)
        self.colormap_widget.secondary_label_changed.connect(self._handle_secondary_label_changed)
        self.state.label_img_changed.connect(lambda lbl_img: self.colormap_widget.handle_label_type_changed(lbl_img.label_type))
        vbox.addWidget(self.colormap_widget)

        self._tool_settings = QGroupBox('Tool settings')
        self._tool_settings.setLayout(QVBoxLayout())
        #self._tools: typing.List[Tool] = self._mock_load_tools()
        self._tool_param_widgets: typing.List[QWidget] = []

        self._current_tool: typing.Optional[Tool] = None

        vbox.addWidget(self._tool_settings)
        self._tool_settings.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        #vbox.addStretch(2)

        self.side_widget = QWidget()
        self.side_widget.setLayout(vbox)
        self.side_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self.ui.center.addWidget(self.side_widget)

        #self._current_tool = self._tools[0]
        #self.canvas.set_current_tool(self._tools[0])
        self.ui.tbtnBugMask.animateClick()
        self.handle_reflection_mask_checked(False)
        self.handle_segments_mask_checked(False)

        self.undo_stack: List[List[CommandEntry]] = []
        self.redo_stack: List[List[CommandEntry]] = []

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
        self._tools_.append(ToolEntry(tool, toolbutton, param_widget))
        tool.cursor_changed.connect(self._handle_tool_cursor_changed)

    def _create_param_widgets(self):
        for tool in self._tools:
            param_widget = self._create_param_widget(tool)
            self._tool_param_widgets.append(param_widget)

    def _handle_param_changed(self, tool_id: int):
        tool = self._tools_[tool_id].tool
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
        #self.canvas.set_current_tool(self._current_tool)

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
        tool = self._tools_[tool_id].tool
        tool.set_user_param(spbox.objectName(), spbox.value())

    def _handle_lineedit_text_changed(self, tool_id: int, param_name: str, text: str):
        tool = self._tools_[tool_id].tool
        tool.set_user_param(param_name, text)

    def _handle_checkbox_toggled(self, tool_id: int, param_name: str, checked: Qt.CheckState):
        tool = self._tools_[tool_id].tool
        tool.set_user_param(param_name, checked == Qt.CheckState.Checked)

    def set_photo(self, photo: Photo):
        logging.info(f'LE - Setting a new photo to {photo.image_name}')
        #self.current_photo = photo
        self.canvas.set_photo_(self.state.current_photo)

        self.show_whole_image()

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

        self.state.label_img = self.state.current_photo[self.canvas.current_mask_shown]

    def show_whole_image(self):
        self._scene.setSceneRect(self.canvas.sceneBoundingRect())
        self._scene.update()
        logging.info(f'LE - fitting image into view, canvas rect is {self.canvas.boundingRect()}')
        logging.info(f'LE - photo size is {self.state.current_photo.image.size().toTuple()}')
        self.photo_view.fitInView(self.canvas, Qt.KeepAspectRatio)

    def handle_bug_mask_checked(self, checked: bool):
        if checked:
            self.switch_label_image(LabelType.BUG)
        #if self.state.current_photo is None:
        #    return
        #print(f"bug {checked}")
        #if not self.state.current_photo.bug_mask.is_set:
        #    #LabelImg.assign_to_photo(self.current_photo, LabelType.BUG)
        #    self.state.current_photo.bug_mask.make_empty(self.state.current_photo.image.size().toTuple())
        #    self.canvas.mask_widgets[LabelType.BUG].set_mask_image(self.state.current_photo.bug_mask)
        #self.canvas.set_mask_shown(LabelType.BUG, checked)
        #if checked and self.state.label_img is not None:
        #    self.state.label_img = self.state.current_photo[LabelType.BUG]

    def handle_segments_mask_checked(self, checked: bool):
        if checked:
            self.switch_label_image(LabelType.REGIONS)
        #if self.state.current_photo is None:
        #    return
        #print(f"segments {checked}")
        #if not self.state.current_photo.segments_mask.is_set:
        #    #LabelImg.assign_to_photo(self.current_photo, LabelType.REGIONS)
        #    self.state.current_photo.segments_mask.make_empty(self.state.current_photo.image.size().toTuple())
        #    self.canvas.mask_widgets[LabelType.REGIONS].set_mask_image(self.state.current_photo.segments_mask)
        #self.canvas.set_mask_shown(LabelType.REGIONS, checked)
        #if checked and self.state.label_img is not None:
        #    self.state.label_img = self.state.current_photo[LabelType.REGIONS]

    def handle_reflection_mask_checked(self, checked: bool):
        if checked:
            self.switch_label_image(LabelType.REFLECTION)
       # print(f"reflections {checked}")
       # if self.state.current_photo is None:
       #     return
       # if not self.state.current_photo.reflection_mask.is_set:
       #     #LabelImg.assign_to_photo(self.current_photo, LabelType.REFLECTION)
       #     self.current_photo.reflection_mask.make_empty(self.current_photo.image.size().toTuple())
       #     self.canvas.mask_widgets[LabelType.REFLECTION].set_mask_image(self.current_photo.reflection_mask)
       # self.canvas.set_mask_shown(LabelType.REFLECTION, checked)
       # if checked and self.state.label_img is not None:
       #     self.state.label_img = self.current_photo[LabelType.REFLECTION]

    def switch_label_image(self, label_type: LabelType):
        logging.info(f'LE - Retrieving {repr(label_type)}')
        hide = set(list(LabelType))
        hide.remove(label_type)
        for hide_label in hide:
            logging.info(f'Hiding label {repr(hide_label)}')
            self.canvas.set_mask_shown(hide_label, False)
        if self.state.current_photo is None:
            logging.info(f'LE - state.current_photo is None, returning')
            return
        lbl_img = self.state.current_photo[label_type]
        self.state.label_img = lbl_img
        self.canvas.set_mask_shown(label_type, True)

    def handle_tool_activated(self, checked: bool, tool_id: int):
        if checked:
            self._current_tool = self._tools_[tool_id].tool
            if self.state.colormap is not None:
                self._current_tool.color_map_changed(self.state.colormap.colormap)
            self.canvas.set_current_tool(self._current_tool)
            self._tool_settings.setTitle(f'{self._current_tool.tool_name} settings')
            self._tool_settings.setVisible(True)
            self._tool_settings.layout().addWidget(self._tool_param_widgets[tool_id])
        self._tool_param_widgets[tool_id].setVisible(checked)
        print(f'{"activated" if checked else "deactivated"} the tool {self._current_tool.tool_name}')

    def handle_label_changed(self, lab_changes: typing.List[LabelChange]):
        #label_img = self.state.current_photo.label_dict[self.canvas.current_mask_shown].label_img
        ##self.current_photo.label_dict[self.canvas.current_mask_shown].label_img

        #new_labels = np.unique(edit_img)[1:] # filter out the -1 label which is the first on in the returned array
        #command = CommandEntry()

        #for label in new_labels:
        #    old_and_new = np.where(edit_img == label, label_img, -1)
        #    old_labels = np.unique(old_and_new)[1:] # filter out -1
        #    for old_label in old_labels:
        #        coords = np.nonzero(old_and_new == old_label)
        #        change = LabelChange(coords, label, old_label, self.canvas.current_mask_shown)
        #        command.add_label_change(change)
        #self.redo_stack.clear() # copying GIMP's behaviour: when the user paints something, the redo stack is cleared
        #self.ui.tbtnRedo.setEnabled(False)
        #self.do_command(command, update_canvas=False)

        if len(lab_changes) == 0:
            return
        photo = self.state.current_photo
        command = CommandEntry(lab_changes, label_type=self.canvas.current_mask_shown, update_canvas=False)
        commands = [command]

        if command.label_type == LabelType.BUG:
            if photo.segments_mask.is_set:
                if (cmd_for_regions := propagate_mask_changes_to(photo.segments_mask, command)) is not None:
                    commands.append(cmd_for_regions)
            if photo.reflection_mask.is_set:
                if (cmd_for_reflections := propagate_mask_changes_to(photo.reflection_mask, command)) is not None:
                    commands.append(cmd_for_reflections)

        self.redo_stack.clear()
        self.ui.tbtnRedo.setEnabled(False)
        self.do_commands(commands)
        #io.imsave('/home/radoslav/knife_regions.tif', self.current_photo.label_dict[LabelType.REGIONS].label_img)

    def handle_undo_clicked(self):
        commands = self.undo_stack.pop()
        self.do_commands(commands)
        if len(self.undo_stack) == 0:
            self.ui.tbtnUndo.setEnabled(False)

    def handle_redo_clicked(self):
        commands = self.redo_stack.pop()
        self.do_commands(commands)
        if len(self.redo_stack) == 0:
            self.ui.tbtnRedo.setEnabled(False)

    def change_labels(self, label_img: np.ndarray, change: LabelChange):
        label_img[change.coords[0], change.coords[1]] = change.new_label

    def do_command(self, command: CommandEntry, update_canvas: bool=True) -> CommandEntry:
        reverse_command = CommandEntry(label_type=command.label_type)
        labels_changed = set()
        for change in command.change_chain:
            label_img = self.state.current_photo[change.label_type].label_img
            #io.imsave('/home/radoslav/pre_change.png', 255 * label_img.astype(np.uint8))
            self.change_labels(label_img, change)
            reverse_command.add_label_change(change.swap_labels())
            labels_changed.add(change.label_type)
        reverse_command.do_type = DoType.Undo if command.do_type == DoType.Do else DoType.Do

        if command.update_canvas:
            for label_type in labels_changed:
                self.canvas.update_label(label_type)
                #io.imsave(f'/home/radoslav/change_{label_type}.png', 255 * self.current_photo.label_dict[label_type].label_img.astype(np.uint8))
        else:
            if LabelType.BUG in labels_changed:
                self.canvas.update_clip_mask()

        return reverse_command

    def do_commands(self, commands: typing.List[CommandEntry], update_canvas: bool=True):
        reverse_commands = [self.do_command(command) for command in commands]

        labels_changed = set([command.label_type for command in commands])

        do_type = reverse_commands[0].do_type

        if do_type == DoType.Undo:
            self.undo_stack.append(reverse_commands)
            self.ui.tbtnUndo.setEnabled(True)
        else:
            self.redo_stack.append(reverse_commands)
            self.ui.tbtnRedo.setEnabled(True)

        #if update_canvas:
        #    for label_type in labels_changed:
        #        self.canvas.update_label(label_type)
        #        #io.imsave(f'/home/radoslav/change_{label_type}.png', 255 * self.current_photo.label_dict[label_type].label_img.astype(np.uint8))
        #else:
        #    if LabelType.BUG in labels_changed:
        #        self.canvas.update_clip_mask()

    def _handle_primary_label_changed(self, label: int):
        self.state.primary_label = label
        if self._current_tool is None:
            return
        self._current_tool.update_primary_label(label)
        self.canvas.cursor__.set_cursor(self._current_tool.cursor_image)

    def _handle_secondary_label_changed(self, label: int):
        self.state.secondary_label = label
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
        self._glabel_line_edit.setZValue(100)

        self._glabel_list_view.setPos(QPoint(0, self._glabel_line_edit.boundingRect().height()))
        self._glabel_list_view.setZValue(102)

        self._glabel_line_edit.update()
        self._glabel_list_view.update()

    def _show_label_search_bar(self):
        self._glabel_line_edit.setVisible(True)
        self._label_line_edit.setFocus()
        self.photo_view.allow_zoom(False)

    def _hide_label_search_bar(self):
        self.qtimer.stop()
        self._glabel_line_edit.setVisible(False)
        self.photo_view.allow_zoom(True)

    def _handle_tool_cursor_changed(self, tool_id: int, cursor_image: QImage):
        if self.canvas._current_tool.tool_id == tool_id:
            self.canvas.cursor__.set_cursor(cursor_image)
