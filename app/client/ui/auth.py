import flet as ft
import httpx
import asyncio

API_URL = "http://127.0.0.1:8000"


def build_auth_window(page, on_success):
    username = ft.TextField(label="Username", width=300)
    password = ft.TextField(label="Password", password=True, width=300)
    name_field = ft.TextField(label="Full Name (for registration)", width=300, visible=False)
    error_text = ft.Text("", color="red", size=14)

    is_registering = False

    def toggle_mode(e):
        nonlocal is_registering
        is_registering = not is_registering
        name_field.visible = is_registering
        action_btn.text = "Register" if is_registering else "Login"
        toggle_btn.text = "Already have an account? Login" if is_registering else "Need an account? Register"
        error_text.value = ""
        page.update()

    async def handle_auth(e):
        if not username.value or not password.value:
            error_text.value = "Username and password required"
            page.update()
            return
        if is_registering and not name_field.value:
            error_text.value = "Full name required for registration"
            page.update()
            return

        error_text.value = "Processing..."
        page.update()

        endpoint = "/register" if is_registering else "/login"
        payload = {"username": username.value, "password": password.value}
        if is_registering:
            payload["name"] = name_field.value

        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}{endpoint}", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    on_success(str(data["id"]), data.get("username", username.value))
                else:
                    error_text.value = resp.json().get("detail", "Authentication failed")
                    page.update()
            except Exception as ex:
                error_text.value = f"Server error: {ex}"
                page.update()

    action_btn = ft.Button("Login", on_click=handle_auth, width=300)
    toggle_btn = ft.TextButton("Need an account? Register", on_click=toggle_mode)

    return ft.Column(
        controls=[
            ft.Text("Xenon Messenger", size=32, weight="bold"),
            ft.Divider(),
            username,
            password,
            name_field,
            error_text,
            action_btn,
            toggle_btn
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )