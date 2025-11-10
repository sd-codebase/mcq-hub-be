"""
Service layer for Topics module.
Contains business logic and database operations.
"""

from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.config.database import get_database
from app.core.exceptions import (
    ResourceNotFoundException,
    InvalidInputException,
    InvalidObjectIdException
)
from app.modules.topics.schemas import TopicCreate, TopicUpdate, TopicStatus


class TopicService:
    """Service class for topic operations."""

    def __init__(self):
        self.collection_name = "topics"
        self.chapter_collection = "chapters"

    async def _verify_chapter_exists(self, chapter_id: str) -> None:
        """
        Verify that the chapter exists.

        Args:
            chapter_id: Chapter ID to verify

        Raises:
            InvalidObjectIdException: If chapter_id is not a valid ObjectId
            ResourceNotFoundException: If chapter not found
        """
        if not ObjectId.is_valid(chapter_id):
            raise InvalidObjectIdException(value=chapter_id, resource="Chapter")

        db = get_database()
        chapter = await db[self.chapter_collection].find_one({"_id": ObjectId(chapter_id)})

        if not chapter:
            raise ResourceNotFoundException(resource="Chapter", identifier=chapter_id)

    async def create(self, topic_data: TopicCreate) -> Dict[str, Any]:
        """
        Create a new topic.

        Args:
            topic_data: Topic creation data

        Returns:
            Created topic with ID

        Raises:
            ResourceNotFoundException: If chapter not found
        """
        # Verify chapter exists
        await self._verify_chapter_exists(topic_data.chapterId)

        db = get_database()
        topic_dict = topic_data.model_dump()

        result = await db[self.collection_name].insert_one(topic_dict)

        created_topic = await db[self.collection_name].find_one({"_id": result.inserted_id})
        created_topic["id"] = str(created_topic.pop("_id"))

        return created_topic

    async def get_by_id(self, topic_id: str) -> Dict[str, Any]:
        """
        Get a topic by ID.

        Args:
            topic_id: Topic ID

        Returns:
            Topic data

        Raises:
            InvalidObjectIdException: If topic_id is not a valid ObjectId
            ResourceNotFoundException: If topic not found
        """
        if not ObjectId.is_valid(topic_id):
            raise InvalidObjectIdException(value=topic_id, resource="Topic")

        db = get_database()
        topic = await db[self.collection_name].find_one({"_id": ObjectId(topic_id)})

        if not topic:
            raise ResourceNotFoundException(resource="Topic", identifier=topic_id)

        topic["id"] = str(topic.pop("_id"))
        return topic

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[TopicStatus] = None,
        chapter_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all topics with pagination and optional filters.

        Args:
            skip: Number of topics to skip
            limit: Maximum number of topics to return
            status: Optional status filter
            chapter_id: Optional chapter ID filter

        Returns:
            List of topics sorted by order

        Raises:
            InvalidInputException: If pagination parameters are invalid
            InvalidObjectIdException: If chapter_id is not a valid ObjectId
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

        # Validate chapter_id if provided
        if chapter_id:
            if not ObjectId.is_valid(chapter_id):
                raise InvalidObjectIdException(value=chapter_id, resource="Chapter")

        db = get_database()
        query = {}

        if status:
            query["status"] = status.value

        if chapter_id:
            query["chapterId"] = chapter_id

        topics = await db[self.collection_name].find(query).sort("order", 1).skip(skip).limit(limit).to_list(length=limit)

        for topic in topics:
            topic["id"] = str(topic.pop("_id"))

        return topics

    async def update(self, topic_id: str, topic_data: TopicUpdate) -> Dict[str, Any]:
        """
        Update an existing topic.

        Args:
            topic_id: Topic ID
            topic_data: Update data

        Returns:
            Updated topic

        Raises:
            InvalidObjectIdException: If topic_id is not a valid ObjectId
            InvalidInputException: If no fields to update
            ResourceNotFoundException: If topic or chapter not found
        """
        if not ObjectId.is_valid(topic_id):
            raise InvalidObjectIdException(value=topic_id, resource="Topic")

        # Only update provided fields
        update_data = {k: v for k, v in topic_data.model_dump().items() if v is not None}

        if not update_data:
            raise InvalidInputException(
                message="No valid fields provided for update",
                details={}
            )

        # Verify chapter exists if chapterId is being updated
        if "chapterId" in update_data:
            await self._verify_chapter_exists(update_data["chapterId"])

        db = get_database()
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(topic_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ResourceNotFoundException(
                resource="Topic",
                identifier=topic_id,
                field="ID"
            )

        updated_topic = await db[self.collection_name].find_one({"_id": ObjectId(topic_id)})
        updated_topic["id"] = str(updated_topic.pop("_id"))

        return updated_topic

    async def delete(self, topic_id: str) -> None:
        """
        Delete a topic.

        Args:
            topic_id: Topic ID

        Raises:
            InvalidObjectIdException: If topic_id is not a valid ObjectId
            ResourceNotFoundException: If topic not found
        """
        if not ObjectId.is_valid(topic_id):
            raise InvalidObjectIdException(value=topic_id, resource="Topic")

        db = get_database()
        result = await db[self.collection_name].delete_one({"_id": ObjectId(topic_id)})

        if result.deleted_count == 0:
            raise ResourceNotFoundException(
                resource="Topic",
                identifier=topic_id,
                field="ID"
            )
