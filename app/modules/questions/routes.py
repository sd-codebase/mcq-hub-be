"""
API routes for Questions module.
Includes standard CRUD and bulk operations.
"""

from typing import List, Optional
from fastapi import APIRouter, status, Query

from app.modules.questions.schemas import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionStatus,
    QuestionType,
    BulkQuestionCreate,
    BulkQuestionCreateResponse,
    BulkQuestionUpdate,
    BulkQuestionUpdateResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse
)
from app.modules.questions.service import QuestionService

# Create router
router = APIRouter()

# Initialize service
question_service = QuestionService()


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(question: QuestionCreate):
    """
    Create a new question.

    Supports three question types:
    - MCQ: Requires options and correctAnswer
    - Interview: Optional answer field
    - Output: Requires output field

    Args:
        question: Question creation data

    Returns:
        Created question with ID

    Raises:
        ResourceNotFoundException: If topic not found
        ValidationError: If type-specific fields are invalid
    """
    return await question_service.create(question)


@router.post("/bulk", response_model=BulkQuestionCreateResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_questions(data: BulkQuestionCreate):
    """
    Bulk create multiple questions.

    Creates multiple questions in a single atomic operation.
    All questions must be valid or the entire operation fails.

    Args:
        data: Bulk create data with list of questions

    Returns:
        Number of created questions and their data

    Raises:
        ResourceNotFoundException: If any topic not found
        ValidationError: If any question is invalid
        InvalidInputException: If bulk operation fails
    """
    return await question_service.bulk_create(data.questions)


@router.post("/generate", response_model=GenerateQuestionsResponse, status_code=status.HTTP_201_CREATED)
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate questions using AI (Google Gemini) for a specific topic.

    Generates questions based on the topic context (subject, chapter, topic names).
    Question count varies by type:
    - MCQ: 15 questions with 4 options each
    - Output: 15 code output questions
    - Interview: 10 detailed interview questions

    All generated questions are saved with Inactive status and sequential order numbers.

    Args:
        request: Generation request with topicId and question type

    Returns:
        Number of generated questions and their data with IDs

    Raises:
        InvalidObjectIdException: If topicId is invalid
        ResourceNotFoundException: If topic not found
        InvalidInputException: If generation or saving fails
    """
    return await question_service.generate_ai_questions(request.topicId, request.type)


@router.get("/", response_model=List[QuestionResponse])
async def get_all_questions(
    skip: int = Query(default=0, ge=0, description="Number of questions to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of questions to return"),
    status: Optional[QuestionStatus] = Query(default=None, description="Filter by status (Active or Inactive)"),
    topicId: Optional[str] = Query(default=None, description="Filter by topic ID"),
    type: Optional[QuestionType] = Query(default=None, description="Filter by question type (mcq, interview, output)")
):
    """
    Get all questions with pagination and optional filters.

    Questions are sorted by order in ascending order.

    Args:
        skip: Number of questions to skip (default: 0)
        limit: Maximum number of questions to return (default: 10, max: 100)
        status: Optional status filter (Active or Inactive)
        topicId: Optional topic ID filter
        type: Optional question type filter

    Returns:
        List of questions
    """
    return await question_service.get_all(
        skip=skip,
        limit=limit,
        status=status,
        topic_id=topicId,
        question_type=type
    )


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str):
    """
    Get a specific question by ID.

    Args:
        question_id: Question ID

    Returns:
        Question data

    Raises:
        InvalidObjectIdException: If question_id is invalid
        ResourceNotFoundException: If question not found
    """
    return await question_service.get_by_id(question_id)


@router.put("/bulk", response_model=BulkQuestionUpdateResponse)
async def bulk_update_questions(data: BulkQuestionUpdate):
    """
    Bulk update multiple questions.

    Updates multiple questions in a single atomic operation.
    All updates must be valid or the entire operation fails.

    Args:
        data: Bulk update data with list of {id, data} pairs

    Returns:
        Number of updated questions and their data

    Raises:
        InvalidObjectIdException: If any question_id is invalid
        InvalidInputException: If bulk operation fails
        ResourceNotFoundException: If any question not found
        ValidationError: If any update data is invalid
    """
    return await question_service.bulk_update(data.questions)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: str, question_update: QuestionUpdate):
    """
    Update an existing question.

    Args:
        question_id: Question ID
        question_update: Fields to update

    Returns:
        Updated question data

    Raises:
        InvalidObjectIdException: If question_id is invalid
        InvalidInputException: If no fields provided for update
        ResourceNotFoundException: If question or topic not found
        ValidationError: If type-specific fields are invalid
    """
    return await question_service.update(question_id, question_update)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: str):
    """
    Delete a question.

    Args:
        question_id: Question ID

    Returns:
        No content

    Raises:
        InvalidObjectIdException: If question_id is invalid
        ResourceNotFoundException: If question not found
    """
    await question_service.delete(question_id)
