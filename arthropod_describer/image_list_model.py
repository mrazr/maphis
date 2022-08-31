import typing
from pathlib import Path
from typing import List

import PySide2
from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt, QSortFilterProxyModel
from PySide2.QtWidgets import QWidget

from arthropod_describer.common.local_storage import Storage
from arthropod_describer.common.photo import Photo, UpdateContext
from arthropod_describer.common.state import State
from arthropod_describer.thumbnail_storage import ThumbnailStorage_

ROLE_IMAGE_NAME = Qt.UserRole + 1
ROLE_THUMBNAIL = Qt.UserRole + 3
ROLE_IS_APPROVED = Qt.UserRole + 42
ROLE_APPROVAL_COUNT = Qt.UserRole + 4
ROLE_IS_HIGHLIGHTED = Qt.UserRole + 5
ROLE_HAS_UNSAVED_CHANGES = Qt.UserRole + 6
ROLE_SCALE_MARKER_IMAGE = Qt.UserRole + 7
ROLE_IMAGE_PATH = Qt.UserRole + 8
ROLE_TAGS = Qt.UserRole + 9


class ImageListModel(QAbstractListModel):

    def __init__(self, parent: QWidget = None):
        QAbstractListModel.__init__(self, parent)

        self.highlighted_indexes: List[int] = []
        self.image_paths: List[Path] = []
        # self.thumbnails: Optional[ThumbnailStorage] = None
        self.dragging = False
        self.storage: Storage = None

    def initialize(self, image_paths: List[Path], thumbnail_storage: ThumbnailStorage_, processed_count: int, storage: Storage) -> bool:
        self.storage = storage
        self.storage.update_photo.connect(self._handle_photo_update)
        self.storage.storage_update.connect(self._handle_storage_update)
        self.thumbnail_storage = thumbnail_storage
        self.thumbnail_storage.update_photo.connect(self._handle_thumbnail_update)
        self.highlighted_indexes = []
        # if self.thumbnails is not None:
        #     self.thumbnails.thumbnails_loaded.disconnect(self.handle_thumbnails_loaded)
        # self.thumbnails = thumbnail_storage
        # self.thumbnails.thumbnails_loaded.connect(self.handle_thumbnails_loaded)
        self.beginResetModel()
        self.image_paths = image_paths
        self.endResetModel()
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.image_paths), 0))

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        return 0 if self.storage is None else self.storage.image_count

    def columnCount(self, parent: QModelIndex = QModelIndex()):
        return 1

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.storage.image_names[index.row()]
            return None
        if role == ROLE_IMAGE_NAME:
            return self.storage.image_names[index.row()]

        if role == ROLE_THUMBNAIL and index.column() == 0:
            photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
            return photo.thumbnail

        if role == ROLE_IS_APPROVED:
            return self.storage.is_approved(index.row())

        if role == ROLE_APPROVAL_COUNT:
            photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
            approval = photo.approved['Labels']
            mask_names = self.storage.get_label_hierarchy2('Labels').mask_names
            approval_count = 0 if approval is None else mask_names.index(approval) + 1
            return approval_count, len(mask_names)
        if role == ROLE_IS_HIGHLIGHTED:
            if len(self.highlighted_indexes) > 0:
                return index.row() in self.highlighted_indexes
            return True
        if role == ROLE_HAS_UNSAVED_CHANGES:
            return self.storage.get_photo_by_idx(index.row(), load_image=False).has_unsaved_changes

        if role == ROLE_SCALE_MARKER_IMAGE:
            photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
            if photo.scale_setting is None:
                return None
            return photo.scale_setting.scale_marker_img
        if role == ROLE_IMAGE_PATH:
            return self.storage.get_photo_by_idx(index.row(), load_image=False).image_path

        if role == ROLE_TAGS:
            return self.storage.get_photo_by_idx(index.row(), load_image=False).tags

        return None

    def highlight_indexes(self, idxs: List[int]):
        self.highlighted_indexes = idxs
        self.dataChanged.emit(self.createIndex(0, 0),
                              self.createIndex(self.rowCount() - 1, 0))

    def handle_slider_pressed(self):
        self.dragging = True

    def handle_slider_released(self, first_index: QModelIndex, last_index: QModelIndex):
        self.dragging = False
        # self.thumbnails.load_thumbnails(first_index.row() - 50, last_index.row() + 50)

    def handle_thumbnails_loaded(self, indices: List[int]):
        fidx = self.index(indices[0], 0)
        lidx = self.index(indices[-1], 0)
        self.dataChanged.emit(fidx, lidx, [ROLE_THUMBNAIL])

    def handle_approval_changed(self, photo: Photo):
        idx = self.storage.image_names.index(photo.image_name)
        index = self.index(idx, 0)
        self.dataChanged.emit(index, index, [ROLE_IS_APPROVED])

    def _handle_photo_update(self, img_name: str, ctx: UpdateContext, data: typing.Dict[str, typing.Any]):
        index = self.index(self.storage.image_names.index(img_name), 0)
        if 'tags' in data:
            self.dataChanged.emit(index, index, [ROLE_TAGS])

    def _handle_storage_update(self, data: typing.Dict[str, typing.Any]):
        if 'photos' in data:
            if 'deleted' in data['photos']:
                self.beginResetModel()
                self.endResetModel()

    def _handle_thumbnail_update(self, img_name: str, ctx: UpdateContext, data: typing.Dict[str, typing.Any]):
        i = self.storage.image_names.index(img_name)
        idx = self.index(i, 0)
        self.dataChanged.emit(idx, idx, [ROLE_THUMBNAIL])


class ImageListSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, state: State, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)
        self._state = state

    def filterAcceptsRow(self, source_row: int, source_parent: PySide2.QtCore.QModelIndex) -> bool:
        index = self.sourceModel().index(source_row, 0, source_parent)
        tags: typing.Set[str] = self.sourceModel().data(index, ROLE_TAGS)
        # return self.filterRegExp().pattern() in tags
        return set(self._state.active_tags_filter).issubset(tags)
