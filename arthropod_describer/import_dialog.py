import json
import math
import multiprocessing
import os
import re
import shutil
import typing
from concurrent.futures import Future
from enum import IntEnum
from pathlib import Path
from queue import Queue
from threading import Lock
from time import time, sleep
from typing import Union, Optional, List, Literal, Dict, Tuple

import PySide2
import cv2
import qimage2ndarray
from PIL import Image
from PySide2.QtCore import Qt, QAbstractItemModel, QObject, QModelIndex, Signal, QAbstractTableModel, QRegExp, QSize, \
    QTimer, QDir
from PySide2.QtGui import QColor, QRegExpValidator, QPixmap
from PySide2.QtWidgets import QApplication, QDialog, QDialogButtonBox, QCompleter, QFileSystemModel, QTableWidgetItem, \
    QStyledItemDelegate, QWidget, QStyleOptionViewItem, QLineEdit, QComboBox, QLabel, QHeaderView, QVBoxLayout, \
    QTableView

from arthropod_describer.common.image_operation_binding import ResizeWidget
from arthropod_describer.common.label_image import LabelImgType
from arthropod_describer.common.local_storage import IMAGE_REFEX, restructure_folder
from arthropod_describer.common.scale_setting_widget import ScaleSettingWidget
from arthropod_describer.common.state import State
from arthropod_describer.common.units import Value, UnitStore
from arthropod_describer.common.utils import choose_folder, get_scale_line_ends, get_scale_marker_roi, \
    get_reference_length, ScaleLineInfo
from arthropod_describer.image_viewer import ImageViewer
from arthropod_describer.import_utils import TempStorage, TempPhoto
from arthropod_describer.thumbnail_storage import ThumbnailDelegate, ThumbnailStorage_
from arthropod_describer.ui_import_dialog import Ui_ImportDialog

TXT_EXTRACT_SCALE = 'Extract scale from scale markers'
TXT_PLEASE_NAVIGATE_TO_PHOTOS = 'Please navigate to a folder with photos.'


COL_IMPORT = 0
COL_THUMB = 1
COL_NAME = 2
COL_SRC_SIZE = 3
COL_DST_SIZE = 4
COL_SCALE = 5
# COL_ROTATION = 6
COL_SCALE_MARKER = 6
COL_REF_LENGTH = 7
COL_PHOTO_FOLDER = 8
COL_PHOTO_TAG = 9


class ImportAction(IntEnum):
    ImportPhotos = 0,
    CreateProject = 1,


def mp_recognize_scales(img_paths: List[str], result_queue: multiprocessing.Queue, ev: multiprocessing.Event):
    unit_store = UnitStore()
    dig_re = re.compile(r'([0-9]+)\s*([a-zA-Z]m)')
    _time = time()
    for idx, img_path in enumerate(img_paths):
        if ev.is_set():
            print('event is set, i shall finish now')
            result_queue.put_nowait(None)
            return
        # print(f'{_time} alive on {img_path}')
        # photo: TempPhoto = self.temp_storage.get_photo_by_idx(i, True)
        # print(f'detecting in {img_path}')
        image = cv2.imread(img_path)
        scale_marker, (left, top, width, height) = get_scale_marker_roi(image)
        ref_length, scale_rotated = get_reference_length(scale_marker)
        p1x, p1y, p2x, p2y = get_scale_line_ends(scale_marker)
        if p1x < 0:
            continue
        if len(ref_length) > 0:
            match = dig_re.match(ref_length)
            length = int(match.groups()[0])
            unit_str = match.groups()[1]
            unit = unit_store.units[unit_str]
            ref_length = Value(length, unit)
            px_length = Value(round(math.sqrt(((p1x - p2x) * (p1x - p2x) + (p1y - p2y) * (p1y - p2y)))),
                              unit_store.units['px'])
            image_scale = px_length / ref_length
        else:
            ref_length = None
            image_scale = None
            px_length = None
        p1x_, p1y_, p2x_, p2y_ = get_scale_line_ends(scale_rotated)
        scale_rotated = cv2.cvtColor(scale_rotated, cv2.COLOR_GRAY2RGB)
        scale_rotated = cv2.line(scale_rotated, (p1x_, p1y_ - 10), (p1x_, p1y_ + 10), [0, 255, 0], thickness=2)
        scale_rotated = cv2.line(scale_rotated, (p2x_, p1y_ - 10), (p2x_, p1y_ + 10), [0, 255, 0], thickness=2)
        scale_rotated = cv2.resize(scale_rotated, (154, 26), interpolation=cv2.INTER_LINEAR)
        # pixmap = QPixmap.fromImage(qimage2ndarray.array2qimage(scale_rotated))
        scale_marker = scale_rotated

        result_queue.put_nowait((idx, image_scale, ref_length, px_length, (p1x+left, p1y+top, p2x+left, p2y+top), scale_marker,
                                 (left, top, width, height)))
    result_queue.put_nowait(None)


