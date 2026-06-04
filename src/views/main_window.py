import flet as ft
from datetime import datetime

def main(page: ft.Page):
    page.clean()
    page.title = "Xenon-App"
    page.theme_mode = "light"


    def changeTheme():
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            changeTheme_Btn.content = "Change theme to light"
            changeTheme_Btn.icon = ft.Icons.LIGHT_MODE
            page.update()
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            changeTheme_Btn.content = "Change theme to dark"
            changeTheme_Btn.icon = ft.Icons.DARK_MODE
            page.update()

    

    changeTheme_Btn = ft.Button("Change theme to dark", on_click=changeTheme, icon=ft.Icons.DARK_MODE)

    page.add(changeTheme_Btn)
    
ft.run(main)