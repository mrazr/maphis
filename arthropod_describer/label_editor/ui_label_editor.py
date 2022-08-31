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
        LabelEditor.resize(1220, 704)
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
        self.tbtnUndo.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.toolBar.addWidget(self.tbtnUndo)

        self.tbtnRedo = QToolButton(LabelEditor)
        self.tbtnRedo.setObjectName(u"tbtnRedo")
        self.tbtnRedo.setEnabled(False)
        self.tbtnRedo.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.toolBar.addWidget(self.tbtnRedo)

        self.toolBox = QGroupBox(LabelEditor)
        self.toolBox.setObjectName(u"toolBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.toolBox.sizePolicy().hasHeightForWidth())
        self.toolBox.setSizePolicy(sizePolicy1)
        self.toolBox.setFlat(False)
        self.toolBox.setCheckable(False)
        self.horizontalLayout = QHBoxLayout(self.toolBox)
        self.horizontalLayout.setObjectName(u"horizontalLayout")

        self.toolBar.addWidget(self.toolBox)

        self.MaskGroup = QGroupBox(LabelEditor)
        self.MaskGroup.setObjectName(u"MaskGroup")
        sizePolicy1.setHeightForWidth(self.MaskGroup.sizePolicy().hasHeightForWidth())
        self.MaskGroup.setSizePolicy(sizePolicy1)
        self.horizontalLayout_2 = QHBoxLayout(self.MaskGroup)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.toolBar.addWidget(self.MaskGroup)

        self.grpMaskStyle = QGroupBox(LabelEditor)
        self.grpMaskStyle.setObjectName(u"grpMaskStyle")
        sizePolicy1.setHeightForWidth(self.grpMaskStyle.sizePolicy().hasHeightForWidth())
        self.grpMaskStyle.setSizePolicy(sizePolicy1)
        self.grpMaskStyle.setFlat(False)
        self.grpMaskStyle.setCheckable(False)
        self.horizontalLayout_3 = QHBoxLayout(self.grpMaskStyle)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, -1, -1, -1)
        self.label_2 = QLabel(self.grpMaskStyle)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)

        self.sliderOpacity = QSlider(self.grpMaskStyle)
        self.sliderOpacity.setObjectName(u"sliderOpacity")
        self.sliderOpacity.setMaximum(100)
        self.sliderOpacity.setSingleStep(5)
        self.sliderOpacity.setValue(75)
        self.sliderOpacity.setOrientation(Qt.Horizontal)
        self.sliderOpacity.setTickPosition(QSlider.TicksBelow)
        self.sliderOpacity.setTickInterval(15)

        self.verticalLayout_2.addWidget(self.sliderOpacity)


        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.btnFilledStyle = QRadioButton(self.grpMaskStyle)
        self.btnFilledStyle.setObjectName(u"btnFilledStyle")
        self.btnFilledStyle.setCheckable(True)
        self.btnFilledStyle.setChecked(True)
        self.btnFilledStyle.setAutoExclusive(True)

        self.horizontalLayout_3.addWidget(self.btnFilledStyle, 0, Qt.AlignVCenter)

        self.btnOutlineStyle = QRadioButton(self.grpMaskStyle)
        self.btnOutlineStyle.setObjectName(u"btnOutlineStyle")
        self.btnOutlineStyle.setCheckable(True)
        self.btnOutlineStyle.setAutoExclusive(True)

        self.horizontalLayout_3.addWidget(self.btnOutlineStyle)

        self.label = QLabel(self.grpMaskStyle)
        self.label.setObjectName(u"label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)

        self.horizontalLayout_3.addWidget(self.label)

        self.spinOutlineWidth = QSpinBox(self.grpMaskStyle)
        self.spinOutlineWidth.setObjectName(u"spinOutlineWidth")
        self.spinOutlineWidth.setEnabled(False)
        self.spinOutlineWidth.setMinimum(1)
        self.spinOutlineWidth.setMaximum(7)
        self.spinOutlineWidth.setValue(3)

        self.horizontalLayout_3.addWidget(self.spinOutlineWidth)


        self.toolBar.addWidget(self.grpMaskStyle)

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
        self.hspcLeft = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.controls.addItem(self.hspcLeft)

        self.layoutLabelInfo = QHBoxLayout()
        self.layoutLabelInfo.setObjectName(u"layoutLabelInfo")
        self.layoutLabelInfo.setContentsMargins(0, -1, -1, -1)
        self.lblHovered = QLabel(LabelEditor)
        self.lblHovered.setObjectName(u"lblHovered")

        self.layoutLabelInfo.addWidget(self.lblHovered)

        self.lblLabelIcon = QLabel(LabelEditor)
        self.lblLabelIcon.setObjectName(u"lblLabelIcon")

        self.layoutLabelInfo.addWidget(self.lblLabelIcon)

        self.lblLabelInfo = QLabel(LabelEditor)
        self.lblLabelInfo.setObjectName(u"lblLabelInfo")

        self.layoutLabelInfo.addWidget(self.lblLabelInfo)


        self.controls.addLayout(self.layoutLabelInfo)

        self.hspcRight = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.controls.addItem(self.hspcRight)


        self.photo_view.addLayout(self.controls)


        self.center.addLayout(self.photo_view)


        self.verticalLayout.addLayout(self.center)


        self.retranslateUi(LabelEditor)

        QMetaObject.connectSlotsByName(LabelEditor)
    # setupUi

    def retranslateUi(self, LabelEditor):
        LabelEditor.setWindowTitle(QCoreApplication.translate("LabelEditor", u"Form", None))
        self.tbtnUndo.setText(QCoreApplication.translate("LabelEditor", u"Undo", None))
        self.tbtnRedo.setText(QCoreApplication.translate("LabelEditor", u"Redo", None))
        self.toolBox.setTitle(QCoreApplication.translate("LabelEditor", u"Mask tools", None))
        self.MaskGroup.setTitle(QCoreApplication.translate("LabelEditor", u"Active mask", None))
        self.grpMaskStyle.setTitle(QCoreApplication.translate("LabelEditor", u"Mask style", None))
        self.label_2.setText(QCoreApplication.translate("LabelEditor", u"Opacity", None))
        self.btnFilledStyle.setText(QCoreApplication.translate("LabelEditor", u"Filled", None))
        self.btnOutlineStyle.setText(QCoreApplication.translate("LabelEditor", u"Outline", None))
        self.label.setText(QCoreApplication.translate("LabelEditor", u"Width", None))
        self.spinOutlineWidth.setSuffix(QCoreApplication.translate("LabelEditor", u"px", None))
        self.lblHovered.setText(QCoreApplication.translate("LabelEditor", u"Hovered label:", None))
        self.lblLabelIcon.setText("")
        self.lblLabelInfo.setText("")
    # retranslateUi

