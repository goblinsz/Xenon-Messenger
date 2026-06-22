import flet as ft
from auth import build_auth_window
from main import MainWindow
from settings_manager import load_settings

async def main(page: ft.Page):
    page.title = "Xenon Messenger"
    page.padding = 20

    settings = load_settings()
    page.theme_mode = ft.ThemeMode.DARK if settings.get("theme_mode") == "dark" else ft.ThemeMode.LIGHT

    async def show_main(my_id: str, my_name: str, my_username: str):
        page.controls.clear()
        main_window = MainWindow(page, my_id, my_name, my_username, on_logout=show_auth)
        page.add(main_window.view, main_window.settings_overlay, main_window.add_contact_overlay, main_window.create_group_overlay)
        await main_window.initialize()
        page.update()

    async def show_auth(e=None):
        page.controls.clear()
        page.bgcolor = None
        auth_view = build_auth_window(page, on_success=show_main)
        page.add(auth_view)
        page.update()

    await show_auth()

ft.app(target=main, assets_dir="assets")
