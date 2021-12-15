from typing import Optional

from PySide2.QtCore import Signal, QObject
from PySide2.QtGui import Qt
from PySide2.QtWidgets import QWidget, QGraphicsScene

from custom_graphics_view import CustomGraphicsView
from canvas_widget import CanvasWidget
from view.ui_mask_edit_view import Ui_MaskEditor
from model.photo import Photo, MaskType


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

        self._scene = QGraphicsScene()

        self.photo_view = CustomGraphicsView()
        self.ui.center.addWidget(self.photo_view)
        self.photo_view.setScene(self._scene)

        self.photo_view.setInteractive(True)

        self.canvas = CanvasWidget()
        self._scene.addItem(self.canvas)
        self.canvas.initialize()

        self.current_photo: Optional[Photo] = None

    def set_photo(self, photo: Photo):
        self.current_photo = photo
        self.canvas.set_photo(self.current_photo)
        self.canvas.left_press.connect(lambda: print("hello"))
        self._scene.setSceneRect(self.canvas.sceneBoundingRect())
        self._scene.update()
        self.photo_view.fitInView(self.canvas, Qt.KeepAspectRatio)

    def handle_bug_mask_checked(self, checked: bool):
        print(f"bug {checked}")
        self.canvas.set_mask_shown(MaskType.BUG_MASK, checked)

    def handle_segments_mask_checked(self, checked: bool):
        print(f"segments {checked}")
        self.canvas.set_mask_shown(MaskType.SEGMENTS_MASK, checked)

    def handle_reflection_mask_checked(self, checked: bool):
        print(f"reflections {checked}")
        self.canvas.set_mask_shown(MaskType.REFLECTION_MASK, checked)


