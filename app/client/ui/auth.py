import flet as ft
import httpx

API_URL = "http://127.0.0.1:8000"


def build_auth_window(page, on_success):
    username = ft.TextField(label="Username", width=300)
    password = ft.TextField(label="Password", password=True, width=300)
    name_field = ft.TextField(label="Full Name (for registration)", width=300, visible=False)
    error_text = ft.Text("", color="red", size=14)

    is_registering = False

    # Define buttons FIRST so toggle_mode can see them
    action_btn = ft.Button("Login", width=300)
    toggle_btn = ft.TextButton("Need an account? Register")

    def toggle_mode(e):
        nonlocal is_registering

        # 1. Flip the state FIRST
        is_registering = not is_registering

        # 2. Update UI based on the NEW state
        name_field.visible = is_registering

        if is_registering:
            action_btn.text = "Register"
            toggle_btn.text = "Already have an account? Login"
        else:
            action_btn.text = "Login"
            toggle_btn.text = "Need an account? Register"

        error_text.value = ""

        # 3. FORCE UPDATE each widget individually
        # This is the missing piece! page.update() is often too slow or misses nested widgets.
        name_field.update()
        action_btn.update()
        toggle_btn.update()
        error_text.update()

    async def handle_auth(e):
        if not username.value or not password.value:
            error_text.value = "Username and password required"
            error_text.update()
            return
        if is_registering and not name_field.value:
            error_text.value = "Full name required for registration"
            error_text.update()
            return

        error_text.value = "Processing..."
        error_text.update()

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
                    error_text.update()
            except Exception as ex:
                error_text.value = f"Server error: {ex}"
                error_text.update()

    action_btn.on_click = handle_auth
    toggle_btn.on_click = toggle_mode

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