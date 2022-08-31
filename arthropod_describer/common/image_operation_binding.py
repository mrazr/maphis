import typing

import PySide2
from PySide2.QtCore import QObject, Signal, Qt
from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QDialogButtonBox, \
    QDialog, QVBoxLayout

from arthropod_describer.common.photo import Photo


class ResizeWidget(QWidget):
    invalid_input = Signal(bool)
    valid_input = Signal(bool)

    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)
        layout = QGridLayout()

        layout.addWidget(QLabel("Width"), 0, 0)
        self.spboxWidth = QSpinBox()
        layout.addWidget(self.spboxWidth, 0, 1)

        layout.addWidget(QLabel("Height"), 1, 0)
        self.spboxHeight = QSpinBox()
        layout.addWidget(self.spboxHeight, 1, 1)

        layout.addWidget(QLabel("Resize factor"), 2, 0)
        self.spboxFactor = QDoubleSpinBox()
        self.spboxFactor.setSingleStep(0.25)
        self.spboxFactor.setDecimals(4)
        self.spboxFactor.setMinimum(0.001)
        self.spboxFactor.setMaximum(1.0)
        layout.addWidget(self.spboxFactor, 2, 1)

        self.setLayout(layout)

        self._aspect: float = 0.0
        self._size: typing.Tuple[int, int] = (0, 0)

        self.spboxWidth.valueChanged.connect(self._update_height)
        self.spboxHeight.valueChanged.connect(self._update_width)
        self.spboxFactor.valueChanged.connect(self._update_width_height)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box, 3, 1)

    def set_size(self, size: typing.Tuple[int, int], factor: float = 1.0, max_factor: float = 1.0):
        self._size = size
        self._aspect = size[0] / size[1]
        self.spboxWidth.setMaximum(round(size[0] * max_factor))
        self.spboxWidth.setValue(round(size[0] * factor))

        self.spboxHeight.setMaximum(round(size[1] * max_factor))
        self.spboxHeight.setValue(round(size[1] * factor))

        self.spboxFactor.blockSignals(True)
        self.spboxFactor.setMaximum(max_factor)
        self.spboxFactor.setValue(min(factor, max_factor))
        self.spboxFactor.blockSignals(False)

    def _update_height(self, _):
        self.spboxHeight.blockSignals(True)
        if self.spboxWidth.value() != 0:
            self.spboxHeight.setValue(int(round(self.spboxWidth.value() / self._aspect)))
            self._update_factor()
        else:
            self.invalid_input.emit(True)
        self.spboxHeight.blockSignals(False)
        self._validate_input()

    def _update_width(self, _):
        self.spboxWidth.blockSignals(True)
        if self.spboxHeight.value() != 0:
            val = int(round(self.spboxHeight.value() * self._aspect))
            self.spboxWidth.setValue(val)
            self._update_factor()
        else:
            self.invalid_input.emit(True)
        self.spboxWidth.blockSignals(False)
        self._validate_input()

    def _update_width_height(self, _):
        if self.spboxFactor.value() == 0.0:
            self.invalid_input.emit(True)
            return
        self.spboxWidth.blockSignals(True)
        self.spboxWidth.setValue(int(round(self._size[0] * self.spboxFactor.value())))
        self.spboxWidth.blockSignals(False)

        self.spboxHeight.blockSignals(True)
        self.spboxHeight.setValue(int(round(self._size[1] * self.spboxFactor.value())))
        self.spboxHeight.blockSignals(False)
        self._validate_input()

    def _update_factor(self):
        self.spboxFactor.blockSignals(True)
        self.spboxFactor.setValue(self.spboxWidth.value() / self._size[0])
        self.spboxFactor.blockSignals(False)
        self._validate_input()

    def _validate_input(self):
        if self.spboxWidth.value() == 0 or self.spboxHeight.value() == 0:
            #self.invalid_input.emit(True)
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        else:
            #self.valid_input.emit(True)
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    def set_photo(self, photo: Photo):
        self.set_size(photo.image_size)


class ImageOperation(QObject):
    photo_resized = Signal(Photo)
    photo_rotated = Signal([Photo, bool])
    photo_resolution_changed = Signal(Photo)
    operation_running = Signal(Photo)
    operation_finished = Signal(Photo)

    def __init__(self, widg_parent: typing.Optional[QWidget], parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)
        self.photo: typing.Optional[Photo] = None
        self.widget_parent = widg_parent
        self.current_widget: typing.Optional[QWidget] = None

    def init(self, photo: Photo):
        self.photo = photo
        if self.current_widget is not None:
            self.current_widget.hide()
            self.current_widget.deleteLater()
            self.current_widget = None

    def rotate(self, clockwise: bool):
        self.photo.rotate(not clockwise)
        self.photo_rotated.emit(self.photo, clockwise)

    def resize(self):
        resize_widg = ResizeWidget(parent=self.widget_parent)
        resize_widg.set_photo(self.photo)
        diag = QDialog(parent=self.widget_parent)
        diag.setWindowTitle(f'Resizing: {self.photo.image_name}')
        diag.setWindowModality(Qt.WindowModal)
        diag.setLayout(QVBoxLayout())
        diag.layout().addWidget(resize_widg)

        resize_widg.button_box.button(QDialogButtonBox.Ok).clicked.connect(diag.accept)
        resize_widg.button_box.button(QDialogButtonBox.Cancel).clicked.connect(diag.reject)
        self.operation_running.emit(self.photo)
        if diag.exec_() == QDialog.Accepted:
            self.photo.resize(resize_widg.spboxFactor.value())
            self.photo_resized.emit(self.photo)
        self.operation_finished.emit(self.photo)