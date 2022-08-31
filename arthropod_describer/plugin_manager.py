import importlib.resources
import inspect
import logging
import os
import typing
from enum import IntEnum
from importlib import import_module
from pathlib import Path
from typing import Optional, List, Any, Union, Dict

from PySide2.QtCore import QAbstractItemModel, QObject, QModelIndex, Qt, Signal, QSortFilterProxyModel, QItemSelection
from PySide2.QtWidgets import QWidget, QVBoxLayout

from arthropod_describer.common.plugin import RegionComputation, Plugin, PropertyComputation, GeneralAction
from arthropod_describer.common.state import State
from arthropod_describer.common.user_params import create_params_widget, UserParamWidgetBinding
from arthropod_describer.ui_plugins_widget import Ui_PluginsWidget


logger = logging.getLogger("PluginManager")


class PluginListModel(QAbstractItemModel):
    def __init__(self, parent: QObject = None):
        QAbstractItemModel.__init__(self, parent)
        self._plugin_list: List[Plugin] = []

    @property
    def plugin_list(self) -> List[Plugin]:
        return self._plugin_list

    @plugin_list.setter
    def plugin_list(self, plugins: List[Plugin]):
        self._plugin_list = plugins

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._plugin_list)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 1

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, 0)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.DisplayRole:
            return self._plugin_list[index.row()].info.name
        elif role == Qt.UserRole + 1:
            return self._plugin_list[index.row()].plugin_id
        return None

    def parent(self, index: QModelIndex) -> QModelIndex:
        return QModelIndex()


class RegionCompsListModel(QAbstractItemModel):
    def __init__(self, parent: QObject = None):
        QAbstractItemModel.__init__(self, parent)
        self.region_comps: Union[List[RegionComputation], List[PropertyComputation]] = []
        self.computations_dict: Dict[str, Union[RegionComputation, PropertyComputation]] = {comp.info.key: comp for comp in self.region_comps}

    @property
    def comps_list(self) -> Union[List[RegionComputation], List[PropertyComputation]]:
        return self.region_comps

    @comps_list.setter
    def comps_list(self, comps: Union[List[RegionComputation], List[PropertyComputation]]):
        self.region_comps = comps
        self.dataChanged.emit(self.createIndex(0, 0),
                              self.createIndex(len(self.region_comps) - 1, 0))

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.region_comps)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 1

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, 0)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.row() >= len(self.region_comps):
            return None
        if role == Qt.DisplayRole:
            return self.region_comps[index.row()].info.name
        elif role == Qt.UserRole + 1:
            return self.region_comps[index.row()].info.name
        return None

    def parent(self, index: QModelIndex) -> QModelIndex:
        return QModelIndex()

    def add_computation(self, comp: Union[RegionComputation, PropertyComputation]):
        self.region_comps.append(comp)
        self.computations_dict[comp.info.key] = comp
        self.dataChanged.emit(self.index(0, 0),
                              self.index(len(self.region_comps) - 1, 0))


class ProcessType(IntEnum):
    SELECTED_PHOTOS = 0,
    ALL_PHOTOS = 1,
    ALL_UNSEGMENTED = 2,


