"""
API routes for Subjects module.
"""

from typing import List, Optional
from fastapi import APIRouter, status, Query

from app.modules.subjects.schemas import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectStatus,
    HierarchyCreate,
    HierarchyResponse
)
from app.modules.subjects.service import SubjectService

# Create router
router = APIRouter()

# Initialize service
subject_service = SubjectService()


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(subject: SubjectCreate):
    """
    Create a new subject.

    Args:
        subject: Subject creation data

    Returns:
        Created subject with ID

    Raises:
        DuplicateResourceException: If subject with name or shortName exists
    """
    return await subject_service.create(subject)


@router.post("/hierarchy", response_model=HierarchyResponse, status_code=status.HTTP_201_CREATED)
async def create_subject_hierarchy(hierarchy: HierarchyCreate):
    """
    Create a complete subject hierarchy with chapters and topics.

    Creates a subject along with its chapters and topics in a single request.
    All entities are created with Inactive status by default.

    Args:
        hierarchy: Hierarchy creation data with subject, chapters (topics), and topics (subtopics)

    Returns:
        Complete hierarchy with all created entities and their IDs

    Raises:
        DuplicateResourceException: If subject with name or shortName exists
        ValidationError: If any validation fails
    """
    return await subject_service.create_hierarchy(hierarchy)


@router.get("/", response_model=List[SubjectResponse])
async def get_all_subjects(
    skip: int = Query(default=0, ge=0, description="Number of subjects to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of subjects to return"),
    status: Optional[SubjectStatus] = Query(default=None, description="Filter by status (Active or Inactive)")
):
    """
    Get all subjects with pagination and optional status filter.

    Subjects are sorted by order in ascending order.

    Args:
        skip: Number of subjects to skip (default: 0)
        limit: Maximum number of subjects to return (default: 10, max: 100)
        status: Optional status filter (Active or Inactive)

    Returns:
        List of subjects
    """
    return await subject_service.get_all(skip=skip, limit=limit, status=status)


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(subject_id: str):
    """
    Get a specific subject by ID.

    Args:
        subject_id: Subject ID

    Returns:
        Subject data

    Raises:
        InvalidObjectIdException: If subject_id is invalid
        ResourceNotFoundException: If subject not found
    """
    return await subject_service.get_by_id(subject_id)


@router.get("/shortname/{short_name}", response_model=SubjectResponse)
async def get_subject_by_short_name(short_name: str):
    """
    Get a subject by its shortName.

    Args:
        short_name: Subject short name

    Returns:
        Subject data

    Raises:
        ResourceNotFoundException: If subject not found
    """
    return await subject_service.get_by_short_name(short_name)


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(subject_id: str, subject_update: SubjectUpdate):
    """
    Update an existing subject.

    Args:
        subject_id: Subject ID
        subject_update: Fields to update

    Returns:
        Updated subject data

    Raises:
        InvalidObjectIdException: If subject_id is invalid
        InvalidInputException: If no fields provided for update
        DuplicateResourceException: If name or shortName conflicts
        ResourceNotFoundException: If subject not found
    """
    return await subject_service.update(subject_id, subject_update)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: str):
    """
    Delete a subject.

    Args:
        subject_id: Subject ID

    Returns:
        No content

    Raises:
        InvalidObjectIdException: If subject_id is invalid
        ResourceNotFoundException: If subject not found
    """
    await subject_service.delete(subject_id)
