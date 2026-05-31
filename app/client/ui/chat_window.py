import datetime
import sys
from typing import *
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QToolBox, QListWidget,
    QVBoxLayout, QLabel, QTextEdit, QLineEdit, QHBoxLayout
)
from dataclasses import dataclass
from datetime import datetime
from RaS.sendk import send

class Message:
    def __init__(self, text: str, author: str, date: datetime):
        self.text = text
        self.author = author
        self.date = datetime.datetime.now()


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat")
        self.resize(500, 700)
        messages: list[str] = []
        self.setupUi()

    def setupUi(self):
        main_layout = QHBoxLayout()
        messages_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        contact_layout = QVBoxLayout()

        self.ListContacts = QListWidget(self)

        main_layout.addLayout(messages_layout)
        main_layout.addLayout(input_layout)
        main_layout.addLayout(contact_layout)

        self.messages = QTextEdit(self)
        self.messages.setReadOnly(True)
        messages_layout.addWidget(self.messages)

        send_button = QPushButton("Send", self)
        send_button.clicked.connect(self.send_message)
        self.text = QLineEdit(self)
        self.text.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.text, 3)
        input_layout.addWidget(send_button, 1)

        self.setLayout(main_layout)





    async def send_message(self, text: str) -> None:
        text = self.text.text().strip()
        await send("gf", text, "lk")
        if not text:
            return

        self.messages.append(text)
        self.text.clear()

app = QApplication(sys.argv)
window = Window()
window.show()

app.exec()