class PluginManager(QWidget):
    apply_region_computation = Signal([RegionComputation, ProcessType])
    apply_property_computation = Signal([PropertyComputation, ProcessType])

    def __init__(self, state: State, parent: Optional[QWidget] = None):
        QWidget.__init__(self, parent)
        self.ui = Ui_PluginsWidget()
        self.ui.setupUi(self)

        self.all_region_computations: List[RegionComputation] = []
        self.all_measurement_computations: List[PropertyComputation] = []

        self.plugins: List[Plugin] = self._load_plugins()

        self.state = state

        self._current_plugin: Optional[Plugin] = None

        self.plugin_list_model = PluginListModel()
        self.plugin_list_model.plugin_list = self.plugins
        self.ui.cmbPlugins.setModel(self.plugin_list_model)
        self.ui.cmbPlugins.currentIndexChanged.connect(self._handle_current_plugin_changed)
        self.ui.cmbRegComps.currentIndexChanged.connect(self._handle_reg_comp_changed)
        self.ui.cmbPropComps.currentIndexChanged.connect(self._handle_prop_comp_changed)

        self.region_comps_list_model = RegionCompsListModel()
        self.ui.grpRegionSettings.setLayout(QVBoxLayout())
        self._reg_comp_param_widget: QWidget = QWidget()
        self._current_reg_comp: Optional[RegionComputation] = None
        self._param_binding: Optional[UserParamWidgetBinding] = UserParamWidgetBinding(self.state)

        self.ui.btnRegApply.clicked.connect(self.handle_apply_clicked)
        self.ui.btnRegApplyAll.clicked.connect(self.handle_apply_all_clicked)

        self.region_restrict_model = QSortFilterProxyModel()
        # TODO replace with correct colormap model
        #self.region_restrict_model.setSourceModel(self.state.colormap)
        self.ui.regRestrictView.setModel(self.region_restrict_model)
        self.region_restrict_model.setFilterRole(Qt.UserRole + 3)
        self.region_restrict_model.setFilterFixedString('used')
        #self.ui.btnReset.clicked.connect(self.handle_reset_clicked)

        self.reg_selected_regions = []

        self.reg_label_sel_model: QItemSelection = self.ui.regRestrictView.selectionModel()
        self.reg_label_sel_model.selectionChanged.connect(self._handle_label_selection_changed)

        self.prop_comps_list_model = RegionCompsListModel()
        self.ui.grpPropSettings.setLayout(QVBoxLayout())
        self._prop_comp_param_widget: QWidget = QWidget()
        self._current_prop_comp: Optional[PropertyComputation] = None
        self._prop_param_binding = UserParamWidgetBinding(self.state)

        self.prop_region_restrict_model = QSortFilterProxyModel()
        # TODO replace with correct colormap model
        #self.prop_region_restrict_model.setSourceModel(self.state.colormap)
        self.ui.propRestrictView.setModel(self.prop_region_restrict_model)
        self.prop_region_restrict_model.setFilterRole(Qt.UserRole + 3)
        self.prop_region_restrict_model.setFilterFixedString('used')

        self.prop_label_sel_model: QItemSelection = self.ui.propRestrictView.selectionModel()
        self.prop_label_sel_model.selectionChanged.connect(self._handle_label_selection_changed)

        self.prop_selected_regions = []

        self.current_computation = {
            'region': self._current_reg_comp,
            'property': self._current_prop_comp
        }

        self.comp_desc = {
            'region': self.ui.lblRegDesc,
            'property': self.ui.lblPropDesc
        }

        self.comp_param_widget = {
            'region': self._reg_comp_param_widget,
            'property': self._prop_comp_param_widget
        }

        self.grp_settings = {
            'region': self.ui.grpRegionSettings,
            'property': self.ui.grpPropSettings
        }

        self.param_binding = {
            'region': self._param_binding,
            'property': self._prop_param_binding
        }

        self.grp_restrict = {
            'region': self.ui.grpRegRestrict,
            'property': self.ui.grpPropRestrict
        }

        self.restrict_model = {
            'region': self.region_restrict_model,
            'property': self.prop_region_restrict_model
        }

        self.restrict_view = {
            'region': self.ui.regRestrictView,
            'property': self.ui.propRestrictView
        }

        # if len(self.plugins) > 0:
        #     self._handle_current_plugin_changed(0)

    def set_show_region_computation(self, reg_comp: RegionComputation):
        self.ui.lblRegDesc.setText(reg_comp.info.description)

    def set_show_prop_computation(self, prop_comp: PropertyComputation):
        self.ui.lblPropDesc.setText(prop_comp.info.description)

    def handle_apply_clicked(self, chkd: bool):
        self.apply_region_computation.emit(self.current_computation['region'], ProcessType.SELECTED_PHOTOS)

    def handle_apply_all_clicked(self, chkd: bool):
        self.apply_region_computation.emit(self.current_computation['region'], ProcessType.ALL_PHOTOS)

    def _handle_label_selection_changed(self, selection: QItemSelection):
        curr_widget = self.ui.pluginTabWidget.currentWidget()
        widg_name = curr_widget.objectName()
        if widg_name == 'tabRegionComps':
            indexes = self.reg_label_sel_model.selectedIndexes()
            self.reg_selected_regions.clear()
            labels = self.reg_selected_regions
            restrict_model = self.region_restrict_model
        else:
            indexes = self.prop_label_sel_model.selectedIndexes()
            self.prop_selected_regions.clear()
            labels = self.prop_selected_regions
            restrict_model = self.prop_region_restrict_model

        for index in indexes:
            labels.append(restrict_model.data(index, Qt.UserRole))

    @property
    def current_plugin(self) -> Plugin:
        return self._current_plugin

    @current_plugin.setter
    def current_plugin(self, plg: Plugin):
        self._current_plugin = plg

    def _handle_current_plugin_changed(self, index: int):
        plugin = self.plugins[index]
        self.current_plugin = plugin
        print(f'activated plugin {plugin.info.name}')
        self.region_comps_list_model.comps_list = plugin.region_computations
        self.ui.cmbRegComps.setModel(self.region_comps_list_model)
        self.ui.cmbRegComps.setCurrentIndex(0)

        self.prop_comps_list_model.comps_list = plugin.property_computations
        if len(self.prop_comps_list_model.comps_list) == 0:
            self.ui.cmbPropComps.setEnabled(False)
        else:
            self.ui.cmbPropComps.setEnabled(True)
            self.ui.cmbPropComps.setModel(self.prop_comps_list_model)
            self.ui.cmbPropComps.setCurrentIndex(0)

    def _handle_current_reg_comp_changed(self, index: int):
        print("REG COMP")
        self._current_reg_comp = self.current_plugin.region_computations[index]
        self.ui.lblRegDesc.setText(self._current_reg_comp.info.description)
        #widg = create_params_widget(reg_comp.user_params)
        #self.ui.grpRegionSettings.setLayout(widg.layout())
        if self._reg_comp_param_widget is not None:
            self.ui.grpRegionSettings.layout().removeWidget(self._reg_comp_param_widget)
            self._param_binding.param_widget = None
            self._param_binding.user_params = dict()
            self._reg_comp_param_widget.deleteLater()
            self._reg_comp_param_widget = None
        if len(self._current_reg_comp.user_params) > 0:
            self._reg_comp_param_widget = create_params_widget(self._current_reg_comp.user_params, self.state)
            self._param_binding.bind(self._current_reg_comp.user_params, self._reg_comp_param_widget)
            self.ui.grpRegionSettings.layout().addWidget(self._reg_comp_param_widget)
            self.ui.grpRegionSettings.setVisible(True)
        else:
            self.ui.grpRegionSettings.setVisible(False)
        self.ui.grpRegRestrict.setVisible(self._current_reg_comp.region_restricted)
        self.ui.grpRegionSettings.update()

        if self._current_reg_comp.region_restricted:
            #self.region_restrict_model.setSourceModel(self._current_colormap_model)
            #self.state.colormap.used_labels = np.unique(self.state.label_img.label_img)
            #self.state.colormap.set_used_labels(set(list(np.unique(self.state.label_img.label_img))))
            self.region_restrict_model.setFilterFixedString('used')
            self.ui.regRestrictView.setModel(self.region_restrict_model)
            #self.ui.regRestrictView.dataChanged(self.region_restrict_model.createIndex(0, 0),
            #                                    self.region_restrict_model.createIndex(len(self.state.colormap.used_labels)-1,
            #                                                                          0))
        else:
            self.region_restrict_model.setFilterFixedString('')
        self.ui.regRestrictView.setVisible(self._current_reg_comp.region_restricted)

    def _handle_reg_comp_changed(self, index: int):
        self._handle_current_comp_changed('region', index)

    def _handle_prop_comp_changed(self, index: int):
        self._handle_current_comp_changed('property', index)

    def _handle_current_comp_changed(self, comp_str: str, index: int):
        #self._current_reg_comp = self.current_plugin.region_computations[index]
        if index < 0:
            return
        self.current_computation[comp_str] = self.current_plugin.region_computations[index] if comp_str == 'region' else self.current_plugin.property_computations[index]
        self.comp_desc[comp_str].setText(self.current_computation[comp_str].info.description)
        #self.ui.lblRegDesc.setText(self._current_reg_comp.info.description)
        #widg = create_params_widget(reg_comp.user_params)
        #self.ui.grpRegionSettings.setLayout(widg.layout())
        if self.comp_param_widget[comp_str] is not None:
            #self.ui.grpRegionSettings.layout().removeWidget(self._reg_comp_param_widget)
            self.grp_settings[comp_str].layout().removeWidget(self.comp_param_widget[comp_str])
            self.param_binding[comp_str].param_widget = None
            self.param_binding[comp_str].user_params = dict()
            self.comp_param_widget[comp_str].deleteLater()
            self.comp_param_widget[comp_str] = None
        if len(self.current_computation[comp_str].user_params) > 0:
            self.comp_param_widget[comp_str] = create_params_widget(self.current_computation[comp_str].user_params, self.state)
            self.param_binding[comp_str].bind(self.current_computation[comp_str].user_params,
                                               self.comp_param_widget[comp_str])
            #self.ui.grpRegionSettings.layout().addWidget(self._reg_comp_param_widget)
            #self.ui.grpRegionSettings.setVisible(True)
            self.grp_settings[comp_str].layout().addWidget(self.comp_param_widget[comp_str])
            self.grp_settings[comp_str].setVisible(True)
        else:
            self.grp_settings[comp_str].setVisible(False)
        #self.ui.grpRegRestrict.setVisible(self._current_reg_comp.region_restricted)
        #self.ui.grpRegionSettings.update()

        self.grp_restrict[comp_str].setVisible(self.current_computation[comp_str].region_restricted)
        self.grp_restrict[comp_str].update()

        if self.current_computation[comp_str].region_restricted:
            #self.region_restrict_model.setSourceModel(self.state.colormap)
            # self.restrict_model[comp_str].setSourceModel(self._current_colormap_model)
            #self.state.colormap.used_labels = np.unique(self.state.label_img.label_img)
            #self.state.colormap.set_used_labels(set(list(np.unique(self.state.label_img.label_img))))
            #self.region_restrict_model.setFilterFixedString('used')
            self.restrict_model[comp_str].setFilterFixedString('used')
            self.restrict_view[comp_str].setModel(self.restrict_model[comp_str])
            #self.ui.regRestrictView.setModel(self.region_restrict_model)
            #self.ui.regRestrictView.dataChanged(self.region_restrict_model.createIndex(0, 0),
            #                                    self.region_restrict_model.createIndex(len(self.state.colormap.used_labels)-1,
            #                                                                          0))
        else:
            #self.region_restrict_model.setFilterFixedString('')
            self.restrict_model[comp_str].setFilterFixedString('')
        #self.ui.regRestrictView.setVisible(self._current_reg_comp.region_restricted)
        self.restrict_view[comp_str].setVisible(self.current_computation[comp_str].region_restricted)

    def _load_plugins(self) -> List[Plugin]:
        plugs = []
        for plugin_path in get_plugin_folder_paths():
            plugin = load_plugin(Path(plugin_path))
            print(f'loading {plugin_path}')
            if plugin is None:
                continue
            self.all_region_computations.extend(plugin.region_computations)
            self.all_measurement_computations.extend(plugin.property_computations)
            plugs.append(plugin)
        return plugs


