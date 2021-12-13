from pathlib import Path
from typing import List, Optional

from PySide2.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QBrush, QColor, QIcon, QPixmap, QPainter

#from thumbnail_storage import ThumbnailStorage
from .thumbnail_storage import ThumbnailStorage

class ImageListModel(QAbstractListModel):

    def __init__(self, parent: QWidget = None):
        QAbstractListModel.__init__(self, parent)

        self.image_paths: List[Path] = []
        #self.processed_images_count: int = 0
        #self.camera: Optional[Camera] = None
        #self.snow_level1 = QPixmap(':/icons/snowflake.svg')
        #self.snow_level1 = self.snow_level1.scaledToWidth(24)
        #self.snow_level2 = QPixmap()
        #self.snow_level3 = QPixmap()
        #self.sun = QIcon(':/icons/sun.svg')
        #self.moon = QIcon(':/icons/moon.svg')
        #self.quality_colors = {
        #    'BAD': QColor(200, 0, 0),
        #    'OK': QColor(200, 100, 0),
        #    'GOOD': QColor(100, 200, 0),
        #}
        #self._generate_snow_level_icons()
        self.thumbnails: Optional[ThumbnailStorage] = None
        #self.thumbnails.thumbnails_loaded.connect(self.handle_thumbnails_loaded)
        self.dragging = False

    #def _generate_snow_level_icons(self):
    #    self.snow_level2 = QPixmap(2 * self.snow_level1.width(), self.snow_level1.height())
    #    self.snow_level2.fill(QColor(0, 0, 0, 0))
    #    painter1 = QPainter(self.snow_level2)
    #    painter1.drawPixmap(0, 0, self.snow_level1.width(), self.snow_level1.height(), self.snow_level1)
    #    painter1.drawPixmap(self.snow_level1.width(), 0, self.snow_level1)

    #    self.snow_level3 = QPixmap(3 * self.snow_level1.width(), self.snow_level1.height())
    #    self.snow_level3.fill(QColor(0, 0, 0, 0))
    #    painter2 = QPainter(self.snow_level3)
    #    painter2.drawPixmap(0, 0, self.snow_level1)
    #    painter2.drawPixmap(self.snow_level1.width(), 0, self.snow_level1)
    #    painter2.drawPixmap(2 * self.snow_level1.width(), 0, self.snow_level1)

    def initialize(self, image_paths: List[Path], thumbnail_storage: ThumbnailStorage, processed_count: int) -> bool:
        self.image_paths.clear()
        #self.thumbnails.initialize()
        if self.thumbnails is not None:
            self.thumbnails.thumbnails_loaded.disconnect(self.handle_thumbnails_loaded)
        self.thumbnails = thumbnail_storage
        self.thumbnails.thumbnails_loaded.connect(self.handle_thumbnails_loaded)
        self.beginResetModel()
        self.image_paths = image_paths
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        return len(self.image_paths)

    def columnCount(self, parent: QModelIndex = QModelIndex()):
        return 1

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return self.image_paths[index.row()].name
            return None

        #if role == Qt.DecorationRole and index.column() == 1:
        #    average_snow_height = self.camera.average_snow_height(self.image_names[index.row()].name)
        #    if average_snow_height > 0:
        #        if average_snow_height == 1:
        #            return self.snow_level1
        #        elif average_snow_height == 2:
        #            return self.snow_level2
        #        elif average_snow_height >= 3:
        #            return self.snow_level3
        #    return None

        if role == Qt.DecorationRole and index.column() == 0:
            return self.thumbnails.get_thumbnail(index.row(), self.dragging)

        #if role == Qt.BackgroundRole:
        #    photo_state = self.camera.photo_state(index.row())
        #    if photo_state == PhotoState.Processed:
        #        quality = self.camera.image_quality(self.image_names[index.row()].name)
        #        if quality < 0.33:
        #            color = self.quality_colors['BAD']
        #        elif quality < 0.66:
        #            color = self.quality_colors['OK']
        #        else:
        #            color = self.quality_colors['GOOD']
        #        return QBrush(color)
        #    elif photo_state == PhotoState.Skipped:
        #        return QBrush(QColor(150, 150, 150, 255))
        #    else:
        #        QBrush(QColor(0, 0, 0, 200))

        #if role == Qt.UserRole:
        #    return self.image_names[index.row()]

        #if role == Qt.UserRole + 1:
        #    return self.camera.is_snowy(self.image_names[index.row()].name)

        #if role == Qt.UserRole + 2:
        #    return 'snow' if self.camera.is_snowy(self.image_names[index.row()].name) else 'ground'

        #if role == Qt.ForegroundRole and index.row() < self.processed_images_count:
        #    return QBrush(QColor(0, 150, 0))
        return None

    #def set_processed_count(self, count: int):
    #    self.processed_images_count = count
    #    self.dataChanged.emit(self.index(0, 0), self.index(self.processed_images_count - 1, 0), [Qt.BackgroundRole])

    #def update_items(self, start_image: str, end_image: str):
    #    start_id = self.camera.image_names_ids[start_image]
    #    end_id = self.camera.image_names_ids[end_image]
    #    top_left = self.index(start_id, 0)
    #    bottom_right = self.index(end_id, 2)
    #    self.dataChanged.emit(top_left, bottom_right, [Qt.BackgroundRole, Qt.DecorationRole])

    def handle_slider_pressed(self):
        self.dragging = True

    def handle_slider_released(self, first_index: QModelIndex, last_index: QModelIndex):
        self.dragging = False
        self.thumbnails.load_thumbnails(first_index.row() - 50, last_index.row() + 50)

    def handle_thumbnails_loaded(self, indices: List[int]):
        fidx = self.index(indices[0], 0)
        lidx = self.index(indices[-1], 0)
        self.dataChanged.emit(fidx, lidx, [Qt.DecorationRole])
