import flet as ft
from main_window import main

def build(page: ft.Page):
    page.clean()
    page.title = "Xenon Auth"

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page.theme_mode = ft.ThemeMode.SYSTEM

    username = ft.TextField(label="Username")
    password = ft.TextField(label="Пароль", password=True)
    password_Repeat = ft.TextField(label="Повтор пароля", password=True)
    error_Msg = ft.Text(value="", color=ft.Colors.RED)

    def login():
        print("login")
        ft.run(main)

    def register():
        print("regester")
        ft.run(main)

    def showRegestration():
        page.clean()
        page.add(
            ft.Column(
                [
                    username,
                    password,
                    password_Repeat,
                    ft.Button("Зарегестрироваться", on_click=register, width=300),
                    ft.Button("Уже есть аккаунт", on_click=showLogin, width=300),
                    ft.TextButton("Уже есть аккаунт? Войти", on_click=showLogin, width=300),
                    error_Msg,
                ]
            )
        )

    def showLogin():
        page.clean()
        page.add(
            ft.Column(
                [
                    username,
                    password,
                    ft.Button("Войти", on_click=login, width=300),
                    ft.TextButton("Нет аккаунта? Зарегестрироваться", on_click=showRegestration, width=300),
                    error_Msg,
                ]
            )
        )

    showLogin()


ft.run(build)