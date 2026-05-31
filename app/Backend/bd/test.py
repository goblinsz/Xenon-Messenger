import asyncio

from app.Backend.bd.bd import init_pool, get_all_users, close_pool


async def main():
    await init_pool()

    print(await get_all_users("Fox"))

    await close_pool()

if __name__ == "__main__":
    asyncio.run(main())