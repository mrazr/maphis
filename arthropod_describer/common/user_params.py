import enum
import itertools
import typing
from typing import List, Dict, Callable, Any

from PySide2.QtCore import QObject, Signal
from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QLineEdit, QCheckBox


class ParamType(enum.IntEnum):
    INT = 0,
    STR = 1,
    BOOL = 2,

    @classmethod
    def from_str(cls, type_str: typing.Union['INT', 'STR', 'BOOL']) -> 'ParamType':
        if type_str == 'INT':
            return ParamType.INT
        elif type_str == 'STR':
            return ParamType.STR
        else:
            return ParamType.BOOL


def convert_to_bool(string) -> bool:
    return string == 'True'


class ToolUserParam(QObject):
    converters: Dict[ParamType, Callable[[str], Any]] = {
        ParamType.INT: int,
        ParamType.BOOL: convert_to_bool,
        ParamType.STR: lambda s: s
    }

    value_changed = Signal([str, int])

    def __init__(self, name: str = '', param_type: ParamType = ParamType.STR, default_value='',
                 min_val: int = -1, max_val: int = -1, step: int = 1, key: str = '', desc: str = '', parent: QObject = None):
        QObject.__init__(self, parent)
        self.name = name
        self.key = key if key != '' else self.name
        self.desc = desc
        self.param_type = param_type
        self.default_value = default_value
        self.value = self.default_value
        if self.param_type == ParamType.INT:
            assert min_val >= 0
            assert max_val >= 0
        self.min_value = min_val
        self.max_value = max_val
        self.value_step = step

    def set_attr(self, attr_name: str, value: Any):
        value_ = value
        if 'value' in attr_name:
            value_ = self.converters[self.param_type](value)
            if attr_name == 'default_value':
                self.__setattr__('value', value_)
        elif attr_name == 'param_type':
            value_ = ParamType.from_str(value)
        self.__setattr__(attr_name, value_)
        self.value_changed.emit(self.key, value_)

    @classmethod
    def load_params_from_doc_str(cls, doc_str: str) -> Dict[str, 'ToolUserParam']:
        lines = [line.strip() for line in doc_str.splitlines()]
        lines = list(itertools.dropwhile(lambda line: not line.startswith('USER_PARAMS'), lines))[1:]
        params: List[ToolUserParam] = []
        _param: Dict[str, Any] = {}

        lines = list(itertools.dropwhile(lambda line: not line.startswith('NAME'), lines))

        i = 0
        next_i = 1

        while i < len(lines) and next_i < len(lines):
            while next_i < len(lines) and not lines[next_i].startswith('NAME'):
                next_i += 1
            param_str = '\n'.join(lines[i:next_i])
            param = ToolUserParam.create_from_str(param_str)
            params.append(param)
            i = next_i
            next_i += 1

        return {param.key: param for param in params}

        #while i < len(lines):
        #    if lines[i].startswith('NAME'):
        #        next_i = i + 1
        #        while not lines[next_i].startswith('NAME') and next_i < len(lines):
        #            i += 1
        #        param_str = '\n'.join(lines[i:next_i])
        #        param = ToolUserParam.create_from_str(param_str)
        #        params.append(param)
        #        i = next_i
        #    i += 1

    #@classmethod
    #def from_str(cls, param_str: str) -> 'ToolUserParam':
    #    lines = param_str.splitlines()

    @classmethod
    def create_from_str(cls, param_str: str) -> 'ToolUserParam':
        lines = param_str.splitlines()
        param = ToolUserParam()
        for line in lines:
            attr_name, attr_val_str = line.split(':')
            attr_name = attr_name.strip().lower()
            attr_val_str = attr_val_str.strip()
            param.set_attr(attr_name, attr_val_str)
        return param


def get_val_setter(binding: 'UserParamWidgetBinding', param_name: str):
    def set_val(val: Any):
        print(f'settings {param_name}')
        #binding.user_params[param_name].value = val
        binding.user_params[param_name].set_attr('value', val)
    return set_val


class UserParamWidgetBinding(QObject):
    def __init__(self, parent: QObject = None):
        QObject.__init__(self, parent)
        self.user_params: Dict[str, ToolUserParam] = dict()
        self.param_widget: typing.Optional[QWidget] = None

    def bind(self, params: List[ToolUserParam], param_widget: QWidget):
        self.user_params = {param.key: param for param in params}
        self.param_widget = param_widget
        for param_name, param in self.user_params.items():
            if param.param_type == ParamType.INT:
                spbox: QSpinBox = param_widget.findChild(QSpinBox, param.key)
                spbox.valueChanged.connect(get_val_setter(self, param_name))
            elif param.param_type == ParamType.STR:
                line_edit: QLineEdit= param_widget.findChild(QLineEdit, param.key)
                line_edit.textChanged.connect(get_val_setter(self, param_name))
            else:
                chkbox: QCheckBox = param_widget.findChild(QCheckBox, param.key)
                chkbox.stateChanged.connect(get_val_setter(self, param_name))

    def _handle_int_value_changed(self, param_name: str, value: int):
        print(id(param_name))
        self.user_params[param_name].value = value

    def _handle_str_value_changed(self, param_name: str, value: str):
        print(id(param_name))
        self.user_params[param_name].value = value

    def _handle_bool_value_changed(self, param_name: str, value: bool):
        print(id(param_name))
        self.user_params[param_name].value = value


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
            spbox.setObjectName(param.key)
            spbox.setMinimum(param.min_value)
            spbox.setMaximum(param.max_value)
            spbox.setSingleStep(param.value_step)
            spbox.setValue(param.value)
            lay.addWidget(spbox, row, 1)
        elif param.param_type == ParamType.STR:
            line_edit = QLineEdit()
            line_edit.setObjectName(param.key)
            line_edit.setText(param.value)
            lay.addWidget(line_edit, row, 1)
        else:
            chkbox = QCheckBox()
            chkbox.setObjectName(param.key)
            chkbox.setChecked(param.value)
            lay.addWidget(chkbox, row, 1)
    widget.setLayout(lay)
    return widget

