import sys
import typing

from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QMainWindow, QApplication, QWidget, QHBoxLayout, QSizePolicy
from PySide2.QtCore import QModelIndex, QPoint

from view.ui_arthropod_describer import Ui_ArhtropodDescriber
from view.ui_mask_edit_view import Ui_MaskEditor
from dbg_utils import MockStorage
from model.photo_loader import Storage, LocalStorage
from utils import choose_folder
from model.image_list_model import ImageListModel
from model.thumbnail_storage import ThumbnailStorage, ThumbnailDelegate
from mask_editor import MaskEditor
import resources


class ArthropodDescriber(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.ui = Ui_ArhtropodDescriber()
        self.ui.setupUi(self)

        #self.editor_ui = Ui_MaskEditor()
        #self.editor = QWidget()
        #self.editor_ui.setupUi(self.editor)

        self.mask_editor = MaskEditor()

        hbox = QHBoxLayout()
        hbox.addWidget(self.mask_editor.widget)

        self.ui.pgEditor.setLayout(hbox)

        self.storage: typing.Optional[Storage] = None
        self.thumbnail_storage: typing.Optional[ThumbnailStorage] = ThumbnailStorage()
        self.image_list_model = ImageListModel()
        self.ui.imageListView.setModel(self.image_list_model)
        self.ui.imageListView.selectionModel().currentChanged.connect(self.handle_current_changed)
        self.ui.imageListView.verticalScrollBar().sliderPressed.connect(self.image_list_model.handle_slider_pressed)
        self.ui.imageListView.verticalScrollBar().sliderReleased.connect(self.handle_image_list_slider_released)
        self.thumbnail_delegate = ThumbnailDelegate(self.thumbnail_storage)
        self.ui.imageListView.setItemDelegate(self.thumbnail_delegate)
        self.ui.imageListView.setUniformItemSizes(True)
        self.ui.imageListView.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred))

        self.ui.actionOpen_folder.triggered.connect(self.handle_action_open_folder_triggered)

    def set_storage(self, storage: Storage):
        self.storage = storage
        self.thumbnail_storage.initialize(self.storage)
        self.image_list_model.initialize(self.storage.image_paths, self.thumbnail_storage, 0)

    def handle_action_open_folder_triggered(self, checked: bool):
        maybe_path = choose_folder(self)
        if maybe_path is not None:
            strg = LocalStorage.load_from(maybe_path)
            self.set_storage(strg)

    def handle_current_changed(self, current: QModelIndex, previous: QModelIndex):
        row = current.row()
        print(f'now showing {self.storage.image_names[row]}')
        photo = self.storage.get_photo_by_idx(row)
        self.mask_editor.set_photo(photo)

    def handle_image_list_slider_released(self):
        first_idx = self.ui.imageListView.indexAt(QPoint(0, 0))
        last_idx = self.ui.imageListView.indexAt(self.ui.imageListView.viewport().rect().bottomLeft())
        self.image_list_model.handle_slider_released(first_idx, last_idx)

    def closeEvent(self, event: QCloseEvent):
        self.thumbnail_storage.stop()

if __name__ == "__main__":
    app = QApplication([])
    #app.setStyle(TooltipProxyStyle(app.style()))
    #strg = MockStorage.create()
    window = ArthropodDescriber()
    #window.set_storage(strg)
    window.showMaximized()
    #strg.destroy()
    sys.exit(app.exec_())
