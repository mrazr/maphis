import enum
import itertools
import typing
from collections import abc
from typing import List, Dict, Callable, Any

from PySide2.QtCore import QObject, Signal, Qt, QItemSelection
from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QLineEdit, QCheckBox, QSizePolicy, \
    QDialogButtonBox, QPushButton, QListWidget, QListWidgetItem, QHBoxLayout, QComboBox, QVBoxLayout, QToolButton

from arthropod_describer.common.state import State
from arthropod_describer.common.storage import _Storage
from arthropod_describer.common.utils import get_dict_from_doc_str


class ParamSource(enum.IntEnum):
    User = 0,
    Photo = 1,
    Storage = 2,


class ParamValueCardinality(enum.IntEnum):
    SingleValue = 0,
    MultiValue = 1,


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


enums = {
    'PARAM_SOURCE': ParamSource,
    'PARAM_VALUE_CARDINALITY': ParamValueCardinality,
    'PARAM_TYPE': ParamType
}


def convert_to_bool(string_or_bool) -> bool:
    return string_or_bool if type(string_or_bool) is bool else string_or_bool == 'True'


class UserParamInstance(QObject):
    value_changed = Signal([QObject])

    converters: Dict[typing.Any, Callable[[str], Any]] = {
        ParamType.INT: int,
        ParamType.BOOL: convert_to_bool, #lambda value_in_bool_or_str: value_in_bool_or_str,
        ParamType.STR: lambda s: s,
    }

    def __init__(self, param_key: str, param_type: ParamType, idx: int, value: typing.Any, data_is_collection: bool,
                 min_value: int, max_value: int):
        super(UserParamInstance, self).__init__(None)
        self.param_key = param_key
        self.param_type = param_type
        self.data_is_collection: bool = data_is_collection
        self.idx = idx
        self._value: typing.Any = value
        self.min_value = min_value
        self.max_value = max_value

    @property
    def value(self) -> typing.Any:
        return self._value

    @value.setter
    def value(self, val: typing.Any):
        self.set_attr('_value', val)

    def set_attr(self, attr_name: str, value: Any):
        value_ = value
        if attr_name in ['_value', 'value'] and not self.data_is_collection:
            value_ = self.converters[self.param_type](value)
            if attr_name == 'default_value':
                self.__setattr__('_value', value_)
            else:
                if self.param_type == ParamType.INT:
                    if self.min_value is not None:
                        value_ = max(self.min_value, value_)
                    if self.max_value is not None:
                        value_ = min(self.max_value, value_)
                self.__setattr__('_value', value_)
        elif attr_name in ['min_value', 'max_value']:
            value_ = int(value)  # TODO what about float?
            self.__setattr__(attr_name, value_)
        else:
            self.__setattr__(attr_name, value_)
        self.value_changed.emit(self)


