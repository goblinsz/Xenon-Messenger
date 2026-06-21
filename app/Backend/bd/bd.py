import asyncio
import asyncpg
import bcrypt
import os
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv

# Locate .env relative to this script (two levels up from app/Backend/bd/bd.py)
_script_dir = os.path.abspath(os.path.dirname(__file__))
_dotenv_path = os.path.join(_script_dir, '..', '..', '.env')
if os.path.isfile(_dotenv_path):
    load_dotenv(_dotenv_path)
else:
    load_dotenv()  # fallback

_db_host = os.getenv("DB_HOST")
_db_port = os.getenv("DB_PORT")
_db_name = os.getenv("DB_NAME")
_db_user = os.getenv("DB_USER")
_db_password = os.getenv("DB_PASSWORD")

missing = []
if _db_host is None:
    missing.append("DB_HOST")
if _db_port is None:
    missing.append("DB_PORT")
if _db_name is None:
    missing.append("DB_NAME")
if _db_user is None:
    missing.append("DB_USER")
if _db_password is None:
    missing.append("DB_PASSWORD")
if missing:
    raise EnvironmentError(f"Missing environment variables in .env file: {', '.join(missing)}")

DB_CONFIG = {
    "database": _db_name,
    "user": _db_user,
    "password": _db_password,
    "host": _db_host,
    "port": int(_db_port)
}
pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global pool
    if not pool:
        pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)
        await init_db_schema()

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None

