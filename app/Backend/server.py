from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
from bd.bd import (
    init_pool, close_pool, register_user, authenticate_user, get_all_users_list,
    get_user_by_username, get_user_profile_by_id, block_user, is_blocked,
    get_or_create_direct_conversation, save_message_db, get_conversation_messages,
    create_group_conversation, set_strict_mode, is_strict_mode, update_whitelist, is_sender_allowed,
    unblock_user, get_block_status
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


class BlockRequest(BaseModel):
    blocker_id: int
    blocked_id: int


class GroupCreate(BaseModel):
    creator_id: int
    name: str
    participant_ids: List[int]


class PrivacyRequest(BaseModel):
    user_id: int
    enabled: bool


class WhitelistRequest(BaseModel):
    user_id: int
    allowed_ids: List[int]

class UnblockRequest(BaseModel):
    blocker_id: int
    blocked_id: int

class BlockStatusRequest(BaseModel):
    user1_id: int
    user2_id: int

@app.post("/register")
async def register(user: UserCreate):
    try:
        return {"status": "ok", "id": await register_user(user.username, user.name, user.password)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login")
async def login(user: UserLogin):
    name, id = await authenticate_user(user.username, user.password)
    if not id: raise HTTPException(status_code=401, detail="Wrong login or password")
    return {"status": "ok", "id": id, "username": user.username, "name": name}


@app.post("/block")
async def block_user_endpoint(req: BlockRequest):
    if req.blocker_id == req.blocked_id: raise HTTPException(status_code=400, detail="You cannot block yourself.")
    try:
        await block_user(req.blocker_id, req.blocked_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unblock")
async def unblock_user_endpoint(req: UnblockRequest):
    try:
        await unblock_user(req.blocker_id, req.blocked_id)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/block_status")
async def get_block_status_endpoint(req: BlockStatusRequest):
    try:
        status = await get_block_status(req.user1_id, req.user2_id)
        return {"status": "ok", **status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/send_message")
async def send_message_endpoint(msg: MessageSend):
    try:
        if msg.sender_id == msg.target_id:
            raise HTTPException(status_code=400, detail="You cannot send messages to yourself.")
        if await is_blocked(blocker_id=msg.target_id, blocked_id=msg.sender_id):
            raise HTTPException(status_code=403, detail="You cannot message this user. They have blocked you.")
        if await is_blocked(blocker_id=msg.sender_id, blocked_id=msg.target_id):
            raise HTTPException(status_code=403, detail="You have blocked this user. Unblock them to send messages.")

        # Strict Mode Check
        if await is_strict_mode(msg.target_id):
            if not await is_sender_allowed(msg.target_id, msg.sender_id):
                raise HTTPException(status_code=403, detail="This user only accepts messages from their contacts.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conv_id = await get_or_create_direct_conversation(msg.sender_id, msg.target_id)
        await save_message_db(conv_id, msg.sender_id, msg.content, timestamp)
        await send(target_id=str(msg.target_id), content=msg.content, sender=str(msg.sender_id), timestamp=timestamp)
        return {"status": "ok", "message": "Sent to queue"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/messages/{id1}/{id2}")
async def get_messages(id1: int, id2: int):
    try:
        conv_id = await get_or_create_direct_conversation(id1, id2)
        return {"status": "ok", "messages": await get_conversation_messages(conv_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/groups/create")
async def create_group_endpoint(req: GroupCreate):
    try:
        participants = set(req.participant_ids)
        participants.add(req.creator_id)
        conv_id = await create_group_conversation(req.name, list(participants))
        return {"status": "ok", "conversation_id": conv_id, "message": f"Group '{req.name}' successfully created!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users")
async def get_user(username: str):
    user = await get_user_by_username(username)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok", "user": user}


@app.get("/users/id/{user_id}")
async def get_user_by_id_endpoint(user_id: int):
    user_data = await get_user_profile_by_id(user_id)
    if not user_data: raise HTTPException(status_code=404, detail="User not found")
    return user_data


@app.get("/users/all")
async def get_all_users():
    try:
        return {"status": "ok", "users": await get_all_users_list()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/privacy/set_strict")
async def set_strict_endpoint(req: PrivacyRequest):
    try:
        await set_strict_mode(req.user_id, req.enabled)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/privacy/update_whitelist")
async def update_whitelist_endpoint(req: WhitelistRequest):
    try:
        await update_whitelist(req.user_id, req.allowed_ids)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))