import asyncio
import asyncpg
import bcrypt
from typing import Optional, Tuple

DB_CONFIG = {
    "database": "postgres",
    "user": "admin",
    "password": "postgres",
    "host": "192.168.1.65",
    "port": 5432
}

pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global pool
    if not pool:
        pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)

async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None

async def register_user(username: str, name: str, password: str) -> Optional[int]:
    hashed_password = await asyncio.to_thread(
        lambda: bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    )
    async with pool.acquire() as conn:
        id = await conn.fetchval(
            "INSERT INTO users (username, name, password) VALUES ($1, $2, $3) RETURNING id;",
            username, name, hashed_password
        )
    return id

async def authenticate_user(username: str, password: str) -> Tuple[Optional[str], int]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT name, password, id FROM users WHERE username = $1;",
            username
        )
        if row:
            name, stored_password, id = row["name"], row["password"], row["id"]
            is_valid = await asyncio.to_thread(
                bcrypt.checkpw, password.encode('utf-8'), stored_password.encode('utf-8')
            )
            if is_valid:
                return name, id
    return None, 0

async def get_all_users_list():
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, username, name FROM users;")
        return [{"id": row["id"], "username": row["username"], "name": row["name"]} for row in rows]


async def get_chat_history(id1: int, id2: int):
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    table_name = f"chat_{min_id}_{max_id}"

    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            table_name
        )
        if not exists:
            return []

        rows = await conn.fetch(
            f"SELECT time, sender, target, content FROM {table_name} ORDER BY time ASC;"
        )

        return [
            {
                "time": row["time"],
                "sender": str(row["sender"]),
                "target": str(row["target"]),
                "content": row["content"]
            }
            for row in rows
        ]

async def create_table_chat(id1: int, id2: int) -> None:
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    table_name = f"chat_{min_id}_{max_id}"
    async with pool.acquire() as conn:
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                time VARCHAR, 
                sender VARCHAR(10), 
                target VARCHAR(10), 
                content VARCHAR(1000)
            )
        """)

async def filling_the_chat(id1: int, id2: int, content: str, time_str: str):
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    table_name = f"chat_{min_id}_{max_id}"

    async with pool.acquire() as conn:
        await conn.execute(
            f"INSERT INTO {table_name} (time, sender, target, content) VALUES ($1, $2, $3, $4);",
            time_str, str(id1), str(id2), content
        )