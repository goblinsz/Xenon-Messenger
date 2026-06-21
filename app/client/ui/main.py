from datetime import datetime
import flet as ft
import httpx
import aio_pika
import json
import asyncio
import os


from chat_history import save_message
from settings_manager import load_settings, save_settings
from windows_toasts import WindowsToaster, Toast

API_URL = "http://10.0.0.103:8000"
RABBIT_URL = "amqp://g:g@10.0.0.103/"


class MainWindow:
    def __init__(self, page: ft.Page, my_id: str, my_name: str, my_username: str, on_logout):
        self.page = page
        self.my_id = my_id
        self.my_name = my_name
        self.my_username = my_username
        self.on_logout = on_logout
        self.current_friend_id = None
        self.current_group_id = None
        self.my_contacts = self.load_contacts_json()

        self.settings = load_settings()
        self.theme = self.settings.get("theme", {})

        # initialize attributes that apply_theme will touch
        self.current_font = None
        self.current_size = 16
        self.my_bubble_color = "#DCF8C6"

        self.stop_event = asyncio.Event()

        self.status_text = ft.Text(f"Logged in as: {my_name} (ID: {my_id})", size=16, color="gray", weight=ft.FontWeight.BOLD)
        self.block_btn = ft.IconButton(ft.Icons.BLOCK, tooltip="Block User", visible=False, icon_color="red",
                                       on_click=self.handle_block_toggle)
        self.block_warning = ft.Text("", size=14, weight=ft.FontWeight.BOLD, visible=False)

        self.message_history = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True, controls=[])
        self.friends_list = ft.ListView(expand=1, spacing=10, padding=20, controls=[])
        self.groups_list = ft.ListView(expand=1, spacing=10, padding=20, controls=[])

        self.msg_input = ft.TextField(hint_text="Type message...", expand=True)
        self.send_btn = ft.Button("Send", icon=ft.Icons.SEND, on_click=self.send_message)
        self.msg_input.on_submit = self.send_message

        self.toolbar = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Xenon Messenger", size=22, weight=ft.FontWeight.BOLD),
                        ft.VerticalDivider(width=1, thickness=1, color="grey"),
                        ft.Text(f"@{self.my_username}", size=14, color="blue", weight=ft.FontWeight.BOLD),
                        ft.Text(f"(ID: {self.my_id})", size=12, color="gray", italic=True)
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10
                ),
                ft.Row([
                    ft.IconButton(ft.Icons.GROUP_ADD, tooltip="Create Group",
                                  on_click=lambda _: self.show_create_group()),
                    ft.IconButton(ft.Icons.PERSON_ADD, tooltip="Add Contact",
                                  on_click=lambda _: self.show_add_contact()),
                    ft.IconButton(ft.Icons.SETTINGS, tooltip="Settings", on_click=lambda _: self.show_settings()),
                    ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", on_click=self.handle_logout)
                ], spacing=10)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.left_column = ft.Column(
            controls=[
                ft.Text("Groups", size=18, weight=ft.FontWeight.BOLD),
                self.groups_list,
                ft.Divider(),
                ft.Text("Contacts", size=18, weight=ft.FontWeight.BOLD),
                self.friends_list
            ],
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
        if self.current_font == "Default": self.current_font = None
        self.current_size = int(self.theme.get("font_size", 16))
        self.my_bubble_color = self.theme.get("bubble_color", "#DCF8C6")
        self.page.update()

    def update_settings_file(self):
        self.settings["theme"] = self.theme
        save_settings(self.settings)

    async def initialize(self):
        await self.load_contacts()
        await self.load_groups()
        if self.settings.get("strict_mode", False):
            await self.sync_whitelist_to_server()
        asyncio.create_task(self.listen_to_my_queue())

    async def handle_logout(self, _):
        self.stop_event.set()
        await self.on_logout()

    def load_contacts_json(self):
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, "r", encoding="utf-8") as f:
                    contacts = json.load(f)
                    # Ensure all ids are stored as strings to avoid type mismatches later
                    for c in contacts:
                        if isinstance(c.get("id"), int):
                            c["id"] = str(c["id"])
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
            if self.current_friend_id: asyncio.create_task(self.load_chat_history(self.current_friend_id))

        def toggle_dark_mode(e):
            self.page.theme_mode = ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
            self.page.update()

        privacy_switch = ft.Switch(label="Private mode",
                                   value=self.settings.get("strict_mode", False),
                                   on_change=self.toggle_strict_mode)
        font_dropdown = ft.Dropdown(label="Font Family", value=self.theme.get("font_family"),
                                    options=[ft.DropdownOption(key="Default"), ft.DropdownOption(key="Courier New"),
                                             ft.DropdownOption(key="Consolas")],
                                    on_select=lambda e: change_color(e, "font_family"), width=260)
        size_dropdown = ft.Dropdown(label="Font Size", value=str(self.theme.get("font_size")),
                                    options=[ft.DropdownOption(key=str(s), text=str(s)) for s in
                                             [12, 14, 16, 18, 20, 24]],
                                    on_select=lambda e: change_color(e, "font_size"), width=260)
        bg_color_dropdown = ft.Dropdown(label="Background Color", value=self.theme.get("bg_color"),
                                        options=[ft.DropdownOption(key="", text="Default"),
                                                 ft.DropdownOption(key="#F0F8FF", text="Alice Blue"),
                                                 ft.DropdownOption(key="#F5F5F5", text="Light Gray")],
                                        on_select=lambda e: change_color(e, "bg_color"), width=260)
        bubble_color_dropdown = ft.Dropdown(label="My Bubble Color", value=self.theme.get("bubble_color"),
                                            options=[ft.DropdownOption(key="#DCF8C6", text="Classic Green"),
                                                     ft.DropdownOption(key="#BBDEFB", text="Ocean Blue"),
                                                     ft.DropdownOption(key="#FFECB3", text="Warm Yellow")],
                                            on_select=lambda e: change_color(e, "bubble_color"), width=260)

        self.settings_overlay = ft.Container(
            visible=False,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Customization Settings", size=20, weight=ft.FontWeight.BOLD),
                        privacy_switch,
                        ft.Switch(label="Dark Mode", value=(self.page.theme_mode == ft.ThemeMode.DARK),
                                  on_change=toggle_dark_mode),
                        font_dropdown, size_dropdown, bg_color_dropdown, bubble_color_dropdown
                    ], tight=True, spacing=15, scroll=ft.ScrollMode.AUTO),
                    padding=20, width=320, height=400
                )
            ),
            alignment=ft.Alignment.CENTER, bgcolor="#80000000", expand=True
        )

        self.add_username_input = ft.TextField(hint_text="Enter exact username", autofocus=True)
        self.add_error_text = ft.Text("", color="red", size=12)
        self.add_contact_overlay = ft.Container(visible=False, content=ft.Card(content=ft.Container(content=ft.Column(
            [ft.Text("Add Contact", size=20, weight=ft.FontWeight.BOLD), self.add_username_input, self.add_error_text, ft.Row(
                [ft.TextButton("Cancel", on_click=lambda _: self.hide_overlays()),
                 ft.TextButton("Search & Add", on_click=self.add_new_contact)], alignment=ft.MainAxisAlignment.END)],
            tight=True, spacing=10), padding=20, width=300)), alignment=ft.Alignment.CENTER, bgcolor="#80000000",
                                                expand=True)

        self.group_name_input = ft.TextField(hint_text="Group name", autofocus=True)
        self.group_participants_list = ft.ListView(height=200, spacing=5)
        self.group_error_text = ft.Text("", color="red", size=12)
        self.create_group_overlay = ft.Container(visible=False, content=ft.Card(content=ft.Container(content=ft.Column(
            [ft.Text("Create Group", size=20, weight=ft.FontWeight.BOLD), self.group_name_input,
             ft.Text("Select participants:", size=14, weight=ft.FontWeight.BOLD), self.group_participants_list,
             self.group_error_text, ft.Row([ft.TextButton("Cancel", on_click=lambda _: self.hide_overlays()),
                                            ft.TextButton("Create", on_click=self.create_group)],
                                           alignment=ft.MainAxisAlignment.END)], tight=True, spacing=10), padding=20,
                                                                                                     width=350)),
                                                 alignment=ft.Alignment.CENTER, bgcolor="#80000000", expand=True)

    def show_settings(self):
        self.hide_overlays()
        self.settings_overlay.visible = True
        self.page.update()

    def show_add_contact(self):
        self.hide_overlays()
        self.add_username_input.value = ""
        self.add_error_text.value = ""
        self.add_contact_overlay.visible = True
        self.page.update()

    def show_create_group(self):
        self.hide_overlays()
        self.group_name_input.value = ""
        self.group_error_text.value = ""
        self.group_participants_list.controls.clear()
        for c in self.my_contacts:
            self.group_participants_list.controls.append(
                ft.Checkbox(label=f"{c['name']} (@{c['username']})", value=False, data=str(c['id']))
            )
        self.create_group_overlay.visible = True
        self.page.update()

    def hide_overlays(self):
        self.settings_overlay.visible = False
        self.add_contact_overlay.visible = False
        self.create_group_overlay.visible = False
        self.page.update()

    async def create_group(self, _):
        name = self.group_name_input.value.strip()
        if not name:
            self.group_error_text.value = "Name is required"
            self.page.update()
            return
        selected = [int(cb.data) for cb in self.group_participants_list.controls if cb.value]
        if len(selected) < 1:
            self.group_error_text.value = "Select at least 1 participant"
            self.page.update()
            return

        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}/groups/create", json={"creator_id": int(self.my_id), "name": name,
                                                                           "participant_ids": selected})
                if resp.status_code == 200:
                    self.hide_overlays()
                    await self.load_groups()
                    self._show_error_snack("Group created!", bgcolor="green")
                else:
                    self.group_error_text.value = resp.json().get("detail", "Error")
                    self.page.update()
            except Exception as ex:
                self.group_error_text.value = str(ex)
                self.page.update()

    async def add_new_contact(self, _):
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
                    user = resp.json().get("user", {})
                    user_id = str(user.get("id"))
                    if user_id == self.my_id:
                        self.add_error_text.value = "You cannot add yourself!"
                    elif any(c["id"] == user_id for c in self.my_contacts):
                        self.add_error_text.value = "Already in your contacts!"
                    else:
                        self.my_contacts.append(
                            {"id": user_id, "username": user.get("username"), "name": user.get("name")})
                        self.save_contacts_json()
                        self.hide_overlays()
                        await self.load_contacts()
                        if self.settings.get("strict_mode", False): await self.sync_whitelist_to_server()
                else:
                    self.add_error_text.value = "User not found."
                self.page.update()
            except Exception as ex:
                self.add_error_text.value = f"Server error: {ex}"
                self.page.update()

    async def handle_block_toggle(self, _):
        if not self.current_friend_id: return
        is_blocking = not getattr(self, 'i_blocked_them', False)
        endpoint = "/block" if is_blocking else "/unblock"
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}{endpoint}", json={"blocker_id": int(self.my_id),
                                                                       "blocked_id": int(self.current_friend_id)})
                if resp.status_code == 200:
                    self.i_blocked_them = is_blocking
                    self.update_block_ui()
                    self._show_error_snack(f"User {'blocked' if is_blocking else 'unblocked'}.",
                                           bgcolor="orange" if is_blocking else "green")
            except Exception as e:
                print(f"Block error: {e}")

    async def check_block_status(self):
        if not self.current_friend_id: return
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}/block_status",
                                         json={"user1_id": int(self.my_id), "user2_id": int(self.current_friend_id)})
                if resp.status_code == 200:
                    data = resp.json()
                    self.i_blocked_them = data.get("i_blocked_them", False)
                    self.they_blocked_me = data.get("they_blocked_me", False)
                    self.update_block_ui()
            except Exception as e:
                print(f"Block status error: {e}")

    def update_block_ui(self):
        if getattr(self, 'they_blocked_me', False):
            self.block_warning.value = "⚠️ This user has blocked you."
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
            self.send_btn.disabled = True if self.current_group_id else False

        if getattr(self, 'i_blocked_them', False):
            self.block_btn.icon = ft.Icons.CHECK_CIRCLE_OUTLINE
            self.block_btn.tooltip = "Unblock"
            self.block_btn.icon_color = "green"
        else:
            self.block_btn.icon = ft.Icons.BLOCK
            self.block_btn.tooltip = "Block"
            self.block_btn.icon_color = "red"
        self.page.update()

    def select_friend(self, friend_id: str, friend_name: str):
        self.current_friend_id = friend_id
        self.current_group_id = None
        self.status_text.value = f"Talking to: {friend_name} (ID: {friend_id})"
        self.block_btn.visible = True
        self.block_warning.visible = False
        self.msg_input.disabled = False
        self.send_btn.disabled = False
        self.message_history.controls.clear()
        self.page.update()
        asyncio.create_task(self.load_chat_history(friend_id))
        asyncio.create_task(self.check_block_status())

    def select_group(self, conv_id: str, group_name: str):
        self.current_friend_id = None
        self.current_group_id = conv_id
        self.status_text.value = f"Group: {group_name}"
        self.block_btn.visible = False
        self.block_warning.visible = False
        self.msg_input.disabled = False
        self.send_btn.disabled = False
        self.message_history.controls.clear()
        self.page.update()
        asyncio.create_task(self.load_group_history(conv_id))

    async def load_groups(self):
        self.groups_list.controls.clear()
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/conversations/{self.my_id}")
                if resp.status_code == 200:
                    for c in resp.json().get("conversations", []):
                        self.groups_list.controls.append(ft.ListTile(
                            title=ft.Text(c["name"], weight=ft.FontWeight.BOLD), leading=ft.Icon(ft.Icons.GROUP),
                            on_click=lambda e, cid=str(c["id"]), cname=c["name"]: self.select_group(cid, cname)
                        ))
            except Exception as e:
                print(f"Load groups error: {e}")
        self.page.update()

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

        self.friends_list.update()
        self.page.update()

    def build_chat_bubble(self, text, is_mine):
        return ft.Container(
            content=ft.Text(text, size=self.current_size, font_family=self.current_font, color="black"),
            bgcolor=self.my_bubble_color if is_mine else "#E5E5EA",
            border_radius=15, padding=15, width=400,
            alignment=ft.Alignment.CENTER_RIGHT if is_mine else ft.Alignment.CENTER_LEFT
        )

    async def _append_message_safe(self, sender_id: str, content: str, is_mine: bool):
        sender_name = "You" if is_mine else self.get_sender_name(sender_id)
        bubble = self.build_chat_bubble(f"{sender_name}: {content}", is_mine)
        self.message_history.controls.append(bubble)
        self.message_history.update()

    def get_sender_name(self, sender_id: str) -> str:
        if str(sender_id) == str(self.my_id): return "You"
        for contact in self.my_contacts:
            if str(contact["id"]) == str(sender_id): return contact["name"]
        return f"User {sender_id}"

    async def load_chat_history(self, friend_id: str):
        self.message_history.controls.clear()
        self.page.update()

        messages_data = []
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/messages/{self.my_id}/{friend_id}")
                if resp.status_code == 200:
                    messages_data = resp.json().get("messages", [])
            except:
                pass

        bubbles = []
        for msg in messages_data:
            is_mine = str(msg["sender"]) == str(self.my_id)
            sender_name = "You" if is_mine else self.get_sender_name(str(msg["sender"]))
            bubbles.append(self.build_chat_bubble(f"{sender_name}: {msg['content']}", is_mine))

        self.message_history.controls = bubbles
        self.message_history.update()

    async def load_group_history(self, conv_id: str):
        self.message_history.controls.clear()
        self.page.update()

        messages_data = []
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/messages/group/{conv_id}")
                if resp.status_code == 200:
                    messages_data = resp.json().get("messages", [])
            except:
                pass

        for msg in messages_data:
            is_mine = str(msg["sender"]) == str(self.my_id)
            self.message_history.controls.append(
                self.build_chat_bubble(f"{self.get_sender_name(str(msg['sender']))}: {msg['content']}",
                                       is_mine))
        self.page.update()

    def trigger_notification(self, sender_id, content):
        sender_name = self.get_sender_name(sender_id)
        snack = ft.SnackBar(content=ft.Text(f"New message from {sender_name}: {content}"), action="View",
                            on_action=lambda e: self.select_friend(sender_id, sender_name))
        self.page.overlay.append(snack)
        self.page.update()

    def show_desktop_notification(self, sender_title: str, message_content: str):
        try:
            toaster = WindowsToaster("Xenon Messenger")
            toast = Toast()
            toast.text_fields = [f"New Message from {sender_title}", message_content[:60]]
            toaster.show_toast(toast)
        except:
            pass

    async def verify_and_add_contact(self, sender_id: str):
        # Convert sender_id to int for comparison with stored ids (which may be ints or strings)
        sender_int = int(sender_id)
        if not any(int(c["id"]) == sender_int for c in self.my_contacts):
            async with httpx.AsyncClient(trust_env=False) as client:
                try:
                    resp = await client.get(f"{API_URL}/users/id/{sender_id}")
                    if resp.status_code == 200:
                        u = resp.json()
                        # Store id as string for consistency
                        self.my_contacts.append({"id": str(u["id"]), "username": u["username"], "name": u["name"]})
                        self.save_contacts_json()
                        await self.load_contacts()
                except:
                    pass

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
                        timestamp = data.get('timestamp')

                        if content:
                            await self.verify_and_add_contact(sender)
                            await save_message(int(self.my_id), timestamp, int(sender), int(self.my_id), content, False)

                            if sender == self.current_friend_id:
                                self.page.run_task(self._append_message_safe, sender, content, False)
                            else:
                                sender_name = next((c["name"] for c in self.my_contacts if c["id"] == sender),
                                                   f"User {sender}")
                                self.trigger_notification(sender, content)
                                self.show_desktop_notification(sender_name, content)

                await queue.consume(on_message)
                await self.stop_event.wait()
        except Exception as e:
            print(f"Listener error: {e}")

    async def _handle_incoming_message(self, sender: str, content: str, timestamp: str):
        await self.verify_and_add_contact(sender)

        if sender == self.current_friend_id:
            sender_name = self.get_sender_name(sender)
            self.message_history.controls.append(
                self.build_chat_bubble(f"{sender_name}: {content}", False)
            )
            self.message_history.update()
            self.page.update()
        else:
            sender_name = next((c["name"] for c in self.my_contacts if c["id"] == sender), f"User {sender}")
            self.trigger_notification(sender, content)
            self.show_desktop_notification(sender_name, content)

        await save_message(int(self.my_id), timestamp, int(sender), int(self.my_id), content, False)

    async def send_message(self, _):
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
                        self.page.run_task(self._append_message_safe, self.my_id, text, True)
                        await save_message(int(self.my_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                           int(self.my_id), int(self.current_friend_id), text, True)
                    else:
                        self._show_error_snack(resp.json().get("detail", "Ошибка отправки"))
                except Exception as ex:
                    self._show_error_snack(f"Ошибка сети: {ex}")

        asyncio.create_task(do_send())

    def _show_error_snack(self, message: str, bgcolor: str = "red"):
        snack = ft.SnackBar(content=ft.Text(message, color="white"), bgcolor=bgcolor, duration=4000)
        self.page.overlay.append(snack)
        self.page.update()

    async def toggle_strict_mode(self, e):
        enabled = e.control.value
        self.settings["strict_mode"] = enabled
        save_settings(self.settings)
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                await client.post(f"{API_URL}/privacy/set_strict",
                                  json={"user_id": int(self.my_id), "enabled": enabled})
                if enabled: await self.sync_whitelist_to_server()
                self._show_error_snack(f"Privacy mode {'enabled' if enabled else 'disabled'}.", bgcolor="green")
            except Exception as ex:
                self._show_error_snack(f"Failed: {ex}")

    async def sync_whitelist_to_server(self):
        allowed_ids = [int(c["id"]) for c in self.my_contacts]
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                await client.post(f"{API_URL}/privacy/update_whitelist",
                                  json={"user_id": int(self.my_id), "allowed_ids": allowed_ids})
            except:
                pass
