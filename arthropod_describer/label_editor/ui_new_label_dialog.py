# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_label_dialog.ui'
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


class Ui_NewLabelDialog(object):
    def setupUi(self, NewLabelDialog):
        if not NewLabelDialog.objectName():
            NewLabelDialog.setObjectName(u"NewLabelDialog")
        NewLabelDialog.resize(377, 210)
        self.verticalLayout = QVBoxLayout(NewLabelDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, -1, -1, -1)
        self.colorLayout = QVBoxLayout()
        self.colorLayout.setObjectName(u"colorLayout")
        self.colorLayout.setContentsMargins(30, 30, 30, 30)
        self.lblColor = QLabel(NewLabelDialog)
        self.lblColor.setObjectName(u"lblColor")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblColor.sizePolicy().hasHeightForWidth())
        self.lblColor.setSizePolicy(sizePolicy)
        self.lblColor.setMinimumSize(QSize(72, 72))

        self.colorLayout.addWidget(self.lblColor)

        self.btnSetColor = QPushButton(NewLabelDialog)
        self.btnSetColor.setObjectName(u"btnSetColor")

        self.colorLayout.addWidget(self.btnSetColor)


        self.horizontalLayout.addLayout(self.colorLayout)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, 50, -1, -1)
        self.label = QLabel(NewLabelDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.label)

        self.txtLabelName = QLineEdit(NewLabelDialog)
        self.txtLabelName.setObjectName(u"txtLabelName")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.txtLabelName)

        self.label_2 = QLabel(NewLabelDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.LabelRole, self.label_2)

        self.txtLabelCode = QLineEdit(NewLabelDialog)
        self.txtLabelCode.setObjectName(u"txtLabelCode")

        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.txtLabelCode)


        self.horizontalLayout.addLayout(self.formLayout)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(NewLabelDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(NewLabelDialog)

        QMetaObject.connectSlotsByName(NewLabelDialog)
    # setupUi

    def retranslateUi(self, NewLabelDialog):
        NewLabelDialog.setWindowTitle(QCoreApplication.translate("NewLabelDialog", u"Form", None))
        self.lblColor.setText("")
        self.btnSetColor.setText(QCoreApplication.translate("NewLabelDialog", u"Set color", None))
        self.label.setText(QCoreApplication.translate("NewLabelDialog", u"Name:", None))
        self.label_2.setText(QCoreApplication.translate("NewLabelDialog", u"Code:", None))
    # retranslateUi

