import flet as ft
import httpx
import os
from settings_manager import load_settings, save_settings, load_private_keys, save_private_keys
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization


API_URL = "http://83.239.75.58:8000"
print(f"Using API_URL: {API_URL}")


def generate_key_pair():
    private_key = x25519.X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return private_bytes.hex(), public_bytes.hex()


async def ensure_public_key_on_server(user_id: str, settings: dict):
    local_entry = None
    for acc in settings.get("accounts", []):
        if acc.get("id") == user_id:
            local_entry = acc
            break

    if local_entry is None:
        local_entry = {
            "id": user_id,
            "username": "",
            "name": "",
            "password": "",
            "private_key": ""
        }
        settings["accounts"].append(local_entry)

    if local_entry.get("private_key"):
        return

    private_keys = load_private_keys()
    recovered_key = private_keys.get(user_id)
    if recovered_key:
        local_entry["private_key"] = recovered_key
        save_settings(settings)
        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.get(f"{API_URL}/check_public_key/{user_id}")
                if resp.status_code == 200:
                    data = resp.json()
                    if not data.get("has_public_key", False):
                        private_bytes = bytes.fromhex(recovered_key)
                        private_key = x25519.X25519PrivateKey.from_private_bytes(private_bytes)
                        public_key = private_key.public_key()
                        public_bytes = public_key.public_bytes(
                            encoding=serialization.Encoding.Raw,
                            format=serialization.PublicFormat.Raw
                        )
                        public_hex = public_bytes.hex()
                        upload_resp = await client.post(f"{API_URL}/upload_public_key", json={
                            "user_id": int(user_id),
                            "public_key": public_hex
                        })
                        if upload_resp.status_code == 200:
                            print("Public key uploaded (recovered) successfully")
            except Exception as e:
                print(f"Error during recovered key upload: {e}")
        return

    private_hex, public_hex = generate_key_pair()
    local_entry["private_key"] = private_hex
    save_settings(settings)

    private_keys[user_id] = private_hex
    save_private_keys(private_keys)

    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            upload_resp = await client.post(f"{API_URL}/upload_public_key", json={
                "user_id": int(user_id),
                "public_key": public_hex
            })
            if upload_resp.status_code == 200:
                print("Public key uploaded (new) successfully")
            else:
                print(f"Failed to upload public key: {upload_resp.text}")
        except Exception as e:
            print(f"Error uploading public key: {e}")


def build_auth_window(page: ft.Page, on_success):
    settings = load_settings()
    page.theme_mode = ft.ThemeMode.DARK if settings.get("theme_mode") == "dark" else ft.ThemeMode.LIGHT
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
            private_hex, public_hex = generate_key_pair()
            payload["public_key"] = public_hex
            temp_private_key = private_hex
        else:
            temp_private_key = None

        async with httpx.AsyncClient(trust_env=False) as client:
            try:
                resp = await client.post(f"{API_URL}{endpoint}", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    user_id = str(data["id"])
                    user_name = data.get("name", uname)
                    user_username = data.get("username", uname)

                    account_entry = None
                    for acc in settings["accounts"]:
                        if acc["username"] == uname:
                            account_entry = acc
                            break
                    if account_entry is None:
                        account_entry = {
                            "id": user_id,
                            "username": user_username,
                            "name": user_name,
                            "password": pwd,
                            "private_key": ""
                        }
                        settings["accounts"].append(account_entry)
                    else:
                        account_entry["id"] = user_id
                        account_entry["name"] = user_name
                        account_entry["password"] = pwd

                    if is_reg and temp_private_key:
                        account_entry["private_key"] = temp_private_key
                        private_keys = load_private_keys()
                        private_keys[user_id] = temp_private_key
                        save_private_keys(private_keys)

                    save_settings(settings)

                    if not is_reg:
                        await ensure_public_key_on_server(user_id, settings)

                    await on_success(user_id, user_name, user_username)
                else:
                    error_text.value = resp.json().get("detail", "Authentication failed")
                    page.update()
            except Exception as ex:
                error_text.value = f"Server error: {ex}"
                print(f"Connection error: {ex} (API_URL={API_URL})")
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
