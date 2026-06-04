from core.database import db

class MessageRepository:
    
    @staticmethod
    async def create(from_user_id: int, to_user_id: int, text: str) -> int:
        return await db.fetchval("""
            INSERT INTO messages (from_user_id, to_user_id, text) 
            VALUES ($1, $2, $3) RETURNING id
        """, from_user_id, to_user_id, text)
    
    @staticmethod
    async def get_dialog(user1_id: int, user2_id: int, limit: int = 50):
        return await db.fetch("""
            SELECT 
                m.id,
                m.text,
                m.created_at,
                m.is_read,
                m.from_user_id,
                m.to_user_id,
                u.username as sender_name
            FROM messages m
            JOIN users u ON m.from_user_id = u.id
            WHERE (m.from_user_id = $1 AND m.to_user_id = $2)
               OR (m.from_user_id = $2 AND m.to_user_id = $1)
            ORDER BY m.created_at ASC
            LIMIT $3
        """, user1_id, user2_id, limit)
    
    @staticmethod
    async def mark_as_read(message_id: int):
        await db.execute("""
            UPDATE messages 
            SET is_read = TRUE 
            WHERE id = $1
        """, message_id)
    
    @staticmethod
    async def get_unread_count(user_id: int) -> int:
        return await db.fetchval("""
            SELECT COUNT(*) 
            FROM messages 
            WHERE to_user_id = $1 AND is_read = FALSE
        """, user_id)
