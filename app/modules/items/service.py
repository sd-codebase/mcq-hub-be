"""
Service layer for Items module.
Contains business logic and database operations.
"""

from typing import List, Dict, Any
from bson import ObjectId

from app.config.database import get_database
from app.core.exceptions import (
    ResourceNotFoundException,
    InvalidInputException,
    InvalidObjectIdException
)
from app.modules.items.schemas import ItemCreate, ItemUpdate


class ItemService:
    """Service class for item operations."""

    def __init__(self):
        self.collection_name = "items"

    async def create(self, item_data: ItemCreate) -> Dict[str, Any]:
        """
        Create a new item.

        Args:
            item_data: Item creation data

        Returns:
            Created item with ID

        Raises:
            DatabaseConnectionException: If database operation fails
        """
        db = get_database()
        item_dict = item_data.model_dump()

        result = await db[self.collection_name].insert_one(item_dict)

        created_item = await db[self.collection_name].find_one({"_id": result.inserted_id})
        created_item["id"] = str(created_item.pop("_id"))

        return created_item

    async def get_by_id(self, item_id: str) -> Dict[str, Any]:
        """
        Get an item by ID.

        Args:
            item_id: Item ID

        Returns:
            Item data

        Raises:
            InvalidObjectIdException: If item_id is not a valid ObjectId
            ResourceNotFoundException: If item not found
        """
        if not ObjectId.is_valid(item_id):
            raise InvalidObjectIdException(value=item_id, resource="Item")

        db = get_database()
        item = await db[self.collection_name].find_one({"_id": ObjectId(item_id)})

        if not item:
            raise ResourceNotFoundException(resource="Item", identifier=item_id)

        item["id"] = str(item.pop("_id"))
        return item

    async def get_all(self, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all items with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of items

        Raises:
            InvalidInputException: If pagination parameters are invalid
        """
        if skip < 0:
            raise InvalidInputException(
                message="Skip parameter must be non-negative",
                details={"skip": skip}
            )

        if limit < 1 or limit > 100:
            raise InvalidInputException(
                message="Limit must be between 1 and 100",
                details={"limit": limit}
            )

        db = get_database()
        items = await db[self.collection_name].find().skip(skip).limit(limit).to_list(length=limit)

        for item in items:
            item["id"] = str(item.pop("_id"))

        return items

    async def update(self, item_id: str, item_data: ItemUpdate) -> Dict[str, Any]:
        """
        Update an existing item.

        Args:
            item_id: Item ID
            item_data: Update data

        Returns:
            Updated item

        Raises:
            InvalidObjectIdException: If item_id is not a valid ObjectId
            InvalidInputException: If no fields to update
            ResourceNotFoundException: If item not found
        """
        if not ObjectId.is_valid(item_id):
            raise InvalidObjectIdException(value=item_id, resource="Item")

        # Only update provided fields
        update_data = {k: v for k, v in item_data.model_dump().items() if v is not None}

        if not update_data:
            raise InvalidInputException(
                message="No valid fields provided for update",
                details={}
            )

        db = get_database()
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ResourceNotFoundException(
                resource="Item",
                identifier=item_id,
                field="ID"
            )

        updated_item = await db[self.collection_name].find_one({"_id": ObjectId(item_id)})
        updated_item["id"] = str(updated_item.pop("_id"))

        return updated_item

    async def delete(self, item_id: str) -> None:
        """
        Delete an item.

        Args:
            item_id: Item ID

        Raises:
            InvalidObjectIdException: If item_id is not a valid ObjectId
            ResourceNotFoundException: If item not found
        """
        if not ObjectId.is_valid(item_id):
            raise InvalidObjectIdException(value=item_id, resource="Item")

        db = get_database()
        result = await db[self.collection_name].delete_one({"_id": ObjectId(item_id)})

        if result.deleted_count == 0:
            raise ResourceNotFoundException(
                resource="Item",
                identifier=item_id,
                field="ID"
            )
