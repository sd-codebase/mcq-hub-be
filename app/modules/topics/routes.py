"""
API routes for Topics module.
"""

from typing import List, Optional
from fastapi import APIRouter, status, Query

from app.modules.topics.schemas import TopicCreate, TopicUpdate, TopicResponse, TopicStatus
from app.modules.topics.service import TopicService

# Create router
router = APIRouter()

# Initialize service
topic_service = TopicService()


@router.post("/", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(topic: TopicCreate):
    """
    Create a new topic.

    Args:
        topic: Topic creation data

    Returns:
        Created topic with ID

    Raises:
        ResourceNotFoundException: If chapter not found
    """
    return await topic_service.create(topic)


@router.get("/", response_model=List[TopicResponse])
async def get_all_topics(
    skip: int = Query(default=0, ge=0, description="Number of topics to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of topics to return"),
    status: Optional[TopicStatus] = Query(default=None, description="Filter by status (Active or Inactive)"),
    chapterId: Optional[str] = Query(default=None, description="Filter by chapter ID")
):
    """
    Get all topics with pagination and optional filters.

    Topics are sorted by order in ascending order.

    Args:
        skip: Number of topics to skip (default: 0)
        limit: Maximum number of topics to return (default: 10, max: 100)
        status: Optional status filter (Active or Inactive)
        chapterId: Optional chapter ID filter

    Returns:
        List of topics
    """
    return await topic_service.get_all(skip=skip, limit=limit, status=status, chapter_id=chapterId)


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str):
    """
    Get a specific topic by ID.

    Args:
        topic_id: Topic ID

    Returns:
        Topic data

    Raises:
        InvalidObjectIdException: If topic_id is invalid
        ResourceNotFoundException: If topic not found
    """
    return await topic_service.get_by_id(topic_id)


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(topic_id: str, topic_update: TopicUpdate):
    """
    Update an existing topic.

    Args:
        topic_id: Topic ID
        topic_update: Fields to update

    Returns:
        Updated topic data

    Raises:
        InvalidObjectIdException: If topic_id is invalid
        InvalidInputException: If no fields provided for update
        ResourceNotFoundException: If topic or chapter not found
    """
    return await topic_service.update(topic_id, topic_update)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: str):
    """
    Delete a topic.

    Args:
        topic_id: Topic ID

    Returns:
        No content

    Raises:
        InvalidObjectIdException: If topic_id is invalid
        ResourceNotFoundException: If topic not found
    """
    await topic_service.delete(topic_id)
