"""
Pydantic schemas for Subjects module.
"""

import re
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from bson import ObjectId


class SubjectStatus(str, Enum):
    """Enum for subject status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


def generate_shortname(name: str) -> str:
    """
    Generate shortName from name if not provided.

    Rules:
    - Keep alphanumeric characters and special chars: $, +, -, _, #
    - Remove all other special characters
    - Replace multiple spaces with single hyphen
    - Convert to lowercase

    Args:
        name: Subject name

    Returns:
        Generated short name
    """
    # Keep only alphanumeric and allowed special chars: $ + - _ #
    cleaned = re.sub(r'[^a-zA-Z0-9\s$+\-_#]', '', name)
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Replace spaces with hyphens
    cleaned = cleaned.replace(' ', '-')
    # Convert to lowercase
    return cleaned.lower()


class SubjectBase(BaseModel):
    """Base schema for Subject with common fields."""
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Full name of the subject"
    )
    shortName: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Short name or abbreviation for the subject (auto-generated if not provided)"
    )
    status: SubjectStatus = Field(
        default=SubjectStatus.ACTIVE,
        description="Subject status (Active or Inactive)"
    )
    order: int = Field(
        ...,
        ge=1,
        description="Display order (must be positive integer)"
    )

    @field_validator('name')
    @classmethod
    def validate_name_no_leading_trailing_spaces(cls, v: str) -> str:
        """Ensure no leading or trailing spaces in name."""
        if v != v.strip():
            raise ValueError("Name cannot have leading or trailing spaces")
        return v


class SubjectCreate(SubjectBase):
    """Schema for creating a new subject."""

    @model_validator(mode='before')
    @classmethod
    def generate_shortname_if_missing(cls, data: Any) -> Any:
        """Generate shortName from name if not provided, or uppercase if provided."""
        if isinstance(data, dict):
            # If shortName is not provided or empty, generate it from name
            if not data.get('shortName'):
                if data.get('name'):
                    data['shortName'] = generate_shortname(data['name'])
            else:
                # If shortName is provided, convert to uppercase
                data['shortName'] = data['shortName'].upper()
        return data

    @field_validator('shortName')
    @classmethod
    def validate_shortname_no_leading_trailing_spaces(cls, v: Optional[str]) -> Optional[str]:
        """Ensure no leading or trailing spaces in shortName."""
        if v is not None and v != v.strip():
            raise ValueError("Short name cannot have leading or trailing spaces")
        return v


class SubjectUpdate(BaseModel):
    """Schema for updating an existing subject. All fields are optional."""
    name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100
    )
    shortName: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50
    )
    status: Optional[SubjectStatus] = None
    order: Optional[int] = Field(None, ge=1)

    @model_validator(mode='before')
    @classmethod
    def handle_shortname_generation(cls, data: Any) -> Any:
        """
        Generate shortName from name if name is being updated but shortName is not provided.
        If shortName is provided, convert to uppercase.
        """
        if isinstance(data, dict):
            # If name is being updated but shortName is not provided
            if data.get('name') and 'shortName' not in data:
                data['shortName'] = generate_shortname(data['name'])
            # If shortName is explicitly provided (not None), uppercase it
            elif data.get('shortName'):
                data['shortName'] = data['shortName'].upper()
        return data

    @field_validator('name')
    @classmethod
    def validate_name_no_leading_trailing_spaces(cls, v: Optional[str]) -> Optional[str]:
        """Ensure no leading or trailing spaces in name."""
        if v is not None and v != v.strip():
            raise ValueError("Name cannot have leading or trailing spaces")
        return v

    @field_validator('shortName')
    @classmethod
    def validate_shortname_no_leading_trailing_spaces(cls, v: Optional[str]) -> Optional[str]:
        """Ensure no leading or trailing spaces in shortName."""
        if v is not None and v != v.strip():
            raise ValueError("Short name cannot have leading or trailing spaces")
        return v


class SubjectResponse(SubjectBase):
    """Schema for subject responses with ID."""
    id: str = Field(description="Unique identifier")
    shortName: str = Field(description="Short name or abbreviation for the subject")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )
