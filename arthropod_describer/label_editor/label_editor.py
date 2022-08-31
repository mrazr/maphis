import logging
import shutil
import tempfile
import typing
from pathlib import Path
from typing import Optional, List

import numpy as np
from PySide2.QtCore import Signal, QObject, QSize, QItemSelectionModel, QPoint, QModelIndex
from PySide2.QtGui import Qt, QImage, QPixmap, QColor
from PySide2.QtWidgets import QWidget, QToolButton, QGroupBox, QVBoxLayout, QGridLayout, QSizePolicy, QButtonGroup, \
    QAbstractButton, QRadioButton, QAction, QHBoxLayout, QSpacerItem, QLabel, QMenu

from arthropod_describer.common.edit_command_executor import EditCommandExecutor
from arthropod_describer.common.label_change import LabelChange, DoType, CommandEntry, CommandKind
from arthropod_describer.common.label_hierarchy import Node
from arthropod_describer.common.label_tree_model import LabelTreeModel
from arthropod_describer.common.label_tree_view import LabelTreeView
from arthropod_describer.common.local_storage import Storage
from arthropod_describer.common.photo import Photo, UpdateContext
from arthropod_describer.common.photo_layer import PhotoLayer
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool
from arthropod_describer.common.undo_manager import UndoManager
from arthropod_describer.common.user_params import UserParamWidgetBinding, \
    create_params_widget
from arthropod_describer.common.visualization_layer import VisualizationLayer
from arthropod_describer.image_viewer import ImageViewer
from arthropod_describer.label_editor.computation_widget import ComputationWidget
from arthropod_describer.label_editor.label_layer import LabelLayer
from arthropod_describer.label_editor.label_level_switch import LabelLevelSwitch
from arthropod_describer.label_editor.new_label_dialog import NewLabelDialog
from arthropod_describer.label_editor.ui_label_editor import Ui_LabelEditor

import PySide2
from PySide2.QtWidgets import QApplication


class ToolEntry:
    def __init__(self, tool: Tool, toolbutton: QToolButton, param_widget: typing.Optional[QWidget]=None):
        self.tool = tool
        self.toolbutton = toolbutton
        self.param_widget = param_widget


