import typing

import PySide2
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QColor, QPixmap, QValidator
from PySide2.QtWidgets import QWidget, QColorDialog, QDialogButtonBox, QDialog

from arthropod_describer.common.label_hierarchy import Node
from arthropod_describer.common.state import State
from arthropod_describer.label_editor.ui_new_label_dialog import Ui_NewLabelDialog


class LabelNameValidator(QValidator):

    def __init__(self, state: State, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)
        self.state: State = state
        self._editted_label_name: str = ''
        self._all_names: typing.Set[str] = set()

    def initialize_with_name(self, label_name: str):
        self._editted_label_name = label_name
        self._all_names.clear()
        self._all_names = {node.name for node in self.state.label_hierarchy.nodes.values()}
        self._all_names.remove(label_name)

    def validate(self, cand_name: str, cursor_pos: int) -> PySide2.QtGui.QValidator.State:
        if cand_name in self._all_names:
            return QValidator.Intermediate
        return QValidator.Acceptable


class NewLabelDialog(QDialog):
    add_new_label_requested = Signal([int, str, QColor])
    modified_label = Signal(int, str, QColor)

    def __init__(self, state: State, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)
        self.state: State = state
        self.ui = Ui_NewLabelDialog()
        self.ui.setupUi(self)
        self._lblColor_pixmap = QPixmap(self.ui.lblColor.minimumSize())
        self._label_color: QColor = QColor()
        self.ui.btnSetColor.clicked.connect(self._pick_color)
        self._parent_node: typing.Optional[Node] = None
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.ui.txtLabelCode.setEnabled(False)
        # TODO set a validator for self.ui.txtLabelName to reject values clashing with already used label names
        # self._name_validator: LabelNameValidator = LabelNameValidator(self.state)
        self.ui.txtLabelName.textChanged.connect(self._handle_txtLabelName_changed)
        # self.ui.btnColor.setPixmap(self._lblColor_pixmap)
        # self.ui.btnColor.setIcon(QIcon(self._lblColor_pixmap))
        # self.ui.btnColor.setIconSize(self.ui.btnColor.minimumSize())

        self._modified_label_name: str = ''
        self._all_label_names: typing.Set[str] = set()

        self.setWindowModality(Qt.ApplicationModal)

    def add_new_label(self, parent_label: int):
        parent_node = self.state.label_hierarchy.nodes[parent_label]
        self._label_color = QColor()
        self._parent_node = parent_node
        self._lblColor_pixmap.fill(QColor(*parent_node.color))

        self.ui.txtLabelName.setText('')
        new_label = self.state.label_hierarchy.get_available_label(parent_label)
        self.ui.txtLabelCode.setText(self.state.label_hierarchy.code(new_label))

        self._modified_label_name = ''
        self._all_label_names = {node.name for node in self.state.label_hierarchy.nodes.values()}
        # self._name_validator.initialize_with_name('')
        # self.ui.txtLabelName.setValidator(self._name_validator)

        # self.ui.btnColor.setIcon(QIcon(self._lblColor_pixmap))
        self.setWindowTitle(f'Add a new child label of {parent_node.name}')
        self.ui.lblColor.setPixmap(self._lblColor_pixmap)
        if self.exec_() == QDialog.Accepted:
            # self.state.label_hierarchy.add_child_label(self._parent_node.label, self.ui.txtLabelName.text(),
            #                                            self._label_color.toTuple()[:3])

            self.add_new_label_requested.emit(self._parent_node.label, self.ui.txtLabelName.text(), self._label_color)

    def modify_label(self, label: int):
        label_node = self.state.label_hierarchy.nodes[label]
        self._label_color = QColor()
        self._parent_node = label_node

        self.ui.btnSetColor.setEnabled(label > 0)

        self._modified_label_name = label_node.name
        self._all_label_names = {node.name for node in self.state.label_hierarchy.nodes.values()}
        self._all_label_names.remove(self._modified_label_name)

        # self._name_validator.initialize_with_name(label_node.name)
        # self.ui.txtLabelName.setValidator(self._name_validator)

        self._lblColor_pixmap.fill(QColor(*label_node.color))
        self.ui.lblColor.setPixmap(self._lblColor_pixmap)
        self.ui.txtLabelName.setText(label_node.name)
        self.ui.txtLabelCode.setText(label_node.code)
        self.setWindowTitle(f'Modify {label_node.name}')
        role = self.exec_()
        if role == QDialog.Accepted:
            self.modified_label.emit(label_node.label, self.ui.txtLabelName.text(), self._label_color)

    def _handle_txtLabelName_changed(self, text: str):
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(text not in self._all_label_names)

    def _pick_color(self):
        color = QColorDialog.getColor(initial=QColor(*self._parent_node.color))
        if color.isValid():
            self._lblColor_pixmap.fill(color)
            self.ui.lblColor.setPixmap(self._lblColor_pixmap)
            self._label_color = color