class ImportDialog(QDialog):
    import_btn_clicked = Signal()
    copying_finished = Signal([Path, list])
    open_project = Signal([Path, TempStorage])
    import_photos = Signal(TempStorage) #Signal(list)

    def __init__(self, parent: Optional[PySide2.QtWidgets.QWidget] = None,
                 f: Qt.WindowFlags = Qt.WindowFlags()):
        QDialog.__init__(self, parent, f)
        self.images_to_copy: List[str] = []
        self.current_mode: ImportAction = ImportAction.CreateProject
        self.ui = Ui_ImportDialog()
        self.ui.setupUi(self)

        self.temp_storage: Optional[TempStorage] = None
        # self.thumbnail_storage: ThumbnailStorage = ThumbnailStorage(thumb_size=(128, 64))
        # self.thumbnail_delegate: ThumbnailDelegate = ThumbnailDelegate(self.thumbnail_storage)
        self.thumbnail_delegate: ThumbnailDelegate = None
        self.image_list_model: ImageImportTableModel = ImageImportTableModel()
        # self.image_list_model.set_thumbnail_storage(self.thumbnail_storage)
        self.image_list_model.import_status_changed.connect(self._handle_import_status_changed)
        self.ui.imageList.doubleClicked.connect(self.handle_double_click_on_table)

        self._state = State()

        self.scale_rec_queue: multiprocessing.Queue = multiprocessing.Queue()
        self.scale_rec_timer: QTimer = QTimer()
        self.scale_rec_timer.timeout.connect(self._update_scale_info)
        self._scale_process: multiprocessing.Process = multiprocessing.Process()
        self._scale_stop_event: multiprocessing.Event = multiprocessing.Event()
        self._scale_recognizing_in_progress: bool = False
        self._scale_recognition_left: int = 0

        self._setup_resize_dialog()
        self._setup_import_dialog()
        self._setup_resolution_setter()
        self._setup_image_op()

    def _update_import_button_text(self, scale_recognition_left = 0):
        # If the scale recognition is not running, set the appropriate button text ("Import" or "Create").
        if not self._scale_recognizing_in_progress:
            if self.current_mode == ImportAction.CreateProject:
                self.btnImport.setText("Create")
            else:
                self.btnImport.setText("Import")
        # If the scale recognition is running, and we got info about progress, display it.
        else:
            self.btnImport.setText(f"…reading scale ({scale_recognition_left} photo{'s' if scale_recognition_left > 1 else ''} left)…")

    def _update_scale_info(self):
        while not self.scale_rec_queue.empty():
            res = self.scale_rec_queue.get_nowait()
            if res is None or self.temp_storage is None:
                self.scale_rec_timer.stop()
                self._scale_process.terminate()
                self._scale_process.join()
                self._scale_recognizing_in_progress = False
                self._enable_import_button_if_inout_dirs_valid()
                self.ui.btnExtractScale.setText(TXT_EXTRACT_SCALE)
                self.ui.btnFindInput.setEnabled(True)
                self.ui.txtInput.setEnabled(True)
                self._switch_to_normal_state()
                return
            self._scale_recognition_left -= 1
            idx, image_scale, ref_length, px_length, (p1x, p1y, p2x, p2y), scale_marker, (left, top, width, height) = res
            photo = self.temp_storage.photos_to_import[idx] #self.temp_storage.get_photo_by_idx(idx, False)
            # photo.image_scale = image_scale

            self._update_import_button_text(self._scale_recognition_left)
            sc_setting = photo.scale_setting
            sc_setting.scale = image_scale
            sc_setting.reference_length = ref_length
            sc_setting.scale_line = ScaleLineInfo(
                p1=(p1x, p1y),
                p2=(p2x, p2y),
                length=px_length
            )
            photo.import_info.scale_marker = QPixmap.fromImage(qimage2ndarray.array2qimage(scale_marker))

            sc_setting.scale_marker_bbox = (left, top, width, height)
            sc_setting.scale_marker_img = photo.import_info.scale_marker

            photo.scale_setting = sc_setting

            # photo.import_info.scale_info = photo.scale_setting
            # photo.import_info.original_scale_info = photo.import_info.scale_info
            # photo.import_info.scale_marker = scale_marker

            # photo.ref_length = ref_length
            # ruler = self.ruler_tools[idx]
            # ruler.set_line(QPoint(p1x, p1y), QPoint(p2x, p2y))
            s_index = self.image_list_model.index(idx, COL_SCALE)
            e_index = self.image_list_model.index(idx, COL_REF_LENGTH)
            self.image_list_model.dataChanged.emit(s_index, e_index,
                                                   [Qt.DisplayRole, Qt.DecorationRole])

    def _handle_scales_accepted(self):
        for idx in range(self.temp_storage.image_count):
            photo = self.temp_storage.get_photo_by_idx(idx, False)
            scale_set_tuple = self._scale_set_widget.scale_settings[photo.image_path]
            photo.scale_setting = scale_set_tuple.new_scale_set
        self._handle_scale_set(list(range(self.temp_storage.image_count)))
        self._scale_set_widget.close()

    def _setup_resolution_setter(self):
        self.image_viewer = ImageViewer(self._state)

        self._scale_set_widget = ScaleSettingWidget(self._state)
        self._scale_set_widget.accepted.connect(self._handle_scales_accepted)

    def _handle_scale_set(self, idxs: List[int]):
        first = self.image_list_model.index(idxs[0], 0, QModelIndex())
        end = self.image_list_model.index(idxs[-1], 0, QModelIndex())
        self.image_list_model.dataChanged.emit(first,
                                               end)

    def _handle_photo_rotated(self, photo: TempPhoto, clockwise: bool):
        # TODO REMOVE THIS
        return
        idx = self.temp_storage.image_names.index(photo.image_name)
        self.temp_storage.rotations[idx] = photo.import_info.rotation
        self.temp_storage.dst_image_sizes[idx] = photo.import_info.dst_size

        _photo = self.temp_storage.get_photo_by_idx(idx, load_image=True)

        self._scale_set_widget._fetch_photo(idx)

        idx = self.temp_storage.image_names.index(_photo.image_name)
        index = self.image_list_model.index(idx, COL_ROTATION)
        self.image_list_model.dataChanged.emit(index, index, Qt.DisplayRole)

        path = self.thumbnail_storage._thumbnail_folder / _photo.image_name

        self.thumbnail_storage.load_thumbnail(idx)
        with Image.open(path) as im:
            im = im.rotate(-90 if clockwise else 90, resample=1, expand=True)
            im.save(path)

        self.thumbnail_storage.reload_thumbnail(idx)

    def _setup_resize_dialog(self):
        self._resize_widget = ResizeWidget()
        self._resize_dialog = QDialog(parent=self)
        self._resize_dialog.setWindowTitle('Set image size')
        vbox = QVBoxLayout()
        vbox.addWidget(self._resize_widget)
        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._resize_widget.button_box.button(QDialogButtonBox.Ok).clicked.connect(self._resize_dialog.accept)
        self._resize_widget.invalid_input.connect(self._button_box.button(QDialogButtonBox.Ok).setDisabled)
        self._resize_widget.valid_input.connect(self._button_box.button(QDialogButtonBox.Ok).setEnabled)
        self._resize_widget.button_box.button(QDialogButtonBox.Cancel).clicked.connect(self._resize_dialog.reject)
        #vbox.addWidget(self._button_box)
        self._resize_dialog.setLayout(vbox)

    def _setup_image_op(self):
        self._scale_set_widget.image_op.photo_rotated.connect(self._handle_photo_rotated)

    def handle_double_click_on_table(self, index: QModelIndex):
        if index.column() == COL_SRC_SIZE or index.column() == COL_DST_SIZE:
            photo = self.temp_storage.photos[index.row()]
            self._resize_widget.set_size(photo.import_info.src_size, factor=photo.import_info.resize_factor,
                                         max_factor=photo.import_info.max_resize_factor)
            self._resize_widget.spboxFactor.setValue(photo.import_info.resize_factor)
            # self._resize_widget.set_size(index.data(Qt.UserRole))
            self._resize_dialog.setWindowModality(Qt.WindowModal)
            if self._resize_dialog.exec_() == QDialog.Accepted:
                # self.temp_storage.dst_image_sizes[index.row()] = (self._resize_widget.spboxWidth.value(),
                #                                                   self._resize_widget.spboxHeight.value())
                # self.temp_storage.photos[index.row()].import_info.dst_size = (self._resize_widget.spboxWidth.value(),
                #                                                               self._resize_widget.spboxHeight.value())
                self.temp_storage.photos[index.row()].resize(self._resize_widget.spboxFactor.value())
                self.image_list_model.dataChanged.emit(self.image_list_model.index(index.row(), COL_DST_SIZE),
                                                  self.image_list_model.index(index.row(), COL_SCALE))
        elif index.column() == COL_SCALE:
            self._scale_set_widget.initialize(self.temp_storage)
            self._scale_set_widget.showMaximized()
            photo = self.temp_storage.get_photo_by_idx(index.row(), True)
            self._scale_set_widget.image_viewer.set_photo(photo, True)
            # self._scale_set_widget._fetch_photo(index.row())

    def closeEvent(self, arg__1:PySide2.QtGui.QCloseEvent):
        self._cancel_scale_extraction()
        self._reset_import_dialog()

    def reject(self):
        self.close()

    def _setup_import_dialog(self):
        self.ui.spinBoxImageScale.setVisible(False)
        self.ui.lblImageScale.setVisible(False)
        self._projects_folder: Path = Path('')
        self._project_name: str = ''

        self.setVisible(False)

        self.ui.grpLabelAssignments.setVisible(False)
        self.layout().removeWidget(self.ui.grpLabelAssignments)
        self.adjustSize()

        self.btnImport = self.ui.btnBoxImport.button(QDialogButtonBox.Ok)
        self.btnCancel = self.ui.btnBoxImport.button(QDialogButtonBox.Cancel)

        self.ui.btnFindInput.clicked.connect(self._handle_find_input_clicked)
        self.ui.btnFindOutput.clicked.connect(self._handle_find_output_clicked)
        self.ui.btnExtractScale.clicked.connect(self._handle_extract_scale_clicked)
        # self.ui.btnExtractScale.hide()

        self.btnImport.clicked.connect(self._handle_import_btn_clicked)

        self.btnCancel.clicked.connect(self._handle_cancel_btn_clicked)

        input_path_completer = QCompleter(parent=self)
        filesys_model = QFileSystemModel(input_path_completer)
        filesys_model.setFilter(QDir.AllDirs | QDir.Drives | QDir.NoDotAndDotDot)
        input_path_completer.setModel(filesys_model)
        self.ui.txtInput.setCompleter(input_path_completer)
        self.ui.txtInput.textChanged.connect(self._handle_import_txtInput_changed)
        self.ui.txtInput.textEdited.connect(self._handle_import_txtInput_changed)

        self.ui.spinboxNestLevel.valueChanged.connect(lambda: self._handle_import_txtInput_changed(self.ui.txtInput.text()))

        output_path_completer = QCompleter(parent=self)
        output_path_completer.setModel(QFileSystemModel(output_path_completer))
        self.ui.txtOutput.setCompleter(output_path_completer)
        self.ui.txtOutput.textChanged.connect(self._handle_import_txtOutput_changed)

        self._import_value_lock = Lock()
        self._import_progress_value = 0
        self.import_item_delegate = AssignedLabelImageItemDelegate(self.ui.tableLabelImages.model())
        self.ui.tableLabelImages.setItemDelegate(self.import_item_delegate)
        self.ui.tableLabelImages.setHorizontalHeaderLabels(["Assigned", "Name", "Type"])

        #self.ui.btnAddLabelImage.clicked.connect(self.add_new_label_image_for_import)
        self._project_name_validator = QRegExpValidator()
        reg_exp = QRegExp(r'^[^\t\r\n\\\/<>:"|?*]*[^\t\r\n\\\/<>:"|?*.\s]$')  # https://regex101.com/library/AUr9uv?orderBy=RELEVANCE&search=windows+filename
        self._project_name_validator.setRegExp(reg_exp)
        self.ui.txtProjectName.setValidator(self._project_name_validator)
        self.ui.txtProjectName.textChanged.connect(self._append_project_name_to_output_path)
        self.setTabOrder(self.ui.txtProjectName, self.ui.txtInput)
        self.setTabOrder(self.ui.txtInput, self.ui.txtOutput)
        self.setTabOrder(self.ui.txtOutput, self.ui.spinBoxImageScale)
        self.setTabOrder(self.ui.spinBoxImageScale, self.btnImport)

        self.ui.resizeLayout.setColumnStretch(0, 2)
        self.ui.resizeLayout.setColumnStretch(1, 1)
        self.ui.resizeLayout.setColumnStretch(2, 2)
        self.ui.resizeLayout.addWidget(QLabel("Original size"), 0, 0, Qt.AlignHCenter)
        self.ui.resizeLayout.addWidget(QLabel("Resizing factor"), 0, 1, Qt.AlignHCenter)
        self.ui.resizeLayout.addWidget(QLabel("New size"), 0, 2, Qt.AlignHCenter)
        self._resize_settings: Dict[Tuple[int, int], Tuple[Tuple[int, int], float]] = {}
        self._reset_import_dialog()

        self.ui.imageList.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.ui.imageList.verticalScrollBar().setSingleStep(12)

        self.ui.chkBoxImportCount.stateChanged.connect(self._handle_chkImportCount_stateChanged)

        self.ui.chkMaxSize.stateChanged.connect(self.toggle_max_height_constraint)
        self.ui.spboxMaxSize.valueChanged.connect(self.update_max_height_constraint)

        self._handle_import_txtInput_changed("")  # To (re)set the list model and disable the parts of the GUI that shouldn't be active when no photo folder is initially selected.

        self.ui.rbtnTagInfer.toggled.connect(self.handle_infer_tags_toggled)
        self.ui.rbtnTagGlobal.toggled.connect(self.handle_assign_global_tag_toggled)
        self.ui.txtTagGlobal.textChanged.connect(self.handle_global_tag_changed)
        QObject.connect(QApplication.instance(), PySide2.QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.handle_focus_changed)

    def toggle_max_height_constraint(self, state: Qt.CheckState):
        self.temp_storage.set_max_size(0 if state == Qt.Unchecked else self.ui.spboxMaxSize.value())
        first = self.image_list_model.index(0, COL_DST_SIZE)
        last = self.image_list_model.index(self.temp_storage.image_count - 1, COL_SCALE)
        self.image_list_model.dataChanged.emit(first, last)

    def update_max_height_constraint(self, value: int):
        if self.ui.chkMaxSize.isChecked():
            self.temp_storage.set_max_size(value)
        first = self.image_list_model.index(0, COL_DST_SIZE)
        last = self.image_list_model.index(self.temp_storage.image_count - 1, COL_SCALE)
        self.image_list_model.dataChanged.emit(first, last)

    def _handle_import_txtOutput_changed(self, text: str):
        self._projects_folder = Path(text)
        # If a valid path has been selected as a folder for projects, remember it in config.
        if self.current_mode == ImportAction.CreateProject and self._projects_folder.exists():
            self.parent().config["projects_folder"] = str(self._projects_folder)
            print(f'setting "projects_folder" to {str(self._projects_folder)}')

        self.update_lbl_project_dest()
        self._enable_import_button_if_inout_dirs_valid()

    def update_lbl_project_dest(self):
        if not self._projects_folder.exists():
            self.ui.lblProjectDestination.setText(f"{self._projects_folder} is not a valid folder.")
        else:
            if len(self._project_name) > 0:
                if (out_path := self._projects_folder / self._project_name).exists():
                    if len(os.listdir(out_path)) > 0 and self.current_mode == ImportAction.CreateProject:
                        self.ui.lblProjectDestination.setText(f'{self._projects_folder / self._project_name} is not empty!')
                        return
                self.ui.lblProjectDestination.setText(f'{self._projects_folder / self._project_name}')
            else:
                self.ui.lblProjectDestination.setText('Please give the project a name.')

    def set_label_image_assignments(self, lbl_img_assignments: List[Tuple[str, str, bool]]):
        self.ui.tableLabelImages.setRowCount(len(lbl_img_assignments))
        for row, item in enumerate(lbl_img_assignments):
            name, lbl_t, assig = create_table_widget_row(item[0], item[1], item[2])
            self.ui.tableLabelImages.setItem(row, 0, assig)
            self.ui.tableLabelImages.setItem(row, 1, name)
            self.ui.tableLabelImages.setItem(row, 2, lbl_t)

    def _update_lblImportImgCount_text(self):
        if self.temp_storage is not None:
            import_count = sum([int(photo.import_info.include) for photo in self.temp_storage.photos])
            # self.ui.lblImportImgCount.setText(f'{import_count} photo will be imported.')
            self.ui.chkBoxImportCount.blockSignals(True)

            if self.temp_storage.image_count == 1:
                self.ui.chkBoxImportCount.setText(f'{import_count} photo{"s" if import_count != 1 else ""} selected for import.')
            else:
                self.ui.chkBoxImportCount.setText(f'{import_count} out of {self.temp_storage.image_count} photos selected for import.')
            if import_count == 0:
                self.ui.chkBoxImportCount.setCheckState(Qt.Unchecked)
            elif import_count == self.temp_storage.image_count:
                self.ui.chkBoxImportCount.setCheckState(Qt.Checked)
            else:
                self.ui.chkBoxImportCount.setCheckState(Qt.PartiallyChecked)

            self.ui.chkBoxImportCount.blockSignals(False)
            self.ui.btnExtractScale.setEnabled(import_count > 0)
        else:
            # self.ui.lblImportImgCount.setText('')
            self.ui.chkBoxImportCount.setCheckState(Qt.Unchecked)
            self.ui.chkBoxImportCount.setText('No photos found.')
        self._enable_import_button_if_inout_dirs_valid()

    def _handle_chkImportCount_stateChanged(self, state: Qt.CheckState):
        if self.temp_storage is None:
            return
        if state == Qt.PartiallyChecked:
            self.ui.chkBoxImportCount.setCheckState(Qt.Checked)
            return
        for photo in self.temp_storage.photos:
            photo.import_info.include = state == Qt.Checked
        first = self.image_list_model.index(0, COL_IMPORT)
        last = self.image_list_model.index(self.temp_storage.image_count - 1, COL_IMPORT)
        self.image_list_model.dataChanged.emit(first, last, Qt.CheckStateRole)
        self._update_lblImportImgCount_text()

    def _handle_import_txtInput_changed(self, text: str):
        if text == '' or text.isspace() or not Path(text).exists():
            self.ui.txtInput.setPlaceholderText('Please provide a valid folder.')
            return
        self.ui.spinboxNestLevel.setEnabled(False)

        # TODO show hint that the folder does not exist.
        # if not Path(text).exists():
        #     return
        # contains_photos = _folder_contains_photos(Path(text))
        photo_paths = _discover_photos_rec(Path(text), self.ui.spinboxNestLevel.value())
        contains_photos = len(photo_paths) > 0
        if contains_photos:
            path = Path(text)
            image_fnames = [fname for fname in os.listdir(path) if re.match(IMAGE_REFEX, fname)]
            # image_paths: List[Path] = [Path(direntry.path) for direntry in os.scandir(path) if direntry.is_file() and re.match(IMAGE_REFEX, direntry.name)]
            image_paths = photo_paths
            if self.temp_storage is not None:
                self.temp_storage.close_storage()
            self.temp_storage = TempStorage(image_paths, Path(text),
                                            max_size=self.ui.spboxMaxSize.value() if self.ui.chkMaxSize.isChecked() else 0)
            self._state.storage = self.temp_storage
            self.thumbnail_storage = ThumbnailStorage_(self.temp_storage, thumbnail_size=(128, 64))

            self.image_list_model.set_storage(self.temp_storage)
            self.ui.imageList.reset()
            self.ui.imageList.setModel(self.image_list_model)
            self.ui.imageList.verticalHeader().setDefaultSectionSize(self.thumbnail_storage.thumbnail_size[1] + 32)
            self.ui.imageList.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.ui.imageList.setColumnWidth(1, self.thumbnail_storage.thumbnail_size[0])
            self.ui.imageList.setColumnWidth(6, 170)

            self.ui.grpImagesToImport.setEnabled(True)

            self._enable_import_button_if_inout_dirs_valid()
            self.handle_assign_global_tag_toggled(self.ui.rbtnTagGlobal.isChecked())
            self.handle_infer_tags_toggled(self.ui.rbtnTagInfer.isChecked())
            self.ui.chkMaxSize.setEnabled(True)
            self.ui.spboxMaxSize.setEnabled(True)
        else:
            self.ui.grpImagesToImport.setEnabled(False)

            self.ui.imageList.reset()
            self.ui.imageList.setModel(None)
            if self.temp_storage is not None:
                self.temp_storage.close_storage()
                # TODO call close_storage() on self.thumbnail_storage
            self.temp_storage = None
            # self.ui.btnBoxImport.button(QDialogButtonBox.Ok).setText('Create')
            self.ui.btnBoxImport.button(QDialogButtonBox.Ok).setEnabled(False)
            self.ui.chkMaxSize.setEnabled(False)
            self.ui.spboxMaxSize.setEnabled(False)
        self._update_lblImportImgCount_text()

        self.ui.spinboxNestLevel.setEnabled(True)

    def _enable_import_button_if_inout_dirs_valid(self):
        in_path = Path(self.ui.txtInput.text())
        in_contains_images = self.temp_storage is not None and self.temp_storage.image_count > 0
        if self.temp_storage is not None:
            import_count = sum([int(photo.import_info.include) for photo in self.temp_storage.photos])
        else:
            import_count = 0
        self.ui.chkBoxImportCount.setEnabled(in_contains_images)
        self.btnImport.setEnabled(in_contains_images and self._output_folder_okay() and not self._scale_recognizing_in_progress and import_count > 0)
        self._update_import_button_text(len(self.temp_storage.photos_to_import) if self.temp_storage is not None else 0)

    def _output_folder_okay(self) -> bool:
        projects_folder_exists = self._projects_folder.exists()
        valid_project_name = len(self._project_name) > 0
        project_folder_empty = not (self._projects_folder / self._project_name).exists() or len(os.listdir(self._projects_folder / self._project_name)) == 0
        valid_project_folder = project_folder_empty or self.current_mode == ImportAction.ImportPhotos

        return projects_folder_exists and valid_project_name and valid_project_folder

    def _handle_find_folder(self, input_or_output: Union[Literal['input'], Literal['output']]):
        maybe_path = choose_folder(self, "Open photo folder" if input_or_output == 'input' else "Select new project folder",
                                   path=None if input_or_output == 'input' else self._projects_folder)
        text_field = self.ui.txtInput if input_or_output == 'input' else self.ui.txtOutput
        if maybe_path is not None:
            text_field.setText(str(maybe_path))
            if input_or_output == 'output':
                self._projects_folder = Path(self.ui.txtOutput.text())
            self._enable_import_button_if_inout_dirs_valid()

    def _handle_find_input_clicked(self):
        self._handle_find_folder('input')

    def _handle_import_image_copied(self, _: Future):
        self._import_value_lock.acquire(True, timeout=-1)
        self._import_progress_value += 1
        self.ui.prgrImageCopying.setValue(self._import_progress_value)
        if self._import_progress_value == self.ui.prgrImageCopying.maximum():
            path = Path(self.ui.txtOutput.text())
            if self.current_mode == ImportAction.ImportPhotos:
                self.import_photos.emit(self.temp_storage)
            else:
                self.open_project.emit(path)
            self._import_progress_value = 0
            self._reset_import_dialog()
        self._import_value_lock.release()

    def _handle_find_output_clicked(self):
        self._handle_find_folder('output')

    def _reset_import_dialog(self):
        self.ui.spinBoxImageScale.setVisible(False)
        self.ui.lblImageScale.setVisible(False)
        self.images_to_copy = []
        self.current_mode = ImportAction.CreateProject

        self.ui.txtOutput.setEnabled(True)

        self.ui.txtInput.setEnabled(True)

        self.ui.txtProjectName.setEnabled(True)

        self.ui.txtProjectName.clear()

        self.ui.spinBoxImageScale.setEnabled(True)

        self.ui.btnFindInput.setEnabled(True)

        self.ui.btnFindOutput.setVisible(True)

        self.ui.btnFindOutput.setEnabled(True)

        self.ui.btnExtractScale.setEnabled(False)

        self.ui.txtInput.clear()

        # self.ui.btnExtractScale.setText(TXT_EXTRACT_SCALE)
        self._switch_to_normal_state()

        # self.ui.lblNoImagesInfo.setVisible(False)

        self.ui.prgrImageCopying.setValue(0)

        self.ui.prgrImageCopying.setVisible(False)

        self.ui.txtInput.completer().model().setRootPath(str(Path.home()))

        self.ui.txtOutput.completer().model().setRootPath(str(Path.home()))

        self.btnImport.setEnabled(False)

        self.btnCancel.setEnabled(True)

        self.ui.lblResizeImages.setVisible(False)

        self.ui.resizeLayout.itemAtPosition(0, 0).widget().setVisible(False)
        self.ui.resizeLayout.itemAtPosition(0, 1).widget().setVisible(False)
        self.ui.resizeLayout.itemAtPosition(0, 2).widget().setVisible(False)

        self.temp_storage = None
        self.thumbnail_storage = None
        self.image_list_model.set_storage(None)
        # self.thumbnail_storage.stop()
        self._scale_stop_event.set()
        self.scale_rec_timer.stop()
        self.scale_rec_queue.close()
        self.scale_rec_queue = multiprocessing.Queue()

        # Use a project folder path stored in config. Only use Path.home() if the config is not found or the path it specifies does not exist.
        if "projects_folder" in self.parent().config:
            projects_folder_from_config = Path(self.parent().config["projects_folder"])
            if not projects_folder_from_config.exists():
                projects_folder_from_config = Path.home()
        else:
            projects_folder_from_config = Path.home()
        self._projects_folder = projects_folder_from_config.resolve()

        self._project_name: str = ''
        self._scale_recognizing_in_progress = False
        self._update_lblImportImgCount_text()

        self.ui.chkMaxSize.setEnabled(False)
        self.ui.spboxMaxSize.setEnabled(False)

    def _append_project_name_to_output_path(self, project_name: str):
        if self._projects_folder == Path(''):
            return
        self._project_name = project_name
        out = Path(self._projects_folder / project_name)
        self._enable_import_button_if_inout_dirs_valid()
        self.update_lbl_project_dest()

    def _handle_import_btn_clicked(self):
        in_path = Path(self.ui.txtInput.text())
        out_path = self._projects_folder / self._project_name
        self.import_folder(in_path, out_path)

    def _switch_to_scale_extraction_state(self):
        self.ui.btnExtractScale.setText('Cancel scale extraction')
        self.ui.btnFindInput.setEnabled(False)
        self.ui.txtInput.setEnabled(False)
        self._scale_recognizing_in_progress = True
        self.ui.chkBoxImportCount.setEnabled(False)
        self.image_list_model.disable_import_chkBoxes()

    def _switch_to_normal_state(self):
        self.ui.btnExtractScale.setText(TXT_EXTRACT_SCALE)
        self.ui.btnFindInput.setEnabled(True)
        self.ui.txtInput.setEnabled(True)
        self._scale_recognizing_in_progress = False
        self.ui.chkBoxImportCount.setEnabled(True)
        self.image_list_model.enable_import_chkBoxes()

    def _cancel_scale_extraction(self):
        if self._scale_recognizing_in_progress:
            self._scale_stop_event.set()
            self._scale_process.terminate()
            self.scale_rec_timer.stop()
            while self._scale_process.is_alive():
                sleep(0.001)
            self._switch_to_normal_state()
        self._update_import_button_text()

    def _handle_extract_scale_clicked(self):
        if self._scale_recognizing_in_progress:
            self._cancel_scale_extraction()
            self._scale_recognizing_in_progress = False
            self._enable_import_button_if_inout_dirs_valid()
        else:
            # self.ui.btnFindInput.setEnabled(False)
            # self.ui.txtInput.setEnabled(False)
            # self.ui.btnExtractScale.setText('Cancel scale extraction')

            self.scale_rec_timer.setInterval(750)
            self.scale_rec_timer.start()
            # img_paths = [str(path) for path in self.temp_storage.image_paths]
            img_paths = [str(photo.import_info.src_path) for photo in self.temp_storage.photos_to_import]
            self._scale_recognizing_in_progress = True
            self._scale_recognition_left = len(img_paths)
            print(f'scale rec left = {self._scale_recognition_left}')
            self._update_import_button_text(self._scale_recognition_left)
            self._enable_import_button_if_inout_dirs_valid()
            self._scale_stop_event = multiprocessing.Event()
            self._scale_process = multiprocessing.Process(target=mp_recognize_scales,
                                                          args=(img_paths, self.scale_rec_queue, self._scale_stop_event))
            self._scale_process.start()
            self._switch_to_scale_extraction_state()

    def import_folder(self, in_path: Path, out_path: Path):
        lbl_img_types = {}
        lbl_img_types['Labels'] = {
            'always_constrain_to': None,
            'allow_constrain_to': ['Labels']
        }

        lbl_img_types['Reflections'] = {
            'always_constrain_to': 'Labels',
            'allow_constrain_to': None
        }

        lbls_info = {'label_images': {lbl_name: lbl_info for lbl_name, lbl_info in lbl_img_types.items()},
                     'default_label_image': 'Labels'}

        restructure_folder(out_path, label_folders=list(lbl_img_types.keys()), parents=True)
        self.images_to_copy = []
        for file in os.scandir(in_path):
            if file.is_dir() or not IMAGE_REFEX.match(file.name):
                continue
            self.images_to_copy.append(file)

        self.ui.prgrImageCopying.setMaximum(len(self.images_to_copy))
        self.ui.prgrImageCopying.setVisible(True)
        self.ui.prgrImageCopying.setValue(0)
        self.btnCancel.setEnabled(False)
        self.btnImport.setEnabled(False)
        self.ui.txtOutput.setEnabled(False)
        self.ui.txtInput.setEnabled(False)
        self.ui.spinBoxImageScale.setEnabled(False)
        self.ui.btnFindInput.setEnabled(False)
        self.ui.btnFindOutput.setEnabled(False)
        self.ui.txtProjectName.setEnabled(False)
        self.ui.prgrImageCopying.setEnabled(True)
        self.ui.chkMaxSize.setEnabled(False)
        self.ui.spboxMaxSize.setEnabled(False)

        with open(out_path / 'label_images_info.json', 'w') as f:
            json.dump(lbls_info, f, indent=2)

        present_img_fnames = {fname for fname in os.listdir(out_path / 'images')}
        actual_image_fnames = []
        for i, photo in enumerate(self.temp_storage.photos):
            if not photo.import_info.include:
                continue
            img_path = photo.image_path
            dst_name = img_path.name
            while dst_name in present_img_fnames:
                dot_splits = dst_name.split('.')
                new_dst_name = '.'.join(dot_splits[:-1]) + '_copy.' + dot_splits[-1]
                idx = self.temp_storage.image_names.index(dst_name)
                self.temp_storage._image_names[idx] = new_dst_name
                dst_name = new_dst_name
            actual_image_fnames.append(dst_name)

            dst_path = out_path / 'images' / dst_name
            # if self.temp_storage.image_sizes[i] != self.temp_storage.dst_image_sizes[i] or self.temp_storage.rotations[i] != 0:
            if photo.import_info.src_size != photo.import_info.dst_size:
                # if photo.scale_setting is not None:
                #     mid = np.round(0.5 * np.array(photo.import_info.src_size))
                #     photo.scale_setting.scale_by_factor(photo.import_info.resize_factor, mid)
                    # photo.scale_setting.scale_line.scale(photo.import_info.resize_factor, mid)
                with Image.open(img_path) as im:
                    # if self.temp_storage.image_sizes[i] != self.temp_storage.dst_image_sizes[i]:
                    im = im.resize(photo.import_info.dst_size, resample=2)
                    # if self.temp_storage.rotations[i] != 0:
                    #     im = im.rotate(self.temp_storage.rotations[i] * -90, resample=2, expand=True)
                    im.save(dst_path)
            else:
                shutil.copy2(img_path, dst_path)
            photo.image_path = dst_path

            self.ui.prgrImageCopying.setValue(i + 1)

        path = Path(self.ui.txtOutput.text())
        if self.current_mode == ImportAction.ImportPhotos:
            self.import_photos.emit(self.temp_storage)
        else:
            self.open_project.emit(out_path, self.temp_storage)
        self._reset_import_dialog()

    def open_for_creating_project(self):
        self._reset_import_dialog()
        self.current_mode = ImportAction.CreateProject
        self.setWindowTitle("Create a new project")
        self._project_name = ''
        self.ui.txtOutput.setText(str(self._projects_folder))
        self.ui.txtProjectName.setText(self._project_name)
        self.ui.lblProjectDestination.setEnabled(True)

        self.ui.txtOutput.setVisible(True)
        self.ui.lblProjectsFolder.setVisible(True)

        self.show()

    def open_for_importing(self, project_folder: Path, project_name: str):
        self._reset_import_dialog()
        self.current_mode = ImportAction.ImportPhotos
        self.ui.txtOutput.setText(str(project_folder.parent))
        self.ui.txtOutput.setEnabled(False)
        self.ui.txtProjectName.setText(project_name)
        self.ui.txtProjectName.setEnabled(False)
        self.ui.btnFindOutput.setVisible(False)
        self.ui.btnFindOutput.setEnabled(False)
        self.ui.txtInput.setEnabled(True)
        self.ui.btnFindInput.setEnabled(True)
        self.ui.spinBoxImageScale.setEnabled(True)
        self.setWindowTitle("Import photos")

        self.ui.lblProjectDestination.setEnabled(False)

        self._projects_folder = project_folder.parent

        self.show()

    def _handle_cancel_btn_clicked(self):
        self.close()
        self._reset_import_dialog()

    def _handle_import_status_changed(self, photo_idx: int, will_import: bool):
        self._update_lblImportImgCount_text()

    def handle_infer_tags_toggled(self, checked: bool):
        print(f"calling import_dialog.handle_infer_tags_toggled({checked})")
        if not checked or self.temp_storage is None:
            return
        for photo in self.temp_storage.photos:
            # photo.tags = {'_'.join(photo.import_info.relative_path.parent.parts)}
            photo.tags = set(photo.import_info.relative_path.parent.parts).union({self.temp_storage.root_folder.name})

        self.image_list_model.dataChanged.emit(self.image_list_model.index(0, COL_PHOTO_TAG),
                                          self.image_list_model.index(self.temp_storage.image_count - 1, COL_PHOTO_TAG))

    def handle_assign_global_tag_toggled(self, checked: bool):
        print(f"calling import_dialog.handle_assign_global_tag_toggled({checked})")
        if not checked or self.temp_storage is None:
            return
        for photo in self.temp_storage.photos:
            photo.tags = {self.ui.txtTagGlobal.text()}

        self.image_list_model.dataChanged.emit(self.image_list_model.index(0, COL_PHOTO_TAG),
                                          self.image_list_model.index(self.temp_storage.image_count - 1, COL_PHOTO_TAG))

    def handle_global_tag_changed(self, tag: str):
        print("calling import_dialog.handle_global_tag_changed")
        self.handle_assign_global_tag_toggled(self.ui.rbtnTagGlobal.isChecked())

    def handle_focus_changed(self, old, now):
        # print("calling import_dialog.handle_focus_changed:")
        # print(self)
        # print(old)
        # print(now)
        # print(" ")
        if now == self.ui.txtTagGlobal:
            self.ui.rbtnTagGlobal.setChecked(True)



