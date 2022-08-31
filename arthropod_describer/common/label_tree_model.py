import typing
from enum import IntEnum
from functools import partial

import PySide2
from PySide2.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide2.QtGui import QColor

from arthropod_describer.common.label_hierarchy import Node, LabelHierarchy
from arthropod_describer.common.state import State


class LabelTreeMode(IntEnum):
    Choosing = 0,
    ChoosingAndConstraint = 1,


class LabelTreeModel(QAbstractItemModel):
    def __init__(self, state: State, mode: LabelTreeMode = LabelTreeMode.ChoosingAndConstraint, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)
        self.state = state
        self.mode: LabelTreeMode = mode

    def columnCount(self, parent: PySide2.QtCore.QModelIndex = None) -> int:
        return 1 if self.mode == LabelTreeMode.Choosing else 2

    def data(self, index: PySide2.QtCore.QModelIndex, role: int = Qt.DisplayRole) -> typing.Any:
        label_node: Node = index.internalPointer()
        if index.internalPointer() is None:
            return None
        if index.column() == 0:
            if role == Qt.DisplayRole:
                return label_node.name #self.state.colormap.label_names[label_node.label]
            elif role == Qt.DecorationRole:
                return QColor(*label_node.color) #QColor(*self.state.colormap.colormap[label_node.label])
            elif role == Qt.ForegroundRole:
                if self.mode == LabelTreeMode.Choosing:
                    return QColor.fromRgb(0, 0, 0)
                elif label_node.label == self.state.primary_label:
                    return QColor.fromRgb(0, 0, 0)
                elif self.state.constraint_label == 0 or self.state.label_hierarchy.is_descendant_of(label_node.label, self.state.constraint_label):
                    return QColor.fromRgb(0, 0, 0)
                else:
                    return QColor.fromRgb(192, 192, 192)
            elif role == Qt.BackgroundRole:
                if self.mode == LabelTreeMode.ChoosingAndConstraint and label_node.label == self.state.primary_label:
                    return QColor.fromRgb(0, 200, 0, 100)

        return None

    def index(self, row: int, column: int, parent: PySide2.QtCore.QModelIndex = QModelIndex()) -> PySide2.QtCore.QModelIndex:
        if not parent.isValid():
            return self.createIndex(row, column, self.state.label_hierarchy.nodes[LabelHierarchy.ROOT].children[row])

        parent_node: Node = parent.internalPointer()
        if row >= len(parent_node.children):  # TODO this should not be necessary, but alas
            return QModelIndex()
        return self.createIndex(row, column, parent_node.children[row])

    def rowCount(self, parent: PySide2.QtCore.QModelIndex = QModelIndex()) -> int:
        if self.state.label_hierarchy is None:
            return 0
        if not parent.isValid():
            return len(self.state.label_hierarchy.children[LabelHierarchy.ROOT])

        parent_node: Node = parent.internalPointer()

        return len(parent_node.children)

    def parent(self, child: QModelIndex) -> QModelIndex:
        label_node: Node = child.internalPointer()
        if label_node is None or label_node.label == LabelHierarchy.ROOT:
            return QModelIndex()
        parent_node = label_node.parent
        return self.createIndex(self.state.label_hierarchy.children[parent_node.label].index(label_node.label), 0, parent_node)

    def flags(self, index:PySide2.QtCore.QModelIndex) -> PySide2.QtCore.Qt.ItemFlags:
        if self.mode == LabelTreeMode.ChoosingAndConstraint:
            if index.column() == 0 or index.internalPointer().label == 0:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            if index.internalPointer().label == 0:
                return Qt.NoItemFlags
            label = index.internalPointer().label
            used_labels = self.state.storage.used_regions('Labels') # TODO un-hard-code 'Labels'
            hierarchy = self.state.label_hierarchy
            if label in used_labels or any(map(partial(hierarchy.is_ancestor_of, label), used_labels)):
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            return Qt.NoItemFlags

    def set_constraint(self, label: int):
        index = self.find_index(label)
        self.dataChanged.emit(self.index(0, 0, QModelIndex()),
                              self.index(self.rowCount(QModelIndex())-1, 1, QModelIndex()),
                              [Qt.ForegroundRole])

    def find_index(self, label: int) -> QModelIndex:
        lab_hier = self.state.label_hierarchy
        index = self.parent(self.index(0, 0))

        while index.isValid():
            for child_idx in range(self.rowCount(index)):
                child = index.child(child_idx, 0)
                label_node: Node = child.internalPointer()
                if label_node.label == label:
                    return child
                elif lab_hier.is_ancestor_of(label_node.label, label):
                    index = child
                    break
        return index

    def handle_label_color_changed(self, label: int, color: QColor):
        index = self.find_index(label)
        lab_node: Node = index.internalPointer()
        lab_node.color = color.toTuple()[:3]
        self.dataChanged.emit(index, index, Qt.DecorationRole)
