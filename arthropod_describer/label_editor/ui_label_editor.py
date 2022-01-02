# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'label_editor.ui'
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


class Ui_LabelEditor(object):
    def setupUi(self, LabelEditor):
        if not LabelEditor.objectName():
            LabelEditor.setObjectName(u"LabelEditor")
        LabelEditor.resize(1059, 704)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LabelEditor.sizePolicy().hasHeightForWidth())
        LabelEditor.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(LabelEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.toolBar = QHBoxLayout()
        self.toolBar.setObjectName(u"toolBar")
        self.tbtnUndo = QToolButton(LabelEditor)
        self.tbtnUndo.setObjectName(u"tbtnUndo")
        self.tbtnUndo.setEnabled(False)

        self.toolBar.addWidget(self.tbtnUndo)

        self.tbtnRedo = QToolButton(LabelEditor)
        self.tbtnRedo.setObjectName(u"tbtnRedo")
        self.tbtnRedo.setEnabled(False)

        self.toolBar.addWidget(self.tbtnRedo)

        self.btnResetZoom = QPushButton(LabelEditor)
        self.btnResetZoom.setObjectName(u"btnResetZoom")

        self.toolBar.addWidget(self.btnResetZoom)

        self.btnZoomBug = QPushButton(LabelEditor)
        self.btnZoomBug.setObjectName(u"btnZoomBug")

        self.toolBar.addWidget(self.btnZoomBug)

        self.toolBox = QGroupBox(LabelEditor)
        self.toolBox.setObjectName(u"toolBox")
        self.toolBox.setFlat(False)
        self.toolBox.setCheckable(False)
        self.horizontalLayout = QHBoxLayout(self.toolBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")

        self.toolBar.addWidget(self.toolBox)

        self.MaskGroup = QGroupBox(LabelEditor)
        self.MaskGroup.setObjectName(u"MaskGroup")
        self.horizontalLayout_2 = QHBoxLayout(self.MaskGroup)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.tbtnBugMask = QToolButton(self.MaskGroup)
        self.tbtnBugMask.setObjectName(u"tbtnBugMask")
        self.tbtnBugMask.setCheckable(True)
        self.tbtnBugMask.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.tbtnBugMask)

        self.tbtnSegmentsMask = QToolButton(self.MaskGroup)
        self.tbtnSegmentsMask.setObjectName(u"tbtnSegmentsMask")
        self.tbtnSegmentsMask.setCheckable(True)
        self.tbtnSegmentsMask.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.tbtnSegmentsMask)

        self.tbtnReflectionMask = QToolButton(self.MaskGroup)
        self.tbtnReflectionMask.setObjectName(u"tbtnReflectionMask")
        self.tbtnReflectionMask.setCheckable(True)
        self.tbtnReflectionMask.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.tbtnReflectionMask)

        self.line = QFrame(self.MaskGroup)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout_2.addWidget(self.line)

        self.btnResetLabel = QPushButton(self.MaskGroup)
        self.btnResetLabel.setObjectName(u"btnResetLabel")
        self.btnResetLabel.setEnabled(False)

        self.horizontalLayout_2.addWidget(self.btnResetLabel)


        self.toolBar.addWidget(self.MaskGroup)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.toolBar.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.toolBar)

        self.center = QHBoxLayout()
        self.center.setObjectName(u"center")
        self.photo_view = QVBoxLayout()
        self.photo_view.setObjectName(u"photo_view")
        self.photo_view.setContentsMargins(0, -1, -1, 0)
        self.controls = QHBoxLayout()
        self.controls.setObjectName(u"controls")
        self.btnPrevious = QPushButton(LabelEditor)
        self.btnPrevious.setObjectName(u"btnPrevious")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnPrevious.sizePolicy().hasHeightForWidth())
        self.btnPrevious.setSizePolicy(sizePolicy1)

        self.controls.addWidget(self.btnPrevious)

        self.hspcLeft = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.controls.addItem(self.hspcLeft)

        self.hspcRight = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.controls.addItem(self.hspcRight)

        self.btnNext = QPushButton(LabelEditor)
        self.btnNext.setObjectName(u"btnNext")

        self.controls.addWidget(self.btnNext)


        self.photo_view.addLayout(self.controls)


        self.center.addLayout(self.photo_view)

        self.tabSidebar = QTabWidget(LabelEditor)
        self.tabSidebar.setObjectName(u"tabSidebar")
        self.tabEditing = QWidget()
        self.tabEditing.setObjectName(u"tabEditing")
        self.tabSidebar.addTab(self.tabEditing, "")
        self.tabPlugins = QWidget()
        self.tabPlugins.setObjectName(u"tabPlugins")
        self.tabSidebar.addTab(self.tabPlugins, "")

        self.center.addWidget(self.tabSidebar)


        self.verticalLayout.addLayout(self.center)


        self.retranslateUi(LabelEditor)

        self.tabSidebar.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(LabelEditor)
    # setupUi

    def retranslateUi(self, LabelEditor):
        LabelEditor.setWindowTitle(QCoreApplication.translate("LabelEditor", u"Form", None))
        self.tbtnUndo.setText(QCoreApplication.translate("LabelEditor", u"Undo", None))
        self.tbtnRedo.setText(QCoreApplication.translate("LabelEditor", u"Redo", None))
        self.btnResetZoom.setText(QCoreApplication.translate("LabelEditor", u"Reset zoom", None))
        self.btnZoomBug.setText(QCoreApplication.translate("LabelEditor", u"Zoom on bug", None))
        self.toolBox.setTitle(QCoreApplication.translate("LabelEditor", u"Mask tools", None))
        self.MaskGroup.setTitle(QCoreApplication.translate("LabelEditor", u"Active mask", None))
        self.tbtnBugMask.setText(QCoreApplication.translate("LabelEditor", u"Bug", None))
        self.tbtnSegmentsMask.setText(QCoreApplication.translate("LabelEditor", u"Segments", None))
        self.tbtnReflectionMask.setText(QCoreApplication.translate("LabelEditor", u"Reflections", None))
        self.btnResetLabel.setText(QCoreApplication.translate("LabelEditor", u"Reset", None))
        self.btnPrevious.setText(QCoreApplication.translate("LabelEditor", u"<", None))
        self.btnNext.setText(QCoreApplication.translate("LabelEditor", u">", None))
        self.tabSidebar.setTabText(self.tabSidebar.indexOf(self.tabEditing), QCoreApplication.translate("LabelEditor", u"Editing", None))
        self.tabSidebar.setTabText(self.tabSidebar.indexOf(self.tabPlugins), QCoreApplication.translate("LabelEditor", u"Plugins", None))
    # retranslateUi

