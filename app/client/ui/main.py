import flet as ft
import httpx
import aio_pika
import json
import asyncio
import os

API_URL = "http://127.0.0.1:8000"
RABBIT_URL = "amqp://g:g@10.0.0.103/"
CONTACTS_FILE = "my_contacts.json"


class MainWindow:
    def __init__(self, page: ft.Page, my_id: str, my_name: str, on_logout):
        self.page = page
        self.my_id = my_id
        self.my_name = my_name
        self.on_logout = on_logout
        self.current_friend_id = None
        self.my_contacts = self.load_contacts_json()

        self.status_text = ft.Text(f"Logged in as: {my_name} (ID: {my_id})", size=16, color="gray", weight="bold")
        self.message_history = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True, controls=[])
        self.friends_list = ft.ListView(expand=1, spacing=10, padding=20, controls=[])

        self.msg_input = ft.TextField(hint_text="Type message...", expand=True)
        self.send_btn = ft.Button("Send", icon=ft.Icons.SEND, on_click=self.send_message)
        self.msg_input.on_submit = self.send_message

        self.toolbar = ft.Row(
            controls=[
                ft.Text("Xenon Messenger", size=20, weight="bold"),
                ft.Row([
                    ft.IconButton(ft.Icons.PERSON_ADD, tooltip="Add Contact",
                                  on_click=lambda _: self.show_add_contact()),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Settings", on_click=lambda _: self.show_settings()),
                    ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", on_click=lambda _: self.on_logout())
                ], spacing=10)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.left_column = ft.Column(
            controls=[
                ft.Text("My contacts", size=20, weight="bold"),
                ft.Divider(),
                self.friends_list
            ],
            width=300
        )

        self.right_column = ft.Column(
            expand=True,
            controls=[
                self.status_text,
                ft.Divider(),
                self.message_history,
                ft.Row([self.msg_input, self.send_btn], spacing=10)
            ]
        )

        self.view = ft.Column(
            expand=True,
            controls=[
                self.toolbar,
                ft.Divider(),
                ft.Row(expand=True, controls=[self.left_column, self.right_column])
            ]
        )

        self.build_overlays()
        asyncio.create_task(self.load_contacts())
        asyncio.create_task(self.listen_to_my_queue())

    def load_contacts_json(self):
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_contacts_json(self):
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.my_contacts, f, indent=4)

    def build_overlays(self):
        def toggle_theme(e):
            self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
            self.page.update()

        self.settings_overlay = ft.Container(
            visible=False,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Settings", size=20, weight="bold"),
                        ft.Switch(label="Dark Mode", value=(self.page.theme_mode == ft.ThemeMode.DARK),
                                  on_change=toggle_theme),
                        ft.Row([ft.TextButton("Close", on_click=lambda _: self.hide_overlays())],
                               alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=20),
                    padding=20, width=300
                )
            ),
            alignment=ft.Alignment.CENTER,
            bgcolor="#80000000",
            expand=True
        )


        self.add_username_input = ft.TextField(hint_text="Enter exact username", autofocus=True)
        self.add_error_text = ft.Text("", color="red", size=12)

        self.add_contact_overlay = ft.Container(
            visible=False,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Add Contact", size=20, weight="bold"),
                        self.add_username_input,
                        self.add_error_text,
                        ft.Row([
                            ft.TextButton("Cancel", on_click=lambda _: self.hide_overlays()),
                            ft.TextButton("Search & Add", on_click=self.add_new_contact)
                        ], alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=10),
                    padding=20, width=300
                )
            ),
            alignment=ft.Alignment.CENTER,
            bgcolor="#80000000",
            expand=True
        )

    def show_settings(self):
        self.settings_overlay.visible = True
        self.page.update()

    def show_add_contact(self):
        self.add_username_input.value = ""
        self.add_error_text.value = ""
        self.add_contact_overlay.visible = True
        self.page.update()

    def hide_overlays(self):
        self.settings_overlay.visible = False
        self.add_contact_overlay.visible = False
        self.page.update()

    async def add_new_contact(self, e):
        username = self.add_username_input.value.strip()
        if not username:
            self.add_error_text.value = "Username cannot be empty"
            self.page.update()
            return

        self.add_error_text.value = "Searching..."
        self.page.update()


        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/users", params={"username": username})
                if resp.status_code == 200:
                    data = resp.json()
                    user = data.get("user", {})
                    user_id = str(user.get("id"))

                    if user_id == self.my_id:
                        self.add_error_text.value = "You cannot add yourself!"
                        self.page.update()
                        return


                    if any(c["id"] == user_id for c in self.my_contacts):
                        self.add_error_text.value = "Already in your contacts!"
                        self.page.update()
                        return


                    self.my_contacts.append({
                        "id": user_id,
                        "username": user.get("username"),
                        "name": user.get("name")
                    })
                    self.save_contacts_json()

                    self.hide_overlays()
                    await self.load_contacts()
                else:
                    self.add_error_text.value = "User not found on server."
                    self.page.update()
            except Exception as ex:
                self.add_error_text.value = f"Server error: {ex}"
                self.page.update()

    def select_friend(self, friend_id: str, friend_name: str):
        self.current_friend_id = friend_id
        self.status_text.value = f"Talking to: {friend_name} (ID: {friend_id})"
        self.message_history.controls.clear()
        self.page.update()
        asyncio.create_task(self.load_chat_history(friend_id))

    async def load_contacts(self):
        self.friends_list.controls.clear()
        for user in self.my_contacts:
            self.friends_list.controls.append(
                ft.ListTile(
                    title=ft.Text(user["name"]),
                    subtitle=ft.Text(f"@{user['username']}"),
                    leading=ft.Icon(ft.Icons.PERSON),
                    on_click=lambda e, uid=user["id"], uname=user["name"]: self.select_friend(uid, uname)
                )
            )
        self.page.update()

    async def load_chat_history(self, friend_id: str):
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/messages/{self.my_id}/{friend_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    messages = data.get("messages", [])
                    self.message_history.controls.clear()

                    for msg in messages:
                        is_mine = str(msg["sender"]) == str(self.my_id)
                        bubble = ft.Container(
                            content=ft.Text(f"{'You' if is_mine else 'Friend'}: {msg['content']}", size=16,
                                            color="black"),
                            bgcolor="#DCF8C6" if is_mine else "#E5E5EA",
                            border_radius=15,
                            padding=15,
                            width=400,
                            alignment=ft.Alignment.CENTER_RIGHT if is_mine else ft.Alignment.CENTER_LEFT
                        )
                        self.message_history.controls.append(bubble)
                    self.page.update()
            except Exception as ex:
                print(f"Load history error: {ex}")

    async def listen_to_my_queue(self):
        try:
            connection = await aio_pika.connect_robust(RABBIT_URL)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange("direct_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
                queue = await channel.declare_queue(self.my_id, durable=True)
                await queue.bind(exchange, routing_key=self.my_id)

                async def on_message(message):
                    async with message.process():
                        data = json.loads(message.body.decode('utf-8'))
                        content = data.get('content')
                        sender = str(data.get('from'))

                        if content and sender == self.current_friend_id:
                            bubble = ft.Container(
                                content=ft.Text(f"Friend: {content}", size=16, color="black"),
                                bgcolor="#E5E5EA",
                                border_radius=15,
                                padding=15,
                                width=400,
                                alignment=ft.Alignment.CENTER_LEFT
                            )
                            self.message_history.controls.append(bubble)
                            self.page.update()

                await queue.consume(on_message)
                await asyncio.Future()
        except Exception as e:
            print(f"Listener error: {e}")

    def send_message(self, e):
        if not self.current_friend_id:
            return

        if self.msg_input.value:
            text = self.msg_input.value

            my_bubble = ft.Container(
                content=ft.Text(f"You: {text}", size=16, color="black"),
                bgcolor="#DCF8C6",
                border_radius=15,
                padding=15,
                width=400,
                alignment=ft.Alignment.CENTER_RIGHT
            )
            self.message_history.controls.append(my_bubble)

            async def do_send():
                async with httpx.AsyncClient(trust_env=False) as client:
                    await client.post(f"{API_URL}/send_message", json={
                        "sender_id": int(self.my_id),
                        "target_id": int(self.current_friend_id),
                        "content": text
                    })

            asyncio.create_task(do_send())
            self.msg_input.value = ""
            self.page.update()