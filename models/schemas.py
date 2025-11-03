from typing import List, Optional

from pydantic import BaseModel, Field


class RecipeIngredient(BaseModel):
    name: str = Field(..., max_length=50)

    class Config:
        extra = "forbid"


class RecipeCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    cooking_time: int = Field(..., gt=0, le=300)
    ingredients: List[RecipeIngredient] = Field(..., max_items=20)

    class Config:
        extra = "forbid"


class Recipe(BaseModel):
    id: int
    title: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    cooking_time: int = Field(..., gt=0, le=300)
    views: int = Field(..., ge=0)
    ingredients: List[RecipeIngredient] = Field(..., max_items=20)

    class Config:
        extra = "forbid"


class RecipeSearch(BaseModel):
    id: int
    title: str = Field(..., max_length=100)
    views: int = Field(..., ge=0)
    cooking_time: int = Field(..., gt=0, le=300)

    class Config:
        extra = "forbid"
