# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plugins_widget.ui'
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


class Ui_PluginsWidget(object):
    def setupUi(self, PluginsWidget):
        if not PluginsWidget.objectName():
            PluginsWidget.setObjectName(u"PluginsWidget")
        PluginsWidget.resize(650, 430)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PluginsWidget.sizePolicy().hasHeightForWidth())
        PluginsWidget.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(PluginsWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.grpPlugins = QGroupBox(PluginsWidget)
        self.grpPlugins.setObjectName(u"grpPlugins")
        sizePolicy.setHeightForWidth(self.grpPlugins.sizePolicy().hasHeightForWidth())
        self.grpPlugins.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.grpPlugins)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cmbPlugins = QComboBox(self.grpPlugins)
        self.cmbPlugins.setObjectName(u"cmbPlugins")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.cmbPlugins.sizePolicy().hasHeightForWidth())
        self.cmbPlugins.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.cmbPlugins)

        self.pluginTabWidget = QTabWidget(self.grpPlugins)
        self.pluginTabWidget.setObjectName(u"pluginTabWidget")
        sizePolicy.setHeightForWidth(self.pluginTabWidget.sizePolicy().hasHeightForWidth())
        self.pluginTabWidget.setSizePolicy(sizePolicy)
        self.tabRegionComps = QWidget()
        self.tabRegionComps.setObjectName(u"tabRegionComps")
        sizePolicy.setHeightForWidth(self.tabRegionComps.sizePolicy().hasHeightForWidth())
        self.tabRegionComps.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.tabRegionComps)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.cmbRegComps = QComboBox(self.tabRegionComps)
        self.cmbRegComps.setObjectName(u"cmbRegComps")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.cmbRegComps.sizePolicy().hasHeightForWidth())
        self.cmbRegComps.setSizePolicy(sizePolicy2)

        self.verticalLayout_2.addWidget(self.cmbRegComps)

        self.grpRegDesc = QGroupBox(self.tabRegionComps)
        self.grpRegDesc.setObjectName(u"grpRegDesc")
        sizePolicy3 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.grpRegDesc.sizePolicy().hasHeightForWidth())
        self.grpRegDesc.setSizePolicy(sizePolicy3)
        self.horizontalLayout_3 = QHBoxLayout(self.grpRegDesc)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lblRegDesc = QLabel(self.grpRegDesc)
        self.lblRegDesc.setObjectName(u"lblRegDesc")
        sizePolicy3.setHeightForWidth(self.lblRegDesc.sizePolicy().hasHeightForWidth())
        self.lblRegDesc.setSizePolicy(sizePolicy3)
        self.lblRegDesc.setWordWrap(True)

        self.horizontalLayout_3.addWidget(self.lblRegDesc)


        self.verticalLayout_2.addWidget(self.grpRegDesc)

        self.grpRegionSettings = QGroupBox(self.tabRegionComps)
        self.grpRegionSettings.setObjectName(u"grpRegionSettings")
        sizePolicy3.setHeightForWidth(self.grpRegionSettings.sizePolicy().hasHeightForWidth())
        self.grpRegionSettings.setSizePolicy(sizePolicy3)

        self.verticalLayout_2.addWidget(self.grpRegionSettings)

        self.grpRegRestrict = QGroupBox(self.tabRegionComps)
        self.grpRegRestrict.setObjectName(u"grpRegRestrict")
        sizePolicy4 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.grpRegRestrict.sizePolicy().hasHeightForWidth())
        self.grpRegRestrict.setSizePolicy(sizePolicy4)
        self.verticalLayout_4 = QVBoxLayout(self.grpRegRestrict)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.regRestrictView = QListView(self.grpRegRestrict)
        self.regRestrictView.setObjectName(u"regRestrictView")
        sizePolicy4.setHeightForWidth(self.regRestrictView.sizePolicy().hasHeightForWidth())
        self.regRestrictView.setSizePolicy(sizePolicy4)
        self.regRestrictView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.regRestrictView.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout_4.addWidget(self.regRestrictView)


        self.verticalLayout_2.addWidget(self.grpRegRestrict)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnRegApply = QPushButton(self.tabRegionComps)
        self.btnRegApply.setObjectName(u"btnRegApply")

        self.horizontalLayout_2.addWidget(self.btnRegApply)

        self.btnRegApplyAll = QPushButton(self.tabRegionComps)
        self.btnRegApplyAll.setObjectName(u"btnRegApplyAll")

        self.horizontalLayout_2.addWidget(self.btnRegApplyAll)

        self.btnRegReset = QPushButton(self.tabRegionComps)
        self.btnRegReset.setObjectName(u"btnRegReset")

        self.horizontalLayout_2.addWidget(self.btnRegReset)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.pluginTabWidget.addTab(self.tabRegionComps, "")
        self.tabPropComps = QWidget()
        self.tabPropComps.setObjectName(u"tabPropComps")
        self.verticalLayout_3 = QVBoxLayout(self.tabPropComps)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.cmbPropComps = QComboBox(self.tabPropComps)
        self.cmbPropComps.setObjectName(u"cmbPropComps")
        sizePolicy2.setHeightForWidth(self.cmbPropComps.sizePolicy().hasHeightForWidth())
        self.cmbPropComps.setSizePolicy(sizePolicy2)

        self.verticalLayout_3.addWidget(self.cmbPropComps)

        self.grpPropDesc = QGroupBox(self.tabPropComps)
        self.grpPropDesc.setObjectName(u"grpPropDesc")
        sizePolicy3.setHeightForWidth(self.grpPropDesc.sizePolicy().hasHeightForWidth())
        self.grpPropDesc.setSizePolicy(sizePolicy3)
        self.horizontalLayout_7 = QHBoxLayout(self.grpPropDesc)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.lblPropDesc = QLabel(self.grpPropDesc)
        self.lblPropDesc.setObjectName(u"lblPropDesc")
        sizePolicy3.setHeightForWidth(self.lblPropDesc.sizePolicy().hasHeightForWidth())
        self.lblPropDesc.setSizePolicy(sizePolicy3)
        self.lblPropDesc.setWordWrap(True)

        self.horizontalLayout_7.addWidget(self.lblPropDesc)


        self.verticalLayout_3.addWidget(self.grpPropDesc)

        self.grpPropSettings = QGroupBox(self.tabPropComps)
        self.grpPropSettings.setObjectName(u"grpPropSettings")
        sizePolicy3.setHeightForWidth(self.grpPropSettings.sizePolicy().hasHeightForWidth())
        self.grpPropSettings.setSizePolicy(sizePolicy3)

        self.verticalLayout_3.addWidget(self.grpPropSettings)

        self.grpPropRestrict = QGroupBox(self.tabPropComps)
        self.grpPropRestrict.setObjectName(u"grpPropRestrict")
        sizePolicy4.setHeightForWidth(self.grpPropRestrict.sizePolicy().hasHeightForWidth())
        self.grpPropRestrict.setSizePolicy(sizePolicy4)
        self.verticalLayout_6 = QVBoxLayout(self.grpPropRestrict)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.propRestrictView = QListView(self.grpPropRestrict)
        self.propRestrictView.setObjectName(u"propRestrictView")
        sizePolicy5 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.propRestrictView.sizePolicy().hasHeightForWidth())
        self.propRestrictView.setSizePolicy(sizePolicy5)
        self.propRestrictView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.propRestrictView.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout_6.addWidget(self.propRestrictView)


        self.verticalLayout_3.addWidget(self.grpPropRestrict)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.btnPropApply = QPushButton(self.tabPropComps)
        self.btnPropApply.setObjectName(u"btnPropApply")

        self.horizontalLayout_6.addWidget(self.btnPropApply)

        self.btnPropApplyAll = QPushButton(self.tabPropComps)
        self.btnPropApplyAll.setObjectName(u"btnPropApplyAll")

        self.horizontalLayout_6.addWidget(self.btnPropApplyAll)

        self.btnPropReset = QPushButton(self.tabPropComps)
        self.btnPropReset.setObjectName(u"btnPropReset")

        self.horizontalLayout_6.addWidget(self.btnPropReset)


        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.pluginTabWidget.addTab(self.tabPropComps, "")

        self.verticalLayout.addWidget(self.pluginTabWidget)


        self.horizontalLayout.addWidget(self.grpPlugins)


        self.retranslateUi(PluginsWidget)

        self.pluginTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(PluginsWidget)
    # setupUi

    def retranslateUi(self, PluginsWidget):
        PluginsWidget.setWindowTitle(QCoreApplication.translate("PluginsWidget", u"Form", None))
        self.grpPlugins.setTitle(QCoreApplication.translate("PluginsWidget", u"Plugins", None))
        self.grpRegDesc.setTitle(QCoreApplication.translate("PluginsWidget", u"Description", None))
        self.lblRegDesc.setText("")
        self.grpRegionSettings.setTitle(QCoreApplication.translate("PluginsWidget", u"Settings", None))
        self.grpRegRestrict.setTitle(QCoreApplication.translate("PluginsWidget", u"Apply to regions", None))
        self.btnRegApply.setText(QCoreApplication.translate("PluginsWidget", u"Apply", None))
        self.btnRegApplyAll.setText(QCoreApplication.translate("PluginsWidget", u"Apply to all", None))
        self.btnRegReset.setText(QCoreApplication.translate("PluginsWidget", u"Reset", None))
        self.pluginTabWidget.setTabText(self.pluginTabWidget.indexOf(self.tabRegionComps), QCoreApplication.translate("PluginsWidget", u"Regions", None))
        self.grpPropDesc.setTitle(QCoreApplication.translate("PluginsWidget", u"Description", None))
        self.lblPropDesc.setText("")
        self.grpPropSettings.setTitle(QCoreApplication.translate("PluginsWidget", u"Settings", None))
        self.grpPropRestrict.setTitle(QCoreApplication.translate("PluginsWidget", u"Apply to regions", None))
        self.btnPropApply.setText(QCoreApplication.translate("PluginsWidget", u"Apply", None))
        self.btnPropApplyAll.setText(QCoreApplication.translate("PluginsWidget", u"Apply to all", None))
        self.btnPropReset.setText(QCoreApplication.translate("PluginsWidget", u"Reset", None))
        self.pluginTabWidget.setTabText(self.pluginTabWidget.indexOf(self.tabPropComps), QCoreApplication.translate("PluginsWidget", u"Properties", None))
    # retranslateUi

