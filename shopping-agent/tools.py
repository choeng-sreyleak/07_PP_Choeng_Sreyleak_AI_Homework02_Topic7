"""In-memory shopping catalog and business logic.

Responsibilities:
- store product information and stock levels
- implement search, stock lookup, purchase, and delete operations
- expose the tool functions used by the agent and harness
"""

from typing import Dict, List


_PRODUCTS: List[Dict] = [
    {"id": 1, "name": "Aegis 14 Laptop",       "category": "laptop",     "price": 899.00, "stock": 0},
    {"id": 2, "name": "Vertex Pro 15 Laptop",  "category": "laptop",     "price": 1299.00, "stock": 5},
    {"id": 3, "name": "Nimbus Air Laptop",     "category": "laptop",     "price": 749.00, "stock": 12},
    {"id": 4, "name": "Wireless Mouse M1",     "category": "accessory",  "price": 19.99,  "stock": 40},
    {"id": 5, "name": "USB-C Hub 7-in-1",      "category": "accessory",  "price": 34.50,  "stock": 8},
]


def _find_product(product_id: int):
    return next((p for p in _PRODUCTS if p["id"] == product_id), None)


def search_product(query: str) -> Dict:
    """Search the catalog by keyword, or return all in-stock items for stock queries."""
    q = query.lower().strip()
    stock_terms = ("stock", "available", "availability", "in stock", "instock")
    all_terms = ("all", "catalog", "products", "items")

    if q in all_terms or q == "":
        matches = list(_PRODUCTS)
    elif any(term in q for term in stock_terms):
        matches = [p for p in _PRODUCTS if p["stock"] > 0]
    else:
        matches = [p for p in _PRODUCTS if q in p["name"].lower() or q in p["category"].lower()]

    return {
        "ok": True,
        "count": len(matches),
        "results": [{"id": p["id"], "name": p["name"], "price": p["price"]} for p in matches],
    }


def check_stock(product_id: int) -> Dict:
    """Look up current stock for a product id."""
    product = _find_product(product_id)
    if product is None:
        return {"ok": False, "error": "PRODUCT_NOT_FOUND", "message": f"No product with id {product_id}."}
    return {"ok": True, "product_id": product_id, "name": product["name"], "stock": product["stock"]}


def get_product(product_id: int) -> Dict:
    """Get full product details for display and confirmation."""
    product = _find_product(product_id)
    if product is None:
        return {"ok": False, "error": "PRODUCT_NOT_FOUND", "message": f"No product with id {product_id}."}
    return {
        "ok": True,
        "product": {
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "price": product["price"],
            "stock": product["stock"],
        },
    }


def buy_product(product_id: int, quantity: int) -> Dict:
    """Attempt to purchase `quantity` units of a product, decrementing stock."""
    product = _find_product(product_id)
    if product is None:
        return {"ok": False, "error": "PRODUCT_NOT_FOUND", "message": f"No product with id {product_id}."}
    if product["stock"] < quantity:
        return {
            "ok": False,
            "error": "OUT_OF_STOCK",
            "message": f"Only {product['stock']} unit(s) of '{product['name']}' available.",
        }
    product["stock"] -= quantity
    total = round(product["price"] * quantity, 2)
    return {
        "ok": True,
        "product_id": product_id,
        "name": product["name"],
        "quantity": quantity,
        "total_price": total,
        "remaining_stock": product["stock"],
    }


def delete_product(product_id: int) -> Dict:
    """Remove a product from the catalog entirely. Admin-only (enforced in harness.py)."""
    product = _find_product(product_id)
    if product is None:
        return {"ok": False, "error": "PRODUCT_NOT_FOUND", "message": f"No product with id {product_id}."}
    if product["stock"] > 0:
        return {
            "ok": False,
            "error": "DELETE_FORBIDDEN_IN_STOCK",
            "message": f"Cannot delete '{product['name']}' because it has {product['stock']} unit(s) in stock.",
        }
    _PRODUCTS.remove(product)
    return {"ok": True, "message": f"Product '{product['name']}' (id={product_id}) deleted."}


TOOL_FUNCTIONS = {
    "search_product": search_product,
    "check_stock": check_stock,
    "get_product": get_product,
    "buy_product": buy_product,
    "delete_product": delete_product,
}