def create_table_widget_row(name: str, label_type: Union[str, int, LabelImgType], assigned: bool) -> List[QTableWidgetItem]:
    name_item = QTableWidgetItem(name)
    name_item.setData(Qt.UserRole + 1, name)
    if isinstance(label_type, LabelImgType):
        label_type_str = LabelImgType._member_names_[int(label_type)]
    elif type(label_type) == int:
        label_type_str = LabelImgType._member_names_[label_type]
        label_type = LabelImgType(label_type)
    else:
        label_type_str = label_type
        label_type = LabelImgType._member_map_[label_type_str]
    label_type_item = QTableWidgetItem(label_type_str)
    label_type_item.setData(Qt.UserRole + 1, label_type)
    assigned_item = QTableWidgetItem('')
    assigned_item.setData(Qt.UserRole + 1, assigned)
    assigned_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
    assigned_item.setCheckState(Qt.Checked if assigned else Qt.Unchecked)

    return [name_item, label_type_item, assigned_item]


class AssignedLabelImageItemDelegate(QStyledItemDelegate):
    def __init__(self, model: QAbstractItemModel, parent: QObject = None):
        QStyledItemDelegate.__init__(self, parent)
        self._model: QAbstractItemModel = model

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.column() == 1:
            return QLineEdit(parent=parent)
        elif index.column() == 2:
            return QComboBox(parent)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if index.column() == 1:
            name = self._model.data(index)
            editor.setText(name)
        elif index.column() == 2:
            for name in LabelImgType._member_names_:
                editor.addItem(name)
            editor.setCurrentIndex(int(self._model.data(index, Qt.UserRole+1)))

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex):
        if index.column() == 1:
            model.setData(index, editor.text())
            model.setData(index, editor.text(), Qt.UserRole + 1)
        elif index.column() == 2:
            model.setData(index, editor.currentText())
            model.setData(index, LabelImgType._member_map_[editor.currentText()], Qt.UserRole + 1)
        else:
            model.setData(index, editor.checkState() == Qt.Checked)
            model.setData(index, editor.checkState() == Qt.Checked, Qt.UserRole + 1)


