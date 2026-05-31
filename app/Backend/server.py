from fastapi import FastAPI

app = FastAPI()

users = ["Mike", "John", "Ivan"]


@app.get("/users")
def get_users():
    return users

@app.post("/users")
def create_user(name: str):
    users.append(name.capitalize())
    return {"status": "ok"}

@app.delete("/users/{name}")
def delete_user(name: str):
    if name in users:
        users.remove(name)
        return {"status": "ok"}
    else:
        return {"status": "404"}

