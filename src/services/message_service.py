from repositories.message_repo import MessageRepository
from repositories.user_repo import UserRepository

class MessageService:
    
    @staticmethod
    async def send_message(from_username: str, to_username: str, text: str):
        from_user = await UserRepository.get_by_username(from_username)
        if not from_user:
            return False, "Отправитель не найден"
        
        to_user = await UserRepository.get_by_username(to_username)
        if not to_user:
            return False, "Получатель не найден"
        
        message_id = await MessageRepository.create(
            from_user['id'], 
            to_user['id'], 
            text
        )
        
        return True, {
            "message_id": message_id,
            "from": from_username,
            "to": to_username,
            "text": text
        }
    
    @staticmethod
    async def get_dialog(username1: str, username2: str, limit: int = 50):
        user1 = await UserRepository.get_by_username(username1)
        user2 = await UserRepository.get_by_username(username2)
        
        if not user1 or not user2:
            return False, "Пользователь не найден"
        
        messages = await MessageRepository.get_dialog(
            user1['id'], 
            user2['id'], 
            limit
        )
        
        return True, messages
    
    @staticmethod
    async def get_unread_count(username: str):
        user = await UserRepository.get_by_username(username)
        if not user:
            return False, "Пользователь не найден"
        
        count = await MessageRepository.get_unread_count(user['id'])
        return True, count