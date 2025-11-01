"""
INTENTIONAL BUGS IN THIS API (Import, Edge Cases, Validation Issues):

1. Missing import error handling - crashes when optional dependency not available
2. Circular import issues in helper modules
3. Zero division errors in statistics calculations
4. Off-by-one errors in array indexing and pagination
5. Unicode/encoding issues with special characters
6. Regex denial of service (ReDoS) vulnerability
7. Missing validation for email format allowing invalid emails
8. Integer boundary cases (MIN_INT, MAX_INT) causing crashes
9. Division by zero in average calculations
10. Null/None handling - doesn't distinguish between null and missing fields
11. Array index out of bounds on empty collections
12. Improper handling of negative numbers in calculations
13. JSON parsing errors on malformed input not caught
14. File path traversal vulnerability in file operations
15. Recursion depth issues causing stack overflow
16. Improper handling of very large numbers (BigInt needed)
17. Date parsing accepts invalid dates (Feb 30, etc.)
18. No validation on enum values allowing arbitrary strings
19. String length validation missing causing buffer issues
20. Type coercion issues mixing strings and numbers

These are subtle validation and edge case bugs that pass basic testing.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
import re
import json
import math

# BUG 1: Import without error handling - crashes if numpy not installed
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    # BUG 1: Code doesn't handle this gracefully in endpoints
    NUMPY_AVAILABLE = False

app = FastAPI(title="Edge Case & Validation Bug API", version="3.0.0")

# In-memory storage
users_db = {}
posts_db = {}
analytics_db = {"views": [], "clicks": []}
user_id_counter = 1


class User(BaseModel):
    username: str
    email: str  # BUG 7: No email format validation
    age: int
    bio: Optional[str] = None
    tags: List[str] = []
    
    # BUG 7: Validator doesn't actually validate email properly
    @validator('email')
    def validate_email(cls, v):
        # BUG 7: Accepts emails like "test@", "test", "@example.com"
        if '@' in v:  # Too simple, allows invalid emails
            return v
        raise ValueError('Email must contain @')


class Post(BaseModel):
    title: str
    content: str
    author_id: int
    published_date: str  # BUG 17: String date with no validation
    status: str  # BUG 18: No enum validation
    rating: Optional[float] = None


class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = {}
    limit: int = 10


# BUG 6: ReDoS vulnerability
UNSAFE_REGEX = re.compile(r'^(a+)+b$')  # Catastrophic backtracking


@app.get("/")
def root():
    return {"message": "Edge Case Bug API"}


@app.post("/users")
def create_user(user: User):
    """
    BUG 8: No validation for integer boundaries
    BUG 19: No string length validation
    """
    global user_id_counter
    
    # BUG 8: Age can be negative, zero, or MAX_INT
    # No validation for reasonable ranges
    if user.age < 0:
        # This check is here but doesn't run for age=0 or very large values
        pass
    
    # BUG 19: Username can be empty string or extremely long
    # No length validation causes issues
    
    user_id = user_id_counter
    users_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "age": user.age,
        "bio": user.bio,
        "tags": user.tags
    }
    user_id_counter += 1
    
    return users_db[user_id]


# BUG 3: Division by zero
@app.get("/users/{user_id}/stats")
def get_user_stats(user_id: int):
    """
    BUG 3 & 9: Division by zero in calculations
    BUG 11: Array index out of bounds on empty collections
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_posts = [p for p in posts_db.values() if p.get("author_id") == user_id]
    
    # BUG 9: Division by zero when user has no posts
    total_ratings = sum(p.get("rating", 0) for p in user_posts if p.get("rating"))
    avg_rating = total_ratings / len(user_posts)  # BUG 9: Crashes on empty list
    
    # BUG 11: Index out of bounds
    latest_post = user_posts[0]  # BUG 11: Crashes if user_posts is empty
    
    return {
        "total_posts": len(user_posts),
        "average_rating": avg_rating,
        "latest_post": latest_post
    }


