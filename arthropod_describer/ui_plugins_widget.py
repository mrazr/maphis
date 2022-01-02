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
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PluginsWidget.sizePolicy().hasHeightForWidth())
        PluginsWidget.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(PluginsWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.grpPlugins = QGroupBox(PluginsWidget)
        self.grpPlugins.setObjectName(u"grpPlugins")
        self.verticalLayout = QVBoxLayout(self.grpPlugins)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cmbPlugins = QComboBox(self.grpPlugins)
        self.cmbPlugins.setObjectName(u"cmbPlugins")

        self.verticalLayout.addWidget(self.cmbPlugins)

        self.pluginTabWidget = QTabWidget(self.grpPlugins)
        self.pluginTabWidget.setObjectName(u"pluginTabWidget")
        self.tabRegionComps = QWidget()
        self.tabRegionComps.setObjectName(u"tabRegionComps")
        self.verticalLayout_2 = QVBoxLayout(self.tabRegionComps)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.cmbRegComps = QComboBox(self.tabRegionComps)
        self.cmbRegComps.setObjectName(u"cmbRegComps")

        self.verticalLayout_2.addWidget(self.cmbRegComps)

        self.grpRegDesc = QGroupBox(self.tabRegionComps)
        self.grpRegDesc.setObjectName(u"grpRegDesc")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.grpRegDesc.sizePolicy().hasHeightForWidth())
        self.grpRegDesc.setSizePolicy(sizePolicy1)
        self.horizontalLayout_3 = QHBoxLayout(self.grpRegDesc)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lblRegDesc = QLabel(self.grpRegDesc)
        self.lblRegDesc.setObjectName(u"lblRegDesc")
        sizePolicy2 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lblRegDesc.sizePolicy().hasHeightForWidth())
        self.lblRegDesc.setSizePolicy(sizePolicy2)
        self.lblRegDesc.setWordWrap(True)

        self.horizontalLayout_3.addWidget(self.lblRegDesc)


        self.verticalLayout_2.addWidget(self.grpRegDesc)

        self.grpRegionSettings = QGroupBox(self.tabRegionComps)
        self.grpRegionSettings.setObjectName(u"grpRegionSettings")
        sizePolicy1.setHeightForWidth(self.grpRegionSettings.sizePolicy().hasHeightForWidth())
        self.grpRegionSettings.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.grpRegionSettings)

        self.grpRegRestrict = QGroupBox(self.tabRegionComps)
        self.grpRegRestrict.setObjectName(u"grpRegRestrict")
        self.verticalLayout_4 = QVBoxLayout(self.grpRegRestrict)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.regRestrictView = QListView(self.grpRegRestrict)
        self.regRestrictView.setObjectName(u"regRestrictView")
        self.regRestrictView.setSelectionMode(QAbstractItemView.MultiSelection)
        self.regRestrictView.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.verticalLayout_4.addWidget(self.regRestrictView)


        self.verticalLayout_2.addWidget(self.grpRegRestrict)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnApply = QPushButton(self.tabRegionComps)
        self.btnApply.setObjectName(u"btnApply")

        self.horizontalLayout_2.addWidget(self.btnApply)

        self.btnApplyToAll = QPushButton(self.tabRegionComps)
        self.btnApplyToAll.setObjectName(u"btnApplyToAll")

        self.horizontalLayout_2.addWidget(self.btnApplyToAll)

        self.btnReset = QPushButton(self.tabRegionComps)
        self.btnReset.setObjectName(u"btnReset")

        self.horizontalLayout_2.addWidget(self.btnReset)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.pluginTabWidget.addTab(self.tabRegionComps, "")
        self.tabPropComps = QWidget()
        self.tabPropComps.setObjectName(u"tabPropComps")
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
        self.btnApply.setText(QCoreApplication.translate("PluginsWidget", u"Apply", None))
        self.btnApplyToAll.setText(QCoreApplication.translate("PluginsWidget", u"Apply to all", None))
        self.btnReset.setText(QCoreApplication.translate("PluginsWidget", u"Reset", None))
        self.pluginTabWidget.setTabText(self.pluginTabWidget.indexOf(self.tabRegionComps), QCoreApplication.translate("PluginsWidget", u"Regions", None))
        self.pluginTabWidget.setTabText(self.pluginTabWidget.indexOf(self.tabPropComps), QCoreApplication.translate("PluginsWidget", u"Properties", None))
    # retranslateUi

