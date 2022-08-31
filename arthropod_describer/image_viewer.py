import typing
from enum import IntEnum
from typing import List
import importlib.resources

import PySide2
from PySide2.QtCore import Qt, QRegExp, Signal
from PySide2.QtGui import QRegExpValidator, QImage, QIcon, QPixmap
from PySide2.QtWidgets import QWidget, QGraphicsScene, QVBoxLayout, QSizePolicy

from arthropod_describer.common.layer import Layer, MouseEventLayer
from arthropod_describer.common.photo import Photo, UpdateContext
from arthropod_describer.common.state import State
from arthropod_describer.common.storage import Storage
from arthropod_describer.common.tool import Tool
from arthropod_describer.custom_graphics_view import CustomGraphicsView
from arthropod_describer.ui_image_viewer import Ui_ImageViewer


class ViewerMode(IntEnum):
    OnlyPhoto = 0,
    Combined = 1


class ImageViewer(QWidget):
    first_photo_requested = Signal()
    prev_photo_requested = Signal()
    next_photo_requested = Signal()
    last_photo_requested = Signal()
    rotate_cw_requested = Signal()
    rotate_ccw_requested = Signal()
    photo_switched = Signal(Photo)

    def __init__(self, state: State, mode: ViewerMode = ViewerMode.Combined, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)

        self.ui = Ui_ImageViewer()
        self.ui.setupUi(self)

        self.ui.tbtnFirst.clicked.connect(self.first_photo_requested.emit)
        self.ui.tbtnPrev.clicked.connect(self.prev_photo_requested.emit)
        self.ui.tbtnNext.clicked.connect(self.next_photo_requested.emit)
        self.ui.tbtnLast.clicked.connect(self.last_photo_requested.emit)

        self.ui.tbtnRotateCW.hide()
        self.ui.tbtnRotateCCW.hide()
        self.ui.tbtnRotateCW.clicked.connect(self.rotate_cw_requested.emit)
        self.ui.tbtnRotateCCW.clicked.connect(self.rotate_ccw_requested.emit)
        with importlib.resources.path('resources', 'rotate.png') as path:
            img = QImage(str(path))
            self.ui.tbtnRotateCW.setIcon(QIcon(QPixmap.fromImage(img)))
            self.ui.tbtnRotateCCW.setIcon(QIcon(QPixmap.fromImage(img.mirrored(True, False))))

        self.state: State = state

        self.graphics_scene: QGraphicsScene = QGraphicsScene()

        self.mode: ViewerMode = mode

        self.mouse_event_layer = MouseEventLayer(self.state)
        self.mouse_event_layer.initialize()
        self.graphics_scene.addItem(self.mouse_event_layer)
        self.mouse_event_layer.setZValue(1000)
        self.mouse_event_layer.setPos(0, 0)

        self.layers: List[Layer] = [self.mouse_event_layer]

        self._setup_zoom_combo_box()
        self._setup_photo_view()

        # TODO Karel: when the rotate icons are ready in arthropod_describer/resources, uncomment and modify this block to load them and assign them to the rotation buttons
        #with importlib.resources.path('arthropod_describer.resources', 'rotate_cw.png') as path:
        #    img = QImage(str(path))
        #    self.ui.tbtnRotateCW.setIcon(QIcon(QPixmap.fromImage(img)))
        #    self.ui.tbtnRotateCW.setIconSize(......)

        with importlib.resources.path('resources', 'next.png') as path:
            img = QImage(str(path))
            self.ui.tbtnPrev.setIcon(QIcon(QPixmap.fromImage(img.mirrored(True, False))))
            self.ui.tbtnNext.setIcon(QIcon(QPixmap.fromImage(img)))
            #self.ui.tbtnPrev.setIconSize(......)
            #self.ui.tbtnNext.setIconSize(......)

        with importlib.resources.path('resources', 'last.png') as path:
            img = QImage(str(path))
            self.ui.tbtnFirst.setIcon(QIcon(QPixmap.fromImage(img.mirrored(True, False))))
            self.ui.tbtnLast.setIcon(QIcon(QPixmap.fromImage(img)))
            #self.ui.tbtnFirst.setIconSize(......)
            #self.ui.tbtnLast.setIconSize(......)

        self.storage: typing.Optional[Storage] = None

    def _setup_photo_view(self):
        self.photo_view = CustomGraphicsView(self.state)
        self.ui.viewFrame.setLayout(QVBoxLayout())
        self.ui.viewFrame.layout().addWidget(self.photo_view)
        self.photo_view.setScene(self.graphics_scene)
        self.photo_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.photo_view.setInteractive(True)
        self.photo_view.view_changed.connect(self._handle_view_changed)
        # TODO make space, tab into proper shortcuts
        #self.photo_view.space_pressed.connect(self._toggle_approval_of_mask)
        #self.photo_view.tab_pressed.connect(self._pick_next_label)

    def _setup_zoom_combo_box(self):
        self.ui.cbxZoom.currentTextChanged.connect(self.handle_zoom_selected)
        fit_photo_string = self.ui.cbxZoom.itemText(0)
        fit_specimen_string = self.ui.cbxZoom.itemText(1)
        zoom_validation_regexp = '^(\d+%?)|' + fit_photo_string + '|' + fit_specimen_string + '$'
        self.ui.cbxZoom.setValidator(QRegExpValidator(QRegExp(zoom_validation_regexp), self.ui.cbxZoom))

    def add_layer(self, layer: Layer):
        self.layers.pop()
        self.layers.append(layer)
        self.graphics_scene.addItem(layer)
        layer.initialize()
        layer.setPos(0, 0)
        for i in range(len(self.layers)):
            self.layers[i].setZValue(1)
        self.layers.append(self.mouse_event_layer)
        self.mouse_event_layer.layers.append(layer)

    def _handle_view_changed(self):
        # Update the zoom combo box if the zoom got changed during the view change. Temporarily block signals to prevent infinite loop.
        self.ui.cbxZoom.blockSignals(True)
        #print('_handle_view_changed')
        int_zoom_value = int(100 * self.photo_view.transform().m11()) # Calculate the actual zoom in %.
        self.ui.cbxZoom.setCurrentText(f'{int_zoom_value}%')
        self.ui.cbxZoom.blockSignals(False)

        # TODO: Wouldn't it be better to store a reference to the CustomGraphicsView in State, and where needed,
        #       just extract the transform from there? That would give no opportunity for inconsistencies.
        #       Otherwise, all parts of the code that affect the transform must keep State updated like this,
        #       e.g. by calling _handle_view_changed().
        #       .
        #       If ImageViewer._handle_view_changed() is always connected to CustomGraphicsView.view_changed
        #       (seems to be), then it isn't necessary to explicitly do `self.state.current_view_transform = m`
        #       at the end of CustomGraphicsView.wheelEvent() -- has been removed from there.
        self.state.current_view_transform = self.photo_view.transform()

    def handle_zoom_selected(self, value):
        zoom_digits = ''.join(c for c in value if c.isdigit())
        if len(zoom_digits) > 0:
            int_zoom_value = int(zoom_digits)
            # Change the current zoom to int_zoom_value.
            m = self.photo_view.transform()
            m.setMatrix(int_zoom_value / 100,              m.m12(), m.m13(),
                        m.m21(), int_zoom_value / 100, m.m23(),
                        m.m31(),              m.m32(), m.m33())
            self.photo_view.setTransform(m, False)
            # Make sure not to zoom out too much.
            srect = self.photo_view.sceneRect()
            rrect = self.photo_view.mapToScene(self.photo_view.rect()).boundingRect()
            if rrect.height() > srect.height() and rrect.width() > srect.width():
                self.photo_view.fitInView(srect, Qt.KeepAspectRatio)

            self.photo_view.scene().update()
            print(f'zoom: changed via combo box to "{value}", int_zoom_value: {int_zoom_value}')
            # Call "self.photo_view.view_changed.emit()" or "self._handle_view_changed()" to update the combo box text in case zooming out too much was prevented, i.e. different value than what was entered got used. (Careful about infinite loops.)
            self.photo_view.view_changed.emit()
        else:
            fit_photo_string = self.ui.cbxZoom.itemText(0)
            fit_specimen_string = self.ui.cbxZoom.itemText(1)
            if (value == fit_specimen_string) and (self.state.current_photo.bug_bbox is None):  # TODO: Is this bug_bbox set properly? Currently, it seems to be always None, and its source code is marked with "remove this" todo.
                print('zoom: no specimen found, will fit whole photo instead')
                self.ui.cbxZoom.setCurrentIndex(0)
                return

            # Process the "Fit photo" (self.ui.cbxZoom.itemText(0)) option
            if value == fit_photo_string:
                self.show_whole_image()
                print(f'zoom: changed via combo box to "{fit_photo_string}"')

            # Process the "Fit specimen" (self.ui.cbxZoom.itemText(1)) option
            if value == fit_specimen_string:
                self.zoom_on_bug()  # TODO: Implement zoom_on_bug() once a bounding box is available.
                print(f'zoom: changed via combo box to "{fit_specimen_string}"')

            # Trigger the update of the zoom combo box (transforms "Fit photo" and "Fit specimen" to percentages)
            self._handle_view_changed()

    def set_photo(self, photo: typing.Optional[Photo], reset_view: bool=False, reset_tool: bool = True):
        for layer in self.layers:
            layer.set_photo(photo, reset_tool=reset_tool)
        if reset_view:
            self.show_whole_image()
        # This will trigger updating the zoom combo box.
        self._handle_view_changed()
        if photo is None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            idx = self.state.storage.image_names.index(photo.image_name)
            # TODO in case of a filtered list of photos, the line below does not work with correct count of photos
            self.enable_navigation_buttons(idx)
        self.photo_switched.emit(photo)

    def set_tool(self, tool: typing.Optional[Tool], reset_current: bool = True):
        self.state.current_tool = tool
        for layer in self.layers:
            layer.set_tool(tool, reset_current)

    #def visualize_label_level(self, level: int):
    #    self.state.current_label_level = level
    #    self.canvas.label_view.switch_label_level(level)

    def show_whole_image(self):
        if len(self.layers) == 0:
            return
        self.graphics_scene.setSceneRect(self.layers[0].sceneBoundingRect())
        self.graphics_scene.update()
        # Temporarily turn off the scrollbars so that their size doesn't interfere with fitInView() calculations.
        self.photo_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.photo_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.photo_view.fitInView(self.layers[0], Qt.KeepAspectRatio)
        self.photo_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.photo_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def enable_first_button(self, enable: bool = True):
        self.ui.tbtnFirst.setEnabled(enable)

    def enable_prev_button(self, enable: bool = True):
        self.ui.tbtnPrev.setEnabled(enable)

    def enable_next_button(self, enable: bool = True):
        self.ui.tbtnNext.setEnabled(enable)

    def enable_last_button(self, enable: bool = True):
        self.ui.tbtnLast.setEnabled(enable)

    def enable_navigation_buttons(self, idx: int, current_photo_count: int = -1):
        max_index = self.state.storage.image_count - 1 if current_photo_count < 0 else current_photo_count - 1
        self.enable_first_button(idx > 0)
        self.enable_prev_button(idx > 0)
        self.enable_next_button(idx < max_index)
        self.enable_last_button(idx < max_index)

    def _handle_update_photo(self, img_name: str, ctx: UpdateContext, data: typing.Dict[str, typing.Any]):
        if ctx == UpdateContext.Measurements:
            return
        print(f'reacting to photo update {ctx} for {img_name}')
        if self.state.current_photo is not None and self.state.current_photo.image_name == img_name:
            self.set_photo(self.state.current_photo, False, False)

    def set_storage(self, storage: typing.Optional[Storage]):
        if self.storage is not None:
            self.storage.update_photo.disconnect(self._handle_update_photo)
        self.storage = storage
        self.storage.update_photo.connect(self._handle_update_photo)