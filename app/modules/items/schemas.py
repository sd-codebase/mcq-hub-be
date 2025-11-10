"""
Pydantic schemas for Items module.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class ItemBase(BaseModel):
    """Base schema for Item with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the item")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    quantity: int = Field(default=0, ge=0, description="Quantity must be non-negative")


class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an existing item. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)


class ItemResponse(ItemBase):
    """Schema for item responses with ID."""
    id: str = Field(description="Unique identifier")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
