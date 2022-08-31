import importlib.resources
import typing

import PySide2
from PySide2.QtCore import Signal
from PySide2.QtGui import QIcon, Qt, QPixmap, QImage
from PySide2.QtWidgets import QWidget

from arthropod_describer.common.photo import Photo
from arthropod_describer.ui_thumbnail_gui import Ui_ThumbnailGUI


class ThumbGUI(QWidget):
    resize_icon: typing.Optional[QIcon] = None
    ccw_icon: typing.Optional[QIcon] = None
    cw_icon: typing.Optional[QIcon] = None
    resolution_icon: typing.Optional[QIcon] = None
    delete_icon: typing.Optional[QIcon] = None

    resize_requested = Signal(Photo)
    rotate_requested = Signal([Photo, bool])
    resolution_setting_requested = Signal(Photo)
    save_photo = Signal(Photo)
    delete_photo_requested = Signal(Photo)

    def __init__(self, photo: Photo, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)
        self.ui = Ui_ThumbnailGUI()
        self.ui.setupUi(self)

        self.setMaximumWidth(248)
        self.setMinimumWidth(248)
        self.setMinimumHeight(128)
        self.setMaximumHeight(128)

        self.photo = photo

        if self.resize_icon is None:
            # Placeholder icons, replace
            with importlib.resources.path('resources', 'resize.png') as path:
                self.resize_icon = QIcon(str(path))
            with importlib.resources.path('resources', 'rotate.png') as path:
                self.cw_icon = QIcon(str(path))
            with importlib.resources.path('resources', 'rotate.png') as path:
                img = QImage(str(path))
                self.ccw_icon = QIcon(QPixmap.fromImage(img.mirrored(True, False)))
            with importlib.resources.path('resources', 'ruler.png') as path:
                self.resolution_icon = QIcon(str(path))
            with importlib.resources.path('resources', 'floppy-disk.png') as path:
                self.save_icon = QIcon(str(path))
            with importlib.resources.path('resources', 'delete.png') as path:
                self.delete_icon = QIcon(str(path))

        self.ui.tbtnResize.setIcon(self.resize_icon)
        self.ui.tbtnRotateCW.setIcon(self.cw_icon)
        self.ui.tbtnRotateCCW.setIcon(self.ccw_icon)
        self.ui.tbtnSetResolution.setIcon(self.resolution_icon)
        self.ui.tbtnSave.setIcon(self.save_icon)
        self.ui.tbtnDelete.setIcon(self.delete_icon)

        self.ui.tbtnResize.clicked.connect(handler(self.resize_requested, photo))
        self.ui.tbtnRotateCW.clicked.connect(handler(self.rotate_requested, photo, True))
        self.ui.tbtnRotateCCW.clicked.connect(handler(self.rotate_requested, photo, False))
        self.ui.tbtnSetResolution.clicked.connect(handler(self.resolution_setting_requested, photo))
        self.ui.tbtnSave.clicked.connect(self._save)
        self.ui.tbtnSave.setVisible(self.photo.has_unsaved_changes)
        self.ui.tbtnDelete.clicked.connect(handler(self.delete_photo_requested, photo))

        self.ui.lblImgSize.setText(f'{photo.image_size[0]} \u00d7 {photo.image_size[1]}')
        if (scale := photo.image_scale) is not None and scale.value > 0:
            self.ui.lblResolution.setText(f'{scale}')
        else:
            self.ui.lblResolution.setText('1 mm = ? px')

        approval = photo.approved['Labels']
        if approval is None:
            self.ui.lblApprovalInfo.setToolTip('Nothing approved yet')
        else:
            self.ui.lblApprovalInfo.setToolTip(f'Approved up to {approval}')

        self.setMouseTracking(True)

    def _save(self):
        self.save_photo.emit(self.photo)
        self.ui.tbtnSave.setVisible(False)


def handler(signal: Signal, *args):
    def emit():
        signal.emit(*args)
    return emit