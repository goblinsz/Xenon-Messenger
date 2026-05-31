from datetime import date

from PyQt6.lupdate import user
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()

users = []

class User(BaseModel):
    name: str


class Messages(BaseModel):
    message: str
    date: date
    author: User

@app.get("/users")
def get_users():
    return users

@app.post("/users")
def create_user(user: User):
    users.append(user)
    return {"status": "ok"}

@app.delete("/users/{name}")
def delete_user(name: str):
    for user.name in users:
        if user.name == name:
            users.remove(user)
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="User not found")

