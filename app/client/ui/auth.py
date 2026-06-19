import flet as ft
import httpx
from settings_manager import load_settings, save_settings

API_URL = "http://10.0.0.103:8000"


def build_auth_window(page: ft.Page, on_success):
    settings = load_settings()
    saved_accounts = settings.get("accounts", [])

    username = ft.TextField(label="Username", width=300)
    password = ft.TextField(label="Password", password=True, width=300)
    name_field = ft.TextField(label="Full Name", width=300)
    error_text = ft.Text("", color="red", size=14)

    is_registering = False

    accounts_view = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    login_view = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=not bool(saved_accounts)
    )

    async def execute_login(uname, pwd, name_val=None, is_reg=False):
        error_text.value = "Processing..."
        page.update()

        endpoint = "/register" if is_reg else "/login"
        payload = {"username": uname, "password": pwd}
        if is_reg:
            payload["name"] = name_val

        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}{endpoint}", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    user_id = str(data["id"])
                    user_name = data.get("name", uname)
                    user_username = data.get("username", uname)

                    if not any(acc["username"] == uname for acc in settings["accounts"]):
                        settings["accounts"].append({
                            "id": user_id,
                            "username": user_username,
                            "name": user_name,
                            "password": pwd
                        })
                        save_settings(settings)

                    await on_success(user_id, user_name, user_username)
                else:
                    error_text.value = resp.json().get("detail", "Authentication failed")
                    page.update()
            except Exception as ex:
                error_text.value = f"Server error: {ex}"
                page.update()

    def remove_account(uname):
        settings["accounts"] = [acc for acc in settings["accounts"] if acc["username"] != uname]
        save_settings(settings)
        build_account_list()
        if not settings["accounts"]:
            show_login_form()
        page.update()

    def build_account_list():
        accounts_view.controls.clear()
        accounts_view.controls.append(ft.Text("Saved Accounts", size=20, weight="bold"))
        for acc in settings["accounts"]:
            accounts_view.controls.append(
                ft.Row([
                    ft.Button(
                        f"Log in as {acc['name']}",
                        icon=ft.Icons.PERSON,
                        on_click=lambda e, u=acc['username'], p=acc['password']: page.run_task(execute_login, u, p)
                    ),
                    ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Remove Account",
                                  on_click=lambda e, u=acc['username']: remove_account(u))
                ], alignment=ft.MainAxisAlignment.CENTER)
            )
        accounts_view.controls.append(ft.TextButton("Add another account", on_click=show_login_form))

    def show_login_form(e=None):
        accounts_view.visible = False
        login_view.visible = True
        rebuild_form()
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
        await execute_login(username.value, password.value, name_field.value, is_registering)

    def rebuild_form():
        nonlocal is_registering

        name_field.visible = is_registering

        action_btn = ft.Button(
            "Register" if is_registering else "Login",
            width=300,
            on_click=handle_auth
        )
        toggle_btn = ft.TextButton(
            "Already have an account? Login" if is_registering else "Need an account? Register",
            on_click=toggle_mode
        )

        login_view.controls = [
            username, password, name_field, error_text, action_btn, toggle_btn
        ]

    def toggle_mode(e):
        nonlocal is_registering
        is_registering = not is_registering
        error_text.value = ""

        rebuild_form()
        page.update()

    if saved_accounts:
        build_account_list()
    else:
        rebuild_form()

    return ft.Column(
        controls=[
            ft.Text("Xenon Messenger", size=32, weight="bold"),
            ft.Divider(),
            accounts_view,
            login_view
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )