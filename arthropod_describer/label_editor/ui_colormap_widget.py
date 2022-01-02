# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'colormap_widget.ui'
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


class Ui_ColormapWidget(object):
    def setupUi(self, ColormapWidget):
        if not ColormapWidget.objectName():
            ColormapWidget.setObjectName(u"ColormapWidget")
        ColormapWidget.resize(475, 264)
        self.verticalLayout_2 = QVBoxLayout(ColormapWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.groupBox = QGroupBox(ColormapWidget)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.colormapComboBox = QComboBox(self.groupBox)
        self.colormapComboBox.setObjectName(u"colormapComboBox")

        self.verticalLayout.addWidget(self.colormapComboBox)

        self.LabelChooser = QHBoxLayout()
        self.LabelChooser.setObjectName(u"LabelChooser")
        self.leftLabel = QVBoxLayout()
        self.leftLabel.setObjectName(u"leftLabel")
        self.currentLabelLeft = QLabel(self.groupBox)
        self.currentLabelLeft.setObjectName(u"currentLabelLeft")

        self.leftLabel.addWidget(self.currentLabelLeft, 0, Qt.AlignHCenter|Qt.AlignTop)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.labelIndicator = QLabel(self.groupBox)
        self.labelIndicator.setObjectName(u"labelIndicator")
        self.labelIndicator.setStyleSheet(u"border-color: rgb(0, 0, 0);\n"
"border-size: 1px;")

        self.horizontalLayout.addWidget(self.labelIndicator)

        self.leftComboBox = QComboBox(self.groupBox)
        self.leftComboBox.setObjectName(u"leftComboBox")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leftComboBox.sizePolicy().hasHeightForWidth())
        self.leftComboBox.setSizePolicy(sizePolicy)
        self.leftComboBox.setInsertPolicy(QComboBox.InsertAtBottom)
        self.leftComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.horizontalLayout.addWidget(self.leftComboBox)


        self.leftLabel.addLayout(self.horizontalLayout)

        self.lblLeftLabelName = QLabel(self.groupBox)
        self.lblLeftLabelName.setObjectName(u"lblLeftLabelName")

        self.leftLabel.addWidget(self.lblLeftLabelName, 0, Qt.AlignHCenter|Qt.AlignTop)


        self.LabelChooser.addLayout(self.leftLabel)


        self.verticalLayout.addLayout(self.LabelChooser)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout.addWidget(self.label_4)

        self.opacitySlider = QSlider(self.groupBox)
        self.opacitySlider.setObjectName(u"opacitySlider")
        self.opacitySlider.setMaximum(100)
        self.opacitySlider.setValue(20)
        self.opacitySlider.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.opacitySlider)


        self.verticalLayout_2.addWidget(self.groupBox)


        self.retranslateUi(ColormapWidget)

        QMetaObject.connectSlotsByName(ColormapWidget)
    # setupUi

    def retranslateUi(self, ColormapWidget):
        ColormapWidget.setWindowTitle(QCoreApplication.translate("ColormapWidget", u"LabelWidget", None))
        self.groupBox.setTitle(QCoreApplication.translate("ColormapWidget", u"Colormap and labels", None))
        self.label_3.setText(QCoreApplication.translate("ColormapWidget", u"Active colormap", None))
        self.currentLabelLeft.setText(QCoreApplication.translate("ColormapWidget", u"Current label", None))
        self.labelIndicator.setText("")
        self.lblLeftLabelName.setText("")
        self.label_4.setText(QCoreApplication.translate("ColormapWidget", u"Label opacity", None))
    # retranslateUi

