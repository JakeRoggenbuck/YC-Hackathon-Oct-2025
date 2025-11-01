"""
INTENTIONAL BUGS IN THIS API (Advanced/Subtle Issues):

1. SQL Injection vulnerability in search endpoint (raw SQL concatenation)
2. Race condition in inventory management (no locking mechanism)
3. Memory leak - unbounded cache growth without eviction policy
4. Integer overflow in price calculation for bulk orders
5. Timezone-naive datetime comparisons causing incorrect results
6. N+1 query problem in relationship loading
7. Silent data truncation in database fields
8. Improper null handling causing empty list returns to be indistinguishable from errors
9. Floating point precision errors in financial calculations
10. CORS vulnerability allowing credential exposure
11. Pagination offset injection allowing negative offsets
12. Resource exhaustion - no rate limiting on expensive operations
13. Improper error serialization leaking internal system details
14. Stale cache serving outdated data after updates
15. Transaction isolation issues causing phantom reads

These are production-level bugs that slip through code review and only manifest under specific conditions.
"""

from fastapi import FastAPI, HTTPException, Query, Header, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import time
import sqlite3
import json

app = FastAPI(title="Advanced Buggy E-Commerce API", version="2.0.0")

# In-memory "database" simulation
products_db = {}
orders_db = {}
inventory_db = {}
users_db = {}
product_id_counter = 1
order_id_counter = 1

# BUG 3: Unbounded cache - memory leak
cache = {}  # No eviction policy, grows indefinitely

# BUG 14: Stale cache issue
cache_timestamps = {}
CACHE_TTL = 300  # 5 minutes, but we don't check it properly


class Product(BaseModel):
    name: str = Field(..., max_length=100)
    description: str
    price: float  # BUG 9: Using float for money
    stock: int
    category: str


class Order(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    discount_code: Optional[str] = None


class User(BaseModel):
    username: str
    email: str
    password: str  # BUG 13: Password in plain model, could leak in errors
    created_at: Optional[datetime] = None  # BUG 5: Timezone-naive


# Initialize some data
def init_data():
    global product_id_counter, products_db, inventory_db, users_db
    
    products_db[1] = {
        "id": 1,
        "name": "Laptop",
        "description": "High performance laptop",
        "price": 999.99,
        "stock": 50,
        "category": "Electronics"
    }
    products_db[2] = {
        "id": 2,
        "name": "Mouse",
        "description": "Wireless mouse",
        "price": 29.99,
        "stock": 100,
        "category": "Electronics"
    }
    product_id_counter = 3
    
    inventory_db[1] = {"product_id": 1, "reserved": 0, "available": 50}
    inventory_db[2] = {"product_id": 2, "reserved": 0, "available": 100}
    
    users_db[1] = {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123",  # Plain text password
        "created_at": datetime.now()  # BUG 5: No timezone
    }


init_data()


# BUG 1: SQL Injection vulnerability
@app.get("/products/search")
def search_products(query: str = Query(...)):
    """
    Search products by name or description.
    BUG: Uses raw SQL string concatenation - SQL injection vulnerable
    """
    # Simulating SQL injection vulnerability
    sql_query = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
    
    # In reality, this would execute against a real DB
    # Here we simulate the vulnerability
    results = []
    for product in products_db.values():
        # This is vulnerable to injection attacks
        if query in product["name"] or query in product["description"]:
            results.append(product)
    
    # BUG 8: Empty list could mean "no results" or "error occurred"
    # No way to distinguish
    return results


# BUG 2: Race condition in inventory
@app.post("/orders")
async def create_order(order: Order):
    """
    BUG: Race condition - no locking on inventory checks
    Multiple simultaneous requests can oversell inventory
    """
    global order_id_counter
    
    if order.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = products_db[order.product_id]
    inventory = inventory_db[order.product_id]
    
    # BUG 2: No lock here - race condition!
    # Two requests can both see available stock and both succeed
    if inventory["available"] < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Simulate some processing time where race condition can occur
    time.sleep(0.01)
    
    # BUG 2: Stock is decremented without atomic operation
    inventory["available"] -= order.quantity
    inventory["reserved"] += order.quantity
    
    # BUG 4 & 9: Integer overflow and float precision issues
    base_price = product["price"] * order.quantity
    
    # BUG 4: Large quantities can cause integer overflow in calculations
    if order.quantity > 1000000:
        # Calculation wraps around or becomes incorrect
        total = (product["price"] * order.quantity) % (2**31)
    else:
        total = base_price
    
    # Apply discount
    if order.discount_code == "SAVE10":
        # BUG 9: Float arithmetic causes precision errors
        total = total * 0.9  # Should use Decimal for money
    
    order_id = order_id_counter
    orders_db[order_id] = {
        "id": order_id,
        "user_id": order.user_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total": total,
        "created_at": datetime.now(),  # BUG 5: Timezone-naive
        "status": "pending"
    }
    order_id_counter += 1
    
    # BUG 14: Cache product but never invalidate it properly
    cache[f"order_{order_id}"] = orders_db[order_id]
    cache_timestamps[f"order_{order_id}"] = time.time()
    
    return orders_db[order_id]


# BUG 6: N+1 query problem
@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: int):
    """
    BUG: N+1 query problem - fetches each product individually
    """
    user_orders = [o for o in orders_db.values() if o["user_id"] == user_id]
    
    # BUG 6: For each order, we fetch product details separately (N+1)
    enriched_orders = []
    for order in user_orders:
        # Simulating individual queries for each product
        product = products_db.get(order["product_id"])
        enriched_order = {**order, "product": product}
        enriched_orders.append(enriched_order)
    
    return enriched_orders


