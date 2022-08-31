# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'computation.ui'
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


class Ui_Computations(object):
    def setupUi(self, Computations):
        if not Computations.objectName():
            Computations.setObjectName(u"Computations")
        Computations.resize(533, 458)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Computations.sizePolicy().hasHeightForWidth())
        Computations.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(Computations)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cmbRegComps = QComboBox(Computations)
        self.cmbRegComps.setObjectName(u"cmbRegComps")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cmbRegComps.sizePolicy().hasHeightForWidth())
        self.cmbRegComps.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.cmbRegComps)

        self.grpRegDesc = QGroupBox(Computations)
        self.grpRegDesc.setObjectName(u"grpRegDesc")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.grpRegDesc.sizePolicy().hasHeightForWidth())
        self.grpRegDesc.setSizePolicy(sizePolicy2)
        self.horizontalLayout_3 = QHBoxLayout(self.grpRegDesc)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lblRegDesc = QLabel(self.grpRegDesc)
        self.lblRegDesc.setObjectName(u"lblRegDesc")
        sizePolicy2.setHeightForWidth(self.lblRegDesc.sizePolicy().hasHeightForWidth())
        self.lblRegDesc.setSizePolicy(sizePolicy2)
        self.lblRegDesc.setWordWrap(True)

        self.horizontalLayout_3.addWidget(self.lblRegDesc)


        self.verticalLayout.addWidget(self.grpRegDesc)

        self.grpRegionSettings = QGroupBox(Computations)
        self.grpRegionSettings.setObjectName(u"grpRegionSettings")
        sizePolicy2.setHeightForWidth(self.grpRegionSettings.sizePolicy().hasHeightForWidth())
        self.grpRegionSettings.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.grpRegionSettings)

        self.grpRegRestrict = QGroupBox(Computations)
        self.grpRegRestrict.setObjectName(u"grpRegRestrict")
        sizePolicy2.setHeightForWidth(self.grpRegRestrict.sizePolicy().hasHeightForWidth())
        self.grpRegRestrict.setSizePolicy(sizePolicy2)
        self.verticalLayout_4 = QVBoxLayout(self.grpRegRestrict)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.regRestrictView = QListView(self.grpRegRestrict)
        self.regRestrictView.setObjectName(u"regRestrictView")
        sizePolicy2.setHeightForWidth(self.regRestrictView.sizePolicy().hasHeightForWidth())
        self.regRestrictView.setSizePolicy(sizePolicy2)
        self.regRestrictView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.regRestrictView.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout_4.addWidget(self.regRestrictView)


        self.verticalLayout.addWidget(self.grpRegRestrict)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnRegApply = QToolButton(Computations)
        self.btnRegApply.setObjectName(u"btnRegApply")
        sizePolicy.setHeightForWidth(self.btnRegApply.sizePolicy().hasHeightForWidth())
        self.btnRegApply.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.btnRegApply)

        self.btnRegApplyAll = QToolButton(Computations)
        self.btnRegApplyAll.setObjectName(u"btnRegApplyAll")
        sizePolicy.setHeightForWidth(self.btnRegApplyAll.sizePolicy().hasHeightForWidth())
        self.btnRegApplyAll.setSizePolicy(sizePolicy)
        self.btnRegApplyAll.setPopupMode(QToolButton.MenuButtonPopup)
        self.btnRegApplyAll.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.horizontalLayout_2.addWidget(self.btnRegApplyAll)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(Computations)

        QMetaObject.connectSlotsByName(Computations)
    # setupUi

    def retranslateUi(self, Computations):
        Computations.setWindowTitle(QCoreApplication.translate("Computations", u"Form", None))
        self.grpRegDesc.setTitle(QCoreApplication.translate("Computations", u"Description", None))
        self.lblRegDesc.setText("")
        self.grpRegionSettings.setTitle(QCoreApplication.translate("Computations", u"Settings", None))
        self.grpRegRestrict.setTitle(QCoreApplication.translate("Computations", u"Apply to regions", None))
        self.btnRegApply.setText(QCoreApplication.translate("Computations", u"Apply to selected", None))
        self.btnRegApplyAll.setText(QCoreApplication.translate("Computations", u"Apply to all", None))
    # retranslateUi

