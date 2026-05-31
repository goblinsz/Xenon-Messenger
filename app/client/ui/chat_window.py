import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from ui_chat import Ui_MainWindow as UiChat
from ui_auth import Ui_MainWindow as UiAuth


users = ["Mike", "John", "Ivan"]


# ---------------- MESSAGE BUBBLE ----------------
class MessageBubble(QWidget):
    def __init__(self, text: str, is_me: bool):
        super().__init__()

        layout = QHBoxLayout(self)

        label = QLabel(text)
        label.setWordWrap(True)

        if is_me:
            layout.addStretch()
            layout.addWidget(label)
        else:
            layout.addWidget(label)
            layout.addStretch()


# ---------------- AUTH WINDOW ----------------
class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = UiAuth()
        self.ui.setupUi(self)

        self.ui.Login.clicked.connect(self.login)
        self.ui.Register.clicked.connect(self.register)

    def login(self):
        username = self.ui.Username.toPlainText()   # FIX: text(), не toPlainText
        self.open_chat(username)

    def register(self):
        username = self.ui.Username.text()   # FIX
        self.open_chat(username)

    def open_chat(self, username):
        self.chat = MainWindow(username)
        self.chat.show()
        self.close()


# ---------------- MAIN CHAT WINDOW ----------------
class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()

        self.username = username
        self.ui = UiChat()
        self.ui.setupUi(self)

        # показать имя пользователя
        self.ui.current_Username.setText(self.username)

        # контакты
        self.ui.contacts_List.addItems(users)
        self.ui.contacts_List.itemClicked.connect(self.on_user_clicked)

        # текущее состояние чата
        self.target_user = None

        # чат-лог (по пользователям)
        self.messages = {}

        # контейнер сообщений (ВАЖНО: вертикальный layout)
        self.chat_layout = QVBoxLayout(self.ui.chatContainer)
        self.chat_layout.addStretch()

    # ---------------- выбрать пользователя ----------------
    def on_user_clicked(self, item):
        self.target_user = item.text()
        print("Открыли чат с:", self.target_user)

        self.load_chat()

    # ---------------- загрузка истории ----------------
    def load_chat(self):
        # очистка UI
        while self.chat_layout.count() > 1:  # оставляем stretch
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        history = self.messages.get(self.target_user, [])

        for msg in history:
            bubble = MessageBubble(msg["text"], msg["is_me"])
            self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    # ---------------- отправка сообщения ----------------
    def send_message(self, text):
        if not self.target_user or not text:
            return

        msg = {
            "text": text,
            "is_me": True
        }

        self.messages.setdefault(self.target_user, []).append(msg)

        bubble = MessageBubble(text, True)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)


# ---------------- APP ----------------
app = QApplication(sys.argv)

auth = AuthWindow()
auth.show()

app.exec()