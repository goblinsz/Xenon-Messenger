from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from bd.bd import (
    init_pool,
    close_pool,
    register_user,
    authenticate_user,
    get_all_users
)

app = FastAPI()



class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/register")
async def register(user: UserCreate):
    try:
        user_id = await register_user(
            user.username,
            user.password
        )

        return {
            "status": "ok",
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/login")
async def login(user: UserLogin):
    name, user_id = await authenticate_user(
        user.username,
        user.password
    )

    if user_id is None:
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
async def get_users():
    return await get_all_users()