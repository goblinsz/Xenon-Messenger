import asyncio
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from ui_chat import Ui_MainWindow as UiChat
from ui_auth import Ui_MainWindow as UiAuth
from Backend.bd.bd import authenticate_user, register_user

users = ["Mike", "John", "Ivan"]

class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = UiAuth()
        self.ui.setupUi(self)

        self.ui.login_Btn.clicked.connect(self.login)
        self.ui.register_Btn.clicked.connect(self.register)


    def login(self):
        username = self.ui.username.toPlainText()
        password = self.ui.password.toPlainText()

        name, user_id = asyncio.run(authenticate_user(username, password))

        if not user_id:
            print("Wrong login")
            return

        self.open_chat(username)

    def register(self):
        username = self.ui.username.toPlainText()
        password = self.ui.password.toPlainText()

        user_id = asyncio.run(register_user(username, password))

        if not user_id:
            print("Register failed")
            return

        self.open_chat(username)

    def open_chat(self, username):
        self.chat = MainWindow(username)
        self.chat.show()
        self.close()

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()

        self.username = username
        self.ui = UiChat()
        self.ui.setupUi(self)

        self.ui.current_Username.setText(self.username)

        self.ui.contacts_List.addItems(users)
        self.ui.contacts_List.itemClicked.connect(self.on_user_clicked)

        self.target_user = None

    def on_user_clicked(self, item):
        self.target_user = item.text()
        print("Открыли чат с:", self.target_user)

        self.load_chat()


app = QApplication(sys.argv)

auth = AuthWindow()
auth.show()

app.exec()