import sys
from PySide6.QtWidgets import QApplication
from ui.ui_auth import QMainWindow


app = QApplication(sys.argv)

window = QMainWindow()
window.show()

app.exec()