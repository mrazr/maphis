import typing

import PySide2
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QWidget, QLineEdit, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout

from arthropod_describer.common.state import State
from arthropod_describer.common.utils import is_cursor_inside
from arthropod_describer.tags_widget import TagsWidget


class ActiveTagsList(QLineEdit):
    hovered = Signal()

    def __init__(self):
        QLineEdit.__init__(self, None)
        self._active_tags: typing.List[str] = []
        self.setReadOnly(True)
        self.setPlaceholderText('no filtering active')

    def enterEvent(self, event:PySide2.QtCore.QEvent):
        self.hovered.emit()
        super().enterEvent(event)


class TagFilterWidget(QWidget):
    def __init__(self, state: State, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)

        self._state = state
        self._container = QVBoxLayout()
        self._main_layout = QHBoxLayout()

        self._label = QLabel(text='Tag filter:')
        self._main_layout.addWidget(self._label)

        self._tags_list = ActiveTagsList()
        self._tags_list.hovered.connect(self.show_tags_panel_popup)
        self._tags_list.setReadOnly(True)
        self._main_layout.addWidget(self._tags_list)

        self._btn_clear = QPushButton(text='Clear')
        self._btn_clear.setToolTip("Clear the current tag filter")
        self._btn_clear.clicked.connect(self._state.clear_tag_filter)
        self._main_layout.addWidget(self._btn_clear)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._container.addLayout(self._main_layout)

        self._lblPhotoCount = QLabel("")
        self._container.addWidget(self._lblPhotoCount)

        self.setLayout(self._container)

        self.tags_widget = TagsWidget(self._state, parent=self, title="Tags to filter")
        self.tags_widget.hide()
        self.tags_widget.widget_left.connect(lambda: self.tags_widget.hide())
        self._state.tags_filter_changed.connect(self.handle_active_tags_changed)
        # self._state.tags_filter_changed.connect()

    def initialize(self):
        self.tags_widget.storage = self._state.storage
        self._state.storage.storage_update.connect(self.handle_storage_update)
        self.tags_widget.populate()
        self.handle_active_tags_changed(self._state.active_tags_filter)

    def handle_active_tags_changed(self, active_tags: typing.List[str]):
        self.tags_widget.update_tag_states()
        self._tags_list.setText(', '.join(active_tags))
        self._tags_list.setToolTip(self._tags_list.text())
        self._update_photo_count_message()

    def handle_storage_update(self, _: typing.Dict[str, typing.Any]):
        self.tags_widget.populate()
        self.tags_widget.update_tag_states()
        self._update_photo_count_message()

    def _update_photo_count_message(self):
        hidden_count = self._state.hidden_photos_count
        shown_count = self._state.storage.image_count - hidden_count
        self._lblPhotoCount.setText(f'Showing {shown_count} photo{"s" if shown_count != 1 else ""}{"" if hidden_count == 0 else f" ({hidden_count} hidden)"}.')

    def handle_tags_filter_changed(self, _: typing.List[str]):
        self._tags_list.setText(', '.join(self._state.active_tags_filter))

    def show_tags_panel_popup(self):
        if not self.isEnabled():
            return
        pos = self._tags_list.mapToGlobal(self._tags_list.rect().topRight())
        self.tags_widget.move(pos)
        self.tags_widget.show()

    def enterEvent(self, event:PySide2.QtCore.QEvent):
        super(TagFilterWidget, self).enterEvent(event)

    def leaveEvent(self, event:PySide2.QtCore.QEvent):
        super(TagFilterWidget, self).leaveEvent(event)
        # cursor_pos = QCursor.pos()
        # tag_list_rect = self.tags_widget.rect().translated(self.tags_widget.pos())
        # if tag_list_rect.contains(cursor_pos):
        #     return
        if is_cursor_inside(self.tags_widget):
            return
        self.tags_widget.close()
