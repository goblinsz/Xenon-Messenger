from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from bd.bd import (
    init_pool,
    close_pool,
    register_user,
    authenticate_user,
    get_all_users_list,
    create_table_chat,
    filling_the_chat,
    get_chat_history,
    get_user_by_username
)
from sendk import send


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan)


class UserCreate(BaseModel):
    username: str
    name: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class MessageSend(BaseModel):
    sender_id: int
    target_id: int
    content: str


@app.post("/register")
async def register(user: UserCreate):
    try:
        id = await register_user(user.username, user.name, user.password)
        return {"status": "ok", "id": id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login")
async def login(user: UserLogin):
    username, id = await authenticate_user(user.username, user.password)
    if not id:
        raise HTTPException(status_code=401, detail="Wrong login or password")
    return {"status": "ok", "id": id, "username": username}


@app.post("/send_message")
async def send_message_endpoint(msg: MessageSend):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await create_table_chat(msg.sender_id, msg.target_id)
        await filling_the_chat(msg.sender_id, msg.target_id, msg.content, timestamp)

        await send(
            target_id=str(msg.target_id),
            content=msg.content,
            sender=str(msg.sender_id),
            timestamp=timestamp
        )

        return {"status": "ok", "message": "Sent to queue"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{id1}/{id2}")
async def get_messages(id1: int, id2: int):
    try:
        history = await get_chat_history(id1, id2)
        return {"status": "ok", "messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
async def get_user(username: str):
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user": user}


@app.get("/users/all")
async def get_all_users():
    try:
        users = await get_all_users_list()
        return {"status": "ok", "users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))