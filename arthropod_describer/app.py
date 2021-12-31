import os
import sys
import typing
import importlib
import inspect
from pathlib import Path

from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QSizePolicy
from PySide2.QtCore import QModelIndex, QPoint, QItemSelectionModel

from arthropod_describer.common.tool import Tool
from arthropod_describer.common.state import State
from arthropod_describer.common.photo import Photo
from arthropod_describer.plugin_manager import PluginManager
from arthropod_describer.ui_arthropod_describer import Ui_ArhtropodDescriber
from arthropod_describer.common.photo_loader import Storage, LocalStorage
from arthropod_describer.common.utils import choose_folder
from arthropod_describer.image_list_model import ImageListModel
from arthropod_describer.thumbnail_storage import ThumbnailStorage, ThumbnailDelegate
from arthropod_describer.label_editor.mask_editor import MaskEditor
import arthropod_describer.resources


class ArthropodDescriber(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.ui = Ui_ArhtropodDescriber()
        self.ui.setupUi(self)

        self.state = State()

        self.tools: typing.List[Tool] = []
        self._load_tools()

        self.mask_editor = MaskEditor(self.state)
        self._setup_label_editor()

        self.plugins_widget = PluginManager()
        self.mask_editor.side_widget.layout().addWidget(self.plugins_widget)

        self.mask_editor.register_tools(self.tools)

        hbox = QHBoxLayout()
        hbox.addWidget(self.mask_editor.widget)

        self.ui.pgEditor.setLayout(hbox)

        self.storage: typing.Optional[Storage] = None
        self.current_photo: typing.Optional[Photo] = None
        self.current_idx: typing.Optional[QModelIndex] = None

        self.thumbnail_storage: typing.Optional[ThumbnailStorage] = ThumbnailStorage()

        self.image_list_model = ImageListModel()
        self._setup_image_list()

        self.ui.actionOpen_folder.triggered.connect(self.handle_action_open_folder_triggered)

    def _load_tools(self):
        py_files = [inspect.getmodulename(file.path) for file in os.scandir(Path(__file__).parent / 'tools') if file.name.endswith('.py') and file.name != '__init__.py']
        print(py_files)
        modules = [importlib.import_module(f'.{module_name}', '.tools') for module_name in py_files]
        tools = []
        for module in modules:
            members = inspect.getmembers(module)
            for obj_name, obj in members:
                if not obj_name.startswith('Tool_'):
                    continue
                if inspect.isclass(obj) and not inspect.isabstract(obj):
                    tool = obj()
                    tool.set_tool_id(len(tools))
                    self.state.colormap_changed.connect(lambda cmap: tool.color_map_changed(cmap.colormap))
                    tools.append(tool)

        self.tools = tools
        print(f'loaded {len(tools)} tools')

    def _setup_label_editor(self):
        self.mask_editor.signal_prev_photo.connect(self.handle_editor_prev_photo_request)
        self.mask_editor.signal_next_photo.connect(self.handle_editor_next_photo_request)

        self.state.photo_changed.connect(self.mask_editor.set_photo)

    def _setup_image_list(self):
        self.ui.imageListView.setModel(self.image_list_model)
        self.ui.imageListView.selectionModel().currentChanged.connect(self.handle_current_changed)
        self.ui.imageListView.verticalScrollBar().sliderPressed.connect(self.image_list_model.handle_slider_pressed)
        self.ui.imageListView.verticalScrollBar().sliderReleased.connect(self.handle_image_list_slider_released)

        self.thumbnail_delegate = ThumbnailDelegate(self.thumbnail_storage)
        self.ui.imageListView.setItemDelegate(self.thumbnail_delegate)
        self.ui.imageListView.setUniformItemSizes(False)
        self.ui.imageListView.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred))
        #self.context.storage_changed.connect(self.thumbnail_storage.initialize)

        #self.context.storage_changed.connect(lambda storage: self.image_list_model.initialize(storage.image_paths,
        #                                                                                      self.thumbnail_storage,
        #                                                                                      0))

    def set_storage(self, storage: Storage):
        self.storage = storage
        self.thumbnail_storage.initialize(self.storage)
        self.state.storage = storage
        self.state.colormap = self.storage.colormap
        self.image_list_model.initialize(self.storage.image_paths, self.thumbnail_storage, 0)
        self.current_idx = self.image_list_model.index(0, 0)
        self.ui.imageListView.selectionModel().setCurrentIndex(self.current_idx, QItemSelectionModel.Select)
        self.mask_editor.colormap_widget.register_colormap(self.storage.colormap)
        self.mask_editor.colormap_widget.set_colormap(0)

    def handle_action_open_folder_triggered(self, checked: bool):
        maybe_path = choose_folder(self)
        if maybe_path is not None:
            strg = LocalStorage.load_from(maybe_path)
            self.set_storage(strg)

    def handle_current_changed(self, current: QModelIndex, previous: QModelIndex):
        row = current.row()
        photo = self.storage.get_photo_by_idx(row)
        self.current_photo = photo
        #self.mask_editor.set_photo(photo)
        self.state.current_photo = photo
        self.current_idx = current

    def handle_image_list_slider_released(self):
        first_idx = self.ui.imageListView.indexAt(QPoint(0, 0))
        last_idx = self.ui.imageListView.indexAt(self.ui.imageListView.viewport().rect().bottomLeft())
        self.image_list_model.handle_slider_released(first_idx, last_idx)

    def handle_editor_next_photo_request(self):
        if self.storage is None:
            return
        row = min(self.current_idx.row() + 1, self.storage.image_count - 1)
        idx = self.image_list_model.index(row, 0)
        self.current_idx = idx
        self.ui.imageListView.selectionModel().setCurrentIndex(idx, QItemSelectionModel.SelectCurrent)

    def handle_editor_prev_photo_request(self):
        if self.storage is None:
            return
        row = max(self.current_idx.row() - 1, 0)
        idx = self.image_list_model.index(row, 0)
        self.current_idx = idx
        self.ui.imageListView.selectionModel().setCurrentIndex(idx, QItemSelectionModel.SelectCurrent)

    def closeEvent(self, event: QCloseEvent):
        self.thumbnail_storage.stop()


if __name__ == "__main__":
    app = QApplication([])
    window = ArthropodDescriber()
    window.showMaximized()
    sys.exit(app.exec_())