# BUG 4: Off-by-one error in pagination
@app.get("/users")
def get_users(page: int = Query(1), per_page: int = Query(10)):
    """
    BUG 4: Off-by-one error in pagination logic
    """
    users_list = list(users_db.values())
    total = len(users_list)
    
    # BUG 4: Off-by-one - page 1 should be items 0-9, but this does 1-10
    start = page * per_page  # Should be (page - 1) * per_page
    end = start + per_page
    
    # BUG 11: Can go out of bounds
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "data": users_list[start:end]  # Silently returns empty if out of bounds
    }


# BUG 5: Unicode/encoding issues
@app.post("/posts")
def create_post(post: Post):
    """
    BUG 5: Unicode handling issues
    BUG 17: Date validation missing
    BUG 18: Enum/status validation missing
    """
    global posts_db
    
    # BUG 5: Doesn't handle emoji, special unicode characters properly
    # Title with certain unicode can cause issues
    cleaned_title = post.title.encode('ascii', errors='ignore').decode('ascii')
    
    # BUG 17: Accepts invalid dates
    # No validation, accepts "2025-02-30", "2025-13-01", "not-a-date"
    
    # BUG 18: Status has no enum validation
    # Should be ["draft", "published", "archived"]
    # But accepts anything: "deleted", "xyz", "123"
    
    post_id = len(posts_db) + 1
    posts_db[post_id] = {
        "id": post_id,
        "title": cleaned_title,  # BUG 5: Lost unicode characters
        "content": post.content,
        "author_id": post.author_id,
        "published_date": post.published_date,
        "status": post.status,
        "rating": post.rating
    }
    
    return posts_db[post_id]


# BUG 6: ReDoS vulnerability
@app.get("/validate-pattern")
def validate_pattern(input_string: str = Query(...)):
    """
    BUG 6: Catastrophic backtracking - can DOS the server
    """
    # BUG 6: With input like "aaaaaaaaaaaaaaaaaaaaaa" this takes exponential time
    if UNSAFE_REGEX.match(input_string):
        return {"valid": True}
    return {"valid": False}


# BUG 1: Missing import handling
@app.post("/analyze-data")
def analyze_data(numbers: List[float]):
    """
    BUG 1: Crashes if numpy not installed
    BUG 12: Doesn't handle negative numbers properly
    """
    if not NUMPY_AVAILABLE:
        # BUG 1: This check exists but the code still tries to use numpy below
        pass
    
    # BUG 1: Crashes here if numpy not available
    arr = np.array(numbers)  # NameError if numpy not installed
    
    # BUG 12: sqrt of negative number = NaN, not handled
    sqrt_values = [math.sqrt(x) for x in numbers]  # Crashes on negative
    
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "sqrt_mean": sum(sqrt_values) / len(sqrt_values)
    }


