import asyncio

from app.Backend.bd.bd import init_pool, close_pool, register_user


async def main():
    await init_pool()

    await register_user("dddededede", "eefefefefafsfs")

    await close_pool()

if __name__ == "__main__":
    asyncio.run(main())