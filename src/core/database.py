import asyncpg
from .config import config

class Database:
    def __init__(self):
        self.pool = None

    async def init_tables(self):
        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await self.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                from_user_id INTEGER REFERENCES users(id),
                to_user_id INTEGER REFERENCES users(id),
                text TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                config.DATABASE_URL,
                min_size=1,
                max_size=5
            )
            print("Подключено к PostgreSQL. Pool создан")
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            raise

    async def close(self):
        await self.pool.close()
        print("Pool закрыт")
    
    # Для insert, update, delete
    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    #Для SELECT (много строк)
    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
        
    #Для SELECT (одна строка)
    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args):
        #Для SELECT (одно значение) — например, RETURNING id"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

db = Database()