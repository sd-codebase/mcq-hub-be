"""
Service layer for Subjects module.
Contains business logic and database operations.
"""

from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.config.database import get_database
from app.core.exceptions import (
    ResourceNotFoundException,
    InvalidInputException,
    InvalidObjectIdException,
    DuplicateResourceException
)
from app.modules.subjects.schemas import (
    SubjectCreate,
    SubjectUpdate,
    SubjectStatus,
    HierarchyCreate,
    generate_shortname
)


class SubjectService:
    """Service class for subject operations."""

    def __init__(self):
        self.collection_name = "subjects"

    async def _check_duplicate_name(self, name: str, exclude_id: Optional[str] = None) -> None:
        """
        Check if a subject with the given name already exists.

        Args:
            name: Subject name to check
            exclude_id: Optional ID to exclude from check (for updates)

        Raises:
            DuplicateResourceException: If subject with name exists
        """
        db = get_database()
        query = {"name": name}

        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}

        existing = await db[self.collection_name].find_one(query)
        if existing:
            raise DuplicateResourceException(
                resource="Subject",
                field="name",
                value=name
            )

    async def _check_duplicate_short_name(self, short_name: str, exclude_id: Optional[str] = None) -> None:
        """
        Check if a subject with the given shortName already exists.

        Args:
            short_name: Subject shortName to check
            exclude_id: Optional ID to exclude from check (for updates)

        Raises:
            DuplicateResourceException: If subject with shortName exists
        """
        db = get_database()
        query = {"shortName": short_name}

        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}

        existing = await db[self.collection_name].find_one(query)
        if existing:
            raise DuplicateResourceException(
                resource="Subject",
                field="shortName",
                value=short_name
            )

    async def create(self, subject_data: SubjectCreate) -> Dict[str, Any]:
        """
        Create a new subject.

        Args:
            subject_data: Subject creation data

        Returns:
            Created subject with ID

        Raises:
            DuplicateResourceException: If subject with name or shortName exists
        """
        # Check for duplicates
        await self._check_duplicate_name(subject_data.name)
        await self._check_duplicate_short_name(subject_data.shortName)

        db = get_database()
        subject_dict = subject_data.model_dump()

        result = await db[self.collection_name].insert_one(subject_dict)

        created_subject = await db[self.collection_name].find_one({"_id": result.inserted_id})
        created_subject["id"] = str(created_subject.pop("_id"))

        return created_subject

    async def get_by_id(self, subject_id: str) -> Dict[str, Any]:
        """
        Get a subject by ID.

        Args:
            subject_id: Subject ID

        Returns:
            Subject data

        Raises:
            InvalidObjectIdException: If subject_id is not a valid ObjectId
            ResourceNotFoundException: If subject not found
        """
        if not ObjectId.is_valid(subject_id):
            raise InvalidObjectIdException(value=subject_id, resource="Subject")

        db = get_database()
        subject = await db[self.collection_name].find_one({"_id": ObjectId(subject_id)})

        if not subject:
            raise ResourceNotFoundException(resource="Subject", identifier=subject_id)

        subject["id"] = str(subject.pop("_id"))
        return subject

    async def get_by_short_name(self, short_name: str) -> Dict[str, Any]:
        """
        Get a subject by shortName.

        Args:
            short_name: Subject shortName

        Returns:
            Subject data

        Raises:
            ResourceNotFoundException: If subject not found
        """
        db = get_database()
        subject = await db[self.collection_name].find_one({"shortName": short_name})

        if not subject:
            raise ResourceNotFoundException(
                resource="Subject",
                identifier=short_name,
                field="shortName"
            )

        subject["id"] = str(subject.pop("_id"))
        return subject

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[SubjectStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all subjects with pagination and optional status filter.

        Args:
            skip: Number of subjects to skip
            limit: Maximum number of subjects to return
            status: Optional status filter

        Returns:
            List of subjects sorted by order

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
        query = {}

        if status:
            query["status"] = status.value

        subjects = await db[self.collection_name].find(query).sort("order", 1).skip(skip).limit(limit).to_list(length=limit)

        for subject in subjects:
            subject["id"] = str(subject.pop("_id"))

        return subjects

    async def update(self, subject_id: str, subject_data: SubjectUpdate) -> Dict[str, Any]:
        """
        Update an existing subject.

        Args:
            subject_id: Subject ID
            subject_data: Update data

        Returns:
            Updated subject

        Raises:
            InvalidObjectIdException: If subject_id is not a valid ObjectId
            InvalidInputException: If no fields to update
            DuplicateResourceException: If name or shortName conflicts
            ResourceNotFoundException: If subject not found
        """
        if not ObjectId.is_valid(subject_id):
            raise InvalidObjectIdException(value=subject_id, resource="Subject")

        # Only update provided fields
        update_data = {k: v for k, v in subject_data.model_dump().items() if v is not None}

        if not update_data:
            raise InvalidInputException(
                message="No valid fields provided for update",
                details={}
            )

        # Check for duplicate name if name is being updated
        if "name" in update_data:
            await self._check_duplicate_name(update_data["name"], exclude_id=subject_id)

        # Check for duplicate shortName if shortName is being updated
        if "shortName" in update_data:
            await self._check_duplicate_short_name(update_data["shortName"], exclude_id=subject_id)

        db = get_database()
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(subject_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ResourceNotFoundException(
                resource="Subject",
                identifier=subject_id,
                field="ID"
            )

        updated_subject = await db[self.collection_name].find_one({"_id": ObjectId(subject_id)})
        updated_subject["id"] = str(updated_subject.pop("_id"))

        return updated_subject

    async def delete(self, subject_id: str) -> None:
        """
        Delete a subject.

        Args:
            subject_id: Subject ID

        Raises:
            InvalidObjectIdException: If subject_id is not a valid ObjectId
            ResourceNotFoundException: If subject not found
        """
        if not ObjectId.is_valid(subject_id):
            raise InvalidObjectIdException(value=subject_id, resource="Subject")

        db = get_database()
        result = await db[self.collection_name].delete_one({"_id": ObjectId(subject_id)})

        if result.deleted_count == 0:
            raise ResourceNotFoundException(
                resource="Subject",
                identifier=subject_id,
                field="ID"
            )

    async def create_hierarchy(self, hierarchy_data: HierarchyCreate) -> Dict[str, Any]:
        """
        Create a complete subject hierarchy with chapters and topics.

        Args:
            hierarchy_data: Hierarchy creation data

        Returns:
            Complete hierarchy with all created entities

        Raises:
            DuplicateResourceException: If subject name/shortName already exists
            InvalidInputException: If creation fails
        """
        db = get_database()

        # Generate shortName from subject name
        short_name = generate_shortname(hierarchy_data.subject)

        # Check for duplicate subject name and shortName
        await self._check_duplicate_name(hierarchy_data.subject)
        await self._check_duplicate_short_name(short_name)

        # Get next order for subject
        last_subject = await db[self.collection_name].find_one(
            {},
            sort=[("order", -1)]
        )
        subject_order = (last_subject["order"] + 1) if last_subject else 1

        # Create subject with INACTIVE status
        subject_dict = {
            "name": hierarchy_data.subject,
            "shortName": short_name,
            "status": "Inactive",
            "order": subject_order
        }

        subject_result = await db[self.collection_name].insert_one(subject_dict)
        subject_id = str(subject_result.inserted_id)

        # Create chapters and topics
        chapters_response = []

        for chapter_index, chapter_item in enumerate(hierarchy_data.topics):
            # Create chapter
            chapter_dict = {
                "subjectId": subject_id,
                "name": chapter_item.topic,
                "status": "Inactive",
                "order": chapter_index + 1
            }

            chapter_result = await db["chapters"].insert_one(chapter_dict)
            chapter_id = str(chapter_result.inserted_id)

            # Create topics for this chapter
            topics_list = []
            for topic_index, topic_item in enumerate(chapter_item.subtopics):
                topic_dict = {
                    "chapterId": chapter_id,
                    "name": topic_item.name,
                    "status": "Inactive",
                    "order": topic_index + 1
                }

                topic_result = await db["topics"].insert_one(topic_dict)

                topics_list.append({
                    "id": str(topic_result.inserted_id),
                    "chapterId": chapter_id,
                    "name": topic_item.name,
                    "status": "Inactive",
                    "order": topic_index + 1
                })

            chapters_response.append({
                "id": chapter_id,
                "name": chapter_item.topic,
                "subjectId": subject_id,
                "status": "Inactive",
                "order": chapter_index + 1,
                "topics": topics_list
            })

        # Return complete hierarchy
        return {
            "subject": {
                "id": subject_id,
                "name": hierarchy_data.subject,
                "shortName": short_name,
                "status": "Inactive",
                "order": subject_order
            },
            "chapters": chapters_response
        }
