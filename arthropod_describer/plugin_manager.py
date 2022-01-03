import inspect
import os
from enum import IntEnum
from importlib import import_module
from pathlib import Path
from typing import Optional, List, Any

import numpy as np
from PySide2.QtCore import QAbstractItemModel, QObject, QModelIndex, Qt, Signal, QSortFilterProxyModel, QItemSelection
from PySide2.QtWidgets import QWidget, QLayout, QGridLayout, QVBoxLayout

from arthropod_describer.common.plugin import RegionComputation, Plugin, PropertyComputation
from arthropod_describer.common.state import State
from arthropod_describer.common.user_params import create_params_widget, UserParamWidgetBinding
from ui_plugins_widget import Ui_PluginsWidget


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
        self._region_comps: List[RegionComputation] = []

    @property
    def comps_list(self) -> List[RegionComputation]:
        return self._region_comps

    @comps_list.setter
    def comps_list(self, comps: List[RegionComputation]):
        self._region_comps = comps
        self.dataChanged.emit(self.createIndex(0, 0),
                              self.createIndex(len(self._region_comps) - 1, 0))

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._region_comps)

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 1

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        return self.createIndex(row, 0)

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if index.row() >= len(self._region_comps):
            return None
        if role == Qt.DisplayRole:
            return self._region_comps[index.row()].info.name
        elif role == Qt.UserRole + 1:
            return self._region_comps[index.row()].info.name
        return None

    def parent(self, index: QModelIndex) -> QModelIndex:
        return QModelIndex()


class ProcessType(IntEnum):
    CURRENT_PHOTO = 0,
    ALL_PHOTOS = 1,


class PluginManager(QWidget):
    apply_region_computation = Signal([RegionComputation, ProcessType])
    apply_property_computation = Signal([PropertyComputation, ProcessType])

    def __init__(self, state: State, parent: Optional[QWidget] = None):
        QWidget.__init__(self, parent)
        self.ui = Ui_PluginsWidget()
        self.ui.setupUi(self)
        self.plugins: List[Plugin] = self._load_plugins()

        self.state = state

        self._current_plugin: Optional[Plugin] = None

        self.plugin_list_model = PluginListModel()
        self.plugin_list_model.plugin_list = self.plugins
        self.ui.cmbPlugins.setModel(self.plugin_list_model)
        self.ui.cmbPlugins.currentIndexChanged.connect(self._handle_current_plugin_changed)
        self.ui.cmbRegComps.currentIndexChanged.connect(self._handle_current_reg_comp_changed)

        self.region_comps_list_model = RegionCompsListModel()
        self.ui.grpRegionSettings.setLayout(QVBoxLayout())
        self._reg_comp_param_widget: QWidget = QWidget()
        self._current_reg_comp: Optional[RegionComputation] = None
        self._param_binding: Optional[UserParamWidgetBinding] = UserParamWidgetBinding()

        self.ui.btnApply.clicked.connect(self.handle_apply_clicked)
        self.ui.btnApplyToAll.clicked.connect(self.handle_apply_all_clicked)

        self.region_restrict_model = QSortFilterProxyModel()
        self.region_restrict_model.setSourceModel(self.state.colormap)
        self.ui.regRestrictView.setModel(self.region_restrict_model)
        self.region_restrict_model.setFilterRole(Qt.UserRole + 3)
        self.region_restrict_model.setFilterFixedString('used')
        #self.ui.btnReset.clicked.connect(self.handle_reset_clicked)

        self.selected_regions = []

        self.label_sel_model: QItemSelection = self.ui.regRestrictView.selectionModel()
        self.label_sel_model.selectionChanged.connect(self._handle_label_selection_changed)

    def set_show_region_computation(self, reg_comp: RegionComputation):
        self.ui.lblRegDesc.setText(reg_comp.info.description)

    def handle_apply_clicked(self, chkd: bool):
        self.apply_region_computation.emit(self._current_reg_comp, ProcessType.CURRENT_PHOTO)

    def handle_apply_all_clicked(self, chkd: bool):
        self.apply_region_computation.emit(self._current_reg_comp, ProcessType.ALL_PHOTOS)

    def _handle_label_selection_changed(self, selection: QItemSelection):
        indexes = self.label_sel_model.selectedIndexes()
        labels = []
        for index in indexes:
            labels.append(self.region_restrict_model.data(index, Qt.UserRole))
        self.selected_regions = labels

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
            self._reg_comp_param_widget = create_params_widget(self._current_reg_comp.user_params)
            self._param_binding.bind(self._current_reg_comp.user_params, self._reg_comp_param_widget)
            self.ui.grpRegionSettings.layout().addWidget(self._reg_comp_param_widget)
            self.ui.grpRegionSettings.setVisible(True)
        else:
            self.ui.grpRegionSettings.setVisible(False)
        self.ui.grpRegRestrict.setVisible(self._current_reg_comp.region_restricted)
        self.ui.grpRegionSettings.update()

        if self._current_reg_comp.region_restricted:
            self.region_restrict_model.setSourceModel(self.state.colormap)
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

    def _load_plugins(self) -> List[Plugin]:
        plugs = []
        for direntry in os.scandir(Path('./plugins').absolute()):
            if not direntry.is_dir() or direntry.name.startswith('_'):
                continue
            plugs.append(load_plugin(Path(direntry.path)))
        return plugs

    def _update_used_labels(self):
        self.ui.regRestrictView.clear()
        used_labels = np.unique(self.state.current_photo.segments_mask.label_img)


def load_plugin(plugin_folder: Path) -> Plugin:
    module = import_module(f'plugins.{plugin_folder.name}.plugin')
    plug_cls = [member for member in inspect.getmembers(module, lambda o: inspect.isclass(o) and issubclass(o, Plugin))
                if member[1] != Plugin]
    if len(plug_cls) == 0:
        return
    name, cls = plug_cls[0]

    plug_inst = cls(None)

    print(f'loaded {name}')

    return plug_inst

