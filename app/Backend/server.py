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
    name: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserSearch(BaseModel):
    name: str

@app.post("/register")
async def register(user: UserCreate):
    try:
        await init_pool()
        id = await register_user(
            user.username,
            user.name,
            user.password
        )

        return {
            "status": "ok",
            "id": id
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/login")
async def login(user: UserLogin):
    username, id = await authenticate_user(
        user.username,
        user.password
    )

    if id is False:
        raise HTTPException(
            status_code=401,
            detail="Wrong login or password"
        )

    return {
        "status": "ok",
        "id": id,
        "username": username
    }

@app.get("/users")
async def get_users(user: UserSearch):
    name, id = await get_all_users(user.username)

    if name is None:
        raise HTTPException(
            status_code=401,
            detail="Name doesn't exist"
        )
    return {
        "status": "ok",
        "id": id,
        "username": name
    }