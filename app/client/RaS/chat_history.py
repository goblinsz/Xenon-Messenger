import os
import json
from datetime import datetime

HISTORY_DIR = "chat_history"


def get_chat_filename(id1: int, id2: int) -> str:
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    return f"chat_{min_id}_{max_id}.json"


def save_message(time:str, sender: int, target: int, content: str, is_outgoing: bool):
    """
    Сохраняет сообщение в локальный JSON-файл.
    :param time: Время отправки
    :param sender: ID отправителя
    :param target: ID получателя
    :param content: Текст сообщения
    :param is_outgoing: True, если сообщение отправлено нами, False, если получено
    """
    os.makedirs(HISTORY_DIR, exist_ok=True)

    filename = os.path.join(HISTORY_DIR, get_chat_filename(sender, target))

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