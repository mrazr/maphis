import importlib.resources
import typing
from typing import Optional, List, Dict

from PySide2.QtCore import Signal, QSize
from PySide2.QtGui import QPixmap, Qt, QIcon
from PySide2.QtWidgets import QWidget, QGroupBox, QHBoxLayout, QButtonGroup, QAbstractButton, QPushButton, QSizePolicy, \
    QVBoxLayout, QCheckBox, QLabel, QToolButton

from arthropod_describer.common.label_hierarchy import LabelHierarchy
from arthropod_describer.common.local_storage import Storage
from arthropod_describer.common.state import State


class LabelLevelSwitch(QGroupBox):
    label_level_switched = Signal(int)
    approval_toggled = Signal([int, bool])

    def __init__(self, state: State, parent: Optional[QWidget] = None):
        QGroupBox.__init__(self, parent)
        self.setTitle('Approved levels')
        self.state: State = state
        self.state.storage_changed.connect(self.handle_storage_changed)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._label_buttons_group = QButtonGroup(self)
        self._label_buttons_group.setExclusive(False)
        #self._label_buttons_group.setExclusive(True)
        #self._label_buttons_group.idClicked.connect(self.label_level_switched.emit)
        #self._label_buttons_group.buttonClicked.connect(self._handle_button_clicked)
        self._label_buttons_group.buttonClicked.connect(self._handle_button_toggled)

        stylesheet = "QCheckBox:unchecked { color: rgb(220, 150, 0); }\nQCheckBox:checked { color: rgb(0, 150, 0); }"
        self.setStyleSheet(stylesheet)

        self._buttons: List[QPushButton] = []

        self._label_hierarchy: Optional[LabelHierarchy] = None

        self.selected_label_levels: Dict[str, int] = {}

        self.unapproved_stylesheet: str = QPushButton().styleSheet() + '; border: 1px solid orange'
        self.approved_stylesheet: str = QPushButton().styleSheet() + '; border: 1px solid green'

        #with importlib.resources.open_binary("arthropod_describer.resources", "check.png") as icon_io:
        #    bytes = icon_io.read()
        #    pixmap = QPixmap()
        #    if not pixmap.loadFromData(bytes, len(bytes), "PNG"):
        #        print("NOT GOOD")
        #    self._check_icon = QIcon()

        with importlib.resources.path("resources", "check.png") as path:
            self.check_icon = QIcon(str(path))

        with importlib.resources.path("resources", "question.png") as path:
            self.question_icon = QIcon(str(path))

    def _handle_button_clicked(self, btn: QAbstractButton):
        self.label_level_switched.emit(self._label_buttons_group.id(btn))
        self.selected_label_levels[self.state.current_label_name] = self._label_buttons_group.id(btn)

    def _handle_button_toggled(self, btn: QAbstractButton):
        self.approval_toggled.emit(self._label_buttons_group.id(btn), btn.isChecked())

    def handle_storage_changed(self, storage: Storage, old_storage: typing.Optional[Storage]):
        self.selected_label_levels.clear()
        for label_name in storage.label_image_names:
            self.selected_label_levels[label_name] = 0

    def set_label_hierarchy(self, lab_hier: LabelHierarchy):
        self._label_hierarchy = lab_hier
        for btn in self._buttons:
            btn.setVisible(False)
            self._label_buttons_group.removeButton(btn)
            self.layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
        for i, name in enumerate(self._label_hierarchy.mask_names):
            #btn = QToolButton()
            btn = QCheckBox()
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.setText(name)
            btn.setObjectName(f'btnLevel_{name}')
            btn.setCheckable(True)
            #btn.setIcon(self.question_icon)
            btn.setIconSize(QSize(24, 24))
            # if i == 0:
            #     btn.setChecked(True)
            self.layout.addWidget(btn)
            self._label_buttons_group.addButton(btn, i)
            self._buttons.append(btn)
        self.setEnabled(True)
        self.update()

    def return_to_level_for(self, label_name: str):
        level = self.selected_label_levels[label_name]
        if len(self._buttons) > 1:
            self._buttons[level].animateClick(1)
        else:
            self._handle_button_clicked(self._buttons[level])

    #def get_level_button(self, level_name: str) -> Optional[QAbstractButton]:
    #    return self._label_buttons_group.findChild(QPushButton, f'btnLevel_{level_name}')

    def get_level_button(self, idx: int):
        return self._label_buttons_group.button(idx)

    def mark_approved(self, idx: int, approved: bool):
        #self._label_buttons_group.button(idx).setStyleSheet(self.approved_stylesheet if approved else self.unapproved_stylesheet)
        btn = self._label_buttons_group.button(idx)
        btn.setChecked(approved)
        #if approved:
        #    btn.setIcon(self.check_icon)
        #else:
        #    btn.setIcon(self.question_icon)
