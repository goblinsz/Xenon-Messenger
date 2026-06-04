import bcrypt
from repositories.user_repo import UserRepository

class AuthService:
    
    @staticmethod
    async def register(username, password):
        existing = await UserRepository.get_by_username(username)
        if existing:
            return False, "Пользователь с таким именем уже существует"
        
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        user_id = await UserRepository.create(username, password_hash)
        return True, user_id
    
    @staticmethod
    async def login(username, password):
        user = await UserRepository.get_by_username(username)
        if not user:
            return False, "Неверное имя пользователя или пароль"
        
        if not bcrypt.checkpw(
            password.encode('utf-8'), 
            user['password_hash'].encode('utf-8')
        ):
            return False, "Неверное имя пользователя или пароль"

        user_data = {
            "id": user['id'],
            "username": user['username'],
            "created_at": user['created_at']
        }
        return True, user_data