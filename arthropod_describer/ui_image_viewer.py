# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'image_viewer.ui'
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


class Ui_ImageViewer(object):
    def setupUi(self, ImageViewer):
        if not ImageViewer.objectName():
            ImageViewer.setObjectName(u"ImageViewer")
        ImageViewer.resize(1020, 621)
        self.verticalLayout = QVBoxLayout(ImageViewer)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.controlBarContainer = QVBoxLayout()
        self.controlBarContainer.setObjectName(u"controlBarContainer")
        self.controlBar = QHBoxLayout()
        self.controlBar.setObjectName(u"controlBar")
        self.grpImageControls = QGroupBox(ImageViewer)
        self.grpImageControls.setObjectName(u"grpImageControls")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.grpImageControls.sizePolicy().hasHeightForWidth())
        self.grpImageControls.setSizePolicy(sizePolicy)
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

        self.label = QLabel(self.grpImageControls)
        self.label.setObjectName(u"label")

        self.horizontalLayout_4.addWidget(self.label)

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
        self.cbxZoom.setEditable(True)
        self.cbxZoom.setInsertPolicy(QComboBox.NoInsert)

        self.horizontalLayout_4.addWidget(self.cbxZoom)


        self.controlBar.addWidget(self.grpImageControls)


        self.controlBarContainer.addLayout(self.controlBar)


        self.verticalLayout.addLayout(self.controlBarContainer)

        self.viewFrame = QFrame(ImageViewer)
        self.viewFrame.setObjectName(u"viewFrame")
        self.viewFrame.setFrameShape(QFrame.StyledPanel)
        self.viewFrame.setFrameShadow(QFrame.Raised)

        self.verticalLayout.addWidget(self.viewFrame)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.tbtnFirst = QToolButton(ImageViewer)
        self.tbtnFirst.setObjectName(u"tbtnFirst")

        self.horizontalLayout.addWidget(self.tbtnFirst)

        self.tbtnPrev = QToolButton(ImageViewer)
        self.tbtnPrev.setObjectName(u"tbtnPrev")

        self.horizontalLayout.addWidget(self.tbtnPrev)

        self.tbtnNext = QToolButton(ImageViewer)
        self.tbtnNext.setObjectName(u"tbtnNext")

        self.horizontalLayout.addWidget(self.tbtnNext)

        self.tbtnLast = QToolButton(ImageViewer)
        self.tbtnLast.setObjectName(u"tbtnLast")

        self.horizontalLayout.addWidget(self.tbtnLast)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(ImageViewer)

        self.cbxZoom.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ImageViewer)
    # setupUi

    def retranslateUi(self, ImageViewer):
        ImageViewer.setWindowTitle(QCoreApplication.translate("ImageViewer", u"Form", None))
        self.grpImageControls.setTitle(QCoreApplication.translate("ImageViewer", u"Controls", None))
        self.tbtnRotateCCW.setText("")
        self.tbtnRotateCW.setText("")
        self.label.setText(QCoreApplication.translate("ImageViewer", u"Zoom:", None))
        self.cbxZoom.setItemText(0, QCoreApplication.translate("ImageViewer", u"Fit photo", None))
        self.cbxZoom.setItemText(1, QCoreApplication.translate("ImageViewer", u"Fit specimen", None))
        self.cbxZoom.setItemText(2, QCoreApplication.translate("ImageViewer", u"10%", None))
        self.cbxZoom.setItemText(3, QCoreApplication.translate("ImageViewer", u"25%", None))
        self.cbxZoom.setItemText(4, QCoreApplication.translate("ImageViewer", u"50%", None))
        self.cbxZoom.setItemText(5, QCoreApplication.translate("ImageViewer", u"100%", None))
        self.cbxZoom.setItemText(6, QCoreApplication.translate("ImageViewer", u"200%", None))
        self.cbxZoom.setItemText(7, QCoreApplication.translate("ImageViewer", u"300%", None))
        self.cbxZoom.setItemText(8, QCoreApplication.translate("ImageViewer", u"400%", None))

#if QT_CONFIG(tooltip)
        self.tbtnFirst.setToolTip(QCoreApplication.translate("ImageViewer", u"First", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnFirst.setText(QCoreApplication.translate("ImageViewer", u"|<", None))
#if QT_CONFIG(tooltip)
        self.tbtnPrev.setToolTip(QCoreApplication.translate("ImageViewer", u"Previous", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnPrev.setText(QCoreApplication.translate("ImageViewer", u"<", None))
#if QT_CONFIG(tooltip)
        self.tbtnNext.setToolTip(QCoreApplication.translate("ImageViewer", u"Next", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnNext.setText(QCoreApplication.translate("ImageViewer", u">", None))
#if QT_CONFIG(tooltip)
        self.tbtnLast.setToolTip(QCoreApplication.translate("ImageViewer", u"Last", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnLast.setText(QCoreApplication.translate("ImageViewer", u">|", None))
    # retranslateUi

