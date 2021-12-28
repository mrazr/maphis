import typing
from enum import IntEnum
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep, time
from typing import List, Optional, Tuple
import tempfile

import exifread
import numpy as np
from PySide2 import QtGui, QtCore
from PySide2.QtCore import QObject, QThread, Qt, QSize, QRectF, QTimerEvent, Signal
from PySide2.QtGui import QImage, QColor
from PySide2.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PIL import Image

from arthropod_describer.common.photo_loader import Storage


class ThumbnailLoader(QThread):
    finished = Signal([object, object])

    def __init__(self, indexes: List[int], images: List[str], folder: Path):
        QThread.__init__(self)
        self.folder = folder
        self.images = images
        self.indexes = indexes
        self.thumbnails: List[np.ndarray] = []

    def run(self) -> None:
        for img_name in self.images:
            with open(self.folder / img_name, "rb") as f:
                tags = exifread.process_file(f)
            self.thumbnails.append(tags['JPEGThumbnail'])
        self.finished.emit(self.indexes, self.thumbnails)


def thumbnail_load_loop(folder: Path, in_queue: Queue, out_queue: Queue, storage: Storage, thumbnail_size: QSize):
    while True:
        if in_queue.empty():
            sleep(0.1)
            continue
        while not in_queue.empty():
            idx, img_name = in_queue.get_nowait()
            if idx < 0:
                return
            if not (folder / img_name).exists():
                with Image.open(storage.location / 'images' / img_name) as o_img:
                    thumb_size = list(thumbnail_size.toTuple())
                    if o_img.height < o_img.width:
                        thumb_size = thumb_size[::-1]
                    o_img.thumbnail(tuple(thumb_size))
                    o_img.save(folder / img_name, 'JPEG')

            with Image.open(folder / img_name) as img:
                out_queue.put_nowait((idx, np.asarray(img)))


class ThumbnailState(IntEnum):
    NotLoaded = 0
    Loading = 1
    LoadedBytes = 2
    Decoded = 3


