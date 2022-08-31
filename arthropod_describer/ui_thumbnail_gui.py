# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'thumbnail_gui.ui'
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


class Ui_ThumbnailGUI(object):
    def setupUi(self, ThumbnailGUI):
        if not ThumbnailGUI.objectName():
            ThumbnailGUI.setObjectName(u"ThumbnailGUI")
        ThumbnailGUI.resize(248, 160)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ThumbnailGUI.sizePolicy().hasHeightForWidth())
        ThumbnailGUI.setSizePolicy(sizePolicy)
        ThumbnailGUI.setMinimumSize(QSize(248, 160))
        ThumbnailGUI.setMaximumSize(QSize(248, 160))
        self.verticalLayout = QVBoxLayout(ThumbnailGUI)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(5, 5, 5, 0)
        self.lblApprovalInfo = QLabel(ThumbnailGUI)
        self.lblApprovalInfo.setObjectName(u"lblApprovalInfo")
        self.lblApprovalInfo.setMinimumSize(QSize(40, 0))
        self.lblApprovalInfo.setMaximumSize(QSize(16777215, 16))
        font = QFont()
        font.setPointSize(8)
        self.lblApprovalInfo.setFont(font)

        self.horizontalLayout.addWidget(self.lblApprovalInfo, 0, Qt.AlignTop)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.tbtnRotateCCW = QToolButton(ThumbnailGUI)
        self.tbtnRotateCCW.setObjectName(u"tbtnRotateCCW")
        self.tbtnRotateCCW.setMinimumSize(QSize(28, 28))
        self.tbtnRotateCCW.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.tbtnRotateCCW)

        self.tbtnRotateCW = QToolButton(ThumbnailGUI)
        self.tbtnRotateCW.setObjectName(u"tbtnRotateCW")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tbtnRotateCW.sizePolicy().hasHeightForWidth())
        self.tbtnRotateCW.setSizePolicy(sizePolicy1)
        self.tbtnRotateCW.setMinimumSize(QSize(28, 28))
        self.tbtnRotateCW.setMaximumSize(QSize(28, 28))
        self.tbtnRotateCW.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.tbtnRotateCW)

        self.tbtnResize = QToolButton(ThumbnailGUI)
        self.tbtnResize.setObjectName(u"tbtnResize")
        self.tbtnResize.setMinimumSize(QSize(28, 28))
        self.tbtnResize.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.tbtnResize)


        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, 0, 5, -1)
        self.tbtnDelete = QToolButton(ThumbnailGUI)
        self.tbtnDelete.setObjectName(u"tbtnDelete")
        self.tbtnDelete.setMinimumSize(QSize(28, 28))
        self.tbtnDelete.setIconSize(QSize(20, 20))

        self.horizontalLayout_3.addWidget(self.tbtnDelete)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)

        self.lblImgSize = QLabel(ThumbnailGUI)
        self.lblImgSize.setObjectName(u"lblImgSize")
        self.lblImgSize.setStyleSheet(u"background-color: rgba(200, 200, 200, 200)")

        self.horizontalLayout_3.addWidget(self.lblImgSize)


        self.gridLayout.addLayout(self.horizontalLayout_3, 1, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(5, -1, 5, 2)
        self.tbtnSave = QToolButton(ThumbnailGUI)
        self.tbtnSave.setObjectName(u"tbtnSave")
        self.tbtnSave.setMinimumSize(QSize(28, 28))
        self.tbtnSave.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.tbtnSave)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.lblResolution = QLabel(ThumbnailGUI)
        self.lblResolution.setObjectName(u"lblResolution")
        self.lblResolution.setStyleSheet(u"background-color: rgba(200, 200, 200, 200)")

        self.horizontalLayout_2.addWidget(self.lblResolution)

        self.tbtnSetResolution = QToolButton(ThumbnailGUI)
        self.tbtnSetResolution.setObjectName(u"tbtnSetResolution")
        self.tbtnSetResolution.setMinimumSize(QSize(28, 28))
        self.tbtnSetResolution.setIconSize(QSize(20, 20))

        self.horizontalLayout_2.addWidget(self.tbtnSetResolution)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(ThumbnailGUI)

        QMetaObject.connectSlotsByName(ThumbnailGUI)
    # setupUi

    def retranslateUi(self, ThumbnailGUI):
        ThumbnailGUI.setWindowTitle(QCoreApplication.translate("ThumbnailGUI", u"Form", None))
        self.lblApprovalInfo.setText("")
#if QT_CONFIG(tooltip)
        self.tbtnRotateCCW.setToolTip(QCoreApplication.translate("ThumbnailGUI", u"Rotate counterclockwise", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnRotateCCW.setText(QCoreApplication.translate("ThumbnailGUI", u"...", None))
#if QT_CONFIG(tooltip)
        self.tbtnRotateCW.setToolTip(QCoreApplication.translate("ThumbnailGUI", u"Rotate clockwise", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnRotateCW.setText(QCoreApplication.translate("ThumbnailGUI", u"...", None))
#if QT_CONFIG(tooltip)
        self.tbtnResize.setToolTip(QCoreApplication.translate("ThumbnailGUI", u"Resize\u2026", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnResize.setText(QCoreApplication.translate("ThumbnailGUI", u"...", None))
#if QT_CONFIG(tooltip)
        self.tbtnDelete.setToolTip(QCoreApplication.translate("ThumbnailGUI", u"Delete photo from project", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnDelete.setText(QCoreApplication.translate("ThumbnailGUI", u"...", None))
        self.lblImgSize.setText(QCoreApplication.translate("ThumbnailGUI", u"width x height", None))
#if QT_CONFIG(tooltip)
        self.tbtnSave.setToolTip(QCoreApplication.translate("ThumbnailGUI", u"Save changes", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnSave.setText(QCoreApplication.translate("ThumbnailGUI", u"...", None))
        self.lblResolution.setText(QCoreApplication.translate("ThumbnailGUI", u"1 mm = ? px", None))
#if QT_CONFIG(tooltip)
        self.tbtnSetResolution.setToolTip(QCoreApplication.translate("ThumbnailGUI", u"Set scale\u2026", None))
#endif // QT_CONFIG(tooltip)
        self.tbtnSetResolution.setText(QCoreApplication.translate("ThumbnailGUI", u"...", None))
    # retranslateUi

