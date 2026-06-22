import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "accounts": [],
    "theme": {
        "font_family": "Default",
        "font_size": "16",
        "bg_color": "",
        "bubble_color": "#DCF8C6"
    },
    "theme_mode": "light",
    "private_key": ""  # kept for backward compatibility, but per-account keys are used
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return json.loads(json.dumps(DEFAULT_SETTINGS))
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in DEFAULT_SETTINGS:
                if key not in data:
                    data[key] = DEFAULT_SETTINGS[key]
            # Ensure each account has a private_key field
            for acc in data.get("accounts", []):
                if "private_key" not in acc:
                    acc["private_key"] = ""
            return data
    except Exception:
        return json.loads(json.dumps(DEFAULT_SETTINGS))

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