class ThumbnailStorage(QObject):
    thumbnails_loaded = Signal(list)

    def __init__(self, max_thumbnails: int = 200, parent: QObject = None):
        QObject.__init__(self, parent)
        self.thumbnail_count = max_thumbnails
        self.storage: Optional[Storage] = None
        self.thumbnail_bytes: List[Tuple[ThumbnailState, Optional[bytes]]] = []
        self.thumbnails: List[Optional[QImage]] = []
        self.thumbnail_hits: List[int] = []
        self.start = 0
        self.end = 0
        self.lowest_index = 0
        self.highest_index = 0
        self.thumbnail_size = QSize(248, 128)
        self.thumbnail_placeholder = QImage(':/images/thumbnail.png')

        self.loader = QThread()
        self.in_queue: Queue = Queue()
        self.out_queue: Queue = Queue()
        self.preload_queue: Queue = Queue()
        self.load_process: typing.Optional[Process] = None
        self.last_thumbnail_sweep: int = 0
        self.recent_thumbnail_idxs: List[int] = []
        self.recent_thumbnail_flags: List[bool] = []
        self._thumbnail_folder: Path = Path(tempfile.mkdtemp())
        print(f'thumbnail folder is {self._thumbnail_folder}')

    def initialize(self, storage: Storage) -> QSize:
        self.storage = storage
        self.thumbnail_bytes = [(ThumbnailState.NotLoaded, None) for _ in range(self.storage.image_count)]
        self.thumbnails = [None for _ in range(self.storage.image_count)]
        self.thumbnail_hits = [0 for _ in range(self.storage.image_count)]
        self.recent_thumbnail_flags = [False for _ in range(self.storage.image_count)]
        self.load_thumbnail(0)
        self.load_process = Process(target=thumbnail_load_loop,
                                    args=(self._thumbnail_folder, self.in_queue, self.out_queue, self.storage,
                                          self.thumbnail_size))
        self.load_process.start()
        self.startTimer(50)
        self.thumbnail_placeholder = self.thumbnail_placeholder.scaledToHeight(self.thumbnail_size.height(), Qt.SmoothTransformation)
        self.last_thumbnail_sweep = time()
        return self.thumbnail_size

    def get_thumbnail(self, idx: int, dragging: bool) -> Optional[QImage]:
        if self.thumbnail_bytes[idx][0] == ThumbnailState.NotLoaded:
            if not dragging:
                self.load_thumbnails(idx, idx)
            return self.thumbnail_placeholder
        state, thumb = self.thumbnail_bytes[idx]
        if state == ThumbnailState.Decoded:
            self.thumbnail_hits[idx] += 1
            if not self.recent_thumbnail_flags[idx]:
                self.recent_thumbnail_idxs.append(idx)
                self.recent_thumbnail_flags[idx] = True
            return self.thumbnails[idx]
        if state == ThumbnailState.Loading:
            return self.thumbnail_placeholder
        np_img = self.thumbnail_bytes[idx][1]
        pix = QImage(np_img, np_img.shape[1], np_img.shape[0], QImage.Format_RGB888)
        self.thumbnails[idx] = pix
        self.thumbnail_hits[idx] += 1
        self.thumbnail_bytes[idx] = (ThumbnailState.Decoded, self.thumbnail_bytes[idx][1])
        if not self.recent_thumbnail_flags[idx]:
            self.recent_thumbnail_idxs.append(idx)
            self.recent_thumbnail_flags[idx] = True
        return pix

    def load_thumbnail(self, idx: int):
        img_name = self.storage.image_names[idx]
        if not (self._thumbnail_folder / img_name).exists():
            with Image.open(self.storage.location / 'images' / img_name) as o_img:
                thumb_size = [256, 128]
                if o_img.height < o_img.width:
                    thumb_size = thumb_size[::-1]
                o_img.thumbnail(tuple(thumb_size))
                o_img.save(self._thumbnail_folder / img_name, 'JPEG')
        thumb = np.asarray(Image.open(self._thumbnail_folder / img_name))
        self.thumbnail_bytes[idx] = (ThumbnailState.LoadedBytes, thumb)

    def load_thumbnails(self, first_idx: int, last_idx: int):
        for idx in range(first_idx, last_idx+1):
            if idx < 0 or last_idx >= len(self.storage.image_names):
                continue
            if self.thumbnail_bytes[idx][0] != ThumbnailState.NotLoaded or first_idx < 0 or last_idx >= len(self.storage.image_names):
                continue
            self.preload_queue.put_nowait((idx, self.storage.image_names[idx]))

    def handle_load_finished(self, indexes: List[int], thumbnails: List[bytes]):
        for idx, thumb in zip(indexes, thumbnails):
            self.thumbnail_bytes[idx] = (ThumbnailState.LoadedBytes, thumb)
        self.thumbnails_loaded.emit(indexes)

    def timerEvent(self, a0: QTimerEvent) -> None:
        if not self.out_queue.empty():
            indexes: List[int] = []
            while not self.out_queue.empty():
                idx, thumb = self.out_queue.get_nowait()
                self.thumbnail_bytes[idx] = (ThumbnailState.LoadedBytes, thumb)
                indexes.append(idx)
                self.thumbnail_hits[idx] = 10
            self.thumbnails_loaded.emit(indexes)
        while not self.preload_queue.empty():
            thumbs_to_load = set()
            j = 0
            while j < 50 and not self.preload_queue.empty():
                idx, th = self.preload_queue.get_nowait()
                s = self.thumbnail_bytes[idx][0]
                if s == ThumbnailState.NotLoaded:
                    self.thumbnail_bytes[idx] = (ThumbnailState.Loading, None)
                    thumbs_to_load.add((idx, th))
                    j += 1
            thumbs_to_load = sorted(list(thumbs_to_load), key=lambda t: t[0])
            for t in thumbs_to_load:
                self.in_queue.put_nowait(t)
        if time() - self.last_thumbnail_sweep > 10:
            recent_thumbnail_idxs = self.recent_thumbnail_idxs[-200:]
            min_idx = min(recent_thumbnail_idxs, default=-1)
            max_idx = max(recent_thumbnail_idxs, default=-1)
            if min_idx < 0 or max_idx < 0:
                self.last_thumbnail_sweep = time()
                return
            for i in range(len(self.thumbnails)):
                if min_idx <= i <= max_idx or self.thumbnail_bytes[i][0] != ThumbnailState.Decoded:
                    continue
                self.recent_thumbnail_flags[i] = False
                self.thumbnail_bytes[i] = (ThumbnailState.LoadedBytes, self.thumbnail_bytes[i][1])
                self.thumbnails[i] = None
            self.last_thumbnail_sweep = time()

    def stop(self):
        if self.load_process is not None:
            self.load_process.kill()


class ThumbnailDelegate(QStyledItemDelegate):
    def __init__(self, thumbnails: ThumbnailStorage, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)
        self.thumbnails = thumbnails

    def sizeHint(self, option: QStyleOptionViewItem, index: QtCore.QModelIndex) -> QtCore.QSize:
        thumbnail: QImage = index.data(Qt.DecorationRole)
        sz = thumbnail.size()
        sz.setHeight(sz.height() + 32)
        sz.setWidth(sz.width())
        return sz

    def paint(self, painter: QtGui.QPainter, option: QStyleOptionViewItem, index: QtCore.QModelIndex) -> None:
        img_name = index.data(Qt.DisplayRole)
        thumbnail: QImage = index.data(Qt.DecorationRole)
        quality_color = QColor(255, 255, 255) #index.data(Qt.BackgroundRole)
        rect = option.rect
        pic_rect = QRectF(rect.center().x() - 0.5 * thumbnail.size().width(),
                          rect.y() - 0.0 * thumbnail.size().height(),
                          thumbnail.size().width(),
                          thumbnail.size().height())
        text_rect = QRectF(0, rect.y() + pic_rect.height(),
                           rect.width(), 32)
        painter.setRenderHint(painter.SmoothPixmapTransform, True)
        painter.drawImage(pic_rect, thumbnail)
        quality_color = QColor(00, 00, 00, 200) if quality_color is None else quality_color
        painter.fillRect(text_rect, quality_color)
        painter.setPen(QColor(0, 0, 0, 255))
        painter.drawText(text_rect, Qt.AlignCenter, img_name)
        if option.state & QStyle.State_Selected:
            color = option.palette.highlight().color()
            color.setAlpha(100)
            painter.fillRect(rect, color)