async def init_db_schema():
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL, 
                name VARCHAR(100) NOT NULL, password VARCHAR(100) NOT NULL, 
                strict_mode BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS blocked_users (
                blocker_id INT REFERENCES users(id), blocked_id INT REFERENCES users(id),
                PRIMARY KEY (blocker_id, blocked_id)
            );
            CREATE TABLE IF NOT EXISTS allowed_contacts (
                user_id INT REFERENCES users(id), allowed_id INT REFERENCES users(id),
                PRIMARY KEY (user_id, allowed_id)
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY, is_group BOOLEAN DEFAULT FALSE, name VARCHAR(100)
            );
            CREATE TABLE IF NOT EXISTS participants (
                conversation_id INT REFERENCES conversations(id), user_id INT REFERENCES users(id),
                PRIMARY KEY (conversation_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY, conversation_id INT REFERENCES conversations(id), 
                sender_id INT REFERENCES users(id), content TEXT NOT NULL, created_at VARCHAR(50) NOT NULL
            );
        """)

async def register_user(username: str, name: str, password: str) -> int:
    hashed = await asyncio.to_thread(lambda: bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
    async with pool.acquire() as conn:
        try:
            return await conn.fetchval("INSERT INTO users (username, name, password) VALUES ($1, $2, $3) RETURNING id;", username, name, hashed)
        except asyncpg.exceptions.UniqueViolationError:
            raise Exception("Username already exists")

async def authenticate_user(username: str, password: str) -> Tuple[Optional[str], int]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name, password, id FROM users WHERE username = $1;", username)
        if row and await asyncio.to_thread(bcrypt.checkpw, password.encode('utf-8'), row["password"].encode('utf-8')):
            return row["name"], row["id"]
    return None, 0

async def get_user_by_username(username: str):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, username, name FROM users WHERE username = $1;", username)
        return dict(row) if row else None

async def get_user_profile_by_id(user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, username, name FROM users WHERE id = $1;", user_id)
        return dict(row) if row else None

async def get_all_users_list():
    async with pool.acquire() as conn:
        return [dict(r) for r in await conn.fetch("SELECT id, username, name FROM users;")]

async def block_user(blocker_id: int, blocked_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO blocked_users (blocker_id, blocked_id) VALUES ($1, $2) ON CONFLICT DO NOTHING;", blocker_id, blocked_id)

async def is_blocked(blocker_id: int, blocked_id: int) -> bool:
    async with pool.acquire() as conn:
        return (await conn.fetchval("SELECT 1 FROM blocked_users WHERE blocker_id = $1 AND blocked_id = $2;", blocker_id, blocked_id)) is not None

async def set_strict_mode(user_id: int, enabled: bool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET strict_mode = $1 WHERE id = $2;", enabled, user_id)

async def is_strict_mode(user_id: int) -> bool:
    async with pool.acquire() as conn:
        val = await conn.fetchval("SELECT strict_mode FROM users WHERE id = $1;", user_id)
        return bool(val)

async def update_whitelist(user_id: int, allowed_ids: list[int]) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM allowed_contacts WHERE user_id = $1;", user_id)
            if allowed_ids:
                await conn.executemany("INSERT INTO allowed_contacts (user_id, allowed_id) VALUES ($1, $2);", [(user_id, aid) for aid in allowed_ids])

async def is_sender_allowed(target_id: int, sender_id: int) -> bool:
    async with pool.acquire() as conn:
        return (await conn.fetchval("SELECT 1 FROM allowed_contacts WHERE user_id = $1 AND allowed_id = $2;", target_id, sender_id)) is not None

async def get_or_create_direct_conversation(user1_id: int, user2_id: int) -> int:
    async with pool.acquire() as conn:
        conv_id = await conn.fetchval("""
            SELECT c.id FROM conversations c 
            JOIN participants p1 ON c.id = p1.conversation_id 
            JOIN participants p2 ON c.id = p2.conversation_id
            WHERE c.is_group = FALSE AND p1.user_id = $1 AND p2.user_id = $2;
        """, user1_id, user2_id)
        if conv_id: return conv_id
        async with conn.transaction():
            conv_id = await conn.fetchval("INSERT INTO conversations (is_group) VALUES (FALSE) RETURNING id;")
            await conn.execute("INSERT INTO participants (conversation_id, user_id) VALUES ($1, $2), ($1, $3);", conv_id, user1_id, user2_id)
            return conv_id

async def save_message_db(conversation_id: int, sender_id: int, content: str, time_str: str):
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO messages (conversation_id, sender_id, content, created_at) VALUES ($1, $2, $3, $4);", conversation_id, sender_id, content, time_str)

async def get_conversation_messages(conversation_id: int):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT created_at as time, sender_id as sender, content FROM messages WHERE conversation_id = $1 ORDER BY id ASC;", conversation_id)
        return [dict(r) for r in rows]

async def create_group_conversation(name: str, participant_ids: list[int]) -> int:
    async with pool.acquire() as conn:
        async with conn.transaction():
            conv_id = await conn.fetchval("INSERT INTO conversations (is_group, name) VALUES (TRUE, $1) RETURNING id;", name)
            await conn.executemany("INSERT INTO participants (conversation_id, user_id) VALUES ($1, $2);", [(conv_id, pid) for pid in participant_ids])
            return conv_id

async def unblock_user(blocker_id: int, blocked_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM blocked_users WHERE blocker_id = $1 AND blocked_id = $2;",
            blocker_id, blocked_id
        )

async def get_block_status(user1_id: int, user2_id: int) -> dict:
    async with pool.acquire() as conn:
        i_blocked = await conn.fetchval(
            "SELECT 1 FROM blocked_users WHERE blocker_id = $1 AND blocked_id = $2;",
            user1_id, user2_id
        )
        they_blocked = await conn.fetchval(
            "SELECT 1 FROM blocked_users WHERE blocker_id = $1 AND blocked_id = $2;",
            user2_id, user1_id
        )
        return {
            "i_blocked_them": i_blocked is not None,
            "they_blocked_me": they_blocked is not None
        }

async def get_user_conversations(user_id: int):
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.name, c.is_group 
            FROM conversations c
            JOIN participants p ON c.id = p.conversation_id
            WHERE p.user_id = $1 AND c.is_group = TRUE;
        """, user_id)
        return [dict(r) for r in rows]

async def get_conversation_participants(conversation_id: int):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM participants WHERE conversation_id = $1;", conversation_id)
        return [r['user_id'] for r in rows]
