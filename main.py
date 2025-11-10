from fastapi import FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DB_NAME")

# Database client
mongodb_client: Optional[AsyncIOMotorClient] = None


# Custom ObjectId type for Pydantic
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _handler):
        return {"type": "string"}


# Pydantic Models
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    quantity: int = Field(default=0, ge=0)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)


class ItemResponse(ItemBase):
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    global mongodb_client
    mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    try:
        await mongodb_client.admin.command('ping')
        print(f"✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
    
    yield
    
    # Shutdown: Close MongoDB connection
    if mongodb_client:
        mongodb_client.close()
        print("🔌 Disconnected from MongoDB")


# Create FastAPI app
app = FastAPI(
    title="FastAPI MongoDB Tutorial",
    description="A simple REST API with FastAPI and MongoDB",
    version="1.0.0",
    lifespan=lifespan
)


# Helper function
def get_database():
    return mongodb_client[DB_NAME]


# Routes
@app.get("/")
async def root():
    """Root endpoint - Welcome message"""
    return {
        "message": "Welcome to FastAPI with MongoDB!",
        "docs": "/docs"
    }


@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """Create a new item"""
    db = get_database()
    item_dict = item.model_dump()
    result = await db.items.insert_one(item_dict)
    
    created_item = await db.items.find_one({"_id": result.inserted_id})
    created_item["_id"] = str(created_item["_id"])
    return created_item


@app.get("/items/", response_model=List[ItemResponse])
async def get_all_items(skip: int = 0, limit: int = 10):
    """Get all items with pagination"""
    db = get_database()
    items = await db.items.find().skip(skip).limit(limit).to_list(length=limit)
    
    for item in items:
        item["_id"] = str(item["_id"])
    return items


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Get a specific item by ID"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID format"
        )
    
    db = get_database()
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    item["_id"] = str(item["_id"])
    return item


@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item_update: ItemUpdate):
    """Update an existing item"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID format"
        )
    
    db = get_database()
    
    # Only update provided fields
    update_data = {k: v for k, v in item_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    result = await db.items.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    updated_item = await db.items.find_one({"_id": ObjectId(item_id)})
    updated_item["_id"] = str(updated_item["_id"])
    return updated_item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    """Delete an item"""
    if not ObjectId.is_valid(item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID format"
        )
    
    db = get_database()
    result = await db.items.delete_one({"_id": ObjectId(item_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )


@app.get("/health")
async def health_check():
    """Check if API and database are working"""
    try:
        await mongodb_client.admin.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }