import importlib
import importlib
import importlib.resources
import inspect
import json
import logging
import multiprocessing as mp
import os
import platform
import subprocess
import sys
import typing
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import PySide2
from PySide2.QtCore import QModelIndex, QPoint, QItemSelectionModel, QTimer, Signal, Slot, QItemSelection, QObject
from PySide2.QtGui import QCloseEvent, QPixmap, QColor, Qt, QImage, QIcon, QCursor
from PySide2.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QSizePolicy, QMessageBox, QMenu, QAction, \
    QVBoxLayout, QLabel, QDockWidget, QListView, QWidget, QDialogButtonBox, QAbstractItemView

from arthropod_describer.common.blocking_operation import BlockingOperation
from arthropod_describer.common.edit_command_executor import EditCommandExecutor
from arthropod_describer.common.image_operation_binding import ImageOperation
from arthropod_describer.common.label_change import generate_change_command
from arthropod_describer.common.label_hierarchy import LabelHierarchy
from arthropod_describer.common.local_storage import Storage, LocalStorage
from arthropod_describer.common.photo import LabelImg, Photo
from arthropod_describer.common.plugin import RegionComputation, GeneralAction
from arthropod_describer.common.scale_setting_widget import ScaleSettingWidget, ScaleItemDelegate
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool
from arthropod_describer.common.user_params import UserParamWidgetBinding, \
    create_params_widget_with_buttons
from arthropod_describer.common.utils import choose_folder
from arthropod_describer.image_list_delegate import ImageListDelegate, ImageListView
from arthropod_describer.image_list_model import ImageListModel, ImageListSortFilterProxyModel, ROLE_IMAGE_NAME
from arthropod_describer.image_viewer import ImageViewer
from arthropod_describer.import_dialog import ImportDialog
from arthropod_describer.import_utils import TempStorage
from arthropod_describer.label_editor.label_editor import LabelEditor
from arthropod_describer.measurements_viewer.measurements_viewer import MeasurementsViewer
from arthropod_describer.plugin_manager import PluginManager, ProcessType
from arthropod_describer.tag_filter_widget import TagFilterWidget
from arthropod_describer.tags_widget import TagsWidget, PhotoTagsWidget
from arthropod_describer.thumbnail_gui import ThumbGUI
from arthropod_describer.thumbnail_storage import ThumbnailStorage_
from arthropod_describer.tools.ruler import Tool_Ruler
from arthropod_describer.ui_arthropod_describer import Ui_ArhtropodDescriber

logging.basicConfig(filename='arthropod_logger.log', level=logging.INFO, format="%(asctime)s %(filename)-30s %(levelname)-8s %(message)s")
logger = logging.getLogger("ArthropodDescriber")


def run_reg_comp_on_storage(reg_comp: RegionComputation, storage: Storage, progress_queue: mp.Queue, send_photo: bool=True):
    for i in range(storage.image_count):
        photo = storage.get_photo_by_idx(i)
        label_imgs: typing.List[LabelImg] = reg_comp(photo)
        if send_photo:
            progress_queue.put_nowait((i+1, storage.image_count, photo, label_imgs))
        else:
            progress_queue.put_nowait((i+1, storage.image_count))


