import os
import json


HISTORY_DIR = "chat_history"


async def get_chat_filename(id1: int, id2: int) -> str:
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    return f"chat_{min_id}_{max_id}.json"


async def save_message(time:str, sender: int, target: int, content: str, is_outgoing: bool):
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


async def read_chat(sender: int, target: int):
    filename = os.path.join(HISTORY_DIR, get_chat_filename(sender, target))

    if not os.path.exists(filename):
        return "a"

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)

        history.sort(key=lambda msg: msg.get('time', 'sender', 'target', 'content', 'is_outgoing'))
        return history

    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Ошибка чтения истории: {e}")
        return "a"