class UserParam(QObject):
    converters: Dict[typing.Any, Callable[[str], Any]] = {
        ParamType.INT: int,
        ParamType.BOOL: convert_to_bool, #lambda value_in_bool_or_str: value_in_bool_or_str,
        ParamType.STR: lambda s: s,
    }

    value_changed = Signal([str, int])
    param_instance_added = Signal([QObject, UserParamInstance])
    param_instance_removed = Signal([QObject, int])

    def __init__(self, name: str = '', param_type: ParamType = ParamType.STR, default_value='',
                 min_val: typing.Optional[int] = 0, max_val: typing.Optional[int] = 100, step: int = 1,
                 key: str = '', desc: str = '', param_source: ParamSource = ParamSource.User,
                 param_value_cardinality: ParamValueCardinality = ParamValueCardinality.SingleValue, count: int = 1,
                 min_count: int = 1, max_count: int = 1, param_dict: typing.Dict[str, typing.Any] = None, parent: QObject = None):
        QObject.__init__(self, parent)
        self.param_name = name
        self.param_key = key if key != '' else self.param_name
        self.param_desc = desc
        self.param_type = param_type
        self.param_source = param_source
        self.param_source_field: str = ''
        self.param_value_cardinality = param_value_cardinality
        self.data_is_collection: bool = False

        self.count = count
        self.min_count = min_count
        self.max_count = max_count
        self.deletable: bool = self.count > self.min_count

        self.param_instances: typing.Dict[int, UserParamInstance] = dict()
        self.used_idxs: typing.Set[int] = set()
        self.vacant_idxs: typing.Set[int] = set()

        self.default_value = default_value
        # self._value = self.default_value
        # if self.param_type == ParamType.INT:
        #     assert min_val >= 0
        #     assert max_val >= 0
        self.min_value = min_val
        self.max_value = max_val
        self.value_step = step

        if param_dict is not None:
            for attr_name, attr_val_str in param_dict.items():
                if attr_name in enums:
                    attr_val_str = enums[attr_name][attr_val_str]
                else:
                    attr_val_str = attr_val_str.lower().strip()
                attr_name = attr_name.lower().strip()
                self.set_attr(attr_name, attr_val_str)
        if self.default_value is None or self.default_value == '':
            if self.param_type == ParamType.INT:
                self.default_value = 0
            elif self.param_type == ParamType.BOOL:
                self.default_value = True
        if self.param_source != ParamSource.User:
            self.data_is_collection = isinstance(_Storage.__getattribute__(self.param_source_field), abc.Collection)
        for i in range(self.count):
            self.add_instance()

    def set_attr(self, attr_name: str, value: Any):
        value_ = value
        if attr_name == 'default_value' and not self.data_is_collection:
            value_ = self.converters[self.param_type](value)
            # if attr_name == 'default_value':
            #     self.__setattr__('default_value', value_)
            # else:
            #     if self.param_type == ParamType.INT:
            if self.min_value is not None:
                value_ = max(self.min_value, value_)
            if self.max_value is not None:
                value_ = min(self.max_value, value_)
            self.__setattr__('default_value', value_)
        elif attr_name in ['min_value', 'max_value', 'min_count', 'max_count', 'count']:
            # TODO if min_value or max_value then propagate to all instances
            # value_ = self.converters[self.param_type](value)
            value_ = int(value)  # TODO what about float?
            self.__setattr__(attr_name, value_)
        # elif attr_name == 'param_type':
        #     value_ = ParamType.from_str(value)
        else:
            self.__setattr__(attr_name, value_)
        # self.value_changed.emit(self.param_key, value_)

    # @property
    # def value(self) -> typing.Any:
    #     return self._value
    #
    # @value.setter
    # def value(self, val: typing.Any):
    #     self.set_attr('_value', val)
    #     # self.value_changed.emit(self.param_key, self._value)

    @property
    def default_instance(self) -> typing.Optional[UserParamInstance]:
        return None if len(self.param_instances) == 0 else list(self.param_instances.values())[0]

    @property
    def value(self) -> typing.Optional[typing.Any]:
        inst = self.default_instance
        return None if inst is None else inst.value

    @value.setter
    def value(self, val: typing.Any):
        inst = self.default_instance
        if inst is None:
            return
        inst.value = val

    def add_instance(self):
        if len(self.param_instances) == self.max_count:
            return
        if len(self.vacant_idxs) > 0:
            idx = self.vacant_idxs.pop()
        else:
            idx = len(self.param_instances)
        param = UserParamInstance(self.param_key, self.param_type, idx, self.default_value, self.data_is_collection,
                                  self.min_value, self.max_value)
        self.used_idxs.add(idx)
        self.param_instances[idx] = param
        self.param_instance_added.emit(self, param)

    def remove_instance(self, idx: int):
        if idx not in self.param_instances:
            return
        del self.param_instances[idx]
        self.used_idxs.remove(idx)
        self.vacant_idxs.add(idx)
        self.param_instance_removed.emit(self, idx)

    @classmethod
    def load_params_from_doc_str(cls, doc_str: str) -> Dict[str, 'UserParam']:
        if doc_str is None or doc_str == '':
            return {}
        lines = [line.strip() for line in doc_str.splitlines()]
        lines = list(itertools.dropwhile(lambda line: not line.startswith('USER_PARAMS'), lines))[1:]
        params: List[UserParam] = []
        _param: Dict[str, Any] = {}

        lines = list(itertools.dropwhile(lambda line: not line.startswith('PARAM_NAME'), lines))

        i = 0
        next_i = 1

        while i < len(lines) and next_i < len(lines):
            while next_i < len(lines) and not lines[next_i].startswith('PARAM_NAME'):
                next_i += 1
            param_str = '\n'.join(lines[i:next_i])
            param_dict = get_dict_from_doc_str(param_str)
            param = UserParam.create_from_dict(param_dict)
            params.append(param)
            i = next_i
            next_i += 1

        return {param.param_key: param for param in params}

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
    def create_from_str(cls, param_str: str) -> 'UserParam':
        lines = param_str.splitlines()
        param_dict: typing.Dict[str, str] = {}
        for line in lines:
            attr_name, attr_val_str = line.split(':')
            attr_name = attr_name.strip().lower()
            attr_val_str = attr_val_str.strip()
            param_dict[attr_name] = attr_val_str
        return UserParam.create_from_dict(param_dict)

    @classmethod
    def create_from_dict(cls, param_dict: typing.Dict[str, str]) -> 'UserParam':
        if param_dict.setdefault('PARAM_SOURCE', 'User') != 'User' and param_dict.setdefault('PARAM_SOURCE_FIELD', '') == '':
            print(f'Missing a field specification.')
        param_dict.setdefault('PARAM_VALUE_CARDINALITY', 'SingleValue')
        param_data_is_collection = False
        if param_dict['PARAM_SOURCE'] != 'User':
            if param_dict['PARAM_SOURCE'].lower() == 'storage':
                param_data_is_collection = isinstance(_Storage.__getattribute__(param_dict['PARAM_SOURCE_FIELD']), abc.Collection)
        param = UserParam(param_dict=param_dict)
        # for attr_name, attr_val_str in param_dict.items():
        #     if attr_name in enums:
        #         attr_val_str = enums[attr_name][attr_val_str]
        #     else:
        #         attr_val_str = attr_val_str.lower().strip()
        #     attr_name = attr_name.lower().strip()
        #     param.set_attr(attr_name, attr_val_str)
        return param


