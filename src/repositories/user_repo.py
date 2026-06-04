from core.database import db

class UserRepository:
    
    @staticmethod
    async def create(username, password_hash):
        return await db.fetchval("""
            INSERT INTO users (username, password_hash) 
            VALUES ($1, $2) RETURNING id
        """, username, password_hash)
    
    @staticmethod
    async def get_by_username(username):
        return await db.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            username
        )
    
    @staticmethod
    async def get_by_id(user_id):
        return await db.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )