# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'arthropod_describer.ui'
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


class Ui_ArhtropodDescriber(object):
    def setupUi(self, ArhtropodDescriber):
        if not ArhtropodDescriber.objectName():
            ArhtropodDescriber.setObjectName(u"ArhtropodDescriber")
        ArhtropodDescriber.resize(925, 670)
        self.actionOpen_folder = QAction(ArhtropodDescriber)
        self.actionOpen_folder.setObjectName(u"actionOpen_folder")
        self.centralwidget = QWidget(ArhtropodDescriber)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.imageListView = QListView(self.centralwidget)
        self.imageListView.setObjectName(u"imageListView")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imageListView.sizePolicy().hasHeightForWidth())
        self.imageListView.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.imageListView)

        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy1)
        self.pgEditor = QWidget()
        self.pgEditor.setObjectName(u"pgEditor")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pgEditor.sizePolicy().hasHeightForWidth())
        self.pgEditor.setSizePolicy(sizePolicy2)
        self.stackedWidget.addWidget(self.pgEditor)

        self.horizontalLayout.addWidget(self.stackedWidget)

        ArhtropodDescriber.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(ArhtropodDescriber)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 925, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        ArhtropodDescriber.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(ArhtropodDescriber)
        self.statusbar.setObjectName(u"statusbar")
        ArhtropodDescriber.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionOpen_folder)

        self.retranslateUi(ArhtropodDescriber)

        QMetaObject.connectSlotsByName(ArhtropodDescriber)
    # setupUi

    def retranslateUi(self, ArhtropodDescriber):
        ArhtropodDescriber.setWindowTitle(QCoreApplication.translate("ArhtropodDescriber", u"Arthropod Describer", None))
        self.actionOpen_folder.setText(QCoreApplication.translate("ArhtropodDescriber", u"Open folder", None))
        self.menuFile.setTitle(QCoreApplication.translate("ArhtropodDescriber", u"File", None))
    # retranslateUi

