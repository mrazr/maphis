# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'import_dialog.ui'
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


class Ui_ImportDialog(object):
    def setupUi(self, ImportDialog):
        if not ImportDialog.objectName():
            ImportDialog.setObjectName(u"ImportDialog")
        ImportDialog.setWindowModality(Qt.WindowModal)
        ImportDialog.resize(804, 760)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ImportDialog.sizePolicy().hasHeightForWidth())
        ImportDialog.setSizePolicy(sizePolicy)
        ImportDialog.setMinimumSize(QSize(800, 0))
        self.verticalLayout = QVBoxLayout(ImportDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.lblResizeImages = QLabel(ImportDialog)
        self.lblResizeImages.setObjectName(u"lblResizeImages")

        self.gridLayout.addWidget(self.lblResizeImages, 9, 0, 1, 1)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.txtInput = QLineEdit(ImportDialog)
        self.txtInput.setObjectName(u"txtInput")

        self.verticalLayout_4.addWidget(self.txtInput)


        self.gridLayout.addLayout(self.verticalLayout_4, 3, 2, 1, 1)

        self.lblImageScale = QLabel(ImportDialog)
        self.lblImageScale.setObjectName(u"lblImageScale")

        self.gridLayout.addWidget(self.lblImageScale, 7, 0, 1, 1)

        self.label_4 = QLabel(ImportDialog)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 0, 0, 1, 1)

        self.label_3 = QLabel(ImportDialog)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)

        self.imgScaleInputLayout = QHBoxLayout()
        self.imgScaleInputLayout.setObjectName(u"imgScaleInputLayout")
        self.spinBoxImageScale = QSpinBox(ImportDialog)
        self.spinBoxImageScale.setObjectName(u"spinBoxImageScale")
        self.spinBoxImageScale.setMinimum(-1)
        self.spinBoxImageScale.setMaximum(9999)
        self.spinBoxImageScale.setValue(-1)

        self.imgScaleInputLayout.addWidget(self.spinBoxImageScale)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.imgScaleInputLayout.addItem(self.horizontalSpacer_2)


        self.gridLayout.addLayout(self.imgScaleInputLayout, 7, 2, 1, 1)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.spinboxNestLevel = QSpinBox(ImportDialog)
        self.spinboxNestLevel.setObjectName(u"spinboxNestLevel")
        self.spinboxNestLevel.setMinimum(0)
        self.spinboxNestLevel.setValue(0)

        self.horizontalLayout_5.addWidget(self.spinboxNestLevel)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.gridLayout.addLayout(self.horizontalLayout_5, 4, 2, 1, 1)

        self.label = QLabel(ImportDialog)
        self.label.setObjectName(u"label")
        self.label.setInputMethodHints(Qt.ImhDialableCharactersOnly|Qt.ImhDigitsOnly|Qt.ImhEmailCharactersOnly|Qt.ImhFormattedNumbersOnly|Qt.ImhLatinOnly|Qt.ImhLowercaseOnly|Qt.ImhUppercaseOnly|Qt.ImhUrlCharactersOnly)
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.label, 3, 0, 1, 1)

        self.txtOutput = QLineEdit(ImportDialog)
        self.txtOutput.setObjectName(u"txtOutput")

        self.gridLayout.addWidget(self.txtOutput, 1, 2, 1, 1)

        self.resizeLayout = QGridLayout()
        self.resizeLayout.setObjectName(u"resizeLayout")

        self.gridLayout.addLayout(self.resizeLayout, 9, 2, 1, 1)

        self.lblProjectsFolder = QLabel(ImportDialog)
        self.lblProjectsFolder.setObjectName(u"lblProjectsFolder")

        self.gridLayout.addWidget(self.lblProjectsFolder, 1, 0, 1, 1)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")

        self.gridLayout.addLayout(self.horizontalLayout_3, 10, 2, 1, 1)

        self.txtProjectName = QLineEdit(ImportDialog)
        self.txtProjectName.setObjectName(u"txtProjectName")

        self.gridLayout.addWidget(self.txtProjectName, 0, 2, 1, 1)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.btnFindInput = QPushButton(ImportDialog)
        self.btnFindInput.setObjectName(u"btnFindInput")

        self.verticalLayout_5.addWidget(self.btnFindInput)


        self.gridLayout.addLayout(self.verticalLayout_5, 3, 4, 1, 1)

        self.btnFindOutput = QPushButton(ImportDialog)
        self.btnFindOutput.setObjectName(u"btnFindOutput")

        self.gridLayout.addWidget(self.btnFindOutput, 1, 4, 1, 1)

        self.lblProjectDestination = QLabel(ImportDialog)
        self.lblProjectDestination.setObjectName(u"lblProjectDestination")

        self.gridLayout.addWidget(self.lblProjectDestination, 2, 2, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.grpImagesToImport = QGroupBox(ImportDialog)
        self.grpImagesToImport.setObjectName(u"grpImagesToImport")
        self.verticalLayout_3 = QVBoxLayout(self.grpImagesToImport)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(-1, 0, -1, 0)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 0, -1, -1)
        self.chkBoxImportCount = QCheckBox(self.grpImagesToImport)
        self.chkBoxImportCount.setObjectName(u"chkBoxImportCount")
        self.chkBoxImportCount.setEnabled(False)
        self.chkBoxImportCount.setTristate(True)

        self.horizontalLayout_4.addWidget(self.chkBoxImportCount)

        self.lblImportImgCount = QLabel(self.grpImagesToImport)
        self.lblImportImgCount.setObjectName(u"lblImportImgCount")

        self.horizontalLayout_4.addWidget(self.lblImportImgCount)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.chkMaxSize = QCheckBox(self.grpImagesToImport)
        self.chkMaxSize.setObjectName(u"chkMaxSize")
        self.chkMaxSize.setChecked(True)

        self.horizontalLayout_4.addWidget(self.chkMaxSize)

        self.spboxMaxSize = QSpinBox(self.grpImagesToImport)
        self.spboxMaxSize.setObjectName(u"spboxMaxSize")
        self.spboxMaxSize.setMaximum(9999)
        self.spboxMaxSize.setValue(700)

        self.horizontalLayout_4.addWidget(self.spboxMaxSize)

        self.btnExtractScale = QPushButton(self.grpImagesToImport)
        self.btnExtractScale.setObjectName(u"btnExtractScale")

        self.horizontalLayout_4.addWidget(self.btnExtractScale)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.groupBox_2 = QGroupBox(self.grpImagesToImport)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.horizontalLayout_7 = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_5)

        self.rbtnTagInfer = QRadioButton(self.groupBox_2)
        self.rbtnTagInfer.setObjectName(u"rbtnTagInfer")
        self.rbtnTagInfer.setChecked(True)

        self.horizontalLayout_7.addWidget(self.rbtnTagInfer)

        self.rbtnTagGlobal = QRadioButton(self.groupBox_2)
        self.rbtnTagGlobal.setObjectName(u"rbtnTagGlobal")

        self.horizontalLayout_7.addWidget(self.rbtnTagGlobal)

        self.txtTagGlobal = QLineEdit(self.groupBox_2)
        self.txtTagGlobal.setObjectName(u"txtTagGlobal")

        self.horizontalLayout_7.addWidget(self.txtTagGlobal)


        self.verticalLayout_6.addWidget(self.groupBox_2)


        self.verticalLayout_3.addLayout(self.verticalLayout_6)

        self.imageList = QTableView(self.grpImagesToImport)
        self.imageList.setObjectName(u"imageList")

        self.verticalLayout_3.addWidget(self.imageList)


        self.verticalLayout.addWidget(self.grpImagesToImport)

        self.grpLabelAssignments = QGroupBox(ImportDialog)
        self.grpLabelAssignments.setObjectName(u"grpLabelAssignments")
        self.verticalLayout_2 = QVBoxLayout(self.grpLabelAssignments)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableLabelImages = QTableWidget(self.grpLabelAssignments)
        if (self.tableLabelImages.columnCount() < 3):
            self.tableLabelImages.setColumnCount(3)
        if (self.tableLabelImages.rowCount() < 1):
            self.tableLabelImages.setRowCount(1)
        self.tableLabelImages.setObjectName(u"tableLabelImages")
        self.tableLabelImages.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableLabelImages.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableLabelImages.setRowCount(1)
        self.tableLabelImages.setColumnCount(3)
        self.tableLabelImages.horizontalHeader().setMinimumSectionSize(100)
        self.tableLabelImages.horizontalHeader().setDefaultSectionSize(200)
        self.tableLabelImages.horizontalHeader().setStretchLastSection(True)
        self.tableLabelImages.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tableLabelImages)

        self.layLabelAssignments = QVBoxLayout()
        self.layLabelAssignments.setObjectName(u"layLabelAssignments")
        self.layLabelAssignments.setContentsMargins(-1, 0, -1, 10)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.btnAddLabelImage = QPushButton(self.grpLabelAssignments)
        self.btnAddLabelImage.setObjectName(u"btnAddLabelImage")

        self.horizontalLayout.addWidget(self.btnAddLabelImage)

        self.btnRemoveSelected = QPushButton(self.grpLabelAssignments)
        self.btnRemoveSelected.setObjectName(u"btnRemoveSelected")
        self.btnRemoveSelected.setEnabled(False)

        self.horizontalLayout.addWidget(self.btnRemoveSelected)


        self.layLabelAssignments.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.layLabelAssignments)


        self.verticalLayout.addWidget(self.grpLabelAssignments)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.prgrImageCopying = QProgressBar(ImportDialog)
        self.prgrImageCopying.setObjectName(u"prgrImageCopying")
        self.prgrImageCopying.setEnabled(True)
        self.prgrImageCopying.setValue(24)

        self.gridLayout_2.addWidget(self.prgrImageCopying, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, -1, -1, -1)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btnBoxImport = QDialogButtonBox(ImportDialog)
        self.btnBoxImport.setObjectName(u"btnBoxImport")
        self.btnBoxImport.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout_2.addWidget(self.btnBoxImport)


        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)

        QWidget.setTabOrder(self.txtProjectName, self.txtOutput)
        QWidget.setTabOrder(self.txtOutput, self.btnFindOutput)
        QWidget.setTabOrder(self.btnFindOutput, self.txtInput)
        QWidget.setTabOrder(self.txtInput, self.btnFindInput)
        QWidget.setTabOrder(self.btnFindInput, self.spinboxNestLevel)
        QWidget.setTabOrder(self.spinboxNestLevel, self.spinBoxImageScale)
        QWidget.setTabOrder(self.spinBoxImageScale, self.chkBoxImportCount)
        QWidget.setTabOrder(self.chkBoxImportCount, self.chkMaxSize)
        QWidget.setTabOrder(self.chkMaxSize, self.spboxMaxSize)
        QWidget.setTabOrder(self.spboxMaxSize, self.btnExtractScale)
        QWidget.setTabOrder(self.btnExtractScale, self.rbtnTagInfer)
        QWidget.setTabOrder(self.rbtnTagInfer, self.rbtnTagGlobal)
        QWidget.setTabOrder(self.rbtnTagGlobal, self.txtTagGlobal)
        QWidget.setTabOrder(self.txtTagGlobal, self.imageList)
        QWidget.setTabOrder(self.imageList, self.tableLabelImages)
        QWidget.setTabOrder(self.tableLabelImages, self.btnAddLabelImage)
        QWidget.setTabOrder(self.btnAddLabelImage, self.btnRemoveSelected)

        self.retranslateUi(ImportDialog)

        QMetaObject.connectSlotsByName(ImportDialog)
    # setupUi

    def retranslateUi(self, ImportDialog):
        ImportDialog.setWindowTitle(QCoreApplication.translate("ImportDialog", u"Create a new project", None))
        self.lblResizeImages.setText(QCoreApplication.translate("ImportDialog", u"Resize images:", None))
        self.lblImageScale.setText(QCoreApplication.translate("ImportDialog", u"Image scale:", None))
        self.label_4.setText(QCoreApplication.translate("ImportDialog", u"Project name:", None))
        self.label_3.setText(QCoreApplication.translate("ImportDialog", u"Folder scan depth:", None))
        self.spinBoxImageScale.setSuffix(QCoreApplication.translate("ImportDialog", u" pixels/cm", None))
        self.spinboxNestLevel.setSpecialValueText(QCoreApplication.translate("ImportDialog", u"no nesting", None))
        self.label.setText(QCoreApplication.translate("ImportDialog", u"Photo folder:", None))
        self.lblProjectsFolder.setText(QCoreApplication.translate("ImportDialog", u"Project folder destination:", None))
        self.txtProjectName.setPlaceholderText(QCoreApplication.translate("ImportDialog", u"Please provide a name for the project.", None))
        self.btnFindInput.setText(QCoreApplication.translate("ImportDialog", u"Browse...", None))
        self.btnFindOutput.setText(QCoreApplication.translate("ImportDialog", u"Browse...", None))
        self.lblProjectDestination.setText("")
        self.grpImagesToImport.setTitle(QCoreApplication.translate("ImportDialog", u"Images to be imported", None))
        self.chkBoxImportCount.setText("")
        self.lblImportImgCount.setText("")
        self.chkMaxSize.setText(QCoreApplication.translate("ImportDialog", u"Downsample images to maximum height of", None))
        self.spboxMaxSize.setSuffix(QCoreApplication.translate("ImportDialog", u" px", None))
        self.btnExtractScale.setText(QCoreApplication.translate("ImportDialog", u"Extract scale from scale markers", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("ImportDialog", u"Image tag", None))
        self.rbtnTagInfer.setText(QCoreApplication.translate("ImportDialog", u"Infer from folders", None))
        self.rbtnTagGlobal.setText(QCoreApplication.translate("ImportDialog", u"Assign this:", None))
        self.grpLabelAssignments.setTitle(QCoreApplication.translate("ImportDialog", u"Assign each photo these label images:", None))
        self.btnAddLabelImage.setText(QCoreApplication.translate("ImportDialog", u"Add new", None))
        self.btnRemoveSelected.setText(QCoreApplication.translate("ImportDialog", u"Remove selected", None))
    # retranslateUi

