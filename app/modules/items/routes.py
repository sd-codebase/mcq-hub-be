"""
API routes for Items module.
"""

from typing import List
from fastapi import APIRouter, status

from app.modules.items.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.modules.items.service import ItemService

# Create router
router = APIRouter()

# Initialize service
item_service = ItemService()


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """
    Create a new item.

    Args:
        item: Item creation data

    Returns:
        Created item with ID
    """
    return await item_service.create(item)


@router.get("/", response_model=List[ItemResponse])
async def get_all_items(skip: int = 0, limit: int = 10):
    """
    Get all items with pagination.

    Args:
        skip: Number of items to skip (default: 0)
        limit: Maximum number of items to return (default: 10, max: 100)

    Returns:
        List of items
    """
    return await item_service.get_all(skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """
    Get a specific item by ID.

    Args:
        item_id: Item ID

    Returns:
        Item data
    """
    return await item_service.get_by_id(item_id)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item_update: ItemUpdate):
    """
    Update an existing item.

    Args:
        item_id: Item ID
        item_update: Fields to update

    Returns:
        Updated item data
    """
    return await item_service.update(item_id, item_update)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    """
    Delete an item.

    Args:
        item_id: Item ID

    Returns:
        No content
    """
    await item_service.delete(item_id)