def _folder_contains_photos(folder: Path) -> bool:
    if not folder.exists():
        return False
    # TODO what about non-existent folder?
    for file_entry in os.scandir(folder):
        if file_entry.is_file() and re.match(IMAGE_REFEX, file_entry.name):
            return True
    return False


def _discover_photos(folder: Path) -> typing.List[Path]:
    image_paths: typing.List[Path] = []
    if not folder.exists():
        return []
    for file_entry in os.scandir(folder):
        if file_entry.is_file() and re.match(IMAGE_REFEX, file_entry.name):
            image_paths.append(Path(file_entry.path))
    return image_paths


def _discover_photos_rec(folder: Path, nest_level: int=1) -> typing.List[Path]:
    if not folder.exists():
        return []
    queue = Queue()
    queue.put((folder, nest_level))

    discovered_image_paths: typing.List[Path] = []

    while not queue.empty():
        curr_folder, curr_level = queue.get()
        if curr_level < 0:
            continue
        discovered_image_paths.extend(_discover_photos(curr_folder))
        for f_entry in os.scandir(curr_folder):
            if f_entry.is_dir():
                queue.put((Path(f_entry.path), curr_level - 1))

    return discovered_image_paths


class ImageImportTableModel(QAbstractTableModel):
    import_status_changed = Signal([int, bool])

    def __init__(self, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)
        self.storage: Optional[TempStorage] = None
        self.thumbnail_storage: Optional[ThumbnailStorage_] = None
        self.chk_boxes_enabled = True

    def rowCount(self, parent:PySide2.QtCore.QModelIndex=QModelIndex()) -> int:
        if self.storage is None:
            return 0
        return self.storage.image_count

    def columnCount(self, parent:PySide2.QtCore.QModelIndex=QModelIndex()) -> int:
        return 10

    def headerData(self, section:int, orientation:PySide2.QtCore.Qt.Orientation, role:int=Qt.DisplayRole) -> typing.Any:
        if orientation == Qt.Vertical:
            return None
        if section == COL_IMPORT:
            return "Import"
        elif section == COL_THUMB:
            return "Preview"
        elif section == COL_NAME and role == Qt.DisplayRole:
            return "Image name"
        elif section == COL_SRC_SIZE and role == Qt.DisplayRole:
            return "Original size (px)"
        elif section == COL_DST_SIZE and role == Qt.DisplayRole:
            return "New size (px)"
        elif section == COL_SCALE and role == Qt.DisplayRole:
            return "Scale"
        # elif section == COL_ROTATION and role == Qt.DisplayRole:
        #     return "Rotation"
        elif section == COL_SCALE_MARKER and role == Qt.DisplayRole:
            return "Scale marker"
        elif section == COL_REF_LENGTH and role == Qt.DisplayRole:
            return "Reference length"
        elif section == COL_PHOTO_FOLDER and role == Qt.DisplayRole:
            return "Folder"
        elif section == COL_PHOTO_TAG and role == Qt.DisplayRole:
            return "Tags"
        return None

    def data(self, index:PySide2.QtCore.QModelIndex, role:int=Qt.DisplayRole) -> typing.Any:
        photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
        if index.column() == COL_IMPORT:
            if role == Qt.CheckStateRole:
                return Qt.Checked if photo.import_info.include else Qt.Unchecked
        elif index.column() == COL_THUMB:
            if role == Qt.DecorationRole:
                return QPixmap.fromImage(photo.thumbnail)
        elif index.column() == COL_NAME:
            if role == Qt.DisplayRole:
                # return self.storage.image_names[index.row()]
                return photo.image_name
        elif index.column() == COL_SRC_SIZE:
            if role == Qt.DisplayRole:
                # return str(self.storage.image_sizes[index.row()])
                return str(photo.import_info.src_size)
            elif role == Qt.UserRole:
                # return self.storage.image_sizes[index.row()]
                return photo.import_info.src_size
        elif index.column() == COL_DST_SIZE:
            if role == Qt.DisplayRole:
                # return str(self.storage.dst_image_sizes[index.row()])
                return str(photo.import_info.dst_size)
            elif role == Qt.UserRole:
                # return self.storage.image_sizes[index.row()]
                return photo.import_info.dst_size
        elif index.column() == COL_SCALE:
            if role == Qt.DisplayRole:
                # photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
                if (scale := photo.image_scale) is None or scale.value <= 0:
                    return "not set"
                else:
                    return f'{scale}'
        # elif index.column() == COL_ROTATION:
        #     if role == Qt.DisplayRole:
        #         if (rot := photo.import_info.rotation) == 0 or abs(rot == 4):
        #             return "no rotation"
        #         elif rot > 0:
        #             return f"{rot * 90}° CW"
        #         else:
        #             return f"{abs(rot) * 90}° CCW"
        elif index.column() == COL_SCALE_MARKER:
            if role == Qt.DecorationRole:
                # return self.storage.get_photo_by_idx(index.row(), load_image=False).scale_marker
                return photo.import_info.scale_marker
            elif role == Qt.SizeHintRole:
                return QSize(154, 26)
        elif index.column() == COL_REF_LENGTH:
            if role == Qt.DisplayRole:
                # return str(self.storage.get_photo_by_idx(index.row(), load_image=False).ref_length)
                return str(photo.import_info.scale_info.reference_length)
            elif role == Qt.BackgroundRole and photo.import_info.scale_info.reference_length is None: #self.storage.get_photo_by_idx(index.row(), False).ref_length is None:
                return QColor.fromRgb(200, 150, 0)
        elif index.column() == COL_PHOTO_FOLDER:
            if role == Qt.DisplayRole:
                return str(photo.import_info.relative_path.parent)
        elif index.column() == COL_PHOTO_TAG:
            if role == Qt.DisplayRole:
                return ', '.join(photo.tags) if len(photo.tags) > 0 else "no tag"
            elif role == Qt.EditRole:
                return ', '.join(photo.tags)
            elif role == Qt.ForegroundRole:
                if len(photo.tags) == 0:
                    return QColor.fromRgb(150, 150, 150)
        return None

    def flags(self, index: PySide2.QtCore.QModelIndex) -> PySide2.QtCore.Qt.ItemFlags:
        if index.column() == COL_IMPORT:
            if self.chk_boxes_enabled:
                return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
            else:
                return Qt.NoItemFlags
        elif index.column() == COL_PHOTO_TAG:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def enable_import_chkBoxes(self):
        self.chk_boxes_enabled = True
        self.dataChanged.emit(self.index(0, COL_IMPORT),
                              self.index(self.rowCount() - 1, COL_IMPORT), Qt.CheckStateRole)

    def disable_import_chkBoxes(self):
        self.chk_boxes_enabled = False
        self.dataChanged.emit(self.index(0, COL_IMPORT),
                              self.index(self.rowCount() - 1, COL_IMPORT), Qt.CheckStateRole)

    def setData(self, index: PySide2.QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        # if index.column() != COL_IMPORT or role != Qt.CheckStateRole:
        #     return False
        if index.column() == COL_IMPORT and role == Qt.CheckStateRole:
            photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
            photo.import_info.include = bool(value)
            self.import_status_changed.emit(index.row(), bool(value))
            return True
        elif index.column() == COL_PHOTO_TAG:
            photo = self.storage.get_photo_by_idx(index.row(), load_image=False)
            photo.tags = set(map(str.strip, value.split(',')))
            return True
        return False

    # def set_thumbnail_storage(self, thumbnails: ThumbnailStorage_):
    #     self.thumbnail_storage = thumbnails
    #     # self.thumbnail_storage.thumbnails_loaded.connect(self._update_thumbnail_column)

    def set_storage(self, storage: TempStorage):
        self.beginResetModel()
        self.storage = storage
        self.endResetModel()

    def _update_thumbnail_column(self, idxs: List[int]):
        first = self.index(idxs[0], COL_THUMB)
        end = self.index(idxs[-1], COL_THUMB)
        self.dataChanged.emit(first, end, [Qt.DecorationRole])


