import asyncio
import asyncpg
import bcrypt
from typing import Optional, Tuple, List

DB_CONFIG = {
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "10.0.0.103",
    "port": 5432
}

pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)

async def close_pool():
    global pool
    if pool:
        await pool.close()

async def register_user(name: str, email: str, password: str) -> Optional[int]:
    hashed_password = await asyncio.to_thread(
        lambda: bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    )
    async with pool.acquire() as conn:
        user_id = await conn.fetchval(
            "INSERT INTO users (name, email, password) VALUES ($1, $2, $3) RETURNING id;",
            name, email, hashed_password
        )
    return user_id

async def authenticate_user(email: str, password: str) -> Tuple[Optional[str], bool]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT name, password, user_id FROM users WHERE email = $1;",
            email
        )
    if row:
        name, stored_password, user_id = row["name"], row["password"], row["user_id"]
        is_valid = await asyncio.to_thread(
            bcrypt.checkpw, password.encode('utf-8'), stored_password.encode('utf-8')
        )
        if is_valid:
            return name, user_id
    return None, False

async def get_all_users(name: str) -> List[tuple]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, name, email FROM users where name = $1;", name)
        return [tuple(row) for row in rows]

async def delete_user_from_db(id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1;", id)