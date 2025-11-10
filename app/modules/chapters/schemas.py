"""
Pydantic schemas for Chapters module.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class ChapterStatus(str, Enum):
    """Enum for chapter status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ChapterBase(BaseModel):
    """Base schema for Chapter with common fields."""
    subjectId: str = Field(
        ...,
        description="Reference to the parent Subject ID"
    )
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name of the chapter"
    )
    status: ChapterStatus = Field(
        default=ChapterStatus.ACTIVE,
        description="Chapter status (Active or Inactive)"
    )
    order: int = Field(
        ...,
        ge=1,
        description="Display order (must be positive integer)"
    )


class ChapterCreate(ChapterBase):
    """Schema for creating a new chapter."""
    pass


class ChapterUpdate(BaseModel):
    """Schema for updating an existing chapter. All fields are optional."""
    subjectId: Optional[str] = Field(None, description="Reference to the parent Subject ID")
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    status: Optional[ChapterStatus] = None
    order: Optional[int] = Field(None, ge=1)


class ChapterResponse(ChapterBase):
    """Schema for chapter responses with ID."""
    id: str = Field(description="Unique identifier")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
