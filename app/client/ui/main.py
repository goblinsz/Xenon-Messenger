from datetime import datetime
import flet as ft
import httpx
import aio_pika
import json
import asyncio
import os
from chat_history import read_chat, save_message
from settings_manager import load_settings, save_settings
from windows_toasts import WindowsToaster, Toast

API_URL = "http://localhost:8000"
RABBIT_URL = "amqp://g:g@10.0.0.103/"


class MainWindow:
    def __init__(self, page: ft.Page, my_id: str, my_name: str, my_username: str, on_logout):
        self.page = page
        self.my_id = my_id
        self.my_name = my_name
        self.my_username = my_username
        self.on_logout = on_logout
        self.current_friend_id = None
        self.my_contacts = self.load_contacts_json()

        self.settings = load_settings()
        self.theme = self.settings.get("theme", {})

        self.stop_event = asyncio.Event()

        self.status_text = ft.Text(f"Logged in as: {my_name} (ID: {my_id})", size=16, color="gray", weight="bold")
        self.block_btn = ft.IconButton(
            ft.Icons.BLOCK, tooltip="Block User", visible=False, icon_color="red",
            on_click=self.handle_block_toggle
        )
        self.block_warning = ft.Text("", size=14, weight="bold", visible=False)

        self.message_history = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True, controls=[])
        self.friends_list = ft.ListView(expand=1, spacing=10, padding=20, controls=[])

        self.msg_input = ft.TextField(hint_text="Type message...", expand=True)
        self.send_btn = ft.Button("Send", icon=ft.Icons.SEND, on_click=self.send_message)
        self.msg_input.on_submit = self.send_message

        self.toolbar = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Xenon Messenger", size=22, weight="bold"),
                        ft.VerticalDivider(width=1, thickness=1, color="grey"),
                        ft.Text(f"@{self.my_username}", size=14, color="blue", weight="bold"),
                        ft.Text(f"(ID: {self.my_id})", size=12, color="gray", italic=True)
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                ft.Row([
                    ft.IconButton(ft.Icons.PERSON_ADD, tooltip="Add Contact",
                                  on_click=lambda _: self.show_add_contact()),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Settings", on_click=lambda _: self.show_settings()),
                    ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", on_click=self.handle_logout)
                ], spacing=10)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.left_column = ft.Column(
            controls=[ft.Text("My contacts", size=20, weight="bold"), ft.Divider(), self.friends_list],
            width=300
        )

        self.right_column = ft.Column(
            expand=True,
            controls=[
                ft.Row([self.status_text, self.block_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.block_warning,
                ft.Divider(),
                self.message_history,
                ft.Row([self.msg_input, self.send_btn], spacing=10)
            ]
        )

        self.view = ft.Column(
            expand=True,
            controls=[self.toolbar, ft.Divider(), ft.Row(expand=True, controls=[self.left_column, self.right_column])]
        )

        self.apply_theme()
        self.build_overlays()

    @property
    def contacts_file(self):
        return f"contacts_{self.my_id}.json"

    def apply_theme(self):
        self.page.bgcolor = self.theme.get("bg_color") if self.theme.get("bg_color") else None
        self.current_font = self.theme.get("font_family", "Default")
        if self.current_font == "Default":
            self.current_font = None

        self.current_size = int(self.theme.get("font_size", 16))
        self.my_bubble_color = self.theme.get("bubble_color", "#DCF8C6")
        self.page.update()

    def update_settings_file(self):
        self.settings["theme"] = self.theme
        save_settings(self.settings)

    async def initialize(self):
        await self.load_contacts()
        if self.settings.get("strict_mode", False):
            await self.sync_whitelist_to_server()
        asyncio.create_task(self.listen_to_my_queue())

    async def handle_logout(self, e):
        self.stop_event.set()
        await self.on_logout()

    def load_contacts_json(self):
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, "r", encoding="utf-8") as f:
                    contacts = json.load(f)
                    return [c for c in contacts if str(c.get("id")) != str(self.my_id)]
            except Exception:
                return []
        return []

    def save_contacts_json(self):
        with open(self.contacts_file, "w", encoding="utf-8") as f:
            json.dump(self.my_contacts, f, indent=4, ensure_ascii=False)

    def build_overlays(self):
        def change_color(e, key):
            self.theme[key] = e.control.value
            self.update_settings_file()
            self.apply_theme()
            if self.current_friend_id:
                asyncio.create_task(self.load_chat_history(self.current_friend_id))

        def toggle_dark_mode(e):
            self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
            self.page.update()

        privacy_switch = ft.Switch(
            label="Only allow messages from contacts",
            value=self.settings.get("strict_mode", False),
            on_change=self.toggle_strict_mode
        )

        font_dropdown = ft.Dropdown(
            label="Font Family", value=self.theme.get("font_family"),
            options=[ft.DropdownOption(key="Default"), ft.DropdownOption(key="Courier New"),
                     ft.DropdownOption(key="Consolas")],
            on_select=lambda e: change_color(e, "font_family"), width=260
        )

        size_dropdown = ft.Dropdown(
            label="Font Size", value=str(self.theme.get("font_size")),
            options=[ft.DropdownOption(key=str(size), text=str(size)) for size in [12, 14, 16, 18, 20, 24]],
            on_select=lambda e: change_color(e, "font_size"), width=260
        )

        bg_color_dropdown = ft.Dropdown(
            label="Background Color", value=self.theme.get("bg_color"),
            options=[
                ft.DropdownOption(key="", text="Default"),
                ft.DropdownOption(key="#F0F8FF", text="Alice Blue"),
                ft.DropdownOption(key="#F5F5F5", text="Light Gray"),
            ],
            on_select=lambda e: change_color(e, "bg_color"), width=260
        )

        bubble_color_dropdown = ft.Dropdown(
            label="My Bubble Color", value=self.theme.get("bubble_color"),
            options=[
                ft.DropdownOption(key="#DCF8C6", text="Classic Green"),
                ft.DropdownOption(key="#BBDEFB", text="Ocean Blue"),
                ft.DropdownOption(key="#FFECB3", text="Warm Yellow"),
            ],
            on_select=lambda e: change_color(e, "bubble_color"), width=260
        )

        self.settings_overlay = ft.Container(
            visible=False,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Customization Settings", size=20, weight="bold"),
                        privacy_switch,
                        ft.Switch(label="Dark Mode", value=(self.page.theme_mode == ft.ThemeMode.DARK),
                                  on_change=toggle_dark_mode),
                        font_dropdown, size_dropdown, bg_color_dropdown, bubble_color_dropdown,
                        ft.Row([ft.TextButton("Close", on_click=lambda _: self.hide_overlays())],
                               alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
                    padding=20, width=320, height=450
                )
            ),
            alignment=ft.Alignment.CENTER, bgcolor="#80000000", expand=True
        )

        self.add_username_input = ft.TextField(hint_text="Enter exact username", autofocus=True)
        self.add_error_text = ft.Text("", color="red", size=12)

        self.add_contact_overlay = ft.Container(
            visible=False,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Add Contact", size=20, weight="bold"),
                        self.add_username_input, self.add_error_text,
                        ft.Row([ft.TextButton("Cancel", on_click=lambda _: self.hide_overlays()),
                                ft.TextButton("Search & Add", on_click=self.add_new_contact)],
                               alignment=ft.MainAxisAlignment.END)
                    ], tight=True, spacing=10),
                    padding=20, width=300
                )
            ),
            alignment=ft.Alignment.CENTER, bgcolor="#80000000", expand=True
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

                    self.my_contacts.append({"id": user_id, "username": user.get("username"), "name": user.get("name")})
                    self.save_contacts_json()
                    self.hide_overlays()
                    await self.load_contacts()

                    if self.settings.get("strict_mode", False):
                        await self.sync_whitelist_to_server()
                else:
                    self.add_error_text.value = "User not found on server."
                    self.page.update()
            except Exception as ex:
                self.add_error_text.value = f"Server error: {ex}"
                self.page.update()

    async def handle_block_toggle(self, e):
        if not self.current_friend_id: return
        is_blocking = not getattr(self, 'i_blocked_them', False)
        endpoint = "/block" if is_blocking else "/unblock"

        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}{endpoint}", json={
                    "blocker_id": int(self.my_id),
                    "blocked_id": int(self.current_friend_id)
                })
                if resp.status_code == 200:
                    self.i_blocked_them = is_blocking
                    self.update_block_ui()
                    action = "blocked" if is_blocking else "unblocked"
                    color = "orange" if is_blocking else "green"
                    self._show_error_snack(f"User {action} successfully.", bgcolor=color)
            except Exception as e:
                print(f"Block toggle error: {e}")

    async def check_block_status(self):
        if not self.current_friend_id: return
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}/block_status", json={
                    "user1_id": int(self.my_id),
                    "user2_id": int(self.current_friend_id)
                })
                if resp.status_code == 200:
                    data = resp.json()
                    self.i_blocked_them = data.get("i_blocked_them", False)
                    self.they_blocked_me = data.get("they_blocked_me", False)
                    self.update_block_ui()
            except Exception as e:
                print(f"Block status error: {e}")

    def update_block_ui(self):
        if getattr(self, 'they_blocked_me', False):
            self.block_warning.value = "⚠️ This user has blocked you. You cannot send messages."
            self.block_warning.color = "red"
            self.block_warning.visible = True
            self.msg_input.disabled = True
            self.send_btn.disabled = True
        elif getattr(self, 'i_blocked_them', False):
            self.block_warning.value = "⚠️ You have blocked this user."
            self.block_warning.color = "orange"
            self.block_warning.visible = True
            self.msg_input.disabled = True
            self.send_btn.disabled = True
        else:
            self.block_warning.visible = False
            self.msg_input.disabled = False
            self.send_btn.disabled = False

        if getattr(self, 'i_blocked_them', False):
            self.block_btn.icon = ft.Icons.CHECK_CIRCLE_OUTLINE
            self.block_btn.tooltip = "Unblock User"
            self.block_btn.icon_color = "green"
        else:
            self.block_btn.icon = ft.Icons.BLOCK
            self.block_btn.tooltip = "Block User"
            self.block_btn.icon_color = "red"

        self.page.update()

    def select_friend(self, friend_id: str, friend_name: str):
        self.current_friend_id = friend_id
        self.status_text.value = f"Talking to: {friend_name} (ID: {friend_id})"
        self.block_btn.visible = True
        self.block_warning.visible = False
        self.msg_input.disabled = False
        self.send_btn.disabled = False

        self.message_history.controls.clear()
        self.page.update()
        asyncio.create_task(self.load_chat_history(friend_id))
        asyncio.create_task(self.check_block_status())

    async def load_contacts(self):
        self.friends_list.controls.clear()
        for user in self.my_contacts:
            self.friends_list.controls.append(
                ft.ListTile(
                    title=ft.Text(user["name"], size=self.current_size, font_family=self.current_font),
                    subtitle=ft.Text(f"@{user['username']}"), leading=ft.Icon(ft.Icons.PERSON),
                    on_click=lambda e, uid=user["id"], uname=user["name"]: self.select_friend(uid, uname)
                )
            )
        self.page.update()

    def build_chat_bubble(self, text, is_mine):
        return ft.Container(
            content=ft.Text(text, size=self.current_size, font_family=self.current_font, color="black"),
            bgcolor=self.my_bubble_color if is_mine else "#E5E5EA",
            border_radius=15, padding=15, width=400,
            alignment=ft.Alignment.CENTER_RIGHT if is_mine else ft.Alignment.CENTER_LEFT
        )

    def get_sender_name(self, sender_id: str) -> str:
        for contact in self.my_contacts:
            if str(contact["id"]) == str(sender_id):
                return contact["name"]
        return f"User {sender_id}"

    async def load_chat_history(self, friend_id: str):
        history = await read_chat(int(self.my_id), int(self.my_id), int(friend_id))
        self.message_history.controls.clear()

        if not history:
            async with httpx.AsyncClient(trust_env=False) as client:
                try:
                    resp = await client.get(f"{API_URL}/messages/{self.my_id}/{friend_id}")
                    if resp.status_code == 200:
                        messages = resp.json().get("messages", [])
                        for msg in messages:
                            is_mine = str(msg["sender"]) == str(self.my_id)
                            sender_name = "You" if is_mine else self.get_sender_name(str(msg["sender"]))
                            self.message_history.controls.append(
                                self.build_chat_bubble(f"{sender_name}: {msg['content']}", is_mine))
                        self.page.update()
                except Exception as ex:
                    print(f"Load history error: {ex}")
        else:
            for h in history:
                is_mine = str(h["sender"]) == str(self.my_id)
                sender_name = "You" if is_mine else self.get_sender_name(str(h["sender"]))
                self.message_history.controls.append(
                    self.build_chat_bubble(f"{sender_name}: {h['content']}", is_mine))
            self.page.update()

    def trigger_notification(self, sender_id, content):
        sender_name = next((c["name"] for c in self.my_contacts if c["id"] == sender_id), f"User {sender_id}")
        try:
            snack = ft.SnackBar(
                content=ft.Text(f"New message from {sender_name}: {content}"),
                action="View",
                on_action=lambda e: self.select_friend(sender_id, sender_name)
            )
            if hasattr(self.page, 'open'):
                self.page.open(snack)
            else:
                if self.page.overlay is None:
                    self.page.overlay = []
                self.page.overlay.append(snack)
                self.page.update()
        except AttributeError:
            pass

    def show_desktop_notification(self, sender_title: str, message_content: str):
        try:
            toaster = WindowsToaster("Xenon Messenger")
            toast = Toast()
            body_text = message_content if len(message_content) < 60 else f"{message_content[:57]}..."
            toast.text_fields = [f"New Message from {sender_title}", body_text]
            toaster.show_toast(toast)
        except Exception as e:
            print(f"Failed to display desktop notification: {e}")

    async def verify_and_add_contact(self, sender_id: str):
        if not any(c["id"] == sender_id for c in self.my_contacts):
            async with httpx.AsyncClient(trust_env=False) as client:
                try:
                    resp = await client.get(f"{API_URL}/users/id/{sender_id}")
                    if resp.status_code == 200:
                        user_info = resp.json()
                        self.my_contacts.append({
                            "id": str(user_info["id"]),
                            "username": user_info["username"],
                            "name": user_info["name"]
                        })
                        self.save_contacts_json()
                        await self.load_contacts()
                except Exception as e:
                    print(f"Error auto-populating contact: {e}")

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

                        if content:
                            await self.verify_and_add_contact(sender)

                            if sender == self.current_friend_id:
                                sender_name = self.get_sender_name(sender)
                                self.message_history.controls.append(
                                    self.build_chat_bubble(f"{sender_name}: {content}", False))
                                self.page.update()
                            else:
                                sender_name = next((c["name"] for c in self.my_contacts if c["id"] == sender),
                                                   f"User {sender}")
                                self.trigger_notification(sender, content)
                                self.show_desktop_notification(sender_name, content)

                            await save_message(int(self.my_id), data.get('timestamp'), int(sender), int(self.my_id),
                                               content, False)

                await queue.consume(on_message)
                await self.stop_event.wait()
        except Exception as e:
            print(f"Listener error: {e}")

    async def send_message(self, e):
        if not self.current_friend_id or not self.msg_input.value:
            return

        text = self.msg_input.value
        self.msg_input.value = ""
        self.page.update()

        async def do_send():
            async with httpx.AsyncClient(trust_env=False) as client:
                try:
                    resp = await client.post(f"{API_URL}/send_message", json={
                        "sender_id": int(self.my_id),
                        "target_id": int(self.current_friend_id),
                        "content": text
                    })

                    if resp.status_code == 200:
                        self.message_history.controls.append(self.build_chat_bubble(f"You: {text}", True))
                        self.page.update()
                        await save_message(
                            int(self.my_id),
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            int(self.my_id),
                            int(self.current_friend_id),
                            text,
                            True
                        )
                    else:
                        error_detail = resp.json().get("detail", "Unknown server error")
                        self._show_error_snack(f"Send error: {error_detail}")

                except Exception as ex:
                    self._show_error_snack(f"Network error: {ex}")

        asyncio.create_task(do_send())

    def _show_error_snack(self, message: str, bgcolor: str = "red"):
        snack = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=bgcolor,
            duration=4000
        )

        if hasattr(self.page, 'open'):
            self.page.open(snack)
        else:
            if self.page.overlay is None:
                self.page.overlay = []
            self.page.overlay.append(snack)
            self.page.update()

    async def toggle_strict_mode(self, e):
        enabled = e.control.value
        self.settings["strict_mode"] = enabled
        save_settings(self.settings)

        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                await client.post(f"{API_URL}/privacy/set_strict", json={
                    "user_id": int(self.my_id),
                    "enabled": enabled
                })
                if enabled:
                    await self.sync_whitelist_to_server()
                    self._show_error_snack("Privacy mode enabled. Only contacts can message you.", bgcolor="green")
                else:
                    self._show_error_snack("Privacy mode disabled. Anyone can message you.", bgcolor="green")
            except Exception as ex:
                print(f"Privacy error: {ex}")
                self._show_error_snack(f"Failed to update privacy: {ex}")

    async def sync_whitelist_to_server(self):
        allowed_ids = [int(c["id"]) for c in self.my_contacts]
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                await client.post(f"{API_URL}/privacy/update_whitelist", json={
                    "user_id": int(self.my_id),
                    "allowed_ids": allowed_ids
                })
            except Exception as ex:
                print(f"Whitelist sync error: {ex}")