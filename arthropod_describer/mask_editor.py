from typing import Optional

from PySide2.QtCore import QPointF, Qt, QMargins, Signal, QObject
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QWidget, QGraphicsScene, QGraphicsPixmapItem

from view.ui_mask_edit_view import Ui_MaskEditor
from model.photo import Photo, LocalPhoto


class MaskEditor(QObject):
    signal_next_photo = Signal()
    signal_prev_photo = Signal()

    def __init__(self):
        QObject.__init__(self)
        self.widget = QWidget()
        self.ui = Ui_MaskEditor()
        self.ui.setupUi(self.widget)

        self.ui.tbtnBugMask.toggled.connect(self.handle_bug_mask_checked)
        self.ui.tbtnSegmentsMask.toggled.connect(self.handle_segments_mask_checked)
        self.ui.tbtnReflectionMask.toggled.connect(self.handle_reflection_mask_checked)
        self.ui.btnNext.clicked.connect(lambda: self.signal_next_photo.emit())
        self.ui.btnPrevious.clicked.connect(lambda: self.signal_prev_photo.emit())

        self.photo_view = self.ui.maskEditor
        self._scene = QGraphicsScene()
        self.photo_view.setScene(self._scene)

        self.current_photo: Optional[Photo] = None
        self._pixmap = QPixmap()
        self._scene_pixmap = self._scene.addPixmap(self._pixmap)

    def set_photo(self, photo: Photo):
        self.current_photo = photo
        self._pixmap.convertFromImage(photo.image, Qt.ColorOnly)
        self._scene_pixmap.setPos(QPointF(0.0, 0.0))
        self._scene_pixmap.setPixmap(self._pixmap)
        self._scene_pixmap.setTransformOriginPoint(self._pixmap.rect().center())
        print(f'before trans {self._scene_pixmap.sceneBoundingRect()}')
        rect1 = self._pixmap.rect()
        if self._pixmap.height() > self._pixmap.width():
            self._scene_pixmap.setRotation(90.0)
            rect1 = rect1.transposed()
            print(f'after 90 trans {self._scene_pixmap.sceneBoundingRect()}')
        else:
            self._scene_pixmap.setRotation(0.0)
        self._scene_pixmap.update()
        print(self._scene_pixmap.boundingRect().transposed())
        self._scene.setSceneRect(self._scene_pixmap.sceneBoundingRect())
        self._scene.update()
        self.photo_view.fitInView(self._scene_pixmap)

    def handle_bug_mask_checked(self, checked: bool):
        print(f"bug {checked}")

    def handle_segments_mask_checked(self, checked: bool):
        print(f"segments {checked}")

    def handle_reflection_mask_checked(self, checked: bool):
        print(f"reflections {checked}")