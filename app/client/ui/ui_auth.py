# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login_page.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTextEdit,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 596)
        font = QFont()
        font.setFamilies([u"Arial"])
        MainWindow.setFont(font)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(280, 130, 241, 191))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.Username = QTextEdit(self.frame)
        self.Username.setObjectName(u"Username")
        self.Username.setGeometry(QRect(40, 30, 161, 31))
        self.Password = QTextEdit(self.frame)
        self.Password.setObjectName(u"Password")
        self.Password.setGeometry(QRect(40, 80, 161, 31))
        self.Login = QPushButton(self.frame)
        self.Login.setObjectName(u"Login")
        self.Login.setGeometry(QRect(80, 120, 81, 26))
        self.Register = QPushButton(self.frame)
        self.Register.setObjectName(u"Register")
        self.Register.setGeometry(QRect(80, 150, 81, 26))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.Login.setText(QCoreApplication.translate("MainWindow", u"Login", None))
        self.Register.setText(QCoreApplication.translate("MainWindow", u"Register", None))
    # retranslateUi

