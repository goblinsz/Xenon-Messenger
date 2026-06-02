from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bd.bd import (
    init_pool,
    close_pool,
    register_user,
    authenticate_user,
    get_all_users
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()

app = FastAPI(lifespan=lifespan)


async def on_startup():
    print("🚀 FastAPI запускается!")
    await init_pool()

async def on_shutdown():
    print("🛑 FastAPI останавливается!")
    await close_pool()

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserSearch(BaseModel):
    username: str

@app.post("/register")
async def register(user: UserCreate):
    try:
        await init_pool()
        print(user.username, user.password)
        user_id = await register_user(
            user.username,
            user.password
        )

        return {
            "status": "ok",
            "user_id": user_id
        }

    except Exception as e:
        print(f"❌ Ошибка регистрации: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e) + user.username + user.username
        )

@app.post("/login")
async def login(user: UserLogin):
    name, user_id = await authenticate_user(
        user.username,
        user.password
    )

    if user_id is False:
        raise HTTPException(
            status_code=401,
            detail="Wrong login or password"
        )

    return {
        "status": "ok",
        "user_id": user_id,
        "username": name
    }

@app.get("/users")
async def get_users(user: UserSearch):
    username, user_id = await get_all_users(user.username)

    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Username doesn't exist"
        )
    return {
        "status": "ok",
        "user_id": user_id,
        "username": username
    }

