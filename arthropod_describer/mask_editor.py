import typing
from typing import Optional

from PySide2.QtCore import Signal, QObject, QPointF
from PySide2.QtGui import Qt
from PySide2.QtWidgets import QWidget, QGraphicsScene, QToolButton, QGroupBox, QVBoxLayout, QSpinBox, QLineEdit, \
    QCheckBox, QGridLayout, QLabel, QSizePolicy, QToolBox

from tools.tool import Tool, Brush, ToolUserParam, ParamType
from custom_graphics_view import CustomGraphicsView
from canvas_widget import CanvasWidget
from view.ui_mask_edit_view import Ui_MaskEditor
from model.photo import Photo, MaskType


class ToolEntry:
    def __init__(self, tool: Tool, toolbutton: QToolButton, param_widget: typing.Optional[QWidget]=None):
        self.tool = tool
        self.toolbutton = toolbutton
        self.param_widget = param_widget


class MaskEditor(QObject):
    signal_next_photo = Signal()
    signal_prev_photo = Signal()

    def __init__(self):
        QObject.__init__(self)
        self.widget = QWidget()
        self.ui = Ui_MaskEditor()
        self.ui.setupUi(self.widget)

        self.ui.tbtnBugMask.toggled.connect(self.handle_bug_mask_checked)
        self.ui.tbtnSegmentsMask.toggled.connect(self.handle_segments_mask_checked)
        self.ui.tbtnReflectionMask.toggled.connect(self.handle_reflection_mask_checked)
        self.ui.btnNext.clicked.connect(lambda: self.signal_next_photo.emit())
        self.ui.btnPrevious.clicked.connect(lambda: self.signal_prev_photo.emit())

        self._scene = QGraphicsScene()

        self.photo_view = CustomGraphicsView()
        self.ui.center.addWidget(self.photo_view)
        self.photo_view.setScene(self._scene)
        self.photo_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.photo_view.setInteractive(True)

        self.canvas = CanvasWidget()
        self._scene.addItem(self.canvas)
        self.canvas.initialize()
        self.canvas.left_press.connect(self.handle_left_press)
        self.photo_view.view_dragging.connect(self.canvas.handle_view_dragging)

        self.current_photo: Optional[Photo] = None
        self._toolbox = QToolBox()
        self.ui.center.addWidget(self._toolbox)
        self._toolbox.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self._tools: typing.List[Tool] = self._mock_load_tools()
        self._tool_param_widgets: typing.List[QWidget] = []
        self._create_param_widgets()
        self._current_tool: typing.Optional[Tool] = None

        self._current_tool = self._tools[0]
        self.canvas.set_current_tool(self._tools[0])
        self.ui.tbtnBugMask.animateClick()
        self.handle_reflection_mask_checked(False)
        self.handle_segments_mask_checked(False)

    def _mock_load_tools(self) -> typing.List[Tool]:
        return [self._mock_load_tool(i) for i in range(1)]

    def _mock_load_tool(self, tool_id: int) -> Tool:
        tool = Brush()
        tool.set_id(tool_id)
        toolbutton = QToolButton()
        toolbutton.setCheckable(True)
        toolbutton.setAutoExclusive(True)
        toolbutton.setText(tool.tool_name)
        toolbutton.toggled.connect(lambda checked: self.handle_tool_activated(checked, tool_id))
        self.ui.toolBox.layout().addWidget(toolbutton)
        return tool

    def _create_param_widgets(self):
        for tool in self._tools:
            param_widget = self._create_param_widget(tool)
            #self.ui.center.addWidget(param_widget)
            self._toolbox.addItem(param_widget, tool.tool_name)
            self._tool_param_widgets.append(param_widget)
            #param_widget.setVisible(False)

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
                entry.setMinimum(1)
                entry.setMaximum(55)
                entry.setSingleStep(2)
                entry.setValue(param.default_value)
                entry.setObjectName(param_name)
                #entry.valueChanged.connect(lambda val: self._handle_spinbox_value_changed(tool.tool_id,
                #                                                                          str(param_name), val))
                #entry.valueChanged.connect(lambda val: self._handle_spinbox_value_changed(tool.tool_id, entry))
                entry.valueChanged.connect(lambda: self._handle_param_changed(tool.tool_id))
                lay.addWidget(entry, row, 1)
                entry = None
            elif param.param_type == ParamType.STR:
                entry = QLineEdit()
                entry.setText(param.default_value)
                entry.setObjectName(param_name)
                entry.textChanged.connect(lambda: self._handle_param_changed(tool.tool_id))
                #entry.textChanged.connect(lambda text: self._handle_lineedit_text_changed(tool.tool_id,
                #                                                                  str(param_name), text))
                lay.addWidget(entry, row, 1)
                entry = None
            elif param.param_type == ParamType.BOOL:
                entry = QCheckBox()
                entry.setChecked(param.default_value)
                entry.setObjectName(param_name)
                entry.stateChanged.connect(lambda: self._handle_param_changed(tool.tool_id))
                #entry.stateChanged.connect(lambda state: self._handle_checkbox_toggled(tool.tool_id,
                #                                                                       str(param_name), state))
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
        #self.canvas.left_press.connect(lambda: print("hello"))
        self._scene.setSceneRect(self.canvas.sceneBoundingRect())
        self._scene.update()
        self.photo_view.fitInView(self.canvas, Qt.KeepAspectRatio)

    def handle_bug_mask_checked(self, checked: bool):
        print(f"bug {checked}")
        self.canvas.set_mask_shown(MaskType.BUG, checked)

    def handle_segments_mask_checked(self, checked: bool):
        print(f"segments {checked}")
        self.canvas.set_mask_shown(MaskType.REGIONS, checked)

    def handle_reflection_mask_checked(self, checked: bool):
        print(f"reflections {checked}")
        self.canvas.set_mask_shown(MaskType.REFLECTION, checked)

    def handle_tool_activated(self, checked: bool, tool_id: int):
        self._current_tool = self._tools[tool_id]
        self._tool_param_widgets[tool_id].setVisible(checked)
        print(f'{"activated" if checked else "deactivated"} the tool {self._current_tool.tool_name}')

    def handle_left_press(self, pos: QPointF):
        pos = pos.toPoint()

