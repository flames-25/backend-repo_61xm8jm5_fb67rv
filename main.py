import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem

app = FastAPI(title="WarmLeggs API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductCreate(Product):
    pass

class ProductResponse(Product):
    id: str

class OrderCreate(Order):
    pass

class OrderResponse(Order):
    id: str

@app.get("/")
def read_root():
    return {"name": "WarmLeggs Backend", "status": "ok"}

@app.get("/schema")
def get_schema_info():
    """Expose schemas for tooling/validation"""
    return {
        "collections": ["product", "order"],
        "notes": "Schemas are defined in schemas.py",
    }

@app.get("/products", response_model=List[ProductResponse])
def list_products(featured: Optional[bool] = None):
    try:
        query = {}
        if featured is not None:
            query["featured"] = featured
        docs = get_documents("product", query)
        items: List[ProductResponse] = []
        for d in docs:
            d["id"] = str(d.pop("_id"))
            items.append(ProductResponse(**d))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products", response_model=str)
def create_product(product: ProductCreate):
    try:
        product_id = create_document("product", product)
        return product_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1
    color: Optional[str] = None
    size: Optional[str] = None

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    customer_name: str
    customer_email: str
    shipping_address: str
    notes: Optional[str] = None

@app.post("/checkout", response_model=str)
def checkout(payload: CheckoutRequest):
    try:
        # Build order items from product snapshots
        order_items: List[OrderItem] = []
        subtotal = 0.0
        for item in payload.items:
            # fetch product
            prod_docs = db["product"].find({"_id": ObjectId(item.product_id)})
            prod = next(iter(prod_docs), None)
            if not prod:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            price = float(prod.get("price", 0))
            subtotal += price * item.quantity
            order_items.append(OrderItem(
                product_id=item.product_id,
                title=prod.get("title"),
                price=price,
                color=item.color,
                size=item.size,
                quantity=item.quantity,
            ))
        shipping_cost = 0 if subtotal >= 100 else 10
        total = subtotal + shipping_cost
        order = Order(
            items=order_items,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            shipping_address=payload.shipping_address,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            total=total,
            status="pending",
            notes=payload.notes,
        )
        order_id = create_document("order", order)
        return order_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
