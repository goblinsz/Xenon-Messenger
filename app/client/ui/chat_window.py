import asyncio
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from client.ui.ui_chat import Ui_MainWindow as UiChat
from client.ui.ui_auth import Ui_MainWindow as UiAuth
from Backend.bd.bd import authenticate_user, register_user
import requests

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

        response = requests.post(
            "http://127.0.0.1:8000/login",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:
            data = response.json()

            print(data)

            self.open_chat(data["username"])

        else:
            print(response.json())

    def register(self):
        username = self.ui.username.toPlainText()
        password = self.ui.password.toPlainText()

        response = requests.post(
            "http://127.0.0.1:8000/register",
            json={
                "username": username,
                "password": password
            }
        )

        if response.status_code == 200:
            data = response.json()

            print("User ID:", data["user_id"])

            self.open_chat(username)

        else:
            print(response.json())

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