def load_plugin(plugin_folder: Path) -> typing.Optional[Plugin]:
    try:
        module = import_module(f'arthropod_describer.plugins.{plugin_folder.name}.plugin')
    except ModuleNotFoundError:
        logger.error(f'Cannot load {plugin_folder} plugin.')
        return None
    plug_cls = [member for member in inspect.getmembers(module, lambda o: inspect.isclass(o) and issubclass(o, Plugin))
                if member[1] != Plugin]
    if len(plug_cls) == 0:
        return
    name, cls = plug_cls[0]

    plug_inst: Plugin = cls(None)

    if (regions_path := plugin_folder / 'regions').exists():
        reg_comps = load_computations(regions_path)
        for comp_name, comp_cls in reg_comps:
            plug_inst.register_computation(comp_cls)
    if (props_path := plugin_folder / 'properties').exists():
        prop_comps = load_computations(props_path)
        for comp_name, comp_cls in prop_comps:
            plug_inst.register_computation(comp_cls)
    if (actions_path := plugin_folder / 'general').exists():
        general_actions = load_computations(actions_path)
        for action_name, action_cls in general_actions:
            plug_inst.register_computation(action_cls)

    return plug_inst


def get_plugin_folder_paths() -> List[Path]:
    print(f'__file__ is {__file__}')
    py_files = [file.path for file in os.scandir(Path(__file__).parent / 'plugins') if not file.name.startswith('__') and file.is_dir()]
    dbg_str = '\n'.join(py_files)
    print(f'returning plugin paths {dbg_str}')
    return py_files


def is_computation(obj) -> bool:
    return (inspect.isclass(obj) and obj != RegionComputation and obj != PropertyComputation and obj != GeneralAction and
            (issubclass(obj, RegionComputation) or issubclass(obj, PropertyComputation) or issubclass(obj, GeneralAction)))


def load_computations(comp_folder: Path) -> Union[List[RegionComputation], List[PropertyComputation], List[GeneralAction]]:
    comp_type = comp_folder.name
    computations: Union[List[RegionComputation], List[PropertyComputation]] = []
    for file in os.scandir(comp_folder):
        if file.is_dir() or file.name.startswith('_') or not file.name.endswith('.py'):
            continue
        module_name = file.name.split('.')[0]
        module = import_module(f'arthropod_describer.plugins.{comp_folder.parent.name}.{comp_type}.{module_name}')
        comp_cls = inspect.getmembers(module, is_computation)
        computations.extend(comp_cls)
    return computations
