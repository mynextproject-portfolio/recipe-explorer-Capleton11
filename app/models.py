from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional
import uuid

# Constants
MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50


class RecipeBase(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    cuisine: str
    tags: List[str] = Field(default_factory=list)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('title cannot be empty')
        if len(v) > MAX_TITLE_LENGTH:
            raise ValueError(f'title cannot exceed {MAX_TITLE_LENGTH} characters')
        return v

    @field_validator('description', 'cuisine')
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('cannot be empty')
        return v

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v: List[str]) -> List[str]:
        cleaned = [item.strip() for item in v if item.strip()]
        if not cleaned:
            raise ValueError('at least one ingredient is required')
        if len(cleaned) > MAX_INGREDIENTS:
            raise ValueError(f'cannot have more than {MAX_INGREDIENTS} ingredients')
        return cleaned

    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v: List[str]) -> List[str]:
        cleaned = [item.strip() for item in v if item.strip()]
        if not cleaned:
            raise ValueError('at least one instruction step is required')
        return cleaned


class Recipe(RecipeBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = "internal"  # "internal" | "external"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict()


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(RecipeBase):
    pass
