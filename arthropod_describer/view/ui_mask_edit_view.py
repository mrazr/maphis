# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mask_edit_view.ui'
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


class Ui_MaskEditor(object):
    def setupUi(self, MaskEditor):
        if not MaskEditor.objectName():
            MaskEditor.setObjectName(u"MaskEditor")
        MaskEditor.resize(1059, 699)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MaskEditor.sizePolicy().hasHeightForWidth())
        MaskEditor.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(MaskEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.toolBar = QHBoxLayout()
        self.toolBar.setObjectName(u"toolBar")
        self.tbtnUndo = QToolButton(MaskEditor)
        self.tbtnUndo.setObjectName(u"tbtnUndo")

        self.toolBar.addWidget(self.tbtnUndo)

        self.tbtnRedo = QToolButton(MaskEditor)
        self.tbtnRedo.setObjectName(u"tbtnRedo")

        self.toolBar.addWidget(self.tbtnRedo)

        self.groupBox = QGroupBox(MaskEditor)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.horizontalLayout = QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.tbtnBrush = QToolButton(self.groupBox)
        self.tbtnBrush.setObjectName(u"tbtnBrush")
        self.tbtnBrush.setCheckable(True)
        self.tbtnBrush.setAutoRepeat(False)
        self.tbtnBrush.setAutoExclusive(True)
        self.tbtnBrush.setAutoRaise(False)

        self.horizontalLayout.addWidget(self.tbtnBrush)

        self.tbtnBucket = QToolButton(self.groupBox)
        self.tbtnBucket.setObjectName(u"tbtnBucket")
        self.tbtnBucket.setCheckable(True)
        self.tbtnBucket.setAutoExclusive(True)

        self.horizontalLayout.addWidget(self.tbtnBucket)

        self.tbtnKnife = QToolButton(self.groupBox)
        self.tbtnKnife.setObjectName(u"tbtnKnife")
        self.tbtnKnife.setCheckable(True)
        self.tbtnKnife.setAutoExclusive(True)

        self.horizontalLayout.addWidget(self.tbtnKnife)


        self.toolBar.addWidget(self.groupBox)

        self.MaskGroup = QGroupBox(MaskEditor)
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


        self.toolBar.addWidget(self.MaskGroup)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.toolBar.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.toolBar)

        self.center = QHBoxLayout()
        self.center.setObjectName(u"center")
        self.maskEditor = QGraphicsView(MaskEditor)
        self.maskEditor.setObjectName(u"maskEditor")

        self.center.addWidget(self.maskEditor)


        self.verticalLayout.addLayout(self.center)

        self.controls = QHBoxLayout()
        self.controls.setObjectName(u"controls")
        self.btnNext = QPushButton(MaskEditor)
        self.btnNext.setObjectName(u"btnNext")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btnNext.sizePolicy().hasHeightForWidth())
        self.btnNext.setSizePolicy(sizePolicy1)

        self.controls.addWidget(self.btnNext)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.controls.addItem(self.horizontalSpacer_2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.controls.addItem(self.horizontalSpacer)

        self.btnPrevious = QPushButton(MaskEditor)
        self.btnPrevious.setObjectName(u"btnPrevious")

        self.controls.addWidget(self.btnPrevious)


        self.verticalLayout.addLayout(self.controls)


        self.retranslateUi(MaskEditor)

        QMetaObject.connectSlotsByName(MaskEditor)
    # setupUi

    def retranslateUi(self, MaskEditor):
        MaskEditor.setWindowTitle(QCoreApplication.translate("MaskEditor", u"Form", None))
        self.tbtnUndo.setText(QCoreApplication.translate("MaskEditor", u"Undo", None))
        self.tbtnRedo.setText(QCoreApplication.translate("MaskEditor", u"Redo", None))
        self.groupBox.setTitle(QCoreApplication.translate("MaskEditor", u"Mask tools", None))
        self.tbtnBrush.setText(QCoreApplication.translate("MaskEditor", u"Brush", None))
        self.tbtnBucket.setText(QCoreApplication.translate("MaskEditor", u"Bucket", None))
        self.tbtnKnife.setText(QCoreApplication.translate("MaskEditor", u"Knife", None))
        self.MaskGroup.setTitle(QCoreApplication.translate("MaskEditor", u"Active mask", None))
        self.tbtnBugMask.setText(QCoreApplication.translate("MaskEditor", u"Bug", None))
        self.tbtnSegmentsMask.setText(QCoreApplication.translate("MaskEditor", u"Segments", None))
        self.tbtnReflectionMask.setText(QCoreApplication.translate("MaskEditor", u"Reflections", None))
        self.btnNext.setText(QCoreApplication.translate("MaskEditor", u"<", None))
        self.btnPrevious.setText(QCoreApplication.translate("MaskEditor", u">", None))
    # retranslateUi

