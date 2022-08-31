import typing

import PySide2
from PySide2.QtCore import Signal, QModelIndex, Qt, QItemSelection, QItemSelectionModel
from PySide2.QtGui import QColor
from PySide2.QtWidgets import QTreeView, QToolButton

from arthropod_describer.common.label_hierarchy import LabelHierarchy, Node
from arthropod_describer.common.label_tree_model import LabelTreeModel
from arthropod_describer.common.state import State


class LabelTreeView(QTreeView):
    constraint_requested = Signal(int)
    unset_constraint = Signal()
    label_clicked = Signal(int)
    label_color_change = Signal([int, QColor])
    label_dbl_click = Signal(Node)

    def __init__(self, state: State, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None):
        super().__init__(parent)
        self._btn = QToolButton()
        self._curr_index: QModelIndex = QModelIndex()
        self._curr_label: int = -1
        self._constraint_index: typing.Optional[QModelIndex] = QModelIndex()
        self._constraint_label: int = -1
        self._btn_constraint: typing.Optional[QToolButton] = None
        self.state: State = state
        self.state.label_hierarchy_changed.connect(self._handle_label_hierarchy_changed)
        self.state.primary_label_changed.connect(self.choose_label)
        # self.clicked.connect(self._handle_index_activated)
        self.clicked.connect(self._index_click_handler)
        self.setExpandsOnDoubleClick(False)
        self.clicked_idx: QModelIndex = QModelIndex()
        self.setStyleSheet("QTreeView::item { padding: 1px }")
        self.setMouseTracking(True)
        self.entered.connect(self._set_constraint_button)
        self._can_be_self_constrained: bool = True
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self._constraint_mode: bool = False
        self._label_tree_model: typing.Optional[LabelTreeModel] = None

    def _handle_label_hierarchy_changed(self, lab_hier: LabelHierarchy):
        self.reset()
        self.resizeColumnToContents(0)

    def _set_constraint_button(self, index: QModelIndex):
        if not self._can_be_self_constrained:
            return
        if index.internalPointer().label == 0 or (index.internalPointer().label == self.state.constraint_label):
            return
        dst_index = index if index.column() == 1 else index.siblingAtColumn(1)
        if self._curr_index.isValid():
            self.setIndexWidget(self._curr_index, None)
            self._curr_index = QModelIndex()
        btn = QToolButton(text="Set constraint")
        btn.clicked.connect(self.accept_constraint)
        self.setIndexWidget(dst_index, btn)
        self._curr_index = dst_index

    def _handle_index_activated(self, idx: QModelIndex):
        if idx.column() > 0:
            return
        if self.clicked_idx == idx:
            return
        # self.label_clicked.emit(idx.internalPointer().label)
        if self.clicked_idx.isValid():
            self.model().dataChanged.emit(self.clicked_idx, self.clicked_idx, Qt.BackgroundRole)
        self.model().dataChanged.emit(idx, idx, Qt.BackgroundRole)
        self.clicked_idx = idx
        # TODO update the label tree view to show the selected label
        #self.reset()
        #self.expandAll()

    def choose_label(self, label: typing.Union[int, QModelIndex]):
        if isinstance(label, QModelIndex):
            index = label
        else:
            index = self._label_tree_model.find_index(label)
        self.selectionModel().select(index, QItemSelectionModel.SelectCurrent)

    def _index_click_handler(self, index: QModelIndex):
        label = index.internalPointer().label
        self.state.primary_label = label

    # def setModel(self, model: PySide2.QtCore.QAbstractItemModel):
    def setModel(self, model: LabelTreeModel):
        self._label_tree_model = model
        self.setMouseTracking(True)
        self.clicked_idx = QModelIndex()
        self._can_be_self_constrained = False
        if self.state.label_can_be_constrained:
            if (possible_constraints := self.state.storage.label_img_info[self.state.current_label_name].can_constrain_to) is not None:
                self._can_be_self_constrained = self.state.current_label_name in possible_constraints
        super().setModel(model)
        self._constraint_mode = self.model().columnCount() == 2
        self._can_be_self_constrained = self._can_be_self_constrained and self._constraint_mode
        self.expandAll()
        self.resizeColumnToContents(0)

    def accept_constraint(self):
        if self._constraint_index is not None and self._constraint_index.isValid():
            self.remove_unset_constraint_btn()
        btn = QToolButton()
        btn.setText("Remove constraint")
        btn.clicked.connect(self._unset_constraint)
        self.setIndexWidget(self._curr_index, btn)
        self._btn_constraint = btn
        self._constraint_index = self._curr_index
        self._curr_index = QModelIndex()
        self.state.current_constraint.label_name = self.state.current_label_name
        self.state.constraint_label = self._constraint_index.internalPointer().label

    def leaveEvent(self, event:PySide2.QtCore.QEvent):
        if self._curr_index.internalPointer() is None:
            self.setIndexWidget(self._curr_index, None)
            return
        if self._curr_index.isValid():
            if self._constraint_index.internalPointer() is not None:
                if self._constraint_index.internalPointer().label != self._curr_index.internalPointer().label:
                    self.setIndexWidget(self._curr_index, None)
                    self._curr_index = QModelIndex()
            else:
                self.setIndexWidget(self._curr_index, None)
                self._curr_index = QModelIndex()

            #self._delegate.destroyEditor(self._delegate.editor, self._curr_index)
        self._curr_label = -1

    def _unset_constraint(self, set_constraint_button: bool = True):
        index = self._constraint_index
        self.remove_unset_constraint_btn()
        self.state.constraint_label = 0
        self.state.current_constraint.label_name = None
        self.state.current_constraint.label_node = None
        if set_constraint_button:
            self._set_constraint_button(index)

    def remove_unset_constraint_btn(self):
        self.setIndexWidget(self._constraint_index, None)
        self._constraint_index = QModelIndex()
        self._btn_constraint = None
        # self.reset()
        # self.expandAll()

    def set_constraint(self, index: QModelIndex):
        self._curr_index = index
        self.accept_constraint()

    def mouseDoubleClickEvent(self, event:PySide2.QtGui.QMouseEvent):
        index = self.indexAt(event.pos())
        node: Node = index.internalPointer()
        self.label_dbl_click.emit(node)
