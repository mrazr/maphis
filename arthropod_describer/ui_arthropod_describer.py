# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'arthropod_describer.ui'
##
## Created by: Qt User Interface Compiler version 5.14.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *


class Ui_ArhtropodDescriber(object):
    def setupUi(self, ArhtropodDescriber):
        if not ArhtropodDescriber.objectName():
            ArhtropodDescriber.setObjectName(u"ArhtropodDescriber")
        ArhtropodDescriber.resize(925, 481)
        self.actionCreateProject = QAction(ArhtropodDescriber)
        self.actionCreateProject.setObjectName(u"actionCreateProject")
        self.actionOpenProject = QAction(ArhtropodDescriber)
        self.actionOpenProject.setObjectName(u"actionOpenProject")
        self.actionRecentlyOpened = QAction(ArhtropodDescriber)
        self.actionRecentlyOpened.setObjectName(u"actionRecentlyOpened")
        self.actionRecentlyOpened.setEnabled(False)
        self.actionImportPhotos = QAction(ArhtropodDescriber)
        self.actionImportPhotos.setObjectName(u"actionImportPhotos")
        self.actionImportPhotos.setEnabled(False)
        self.actionVersion = QAction(ArhtropodDescriber)
        self.actionVersion.setObjectName(u"actionVersion")
        self.actionUndo = QAction(ArhtropodDescriber)
        self.actionUndo.setObjectName(u"actionUndo")
        self.actionRedo = QAction(ArhtropodDescriber)
        self.actionRedo.setObjectName(u"actionRedo")
        self.actionRedo.setShortcutContext(Qt.WindowShortcut)
        self.actionOpen_project_folder = QAction(ArhtropodDescriber)
        self.actionOpen_project_folder.setObjectName(u"actionOpen_project_folder")
        self.actionOpen_project_folder.setEnabled(False)
        self.actionExit = QAction(ArhtropodDescriber)
        self.actionExit.setObjectName(u"actionExit")
        self.actionSave = QAction(ArhtropodDescriber)
        self.actionSave.setObjectName(u"actionSave")
        self.actionSave.setEnabled(False)
        self.centralwidget = QWidget(ArhtropodDescriber)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.imageListLayout = QVBoxLayout()
        self.imageListLayout.setObjectName(u"imageListLayout")
        self.imageListLayout.setContentsMargins(0, -1, -1, -1)
        self.tagsLayout = QHBoxLayout()
        self.tagsLayout.setObjectName(u"tagsLayout")
        self.tagsLayout.setContentsMargins(-1, 0, -1, -1)
        self.lblTagFilter = QLabel(self.centralwidget)
        self.lblTagFilter.setObjectName(u"lblTagFilter")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblTagFilter.sizePolicy().hasHeightForWidth())
        self.lblTagFilter.setSizePolicy(sizePolicy)

        self.tagsLayout.addWidget(self.lblTagFilter)

        self.cmbTags = QComboBox(self.centralwidget)
        self.cmbTags.setObjectName(u"cmbTags")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cmbTags.sizePolicy().hasHeightForWidth())
        self.cmbTags.setSizePolicy(sizePolicy1)

        self.tagsLayout.addWidget(self.cmbTags)


        self.imageListLayout.addLayout(self.tagsLayout)

        self.imageListView = QListView(self.centralwidget)
        self.imageListView.setObjectName(u"imageListView")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.imageListView.sizePolicy().hasHeightForWidth())
        self.imageListView.setSizePolicy(sizePolicy2)
        self.imageListView.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.imageListView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.imageListView.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.imageListLayout.addWidget(self.imageListView)


        self.horizontalLayout.addLayout(self.imageListLayout)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy3)
        self.tabLabelEditor = QWidget()
        self.tabLabelEditor.setObjectName(u"tabLabelEditor")
        self.tabWidget.addTab(self.tabLabelEditor, "")
        self.tabMeasurements = QWidget()
        self.tabMeasurements.setObjectName(u"tabMeasurements")
        self.tabWidget.addTab(self.tabMeasurements, "")

        self.horizontalLayout.addWidget(self.tabWidget)

        ArhtropodDescriber.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(ArhtropodDescriber)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 925, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuAbout = QMenu(self.menubar)
        self.menuAbout.setObjectName(u"menuAbout")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName(u"menuEdit")
        ArhtropodDescriber.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(ArhtropodDescriber)
        self.statusbar.setObjectName(u"statusbar")
        ArhtropodDescriber.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuAbout.menuAction())
        self.menuFile.addAction(self.actionCreateProject)
        self.menuFile.addAction(self.actionOpenProject)
        self.menuFile.addAction(self.actionRecentlyOpened)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionImportPhotos)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionOpen_project_folder)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuAbout.addAction(self.actionVersion)
        self.menuEdit.addAction(self.actionUndo)
        self.menuEdit.addAction(self.actionRedo)

        self.retranslateUi(ArhtropodDescriber)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ArhtropodDescriber)
    # setupUi

    def retranslateUi(self, ArhtropodDescriber):
        ArhtropodDescriber.setWindowTitle(QCoreApplication.translate("ArhtropodDescriber", u"Arthropod Describer", None))
        self.actionCreateProject.setText(QCoreApplication.translate("ArhtropodDescriber", u"&New project...", None))
