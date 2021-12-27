import json
import typing
from typing import Optional, Union, Dict, Any, List, Tuple
from pathlib import Path

import PySide2
from PySide2.QtCore import QAbstractItemModel, QObject, Qt, QModelIndex
from PySide2.QtGui import QColor

NAME = 'name'
COLORMAP = 'colormap'


class Colormap(QAbstractItemModel):
    def __init__(self, cmap: Optional[Union[str, Dict[str, Any]]]=None, cmap_path: Optional[Path]=None, parent: QObject=None):
        QAbstractItemModel.__init__(self, parent)
        assert not (cmap is None and cmap_path is None)
        self.cmap = None
        if cmap is not None:
            if isinstance(cmap, str): # assume cmap is in JSON string format
                self.cmap = json.loads(cmap)
            elif isinstance(cmap, dict):
                self.cmap = cmap
        else: # load cmap in json format from the path
            with open(cmap_path) as f:
                self.cmap = json.load(f)

        assert NAME in self.cmap
        assert COLORMAP in self.cmap

        if 'ignore' in self.cmap:
            del self.cmap['ignore']

        self.labels: List[int] = list(sorted([int(label) for label in self.cmap[COLORMAP].keys()]))
        c = 'color'
        r = 'red'
        g = 'green'
        b = 'blue'
        self.colormap: Dict[int, Tuple[int, int, int]] = {int(label): (v[c][r], v[c][g], v[c][b]) for label, v in self.cmap[COLORMAP].items()}
        self.label_names: Dict[int, str] = {int(label): v['name'] for label, v in self.cmap[COLORMAP].items()}

    @property
    def name(self) -> str:
        return self.cmap[NAME]

    @property
    def color_count(self) -> int:
        return len(self.labels)

    def get_color(self, label: int) -> Tuple[int, int, int]:
        return self.colormap[label]

    def get_named_color(self, label: int) -> Tuple[str, Tuple[int, int, int]]:
        return self.label_names[label], self.colormap[label]

    def rowCount(self, parent:PySide2.QtCore.QModelIndex=...) -> int:
        return self.color_count

    def columnCount(self, parent:PySide2.QtCore.QModelIndex=...) -> int:
        return 1

    def index(self, row:int, column:int, parent:PySide2.QtCore.QModelIndex=...) -> PySide2.QtCore.QModelIndex:
        return self.createIndex(row, 0)

    def parent(self, index: QModelIndex) -> PySide2.QtCore.QObject:
        return QModelIndex()

    def data(self, index:PySide2.QtCore.QModelIndex, role:int=...) -> typing.Any:
        label = self.labels[index.row()]
        name, color = self.get_named_color(label)

        if role == Qt.DisplayRole:
            return f'{name} ({label})'
        elif role == Qt.DecorationRole:
            return QColor.fromRgb(*color)
        else:
            return None
