import bisect
import typing

import PySide2
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QPushButton, QVBoxLayout, QScrollArea, QSizePolicy, \
    QDialog, QLineEdit, QLabel, QToolButton, QTableWidget, QTableWidgetItem, QGridLayout, QGroupBox

from arthropod_describer.common.photo import Photo, UpdateContext
from arthropod_describer.common.state import State


class TagLine(QWidget):
    tag_delete_request = Signal(str)
    tag_toggled = Signal([str, bool])
    tag_assign_global = Signal(str)

    def __init__(self, tag: str, enabled: bool = True, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)

        self.tag = tag
        self._layout = QHBoxLayout()
        self._checkbox = QCheckBox(text=tag)
        self._checkbox.setChecked(enabled)
        self._checkbox.toggled.connect(lambda b: self.tag_toggled.emit(self.tag, b))
        # self._checkbox.toggled.connect(lambda b: self.photo.toggle_tag(self.tag, b))
        self._btn_delete = QToolButton(text="x")
        self._btn_delete.setToolTip("Delete tag from the project.")
        self._btn_delete.clicked.connect(lambda: self.tag_delete_request.emit(self.tag))

        self._btn_assign_global = QToolButton(text='all')
        self._btn_assign_global.setToolTip("Assign tag to all photos.")
        self._btn_assign_global.clicked.connect(lambda: self.tag_assign_global.emit(self.tag))

        self._layout.addWidget(self._checkbox)
        # self._layout.addWidget(self._btn_assign_global)
        # self._layout.addWidget(self._btn_delete)

        self.setLayout(self._layout)


class TagsWidget(QDialog):
    widget_left = Signal()

    def __init__(self, state: State, title: str = 'Photo tags', parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, Qt.Window
            | Qt.X11BypassWindowManagerHint
            | Qt.FramelessWindowHint)
        self._state = state
        self.storage = self._state.storage
        self.setVisible(False)
        # self.tags = self.storage.used_tags

        self.tag_lines: typing.Dict[str, TagLine] = {}

        self.main_layout = QVBoxLayout()

        self._tags_grid_layout = QGridLayout()
        self._tags_widget = QGroupBox()
        self._tags_widget.setTitle(title)
        self._tags_widget.setLayout(self._tags_grid_layout)

        self._tags_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.tags_sorted: typing.List[str] = []

        self.main_layout.addWidget(self._tags_widget)

        self.setLayout(self.main_layout)
        self.setMaximumHeight(200)

        self.is_hovered: bool = False

        self._lblNoTags = QLabel(text="no tags")
        self._tags_grid_layout.addWidget(self._lblNoTags, 0, 0)

    def _add_tag_line(self, tag: str, enabled: bool = True) -> TagLine:
        tag_widget = TagLine(tag, enabled)
        # tag_widget.tag_toggled.connect(self._state.toggle_filtering_tag)
        if len(self.tag_lines) == 0:
            self._lblNoTags.hide()
            self._tags_grid_layout.removeWidget(self._lblNoTags)
        return tag_widget

    # def _handle_assign_tag_global(self, tag: str):
    #     for photo in self.storage.images:
    #         photo.add_tag(tag)
    #
    # def _handle_delete_tag_global(self, tag: str):
    #     for photo in self.storage.images:
    #         photo.remove_tag(tag)
    #
    def _connect_tag_line_signals(self, tag_line: TagLine):
        tag_line.tag_toggled.connect(self._state.toggle_filtering_tag)

    def clear_tags(self):
        for tag in self.tag_lines.values():
            self._tags_grid_layout.removeWidget(tag)
            tag.deleteLater()
        self.tag_lines.clear()
        self.tags_sorted.clear()

    def populate(self):
        self.clear_tags()
        self.tags_sorted = list(sorted(self.storage.used_tags))
        if len(self.tags_sorted) == 0:
            self._tags_grid_layout.addWidget(self._lblNoTags, 0, 0)
            self._lblNoTags.show()
        else:
            self._lblNoTags.hide()
            self._tags_grid_layout.removeWidget(self._lblNoTags)
        for row, tag in enumerate(self.tags_sorted):
            if tag not in self.tag_lines:
                tag_widget = self._add_tag_line(tag, False)
                self._connect_tag_line_signals(tag_widget)
                self.tag_lines[tag] = tag_widget
                self._tags_grid_layout.addWidget(tag_widget, row, 0)

    def update_tag_states(self):
        for tag, tag_line in self.tag_lines.items():
            tag_line.blockSignals(True)
            tag_line._checkbox.setChecked(tag in self._state.active_tags_filter)
            tag_line.blockSignals(False)

    def leaveEvent(self, event:PySide2.QtCore.QEvent):
        self.is_hovered = False
        self.widget_left.emit()

    def enterEvent(self, event:PySide2.QtCore.QEvent):
        self.is_hovered = True

    def show(self):
        super(TagsWidget, self).show()
        self.adjustSize()


