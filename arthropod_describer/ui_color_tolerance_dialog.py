# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'color_tolerance_dialog.ui'
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


class Ui_ColorToleranceDialog(object):
    def setupUi(self, ColorToleranceDialog):
        if not ColorToleranceDialog.objectName():
            ColorToleranceDialog.setObjectName(u"ColorToleranceDialog")
        ColorToleranceDialog.resize(377, 377)
        self.verticalLayout = QVBoxLayout(ColorToleranceDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.colorLayout = QVBoxLayout()
        self.colorLayout.setObjectName(u"colorLayout")
        self.colorLayout.setContentsMargins(30, 30, 30, 30)
        self.lblColor = QLabel(ColorToleranceDialog)
        self.lblColor.setObjectName(u"lblColor")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblColor.sizePolicy().hasHeightForWidth())
        self.lblColor.setSizePolicy(sizePolicy)
        self.lblColor.setMinimumSize(QSize(72, 72))

        self.colorLayout.addWidget(self.lblColor)

        self.btnSetColor = QPushButton(ColorToleranceDialog)
        self.btnSetColor.setObjectName(u"btnSetColor")

        self.colorLayout.addWidget(self.btnSetColor)


        self.horizontalLayout.addLayout(self.colorLayout)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, 50, -1, -1)
        self.lblSelectedColor = QLabel(ColorToleranceDialog)
        self.lblSelectedColor.setObjectName(u"lblSelectedColor")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.lblSelectedColor)

        self.lblSelectedRange = QLabel(ColorToleranceDialog)
        self.lblSelectedRange.setObjectName(u"lblSelectedRange")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.lblSelectedRange)

        self.spinBoxHueTolerance = QSpinBox(ColorToleranceDialog)
        self.spinBoxHueTolerance.setObjectName(u"spinBoxHueTolerance")
        self.spinBoxHueTolerance.setMaximum(180)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.spinBoxHueTolerance)

        self.lblHue = QLabel(ColorToleranceDialog)
        self.lblHue.setObjectName(u"lblHue")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.lblHue)

        self.spinBoxSaturationTolerance = QSpinBox(ColorToleranceDialog)
        self.spinBoxSaturationTolerance.setObjectName(u"spinBoxSaturationTolerance")
        self.spinBoxSaturationTolerance.setMaximum(255)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.spinBoxSaturationTolerance)

        self.lblSaturation = QLabel(ColorToleranceDialog)
        self.lblSaturation.setObjectName(u"lblSaturation")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.lblSaturation)

        self.spinBoxValueTolerance = QSpinBox(ColorToleranceDialog)
        self.spinBoxValueTolerance.setObjectName(u"spinBoxValueTolerance")
        self.spinBoxValueTolerance.setMaximum(255)

        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.spinBoxValueTolerance)

        self.lblValue = QLabel(ColorToleranceDialog)
        self.lblValue.setObjectName(u"lblValue")

        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.lblValue)

        self.lblHSTolerancePreview = QLabel(ColorToleranceDialog)
        self.lblHSTolerancePreview.setObjectName(u"lblHSTolerancePreview")
        sizePolicy.setHeightForWidth(self.lblHSTolerancePreview.sizePolicy().hasHeightForWidth())
        self.lblHSTolerancePreview.setSizePolicy(sizePolicy)
        self.lblHSTolerancePreview.setMinimumSize(QSize(72, 72))

        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.lblHSTolerancePreview)

        self.sliderPreviewV = QSlider(ColorToleranceDialog)
        self.sliderPreviewV.setObjectName(u"sliderPreviewV")
        self.sliderPreviewV.setOrientation(Qt.Horizontal)

        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.sliderPreviewV)

        self.checkBoxAnimate = QCheckBox(ColorToleranceDialog)
        self.checkBoxAnimate.setObjectName(u"checkBoxAnimate")
        self.checkBoxAnimate.setChecked(True)

        self.formLayout.setWidget(7, QFormLayout.FieldRole, self.checkBoxAnimate)

        self.lblVTolerancePreview = QLabel(ColorToleranceDialog)
        self.lblVTolerancePreview.setObjectName(u"lblVTolerancePreview")
        sizePolicy.setHeightForWidth(self.lblVTolerancePreview.sizePolicy().hasHeightForWidth())
        self.lblVTolerancePreview.setSizePolicy(sizePolicy)
        self.lblVTolerancePreview.setMinimumSize(QSize(72, 32))

        self.formLayout.setWidget(8, QFormLayout.FieldRole, self.lblVTolerancePreview)


        self.horizontalLayout.addLayout(self.formLayout)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(ColorToleranceDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(ColorToleranceDialog)

        QMetaObject.connectSlotsByName(ColorToleranceDialog)
    # setupUi

    def retranslateUi(self, ColorToleranceDialog):
        ColorToleranceDialog.setWindowTitle(QCoreApplication.translate("ColorToleranceDialog", u"Select Color and Tolerance", None))
        self.lblColor.setText("")
        self.btnSetColor.setText(QCoreApplication.translate("ColorToleranceDialog", u"Set color", None))
        self.lblSelectedColor.setText(QCoreApplication.translate("ColorToleranceDialog", u"Selected color", None))
        self.lblSelectedRange.setText(QCoreApplication.translate("ColorToleranceDialog", u"Selected range", None))
        self.lblHue.setText(QCoreApplication.translate("ColorToleranceDialog", u"Hue Tolerance", None))
        self.lblSaturation.setText(QCoreApplication.translate("ColorToleranceDialog", u"Saturation Tolerance", None))
        self.lblValue.setText(QCoreApplication.translate("ColorToleranceDialog", u"Value Tolerance", None))
        self.lblHSTolerancePreview.setText("")
        self.checkBoxAnimate.setText(QCoreApplication.translate("ColorToleranceDialog", u"Animate Value Range Preview", None))
        self.lblVTolerancePreview.setText("")
    # retranslateUi

