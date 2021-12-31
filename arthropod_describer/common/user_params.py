from typing import List

from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QLineEdit, QCheckBox

from arthropod_describer.common.tool import ToolUserParam, ParamType


def create_param_widget(params: ToolUserParam) -> QWidget:
    param_widget = QWidget()
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


def create_params_widget(params: List[ToolUserParam]) -> QWidget:
    widget = QWidget()
    lay = QGridLayout()

    for row, param in enumerate(params):
        param_name = param.name
        label = QLabel()
        label.setText(param_name)
        lay.addWidget(label, row, 0)
        if param.param_type == ParamType.INT:
            spbox = QSpinBox()
            spbox.setMinimum(param.min_value)
            spbox.setMaximum(param.max_value)
            spbox.setSingleStep(param.value_step)
            spbox.setValue(param.value)
            lay.addWidget(spbox, row, 1)
        elif param.param_type == ParamType.STR:
            line_edit = QLineEdit()
            line_edit.setText(param.value)
            lay.addWidget(line_edit, row, 1)
        else:
            chkbox = QCheckBox()
            chkbox.setChecked(param.value)
            lay.addWidget(chkbox, row, 1)
    widget.setLayout(lay)
    return widget