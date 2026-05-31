import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from ui_chat import Ui_MainWindow as UiChat
from ui_auth import Ui_MainWindow as UiAuth


users = ["Mike", "John", "Ivan"]

class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = UiAuth()
        self.ui.setupUi(self)

        self.ui.Login.clicked.connect(self.login)
        self.ui.Register.clicked.connect(self.register)

    def login(self):
        username = self.ui.Username.toPlainText()
        self.open_chat(username)

    def register(self):
        username = self.ui.Username.text()
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