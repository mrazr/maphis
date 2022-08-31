# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'measurement_assign_dialog.ui'
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


class Ui_MeasurementAssignDialog(object):
    def setupUi(self, MeasurementAssignDialog):
        if not MeasurementAssignDialog.objectName():
            MeasurementAssignDialog.setObjectName(u"MeasurementAssignDialog")
        MeasurementAssignDialog.resize(1113, 563)
        self.verticalLayout = QVBoxLayout(MeasurementAssignDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setObjectName(u"mainLayout")
        self.labelLayout = QVBoxLayout()
        self.labelLayout.setObjectName(u"labelLayout")
        self.labelLayout.setContentsMargins(-1, 0, 0, -1)
        self.label = QLabel(MeasurementAssignDialog)
        self.label.setObjectName(u"label")
        self.label.setAutoFillBackground(False)

        self.labelLayout.addWidget(self.label, 0, Qt.AlignHCenter)

        self.labelTree = QTreeView(MeasurementAssignDialog)
        self.labelTree.setObjectName(u"labelTree")
        self.labelTree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.labelTree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.labelTree.setIndentation(10)
        self.labelTree.header().setVisible(False)

        self.labelLayout.addWidget(self.labelTree)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.btnLabelSelectAll = QPushButton(MeasurementAssignDialog)
        self.btnLabelSelectAll.setObjectName(u"btnLabelSelectAll")

        self.horizontalLayout_3.addWidget(self.btnLabelSelectAll)

        self.btnLabelDeselectAll = QPushButton(MeasurementAssignDialog)
        self.btnLabelDeselectAll.setObjectName(u"btnLabelDeselectAll")

        self.horizontalLayout_3.addWidget(self.btnLabelDeselectAll)


        self.labelLayout.addLayout(self.horizontalLayout_3)


        self.mainLayout.addLayout(self.labelLayout)

        self.measurementLayout = QVBoxLayout()
        self.measurementLayout.setObjectName(u"measurementLayout")
        self.measurementLayout.setContentsMargins(-1, 0, 0, -1)
        self.label_2 = QLabel(MeasurementAssignDialog)
        self.label_2.setObjectName(u"label_2")

        self.measurementLayout.addWidget(self.label_2, 0, Qt.AlignHCenter)

        self.measurementTree = QTreeWidget(MeasurementAssignDialog)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.measurementTree.setHeaderItem(__qtreewidgetitem)
        self.measurementTree.setObjectName(u"measurementTree")
        self.measurementTree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.measurementTree.setExpandsOnDoubleClick(False)
        self.measurementTree.header().setVisible(False)

        self.measurementLayout.addWidget(self.measurementTree)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.btnMeasSelectAll = QPushButton(MeasurementAssignDialog)
        self.btnMeasSelectAll.setObjectName(u"btnMeasSelectAll")

        self.horizontalLayout_2.addWidget(self.btnMeasSelectAll)

        self.btnMeasDeselectAll = QPushButton(MeasurementAssignDialog)
        self.btnMeasDeselectAll.setObjectName(u"btnMeasDeselectAll")

        self.horizontalLayout_2.addWidget(self.btnMeasDeselectAll)


        self.measurementLayout.addLayout(self.horizontalLayout_2)


        self.mainLayout.addLayout(self.measurementLayout)

        self.btnAssign = QPushButton(MeasurementAssignDialog)
        self.btnAssign.setObjectName(u"btnAssign")
        self.btnAssign.setEnabled(False)

        self.mainLayout.addWidget(self.btnAssign)

        self.assignmentLayout = QVBoxLayout()
        self.assignmentLayout.setObjectName(u"assignmentLayout")
        self.assignmentLayout.setContentsMargins(-1, 0, 0, -1)
        self.label_3 = QLabel(MeasurementAssignDialog)
        self.label_3.setObjectName(u"label_3")

        self.assignmentLayout.addWidget(self.label_3, 0, Qt.AlignHCenter)

        self.assignmentTree = QTreeWidget(MeasurementAssignDialog)
        __qtreewidgetitem1 = QTreeWidgetItem()
        __qtreewidgetitem1.setText(0, u"1");
        self.assignmentTree.setHeaderItem(__qtreewidgetitem1)
        self.assignmentTree.setObjectName(u"assignmentTree")
        self.assignmentTree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.assignmentTree.setExpandsOnDoubleClick(False)
        self.assignmentTree.header().setVisible(False)

        self.assignmentLayout.addWidget(self.assignmentTree)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.btnAssignmentSelectAll = QPushButton(MeasurementAssignDialog)
        self.btnAssignmentSelectAll.setObjectName(u"btnAssignmentSelectAll")

        self.horizontalLayout.addWidget(self.btnAssignmentSelectAll)

        self.btnAssignmentDeselectAll = QPushButton(MeasurementAssignDialog)
        self.btnAssignmentDeselectAll.setObjectName(u"btnAssignmentDeselectAll")

        self.horizontalLayout.addWidget(self.btnAssignmentDeselectAll)

        self.btnAssignmentRemove = QPushButton(MeasurementAssignDialog)
        self.btnAssignmentRemove.setObjectName(u"btnAssignmentRemove")
        self.btnAssignmentRemove.setEnabled(False)

        self.horizontalLayout.addWidget(self.btnAssignmentRemove)


        self.assignmentLayout.addLayout(self.horizontalLayout)


        self.mainLayout.addLayout(self.assignmentLayout)

        self.settingsLayout = QVBoxLayout()
        self.settingsLayout.setObjectName(u"settingsLayout")
        self.settingsLayout.setContentsMargins(0, -1, -1, -1)
        self.label_4 = QLabel(MeasurementAssignDialog)
        self.label_4.setObjectName(u"label_4")

        self.settingsLayout.addWidget(self.label_4, 0, Qt.AlignHCenter)

        self.settingsScrollArea = QScrollArea(MeasurementAssignDialog)
        self.settingsScrollArea.setObjectName(u"settingsScrollArea")
        self.settingsScrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 216, 480))
        self.settingsScrollArea.setWidget(self.scrollAreaWidgetContents)

        self.settingsLayout.addWidget(self.settingsScrollArea)


        self.mainLayout.addLayout(self.settingsLayout)


        self.verticalLayout.addLayout(self.mainLayout)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 10, -1, -1)
        self.btnDemoSelectColorAndTolerance = QPushButton(MeasurementAssignDialog)
        self.btnDemoSelectColorAndTolerance.setObjectName(u"btnDemoSelectColorAndTolerance")

        self.horizontalLayout_4.addWidget(self.btnDemoSelectColorAndTolerance)

        self.buttonBox = QDialogButtonBox(MeasurementAssignDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel)
        self.buttonBox.setCenterButtons(False)

        self.horizontalLayout_4.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.retranslateUi(MeasurementAssignDialog)
        self.buttonBox.accepted.connect(MeasurementAssignDialog.accept)
        self.buttonBox.rejected.connect(MeasurementAssignDialog.reject)

        QMetaObject.connectSlotsByName(MeasurementAssignDialog)
    # setupUi

    def retranslateUi(self, MeasurementAssignDialog):
        MeasurementAssignDialog.setWindowTitle(QCoreApplication.translate("MeasurementAssignDialog", u"Compute new measurements", None))
        self.label.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Select regions to compute measurements for:", None))
        self.btnLabelSelectAll.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Select all", None))
        self.btnLabelDeselectAll.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Deselect all", None))
        self.label_2.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Specify measurements for selected regions:", None))
        self.btnMeasSelectAll.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Select all", None))
        self.btnMeasDeselectAll.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Deselect all", None))
        self.btnAssign.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Assign", None))
        self.label_3.setText(QCoreApplication.translate("MeasurementAssignDialog", u"This will be computed:", None))
        self.btnAssignmentSelectAll.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Select all", None))
        self.btnAssignmentDeselectAll.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Deselect all", None))
        self.btnAssignmentRemove.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Remove", None))
        self.label_4.setText(QCoreApplication.translate("MeasurementAssignDialog", u"Measurement settings", None))
        self.btnDemoSelectColorAndTolerance.setText(QCoreApplication.translate("MeasurementAssignDialog", u"demo: Select Color and Tolerance", None))
    # retranslateUi

