import typing

from PySide2.QtCore import QObject, Signal

from arthropod_describer.common.photo_loader import Storage
from arthropod_describer.common.photo import Photo, LabelImg
from arthropod_describer.common.colormap import Colormap


class State(QObject):
    colormap_changed = Signal(Colormap)
    storage_changed = Signal(Storage)
    photo_changed = Signal(Photo)
    photo_index_changed = Signal(int)
    label_img_changed = Signal(LabelImg)

    def __init__(self, parent: QObject = None):
        QObject.__init__(self, parent=parent)
        self._colormap: typing.Optional[Colormap] = None
        self._storage: typing.Optional[Storage] = None
        self._current_photo: typing.Optional[Photo] = None
        self._current_photo_idx: int = -1
        self._current_label_img: typing.Optional[LabelImg] = None

    @property
    def colormap(self) -> Colormap:
        return self._colormap

    @colormap.setter
    def colormap(self, colormap: Colormap):
        self._colormap = colormap
        self.colormap_changed.emit(self._colormap)

    @property
    def storage(self) -> Storage:
        return self._storage

    @storage.setter
    def storage(self, storage: Storage):
        self._storage = storage
        self.storage_changed.emit(self._storage)

    @property
    def current_photo(self) -> Photo:
        return self._current_photo

    @current_photo.setter
    def current_photo(self, photo: Photo):
        self._current_photo = photo
        self.photo_changed.emit(self._current_photo)

    @property
    def current_photo_index(self) -> int:
        return self._current_photo_idx

    @current_photo_index.setter
    def current_photo_index(self, idx: int):
        self._current_photo_idx = idx
        self.current_photo = self.storage.get_photo_by_idx(self._current_photo_idx)
        self.photo_index_changed.emit(self._current_photo_idx)

    @property
    def label_img(self) -> LabelImg:
        return self._current_label_img

    @label_img.setter
    def label_img(self, _label_img: LabelImg):
        self._current_label_img = _label_img
        self.label_img_changed.emit(self._current_label_img)

