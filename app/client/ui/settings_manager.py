import os
import json
import platformdirs
import copy

APP_DATA_DIR = platformdirs.user_data_dir(appname="XenonMessenger", appauthor="Xenon", roaming=False)
os.makedirs(APP_DATA_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(APP_DATA_DIR, "settings.json")
PRIVATE_KEYS_FILE = os.path.join(APP_DATA_DIR, "private_keys.json")

DEFAULT_SETTINGS = {
    "accounts": [],
    "theme": {
        "font_family": "Default",
        "font_size": "16",
        "bg_color": "",
        "bubble_color": "#DCF8C6"
    },
    "theme_mode": "light",
    "private_key": ""
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        # Возвращаем глубокую копию, чтобы изменения в loaded settings не меняли DEFAULT_SETTINGS
        return copy.deepcopy(DEFAULT_SETTINGS)

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Гарантируем наличие всех ключей по умолчанию
        for key in DEFAULT_SETTINGS:
            if key not in data:
                data[key] = copy.deepcopy(DEFAULT_SETTINGS[key])

        # Гарантируем наличие private_key в каждом аккаунте
        for acc in data.get("accounts", []):
            if "private_key" not in acc:
                acc["private_key"] = ""

        return data
    except Exception as e:
        print(f"Error loading settings, using defaults: {e}")
        return copy.deepcopy(DEFAULT_SETTINGS)


def save_settings(settings):
    # Убеждаемся, что папка существует (на случай если её удалили вручную)
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)


def load_private_keys():
    if not os.path.exists(PRIVATE_KEYS_FILE):
        return {}
    try:
        with open(PRIVATE_KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading private keys: {e}")
        return {}


def save_private_keys(private_keys):
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    with open(PRIVATE_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(private_keys, f, indent=4, ensure_ascii=False)