class LabelEditor(QObject):
    approval_changed = Signal(Photo)
    unsaved_changes = Signal()

    def __init__(self, state: State, undo_action: QAction, redo_action: QAction, cmd_executor: EditCommandExecutor):
        QObject.__init__(self)
        self.widget = QWidget()
        self.ui = Ui_LabelEditor()
        self.ui.setupUi(self.widget)

        self.ui.toolBox.setVisible(False)

        self.temp_dir = Path(tempfile.mkdtemp())

        self.state = state

        self.state.storage_changed.connect(self.handle_storage_changed)

        self._tools: typing.List[Tool] = []

        self._tools_: typing.List[ToolEntry] = []

        self.tool_param_binding: UserParamWidgetBinding = UserParamWidgetBinding(self.state)

        self._setup_image_viewer()

        self._setup_label_level_switch()

        self._current_tool: typing.Optional[Tool] = None
        self._current_tool_widget: typing.Optional[QWidget] = None

        vbox = QVBoxLayout()

        self.col_count = 5

        self._setup_toolbox()

        self._setup_new_label_dialog()
        self._setup_label_tree_widget()

        self._tool_param_widgets: typing.List[QWidget] = []

        #self.ui.tabSidebar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        #self.ui.tabPlugins.setLayout(QVBoxLayout())

        self.undo_stack: List[List[CommandEntry]] = []
        self.redo_stack: List[List[CommandEntry]] = []

        self.cmd_executor: EditCommandExecutor = cmd_executor
        self.cmd_executor.label_approval_changed.connect(self.handle_approval_changed)
        self.cmd_executor.label_image_modified.connect(self.handle_label_image_changed)
        self.undo_manager: UndoManager = self.cmd_executor.undo_manager
        self.undo_manager.enable_undo_redo.connect(self.enable_undo_redo)

        self.undo_action = undo_action
        self.redo_action = redo_action

        self.ui.tbtnUndo.clicked.connect(self.handle_undo_clicked)
        self.ui.tbtnRedo.clicked.connect(self.handle_redo_clicked)

        self.enable_undo_action(False, '')
        self.enable_redo_action(False, '')

        self.undo_action.triggered.connect(self.handle_undo_clicked)
        self.redo_action.triggered.connect(self.handle_redo_clicked)

        self._setup_center()

        self._setup_hovered_label_info()

        self.widget.setEnabled(False)

        self._label_types_btn_group = QButtonGroup()
        self._label_types_btn_group.setExclusive(True)
        self._label_types_btn_group.buttonClicked.connect(self.handle_label_type_button_clicked)
        self.ui.MaskGroup.setEnabled(True)

        #self.ui.tabRegions.setLayout(QVBoxLayout())
        self.region_computation_widget = ComputationWidget(self.state)
        #self.ui.tabRegions.layout().addStretch(2)

        #self.ui.tabMeasurements.setLayout(QVBoxLayout())
        self.measurements_computation_widget = ComputationWidget(self.state)
        #self.ui.tabMeasurements.layout().addWidget(self.measurements_computation_widget)
        #self.ui.tabMeasurements.layout().addStretch(2)

        #self._setup_sidebar()

        QObject.connect(QApplication.instance(), PySide2.QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.handle_focus_changed)

    def handle_focus_changed(self, old, now):
        # print("calling label_editor.handle_focus_changed:")
        # print(self)
        # print(old)
        # print(now)
        # print(" ")
        pass

    def _setup_label_tree_widget(self):
        self._label_tree_model = LabelTreeModel(self.state)
        self._label_tree = LabelTreeView(self.state)
        self._label_tree.setModel(self._label_tree_model)
        self._label_tree.setEditTriggers(LabelTreeView.NoEditTriggers)
        self.state.new_label_constraint.connect(self._label_tree_model.set_constraint)
        self._label_tree.setIndentation(10)
        self._label_tree.setHeaderHidden(True)
        # self._label_tree.label_clicked.connect(self._handle_primary_label_changed)
        self.state.primary_label_changed.connect(self._handle_primary_label_changed)
        self._label_tree.label_color_change.connect(self._handle_label_color_changed)
        self._label_tree.label_color_change.connect(self._label_tree_model.handle_label_color_changed)
        self._label_tree.customContextMenuRequested.connect(self._show_label_context_menu)
        self._label_tree.label_dbl_click.connect(self.modify_label_node)

        self._label_context_menu: QMenu = QMenu()
        self._label_context_action_add = QAction('New child label')
        self._label_context_action_add.setData('add-label')
        self._label_context_action_add.triggered.connect(self._add_new_label)
        self._label_context_menu.addAction(self._label_context_action_add)
        self._label_context_action_remove_leaf = QAction('Remove label')
        self._label_context_action_remove_leaf.setData('remove-leaf')
        self._label_context_menu.addAction(self._label_context_action_remove_leaf)
        self._label_context_action_remove_subtree = QAction('Remove label and children')
        self._label_context_action_remove_subtree.setData('remove-subtree')
        self._label_context_menu.addAction(self._label_context_action_remove_subtree)

    def _setup_new_label_dialog(self):
        self._new_label_dialog = NewLabelDialog(self.state)
        self._new_label_dialog.modified_label.connect(self._handle_label_node_modified)
        self._new_label_dialog.add_new_label_requested.connect(self.handle_new_label_requested)
        self._new_label_dialog.hide()

    def _show_label_context_menu(self, pos: QPoint):
        index = self._label_tree.indexAt(pos)
        if index.isValid():
            node: Node = index.internalPointer()
            self._label_context_action_add.setData(node)
            if self.state.label_hierarchy.get_level(node.label) + 1 == len(self.state.label_hierarchy.masks):
                self._label_context_action_add.setVisible(False)
            else:
                self._label_context_action_add.setVisible(True)
            if len(node.children) > 0:
                self._label_context_action_remove_leaf.setVisible(False)
                if node.label > 0:
                    self._label_context_action_remove_subtree.setData(node)
                    self._label_context_action_remove_subtree.setVisible(True)
            else:
                self._label_context_action_remove_subtree.setVisible(False)
                if node.label > 0:
                    self._label_context_action_remove_leaf.setData(node)
                    self._label_context_action_remove_leaf.setVisible(True)
            self._label_context_menu.exec_(self._label_tree.viewport().mapToGlobal(pos))
        else:
            self._label_context_action_remove_leaf.setVisible(False)
            self._label_context_action_remove_subtree.setVisible(False)
            self._label_context_action_add.setVisible(True)
            self._label_context_action_add.setData(self.state.label_hierarchy.nodes[-1])
            self._label_context_menu.exec_(self._label_tree.viewport().mapToGlobal(pos))

    def _setup_sidebar(self):
        #self.ui.tabSidebar.hide()
        pass

    # Make sure toggling the visibility of the "hovered label" info does not affect the layout
    def _setup_hovered_label_info(self):
        for i in range(self.ui.layoutLabelInfo.count()):
            sp_retain = self.ui.layoutLabelInfo.itemAt(i).widget().sizePolicy()
            sp_retain.setRetainSizeWhenHidden(True)
            self.ui.layoutLabelInfo.itemAt(i).widget().setSizePolicy(sp_retain)
        self.ui.lblLabelIcon.setPixmap(QPixmap(24, 24)) # TODO: Use some named constant for this, and for the dimensions in "self.label_color_pixmap = QPixmap(24, 24)" in app.py

    def _setup_center(self):
        pass
        #self.ui.center.removeItem(self.ui.photo_view)
        #self.ui.center.removeWidget(self.ui.tabSidebar)
        #self._photo_widget = QWidget()
        #self._photo_widget.setLayout(self.ui.photo_view)
        #rect = QApplication.desktop().availableGeometry()
        #self.splitter = QSplitter()
        #self.splitter.addWidget(self._photo_widget)
        #self.splitter.addWidget(self.ui.tabSidebar)
        #self.ui.center.addWidget(self.splitter)
        #self.ui.tabSidebar.setMaximumWidth(rect.width() / 5)
        #self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.splitter.setStretchFactor(0, 4)
        #self.splitter.setStretchFactor(1, 1)
        #self.splitter.setHandleWidth(10)

    def _setup_label_level_switch(self):
        self._label_switch = LabelLevelSwitch(self.state, self.widget)
        self.state.label_hierarchy_changed.connect(self._label_switch.set_label_hierarchy)
        #self._label_switch.label_level_switched.connect(self.visualize_label_level)#self.handle_label_level_changed)
        self._label_switch.approval_toggled.connect(self.toggle_approval_for)

        lay = QHBoxLayout()
        self.image_viewer.ui.controlBar.addWidget(self._label_switch)
        self.image_viewer.ui.controlBar.addSpacerItem(QSpacerItem(100, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))
        #self.ui.center.addWidget(self._label_switch)

    def _setup_image_viewer(self):
        for i in range(self.ui.toolBar.count()):
            item = self.ui.toolBar.itemAt(i)
            if item is None:
                continue
            #item.widget().hide()
            self.ui.toolBar.removeItem(item)
        self.image_viewer = ImageViewer(self.state)
        self.ui.photo_view.insertWidget(0, self.image_viewer)
        self.image_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.photo_layer = PhotoLayer(self.state)
        self.image_viewer.add_layer(self.photo_layer)

        self.label_layer = LabelLayer(self.state)
        self.image_viewer.add_layer(self.label_layer)
        self.label_layer.label_img_modified.connect(self.handle_label_changed)
        # self.label_layer.constraint_down.connect(self.move_constraint_down)
        # self.label_layer.constraint_up.connect(self.move_constraint_up)
        self.label_layer.cycle_constraint.connect(self.cycle_constraint)
        #self.label_layer.setOpacity(.75)
        self.ui.btnFilledStyle.clicked.connect(self.label_layer.show_mask)
        self.ui.btnFilledStyle.clicked.connect(lambda: self.ui.spinOutlineWidth.setEnabled(False))
        self.ui.btnOutlineStyle.clicked.connect(self.label_layer.show_outline)
        self.ui.btnOutlineStyle.clicked.connect(lambda: self.ui.spinOutlineWidth.setEnabled(True))

        self.ui.spinOutlineWidth.valueChanged.connect(self.label_layer.change_outline_width)

        self.ui.sliderOpacity.valueChanged.connect(lambda val: self.label_layer.setOpacity(val / 100.0))
        self.label_layer.setOpacity(self.ui.sliderOpacity.value() / 100.0)

        self.viz_layer = VisualizationLayer(self.state)
        self.image_viewer.add_layer(self.viz_layer)
        self.viz_layer.setOpacity(.75)

        self.image_viewer.ui.controlBar.addWidget(self.ui.tbtnUndo)
        self.image_viewer.ui.controlBar.addWidget(self.ui.tbtnRedo)

        self.image_viewer.ui.controlBar.addWidget(self.ui.MaskGroup)
        self.image_viewer.ui.controlBar.addWidget(self.ui.grpMaskStyle)
        lay = QHBoxLayout()
        self._label_constraint_label: QLabel = QLabel()
        lay.addWidget(self._label_constraint_label)
        self.image_viewer.ui.controlBarContainer.addWidget(self._label_constraint_label)
        #self.ui.toolBar.removeWidget(self.ui.grpImageControls)
        self.widget.layout().removeItem(self.ui.toolBar)

        self.image_viewer.photo_switched.connect(self.set_photo2)

    def register_tools(self, tools: typing.List[Tool]):
        for tool in tools:
            self.register_tool(tool)

    def register_tool(self, tool: Tool):
        toolbutton = QToolButton()
        toolbutton.setCheckable(True)
        #toolbutton.setAutoExclusive(True)
        #toolbutton.setText(tool.tool_name)
        toolbutton.setToolTip(tool.tool_name)
        if tool.tool_icon is not None:
            toolbutton.setIcon(tool.tool_icon)
            toolbutton.setIconSize(QSize(32, 32))
        #toolbutton.toggled.connect(lambda checked: self.handle_tool_activated(checked, tool.tool_id))
        row, col = len(self._tools) // self.col_count, len(self._tools) % self.col_count

        self._tools.append(tool)
        param_widget = create_params_widget(list(tool.user_params.values()), self.state)
        param_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.tool_buttons_layout.addWidget(toolbutton, row, col)
        self._tools_button_group.addButton(toolbutton, tool.tool_id)
        self._tool_param_widgets.append(param_widget)
        self.tool_settings.layout().addWidget(self._tool_param_widgets[tool.tool_id])
        param_widget.setVisible(False)
        self._tools_.append(ToolEntry(tool, toolbutton, param_widget))
        tool.cursor_changed.connect(self._handle_tool_cursor_changed)

    def _setup_toolbox(self):
        self.tool_box = QWidget()

        self.tool_box_layout = QVBoxLayout()

        self.tool_box.setLayout(self.tool_box_layout)

        self.tool_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._tools_button_group = QButtonGroup()
        self._tools_button_group.buttonToggled.connect(self.handle_tool_activated)
        self._tools_button_group.setExclusive(False)
        self.tool_buttons_widg = QWidget()
        self.tool_buttons_layout = QGridLayout()
        self.tool_buttons_widg.setLayout(self.tool_buttons_layout)
        self.tool_box_layout.addWidget(self.tool_buttons_widg)
        self.tool_box_layout.setAlignment(self.tool_buttons_widg, Qt.AlignTop)

        self.tool_settings = QGroupBox('Settings')
        self.tool_settings.setVisible(False)
        self.tool_settings_layout = QVBoxLayout()
        self.tool_settings.setLayout(self.tool_settings_layout)
        self.tool_settings.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.tool_box_layout.setAlignment(self.tool_settings, Qt.AlignTop)

        self.tool_box_layout.addWidget(self.tool_settings)

        self.tool_out_widget = QGroupBox()
        self.tool_box_layout.addWidget(self.tool_out_widget)
        #self.tool_box_layout.addStretch(2)

    def set_photo2(self, photo: Optional[Photo], reset_view: bool=False):
        #self.undo_stack.clear()
        #self.redo_stack.clear()
        if photo is None:
            # self.state.current_photo = None
            # self.image_viewer.set_photo(None, True)
            # self.enable_undo_action(False, '')
            # self.enable_redo_action(False, '')
            # self.widget.setEnabled(False)
            # self._label_tree.setEnabled(False)
            # self.region_computation_widget.setEnabled(False)
            # self.tool_box.setEnabled(False)
            self.disable()
            return
        else:
            self.enable()
        if self._current_tool is not None:
            self._current_tool.reset_tool()
        label_level = photo.approved[self.state.current_label_name]
        label_hierarchy = self.state.storage.get_label_hierarchy2(self.state.current_label_name)
        if label_level is not None:
            label_level_idx = label_hierarchy.mask_names.index(label_level)
            if label_level_idx + 1 < len(label_hierarchy.mask_names):
                unapproved_index = label_level_idx + 1
            else:
                unapproved_index = label_level_idx
        else:
            label_level_idx = -1
            unapproved_index = 0
        self._label_switch.get_level_button(unapproved_index).setChecked(True)
        #self.state.current_label_level = unapproved_index
        # self.state.current_photo = photo
        # self.image_viewer.set_photo(photo, True)
        for i in range(label_level_idx + 1):
            self._label_switch.mark_approved(i, True)
        for i in range(label_level_idx + 1, len(self._label_switch._buttons)):
            self._label_switch.mark_approved(i, False)
        #self.handle_label_level_changed(unapproved_index)

        enable_undo, enable_redo = self.undo_manager.current_undo_redo.has_commands()

        if enable_undo:
            undo_command = self.undo_manager.current_undo_redo.undo_stack[-1][0].source
        else:
            undo_command = ''

        if enable_redo:
            redo_command = self.undo_manager.current_undo_redo.redo_stack[-1][0].source
        else:
            redo_command = ''

        self.enable_undo_action(enable_undo, undo_command)
        self.enable_redo_action(enable_redo, redo_command)

    def enable_undo_redo(self, image_name: str, label_name: str, do_type: DoType, enable: bool, command_name: str):
        if image_name != self.state.current_photo.image_name: # or label_name != self.state.current_label_name:
            return
        if do_type == DoType.Undo:
            self.enable_undo_action(enable, command_name)
        else:
            self.enable_redo_action(enable, command_name)

    def handle_tool_activated(self, btn: QToolButton, checked: bool): #checked: bool, tool_id: int):
        print(f'{"activating" if checked else "deactivating"} tool id {self._tools_button_group.id(btn)}')
        tool_id = self._tools_button_group.id(btn)
        if checked:
            for btn_ in self._tools_button_group.buttons():
                if btn == btn_:
                    continue
                btn_.setChecked(False)
            self._current_tool = self._tools_[tool_id].tool
            self.tool_out_widget.setVisible(self._current_tool.set_out_widget(self.tool_out_widget))
            if self.state.colormap is not None:
                self._current_tool.color_map_changed(self.state.colormap)
            self.image_viewer.set_tool(self._current_tool)
            if len(self._current_tool.user_params.keys()) > 0:
                self.tool_settings.setVisible(True)
                if self._current_tool_widget is not None:
                    self._current_tool_widget.setVisible(False)
                    self.tool_settings.layout().removeWidget(self._current_tool_widget)
                    # self.tool_settings.layout().addWidget(self._tool_param_widgets[tool.tool_id])
                    self._current_tool_widget.deleteLater()
                self._current_tool_widget = create_params_widget(list(self._current_tool.user_params.values()), self.state)
                self.tool_param_binding = UserParamWidgetBinding(self.state)
                self.tool_param_binding.bind(list(self._current_tool.user_params.values()),
                                             self._current_tool_widget)
                self.tool_settings.layout().addWidget(self._current_tool_widget)
                self.tool_settings.setVisible(True)
                # self._tool_param_widgets[tool_id].setVisible(True)
                self._current_tool_widget.setVisible(True)
            else:
                self.tool_settings.setVisible(False)
        else:
            self._current_tool = None
            self.image_viewer.set_tool(None)
            self._tool_param_widgets[tool_id].setVisible(False)
            self.tool_settings.setVisible(False)
            self.tool_out_widget.setVisible(False)
        self.tool_settings.update()

    def handle_label_changed(self, command: Optional[CommandEntry]):
        if command is None:
            return
        command.image_name = self.state.current_photo.image_name
        commands = [command]

        command.old_approval = self.state.current_photo.approved[self.state.current_label_name]
        # self.remove_approval2(self.state.label_hierarchy.mask_names[self.state.current_label_level])
        lab_hier = self.state.label_hierarchy
        current_level = self.state.current_label_level
        approval_level = -1 if self.state.current_photo.approved[self.state.current_label_name] is None else lab_hier.mask_names.index(self.state.current_photo.approved[self.state.current_label_name])
        if current_level <= approval_level:
            self.remove_approval2(lab_hier.mask_names[current_level])
        command.new_approval = self.state.current_photo.approved[self.state.current_label_name]
        # redo_stack = self.undo_manager.current_undo_redo.redo_stack
        # redo_stack.clear()
        # self.redo_stack.clear()
        # self.enable_redo_action(False)
        # self.do_commands(commands)
        self.cmd_executor.undo_manager.current_undo_redo.clear_redo()
        self.cmd_executor.do_commands(commands)
        self.state.current_photo.recompute_bbox()

    def handle_label_image_changed(self, image_name: str, label_name: str):
        if image_name != self.state.current_photo.image_name and label_name != self.state.current_label_name:
            return
        # self.switch_label_type(label_name)

    def handle_undo_clicked(self):
        self.reset_tool()
        undo_stack = self.undo_manager.current_undo_redo.undo_stack
        if (cmd := undo_stack[-1][0]).command_kind == CommandKind.LabelImgChange:
            if cmd.label_name != self.state.current_label_name:
                btn: QRadioButton = next(filter(lambda btn: btn.objectName() == cmd.label_name, self._label_types_btn_group.buttons()))
                btn.animateClick(1)
                return
        # commands = self.undo_stack.pop()
        commands = undo_stack.pop()
        # self.do_commands(commands)
        self.cmd_executor.do_commands(commands)
        # if len(self.undo_stack) == 0:
        if len(undo_stack) == 0:
            self.undo_action.setText('Undo')
            self.enable_undo_action(False, '')
        else:
            # self.undo_action.setText(f'Undo {self.undo_stack[-1][0].source}')
            self.undo_action.setText(f'Undo {undo_stack[-1][0].source}')
        self.redo_action.setText(f'Redo {commands[0].source}')
        self.state.current_photo.recompute_bbox()

        self.label_layer.set_label_name(self.state.current_label_name)

    def enable_undo_action(self, enable: bool, command_name: str):
        self.undo_action.setEnabled(enable)
        if enable:
            self.undo_action.setText(f'Undo {command_name}')
            self.ui.tbtnUndo.setToolTip(f'Undo {command_name}')
        self.ui.tbtnUndo.setEnabled(enable)

    def enable_redo_action(self, enable: bool, command_name: str):
        self.redo_action.setEnabled(enable)
        if enable:
            self.undo_action.setText(f'Redo {command_name}')
            self.ui.tbtnRedo.setToolTip(f'Redo {command_name}')
        self.ui.tbtnRedo.setEnabled(enable)

    def handle_redo_clicked(self):
        self.reset_tool()
        # commands = self.redo_stack.pop()
        redo_stack = self.undo_manager.current_undo_redo.redo_stack
        if (cmd := redo_stack[-1][0]).command_kind == CommandKind.LabelImgChange:
            if cmd.label_name != self.state.current_label_name:
                btn: QRadioButton = next(filter(lambda btn: btn.objectName() == cmd.label_name, self._label_types_btn_group.buttons()))
                btn.animateClick(1)
                return
        commands = redo_stack.pop()
        # self.do_commands(commands)
        self.cmd_executor.do_commands(commands)
        # if len(self.redo_stack) == 0:
        if len(redo_stack) == 0:
            self.redo_action.setText('Redo')
            self.enable_redo_action(False, '')
        else:
            # self.redo_action.setText(f'Redo {self.redo_stack[-1][0].source}')
            self.redo_action.setText(f'Redo {redo_stack[-1][0].source}')
        self.undo_action.setText(f'Undo {commands[0].source}')
        self.state.current_photo.recompute_bbox()
        self.label_layer.set_label_name(self.state.current_label_name)

    def change_labels(self, label_img: np.ndarray, change: LabelChange):
        label_img[change.coords[0], change.coords[1]] = change.new_label

    def do_command(self, command: CommandEntry, update_canvas: bool=True) -> CommandEntry:
        reverse_command = CommandEntry(source=command.source)
        labels_changed = set()
        for change in command.change_chain:
            label_img = self.state.current_photo[change.label_name].label_image
            self.change_labels(label_img, change)
            self.state.current_photo[change.label_name].set_dirty()
            reverse_command.add_label_change(change.swap_labels())
            labels_changed.add(change.label_name)
        reverse_command.do_type = DoType.Undo if command.do_type == DoType.Do else DoType.Do

        if command.update_canvas:
            for label_type in labels_changed:
                if label_type == self.state.current_label_name:
                    self.label_layer.set_label_name(label_type)

        return reverse_command

    def do_commands(self, commands: typing.List[CommandEntry], update_canvas: bool=True):
        reverse_commands = [self.do_command(command) for command in commands]

        do_type = reverse_commands[0].do_type

        undo_redo = self.undo_manager.current_undo_redo

        if do_type == DoType.Undo:
            # self.undo_stack.append(reverse_commands)
            # undo_redo.undo_stack.append(reverse_commands)
            undo_redo.push(do_type, reverse_commands)
            self.undo_action.setText(f'Undo {reverse_commands[0].source}')
            # self.enable_undo_action(True)
        else:
            # self.redo_stack.append(reverse_commands)
            # undo_redo.redo_stack.append(reverse_commands)
            undo_redo.push(do_type, reverse_commands)
            self.redo_action.setText(f'Redo {reverse_commands[0].source}')
            # self.enable_redo_action(True)

        self.state.label_img = self.state.current_photo[self.state.current_label_name]

        self.remove_approval_for(self.state.label_hierarchy.mask_names[self.state.current_label_level])
        self.unsaved_changes.emit()

    def _handle_primary_label_changed(self, label: int):
        # self.state.primary_label = label
        if self.state.storage is None:
            return
        if label > 0:
            label_level = self.state.storage.get_label_hierarchy2(self.state.current_label_name).get_level(label)
            lab_hier = self.state.storage.get_label_hierarchy2(self.state.current_label_name)
            label_node = lab_hier.nodes[label]
            label_level_to_visualize = label_level if len(label_node.children) > 0 else len(lab_hier.mask_names) - 1
            self.visualize_label_level(label_level_to_visualize)
        if self.state.redraw_canvas:
            self.label_layer.handle_primary_label_changed()
        # TODO this `if` prevents the code below
        if self._current_tool is None:
            return
        self._current_tool.update_primary_label(label)
        self.viz_layer.set_tool(self._current_tool)

    def _handle_tool_cursor_changed(self, tool_id: int, cursor_image: QImage):
        if self._current_tool.tool_id == tool_id:
            self.image_viewer.set_tool(self._tools[tool_id])

    def handle_label_level_changed(self, level: int):
        old_redraw = self.state.redraw_canvas
        self.state.redraw_canvas = False
        self.state.current_label_level = level
        self.label_layer.switch_label_level(level)
        self.state.redraw_canvas = old_redraw and True

    def visualize_label_level(self, level: int):
        self.state.current_label_level = level
        self.label_layer.switch_label_level(level)

    def handle_label_picked(self, label: int):
        level = self.state.label_hierarchy.get_level(label)
        if self.state.current_label_level != level:
            self._label_switch._buttons[level].animateClick(1)
        self.colormap_widget.handle_label_picked(label)

    def handle_storage_changed(self, storage: Storage, old_storage: typing.Optional[Storage]):
        storage.update_photo.connect(self._handle_update_photo)
        self._label_tree_model.beginResetModel()
        for btn in self._label_types_btn_group.buttons():
            btn.setVisible(False)
            self.ui.MaskGroup.layout().removeWidget(btn)
            self._label_types_btn_group.removeButton(btn)
        self.ui.MaskGroup.update()
        for i, label_name in enumerate(sorted(storage.label_image_names)):
            btn = QRadioButton(label_name)#QPushButton(label_name)
            btn.setObjectName(label_name)
            btn.setCheckable(True)
            if label_name == self.state.storage.default_label_image:
                btn.setChecked(True)
            btn.setAutoExclusive(True)
            self.ui.MaskGroup.layout().addWidget(btn)
            self._label_types_btn_group.addButton(btn, i)
        self.state.current_label_name = self.state.storage.default_label_image
        self._update_editing_constraint_label()
        self.ui.MaskGroup.setEnabled(True)
        self._label_tree_model.endResetModel()
        self._label_tree.setModel(self._label_tree_model)
        self._label_tree.expandAll()
        self._label_tree.resizeColumnToContents(0)

        self.undo_manager.initialize(self.state.storage)
        self.image_viewer.set_storage(self.state.storage)

    def _handle_update_photo(self, img_name: str, ctx: UpdateContext, data: Optional[typing.Dict[str, typing.Any]]):
        return
        if ctx == UpdateContext.Photo:
            print(f'reacting to Photo update for {img_name}')
            if img_name == self.state.current_photo.image_name:
                self.set_photo2(self.state.storage.get_photo_by_name(img_name))

    def handle_label_type_button_clicked(self, btn: QAbstractButton):
        # TODO This is only a temporary fix for Issue #23
        if btn.text() == self.state.current_label_name:
            return
        self.switch_label_type(btn.text())

    def switch_label_type(self, label_name: str):
        self.reset_tool()
        self._label_tree_model.beginResetModel()
        old_redraw = self.state.redraw_canvas
        self.state.redraw_canvas = False
        self.state.current_label_name = label_name
        self._label_switch.set_label_hierarchy(
            self.state.storage.get_label_hierarchy2(self.state.current_label_name)
        )
        lab_hier = self.state.storage.get_label_hierarchy2(self.state.current_label_name)

        approved_level = self.state.current_photo.approved[self.state.current_label_name]
        approved_level_index = -1 if approved_level is None else lab_hier.mask_names.index(approved_level)

        self.approve_level(approved_level)

        #level_to_set_index = min(approved_level_index + 1, len(lab_hier.mask_names) - 1)
        #self.state.current_label_level = level_to_set_index
        #self._label_switch.selected_label_levels[self.state.current_label_name] = level_to_set_index
        #self._label_switch.return_to_level_for(self.state.current_label_name)

        hide = set(self.state.current_photo.label_image_info.keys())
        print(hide)
        hide.remove(label_name)
        if self.state.current_photo is None:
            logging.info(f'LE - state.current_photo is None, returning')
            return
        lbl_img = self.state.current_photo[label_name]
        self.state.label_img = lbl_img

        self.cmd_executor.enforce_within_mask(self.state.current_photo, self.state.current_label_name)

        self.label_layer.set_label_name(label_name)

        self.state.redraw_canvas = old_redraw and True
        self._label_tree_model.endResetModel()
        self._label_tree.expandAll()
        self._label_tree.resizeColumnToContents(0)
        #index = self._label_tree_model.index(0, 0)
        index = self._label_tree_model.find_index(self.state.primary_label)
        self._label_tree.setModel(self._label_tree_model)
        self._label_tree.selectionModel().setCurrentIndex(index,
                                                          QItemSelectionModel.Select)
        self._label_tree._handle_index_activated(index)
        self._update_editing_constraint_label()

        enable_undo, enable_redo = self.undo_manager.current_undo_redo.has_commands()

        if enable_undo:
            undo_command = self.undo_manager.current_undo_redo.undo_stack[-1][0].source
        else:
            undo_command = ''

        if enable_redo:
            redo_command = self.undo_manager.current_undo_redo.redo_stack[-1][0].source
        else:
            redo_command = ''

        self.enable_undo_action(enable_undo, undo_command)
        self.enable_redo_action(enable_redo, redo_command)

        # TODO scenario - set a constraint and label in Labels, switch to Reflections, switch back to Labels, and I'm not able to draw withing 'Animal'
        if self.state.current_constraint.constraint_label_name == self.state.current_label_name:
            if self.state.current_constraint.label_node.label > 0:
                index = self._label_tree_model.find_index(self.state.current_constraint.label_node.label).siblingAtColumn(1)
                self._label_tree.set_constraint(index)

    def _update_editing_constraint_label(self):
        if (lbl_info := self.state.storage.label_img_info[self.state.current_label_name]).constrain_to is not None:
            constr_lab_hier = self.state.storage.get_label_hierarchy2(lbl_info.constrain_to)
            self._label_constraint_label.setText(f'Editing constrained to {lbl_info.constrain_to} - {constr_lab_hier.mask_label.name}')
        else:
            self._label_constraint_label.setText("")

    def _toggle_approval_of_mask(self):
        lab_hier = self.state.storage.get_label_hierarchy2(self.state.current_label_name)
        recent_approval = self.state.current_photo.approved[self.state.current_label_name]

        recent_approval_index = -1 if recent_approval is None else lab_hier.mask_names.index(recent_approval)

        level_name = lab_hier.mask_names[self.state.current_label_level]
        level_name_index = lab_hier.mask_names.index(level_name)
        if level_name_index <= recent_approval_index:
            self.remove_approval_for(level_name)
        else:
            self.approve_level(level_name)
        self.approval_changed.emit(self.state.current_photo)

    def remove_approval_for(self, level_name: str):
        lab_hier = self.state.storage.get_label_hierarchy2(self.state.current_label_name)
        index = lab_hier.mask_names.index(level_name)
        #for i, name in enumerate(lab_hier.mask_names[index:]):
        for i in range(len(lab_hier.mask_names)):
            self._label_switch.mark_approved(i, False)
        #index -= 1
        demote_to = None
        if index > 0:
            demote_to = lab_hier.mask_names[index-1]
        self.approve_level(demote_to)
        #self.state.current_photo.approved[self.state.current_label_name] = demote_to
        #self.approval_changed.emit(self.state.current_photo)

    def remove_approval2(self, level_name: str):
        if level_name is None or level_name == '':
            return
        lab_hier = self.state.storage.get_label_hierarchy2(self.state.current_label_name)
        index = lab_hier.mask_names.index(level_name)
        for i in range(len(lab_hier.mask_names) - 1, index-1, -1):
            self._label_switch.mark_approved(i, False)
        demote_to = None
        if index > 0:
            demote_to = lab_hier.mask_names[index-1]
        self.state.current_photo.approved[self.state.current_label_name] = demote_to
        self.approval_changed.emit(self.state.current_photo)

    def approve_level(self, level_name: str):
        for i in range(len(self.state.label_hierarchy.mask_names)):
            self._label_switch.mark_approved(i, False)
        self.state.current_photo.approved[self.state.current_label_name] = level_name
        lab_hier = self.state.storage.get_label_hierarchy2(self.state.current_label_name)
        if level_name is not None and level_name != '':
            index = lab_hier.mask_names.index(level_name)
            for i, name in enumerate(lab_hier.mask_names[:index+1]):
                self._label_switch.mark_approved(i, True)
        else:
            for i in range(len(lab_hier.mask_names)):
                self._label_switch.mark_approved(i, False)
        #if index + 1 < len(lab_hier.mask_names):
        #    self._label_switch.get_level_button(index + 1).animateClick(1)
        #else:
        #    # TODO SWITCH TO NEXT PHOTO
        #    pass
        self.approval_changed.emit(self.state.current_photo)

    def toggle_approval_for(self, level_idx: int, approved: bool):
        level_name = self.state.storage.get_label_hierarchy2(self.state.current_label_name).mask_names[level_idx]
        if approved:
            self.approve_level(level_name)
        else:
            self.remove_approval2(level_name)

    def handle_approval_changed(self, image_name: str, label_name: str, approval: Optional[str]):
        approval = None if approval == '' else approval
        photo = self.state.storage.get_photo_by_name(image_name, load_image=False)
        if image_name == self.state.current_photo.image_name:
            # self.remove_approval2(photo.approved[self.state.current_label_name])
            self.approve_level(approval)
        else:
            photo.approved[label_name] = approval

    def reset_tool(self):
        if self._current_tool is not None:
            self._current_tool.reset_tool()
        self.viz_layer.reset()

    def release_resources(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _handle_label_color_changed(self, label: int, color: QColor):
        self.state.colormap[label] = color.toTuple()[:3]
        self.label_layer._recolor_image()

    def _handle_label_node_modified(self, label: int, name: str, color: QColor):
        label_node: Node = self.state.label_hierarchy.nodes[label]
        label_node.name = name
        if color.isValid():
            label_node.color = color.toTuple()[:3]
            self.state.colormap[label] = label_node.color
            self.label_layer._recolor_image()
        index = self._label_tree_model.find_index(label)
        self._label_tree_model.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.DecorationRole])

    def modify_label_node(self, node: Node):
        self._new_label_dialog.modify_label(node.label)

    def _add_new_label(self):
        node: Node = self._label_context_action_add.data()
        self._new_label_dialog.add_new_label(node.label)

    def handle_new_label_requested(self, parent: int, name: str, color: QColor):
        if parent >= 0:
            parent_index = self._label_tree_model.find_index(parent)
            parent_node: Node = parent_index.internalPointer()
        else:
            parent_index = QModelIndex()
            parent_node: Node = self.state.label_hierarchy.nodes[-1]

        added_label: Node = self.state.label_hierarchy.add_child_label(parent, name, color.toTuple()[:3])
        row = len(parent_node.children) - 1
        self._label_tree_model.beginInsertRows(parent_index, row, row)
        self._label_tree_model.insertRow(row, parent_index)
        self._label_tree_model.endInsertRows()
        new_index = self._label_tree_model.find_index(added_label.label)
        self._label_tree_model.dataChanged.emit(new_index, new_index)
        if parent_index.isValid():
            self._label_tree.expand(parent_index)

    def move_constraint_up(self, label: int):
        curr_constraint = self.state.current_constraint.label
        const_level = self.state.label_hierarchy.get_level(curr_constraint)
        const_parent = self.state.label_hierarchy.parents[curr_constraint]
        if const_parent == -1:
            self._label_tree._unset_constraint(set_constraint_button=False)
        else:
            index = self._label_tree_model.find_index(const_parent).siblingAtColumn(1)
            self._label_tree.set_constraint(index)

    def move_constraint_down(self, label: int):
        ancestors = list(reversed(self.state.label_hierarchy.get_ancestors(label)))
        ancestors.append(label)
        curr_const_level = self.state.label_hierarchy.get_level(self.state.current_constraint.label)
        if curr_const_level + 1 > self.state.label_hierarchy.get_level(label):
            return
        index = self._label_tree_model.find_index(ancestors[curr_const_level + 1]).siblingAtColumn(1)
        self._label_tree.set_constraint(index)

    def cycle_constraint(self, label: int, direction: int):
        ancestors = list(reversed(self.state.label_hierarchy.get_ancestors(label)))
        ancestors.append(label)
        ancestors.append(0)
        if self.state.current_constraint.label > 0:
            curr_const_level = self.state.label_hierarchy.get_level(self.state.current_constraint.label)
        else:
            curr_const_level = -1
        next_constraint = ancestors[(curr_const_level + direction) % len(ancestors)]
        if next_constraint == 0:
            self._label_tree._unset_constraint(set_constraint_button=False)
        else:
            index = self._label_tree_model.find_index(next_constraint).siblingAtColumn(1)
            self._label_tree.set_constraint(index)

    def disable(self):
        self.enable_undo_action(False, '')
        self.enable_redo_action(False, '')
        # self.widget.setEnabled(False)
        self.image_viewer.setEnabled(False)
        self._label_tree.setEnabled(False)
        self.region_computation_widget.setEnabled(False)
        self.tool_box.setEnabled(False)

    def enable(self):
        # self.widget.setEnabled(True)
        self.image_viewer.setEnabled(True)
        self._label_tree.setEnabled(True)
        self.region_computation_widget.setEnabled(True)
        self.tool_box.setEnabled(True)
