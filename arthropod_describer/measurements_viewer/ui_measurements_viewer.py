# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'measurements_viewer.ui'
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


class Ui_MeasurementsViewer(object):
    def setupUi(self, MeasurementsViewer):
        if not MeasurementsViewer.objectName():
            MeasurementsViewer.setObjectName(u"MeasurementsViewer")
        MeasurementsViewer.resize(1010, 603)
        self.verticalLayout = QVBoxLayout(MeasurementsViewer)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.buttonLayout.setContentsMargins(-1, -1, -1, 0)
        self.btnComputeMeasurements = QPushButton(MeasurementsViewer)
        self.btnComputeMeasurements.setObjectName(u"btnComputeMeasurements")

        self.buttonLayout.addWidget(self.btnComputeMeasurements)

        self.btnDelete = QPushButton(MeasurementsViewer)
        self.btnDelete.setObjectName(u"btnDelete")
        self.btnDelete.setEnabled(False)

        self.buttonLayout.addWidget(self.btnDelete)

        self.btnRecompute = QPushButton(MeasurementsViewer)
        self.btnRecompute.setObjectName(u"btnRecompute")
        self.btnRecompute.setEnabled(False)

        self.buttonLayout.addWidget(self.btnRecompute)

        self.btnExport = QToolButton(MeasurementsViewer)
        self.btnExport.setObjectName(u"btnExport")
        self.btnExport.setEnabled(False)
        self.btnExport.setPopupMode(QToolButton.MenuButtonPopup)
        self.btnExport.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btnExport.setArrowType(Qt.NoArrow)

        self.buttonLayout.addWidget(self.btnExport)

        self.chkColorVisually = QCheckBox(MeasurementsViewer)
        self.chkColorVisually.setObjectName(u"chkColorVisually")
        self.chkColorVisually.setChecked(True)

        self.buttonLayout.addWidget(self.chkColorVisually)


        self.verticalLayout.addLayout(self.buttonLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableView = QTableView(MeasurementsViewer)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout.addWidget(self.tableView)


        self.retranslateUi(MeasurementsViewer)

        QMetaObject.connectSlotsByName(MeasurementsViewer)
    # setupUi

    def retranslateUi(self, MeasurementsViewer):
        MeasurementsViewer.setWindowTitle(QCoreApplication.translate("MeasurementsViewer", u"Form", None))
        self.btnComputeMeasurements.setText(QCoreApplication.translate("MeasurementsViewer", u"Compute new measurements", None))
        self.btnDelete.setText(QCoreApplication.translate("MeasurementsViewer", u"Delete selected", None))
        self.btnRecompute.setText(QCoreApplication.translate("MeasurementsViewer", u"Recompute selected", None))
        self.btnExport.setText(QCoreApplication.translate("MeasurementsViewer", u"Export to [XLSX]", None))
        self.chkColorVisually.setText(QCoreApplication.translate("MeasurementsViewer", u"Display color data visually", None))
    # retranslateUi