# def get_val_setter(binding: 'UserParamWidgetBinding', param_key: str, idx: int):
def get_val_setter(param_instance: UserParamInstance):
    def set_val(val: Any):
        #binding.user_params[param_name].value = val
        # binding.user_params[param_key].set_attr('value', val)
        # print(f'setting {param_key} idx: {idx}')
        param_instance.set_attr('value', val)
        print(f'setting {param_instance.param_key} idx: {param_instance.idx}')
    return set_val


# def get_val_setter_qlistwidget(binding: 'UserParamWidgetBinding', param_key: str, idx: int):
def get_val_setter_qlistwidget(binding: 'UserParamWidgetBinding', param_instance: UserParamInstance):
    def set_val():
        listw: QListWidget = binding.param_widget.findChild(QListWidget, f'{param_instance.param_key}_{param_instance.idx}')
        selection = listw.selectedItems()
        data = [item.data(Qt.UserRole) for item in selection]
        if binding.user_params[param_instance.param_key].param_value_cardinality == ParamValueCardinality.SingleValue:
            data = data[0]
        print(f'setting value for {param_instance.param_key} to {data}')
        print(f'setting {param_instance.param_key} idx {param_instance.idx}')
        # binding.user_params[param_key].set_attr('value', data)
        param_instance.set_attr('value', data)

    return set_val


def get_val_setter_combobox(binding: 'UserParamWidgetBinding', param_instance: UserParamInstance):
    def set_val(idx: int):
        combobox: QComboBox = binding.param_widget.findChild(QComboBox, f'{param_instance.param_key}_{param_instance.idx}')
        # binding.user_params[param_key].set_attr('value', combobox.currentData())
        param_instance.set_attr('value', combobox.currentData())
        print(f'setting {param_instance.param_key} idx {param_instance.idx}')
    return set_val


def get_instance_adder(param: UserParam):
    def adder():
        print(f'should add an instance for {param.param_key}')
        # add_button: QPushButton = binding.param_widget.findChild(QPushButton, f'{param.param_key}_add')
        # setting_layout: QVBoxLayout = binding.param_widget.findChild(QVBoxLayout, f'{param.param_key}_layout')
        # setting_layout.removeWidget(add_button)
        # widg = create_param_control(binding._state, param, param.count)
        # # param.count += 1
        # setting_layout.addWidget(widg)
        # setting_layout.addWidget(add_button)
        # param_inst_col = binding.param_instance_collections[param.param_key]
        # param_inst_col.add_instance()
        param.add_instance()
        # add_button.setEnabled(len(param_inst_col.instances) < param.max_count)
    return adder


def get_instance_remover(param: UserParam, idx: int):
    def remove():
        print(f'removing {param.param_key} idx {idx}')
        param.remove_instance(idx)
    return remove


