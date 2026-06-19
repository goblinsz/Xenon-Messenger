import flet as ft
from auth import build_auth_window
from main import MainWindow

async def main(page: ft.Page):
    page.title = "Xenon Messenger"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT

    async def show_main(my_id: str, my_name: str, my_username: str):
        page.controls.clear()
        main_window = MainWindow(page, my_id, my_name, my_username, on_logout=show_auth)
        page.add(main_window.view, main_window.settings_overlay, main_window.add_contact_overlay)
        await main_window.initialize()
        page.update()

    async def show_auth(e=None):
        page.controls.clear()
        page.bgcolor = None
        auth_view = build_auth_window(page, on_success=show_main)
        page.add(auth_view)
        page.update()

    await show_auth()

ft.run(main)