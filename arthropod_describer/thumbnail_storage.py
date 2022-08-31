import os
import re
import typing
from pathlib import Path
from typing import List, Optional

from PIL import Image
from PySide2 import QtGui, QtCore
from PySide2.QtCore import QObject, Qt, QSize, QRectF
from PySide2.QtGui import QImage
from PySide2.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

from arthropod_describer.common.local_storage import Storage
from arthropod_describer.common.photo import UpdateContext, Photo
from arthropod_describer.common.storage import IMAGE_REFEX


class ThumbnailStorage_(Storage):
    def __init__(self, storage: Storage, thumbnail_size: typing.Tuple[int, int] = (248, 128),
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self._main_storage: Storage = storage
        self._main_storage.storage_update.connect(self._handle_storage_update)
        self._main_storage.update_photo.connect(self._handle_photo_update)
        # TODO connect to storage signals to react to inclusion/deletion, rotation etc.
        self._location = self._main_storage.location / '.thumbnails'
        if not self._location.exists():
            os.mkdir(self._location)

        self.thumbnail_size: typing.Tuple[int, int] = thumbnail_size
        self._load_thumbnails()

    def _load_thumbnails(self):
        for img in self._main_storage.images:
            if not (self._location / img.image_path.name).exists():
                self._generate_thumbnail(img)
            else:
                with Image.open(self._location / img.image_name) as im:
                    img.thumbnail = im.toqimage()

    def _generate_thumbnail(self, photo: Photo):
        with Image.open(photo.image_path) as im:
            im.thumbnail(self.thumbnail_size, resample=1)
            im = im.convert('RGB')
            im.save(self._location / photo.image_path.name, 'JPEG')
            photo.thumbnail = im.toqimage()

    def _handle_storage_update(self, data: typing.Dict[str, typing.Any]):
        if 'photos' not in data:
            return
        for new_photo_name in data['photos'].setdefault('included', []):
            photo = self._main_storage.get_photo_by_name(new_photo_name, load_image=False)
            self._generate_thumbnail(photo)
        for deleted_photo_name in data['photos'].setdefault('deleted', []):
            if (thumb_path := self._location / deleted_photo_name).exists():
                os.remove(thumb_path)

    def _handle_photo_update(self, photo_name: str, ctx: UpdateContext, data: typing.Dict[str, typing.Any]):
        if 'operation' not in data or not data['operation'].startswith('rot'):
            return
        photo = self._main_storage.get_photo_by_name(photo_name, load_image=False)
        self._generate_thumbnail(photo)
        # with Image.open(self._location / photo.image_name) as im:
        #     im = im.rotate(90 if ccw else -90, 1, expand=True)
        #     im.save(self._location / photo.image_name)
        #     photo.thumbnail = im.toqimage()
        self.update_photo.emit(photo_name, ctx, {})

    @property
    def location(self) -> Path:
        return self._location

    @classmethod
    def load_from(cls, folder: Path, image_regex: re.Pattern = IMAGE_REFEX) -> typing.Optional['ThumbnailStorage_']:
        return None

    def get_photo_by_idx(self, idx: int, load_image: bool = True) -> Photo:
        raise NotImplementedError(f'{self.__class__.__name__}.get_photo_by_idx is prohibited to use.')

    def get_photo_by_name(self, name: str, load_image: bool = True) -> Photo:
        raise NotImplementedError(f'{self.__class__.__name__}.get_photo_by_name is prohibited to use.')

    @property
    def image_count(self) -> int:
        return self._main_storage.image_count

    @property
    def image_paths(self) -> List[str]:
        return [str(self._location / img_name) for img_name in self._main_storage.image_names]

    @property
    def image_names(self) -> List[str]:
        return self._main_storage.image_names

    @property
    def images(self) -> List[Photo]:
        raise NotImplementedError(f'{self.__class__.__name__}.images is prohibited to use.')

    def save(self) -> bool:
        return super().save()

    def include_photos(self, photo_names: List[str], scale: Optional[int]):
        raise NotImplementedError(f'{self.__class__.__name__}.include_photos() is prohibited to use.')

    @property
    def storage_name(self) -> str:
        return f'{self._main_storage.storage_name}_thumbnails'

    def delete_photo(self, img_name: str, parent: QWidget) -> bool:
        raise NotImplementedError(f'{self.__class__.__name__}.delete_photo() is prohibited to use.')


class ThumbnailDelegate(QStyledItemDelegate):
    def __init__(self, thumbnails: ThumbnailStorage_, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)
        self.thumbnails = thumbnails

    def sizeHint(self, option: QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
        # thumbnail: QImage = index.data(Qt.UserRole + 3)
        sz = QSize(*self.thumbnails.thumbnail_size)
        # sz = QSize(248, 128)
        sz.setHeight(sz.height() + 32)
        sz.setWidth(sz.width())
        return sz

    def paint(self, painter: QtGui.QPainter, option: QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        painter.save()
        approved = index.data(Qt.UserRole + 42)
        thumbnail: QImage = index.data(Qt.UserRole + 3)
        #quality_color = QColor(0, 125, 60) if approved else QColor(200, 150, 0) #QColor(255, 255, 255) #index.data(Qt.BackgroundRole)
        rect = option.rect
        pic_rect = QRectF(rect.center().x() - 0.5 * thumbnail.size().width(),
                          rect.center().y() - 0.5 * thumbnail.size().height() - 16 + 4,
                          thumbnail.size().width(),
                          thumbnail.size().height() - 4)
        painter.setRenderHint(painter.SmoothPixmapTransform, True)
        painter.drawImage(pic_rect, thumbnail)
        painter.restore()