class ParamInstanceCollection:
    def __init__(self, param: UserParam, param_widget: QWidget, state: State):
        self.param = param
        self.param_widget = param_widget
        self.state = state
        self.instances: typing.Dict[int, QWidget] = {}
        self.used_ids: typing.Set[int] = set()
        self.vacant_ids: typing.Set[int] = set()

    def remove_instance(self, idx: int):
        print(f'removing {self.param.param_key} idx {idx}')
        container: QWidget = self.param_widget.findChild(QWidget, f'{self.param.param_key}_{idx}_container_widget')
        # setting_layout: QVBoxLayout = self.param_widget.findChild(QVBoxLayout, f'{self.param.param_key}_{idx}_layout')
        setting_widget: QWidget = self.param_widget.findChild(QWidget, f'{self.param.param_key}')
        setting_layout: QVBoxLayout = setting_widget.layout()

        container.hide()
        setting_layout.removeWidget(container)
        container.deleteLater()
        del self.param.value[idx]
        del self.instances[idx]
        self.used_ids.remove(idx)
        self.vacant_ids.add(idx)

    def add_instance(self) -> QWidget:
        if len(self.vacant_ids) > 0:
            idx = self.vacant_ids.pop()
        else:
            idx = len(self.instances)
        instance_widget = create_param_control(self.state, self.param, idx)
        remove_btn: QToolButton = instance_widget.findChild(QToolButton, f'{self.param.param_key}_{idx}_remove')
        remove_btn.clicked.connect(lambda: self.remove_instance(idx))

        add_button: QPushButton = self.param_widget.findChild(QPushButton, f'{self.param.param_key}_add')

        container: QWidget = self.param_widget.findChild(QWidget, f'{self.param.param_key}')
        container.layout().removeWidget(add_button)
        container.layout().addWidget(instance_widget)
        container.layout().addWidget(add_button)
        self.instances[idx] = instance_widget
        self.used_ids.add(idx)
        add_button.setEnabled(len(self.instances) < self.param.max_count)
        return instance_widget


