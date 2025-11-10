"""
Service layer for Questions module.
Contains business logic, database operations, and bulk operations.
"""

from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo import UpdateOne

from app.config.database import get_database
from app.core.exceptions import (
    ResourceNotFoundException,
    InvalidInputException,
    InvalidObjectIdException
)
from app.modules.questions.schemas import (
    QuestionCreate,
    QuestionUpdate,
    QuestionStatus,
    QuestionType,
    QuestionUpdateItem
)


class QuestionService:
    """Service class for question operations."""

    def __init__(self):
        self.collection_name = "questions"
        self.topic_collection = "topics"

    async def _verify_topic_exists(self, topic_id: str) -> None:
        """
        Verify that the topic exists.

        Args:
            topic_id: Topic ID to verify

        Raises:
            InvalidObjectIdException: If topic_id is not a valid ObjectId
            ResourceNotFoundException: If topic not found
        """
        if not ObjectId.is_valid(topic_id):
            raise InvalidObjectIdException(value=topic_id, resource="Topic")

        db = get_database()
        topic = await db[self.topic_collection].find_one({"_id": ObjectId(topic_id)})

        if not topic:
            raise ResourceNotFoundException(resource="Topic", identifier=topic_id)

    def _convert_to_response(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Convert database document to response format."""
        question["id"] = str(question.pop("_id"))
        return question

    async def create(self, question_data: QuestionCreate) -> Dict[str, Any]:
        """
        Create a new question.

        Args:
            question_data: Question creation data

        Returns:
            Created question with ID

        Raises:
            ResourceNotFoundException: If topic not found
        """
        # Verify topic exists
        await self._verify_topic_exists(question_data.topicId)

        db = get_database()
        question_dict = question_data.model_dump()

        result = await db[self.collection_name].insert_one(question_dict)

        created_question = await db[self.collection_name].find_one({"_id": result.inserted_id})
        return self._convert_to_response(created_question)

    async def bulk_create(self, questions_data: List[QuestionCreate]) -> Dict[str, Any]:
        """
        Bulk create multiple questions.

        Args:
            questions_data: List of questions to create

        Returns:
            Dictionary with created count and questions list

        Raises:
            ResourceNotFoundException: If any topic not found
            InvalidInputException: If bulk operation fails
        """
        if not questions_data:
            raise InvalidInputException(
                message="No questions provided for bulk creation",
                details={}
            )

        # Verify all topics exist first
        unique_topic_ids = set(q.topicId for q in questions_data)
        for topic_id in unique_topic_ids:
            await self._verify_topic_exists(topic_id)

        db = get_database()
        questions_dicts = [q.model_dump() for q in questions_data]

        try:
            result = await db[self.collection_name].insert_many(questions_dicts, ordered=True)

            # Fetch all created questions
            created_questions = await db[self.collection_name].find(
                {"_id": {"$in": result.inserted_ids}}
            ).to_list(length=len(result.inserted_ids))

            # Sort by insertion order
            id_to_question = {q["_id"]: q for q in created_questions}
            ordered_questions = [id_to_question[_id] for _id in result.inserted_ids]

            return {
                "created": len(ordered_questions),
                "questions": [self._convert_to_response(q) for q in ordered_questions]
            }

        except Exception as e:
            raise InvalidInputException(
                message=f"Bulk create operation failed: {str(e)}",
                details={}
            )

    async def get_by_id(self, question_id: str) -> Dict[str, Any]:
        """
        Get a question by ID.

        Args:
            question_id: Question ID

        Returns:
            Question data

        Raises:
            InvalidObjectIdException: If question_id is not a valid ObjectId
            ResourceNotFoundException: If question not found
        """
        if not ObjectId.is_valid(question_id):
            raise InvalidObjectIdException(value=question_id, resource="Question")

        db = get_database()
        question = await db[self.collection_name].find_one({"_id": ObjectId(question_id)})

        if not question:
            raise ResourceNotFoundException(resource="Question", identifier=question_id)

        return self._convert_to_response(question)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[QuestionStatus] = None,
        topic_id: Optional[str] = None,
        question_type: Optional[QuestionType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all questions with pagination and optional filters.

        Args:
            skip: Number of questions to skip
            limit: Maximum number of questions to return
            status: Optional status filter
            topic_id: Optional topic ID filter
            question_type: Optional question type filter

        Returns:
            List of questions sorted by order

        Raises:
            InvalidInputException: If pagination parameters are invalid
            InvalidObjectIdException: If topic_id is not a valid ObjectId
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

        # Validate topic_id if provided
        if topic_id:
            if not ObjectId.is_valid(topic_id):
                raise InvalidObjectIdException(value=topic_id, resource="Topic")

        db = get_database()
        query = {}

        if status:
            query["status"] = status.value

        if topic_id:
            query["topicId"] = topic_id

        if question_type:
            query["type"] = question_type.value

        questions = await db[self.collection_name].find(query).sort("order", 1).skip(skip).limit(limit).to_list(length=limit)

        return [self._convert_to_response(q) for q in questions]

    async def update(self, question_id: str, question_data: QuestionUpdate) -> Dict[str, Any]:
        """
        Update an existing question.

        Args:
            question_id: Question ID
            question_data: Update data

        Returns:
            Updated question

        Raises:
            InvalidObjectIdException: If question_id is not a valid ObjectId
            InvalidInputException: If no fields to update
            ResourceNotFoundException: If question or topic not found
        """
        if not ObjectId.is_valid(question_id):
            raise InvalidObjectIdException(value=question_id, resource="Question")

        # Only update provided fields
        update_data = {k: v for k, v in question_data.model_dump().items() if v is not None}

        if not update_data:
            raise InvalidInputException(
                message="No valid fields provided for update",
                details={}
            )

        # Verify topic exists if topicId is being updated
        if "topicId" in update_data:
            await self._verify_topic_exists(update_data["topicId"])

        db = get_database()
        result = await db[self.collection_name].update_one(
            {"_id": ObjectId(question_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ResourceNotFoundException(
                resource="Question",
                identifier=question_id,
                field="ID"
            )

        updated_question = await db[self.collection_name].find_one({"_id": ObjectId(question_id)})
        return self._convert_to_response(updated_question)

    async def bulk_update(self, updates: List[QuestionUpdateItem]) -> Dict[str, Any]:
        """
        Bulk update multiple questions.

        Args:
            updates: List of question IDs and update data

        Returns:
            Dictionary with updated count and questions list

        Raises:
            InvalidObjectIdException: If any question_id is not valid
            InvalidInputException: If bulk operation fails
            ResourceNotFoundException: If any question not found
        """
        if not updates:
            raise InvalidInputException(
                message="No questions provided for bulk update",
                details={}
            )

        # Validate all IDs and prepare bulk operations
        bulk_operations = []
        question_ids = []

        for idx, update_item in enumerate(updates):
            question_id = update_item.id

            if not ObjectId.is_valid(question_id):
                raise InvalidObjectIdException(
                    value=question_id,
                    resource=f"Question at index {idx}"
                )

            question_ids.append(ObjectId(question_id))

            update_data = {k: v for k, v in update_item.data.model_dump().items() if v is not None}

            if not update_data:
                raise InvalidInputException(
                    message=f"No valid fields provided for update at index {idx}",
                    details={"index": idx, "id": question_id}
                )

            # Verify topic exists if topicId is being updated
            if "topicId" in update_data:
                await self._verify_topic_exists(update_data["topicId"])

            bulk_operations.append(
                UpdateOne({"_id": ObjectId(question_id)}, {"$set": update_data})
            )

        # Verify all questions exist
        db = get_database()
        existing_count = await db[self.collection_name].count_documents(
            {"_id": {"$in": question_ids}}
        )

        if existing_count != len(question_ids):
            raise InvalidInputException(
                message="One or more questions not found",
                details={"provided": len(question_ids), "found": existing_count}
            )

        try:
            # Execute bulk update
            result = await db[self.collection_name].bulk_write(bulk_operations, ordered=True)

            # Fetch all updated questions
            updated_questions = await db[self.collection_name].find(
                {"_id": {"$in": question_ids}}
            ).to_list(length=len(question_ids))

            # Sort by original order
            id_to_question = {q["_id"]: q for q in updated_questions}
            ordered_questions = [id_to_question[_id] for _id in question_ids]

            return {
                "updated": result.modified_count,
                "questions": [self._convert_to_response(q) for q in ordered_questions]
            }

        except Exception as e:
            raise InvalidInputException(
                message=f"Bulk update operation failed: {str(e)}",
                details={}
            )

    async def delete(self, question_id: str) -> None:
        """
        Delete a question.

        Args:
            question_id: Question ID

        Raises:
            InvalidObjectIdException: If question_id is not a valid ObjectId
            ResourceNotFoundException: If question not found
        """
        if not ObjectId.is_valid(question_id):
            raise InvalidObjectIdException(value=question_id, resource="Question")

        db = get_database()
        result = await db[self.collection_name].delete_one({"_id": ObjectId(question_id)})

        if result.deleted_count == 0:
            raise ResourceNotFoundException(
                resource="Question",
                identifier=question_id,
                field="ID"
            )
