"""
Service layer for Chapters module.
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
from app.modules.chapters.schemas import ChapterCreate, ChapterUpdate, ChapterStatus


class ChapterService:
    """Service class for chapter operations."""

    def __init__(self):
        self.collection_name = "chapters"
        self.subject_collection = "subjects"

    async def _verify_subject_exists(self, subject_id: str) -> None:
        """
        Verify that the subject exists.

        Args:
            subject_id: Subject ID to verify

        Raises:
            InvalidObjectIdException: If subject_id is not a valid ObjectId
            ResourceNotFoundException: If subject not found
        """
        if not ObjectId.is_valid(subject_id):
            raise InvalidObjectIdException(value=subject_id, resource="Subject")

        db = get_database()
        subject = await db[self.subject_collection].find_one({"_id": ObjectId(subject_id)})

        if not subject:
            raise ResourceNotFoundException(resource="Subject", identifier=subject_id)

    async def create(self, chapter_data: ChapterCreate) -> Dict[str, Any]:
        """
        Create a new chapter.

        Args:
            chapter_data: Chapter creation data

        Returns:
            Created chapter with ID

        Raises:
            ResourceNotFoundException: If subject not found
        """
        # Verify subject exists
        await self._verify_subject_exists(chapter_data.subjectId)

        db = get_database()
        chapter_dict = chapter_data.model_dump()

        result = await db[self.collection_name].insert_one(chapter_dict)

        created_chapter = await db[self.collection_name].find_one({"_id": result.inserted_id})
        created_chapter["id"] = str(created_chapter.pop("_id"))

        return created_chapter

    async def get_by_id(self, chapter_id: str) -> Dict[str, Any]:
        """
        Get a chapter by ID.

        Args:
            chapter_id: Chapter ID

        Returns:
            Chapter data

        Raises:
            InvalidObjectIdException: If chapter_id is not a valid ObjectId
            ResourceNotFoundException: If chapter not found
        """
        if not ObjectId.is_valid(chapter_id):
            raise InvalidObjectIdException(value=chapter_id, resource="Chapter")

        db = get_database()
        chapter = await db[self.collection_name].find_one({"_id": ObjectId(chapter_id)})

        if not chapter:
            raise ResourceNotFoundException(resource="Chapter", identifier=chapter_id)

        chapter["id"] = str(chapter.pop("_id"))
        return chapter

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[ChapterStatus] = None,
        subject_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all chapters with pagination and optional filters.

        Args:
            skip: Number of chapters to skip
            limit: Maximum number of chapters to return
            status: Optional status filter
            subject_id: Optional subject ID filter

        Returns:
            List of chapters sorted by order

        Raises:
            InvalidInputException: If pagination parameters are invalid
            InvalidObjectIdException: If subject_id is not a valid ObjectId
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

        # Validate subject_id if provided
        if subject_id:
            if not ObjectId.is_valid(subject_id):
                raise InvalidObjectIdException(value=subject_id, resource="Subject")

        db = get_database()
        query = {}

        if status:
            query["status"] = status.value

        if subject_id:
            query["subjectId"] = subject_id

        chapters = await db[self.collection_name].find(query).sort("order", 1).skip(skip).limit(limit).to_list(length=limit)

        for chapter in chapters:
            chapter["id"] = str(chapter.pop("_id"))

        return chapters

    async def update(self, chapter_id: str, chapter_data: ChapterUpdate) -> Dict[str, Any]:
        """
        Update an existing chapter.

        Args:
            chapter_id: Chapter ID
            chapter_data: Update data

        Returns:
            Updated chapter

        Raises:
            InvalidObjectIdException: If chapter_id is not a valid ObjectId
            InvalidInputException: If no fields to update
            ResourceNotFoundException: If chapter or subject not found
        """
        if not ObjectId.is_valid(chapter_id):
            raise InvalidObjectIdException(value=chapter_id, resource="Chapter")

        # Only update provided fields
        update_data = {k: v for k, v in chapter_data.model_dump().items() if v is not None}

        if not update_data:
            raise InvalidInputException(
                message="No valid fields provided for update",
                details={}
            )

        # Verify subject exists if subjectId is being updated
        if "subjectId" in update_data:
            await self._verify_subject_exists(update_data["subjectId"])

        db = get_database()
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(chapter_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ResourceNotFoundException(
                resource="Chapter",
                identifier=chapter_id,
                field="ID"
            )

        updated_chapter = await db[self.collection_name].find_one({"_id": ObjectId(chapter_id)})
        updated_chapter["id"] = str(updated_chapter.pop("_id"))

        return updated_chapter

    async def delete(self, chapter_id: str) -> None:
        """
        Delete a chapter.

        Args:
            chapter_id: Chapter ID

        Raises:
            InvalidObjectIdException: If chapter_id is not a valid ObjectId
            ResourceNotFoundException: If chapter not found
        """
        if not ObjectId.is_valid(chapter_id):
            raise InvalidObjectIdException(value=chapter_id, resource="Chapter")

        db = get_database()
        result = await db[self.collection_name].delete_one({"_id": ObjectId(chapter_id)})

        if result.deleted_count == 0:
            raise ResourceNotFoundException(
                resource="Chapter",
                identifier=chapter_id,
                field="ID"
            )
