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
        ColormapWidget.resize(475, 216)
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
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.leftLabel.addWidget(self.label, 0, Qt.AlignHCenter|Qt.AlignTop)

        self.leftComboBox = QComboBox(self.groupBox)
        self.leftComboBox.setObjectName(u"leftComboBox")
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leftComboBox.sizePolicy().hasHeightForWidth())
        self.leftComboBox.setSizePolicy(sizePolicy)
        self.leftComboBox.setInsertPolicy(QComboBox.InsertAtBottom)
        self.leftComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.leftLabel.addWidget(self.leftComboBox)

        self.lblLeftLabelName = QLabel(self.groupBox)
        self.lblLeftLabelName.setObjectName(u"lblLeftLabelName")

        self.leftLabel.addWidget(self.lblLeftLabelName, 0, Qt.AlignHCenter|Qt.AlignTop)


        self.LabelChooser.addLayout(self.leftLabel)

        self.rightLabel = QVBoxLayout()
        self.rightLabel.setObjectName(u"rightLabel")
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.rightLabel.addWidget(self.label_2, 0, Qt.AlignHCenter|Qt.AlignTop)

        self.rightComboBox = QComboBox(self.groupBox)
        self.rightComboBox.setObjectName(u"rightComboBox")
        sizePolicy.setHeightForWidth(self.rightComboBox.sizePolicy().hasHeightForWidth())
        self.rightComboBox.setSizePolicy(sizePolicy)
        self.rightComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.rightLabel.addWidget(self.rightComboBox)

        self.lblRightLabelName = QLabel(self.groupBox)
        self.lblRightLabelName.setObjectName(u"lblRightLabelName")

        self.rightLabel.addWidget(self.lblRightLabelName, 0, Qt.AlignHCenter|Qt.AlignTop)


        self.LabelChooser.addLayout(self.rightLabel)


        self.verticalLayout.addLayout(self.LabelChooser)

        self.btnSwapLabels = QPushButton(self.groupBox)
        self.btnSwapLabels.setObjectName(u"btnSwapLabels")

        self.verticalLayout.addWidget(self.btnSwapLabels)


        self.verticalLayout_2.addWidget(self.groupBox)


        self.retranslateUi(ColormapWidget)

        QMetaObject.connectSlotsByName(ColormapWidget)
    # setupUi

    def retranslateUi(self, ColormapWidget):
        ColormapWidget.setWindowTitle(QCoreApplication.translate("ColormapWidget", u"LabelWidget", None))
        self.groupBox.setTitle(QCoreApplication.translate("ColormapWidget", u"Colormap and labels", None))
        self.label_3.setText(QCoreApplication.translate("ColormapWidget", u"Active colormap", None))
        self.label.setText(QCoreApplication.translate("ColormapWidget", u"Left", None))
        self.lblLeftLabelName.setText("")
        self.label_2.setText(QCoreApplication.translate("ColormapWidget", u"Right", None))
        self.lblRightLabelName.setText("")
        self.btnSwapLabels.setText(QCoreApplication.translate("ColormapWidget", u"Swap labels", None))
    # retranslateUi

