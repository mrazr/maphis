import random
import typing
from typing import Literal

import cv2 as cv
import numpy as np
from PySide2.QtCore import Signal, Slot, QModelIndex, QSortFilterProxyModel
from PySide2.QtGui import QImage, QPixmap, Qt
from PySide2.QtWidgets import QWidget, QLabel, QCompleter, QLineEdit

from arthropod_describer.common.photo import LabelType
from arthropod_describer.common.tool import qimage2ndarray
from arthropod_describer.common.colormap import Colormap
from arthropod_describer.label_editor.ui_colormap_widget import Ui_ColormapWidget


class ColormapWidget(QWidget):
    primary_label_changed = Signal(int)
    secondary_label_changed = Signal(int)
    label_search_finished = Signal()
    label_opacity_changed = Signal(int)

    def __init__(self, parent: typing.Optional[QWidget] = None):
        QWidget.__init__(self, parent=parent)

        self.ui = Ui_ColormapWidget()
        self.ui.setupUi(self)

        self.colormaps: typing.List[Colormap] = []
        self.current_colormap: typing.Optional[Colormap] = None

        self.label_filter = QSortFilterProxyModel()
        self.label_filter.setFilterRole(Qt.UserRole + 1)

        self.left_label: int = -1
        self.left_label_pixmap = QPixmap(48, 48)

        self.right_label: int = -1
        self.right_label_pixmap = QPixmap(48, 48)

        self.ui.colormapComboBox.currentIndexChanged.connect(self._handle_colormap_changed)
        self.ui.leftComboBox.currentIndexChanged.connect(self._handle_left_label_changed)
        self.ui.rightComboBox.currentIndexChanged.connect(self._handle_right_label_changed)
        self.ui.btnSwapLabels.clicked.connect(self._handle_swap_labels_clicked)
        self.ui.opacitySlider.valueChanged.connect(self.label_opacity_changed.emit)

       # self.colormap_chooser = QWidget()
       # self.colormap_chooser_layout: QHBoxLayout = QHBoxLayout()

       # self.label: QLabel = QLabel(text="Current colormap")
       # self.combobox: QComboBox = QComboBox()

       # self.colormap_chooser_layout.addWidget(self.label)
       # self.colormap_chooser_layout.addWidget(self.combobox)

        self.mouse_img = QImage()
        self.mouse_np = np.array([])
        self.mouse_left_coords: typing.Tuple[np.ndarray, np.ndarray] = None
        self.mouse_right_coords: typing.Tuple[np.ndarray, np.ndarray] = None
        self.mouse_label: QLabel = QLabel()

        self.mouse_label.setAlignment(Qt.AlignHCenter)

        self._build_label_pick_widget()

        self.layout().addWidget(self.mouse_label)

       # self.colormap_chooser.setLayout(self.colormap_chooser_layout)

       # self.widget_layout: QVBoxLayout = QVBoxLayout()

       # self.widget_layout.addWidget(self.colormap_chooser)
       # self.widget_layout.addWidget(self.mouse_label)

       # self.setLayout(self.widget_layout)

        self.label_search_bar = QLineEdit()
        #self.colormap_list_view = QListView()

        self.completer = QCompleter()
        self.completer.activated[QModelIndex].connect(self._handle_label_search_confirmed)
        #self.completer.setPopup(self.colormap_list_view)

        #self.completer2 = QCompleter()

        self.label_search_bar.setCompleter(self.completer)

    def _build_label_pick_widget(self):
        self.mouse_img = QImage(':/images/mouse.png')
        self.mouse_np = qimage2ndarray(self.mouse_img)
        self.mouse_np = cv.resize(self.mouse_np, (0, 0), fx=0.15, fy=0.15, interpolation=cv.INTER_NEAREST)

        self.mouse_left_coords = np.nonzero(self.mouse_np == 127)
        self.mouse_right_coords = np.nonzero(self.mouse_np == 255)

        black = np.nonzero(self.mouse_np == 42)

        self.mouse_np = np.dstack((self.mouse_np, self.mouse_np, self.mouse_np, 255 * np.zeros_like(self.mouse_np))).astype(np.uint8)

        # BGRA, I guess
        self.mouse_np[black] = [0, 0, 0, 255]
        self.mouse_np[self.mouse_left_coords] = [0, 0, 125, 255]
        self.mouse_np[self.mouse_right_coords] = [0, 125, 0, 255]

        self.mouse_img = QImage(self.mouse_np.data, self.mouse_np.shape[1], self.mouse_np.shape[0],
                                4 * self.mouse_np.shape[1], QImage.Format_ARGB32)

        self.mouse_label.setPixmap(QPixmap.fromImage(self.mouse_img, Qt.AutoColor))

    def _paint_label_indicator(self, side: str):
        if side == 'left':
            label = self.left_label
            coords = self.mouse_left_coords
        else:
            label = self.right_label
            coords = self.mouse_right_coords

        color = self.current_colormap.colormap[label]
        self.mouse_np[coords] = color[::-1] + (255,) # `color` is in RGB, we need `BGR`

        self.mouse_img = QImage(self.mouse_np.data, self.mouse_np.shape[1], self.mouse_np.shape[0],
                                4 * self.mouse_np.shape[1], QImage.Format_ARGB32)

        self.mouse_label.setPixmap(QPixmap.fromImage(self.mouse_img, Qt.AutoColor))

    def _handle_colormap_changed(self, current_idx: int):
        self.current_colormap = self.colormaps[current_idx]
        self.label_filter.setSourceModel(self.current_colormap)

        self.left_label = self.current_colormap.labels[0]
        self.right_label = self.current_colormap.labels[0]

        #self.set_label_by_idx(random.randint(0, self.current_colormap.color_count), 'left')

        #self.ui.leftComboBox.setModel(self.current_colormap)
        #self.ui.rightComboBox.setModel(self.current_colormap)

        self.ui.leftComboBox.setModel(self.label_filter)
        self.ui.rightComboBox.setModel(self.label_filter)

        self.completer.setModel(self.label_filter)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        #self.completer.highlighted.connect(lambda _: print("highlight"))
        #completer.setCompletionMode(QCompleter.InlineCompletion)

        tpl = self.label_search_bar.topLevelWidget()
        self.label_search_bar.completer().popup().setParent(tpl, Qt.Popup)

        self.set_label_by_idx(1, 'left')
        self.set_label_by_idx(random.randint(0, self.current_colormap.color_count), 'right')

        self.ui.leftComboBox.setCurrentIndex(1)
        self.ui.rightComboBox.setCurrentIndex(1)

        self.primary_label_changed.emit(self.colormaps[current_idx].labels[1])
        self.secondary_label_changed.emit(self.colormaps[current_idx].labels[1])

    def set_label_by_idx(self, idx: int, side: typing.Union[Literal['left'], Literal['right']]):
        if side == 'left':
            self.ui.leftComboBox.setCurrentIndex(idx)
        else:
            self.ui.rightComboBox.setCurrentIndex(idx)

    def register_colormap(self, colormap: Colormap):
        # TODO handle not inserting duplicates
        self.colormaps.append(colormap)
        self.ui.colormapComboBox.addItem(colormap.name)

    def set_colormap(self, idx: int):
        self.ui.colormapComboBox.setCurrentIndex(idx)

    def _handle_left_label_changed(self, idx: int):
        index = self._correct_index(idx)
        self.change_primary_label(self.current_colormap.labels[index.row()])

    def _handle_right_label_changed(self, idx: int):
        index = self._correct_index(idx)
        self.change_secondary_label(self.current_colormap.labels[index.row()])

    def _handle_swap_labels_clicked(self):
        left_idx = self.ui.rightComboBox.currentIndex()
        right_idx = self.ui.leftComboBox.currentIndex()

        self.set_label_by_idx(left_idx, 'left')
        self.set_label_by_idx(right_idx, 'right')

    def change_primary_label(self, label: int):
        self.left_label = label
        self._paint_label_indicator('left')
        self.primary_label_changed.emit(self.left_label)

    def change_secondary_label(self, label: int):
        self.right_label = label
        self._paint_label_indicator('right')
        self.secondary_label_changed.emit(self.right_label)

    @Slot(QModelIndex)
    def _handle_label_search_confirmed(self, idx: QModelIndex):
        #true_index = self._correct_index(idx)
        label = self.completer.completionModel().data(idx, Qt.UserRole)
        label_index = self.current_colormap.labels.index(label)
        source_index = self.current_colormap.index(label_index, 0)
        target_index = self.label_filter.mapFromSource(source_index)
        self.set_label_by_idx(target_index.row(), 'left')
        self.label_search_bar.clearFocus()
        self.label_search_finished.emit()

    def handle_label_type_changed(self, label_type: LabelType):
        if label_type == LabelType.REGIONS:
            self.label_filter.setFilterFixedString('regions')
        else:
            self.label_filter.setFilterFixedString('mask')

    def _correct_index(self, index: typing.Union[QModelIndex, int]):
        if isinstance(index, QModelIndex):
            return self.label_filter.mapToSource(index)
        return self.label_filter.mapToSource(self.label_filter.index(index, 0))
