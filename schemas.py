"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in USD")
    category: str = Field("leggings", description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    colors: List[str] = Field(default_factory=list, description="Available colors")
    sizes: List[str] = Field(default_factory=list, description="Available sizes")
    featured: bool = Field(False, description="Show on homepage")
    warmth_rating: Optional[int] = Field(5, ge=1, le=5, description="Warmth rating 1-5")
    fabric: Optional[str] = Field(None, description="Fabric composition")
    sku: Optional[str] = Field(None, description="Stock keeping unit")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Referenced product id")
    title: str = Field(..., description="Product title snapshot")
    price: float = Field(..., ge=0, description="Price at purchase time")
    color: Optional[str] = Field(None, description="Selected color")
    size: Optional[str] = Field(None, description="Selected size")
    quantity: int = Field(1, ge=1, description="Quantity")

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    items: List[OrderItem]
    customer_name: str
    customer_email: str
    shipping_address: str
    subtotal: float = Field(..., ge=0)
    shipping_cost: float = Field(0, ge=0)
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="Order status")
    notes: Optional[str] = None

# The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
