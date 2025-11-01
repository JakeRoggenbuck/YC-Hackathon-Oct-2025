"""
INTENTIONAL BUGS IN THIS API (for testing purposes):

1. POST /users - Returns 200 instead of 201 for successful creation
2. GET /users/{user_id} - Doesn't handle non-existent user_id (crashes instead of 404)
3. PUT /users/{user_id} - Doesn't validate if user exists before updating
4. DELETE /users/{user_id} - Returns wrong status code (200 with content instead of 204)
5. GET /users - Pagination parameters don't work correctly (skip/limit ignored)
6. POST /users - Doesn't validate duplicate email addresses
7. PUT /users/{user_id} - Allows partial updates but crashes on missing fields
8. GET /users/search - Query parameter is case-sensitive when it shouldn't be
9. POST /login - Returns 200 even with wrong credentials
10. GET /users/{user_id}/posts - Returns all posts instead of user-specific posts

These bugs can only be discovered through proper API testing with various request combinations.
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List

app = FastAPI(title="Buggy User API", version="1.0.0")

# Local JSON storage using dict
users_db = {}
posts_db = {}
user_id_counter = 1
post_id_counter = 1


class User(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


class Post(BaseModel):
    title: str
    content: str
    user_id: int


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: int


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/")
def read_root():
    return {"message": "Welcome to the Buggy User API"}


# BUG 1: Returns 200 instead of 201
@app.post("/users")
def create_user(user: User):
    global user_id_counter
    
    # BUG 6: Doesn't check for duplicate emails
    user_id = user_id_counter
    users_db[user_id] = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "age": user.age
    }
    user_id_counter += 1
    
    # BUG 1: Should return 201, but returns 200
    return users_db[user_id]


# BUG 2: Crashes on non-existent user_id
@app.get("/users/{user_id}")
def get_user(user_id: int):
    # BUG 2: No error handling for missing user
    return users_db[user_id]


# BUG 5: Pagination doesn't work
@app.get("/users")
def get_users(skip: int = Query(0), limit: int = Query(10)):
    # BUG 5: skip and limit are ignored
    return list(users_db.values())


# BUG 8: Search is case-sensitive
@app.get("/users/search")
def search_users(q: str = Query(...)):
    results = []
    for user in users_db.values():
        # BUG 8: Should be case-insensitive but isn't
        if q in user["name"]:
            results.append(user)
    return results


# BUG 3 & 7: Doesn't validate user exists and crashes on missing fields
@app.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    # BUG 3: Doesn't check if user exists
    # BUG 7: Assumes all fields are present, crashes if trying to access missing fields
    users_db[user_id]["name"] = user.name
    users_db[user_id]["email"] = user.email
    users_db[user_id]["age"] = user.age
    
    return users_db[user_id]


# BUG 4: Returns wrong status code
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    if user_id in users_db:
        del users_db[user_id]
    
    # BUG 4: Should return 204 with no content, but returns 200 with content
    return {"message": "User deleted"}


# BUG 9: Returns 200 even with wrong credentials
@app.post("/login")
def login(login_data: LoginRequest):
    # BUG 9: Always returns success, doesn't validate credentials
    return {
        "status": "success",
        "message": "Login successful",
        "token": "fake-jwt-token-12345"
    }


@app.post("/users/{user_id}/posts")
def create_post(user_id: int, post: Post):
    global post_id_counter
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    post_id = post_id_counter
    posts_db[post_id] = {
        "id": post_id,
        "title": post.title,
        "content": post.content,
        "user_id": post.user_id
    }
    post_id_counter += 1
    
    return posts_db[post_id]


# BUG 10: Returns all posts instead of user-specific posts
@app.get("/users/{user_id}/posts")
def get_user_posts(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    # BUG 10: Returns all posts, doesn't filter by user_id
    return list(posts_db.values())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
