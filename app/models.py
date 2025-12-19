from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    name: str


class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    calories: float
    protein: float
    fiber: float
    sugar: float
    icon_filename: Optional[str] = None  # For ingredient list selection
    bowl_image_filename: Optional[str] = None  # For bowl display
    is_drizzle: bool = Field(default=False)  # For drizzle


class Bowl(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    saved: bool = Field(default=False)


class BowlIngredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bowl_id: int = Field(foreign_key="bowl.id")
    ingredient_id: int = Field(foreign_key="ingredient.id")
    quantity: float


class UserIngredientNutrition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    ingredient_id: int = Field(foreign_key="ingredient.id")
    calories: float
    protein: float
    fiber: float
    sugar: float
