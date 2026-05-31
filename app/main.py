import sys
import asyncio
from PySide6.QtWidgets import QApplication
from Backend.bd.bd import init_pool, close_pool
from client.ui.ui_auth import Ui_MainWindow


async def start():
    await init_pool()

    app = QApplication(sys.argv)
    window = Ui_MainWindow()
    window.show()

    app.exec()
    await close_pool()

if __name__ == "__main__":
    asyncio.run(start())