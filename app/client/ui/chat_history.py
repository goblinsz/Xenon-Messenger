import os
import json

HISTORY_DIR = "chat_history"


def get_chat_filename(owner_id: int, id1: int, id2: int) -> str:
    user_dir = os.path.join(HISTORY_DIR, str(owner_id))
    os.makedirs(user_dir, exist_ok=True)

    min_id = min(id1, id2)
    max_id = max(id1, id2)
    return os.path.join(user_dir, f"chat_{min_id}_{max_id}.json")


async def save_message(owner_id: int, time: str, sender: int, target: int, content: str, is_outgoing: bool):
    filename = get_chat_filename(owner_id, sender, target)
    message_obj = {
        "time": time,
        "sender": sender,
        "target": target,
        "content": content,
        "is_outgoing": is_outgoing
    }

    history = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    history.append(message_obj)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


async def read_chat(owner_id: int, sender: int, target: int):
    filename = get_chat_filename(owner_id, sender, target)
    if not os.path.exists(filename):
        return []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)

        history.sort(key=lambda msg: msg.get('time', ''))
        return history

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading history: {e}")
        return []



def get_group_filename(owner_id: int, conv_id: int) -> str:
    user_dir = os.path.join(HISTORY_DIR, str(owner_id))
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, f"group_{conv_id}.json")


async def save_group_message(owner_id: int, conv_id: int, time: str, sender: int, content: str):
    filename = get_group_filename(owner_id, conv_id)
    message_obj = {"time": time, "sender": sender, "content": content}

    history = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    history.append(message_obj)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


async def read_group_chat(owner_id: int, conv_id: int):
    filename = get_group_filename(owner_id, conv_id)
    if not os.path.exists(filename):
        return []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)

        history.sort(key=lambda msg: msg.get('time', ''))
        return history

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading group history: {e}")
        return []