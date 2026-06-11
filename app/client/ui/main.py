import flet as ft
import httpx
import aio_pika
import json
import asyncio

API_URL = "http://127.0.0.1:8000"
RABBIT_URL = "amqp://g:g@192.168.1.65/"


class MainWindow:
    def __init__(self, page: ft.Page, my_id: str, my_name: str, on_logout):
        self.page = page
        self.my_id = my_id
        self.my_name = my_name
        self.on_logout = on_logout
        self.current_friend_id = None

        self.status_text = ft.Text(f"Logged in as: {my_name} (ID: {my_id})", size=16, color="gray", weight="bold")
        self.message_history = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=True, controls=[])
        self.friends_list = ft.ListView(expand=1, spacing=10, padding=20, controls=[])

        self.msg_input = ft.TextField(hint_text="Type message...", expand=True)
        self.send_btn = ft.Button("Send", icon=ft.Icons.SEND, on_click=self.send_message)
        self.msg_input.on_submit = self.send_message

        self.left_column = ft.Column(
            controls=[
                ft.Row([ft.Text("My Tribe", size=20, weight="bold"),
                        ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", on_click=lambda _: self.on_logout())]),
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

        self.view = ft.Row(expand=True, controls=[self.left_column, self.right_column])

        asyncio.create_task(self.load_contacts())
        asyncio.create_task(self.listen_to_my_queue())

    def select_friend(self, friend_id: str, friend_name: str):
        self.current_friend_id = friend_id
        self.status_text.value = f"Talking to: {friend_name} (ID: {friend_id})"
        self.message_history.controls.clear()
        self.page.update()
        asyncio.create_task(self.load_chat_history(friend_id))

    async def load_contacts(self):
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/users/all")
                if resp.status_code == 200:
                    data = resp.json()
                    self.friends_list.controls.clear()
                    for user in data.get("users", []):
                        if str(user["id"]) != self.my_id:
                            self.friends_list.controls.append(
                                ft.ListTile(
                                    title=ft.Text(user["name"]),
                                    subtitle=ft.Text(f"@{user['username']}"),
                                    leading=ft.Icon(ft.Icons.PERSON),
                                    on_click=lambda e, uid=str(user["id"]), uname=user["name"]: self.select_friend(uid,
                                                                                                                   uname)
                                )
                            )
                    self.page.update()
            except Exception as ex:
                print(f"Load contacts error: {ex}")

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