# BUG 10: Null/None handling
@app.put("/users/{user_id}")
def update_user(user_id: int, updates: Dict[str, Any]):
    """
    BUG 10: Can't distinguish between null value and missing field
    BUG 20: Type coercion issues
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    # BUG 10: updates = {"bio": null} should clear bio
    # but updates = {} should leave bio unchanged
    # This code treats both the same
    for key, value in updates.items():
        # BUG 20: No type checking - can assign string to age, number to username
        user[key] = value
    
    return user


# BUG 13: JSON parsing errors
@app.post("/import-json")
def import_json(raw_json: str):
    """
    BUG 13: No error handling for malformed JSON
    """
    # BUG 13: Crashes on invalid JSON instead of returning error
    data = json.loads(raw_json)  # No try-except
    
    return {"imported": len(data), "data": data}


# BUG 14: Path traversal vulnerability
@app.get("/files/{filename}")
def get_file(filename: str):
    """
    BUG 14: Path traversal vulnerability - no sanitization
    """
    # BUG 14: filename could be "../../etc/passwd"
    # No validation or sanitization
    file_path = f"/app/data/{filename}"
    
    # In a real app, this would read the file
    # Allowing access to system files
    return {"file_path": file_path, "warning": "Path traversal possible"}


# BUG 15: Recursion depth issues
def calculate_fibonacci(n: int) -> int:
    """BUG 15: Stack overflow on large n"""
    # BUG 15: No tail recursion optimization, no iteration
    if n <= 1:
        return n
    return calculate_fibonacci(n - 1) + calculate_fibonacci(n - 2)


@app.get("/fibonacci/{n}")
def get_fibonacci(n: int):
    """
    BUG 15: Stack overflow on large inputs
    BUG 8: No boundary checking on input
    """
    # BUG 8 & 15: n=50+ causes extreme slowness, n=1000+ stack overflow
    result = calculate_fibonacci(n)
    return {"n": n, "result": result}


# BUG 16: Large number handling
@app.post("/calculate-factorial")
def calculate_factorial(n: int):
    """
    BUG 16: Doesn't handle very large results
    BUG 12: Doesn't validate negative input
    """
    # BUG 12: Negative factorial is undefined but not caught
    if n < 0:
        return {"error": "Negative factorial"}
    
    result = 1
    for i in range(1, n + 1):
        result *= i
    
    # BUG 16: For large n, result exceeds float precision
    # Should use string or bigint, but returns inaccurate float
    return {"n": n, "factorial": result}


# BUG 3: More division by zero cases
@app.get("/analytics/conversion-rate")
def get_conversion_rate():
    """
    BUG 3: Division by zero when no views
    """
    total_views = len(analytics_db["views"])
    total_clicks = len(analytics_db["clicks"])
    
    # BUG 3: Crashes when total_views is 0
    conversion_rate = (total_clicks / total_views) * 100
    
    return {
        "views": total_views,
        "clicks": total_clicks,
        "conversion_rate": conversion_rate
    }


# BUG 11: Index out of bounds
@app.get("/posts/latest")
def get_latest_posts(count: int = Query(5)):
    """
    BUG 11: Doesn't check if enough posts exist
    """
    posts_list = list(posts_db.values())
    
    # BUG 11: If count > len(posts_list), silently returns less
    # If posts_list is empty and we try to access [0], crashes
    
    # Also has off-by-one potential
    return posts_list[-count:]  # BUG 11: Crashes if posts_list is empty


# BUG 20: Type coercion issues
@app.post("/calculate")
def calculate(a: str, b: str, operation: str):
    """
    BUG 20: Mixes strings and numbers without proper validation
    """
    # BUG 20: No type checking - assumes strings can convert to numbers
    # "5" + "3" = "53" (string concat) vs 5 + 3 = 8 (addition)
    
    if operation == "add":
        # BUG 20: String concatenation instead of numeric addition
        result = a + b  # "5" + "3" = "53"
    elif operation == "multiply":
        # BUG 20: Tries to convert but no error handling
        result = int(a) * int(b)  # Crashes if a or b aren't numeric
    elif operation == "divide":
        # BUG 3 & 20: Division by zero and type issues
        result = float(a) / float(b)
    else:
        result = 0
    
    return {"a": a, "b": b, "operation": operation, "result": result}


# BUG 19: Buffer/length issues
@app.post("/create-comment")
def create_comment(post_id: int, content: str):
    """
    BUG 19: No length validation causes various issues
    """
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # BUG 19: Content can be empty string or 10MB of text
    # No min/max length validation
    
    # BUG 19: Assuming fixed buffer size somewhere downstream
    comment = {
        "post_id": post_id,
        "content": content,  # No validation
        "created_at": datetime.now().isoformat()
    }
    
    return comment


# Edge case: Empty strings and whitespace
@app.post("/search")
def search(request: SearchRequest):
    """
    Multiple edge cases:
    - Empty query string
    - Only whitespace
    - Very long query
    - Special characters in query
    """
    query = request.query
    
    # BUG: No validation for empty/whitespace-only query
    # BUG: No sanitization for special regex characters
    
    results = []
    for post in posts_db.values():
        # BUG 5: Case-sensitive search, unicode issues
        # BUG: Empty query matches everything
        if query in post["title"] or query in post["content"]:
            results.append(post)
    
    # BUG 4: Limit not properly applied, off-by-one
    return results[:request.limit + 1]  # Returns limit+1 items


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
