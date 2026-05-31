# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'chat.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMenuBar,
    QSizePolicy, QStatusBar, QTextEdit, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 606)
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(12)
        MainWindow.setFont(font)
        self.actionSettings = QAction(MainWindow)
        self.actionSettings.setObjectName(u"actionSettings")
        self.actionAdd_contact = QAction(MainWindow)
        self.actionAdd_contact.setObjectName(u"actionAdd_contact")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.contacts_List = QListWidget(self.centralwidget)
        self.contacts_List.setObjectName(u"contacts_List")
        self.contacts_List.setGeometry(QRect(0, 30, 161, 521))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(16)
        self.contacts_List.setFont(font1)
        self.current_Text = QTextEdit(self.centralwidget)
        self.current_Text.setObjectName(u"current_Text")
        self.current_Text.setGeometry(QRect(170, 500, 611, 51))
        font2 = QFont()
        font2.setFamilies([u"Arial"])
        font2.setPointSize(14)
        self.current_Text.setFont(font2)
        self.current_Text.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.IBeamCursor))
        self.username_Frame = QFrame(self.centralwidget)
        self.username_Frame.setObjectName(u"username_Frame")
        self.username_Frame.setGeometry(QRect(0, 0, 161, 31))
        self.username_Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.username_Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.current_Username = QLabel(self.username_Frame)
        self.current_Username.setObjectName(u"current_Username")
        self.current_Username.setGeometry(QRect(10, 5, 141, 21))
        self.current_Username.setFont(font2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        self.menuSettings = QMenu(self.menubar)
        self.menuSettings.setObjectName(u"menuSettings")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuSettings.menuAction())
        self.menuSettings.addAction(self.actionSettings)
        self.menuSettings.addAction(self.actionAdd_contact)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionSettings.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.actionAdd_contact.setText(QCoreApplication.translate("MainWindow", u"Add contact", None))
        self.current_Username.setText(QCoreApplication.translate("MainWindow", u"Your username", None))
        self.menuSettings.setTitle(QCoreApplication.translate("MainWindow", u"Additional", None))
    # retranslateUi

