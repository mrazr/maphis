# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'image_controls.ui'
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


class Ui_ImageControls(object):
    def setupUi(self, ImageControls):
        if not ImageControls.objectName():
            ImageControls.setObjectName(u"ImageControls")
        ImageControls.resize(400, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ImageControls.sizePolicy().hasHeightForWidth())
        ImageControls.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(ImageControls)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.grpImageControls = QGroupBox(ImageControls)
        self.grpImageControls.setObjectName(u"grpImageControls")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.grpImageControls.sizePolicy().hasHeightForWidth())
        self.grpImageControls.setSizePolicy(sizePolicy1)
        self.horizontalLayout_4 = QHBoxLayout(self.grpImageControls)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.tbtnRotateCCW = QToolButton(self.grpImageControls)
        self.tbtnRotateCCW.setObjectName(u"tbtnRotateCCW")
        self.tbtnRotateCCW.setIconSize(QSize(24, 24))

        self.horizontalLayout_4.addWidget(self.tbtnRotateCCW)

        self.tbtnRotateCW = QToolButton(self.grpImageControls)
        self.tbtnRotateCW.setObjectName(u"tbtnRotateCW")
        self.tbtnRotateCW.setIconSize(QSize(24, 24))

        self.horizontalLayout_4.addWidget(self.tbtnRotateCW)

        self.cbxZoom = QComboBox(self.grpImageControls)
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.addItem("")
        self.cbxZoom.setObjectName(u"cbxZoom")
        sizePolicy1.setHeightForWidth(self.cbxZoom.sizePolicy().hasHeightForWidth())
        self.cbxZoom.setSizePolicy(sizePolicy1)
        self.cbxZoom.setEditable(True)
        self.cbxZoom.setInsertPolicy(QComboBox.NoInsert)

        self.horizontalLayout_4.addWidget(self.cbxZoom)


        self.horizontalLayout.addWidget(self.grpImageControls)


        self.retranslateUi(ImageControls)

        self.cbxZoom.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ImageControls)
    # setupUi

    def retranslateUi(self, ImageControls):
        ImageControls.setWindowTitle(QCoreApplication.translate("ImageControls", u"Form", None))
        self.grpImageControls.setTitle(QCoreApplication.translate("ImageControls", u"Image controls", None))
        self.tbtnRotateCCW.setText("")
        self.tbtnRotateCW.setText("")
        self.cbxZoom.setItemText(0, QCoreApplication.translate("ImageControls", u"Fit photo", None))
        self.cbxZoom.setItemText(1, QCoreApplication.translate("ImageControls", u"Fit specimen", None))
        self.cbxZoom.setItemText(2, QCoreApplication.translate("ImageControls", u"10%", None))
        self.cbxZoom.setItemText(3, QCoreApplication.translate("ImageControls", u"25%", None))
        self.cbxZoom.setItemText(4, QCoreApplication.translate("ImageControls", u"50%", None))
        self.cbxZoom.setItemText(5, QCoreApplication.translate("ImageControls", u"100%", None))
        self.cbxZoom.setItemText(6, QCoreApplication.translate("ImageControls", u"200%", None))
        self.cbxZoom.setItemText(7, QCoreApplication.translate("ImageControls", u"300%", None))
        self.cbxZoom.setItemText(8, QCoreApplication.translate("ImageControls", u"400%", None))

    # retranslateUi

