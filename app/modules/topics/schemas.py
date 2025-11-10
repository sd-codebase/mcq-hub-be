"""
Pydantic schemas for Topics module.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class TopicStatus(str, Enum):
    """Enum for topic status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class TopicBase(BaseModel):
    """Base schema for Topic with common fields."""
    chapterId: str = Field(
        ...,
        description="Reference to the parent Chapter ID"
    )
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name of the topic"
    )
    status: TopicStatus = Field(
        default=TopicStatus.ACTIVE,
        description="Topic status (Active or Inactive)"
    )
    order: int = Field(
        ...,
        ge=1,
        description="Display order (must be positive integer)"
    )


class TopicCreate(TopicBase):
    """Schema for creating a new topic."""
    pass


class TopicUpdate(BaseModel):
    """Schema for updating an existing topic. All fields are optional."""
    chapterId: Optional[str] = Field(None, description="Reference to the parent Chapter ID")
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    status: Optional[TopicStatus] = None
    order: Optional[int] = Field(None, ge=1)


class TopicResponse(TopicBase):
    """Schema for topic responses with ID."""
    id: str = Field(description="Unique identifier")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
