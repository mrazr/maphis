import typing

import PySide2
from PySide2.QtWidgets import QWidget

from arthropod_describer.ui_image_controls import Ui_ImageControls


class ImageControls(QWidget):
    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = None):
        super().__init__(parent, f)

        self.ui = Ui_ImageControls()
        self.ui.setupUi(self)
