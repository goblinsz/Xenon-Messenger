import flet as ft
from auth import build_auth_window
from main import MainWindow

def main(page: ft.Page):
    page.title = "Xenon Messenger"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT

    def show_main(my_id: str, my_name: str):
        page.controls.clear()
        main_window = MainWindow(page, my_id, my_name, on_logout=show_auth)
        page.add(main_window.view, main_window.settings_overlay, main_window.add_contact_overlay)
        page.update()

    def show_auth():
        page.controls.clear()
        auth_view = build_auth_window(page, on_success=show_main)
        page.add(auth_view)
        page.update()

    show_auth()

ft.run(main)