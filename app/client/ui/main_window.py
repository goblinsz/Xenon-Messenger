import flet as ft
import json
import os

def main(page: ft.Page):
    page.title = "Xenon-App"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window_min_width = 800
    page.window_min_height = 600

    contacts_File = "contacts.json"


    def load_contacts():
        if os.path.exists(contacts_File):
            try:
                with open(contacts_File, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        else:
            default_contacts = [
                {"name": "Jane Doe", "role": "Product Manager", "initials": "JD", "color": "BLUE_200"},
                {"name": "John Doe", "role": "Marketing", "initials": "JD", "color": "GREEN_200"}
            ]
            save_contacts(default_contacts)
            return default_contacts

    def save_contacts(contacts_list):
        with open(contacts_File, 'w', encoding='utf-8') as f:
            json.dump(contacts_list, f, indent=4, ensure_ascii=False)

    contacts_data = load_contacts()

    contacts_List = ft.ListView(
        expand=True,
        spacing=8,
        padding=0
    )

    chat_list = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=True,
        padding=10
    )

    def build_contacts_list(query=""):
        contacts_List.controls.clear()

        for contact in contacts_data:
            if query.lower() in contact["name"].lower() or query.lower() in contact["role"].lower():
                tile = ft.ListTile(
                    leading=ft.CircleAvatar(
                        content=ft.Text(contact["initials"], weight=ft.FontWeight.BOLD, color=ft.Colors.ON_PRIMARY),
                        bgcolor=getattr(ft.Colors, contact.get("color", "BLUE_200")),
                    ),
                    title=ft.Text(contact["name"], weight=ft.FontWeight.W_600, size=15),
                    subtitle=ft.Text(contact["role"], size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                    trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=ft.Colors.ON_SURFACE_VARIANT),
                    shape=ft.RoundedRectangleBorder(radius=10),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    on_click=lambda e, c=contact: select_contact(e, c)
                )
                contacts_List.controls.append(tile)
        page.update()

    def select_contact(e, contact):
        for tile in contacts_List.controls:
            tile.bgcolor = ft.Colors.SURFACE_CONTAINER_LOW
        e.control.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        print(f"Открыт чат с: {contact['name']}")
        page.update()

    def show_add_contact_dialog(e):
        name_field = ft.TextField(label="Имя и Фамилия", hint_text="Например: Алексей Смирнов")
        role_field = ft.TextField(label="Должность или Телефон", hint_text="Например: +7 999 000-00-00")

        def save_new_contact(e):
            if not name_field.value.strip():
                name_field.error_text = "Имя обязательно"
                name_field.update()
                return

            initials = "".join([word[0].upper() for word in name_field.value.split()[:2]])

            new_contact = {
                "name": name_field.value.strip(),
                "role": role_field.value.strip() or "Без должности",
                "initials": initials,
                "color": "PURPLE_200"
            }

            contacts_data.append(new_contact)
            save_contacts(contacts_data)
            build_contacts_list()

            page.dialog.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Добавить новый контакт", weight=ft.FontWeight.BOLD),
            content=ft.Column([name_field, role_field], tight=True, spacing=15),
            actions=[
                ft.TextButton("Отмена", on_click=lambda _: close_dialog()),
                ft.Button("Сохранить", on_click=save_new_contact, icon=ft.Icons.SAVE)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def close_dialog():
        page.dialog.open = False
        page.update()

    def add_message(text: str, is_mine: bool):
        if is_mine:
            bg_color = ft.Colors.PRIMARY_CONTAINER
            text_color = ft.Colors.ON_PRIMARY_CONTAINER
            alignment = ft.Alignment.CENTER_RIGHT
            border_radius = ft.BorderRadius.only(top_left=15, top_right=15, bottom_left=15, bottom_right=0)
        else:
            bg_color = ft.Colors.SURFACE_CONTAINER_HIGHEST
            text_color = ft.Colors.ON_SURFACE
            alignment = ft.Alignment.CENTER_LEFT
            border_radius = ft.BorderRadius.only(top_left=15, top_right=15, bottom_left=0, bottom_right=15)

        message_bubble = ft.Container(
            content=ft.Text(
                text,
                size=14,
                color=text_color,
                selectable=True
            ),
            bgcolor=bg_color,
            border_radius=border_radius,
            padding=ft.Padding.all(12),
            alignment=alignment,
            width=page.width * 0.6,
        )

        chat_list.controls.append(message_bubble)
        page.update()

    def send_message(e):
        text = msg_input.value.strip()
        if not text:
            return

        add_message(text, is_mine=True)
        msg_input.value = ""
        msg_input.focus()

    msg_input = ft.TextField(
        hint_text="Введите сообщение...",
        expand=True,
        border_radius=25,
        filled=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        on_submit=send_message,
    )

    send_btn = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        bgcolor=ft.Colors.PRIMARY,
        icon_color=ft.Colors.ON_PRIMARY,
        icon_size=20,
        on_click=send_message
    )

    username = ft.Text(value="User", weight=ft.FontWeight.BOLD, size=18)

    def changeTheme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            changeTheme_Btn.text = "Светлая тема"
            changeTheme_Btn.icon = ft.Icons.LIGHT_MODE
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            changeTheme_Btn.text = "Темная тема"
            changeTheme_Btn.icon = ft.Icons.DARK_MODE
        page.update()

    changeTheme_Btn = ft.Button(
        "Темная тема",
        on_click=changeTheme,
        icon=ft.Icons.DARK_MODE
    )

    sidebar_toolbar = ft.Row(
        controls=[
            username,
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.PERSON_ADD,
                tooltip="Добавить контакт",
                icon_color=ft.Colors.PRIMARY,
                on_click=show_add_contact_dialog
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    chat_area = ft.Column(
        controls=[
            ft.Text("Чат", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            chat_list,
            ft.Row([msg_input, send_btn], spacing=10)
        ],
        expand=True
    )

    top_bar = ft.Row(
        controls=[
            ft.Text("Xenon Messenger", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            changeTheme_Btn
        ]
    )

    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                sidebar_toolbar,
                ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                contacts_List
            ],
            expand=True
        ),
        width=280,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border_radius=12,
        padding=15
    )

    page.add(
        top_bar,
        ft.Container(height=20),
        ft.Row(
            controls=[sidebar, chat_area],
            expand=True,
            spacing=20
        )
    )

    build_contacts_list()
    add_message("Привет! Как продвигается проект?", is_mine=False)
    add_message("Привет! Делаю интерфейс чата на Flet, выглядит отлично.", is_mine=True)

ft.app(target=main)