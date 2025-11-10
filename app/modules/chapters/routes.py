"""
API routes for Chapters module.
"""

from typing import List, Optional
from fastapi import APIRouter, status, Query

from app.modules.chapters.schemas import ChapterCreate, ChapterUpdate, ChapterResponse, ChapterStatus
from app.modules.chapters.service import ChapterService

# Create router
router = APIRouter()

# Initialize service
chapter_service = ChapterService()


@router.post("/", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_chapter(chapter: ChapterCreate):
    """
    Create a new chapter.

    Args:
        chapter: Chapter creation data

    Returns:
        Created chapter with ID

    Raises:
        ResourceNotFoundException: If subject not found
    """
    return await chapter_service.create(chapter)


@router.get("/", response_model=List[ChapterResponse])
async def get_all_chapters(
    skip: int = Query(default=0, ge=0, description="Number of chapters to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of chapters to return"),
    status: Optional[ChapterStatus] = Query(default=None, description="Filter by status (Active or Inactive)"),
    subjectId: Optional[str] = Query(default=None, description="Filter by subject ID")
):
    """
    Get all chapters with pagination and optional filters.

    Chapters are sorted by order in ascending order.

    Args:
        skip: Number of chapters to skip (default: 0)
        limit: Maximum number of chapters to return (default: 10, max: 100)
        status: Optional status filter (Active or Inactive)
        subjectId: Optional subject ID filter

    Returns:
        List of chapters
    """
    return await chapter_service.get_all(skip=skip, limit=limit, status=status, subject_id=subjectId)


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: str):
    """
    Get a specific chapter by ID.

    Args:
        chapter_id: Chapter ID

    Returns:
        Chapter data

    Raises:
        InvalidObjectIdException: If chapter_id is invalid
        ResourceNotFoundException: If chapter not found
    """
    return await chapter_service.get_by_id(chapter_id)


@router.put("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(chapter_id: str, chapter_update: ChapterUpdate):
    """
    Update an existing chapter.

    Args:
        chapter_id: Chapter ID
        chapter_update: Fields to update

    Returns:
        Updated chapter data

    Raises:
        InvalidObjectIdException: If chapter_id is invalid
        InvalidInputException: If no fields provided for update
        ResourceNotFoundException: If chapter or subject not found
    """
    return await chapter_service.update(chapter_id, chapter_update)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(chapter_id: str):
    """
    Delete a chapter.

    Args:
        chapter_id: Chapter ID

    Returns:
        No content

    Raises:
        InvalidObjectIdException: If chapter_id is invalid
        ResourceNotFoundException: If chapter not found
    """
    await chapter_service.delete(chapter_id)
