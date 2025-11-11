"""
Pydantic schemas for Questions module.
Supports MCQ, Interview, and Output question types with type-specific validation.
"""

from enum import Enum
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from bson import ObjectId


class QuestionType(str, Enum):
    """Enum for question types."""
    MCQ = "mcq"
    INTERVIEW = "interview"
    OUTPUT = "output"


class QuestionStatus(str, Enum):
    """Enum for question status."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


# Base class with common fields
class QuestionBase(BaseModel):
    """Base schema for Question with common fields."""
    topicId: str = Field(..., description="Reference to the parent Topic ID")
    question: str = Field(..., min_length=3, description="The question text")
    status: QuestionStatus = Field(
        default=QuestionStatus.ACTIVE,
        description="Question status (Active or Inactive)"
    )
    order: int = Field(..., ge=1, description="Display order (must be positive integer)")


# Type-specific schemas for creation
class MCQQuestionCreate(QuestionBase):
    """Schema for creating an MCQ question."""
    type: Literal[QuestionType.MCQ] = QuestionType.MCQ
    options: List[str] = Field(..., min_length=2, max_length=10, description="Answer options (minimum 2)")
    correctAnswer: int = Field(..., ge=0, description="Index of correct answer (0-based)")
    explanation: Optional[str] = Field(None, max_length=10000, description="Explanation for the answer")

    @field_validator('correctAnswer')
    @classmethod
    def validate_correct_answer(cls, v, info):
        """Validate that correctAnswer is within options range."""
        options = info.data.get('options')
        if options and v >= len(options):
            raise ValueError(f"correctAnswer must be between 0 and {len(options)-1}")
        return v


class InterviewQuestionCreate(QuestionBase):
    """Schema for creating an Interview question."""
    type: Literal[QuestionType.INTERVIEW] = QuestionType.INTERVIEW
    answer: Optional[str] = Field(None, max_length=10000, description="Sample answer")
    explanation: Optional[str] = Field(None, max_length=10000, description="Additional explanation")


class OutputQuestionCreate(QuestionBase):
    """Schema for creating an Output question."""
    type: Literal[QuestionType.OUTPUT] = QuestionType.OUTPUT
    output: str = Field(..., max_length=10000, description="Expected output")
    explanation: Optional[str] = Field(None, max_length=10000, description="Explanation for the output")


# Union type for creation
QuestionCreate = Union[MCQQuestionCreate, InterviewQuestionCreate, OutputQuestionCreate]


# Update schemas (all fields optional except type for type-specific updates)
class MCQQuestionUpdate(BaseModel):
    """Schema for updating an MCQ question."""
    type: Optional[Literal[QuestionType.MCQ]] = None
    topicId: Optional[str] = None
    question: Optional[str] = Field(None, min_length=3)
    options: Optional[List[str]] = Field(None, min_length=2, max_length=10)
    correctAnswer: Optional[int] = Field(None, ge=0)
    explanation: Optional[str] = Field(None, max_length=10000)
    status: Optional[QuestionStatus] = None
    order: Optional[int] = Field(None, ge=1)

    @field_validator('correctAnswer')
    @classmethod
    def validate_correct_answer(cls, v, info):
        """Validate that correctAnswer is within options range if both are provided."""
        if v is not None:
            options = info.data.get('options')
            if options and v >= len(options):
                raise ValueError(f"correctAnswer must be between 0 and {len(options)-1}")
        return v


class InterviewQuestionUpdate(BaseModel):
    """Schema for updating an Interview question."""
    type: Optional[Literal[QuestionType.INTERVIEW]] = None
    topicId: Optional[str] = None
    question: Optional[str] = Field(None, min_length=3)
    answer: Optional[str] = Field(None, max_length=10000)
    explanation: Optional[str] = Field(None, max_length=10000)
    status: Optional[QuestionStatus] = None
    order: Optional[int] = Field(None, ge=1)


class OutputQuestionUpdate(BaseModel):
    """Schema for updating an Output question."""
    type: Optional[Literal[QuestionType.OUTPUT]] = None
    topicId: Optional[str] = None
    question: Optional[str] = Field(None, min_length=3)
    output: Optional[str] = Field(None, max_length=10000)
    explanation: Optional[str] = Field(None, max_length=10000)
    status: Optional[QuestionStatus] = None
    order: Optional[int] = Field(None, ge=1)


# Union type for updates
QuestionUpdate = Union[MCQQuestionUpdate, InterviewQuestionUpdate, OutputQuestionUpdate]


# Response schemas
class MCQQuestionResponse(MCQQuestionCreate):
    """Response schema for MCQ question."""
    id: str = Field(description="Unique identifier")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )


class InterviewQuestionResponse(InterviewQuestionCreate):
    """Response schema for Interview question."""
    id: str = Field(description="Unique identifier")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )


class OutputQuestionResponse(OutputQuestionCreate):
    """Response schema for Output question."""
    id: str = Field(description="Unique identifier")

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={ObjectId: str}
    )


# Union type for responses
QuestionResponse = Union[MCQQuestionResponse, InterviewQuestionResponse, OutputQuestionResponse]


# Bulk operation schemas
class BulkQuestionCreate(BaseModel):
    """Schema for bulk creating questions."""
    questions: List[QuestionCreate] = Field(..., min_length=1, max_length=100)


class BulkQuestionCreateResponse(BaseModel):
    """Response schema for bulk create."""
    created: int = Field(description="Number of questions created")
    questions: List[QuestionResponse] = Field(description="List of created questions")


class QuestionUpdateItem(BaseModel):
    """Single item for bulk update."""
    id: str = Field(..., description="Question ID to update")
    data: QuestionUpdate = Field(..., description="Update data")


class BulkQuestionUpdate(BaseModel):
    """Schema for bulk updating questions."""
    questions: List[QuestionUpdateItem] = Field(..., min_length=1, max_length=100)


class BulkQuestionUpdateResponse(BaseModel):
    """Response schema for bulk update."""
    updated: int = Field(description="Number of questions updated")
    questions: List[QuestionResponse] = Field(description="List of updated questions")


# AI Generation schemas
class GenerateQuestionsRequest(BaseModel):
    """Schema for AI question generation request."""
    topicId: str = Field(..., description="Topic ID for which to generate questions")
    type: QuestionType = Field(..., description="Type of questions to generate (mcq, output, interview)")


class GenerateQuestionsResponse(BaseModel):
    """Response schema for AI question generation."""
    generated: int = Field(description="Number of questions generated and saved")
    questions: List[QuestionResponse] = Field(description="List of generated questions with IDs")