#if QT_CONFIG(shortcut)
        self.actionCreateProject.setShortcut(QCoreApplication.translate("ArhtropodDescriber", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpenProject.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Open project...", None))
#if QT_CONFIG(shortcut)
        self.actionOpenProject.setShortcut(QCoreApplication.translate("ArhtropodDescriber", u"Ctrl+O", None))
#endif // QT_CONFIG(shortcut)
        self.actionRecentlyOpened.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Recent projects", None))
        self.actionImportPhotos.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Import photos...", None))
#if QT_CONFIG(shortcut)
        self.actionImportPhotos.setShortcut(QCoreApplication.translate("ArhtropodDescriber", u"Ctrl+I", None))
#endif // QT_CONFIG(shortcut)
        self.actionVersion.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Version", None))
        self.actionUndo.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Undo", None))
#if QT_CONFIG(shortcut)
        self.actionUndo.setShortcut(QCoreApplication.translate("ArhtropodDescriber", u"Ctrl+Z", None))
#endif // QT_CONFIG(shortcut)
        self.actionRedo.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Redo", None))
#if QT_CONFIG(shortcut)
        self.actionRedo.setShortcut(QCoreApplication.translate("ArhtropodDescriber", u"Ctrl+Y", None))
#endif // QT_CONFIG(shortcut)
        self.actionOpen_project_folder.setText(QCoreApplication.translate("ArhtropodDescriber", u"Show project &folder in explorer", None))
        self.actionExit.setText(QCoreApplication.translate("ArhtropodDescriber", u"E&xit", None))
        self.actionSave.setText(QCoreApplication.translate("ArhtropodDescriber", u"&Save", None))
#if QT_CONFIG(shortcut)
        self.actionSave.setShortcut(QCoreApplication.translate("ArhtropodDescriber", u"Ctrl+S", None))
#endif // QT_CONFIG(shortcut)
        self.lblTagFilter.setText(QCoreApplication.translate("ArhtropodDescriber", u"Tag filter:", None))
        self.cmbTags.setCurrentText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabLabelEditor), QCoreApplication.translate("ArhtropodDescriber", u"Label editor", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabMeasurements), QCoreApplication.translate("ArhtropodDescriber", u"Measurements", None))
        self.menuFile.setTitle(QCoreApplication.translate("ArhtropodDescriber", u"&File", None))
        self.menuAbout.setTitle(QCoreApplication.translate("ArhtropodDescriber", u"&About", None))
        self.menuEdit.setTitle(QCoreApplication.translate("ArhtropodDescriber", u"&Edit", None))
    # retranslateUi