class ArthropodDescriber(QMainWindow):
    copying_finished = Signal()

    def __init__(self):
        QMainWindow.__init__(self)

        app.setAttribute(Qt.AA_DisableWindowContextHelpButton)

        self.ui = Ui_ArhtropodDescriber()
        self.ui.setupUi(self)

        self._setup_version_checking()

        self.config: typing.Dict[str, typing.Any] = {}
        self.load_config()

        self.state = State()
        self.state.label_img_changed.connect(self._handle_label_image_changed)

        self.tools: typing.List[Tool] = []
        self._load_tools()

        self.label_info_label = QLabel()
        self.label_color_pixmap = QPixmap(24, 24)
        self.label_color_pixmap.fill(QColor.fromRgb(0, 0, 0, 0))
        self.label_color_icon = QLabel()
        self.label_color_icon.setPixmap(self.label_color_pixmap)
        self._hovered_label: int = -1

        self.current_idx: typing.Optional[QModelIndex] = None

        self.thumbnail_storage: typing.Optional[ThumbnailStorage_] = None

        self.plugins_widget = PluginManager(self.state)
        self.plugins_widget.apply_region_computation.connect(self.compute_regions3)

        self._setup_plugins_menu_entry()

        self.measurements_viewer = MeasurementsViewer(self.state)
        self.measurements_viewer.open_project_folder.connect(self.open_project_folder_in_explorer)
        self.measurements_viewer.unsaved_changes.connect(self.enable_actionSave)

        self.ui.tabMeasurements.setLayout(QVBoxLayout())
        self.ui.tabMeasurements.layout().addWidget(self.measurements_viewer)

        self.command_executor: EditCommandExecutor = EditCommandExecutor(self.state)
        self.command_executor.label_image_modified.connect(lambda a, b: self.update_applyToUnsegmented_state())

        self.label_editor = LabelEditor(self.state, self.ui.actionUndo, self.ui.actionRedo,
                                        self.command_executor)
        self._setup_label_editor()

        self.toggle_label_info_visible(False)

        self.image_list_model = ImageListModel()

        self.image_list_proxy_model = ImageListSortFilterProxyModel(self.state)
        self.image_list_proxy_model.setSourceModel(self.image_list_model)
        self.image_list_proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.image_list_proxy_model.setSortRole(Qt.DisplayRole)
        self.image_list_proxy_model.setDynamicSortFilter(True)
        self.image_list_proxy_model.sort(0, Qt.SortOrder.AscendingOrder)

        self._setup_image_list()

        self.storage: typing.Optional[Storage] = None

        self.ui.actionOpenProject.triggered.connect(self.handle_action_open_project_triggered)

        self.import_dialog = ImportDialog(self)
        self.import_dialog.open_project.connect(self.open_project)
        self.import_dialog.import_photos.connect(self.include_photos)
        self.ui.actionImportPhotos.triggered.connect(self.handle_action_import_photos_triggered)
        self.ui.actionCreateProject.triggered.connect(self.import_dialog.open_for_creating_project)
        self.import_dialog.set_label_image_assignments(self.config['label_image_assignments'])
        self.project_path: Path = Path('')

        self._recently_opened_menu = QMenu()
        self.ui.actionRecentlyOpened.setMenu(self._recently_opened_menu)
        self._populate_recently_opened_menu()

        self.ui.actionExit.triggered.connect(self.exit_application)

        self.ui.actionSave.triggered.connect(self.save_project)

        self.label_hierarchies = {}

        self._load_default_label_hierarchies()

        self.ui.tabWidget.currentChanged.connect(self._handle_tab_changed)

        self._setup_dock_widgets()

        self.image_op: ImageOperation = ImageOperation(self)
        self.image_op.photo_rotated.connect(self._handle_image_op_photo_rotated)
        self.image_op.photo_resized.connect(self._handle_image_op_photo_resized)
        self.image_op.operation_running.connect(self._highlight_photo_in_image_list)
        self.image_op.operation_finished.connect(lambda _: self.image_list_model.highlight_indexes([]))

        self._setup_scale_setting_widget()

        self.scale_thumbnail_delegate = ScaleItemDelegate(self.thumbnail_storage, self.scale_setting_widget)

        self.current_image_viewer: ImageViewer = self.label_editor.image_viewer

        self.current_tag_index: typing.Optional[QModelIndex] = None
        self.current_tag_widget: typing.Optional[TagsWidget] = None

        # QObject.connect(QApplication.instance(), PySide2.QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.handle_focus_changed)
        QObject.connect(QApplication.instance(), PySide2.QtCore.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.handle_focus_changed)

    def handle_focus_changed(self, old: QWidget, new: QWidget):
        # print("calling app.py:focus changed")
        # if old == self.image_list:
        #     self.close_photo_tags_widget()
        if new == self:
            self.close_photo_tags_widget()
            self._tag_filter_widget.tags_widget.hide()

    def _setup_scale_setting_widget(self):
        self.scale_setting_widget: ScaleSettingWidget = ScaleSettingWidget(self.state)
        self.scale_setting_widget.accepted.connect(self._handle_scales_accepted)
        self.scale_setting_widget.cancelled.connect(self.switch_to_label_editor)

        self.scale_setting_widget.image_viewer.first_photo_requested.connect(self.fetch_first_photo)
        self.scale_setting_widget.image_viewer.last_photo_requested.connect(self.fetch_last_photo)
        self.scale_setting_widget.image_viewer.next_photo_requested.connect(self.fetch_next_photo)
        self.scale_setting_widget.image_viewer.prev_photo_requested.connect(self.fetch_prev_photo)

    def _setup_plugins_menu_entry(self):
        self.plugins_menu = QMenu('Plugins')
        self.menuBar().insertMenu(self.menuBar().actions()[len(self.menuBar().actions()) - 1], self.plugins_menu)
        for plugin in self.plugins_widget.plugins:
            for i, general_action in enumerate(plugin.general_actions):
                self.plugins_menu.addAction(general_action.info.name)
                action: QAction = self.plugins_menu.actions()[i]
                action.setData(general_action)
        self.plugins_menu.triggered.connect(self.execute_general_action_or_show_settings)
        self.plugins_menu.setEnabled(False)

    def _setup_dock_widgets(self):

        self.dw_image_list = QDockWidget()
        lay_ = QHBoxLayout()
        lay_.addWidget(self.ui.lblTagFilter)
        lay_.addWidget(self.ui.cmbTags)
        lay = QVBoxLayout()
        lay.addLayout(lay_)
        self._tag_filter_widget = TagFilterWidget(self.state, parent=self.dw_image_list)
        lay.addWidget(self._tag_filter_widget)
        lay.addWidget(self.image_list)
        widg = QWidget()
        widg.setLayout(lay)

        self.dw_image_list.setWidget(widg)
        self.dw_image_list.setWindowTitle("Photos")
        self.dw_image_list.setFloating(False)
        self.dw_image_list.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.dw_image_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dw_image_list)

        # Move this block to change the placement of this dockwidget
        self.dw_segmentation = QDockWidget()
        self.dw_segmentation.setWindowTitle("Segmentation and other")
        self.dw_segmentation.setWidget(self.label_editor.region_computation_widget)
        self.dw_segmentation.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dw_segmentation)
        self.dw_segmentation.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.dw_segmentation.sizePolicy().setVerticalStretch(1)
        # end of block

        self.dw_toolbox = QDockWidget()
        self.dw_toolbox.setWindowTitle("Tools")
        self.dw_toolbox.setWidget(self.label_editor.tool_box)
        self.dw_toolbox.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dw_toolbox)
        self.dw_toolbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.dw_toolbox.sizePolicy().setVerticalStretch(2)

        self.dw_labels = QDockWidget()
        self.dw_labels.setWindowTitle("Labels")
        self.dw_labels.setWidget(self.label_editor._label_tree)
        self.dw_labels.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dw_labels)
        self.dw_labels.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.dw_labels.sizePolicy().setVerticalStretch(4)

        self.dw_image_list.setEnabled(False)
        self.dw_labels.setEnabled(False)
        self.dw_toolbox.setEnabled(False)
        self.dw_segmentation.setEnabled(False)

    def _setup_label_editor(self):
        self.label_editor.label_layer.label_hovered.connect(self.show_label_info)
        self.label_editor.ui.lblLabelIcon.setStyleSheet("border: 1px solid black")

        for comp in self.plugins_widget.all_region_computations:
            self.label_editor.region_computation_widget.register_computation(comp)
        for comp in self.plugins_widget.all_measurement_computations:
            self.measurements_viewer.computation_widget.register_computation(comp)

        self.label_editor.region_computation_widget.apply_computation.connect(self.compute_regions3)
        self.label_editor.register_tools(self.tools)

        hbox = QHBoxLayout()
        hbox.addWidget(self.label_editor.widget)

        self.ui.tabLabelEditor.setLayout(hbox)

        with importlib.resources.path('resources', 'undo.png') as path:
            undo_icon = QIcon(str(path))
            redo_pix = QImage(str(path))
            redo_pix = QPixmap.fromImage(redo_pix.mirrored(True, False))
            redo_icon = QIcon(redo_pix)
            self.ui.actionRedo.setIcon(redo_icon)
            self.ui.actionUndo.setIcon(undo_icon)
            self.label_editor.ui.tbtnRedo.setIcon(redo_icon)
            self.label_editor.ui.tbtnUndo.setIcon(undo_icon)

        self.label_editor.image_viewer.first_photo_requested.connect(self.fetch_first_photo)
        self.label_editor.image_viewer.prev_photo_requested.connect(self.fetch_prev_photo)
        self.label_editor.image_viewer.next_photo_requested.connect(self.fetch_next_photo)
        self.label_editor.image_viewer.last_photo_requested.connect(self.fetch_last_photo)

        self.label_editor.unsaved_changes.connect(self.enable_actionSave)

    def _setup_image_list(self):
        self.ui.imageListView.setParent(None)
        self.ui.imageListView.deleteLater()
        self.image_list = ImageListView(self.ui.centralwidget)
        self.image_list.show_tag_ui.connect(self.show_tag_ui)
        self.image_list.hide_tag_ui.connect(self.close_photo_tags_widget)

        self.image_list.setModel(self.image_list_proxy_model)

        self.image_list.selectionModel().currentChanged.connect(self.handle_current_changed)
        self.image_list.selectionModel().selectionChanged.connect(self.handle_selection_changed)

        self.image_list.verticalScrollBar().sliderPressed.connect(self.image_list_model.handle_slider_pressed)
        self.image_list.verticalScrollBar().sliderReleased.connect(self.handle_image_list_slider_released)
        self.image_list.setVerticalScrollMode(QListView.ScrollPerPixel)
        self.image_list.verticalScrollBar().setSingleStep(18)
        self.image_list.entered.connect(self.show_thumbnail_gui)
        self.image_list.setMouseTracking(True)

        self.last_index: QModelIndex = QModelIndex()

        self.thumbnail_delegate = ImageListDelegate(self.thumbnail_storage) #ThumbnailDelegate(self.thumbnail_storage)
        self.image_list.setItemDelegate(self.thumbnail_delegate)
        self.image_list.initialize(self.thumbnail_delegate)
        self.image_list.view_left.connect(self.hide_thumb_gui)
        self.image_list.setUniformItemSizes(True)
        self.image_list.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        # TODO: For whatever reason, even with "self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)", self.image_list.verticalScrollBar().rect().width() == 100 at this point, which seems to be nonsense (width of a scrollbar, reasonable value is e.g. 17).
        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.image_list.setMinimumWidth(self.thumbnail_storage.thumbnail_size.width() + self.image_list.verticalScrollBar().rect().width() + 2 * self.image_list.frameWidth())
        # self.image_list.setMaximumWidth(self.thumbnail_storage.thumbnail_size.width() + self.image_list.verticalScrollBar().rect().width() + 2 * self.image_list.frameWidth())
        self.label_editor.approval_changed.connect(self.image_list_model.handle_approval_changed)

        self.ui.cmbTags.addItem('(no filtering)', None)
        self.ui.cmbTags.currentIndexChanged.connect(self.handle_tag_filter_changed)

        self.ui.cmbTags.setEnabled(False)
        self.ui.cmbTags.setVisible(False)
        self.ui.lblTagFilter.setVisible(False)

        self.state.tags_filter_changed.connect(self.handle_tags_filter_changed)

    def _setup_version_checking(self):
        """Setups the stuff for version checking against the remote gitlab repository."""

        # ---- stuff related to checking whether there is a new commit pertaining to the current git branch -----
        self.__gl_project_token = "otxwJ_8ywJfDsuENMcDE"
        self.__current_branch = None
        self.__version_datetime = None
        self.__local_commit_message = None
        self.__remote_version_datetime = None
        self.__remote_commit_message = ''
        try:  # Don't let this crash the whole application
            self.__current_branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True,
                                                   text=True).stdout.strip()
            self.__version_datetime = subprocess.run(['git', 'log', '--format="%cI"', '-n', '1', 'HEAD'],
                                                     capture_output=True, text=True).stdout.strip()
            self.__version_datetime = datetime.fromisoformat(self.__version_datetime.replace('"', ''))
            self.__version_datetime = datetime.utcfromtimestamp(self.__version_datetime.timestamp())
            self.__local_commit_message = subprocess.run(['git', 'log', '--format="%B"', '-n', '1', 'HEAD'],
                                                         capture_output=True, text=True).stdout.strip()
            self.__remote_version_datetime, self.__remote_commit_message = self.__version_datetime, self.__local_commit_message
        except:
            print("Could not obtain git info about local and remote branch")
        # Disable the "?" button (next to the closing "X") in all dialogs.
        stat_lay = self.statusBar()
        stat_lay.addPermanentWidget(QLabel("Dev info: "))
        stat_lay.addPermanentWidget(QLabel("Current branch: "))
        self.__lbl_current_branch = QLabel(self.__current_branch)
        stat_lay.addPermanentWidget(self.__lbl_current_branch)
        stat_lay.addPermanentWidget(QLabel("Version datetime:"))
        self.__lbl_current_datetime = QLabel(str(self.__version_datetime))
        stat_lay.addPermanentWidget(self.__lbl_current_datetime)
        self.__lbl_current_datetime.setStyleSheet("color: green")
        stat_lay.addPermanentWidget(QLabel("Remote version datetime:"))
        self.__lbl_remote_datetime = QLabel(str(self.__remote_version_datetime))
        stat_lay.addPermanentWidget(self.__lbl_remote_datetime)
        self.__lbl_remote_datetime.setStyleSheet("color: green")
        self.setStatusBar(stat_lay)
        stat_lay.hideOrShow()
        #  ---------------------------------------------------------------------------
        QTimer.singleShot(1000, self.__check_for_remote_version_datetime)
        self.__version_check_timer = QTimer(self)
        self.__version_check_timer.setInterval(5 * 60 * 1000)  # check every 5 minutes
        self.__version_check_timer.start()
        self.ui.actionVersion.triggered.connect(self._show_version_info)
        self.ui.actionOpen_project_folder.triggered.connect(self.open_project_folder_in_explorer)

    def close_photo_tags_widget(self, _: QModelIndex):
        if self.current_tag_widget is not None:
            self.current_tag_widget.close()
            self.current_tag_widget.deleteLater()
            self.current_tag_widget = None
            self.current_tag_index = None

    def handle_tag_widget_left(self):
        point = self.image_list.mapFromGlobal(QCursor.pos())
        if not self.image_list.indexAt(point).isValid():
            self.close_photo_tags_widget(None)

    def _load_default_label_hierarchies(self):
        with importlib.resources.path('arthropod_describer', 'regions_label_hierarchy.json') as path:
            self.label_hierarchies['Labels'] = LabelHierarchy.load(path)
        with importlib.resources.path('arthropod_describer', 'reflections_label_hierarchy.json') as path:
            self.label_hierarchies['Reflections'] = LabelHierarchy.load(path)

    def execute_general_action_or_show_settings(self, qaction: QAction):
        action: GeneralAction = qaction.data()
        if len(action.user_params) > 0:
            widget, diag_butt_box, _ = create_params_widget_with_buttons(action.user_params, self.state)

            diag_box: QDialogButtonBox = diag_butt_box
            diag_box.button(QDialogButtonBox.Apply).clicked.connect(lambda: self.execute_general_action(action, widget))
            diag_box.button(QDialogButtonBox.Cancel).clicked.connect(lambda: self.dispose_of_general_action_settings(widget))

            binding = UserParamWidgetBinding(self.state)
            binding.bind(action.user_params, widget)
            widget.setWindowModality(Qt.ApplicationModal)
            widget.show()
        else:
            self.execute_general_action(action)

    def execute_general_action(self, action: GeneralAction, widget: typing.Optional[QWidget] = None):
        if widget is not None:
            widget.close()
            widget.deleteLater()
        action(self.state)

    def dispose_of_general_action_settings(self, widget: QWidget):
        widget.close()
        widget.deleteLater()

    def _handle_scales_accepted(self):
        for idx in range(self.state.storage.image_count):
            photo = self.state.storage.get_photo_by_idx(idx, False)
            scale_set_tuple = self.scale_setting_widget.scale_settings[photo.image_path]
            photo.scale_setting = scale_set_tuple.new_scale_set
        self.switch_to_label_editor()

        # Update any rulers (and their total length display) after a scale change.
        if isinstance(self.label_editor._current_tool, Tool_Ruler):
            self.label_editor._current_tool.set_out_widget(self.label_editor.tool_out_widget)
            # TODO: Update the ruler visualization with something like
            #       self.label_editor.viz_layer.repaint() ?

    def save_project(self):
        self.state.storage.save()
        first_index = self.image_list_model.index(0, 0, QModelIndex())
        last_index = self.image_list_model.index(self.image_list_model.rowCount() - 1, 0, QModelIndex())
        self.image_list_model.dataChanged.emit(first_index,
                                               last_index,
                                               Qt.UserRole + 6)
        self.ui.actionSave.setEnabled(False)

    def _highlight_photo_in_image_list(self, photo: Photo):
        idx = self.state.storage.image_names.index(photo.image_name)
        self.image_list_model.highlight_indexes([idx])

    def _handle_image_op_photo_rotated(self, photo: Photo, cw: bool):
        # Rotate the rulers
        if isinstance(self.label_editor._current_tool, Tool_Ruler):
            mid = (round(self.state.current_photo.image_size[1] * 0.5), round(self.state.current_photo.image_size[0] * 0.5))  # Flip width and height, because this is happening after the photo has already rotated.
            self.label_editor._current_tool.rotate(not cw, mid)

        # TODO: Why is this `return` here, and unreachable code beyond it?
        return
        self.label_editor.reset_tool()
        photo.save()
        if photo.image_name == self.state.current_photo.image_name:
            self.state.current_photo = photo
            self.label_editor.image_viewer.set_photo(photo, reset_view=True)
        idx = self.state.storage.image_names.index(photo.image_name)
        self.thumbnail_storage.rotate_thumbnail(idx, cw)
        self.image_list_model.highlight_indexes([])

    def _handle_image_op_photo_resized(self, photo: Photo):
        self.label_editor.reset_tool()
        photo.save()
        print(f'resize images size is {photo.image_size}')
        if photo.image_name == self.state.current_photo.image_name:
            self.state.current_photo = photo
            self.label_editor.image_viewer.set_photo(photo, reset_view=True)
        self.image_list_model.highlight_indexes([])
        idx = self.state.storage.image_names.index(photo.image_name)
        self.thumbnail_storage.generate_thumbnail(idx)
        self.thumbnail_storage.reload_thumbnail(idx)

    def _handle_tab_changed(self, tab_idx: int):
        if tab_idx == 0:
            self.dw_labels.show()
            self.dw_toolbox.show()
            self.dw_segmentation.show()
        else:
            self.dw_labels.hide()
            self.dw_toolbox.hide()
            self.dw_segmentation.hide()

    def _show_version_info(self):
        print(self.__version_datetime)
        QMessageBox.information(self, "Arthropod Describer version",
                                f'Current branch: {self.__current_branch}\nCurrent version date: {self.__version_datetime}\nRemote version date: {self.__remote_version_datetime}',
                                QMessageBox.Ok)

    def __fetch_remote_version_datetime(self) -> typing.Optional[typing.Tuple[datetime, str]]:
        resp = urllib.request.urlopen(f'https://gitlab.fi.muni.cz/api/v4/projects/20999/repository/commits/{self.__current_branch}?private_token={self.__gl_project_token}',
                                      timeout=1.5)
        if resp.status != 200:
            raise Exception
        resp_obj = json.load(resp)
        __remote_version_datetime = datetime.fromisoformat(resp_obj['committed_date'])
        __remote_version_datetime = datetime.utcfromtimestamp(__remote_version_datetime.timestamp())
        return __remote_version_datetime, resp_obj['message'].strip()

    def __check_for_remote_version_datetime(self):
        try:
            remote_version, commit_message = self.__fetch_remote_version_datetime()
            if remote_version == self.__remote_version_datetime: # Don't show the dialog repeatedly if the remote_version is already familiar to the app.
                return
            self.__remote_version_datetime = remote_version
            self.__remote_commit_message = commit_message
            self.__lbl_remote_datetime.setText(str(self.__remote_version_datetime))
            if self.__remote_version_datetime > self.__version_datetime:
                msg = f'There is a new commit in the remote {self.__current_branch} branch\n'
                msg = msg + f'Datetime: {self.__remote_version_datetime}\nCommit message: {self.__remote_commit_message}'
                QMessageBox.information(self, "New version available",
                                        msg,
                                        QMessageBox.Ok)
                self.__lbl_current_datetime.setStyleSheet("color: red")
                self.__lbl_remote_datetime.setStyleSheet("color: green")
            elif self.__version_datetime > self.__remote_version_datetime:
                self.__lbl_remote_datetime.setStyleSheet("color: red")
                self.__lbl_current_datetime.setStyleSheet("color: green")
            else:
                self.__lbl_remote_datetime.setStyleSheet("color: green")
                self.__lbl_current_datetime.setStyleSheet("color: green")
        except urllib.error.URLError as e:
            print(f'Could not obtain remote repo info reason: {e.reason}')
        except:
            print("Could not obtain remote repo info")

    @Slot()
    def handle_copying_finished(self):
        self.open_project(self.project_path)
        self.import_dialog.hide()

    def update_applyToUnsegmented_state(self):
        unsegmented_count = 0
        if self.state.storage is not None:
            for i in range(self.state.storage.image_count):
                photo = self.state.storage.get_photo_by_idx(i, False)
                if not photo.has_segmentation_for(self.state.storage.default_label_image):
                    unsegmented_count = unsegmented_count + 1
        apply_to_all_unsegmented_text = "Apply to all unsegmented"
        self.label_editor.region_computation_widget.action_applyToUnsegmented.setText(apply_to_all_unsegmented_text + f" ({unsegmented_count if unsegmented_count > 0 else 'none'})")
        self.label_editor.region_computation_widget.action_applyToUnsegmented.setEnabled(unsegmented_count > 0)

    def _load_tools(self):
        logger.info('Attempting to load tools')
        py_files = [inspect.getmodulename(file.path) for file in os.scandir(Path(__file__).parent / 'tools') if file.name.endswith('.py') and file.name != '__init__.py']
        logger.info(py_files)
        modules = [importlib.import_module(f'.{module_name}', '.tools') for module_name in py_files]
        tools = []
        for module in modules:
            members = inspect.getmembers(module)
            for obj_name, obj in members:
                if not obj_name.startswith('Tool_'):
                    continue
                if inspect.isclass(obj) and not inspect.isabstract(obj):
                    tool = obj(self.state)
                    tool.set_tool_id(len(tools))
                    self.state.colormap_changed.connect(tool.color_map_changed) #lambda cmap: tool.color_map_changed(cmap.colormap))
                    tools.append(tool)

        self.tools = tools
        logger.info(f'loaded {len(tools)} tools')

    def handle_tags_filter_changed(self, active_tags: typing.List[str]):
        self.image_list_proxy_model.invalidate()
        self.fetch_first_photo()

    def handle_tag_filter_changed(self, filter_index: int):
        self.clear_selection()
        if self.ui.cmbTags.currentData() is None:
            self.image_list_proxy_model.setFilterFixedString('')
            self.fetch_first_photo()
        else:
            tag = self.ui.cmbTags.currentText()
            self.image_list_proxy_model.setFilterFixedString(tag)
            self.fetch_first_photo()

    def handle_new_tag_added(self, photo: Photo, tag: str):
        tags: typing.List[str] = list(sorted(self.storage.used_tags))
        tag_index = tags.index(tag) + 1  # offset by 1 because the option "(no filter)" is not present in `tags` and is always at index 0
        self.ui.cmbTags.insertItem(tag_index, tag, tag)

    def repopulate_tags_combobox(self):
        self.ui.cmbTags.blockSignals(True)
        for i in range(1, self.ui.cmbTags.count()):
            self.ui.cmbTags.removeItem(1)

        tags: typing.Set[str] = self.storage.used_tags

        for tag in sorted(tags):
            self.ui.cmbTags.addItem(tag, userData=tag)
        self.ui.cmbTags.blockSignals(False)

    def hide_thumb_gui(self):
        if self.last_index.isValid():
            self.image_list.setIndexWidget(self.last_index, None)
            self.last_index = QModelIndex()
        if self.current_tag_widget is not None:
            cursor_pos = QCursor.pos()
            tag_rect = self.current_tag_widget.rect().translated(self.current_tag_widget.pos())
            if tag_rect.contains(cursor_pos):
                return
            self.close_photo_tags_widget(None)

    def show_thumbnail_gui(self, index: QModelIndex):
        if self.last_index.isValid() and index != self.last_index:
            self.image_list.setIndexWidget(self.last_index, None)
            self.last_index = QModelIndex()
        actual_index = self.image_list_proxy_model.mapToSource(index)
        photo = self.state.storage.get_photo_by_idx(actual_index.row(), load_image=False)
        if self.state.current_photo is None or photo.image_name != self.state.current_photo.image_name:
            photo = self.state.storage.get_photo_by_idx(actual_index.row(), load_image=True)
        self.image_op.init(photo)
        widg = ThumbGUI(photo, self.image_list)
        #widg.rotate_requested.connect(self.handle_rotation_requested)
        widg.rotate_requested.connect(lambda _, cw: self.image_op.rotate(cw))
        widg.resize_requested.connect(lambda _: self.image_op.resize())
        widg.resolution_setting_requested.connect(self.handle_resolution_setting_requested)
        widg.save_photo.connect(self._save_photo)
        widg.delete_photo_requested.connect(self.handle_delete_photo_requested)

        self.image_list.setIndexWidget(index, widg)
        self.last_index = index
        widg.setVisible(True)

    def show_tag_ui(self, index: QModelIndex):
        actual_index = self.image_list_proxy_model.mapToSource(index)
        photo = self.state.storage.get_photo_by_idx(actual_index.row(), load_image=False)
        if index != self.current_tag_index:
            self.close_photo_tags_widget(None)
            self.current_tag_widget = PhotoTagsWidget(photo, self.state, self.image_list, Qt.Window
                                                      # | Qt.WindowStaysOnTopHint
                                                      | Qt.X11BypassWindowManagerHint
                                                      | Qt.FramelessWindowHint)
            self.current_tag_widget.setVisible(True)
            self.current_tag_widget.populate()
            self.current_tag_widget.setWindowModality(Qt.NonModal)

            # rect = self.image_list.visualRect(index)
            rect = self.image_list.delegate.tag_rects[index.row()]
            top_right = rect.topRight()
            # app_top_right = self.image_list.mapTo(self, top_right) + self.pos()
            app_top_right = self.image_list.mapToGlobal(top_right)
            # Adjust the Y-position of the panel so that it fits on the screen vertically (unless it is itself too tall -- in that case, scrolling or multi-column layout may be necessary).
            app_top_right.setY(max(min(app_top_right.y(), self.screen().availableGeometry().height() - self.current_tag_widget.height()), 0))

            self.current_tag_widget.move(app_top_right)
            self.current_tag_widget.show()
            self.current_tag_index = index
            self.current_tag_widget.widget_left.connect(self.handle_tag_widget_left)
            # self.current_tag_widget.add_new_tag.connect(self.handle_new_tag_added)

    def _save_photo(self, photo: Photo):
        photo.save()
        idx = self.state.storage.image_names.index(photo.image_name)
        index = self.image_list_model.index(idx, 0, QModelIndex())
        self.image_list_model.dataChanged.emit(index, index, Qt.UserRole + 6)

    def handle_thumbnail_gui_rotate_request(self, widget: ThumbGUI, im_op: ImageOperation):
        def rotate(photo: Photo, cw: bool):
            widget.setEnabled(False)
            im_op.rotate(cw)
            widget.setEnabled(True)
        return rotate

    def set_storage(self, storage: Storage):
        logger.info(f'Setting storage to {storage.location}')
        for lbl_name in storage.label_image_names:
            if storage.get_label_hierarchy2(lbl_name) is None:
                storage.set_label_hierarchy2(lbl_name, self.label_hierarchies[lbl_name])
        self.plugins_menu.setEnabled(True)
        self.storage = storage
        self.storage.storage_update.connect(self.handle_storage_updated)
        self.state.storage = storage
        self._tag_filter_widget.initialize()
        self.state.current_label_name = self.storage.default_label_image
        self.state.set_label_constraint(self.state.current_label_name)
        self.command_executor.initialize(self.state)

        self.thumbnail_storage = ThumbnailStorage_(self.state.storage)
        self.thumbnail_delegate = ImageListDelegate(self.thumbnail_storage)
        self.image_list.initialize(self.thumbnail_delegate)

        self.image_list_model.initialize(self.storage.image_paths, self.thumbnail_storage, 0, self.state.storage)

        self.current_idx = self.image_list_proxy_model.index(0, 0)
        self.label_editor.widget.setEnabled(True)
        self.measurements_viewer.setEnabled(True)
        self.label_editor.ui.MaskGroup.setEnabled(True)
        self.label_editor._label_switch.set_label_hierarchy(self.state.storage.get_label_hierarchy2(self.state.current_label_name))

        if self.state.storage.image_count == 0:
            self.label_editor.image_viewer.set_photo(None, True)
            self.label_editor.disable()
        else:
            self.label_editor.enable()

        self.scale_setting_widget.initialize(self.state.storage)

        self.image_list.selectionModel().setCurrentIndex(self.current_idx, QItemSelectionModel.Select)

        self.setWindowTitle(f'Arthropod Describer - {storage.location}')
        self.ui.actionImportPhotos.setEnabled(True)
        self.measurements_viewer.update_measurements_view()
        self.ui.actionOpen_project_folder.setEnabled(True)
        self.state.constraint_label = 0

        self.dw_image_list.setEnabled(True)
        self.dw_labels.setEnabled(True)
        self.dw_toolbox.setEnabled(True)
        self.dw_segmentation.setEnabled(True)

        self.label_editor.widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.image_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.image_list.setMinimumWidth(self.thumbnail_storage.thumbnail_size[0] + self.image_list.verticalScrollBar().rect().width() + 2 * self.image_list.frameWidth())
        self.image_list.setMaximumWidth(self.thumbnail_storage.thumbnail_size[0] + self.image_list.verticalScrollBar().rect().width() + 2 * self.image_list.frameWidth())
        self.image_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.repopulate_tags_combobox()

    def handle_storage_updated(self, data: typing.Dict[str, typing.Any]):
        if 'tags' in data:
            self.repopulate_tags_combobox()
            # if 'new' in data['tags']:
            #     self.add_tags_to_dropdown(data['tags']['new'])
            # if 'deleted' in data['tags']:
            #     self.remove_tags_from_dropdown(data['tags']['deleted'])

    # def add_tags_to_dropdown(self, tags: typing.Set[str]):
    #     new_tags_sorted = list(sorted(tags))
    #     all_tags = list(sorted(self.storage.used_tags))
    #
    #     for tag in new_tags_sorted:
    #         idx = all_tags.index(tag)
    #         self.ui.cmbTags

    def fetch_photo(self, idx: int):
        if idx < 0 or idx >= self.image_list_model.rowCount():
            return
        # TODO add guard to ensure idx >= 0
        self.image_list.setSelectionMode(QListView.SingleSelection)
        if self.state.current_photo is not None:
            prev_idx = self.state.storage.image_names.index(self.state.current_photo.image_name)
            curr_idx = self.image_list.currentIndex()
            curr_idx_mapped = self.image_list_proxy_model.mapToSource(curr_idx)
            if curr_idx_mapped.row() != prev_idx:
                _idx = self.image_list_model.index(prev_idx, 0)
                self.image_list.setCurrentIndex(self.image_list_proxy_model.mapFromSource(_idx))
        else:
            prev_idx = None
        logger.info(f'fetching photo with the index = {idx} (previous photo index is {prev_idx})')
        new_index = self.image_list_proxy_model.mapFromSource(self.image_list_model.index(idx, 0))
        # self.label_editor.image_viewer.enable_navigation_buttons(new_index.row(), self.image_list_proxy_model.rowCount())
        self.current_image_viewer.enable_navigation_buttons(new_index.row(), self.image_list_proxy_model.rowCount())
        self.image_list.setCurrentIndex(new_index)

    def fetch_first_photo(self):
        new_index = self.image_list_proxy_model.mapToSource(self.image_list_proxy_model.index(0, 0))
        self.fetch_photo(new_index.row())

    def fetch_prev_photo(self):
        new_index = self.image_list_proxy_model.mapToSource(
            # self.image_list_proxy_model.index(max(0, self.image_list.currentIndex().row() - 1), 0)
            self.image_list_proxy_model.index(max(0, self.current_idx.row() - 1), 0)
        )
        self.fetch_photo(new_index.row())

    def fetch_next_photo(self):
        new_index = self.image_list_proxy_model.mapToSource(
            self.image_list_proxy_model.index(
                # min(self.image_list.currentIndex().row() + 1, self.image_list_proxy_model.rowCount() - 1),
                # 0)
                min(self.current_idx.row() + 1, self.image_list_proxy_model.rowCount() - 1),
                0))
        self.fetch_photo(new_index.row())

    def fetch_last_photo(self):
        new_index = self.image_list_proxy_model.mapToSource(
            self.image_list_proxy_model.index(self.image_list_proxy_model.rowCount() - 1, 0)
        )
        self.fetch_photo(new_index.row())

    def clear_selection(self):
        self.image_list.selectionModel().clearSelection()

    def clear_multi_selection(self):
        """
        Deselects everything except the photo that was selected first.
        """
        selection = self.image_list.selectionModel().selectedIndexes()
        if len(selection) < 2:
            return

        selection.remove(self.current_idx)

        first = min(selection, key=lambda idx: idx.row())
        end = max(selection, key=lambda idx: idx.row())
        self.image_list.selectionModel().select(QItemSelection(first, end), QItemSelectionModel.Deselect)

    def handle_action_import_folder_triggered(self, checked: bool):
        self.import_dialog.setVisible(True)

    def handle_current_changed(self, current: QModelIndex, previous: QModelIndex):
        if not current.isValid():
            self.state.current_photo = None
            return
        # if self.image_list.selectionMode() != ImageListView.SingleSelection:
        #     logging.info(f'handle_current_changed, selection mode is not SingleSelection (is {self.image_list.selectionMode()}, returning')
        #     return
        logger.info(f'Image list current item changed from index {previous.row()} ({previous.data(Qt.DisplayRole)}) to {current.row()} ({current.data(Qt.DisplayRole)})')

        mapped_index = self.image_list_proxy_model.mapToSource(current)
        row = mapped_index.row()

        if self.state.current_photo is not None:
            logger.info(f'Unloading the current photo {self.state.current_photo.image_name}.')
            for _, lbl_img in self.state.current_photo.label_images_.items():
                lbl_img.unload()
        photo = self.storage.get_photo_by_idx(row)
        self.state.current_photo = photo
        logger.info(f'Current photo is now {self.state.current_photo.image_name}')
        print(f'Current photo is now {self.state.current_photo.image_name}')

        if self.current_image_viewer == self.label_editor.image_viewer:
            self.label_editor.image_viewer.set_photo(photo, True)
            self.label_editor.image_viewer.enable_navigation_buttons(current.row(), self.image_list_proxy_model.rowCount())
        else:
            self.scale_setting_widget.image_viewer.set_photo(photo, True)
            self.scale_setting_widget.image_viewer.enable_navigation_buttons(current.row(), self.image_list_proxy_model.rowCount())
        self.current_idx = current

    def handle_selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        if len(self.image_list.selectionModel().selectedIndexes()) == 0:
            self.image_list.selectionModel().select(QItemSelection(deselected.indexes()[0],
                                                    deselected.indexes()[0]), QItemSelectionModel.Select)

    def handle_image_list_slider_released(self):
        first_idx = self.image_list.indexAt(QPoint(0, 0))
        last_idx = self.image_list.indexAt(self.image_list.viewport().rect().bottomLeft())
        self.image_list_model.handle_slider_released(first_idx, last_idx)

    def handle_action_import_photos_triggered(self):
        self.import_dialog.open_for_importing(self.state.storage.location,
                                              self.state.storage.storage_name)

    def exit_application(self):
        self.close()

    def closeEvent(self, event: QCloseEvent):
        reply = QMessageBox.question(self, 'Confirmation', 'Do you really want to exit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # self.thumbnail_storage.stop()
            if self.storage is not None:
                self.storage.save()
            self.label_editor.release_resources()
            self.save_config()
            event.accept()
        else:
            event.ignore()

    def handle_action_open_project_triggered(self):
        maybe_path = choose_folder(self, "Open project folder")
        if maybe_path is not None:
            self.open_project(maybe_path, None)

    def _move_recent_project_action_to_front(self, action: QAction):
        """
        Puts the entry of the most recently opened project at the first place in the recently opened projects menu.
        """
        if action is None:
            return
        self._recently_opened_menu.removeAction(action)
        if len(self._recently_opened_menu.actions()) < 3:
            self._recently_opened_menu.addAction(action)
        else:
            self._recently_opened_menu.insertAction(self._recently_opened_menu.actions()[2], action)  # Add just after the separator (at index 2).

    def open_project(self, folder: Path, temp_storage: typing.Optional[TempStorage]):
        logger.info(f'Attempting to open the project from {folder}')
        try:
            if self.state.storage is not None:
                self.state.storage.save()
                logger.info('Stopping ThumbnailStorage')
                # self.thumbnail_storage.stop()
            logger.info(f'Attemtpting to load LocalStorage from {folder}')
            strg = LocalStorage.load_from(folder)  # <-- This is where the exception happens if the .json is not found.

            self.set_storage(strg)

            if temp_storage is not None:
                logger.info('Setting scale infos for the TempStorage')
                for photo_to_import in temp_storage.photos_to_import:
                    photo = strg.get_photo_by_name(photo_to_import.image_name, load_image=False)
                    photo.scale_setting = photo_to_import.import_info.scale_info
                    photo.tags = photo_to_import.tags
                self.scale_setting_widget.initialize(self.state.storage)
                self.scale_setting_widget.image_viewer.set_photo(self.state.current_photo)
            logger.info('Repopulating combobox')
            self.repopulate_tags_combobox()
            logger.info('Saving storage')
            strg.save()
            logger.info('Saved storage')

            folder_string = str(folder)
            project_paths = self.config.setdefault('project_paths', [])
            if folder_string in project_paths:
                #return # TODO: This `return` was here, but seemed incorrect. Instead, moving the project to the beginning of the list was added.
                project_paths.remove(folder_string)
                project_paths.insert(0, folder_string)
            else:
                project_paths.insert(0, folder_string)

            logger.info('Saving config')
            self.save_config()
            logger.info('Saved config')
            logger.info('Populating recently opened')
            self._populate_recently_opened_menu()
            logger.info('Populated recently opened')
            # Move the added/updated menu action to the front.
            action = self._recently_opened_menu.findChild(QAction, folder_string)
            self._move_recent_project_action_to_front(action)

            # TODO: Was this okay? `self.import_dialog.hide()` is here, but originally, we might have already
            #       left the function because of `if str(folder) in project_paths: return` -- that return has
            #       now been removed.
            #       .
            #       This becomes relevant only when creating a new project -- the project is created, then opened (during which it is added to the front of the recent list), and then the import/create window is closed.
            #       What happens when creating a project with a name/location that already exists?
            self.import_dialog.hide()
            self.update_applyToUnsegmented_state()
        except IOError as e:
            error_message = QMessageBox(self)
            error_message.setIcon(QMessageBox.Warning)
            error_message.setWindowTitle('Project not opened')
            error_message.setText(f'Unable to open project from "{folder}".')
            error_message.setStandardButtons(QMessageBox.Ok)
            error_message.exec()
            if (folder_str := str(folder)) in self.config['project_paths']:
                self.config['project_paths'].remove(folder_str)
                if (action := self._recently_opened_menu.findChild(QAction, folder_str)) is not None:
                    self._recently_opened_menu.removeAction(action)

    def include_photos(self, temp_storage: TempStorage):
        # TODO switch to scale setting with for these photos only.
        if (scale := self.import_dialog.ui.spinBoxImageScale.value()) < 0:
            scale = None
        self.state.storage.include_photos([photo.image_name for photo in temp_storage.photos_to_import
                                           if photo.import_info.include], scale)
        # self.thumbnail_storage.initialize(self.state.storage)
        self.image_list_model.initialize(self.state.storage.image_paths, self.thumbnail_storage, 0,
                                         self.state.storage)
        self.import_dialog.hide()
        self.command_executor.update()
        if self.state.storage.image_count == 1:
            self.fetch_first_photo()
        # self.state.storage.blockSignals(True)
        for temp_photo in temp_storage.photos_to_import:
            photo = self.state.storage.get_photo_by_name(temp_photo.image_name, load_image=False)
            photo.scale_setting = temp_photo.import_info.scale_info
            photo.tags = temp_photo.tags
            idx = self.state.storage.image_names.index(photo.image_name)
            # self.thumbnail_storage.generate_thumbnail(idx)
            # self.thumbnail_storage.reload_thumbnail(idx)
        # self.state.storage.blockSignals(False)
        self.update_applyToUnsegmented_state()
        self.repopulate_tags_combobox()

    def load_config(self):
        if not (Path(__file__).parent / 'config.json').exists():
            self.config = {'project_paths': [],
                "label_image_assignments": [
                    ['Labels', "Regions", True],
                    ["Reflections", "Mask", True]
                ]
            }
        else:
            with open(Path(__file__).parent / 'config.json') as f:
                self.config = json.load(f)
            if 'label_image_assignments' not in self.config:
                self.config['label_image_assignments'] = [
                    ['Labels', "Regions", True],
                    ["Reflections", "Mask", True]
                ]

    def save_config(self):
        with open(Path(__file__).parent / 'config.json', 'w') as f:
            json.dump(self.config, f, indent=2)

    def _populate_recently_opened_menu(self):
        # Add the "Clear recent projects list" action if not present.
        clear_recent_project_list_text = "Clear recent projects list"
        clear_recent_project_list_name = "clear_recent_projects_list"
        if self._recently_opened_menu.findChild(QAction, clear_recent_project_list_name) is None:
            action = QAction(clear_recent_project_list_text, parent=self._recently_opened_menu)
            action.setObjectName(clear_recent_project_list_name)
            action.triggered.connect(self._clear_recently_opened_menu)
            self._recently_opened_menu.addAction(action)
            self._recently_opened_menu.addSeparator()

        path_strings = list(self.config['project_paths'])
        for path in path_strings:
            if not Path(path).exists():
                self.config['project_paths'].remove(path)
                continue
            if self._recently_opened_menu.findChild(QAction, path) is not None:
                continue
            action = QAction(path, parent=self._recently_opened_menu)
            action.setObjectName(path)
            action.triggered.connect(self._recent_project_action_handler(action))
            self._recently_opened_menu.addAction(action)
        self.ui.actionRecentlyOpened.setEnabled(len(self.config['project_paths']) > 0)

    def _recent_project_action_handler(self, action: QAction):
        def handle_action_triggered():
            path_text = action.text()

            # Put the project that is just being opened at the front of the recent list.
            self._move_recent_project_action_to_front(action)
            self.config['project_paths'].remove(path_text)
            self.config['project_paths'].insert(0, path_text)

            path = Path(path_text)
            self.open_project(path, None)
        return handle_action_triggered

    def _clear_recently_opened_menu(self):
        self.config['project_paths'].clear()
        self._recently_opened_menu.clear()
        self._populate_recently_opened_menu()
        self.save_config()

    def toggle_label_info_visible(self, visible: bool):
        for i in range(self.label_editor.ui.layoutLabelInfo.count()):
            self.label_editor.ui.layoutLabelInfo.itemAt(i).widget().setVisible(visible)

    def show_label_info(self, label: int):
        if label < 0:
            self.toggle_label_info_visible(False)
            self._hovered_label = label
            return
        if label == self._hovered_label:
            return
        if self._hovered_label < 0 and label >= 0:
            self.toggle_label_info_visible(True)
        self._hovered_label = label
        #info = f'{self.state.colormap.label_names[label]} - code {self.state.label_hierarchy.code(label)}'
        lab_hier = self.state.label_hierarchy
        info = f'{lab_hier.nodes[label].name} - code {lab_hier.nodes[label].code}'
        color = self.state.colormap[label]
        self.label_color_pixmap.fill(QColor.fromRgb(*color, 255 if label > 0 else 0))
        self.label_editor.ui.lblLabelIcon.setPixmap(self.label_color_pixmap)
        self.label_editor.ui.lblLabelInfo.setText(info)

    def open_project_folder_in_explorer(self):
        if self.state.storage is None:  # Shouldn't even be necessary, as the QAction shouldn't be enabled in that case
            return
        if platform.system() == "Windows":
            os.startfile(self.state.storage.location)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(self.state.storage.location)])
        else:
            subprocess.Popen(["xdg-open", str(self.state.storage.location)])

    def handle_rotation_requested(self, photo: Photo, clockwise: bool):
        print(f'rotating {photo.image_name} {"cw" if clockwise else "ccw"}')

    def handle_resize_requested(self, photo: Photo):
        print(f'resizing {photo.image_name}')

    def handle_resolution_setting_requested(self, photo: Photo):
        logger.info(f'setting scale for {photo.image_name}')

        self.scale_setting_widget.initialize(self.state.storage)

        self.image_list.setSelectionMode(QAbstractItemView.SingleSelection)

        self.switch_to_scale_setting()
        if photo.image_name != self.state.current_photo.image_name:
            idx = self.state.storage.image_names.index(photo.image_name)
            index = self.image_list_proxy_model.mapFromSource(self.image_list_model.index(idx, 0))
            self.image_list.setCurrentIndex(index)
        else:
            self.scale_setting_widget.image_viewer.set_photo(self.state.current_photo, True)

    def handle_delete_photo_requested(self, photo: Photo):
        # Ask for confirmation (warn explicitly if the action cannot be undone), and if confirmed, delete the photo from the project.
        self.close_photo_tags_widget(None)
        reply = QMessageBox.warning(self, 'Delete photo?',
                                    f'Do you really want to delete "{photo.image_name}" and all associated\nsegmentations and measurements from this project?\n\nThis action cannot be undone!',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            print(f'deleting {photo.image_name} from the project')
            # TODO: Delete the photo and all associated data (segmentations, reflections, measurements, scale,
            #  rulers...) from the project.
            #  Careful:
            #  -- if it is the currently displayed photo (switch to another one, or display an empty window if it
            #     was the last one, clear undo/redo lists, remove rulers, cancel all drawing operations in progress,
            #     e.g. drawing a polygon...)
            #  -- if any computations using the photo to be deleted are still running (e.g. getting a thumbnail,
            #     or even some plugin)
            self.measurements_viewer.model.beginResetModel()
            current_photo = self.state.current_photo
            current_index = self.image_list.currentIndex()

            next_photo_name = ""

            if self.image_list_proxy_model.rowCount() == 1:
                # Deleting the last photo in a particular (un)filtered view
                logger.info('after deletion there are no more photos (either due to filtering or all photos have been deleted), setting image viewer to None')
                self.label_editor.image_viewer.set_photo(None, True)
                self.state.current_photo = None
            else:
                # If deleting the currently selected photo, compute the next photo that should be displayed and show it
                if photo.image_name == current_photo.image_name:
                    if current_index.row() > 0:
                        new_photo_index = current_index.row() - 1
                    else:
                        new_photo_index = current_index.row() + 1
                    index_to_set = self.image_list_proxy_model.index(new_photo_index, 0)
                    index_to_set_unmapped = self.image_list_proxy_model.mapToSource(index_to_set)
                    next_photo_name = index_to_set_unmapped.data(ROLE_IMAGE_NAME)
                    # self.fetch_photo(index_to_set_unmapped.row())
                else:
                    next_photo_name = self.state.current_photo.image_name

            if not self.state.storage.delete_photo(photo.image_name, self):
                return
            # TODO implement deleting thumbnails from ThumbnailStorage
            # self.thumbnail_storage = None
            # self.thumbnail_storage.initialize(self.state.storage)
            # self.image_list_model.initialize(self.storage.image_paths, self.thumbnail_storage, 0, self.state.storage)

            if next_photo_name != "":
                self.state.current_photo = None
                index = self.state.storage.image_names.index(next_photo_name)
                self.fetch_photo(index)

            self.measurements_viewer.model.update_model()
            self.measurements_viewer.model.endResetModel()
            self.update_applyToUnsegmented_state()

    def show_photo(self, photo: Photo):
        idx = self.storage.image_names.index(photo.image_name)
        source_index = self.image_list_model.index(idx, 0)
        proxy_index = self.image_list_proxy_model.mapFromSource(source_index)
        self.image_list.setCurrentIndex(proxy_index)

    def enable_actionSave(self):
        self.ui.actionSave.setEnabled(True)

    def _handle_label_image_changed(self, lbl_img: LabelImg):
        self.enable_actionSave()

    def _process_region_operation_result(self, storage: Storage, idx: int, label_imgs: typing.List[LabelImg]):
        photo = storage.get_photo_by_idx(idx, False)
        if photo.image_path == self.state.current_photo.image_path:
            commands = []
            for lab_img in label_imgs:
                photo[lab_img.label_info.name].is_segmented = lab_img.is_segmented
                cmd = generate_change_command(self.state.current_photo[lab_img.label_semantic], lab_img.label_image)
                cmd.image_name = photo.image_name
                cmd.label_name = lab_img.label_semantic
                commands.append(cmd)
            self.command_executor.do_commands(commands)
            self.state.label_img_changed.emit(self.state.current_photo['Labels'])
            print('setting the current photo')
            # self.label_editor.set_photo2(self.state.current_photo, reset_view=False)
            self.label_editor.image_viewer.set_photo(self.state.current_photo, False)
        else:
            _photo = self.storage.get_photo_by_name(photo.image_name)
            for lab_img in label_imgs:
                _photo[lab_img.label_semantic].label_image = lab_img.label_image
        self.label_editor.cmd_executor.undo_manager.get_undo_redo(photo.image_name, '').clear_redo()

    def _region_comp_operation(self, reg_comp: RegionComputation):
        def execute(storage: Storage, idx: int):
            photo = storage.get_photo_by_idx(idx, True)
            return reg_comp(photo)
        return execute

    def compute_regions3(self, reg_comp: RegionComputation, process_mode: ProcessType):
        if process_mode == ProcessType.ALL_PHOTOS:
            img_idxs = list(range(self.state.storage.image_count))
        elif process_mode == ProcessType.SELECTED_PHOTOS:
            img_idxs = [self.image_list_proxy_model.mapToSource(index).row() for index in self.image_list.selectionModel().selectedIndexes()]
        else:
            img_idxs = []
            for i in range(self.state.storage.image_count):
                photo = self.state.storage.get_photo_by_idx(i, False)
                if not photo.has_segmentation_for(self.state.storage.default_label_image):
                    img_idxs.append(i)
        block_op = BlockingOperation(self.state.storage, img_idxs,
                                     self._region_comp_operation(reg_comp),
                                     self._process_region_operation_result, parent=self)
        block_op.start()
        self.state.current_photo = self.state.storage.get_photo_by_name(self.state.current_photo.image_name)
        self.update_applyToUnsegmented_state()

    def switch_to_scale_setting(self):
        # self.label_editor.disable()
        #
        # self.label_editor.image_viewer.hide()
        # self.label_editor.ui.photo_view.removeWidget(self.label_editor.image_viewer)
        # self.label_editor.ui.photo_view.insertWidget(0, self.scale_setting_widget)
        #
        # self.image_list.setItemDelegate(self.scale_thumbnail_delegate)

        self.scale_setting_widget.showMaximized()

        self.current_image_viewer = self.scale_setting_widget.image_viewer  # TODO unify image viewer and change only the context around it
        # self.hide_thumb_gui()
        # self.image_list.entered.disconnect(self.show_thumbnail_gui)
        # self.image_list.view_left.disconnect(self.hide_thumb_gui)

        # self.ui.tabWidget.setTabText(0, "Scale setting")

    def switch_to_label_editor(self):
        self.scale_setting_widget.hide()
        # self.label_editor.ui.photo_view.removeWidget(self.scale_setting_widget)
        # self.label_editor.ui.photo_view.insertWidget(0, self.label_editor.image_viewer)

        self.current_image_viewer = self.label_editor.image_viewer

        # self.image_list.setItemDelegate(self.thumbnail_delegate)

        self.label_editor.image_viewer.set_photo(self.state.current_photo, True)

        # self.label_editor.image_viewer.show()

        # self.image_list.entered.connect(self.show_thumbnail_gui)
        # self.image_list.view_left.connect(self.hide_thumb_gui)
        #
        # self.ui.tabWidget.setTabText(0, "Label editor")


if __name__ == "__main__":
    app = QApplication([])
    window = ArthropodDescriber()
    QTimer.singleShot(100, window.showMaximized)
    sys.exit(app.exec_())