class UserParamWidgetBinding(QObject):
    def __init__(self, state: State, parent: QObject = None):
        QObject.__init__(self, parent)
        self.user_params: Dict[str, UserParam] = dict()
        self.param_widget: typing.Optional[QWidget] = None
        # self.param_instance_collections: typing.Dict[str, ParamInstanceCollection] = dict()
        self._state: State = state

    def bind(self, params: List[UserParam], param_widget: QWidget):
        self.user_params = {param.param_key: param for param in params}
        self.param_widget = param_widget
        for param_key, param in self.user_params.items():
            param: UserParam = param
            # param.value_changed.connect(self._handle_param_value_changed)
            # self.param_instance_collections[param.param_key] = ParamInstanceCollection(param, self.param_widget,
            #                                                                            self._state)
            # for i in range(param.count):
            #     self.param_instance_collections[param.param_key].add_instance()
            #     self.bind_control(param, i)
            for idx, param_instance in param.param_instances.items():
                self.bind_param_instance(param, param_instance)
            add_button: QPushButton = param_widget.findChild(QPushButton, f'{param.param_key}_add')
            add_button.clicked.connect(get_instance_adder(param))
            param.param_instance_added.connect(self.bind_param_instance)
            param.param_instance_removed.connect(self.unbind_param_instance)

    def bind_control(self, param: UserParam, param_instance: UserParamInstance):
        if param.param_source == ParamSource.User:
            if param_instance.param_type == ParamType.INT:
                spbox: QSpinBox = self.param_widget.findChild(QSpinBox, f'{param_instance.param_key}_{param_instance.idx}')
                spbox.valueChanged.connect(get_val_setter(param_instance))
            elif param_instance.param_type == ParamType.STR:
                line_edit: QLineEdit= self.param_widget.findChild(QLineEdit, f'{param_instance.param_key}_{param_instance.idx}')
                line_edit.textChanged.connect(get_val_setter(param_instance))
            else:
                chkbox: QCheckBox = self.param_widget.findChild(QCheckBox, f'{param_instance.param_key}_{param_instance.idx}')
                chkbox.toggled.connect(get_val_setter(param_instance))
        else:
            if param.param_value_cardinality == ParamValueCardinality.SingleValue:
                combobox: QComboBox = self.param_widget.findChild(QComboBox, f'{param_instance.param_key}_{param_instance.idx}')
                combobox.currentIndexChanged.connect(get_val_setter_combobox(self, param_instance))
            else:
                listw: QListWidget = self.param_widget.findChild(QListWidget, f'{param_instance.param_key}_{param_instance.idx}')
                listw.itemSelectionChanged.connect(get_val_setter_qlistwidget(self, param_instance))

    def bind_param_instance(self, param: UserParam, instance: UserParamInstance):
        instance_widget = create_param_control(self._state, param, instance)
        self._add_control_widget(param, instance, instance_widget)
        self.bind_control(param, instance)
        instance.value_changed.connect(self._handle_param_value_changed)

    def unbind_param_instance(self, param: UserParam, idx: int):
        print(f'removing {param.param_key} idx {idx}')
        container: QWidget = self.param_widget.findChild(QWidget, f'{param.param_key}_{idx}_container_widget')
        # setting_layout: QVBoxLayout = self.param_widget.findChild(QVBoxLayout, f'{self.param.param_key}_{idx}_layout')
        setting_widget: QWidget = self.param_widget.findChild(QWidget, f'{param.param_key}')
        setting_layout: QVBoxLayout = setting_widget.layout()

        container.hide()
        setting_layout.removeWidget(container)
        container.deleteLater()
        self._update_add_remove_buttons(param)

    def _update_add_remove_buttons(self, param: UserParam):
        add_button: QPushButton = self.param_widget.findChild(QPushButton, f'{param.param_key}_add')
        add_button.setEnabled(len(param.param_instances) < param.max_count or param.max_count < 0)

        for used_idx in param.used_idxs:
            remove_btn: QToolButton = self.param_widget.findChild(QToolButton, f'{param.param_key}_{used_idx}_remove')
            remove_btn.setEnabled(len(param.param_instances) > param.min_count)
            remove_btn.setVisible(len(param.param_instances) > param.min_count)

    def _add_control_widget(self, param: UserParam, instance: UserParamInstance, instance_widget: QWidget):
        remove_btn: QToolButton = instance_widget.findChild(QToolButton, f'{instance.param_key}_{instance.idx}_remove')
        # remove_btn.clicked.connect(lambda: self.remove_instance(instance.idx))
        remove_btn.clicked.connect(get_instance_remover(param, instance.idx))

        add_button: QPushButton = self.param_widget.findChild(QPushButton, f'{instance.param_key}_add')

        container: QWidget = self.param_widget.findChild(QWidget, f'{instance.param_key}')
        container.layout().removeWidget(add_button)
        container.layout().addWidget(instance_widget)
        container.layout().addWidget(add_button)
        self._update_add_remove_buttons(param)

    def _handle_param_value_changed(self, instance: UserParamInstance):
        # param: UserParam = self.user_params[param_key]

        if not instance.data_is_collection:
            if instance.param_type == ParamType.INT:
                spbox: QSpinBox = self.param_widget.findChild(QSpinBox, f'{instance.param_key}_0')
                spbox.blockSignals(True)
                spbox.setValue(instance.value)
                spbox.blockSignals(False)
            elif instance.param_type == ParamType.STR:
                ledit: QLineEdit = self.param_widget.findChild(QLineEdit, f'{instance.param_key}_0')
                ledit.blockSignals(True)
                ledit.setText(instance.param_key)
                ledit.blockSignals(False)
            else:
                chkbox: QCheckBox = self.param_widget.findChild(QCheckBox, f'{instance.param_key}_0')
                chkbox.blockSignals(True)
                chkbox.setChecked(instance.value)
                chkbox.blockSignals(False)
        # else:
        #     listw: QListWidget = self.param_widget.findChild(QListWidget, param.param_key)
        #     selection = listw.selectedItems()
        #     data = [item.data(Qt.UserRole) for item in selection]
        #     if param.param_value_cardinality == ParamValueCardinality.SingleValue:
        #         param.value = data[0]
        #     else:
        #         param.value = data
        #     print("success?")

    def _handle_int_value_changed(self, param_name: str, value: int):
        print(id(param_name))
        self.user_params[param_name].value = value

    def _handle_str_value_changed(self, param_name: str, value: str):
        print(id(param_name))
        self.user_params[param_name].value = value

    def _handle_bool_value_changed(self, param_name: str, value: bool):
        print(id(param_name))
        self.user_params[param_name].value = value


