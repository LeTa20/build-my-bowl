from fastapi import APIRouter, Depends, HTTPException, status, Response, Path
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.db import get_session
from app.models import Bowl, BowlIngredient, Ingredient
from app.auth import get_current_user, User

router = APIRouter()

# Helper function to verify bowl access
def verify_bowl_access(
    bowl: Bowl | None, 
    current_user: User, 
    not_found_detail: str = "Bowl not found",
    unauthorized_detail: str = "Not authorized to modify this bowl"
) -> Bowl:
    # Verify bowl exists and user has access to it
    if not bowl:  # Bowl does not exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=not_found_detail,
        )
        
    # Check if the bowl belongs to the current user
    if bowl.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=unauthorized_detail,
        )
        
    return bowl

# Helper function to get and verify bowl access
def get_and_verify_bowl(
    bowl_id: int,
    current_user: User,
    session: Session,
    unauthorized_detail: str = "Not authorized to modify this bowl"
) -> Bowl:
    # Get bowl by ID and verify user has access to it
    bowl = session.get(Bowl, bowl_id)
    return verify_bowl_access(bowl, current_user, unauthorized_detail=unauthorized_detail)

# Helper function to verify ingredient exists
def verify_ingredient_exists(ingredient_id: int, session: Session) -> Ingredient:
    # Verify ingredient exists and return it
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )
    return ingredient

# Helper function to delete all bowl ingredients
def delete_bowl_ingredients(bowl_id: int, session: Session) -> None:
    # Delete all ingredients associated with a bowl
    bowl_ingredients = session.exec(
        select(BowlIngredient).where(BowlIngredient.bowl_id == bowl_id)
    ).all()
    for bi in bowl_ingredients:
        session.delete(bi)


class CreateBowlRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Bowl name, must be 1-100 characters")


class CreateBowlResponse(BaseModel):
    bowl_id: int


class SaveBowlRequest(BaseModel):
    bowl_id: int = Field(ge=1, description="Bowl ID, must be >= 1")


class SaveBowlResponse(BaseModel):
    bowl_id: int
    saved: bool


class AddIngredientRequest(BaseModel):
    bowl_id: int = Field(ge=1, description="Bowl ID, must be >= 1")
    ingredient_id: int = Field(ge=1, description="Ingredient ID, must be >= 1")
    quantity: float = Field(gt=0, description="Quantity, must be > 0")


class AddIngredientResponse(BaseModel):
    bowl_id: int


class RemoveIngredientRequest(BaseModel):
    bowl_id: int = Field(ge=1, description="Bowl ID, must be >= 1")
    ingredient_id: int = Field(ge=1, description="Ingredient ID, must be >= 1")


class RemoveIngredientResponse(BaseModel):
    bowl_id: int


class BowlResponse(BaseModel):
    id: int
    name: str
    user_id: int
    saved: bool

# Get bowl information by ID
@router.get("/{bowl_id}", response_model=BowlResponse, status_code=status.HTTP_200_OK)
def get_bowl(
    bowl_id: int = Path(ge=1, description="Bowl ID, must be >= 1"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BowlResponse:
    bowl = get_and_verify_bowl(bowl_id, current_user, session, unauthorized_detail="Not authorized to access this bowl")
    
    return BowlResponse(
        id=bowl.id,
        name=bowl.name,
        user_id=bowl.user_id,
        saved=bowl.saved,
    )

# Create a new bowl
@router.post("/create_bowl", response_model=CreateBowlResponse, status_code=status.HTTP_201_CREATED)
def create_bowl(
    request: CreateBowlRequest,
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
) -> CreateBowlResponse:  # Create a new bowl for the current user
    cleaned = request.name.strip()  # Clean bowl name (get name, remove leading/trailing spaces) and store cleaned name
    bowl = Bowl(name=cleaned, user_id=current_user.id, saved=False) 
    session.add(bowl)
    session.commit()
    session.refresh(bowl)
    return CreateBowlResponse(bowl_id=bowl.id)

# Update bowl information
@router.put("/{bowl_id}", response_model=BowlResponse, status_code=status.HTTP_200_OK)
def update_bowl(
    request: CreateBowlRequest,
    bowl_id: int = Path(ge=1, description="Bowl ID, must be >= 1"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BowlResponse:
    bowl = get_and_verify_bowl(bowl_id, current_user, session, unauthorized_detail="Not authorized to update this bowl")
    
    # Clean and update bowl name
    cleaned = request.name.strip()
    bowl.name = cleaned
    session.add(bowl)
    session.commit()
    session.refresh(bowl)
    
    # Return updated bowl details
    return BowlResponse(
        id=bowl.id,
        name=bowl.name,
        user_id=bowl.user_id,
        saved=bowl.saved,
    )

# Save bowl -> mark as saved 
@router.post("/save_bowl", response_model=SaveBowlResponse, status_code=status.HTTP_200_OK)
def save_bowl(
    request: SaveBowlRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SaveBowlResponse:
    bowl = get_and_verify_bowl(request.bowl_id, current_user, session, unauthorized_detail="Not authorized to save this bowl")
    
    # Mark bowl as saved
    bowl.saved = True
    session.add(bowl)
    session.commit()
    
    # Return response indicating bowl is saved
    return SaveBowlResponse(bowl_id=bowl.id, saved=True)

# Add ingredient to bowl
@router.post("/add_ingredient", response_model=AddIngredientResponse, status_code=status.HTTP_200_OK)
def add_ingredient(
    request: AddIngredientRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AddIngredientResponse:
    bowl = get_and_verify_bowl(request.bowl_id, current_user, session)
    
    # Check if ingredient exists
    ingredient = verify_ingredient_exists(request.ingredient_id, session)
    # Check if ingredient already in bowl
    existing = session.exec(
        select(BowlIngredient).where(
            BowlIngredient.bowl_id == request.bowl_id,
            BowlIngredient.ingredient_id == request.ingredient_id,
        )
    ).first() 
    
    # Update quantity if ingredient exists, else add new ingredient to bowl
    if existing:
        existing.quantity = request.quantity
    else:
        bowl_ingredient = BowlIngredient(
            bowl_id=request.bowl_id,
            ingredient_id=request.ingredient_id,
            quantity=request.quantity,
        )
        session.add(bowl_ingredient)
    
    session.commit() 
    return AddIngredientResponse(bowl_id=request.bowl_id)

# Remove ingredient from bowl
@router.post("/remove_ingredient", response_model=RemoveIngredientResponse, status_code=status.HTTP_200_OK)
def remove_ingredient(
    request: RemoveIngredientRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RemoveIngredientResponse:
    bowl = get_and_verify_bowl(request.bowl_id, current_user, session)
    
    # Check if ingredient exists in bowl
    bowl_ingredient = session.exec(
        select(BowlIngredient).where(
            BowlIngredient.bowl_id == request.bowl_id,
            BowlIngredient.ingredient_id == request.ingredient_id,
        )
    ).first() 
    
    # Raise error if ingredient not found in bowl
    if not bowl_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found in bowl",
        )
    
    session.delete(bowl_ingredient)
    session.commit()
    
    return RemoveIngredientResponse(bowl_id=request.bowl_id)

# Delete saved bowl by ID
@router.delete("/{bowl_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bowl(
    bowl_id: int = Path(ge=1, description="Bowl ID, must be >= 1"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowl = get_and_verify_bowl(bowl_id, current_user, session, unauthorized_detail="Not authorized to delete this bowl")
    
    # Delete all ingredients associated with the bowl
    delete_bowl_ingredients(bowl_id, session)
    
    # Delete the bowl itself
    session.delete(bowl)
    session.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
