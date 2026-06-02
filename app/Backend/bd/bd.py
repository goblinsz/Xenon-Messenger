import asyncio
from time import sleep

import asyncpg
import bcrypt
from typing import Optional, Tuple, List

DB_CONFIG = {
    "database": "postgres",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
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

async def authenticate_user(username: str, password: str) -> Tuple[Optional[str], bool]:
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
    return None, False

async def get_all_users(username: str) -> Tuple[Optional[str], bool]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name FROM users where username = $1;", username)
        if rows:
            id = rows["id"]
            name = rows["name"]
            return name, id
        return None, False

async def delete_user_from_db(id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1;", id)

async def create_table_chat(id1: int, id2: int) -> None:
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    table_name = f"chat{min_id}{max_id}"

    async with pool.acquire() as conn:
        await conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (time VARCHAR, sender VARCHAR(10), target VARCHAR(10), content VARCHAR(1000))")

async def filling_the_chat(id1: int, id2: int, content: str, time:str):
    min_id = min(id1, id2)
    max_id = max(id1, id2)
    table_name = f"chat{min_id}{max_id}"
    async with pool.acquire() as conn:
        sleep(2)
        await conn.fetch(f"INSERT INTO {table_name} VALUES ($3, $2, $1, $4);", str(id2), str(id1), time, content)