def create_param_control(state: State, param: UserParam, param_instance: UserParamInstance) -> QWidget:
    control_widget_name = f'{param_instance.param_key}_{param_instance.idx}'
    widg: QWidget = QWidget()
    widg.setObjectName(f'{param_instance.param_key}_{param_instance.idx}_container_widget')
    layout = QHBoxLayout()
    layout.setObjectName(f'{param_instance.param_key}_{param_instance.idx}_layout')
    if param.param_source == ParamSource.User:
        if param_instance.param_type == ParamType.INT:
            spbox = QSpinBox()
            spbox.setObjectName(control_widget_name)
            spbox.setMinimum(param.min_value)
            spbox.setMaximum(param.max_value)
            spbox.setSingleStep(param.value_step)
            spbox.setValue(param_instance.value)
            spbox.setMaximumWidth(200)
            layout.addWidget(spbox)
            # widg = spbox
            # lay.addWidget(spbox, row, 1, alignment=Qt.AlignLeft)
            # setting_widget_layout.addWidget(spbox)
            spbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        elif param_instance.param_type == ParamType.STR:
            line_edit = QLineEdit()
            line_edit.setObjectName(control_widget_name)
            line_edit.setText(param_instance.value)
            # lay.addWidget(line_edit, row, 1)
            # setting_widget_layout.addWidget(line_edit)
            line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            # widg = line_edit
            layout.addWidget(line_edit)
        else:
            chkbox = QCheckBox(text=param.param_name)
            chkbox.setObjectName(control_widget_name)
            chkbox.setChecked(param_instance.value)
            # label.hide()
            # label.deleteLater()
            # lay.removeWidget(label)
            # lay.addWidget(chkbox, row, 0)
            # setting_widget_layout.addWidget(chkbox)
            # widg = chkbox
            chkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            layout.addWidget(chkbox)
    else:
        model = sorted(state.storage.__getattribute__(param.param_source_field))
        # label.setText(param_instance.param_name)
        if param.param_value_cardinality == ParamValueCardinality.SingleValue:
            control_widget: QComboBox = QComboBox()
            control_widget.setObjectName(control_widget_name)
            for item in model:
                control_widget.addItem(str(item), item)
        else:
            control_widget: QListWidget = QListWidget()
            control_widget.setObjectName(control_widget_name)
            for item in model:
                item_widget = QListWidgetItem(str(item))
                item_widget.setData(Qt.UserRole, item)
                control_widget.addItem(item_widget)
            control_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(control_widget)
    remove_btn = QToolButton()
    remove_btn.setStyleSheet('color: red')
    remove_btn.setText('x')
    remove_btn.setObjectName(f'{param_instance.param_key}_{param_instance.idx}_remove')
    layout.addWidget(remove_btn)
    widg.setLayout(layout)
    return widg


def create_params_widget(params: List[UserParam], state: State) -> QWidget:
    widget = QWidget()
    lay = QGridLayout()
    lay.setColumnStretch(0, 4)
    lay.setColumnStretch(1, 1)
    widget.setLayout(lay)
    for row, param in enumerate(params):
        param_name = param.param_name
        label = QLabel()
        label.setText(param_name)
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        label.setWordWrap(True)
        lay.addWidget(label, row, 0)
        setting_widget = QWidget()
        setting_widget.setObjectName(param.param_key)
        setting_widget_layout = QVBoxLayout()
        setting_widget_layout.setObjectName(f'{param.param_key}_layout')
        setting_widget.setLayout(setting_widget_layout)
        # for i in range(param.count):
        #     widg = create_param_control(state, param, i)
        #     if param.param_type == ParamType.BOOL:
        #         label.hide()
        #         lay.removeWidget(label)
        #         label.deleteLater()
        #     setting_widget_layout.addWidget(widg)
        add_button = QPushButton()
        add_button.setText('Add')
        add_button.setObjectName(f'{param.param_key}_add')
        setting_widget_layout.addWidget(add_button)
        add_button.setVisible(param.count < param.max_count or param.max_count < 0)
        lay.addWidget(setting_widget, row, 1)
    widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
    return widget


def create_params_widget_with_buttons(params: List[UserParam], state: State) -> typing.Union[QWidget, QDialogButtonBox, QPushButton]:
    widget = create_params_widget(params, state)
    layout: QGridLayout = widget.layout()
    rows = layout.rowCount()

    hbox = QHBoxLayout()
    button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
    hbox.addWidget(button_box)
    save_button = QPushButton(text='Save settings as default')
    save_button.setEnabled(False)
    hbox.addWidget(save_button)
    layout.addLayout(hbox, rows, 1)

    return widget, button_box, save_button