class PhotoTagsWidget(TagsWidget):
    def __init__(self, photo: Photo, state: State, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(state, parent=parent, f=f)
        self.photo = photo
        self.tags = photo.tags

        self.populate()

        lay = QHBoxLayout()
        self.lblNewTag = QLabel(text="New tag: ")
        self.txtNewTag = QLineEdit()
        self.txtNewTag.setPlaceholderText('enter a new tag and confirm with <Enter>')

        self.txtNewTag.returnPressed.connect(self._handle_confirm_new_tag)

        lay.addWidget(self.lblNewTag)
        lay.addWidget(self.txtNewTag)

        self.main_layout.addLayout(lay)

        state.storage.update_photo.connect(self.handle_photo_update)

    def _handle_confirm_new_tag(self):
        if len(self.txtNewTag.text()) == 0 or self.txtNewTag.text().isspace():
            return
        self.photo.add_tag(self.txtNewTag.text())
        self.txtNewTag.clear()

    def _add_tag_line(self, tag: str, enabled: bool = True) -> TagLine:
        tag_widget = super(PhotoTagsWidget, self)._add_tag_line(tag, enabled)
        # tag_widget.tag_toggled.connect(self.photo.toggle_tag)
        return tag_widget

    def handle_photo_update(self, image_name: str, ctx: UpdateContext, data: typing.Dict[str, typing.Any]):
        if image_name != self.photo.image_name:
            return
        if 'tags' not in data:
            return
        for tag in data['tags']['added']:
            if tag not in self.tag_lines:
                tag_widget = self._add_tag_line(tag)
                self._connect_tag_line_signals(tag_widget)
                self.tag_lines[tag] = tag_widget
                # self._enabled_tags_lay.addWidget(tag_widget)
                position = bisect.bisect(self.tags_sorted, tag)
                for i in range(position, len(self.tags_sorted)):
                    tag_to_move = self.tags_sorted[i]
                    tag_widget_to_move = self.tag_lines[tag_to_move]
                    self._tags_grid_layout.removeWidget(tag_widget_to_move)
                self.tags_sorted.insert(position, tag)
                for row in range(position, len(self.tags_sorted)):
                    tag_to_insert = self.tags_sorted[row]
                    tag_widget_to_insert = self.tag_lines[tag_to_insert]
                    self._tags_grid_layout.addWidget(tag_widget_to_insert, row, 0)
            else:
                self.tag_lines[tag].blockSignals(True)
                self.tag_lines[tag]._checkbox.setChecked(True)
                self.tag_lines[tag].blockSignals(False)

    def _connect_tag_line_signals(self, tag_line: TagLine):
        tag_line.tag_toggled.connect(self.photo.toggle_tag)

    def populate(self):
        super().populate()
        for tag in self.photo.tags:
            tag_widget = self.tag_lines[tag]
            tag_widget.blockSignals(True)
            tag_widget._checkbox.setChecked(True)
            tag_widget.blockSignals(False)

