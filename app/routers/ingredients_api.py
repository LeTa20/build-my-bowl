from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.db import get_session
from app.models import Ingredient, UserIngredientNutrition
from app.auth import get_current_user, User
from sqlmodel import select

router = APIRouter()

# Request model for updating nutrition information
class UpdateNutritionRequest(BaseModel):
    ingredient_id: int = Field(ge=1, description="Ingredient ID, must be >= 1")
    calories: float = Field(ge=0, description="Calories, must be >= 0")
    protein: float = Field(ge=0, description="Protein, must be >= 0")
    fiber: float = Field(ge=0, description="Fiber, must be >= 0")
    sugar: float = Field(ge=0, description="Sugar, must be >= 0")


class UpdateNutritionResponse(BaseModel):
    ingredient_id: int
    updated: bool

# Endpoint to update nutrition information for an ingredient
@router.patch("/update_nutrition", response_model=UpdateNutritionResponse, status_code=status.HTTP_200_OK)
def update_nutrition(
    request: UpdateNutritionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UpdateNutritionResponse:
    ingredient = session.get(Ingredient, request.ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )
    
    # Save user-specific nutrition values
    user_nutrition = session.exec(
        select(UserIngredientNutrition).where(
            UserIngredientNutrition.user_id == current_user.id,
            UserIngredientNutrition.ingredient_id == request.ingredient_id
        )
    ).first()
    
    if user_nutrition:
        # Update existing user-specific values
        user_nutrition.calories = request.calories
        user_nutrition.protein = request.protein
        user_nutrition.fiber = request.fiber
        user_nutrition.sugar = request.sugar
        session.add(user_nutrition)
    else:
        # Create new user-specific values
        user_nutrition = UserIngredientNutrition(
            user_id=current_user.id,
            ingredient_id=request.ingredient_id,
            calories=request.calories,
            protein=request.protein,
            fiber=request.fiber,
            sugar=request.sugar,
        )
        session.add(user_nutrition)
    
    session.commit()
    
    return UpdateNutritionResponse(
        ingredient_id=ingredient.id,
        updated=True,
    )