# BUG 11: Pagination offset injection
@app.get("/products")
def get_products(
    offset: int = Query(0),
    limit: int = Query(10, le=100)
):
    """
    BUG: Negative offset not validated, can cause unexpected behavior
    BUG: No validation on offset being too large
    """
    products_list = list(products_db.values())
    
    # BUG 11: Negative offset causes weird slicing behavior
    # offset=-5 will return last 5 items, which might be unintended
    return products_list[offset:offset + limit]


# BUG 3 & 12: Unbounded cache and no rate limiting
@app.get("/expensive-report")
def generate_report(
    include_all_history: bool = False,
    user_id: Optional[int] = None
):
    """
    BUG 3: Results cached indefinitely - memory leak
    BUG 12: Expensive operation with no rate limiting
    """
    cache_key = f"report_{user_id}_{include_all_history}"
    
    # BUG 3: Cache never expires or gets cleaned up
    if cache_key in cache:
        # BUG 14: Doesn't check if cache is stale
        return cache[cache_key]
    
    # BUG 12: Expensive computation with no rate limiting
    # Attacker can DOS by repeatedly calling this
    time.sleep(2)  # Simulating expensive operation
    
    report = {
        "total_orders": len(orders_db),
        "total_revenue": sum(o.get("total", 0) for o in orders_db.values()),
        "timestamp": datetime.now().isoformat()  # BUG 5: Timezone-naive
    }
    
    # BUG 3: Cache grows without bounds
    cache[cache_key] = report
    
    return report


# BUG 5: Timezone issues
@app.get("/orders/recent")
def get_recent_orders(hours: int = Query(24)):
    """
    BUG: Timezone-naive datetime comparison
    """
    cutoff = datetime.now() - timedelta(hours=hours)  # BUG 5: No timezone
    
    recent = []
    for order in orders_db.values():
        # BUG 5: Comparing timezone-naive datetimes
        # Fails across timezones or DST boundaries
        if order["created_at"] > cutoff:
            recent.append(order)
    
    return recent


# BUG 13: Error information leakage
@app.post("/users")
def create_user(user: User):
    """
    BUG: Error messages leak internal system details
    """
    try:
        # Check for duplicate username
        for existing_user in users_db.values():
            if existing_user["username"] == user.username:
                # BUG 13: Leaking internal database structure and user data
                raise Exception(f"Database integrity error: Duplicate key violation on users.username = '{user.username}'. "
                              f"Existing record: {existing_user}. Database host: db-prod-01.internal.company.com")
        
        user_id = len(users_db) + 1
        users_db[user_id] = {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "password": user.password,  # BUG: Storing plain text password
            "created_at": datetime.now()
        }
        
        return {"id": user_id, "username": user.username}
    
    except Exception as e:
        # BUG 13: Returning raw exception with internal details
        raise HTTPException(status_code=400, detail=str(e))


# BUG 7: Data truncation
@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product):
    """
    BUG: Silent data truncation on long descriptions
    """
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # BUG 7: Silently truncates description to 255 chars without warning
    # Real databases do this, but it should at least warn the user
    truncated_description = product.description[:255]
    
    products_db[product_id].update({
        "name": product.name,
        "description": truncated_description,  # BUG 7: Silent truncation
        "price": product.price,
        "stock": product.stock,
        "category": product.category
    })
    
    # BUG 14: Update DB but forget to invalidate cache
    # Old cached values will still be served
    
    return products_db[product_id]


# BUG 15: Transaction isolation issues
@app.post("/transfer-stock")
def transfer_stock(from_product_id: int, to_product_id: int, quantity: int):
    """
    BUG: No transaction isolation - phantom reads possible
    """
    if from_product_id not in inventory_db or to_product_id not in inventory_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    from_inventory = inventory_db[from_product_id]
    to_inventory = inventory_db[to_product_id]
    
    # BUG 15: No transaction - another request can modify data between reads
    if from_inventory["available"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Simulate some processing time where data can change
    time.sleep(0.01)
    
    # BUG 15: These operations aren't atomic
    # Another request could have modified the inventories
    from_inventory["available"] -= quantity
    to_inventory["available"] += quantity
    
    return {
        "from_product": from_product_id,
        "to_product": to_product_id,
        "quantity": quantity,
        "status": "completed"
    }


# BUG 8: Empty response ambiguity
@app.get("/products/category/{category}")
def get_products_by_category(category: str):
    """
    BUG: Empty list could mean "no products" OR "category doesn't exist"
    No way to distinguish between the two
    """
    results = [p for p in products_db.values() if p["category"] == category]
    
    # BUG 8: Returns [] for both "no products in valid category" 
    # and "invalid category" - ambiguous
    return results


@app.get("/health")
def health_check():
    """
    Health check that doesn't actually check anything critical
    """
    # BUG: Doesn't check database connectivity, cache size, etc.
    return {"status": "healthy", "cache_size": len(cache)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
