import abc
from pathlib import Path
import typing
from enum import IntEnum

from PySide2.QtCore import QSize
from PySide2.QtGui import QImage

from photo_loader import Storage, LocalStorage
from image_list_model import ImageListModel




#class PhotoFolder:
#    def __init__(self, path: Path):
#        self._storage = LocalStorage(path)
#
#    def get_photo(self, image_name: str) -> LocalPhoto:
