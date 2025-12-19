from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from typing import Optional
import string

from app.db import get_session
from app.models import Bowl, BowlIngredient, Ingredient, User, UserIngredientNutrition
from app.auth import get_current_user, get_optional_user, verify_password, hash_password

router = APIRouter() # Router for bowls UI
templates = Jinja2Templates(directory="app/templates") # Jinja2 templates directory

INGREDIENT_ORDER = [
    "Greek Yogurt",
    "Plain Yogurt",
    "Strawberry Yogurt",
    "Banana",
    "Blueberries",
    "Strawberry",
    "Nuts",
    "Peanut Butter",
    "Honey",
]

# Sort ingredients based on predefined order
def sort_ingredients(ingredients: list[Ingredient]) -> list[Ingredient]:
    # Sort ingredients according to the specified display order.
    order_map = {name: idx for idx, name in enumerate(INGREDIENT_ORDER)}
    return sorted( 
        ingredients,
        key=lambda ing: order_map.get(ing.name, 999)  # Put unknown ingredients at the end
    )

# Helper function to verify bowl access
def verify_bowl_access(
    bowl: Bowl | None, 
    current_user: User, 
    not_found_detail: str = "Bowl not found",
    unauthorized_detail: str = "Not authorized to access this bowl"
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
            status_code=status.HTTP_404_NOT_FOUND,  # Using 404 for UI consistency
            detail=unauthorized_detail,
        )
        
    return bowl

# Helper function to get saved bowls for a user
def get_saved_bowls(user_id: int, session: Session) -> list[Bowl]:
    # Get all saved bowls for a user
    return session.exec(
        select(Bowl).where(Bowl.user_id == user_id, Bowl.saved == True)
    ).all()

# Helper function to get or create unsaved bowl for a user
def get_or_create_unsaved_bowl(user_id: int, session: Session) -> Bowl:
    # Get the current unsaved bowl for a user, or create one if it doesn't exist
    bowl = session.exec(
        select(Bowl).where(Bowl.user_id == user_id, Bowl.saved == False)
    ).first()
    if not bowl:
        bowl = Bowl(name="My Bowl", user_id=user_id, saved=False)
        session.add(bowl)
        session.commit()
        session.refresh(bowl)
    return bowl

# Helper function to get nutrition values for an ingredient (user-specific or default)
def get_ingredient_nutrition(ingredient_id: int, user_id: int, session: Session) -> dict:
    # Check for user-specific nutrition values first
    user_nutrition = session.exec(
        select(UserIngredientNutrition).where(
            UserIngredientNutrition.user_id == user_id,
            UserIngredientNutrition.ingredient_id == ingredient_id
        )
    ).first()
    
    if user_nutrition:
        return {
            "calories": user_nutrition.calories,
            "protein": user_nutrition.protein,
            "fiber": user_nutrition.fiber,
            "sugar": user_nutrition.sugar,
        }
    
    # Fall back to default ingredient values
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        return {"calories": 0.0, "protein": 0.0, "fiber": 0.0, "sugar": 0.0}
    
    return {
        "calories": ingredient.calories,
        "protein": ingredient.protein,
        "fiber": ingredient.fiber,
        "sugar": ingredient.sugar,
    }

# Helper function to prepare home content context
def prepare_home_context(request: Request, user: User, session: Session) -> dict:
    # Prepare context dictionary for home_content.html template
    ingredients = sort_ingredients(session.exec(select(Ingredient)).all())
    bowls = get_saved_bowls(user.id, session)
    current_bowl = session.exec(
        select(Bowl).where(Bowl.user_id == user.id, Bowl.saved == False)
    ).first()
    
    bowl_data = None
    if current_bowl:
        bowl_data = calculate_nutrition(current_bowl.id, user.id, session)
    
    return {
        "request": request,
        "user": user,
        "ingredients": ingredients,
        "bowls": bowls,
        "current_bowl": current_bowl,
        "bowl": current_bowl,  # Also pass as 'bowl' for bowl_section.html compatibility
        "bowl_data": bowl_data,
    }

# Calculate total nutrition for a bowl and prepare ingredient details
def calculate_nutrition(bowl_id: int, user_id: int, session: Session) -> dict:
    bowl_ingredients = session.exec( # Get all ingredients in the bowl
        select(BowlIngredient).where(BowlIngredient.bowl_id == bowl_id)
    ).all()
    
    # Initialize totals
    total_calories = 0.0
    total_protein = 0.0
    total_fiber = 0.0
    total_sugar = 0.0
    
    ingredients_list = []
    for bi in bowl_ingredients: # Iterate through each bowl ingredient
        ingredient = session.get(Ingredient, bi.ingredient_id)
        if not ingredient:
            continue
        
        # Get nutrition values (user-specific or default)
        nutrition = get_ingredient_nutrition(bi.ingredient_id, user_id, session)
        
        # Calculate nutrition for this ingredient based on quantity
        calories = nutrition["calories"] * bi.quantity
        protein = nutrition["protein"] * bi.quantity
        fiber = nutrition["fiber"] * bi.quantity
        sugar = nutrition["sugar"] * bi.quantity
        
        # Accumulate totals
        total_calories += calories
        total_protein += protein
        total_fiber += fiber
        total_sugar += sugar
        
        # set units 
        unit = ""
        if "yogurt" in ingredient.name.lower():  # Lowercase 
            unit = "cup" if bi.quantity == 1.0 else "cups"
        elif "honey" in ingredient.name.lower():
            unit = "tbsp"
        elif "peanut" in ingredient.name.lower():
            unit = "tbsp"
        elif "nuts" in ingredient.name.lower():
            unit = "cup" if bi.quantity == 1.0 else "cups"
        elif "strawberry" in ingredient.name.lower() and "yogurt" not in ingredient.name.lower():
            unit = "strawberry" if bi.quantity == 1.0 else "strawberries"
        elif "blueberr" in ingredient.name.lower():
            unit = "cup" if bi.quantity == 1.0 else "cups"
        elif "banana" in ingredient.name.lower():
            unit = "medium banana" if bi.quantity == 1.0 else "medium bananas"
        
        # Append ingredient details to the list
        ingredients_list.append({
            "id": ingredient.id,
            "name": ingredient.name,
            "quantity": bi.quantity,
            "unit": unit,
            "calories": round(calories, 2),
            "protein": round(protein, 2),
            "fiber": round(fiber, 2),
            "sugar": round(sugar, 2),
            "icon_filename": ingredient.icon_filename,
            "bowl_image_filename": ingredient.bowl_image_filename,
            "is_drizzle": ingredient.is_drizzle,
        })
    
    tags = [] 
    # Protein tag 
    if total_protein >= 20: 
        tags.append("High Protein")
    elif total_protein >= 10:
        tags.append("Moderate Protein")
    else:
        tags.append("Low Protein")
    
    # Fiber tag 
    if total_fiber >= 6:
        tags.append("High Fiber")
    elif total_fiber >= 3:
        tags.append("Moderate Fiber")
    else:
        tags.append("Low Fiber")
    
    # Sugar tag
    if total_sugar >= 20:
        tags.append("High Sugar")
    elif total_sugar >= 10:
        tags.append("Moderate Sugar")
    else:
        tags.append("Low Sugar")
    
    # Return nutrition summary and ingredient details
    return {
        "ingredients": ingredients_list,
        "total_calories": round(total_calories, 2),
        "total_protein": round(total_protein, 2),
        "total_fiber": round(total_fiber, 2),
        "total_sugar": round(total_sugar, 2),
        "tags": tags,
    }

# Home page -> show login if not logged in, else show bowl builder
@router.get("/", response_class=HTMLResponse)
def home(request: Request, session: Session = Depends(get_session)):
    # Check for user cookie -> if logged in, show home; if not, show login (NOT register)
    user = get_optional_user(request, session) 
    if not user: 
        # If the user is not logged in -> show login page
        return templates.TemplateResponse(
            "login_wrapper.html",
            {"request": request, "error": None},
        )
    # If logged in, show home page with bowl builder
    context = prepare_home_context(request, user, session)
    
    # Render home page template with user, ingredients, bowls, and current bowl data
    return templates.TemplateResponse(
        "home.html",
        context,
    )

# Login page
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, session: Session = Depends(get_session)):
    # If already logged in, redirect to home (change URL to /)
    try:
        user = get_optional_user(request, session)
        if user:
            # Use redirect to change the URL to / so refresh stays on home
            return RedirectResponse(url="/", status_code=303)
    except Exception:
        # If any error occurs, just show login form
        pass
    
    # Check if this is an HTMX request -> return fragment only
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": None},
        )
    
    # else return full page with wrapper
    return templates.TemplateResponse(
        "login_wrapper.html",
        {"request": request, "error": None},
    )

# Register page
@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request, session: Session = Depends(get_session)):
    # If already logged in, redirect to home (change URL to /)
    try:
        user = get_optional_user(request, session)
        if user:
            # Use redirect to change the URL to / so refresh stays on home
            return RedirectResponse(url="/", status_code=303)
    except Exception:
        # If any error occurs, just show register form
        pass
    
    # Check if this is an HTMX request - return fragment only
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": None},
        )
    
    # Otherwise return full page with wrapper
    return templates.TemplateResponse(
        "register_wrapper.html",
        {"request": request, "error": None},
    )

# Register new user via HTMX
@router.post("/register", response_class=HTMLResponse)
def register_htmx( # HTMX registration endpoint
    request: Request,
    name: str = Form(...), # User's name that will appear in header for bowl builder (Welcome name!)
    username: str = Form(...), 
    password: str = Form(...), 
    session: Session = Depends(get_session),
):
    try: # Check if username already exists
        existing = session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing: 
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Username already exists"}, 
            )
        
        # validation for empty fields
        if not username.strip() or not password.strip() or not name.strip():
            return templates.TemplateResponse( 
                "register.html",
                {"request": request, "error": "Name, username and password cannot be empty"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        # Password validation -> minimum 6 characters and must contain a special character
        if len(password) < 6:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Password must be at least 6 characters long"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        # Check for special character
        has_special = any(char in string.punctuation for char in password)
        if not has_special:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Password must contain at least one special character"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        # Create new user
        user = User(
            username=username,
            password_hash=hash_password(password),
            name=name.strip(),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Set cookie and return home content directly for HTMX
        response = templates.TemplateResponse(
            "home_content.html",
            prepare_home_context(request, user, session),
        )
        response.set_cookie(key="username", value=user.username) 
        return response
    except Exception as e: # Log any unexpected error during registration
        import traceback
        print(f"Registration error: {e}")
        print(traceback.format_exc())
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"Registration failed: {str(e)}"},
        )

# Login via HTMX
@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    try: # Validate user credentials
        user = session.exec(
            select(User).where(User.username == username)
        ).first()
        
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid username or password"},
            )
        
        if not verify_password(password, user.password_hash):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid username or password"},
            )
        
        # Set cookie and return home content directly for HTMX
        response = templates.TemplateResponse(
            "home_content.html",
            prepare_home_context(request, user, session),
        )
        response.set_cookie(key="username", value=user.username)
        return response
    except Exception as e:
        import traceback
        print(f"Login error: {e}")
        print(traceback.format_exc())
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"Login failed: {str(e)}"},
        )

# Logout via HTMX
@router.post("/logout", response_class=HTMLResponse)
def logout(request: Request):
    # Return login fragment for HTMX swap
    response = templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )
    response.delete_cookie(key="username", path="/")
    return response


@router.get("/bowl", response_class=HTMLResponse)
def get_bowl_view(
    request: Request,
    bowl_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if bowl_id:
        bowl = session.get(Bowl, bowl_id)
        bowl = verify_bowl_access(bowl, current_user)
    else:
        bowl = get_or_create_unsaved_bowl(current_user.id, session)
    
    bowl_data = calculate_nutrition(bowl.id, current_user.id, session)
    
    # Render bowl section
    bowl_template = templates.env.get_template("bowl_section.html")
    bowl_content = bowl_template.render(
        request=request,
        bowl=bowl,
        bowl_data=bowl_data,
    )
    
    # Also update ingredient list with current bowl context
    ingredients = sort_ingredients(session.exec(select(Ingredient)).all())
    ingredient_list_template = templates.env.get_template("ingredient_list.html")
    ingredient_list_content = ingredient_list_template.render(
        request=request,
        ingredients=ingredients,
        current_bowl=bowl,  # Pass the current bowl so forms include bowl_id
    )
    
    # Return bowl section with out-of-band update for ingredient list
    return HTMLResponse(
        content=bowl_content + f'<div id="ingredient-list" hx-swap-oob="innerHTML">{ingredient_list_content}</div>'
    )


@router.get("/bowls", response_class=HTMLResponse)
def get_saved_bowls_view(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowls = get_saved_bowls(current_user.id, session)
    
    return templates.TemplateResponse(
        "saved_bowls.html",
        {
            "request": request,
            "bowls": bowls,
        },
    )


@router.post("/bowl/delete", response_class=HTMLResponse)
def delete_bowl(
    request: Request,
    bowl_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        bowl = session.get(Bowl, bowl_id)
        bowl = verify_bowl_access(bowl, current_user)
        
        # Store user_id before deletion
        user_id = current_user.id
        
        # Delete all bowl ingredients first
        bowl_ingredients = session.exec(
            select(BowlIngredient).where(BowlIngredient.bowl_id == bowl_id)
        ).all()
        for bi in bowl_ingredients:
            session.delete(bi)
        
        # Flush to ensure bowl ingredients are deleted before deleting the bowl
        session.flush()
        
        # Delete the bowl
        session.delete(bowl)
        session.commit()
        
        # Return updated saved bowls list (query after commit to ensure deletion is reflected)
        bowls = get_saved_bowls(user_id, session)
        
        return templates.TemplateResponse(
            "saved_bowls.html",
            {
                "request": request,
                "bowls": bowls,
            },
        )
    except Exception as e:
        # Log the error and re-raise for debugging
        import traceback
        print(f"Error in delete_bowl: {e}")
        print(traceback.format_exc())
        raise


@router.post("/bowl/add_ingredient", response_class=HTMLResponse)
def add_ingredient_to_bowl(
    request: Request,
    bowl_id: Optional[int] = Form(None),
    ingredient_id: int = Form(...),
    quantity: float = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if bowl_id:
        bowl = session.get(Bowl, bowl_id)
        bowl = verify_bowl_access(bowl, current_user)
    else:
        bowl = get_or_create_unsaved_bowl(current_user.id, session)
    
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )
    
    existing = session.exec(
        select(BowlIngredient).where(
            BowlIngredient.bowl_id == bowl.id,
            BowlIngredient.ingredient_id == ingredient_id,
        )
    ).first()
    
    if existing:
        existing.quantity = quantity
    else:
        bowl_ingredient = BowlIngredient(
            bowl_id=bowl.id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        )
        session.add(bowl_ingredient)
    
    session.commit()
    
    bowl_data = calculate_nutrition(bowl.id, current_user.id, session)
    
    return templates.TemplateResponse(
        "bowl_section.html",
        {
            "request": request,
            "bowl": bowl,
            "bowl_data": bowl_data,
        },
    )


@router.post("/bowl/remove_ingredient", response_class=HTMLResponse)
def remove_ingredient_from_bowl(
    request: Request,
    bowl_id: int = Form(...),
    ingredient_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowl = session.get(Bowl, bowl_id)
    bowl = verify_bowl_access(bowl, current_user)
    
    bowl_ingredient = session.exec(
        select(BowlIngredient).where(
            BowlIngredient.bowl_id == bowl_id,
            BowlIngredient.ingredient_id == ingredient_id,
        )
    ).first()
    
    if bowl_ingredient:
        session.delete(bowl_ingredient)
        session.commit()
    
    bowl_data = calculate_nutrition(bowl_id, current_user.id, session)
    
    return templates.TemplateResponse(
        "bowl_section.html",
        {
            "request": request,
            "bowl": bowl,
            "bowl_data": bowl_data,
        },
    )


@router.get("/bowl/edit_name", response_class=HTMLResponse)
def edit_bowl_name_form(
    request: Request,
    bowl_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowl = session.get(Bowl, bowl_id)
    bowl = verify_bowl_access(bowl, current_user)
    
    return templates.TemplateResponse(
        "bowl_name_edit.html",
        {
            "request": request,
            "bowl": bowl,
        },
    )


@router.post("/bowl/update_name", response_class=HTMLResponse)
def update_bowl_name(
    request: Request,
    bowl_id: int = Form(...),
    name: str = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowl = session.get(Bowl, bowl_id)
    bowl = verify_bowl_access(bowl, current_user)
    
    cleaned_name = name.strip()
    if not cleaned_name:
        cleaned_name = "My Bowl"
    
    bowl.name = cleaned_name
    session.add(bowl)
    session.commit()
    session.refresh(bowl)
    
    bowl_data = calculate_nutrition(bowl.id, session)
    
    return templates.TemplateResponse(
        "bowl_section.html",
        {
            "request": request,
            "bowl": bowl,
            "bowl_data": bowl_data,
        },
    )


@router.post("/bowl/reset", response_class=HTMLResponse)
def reset_bowl(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Delete the current unsaved bowl (if it exists) to clear the display
    current_bowl = session.exec(
        select(Bowl).where(
            Bowl.user_id == current_user.id, Bowl.saved == False
        )
    ).first()
    if current_bowl:
        # Delete all bowl ingredients first
        bowl_ingredients = session.exec(
            select(BowlIngredient).where(BowlIngredient.bowl_id == current_bowl.id)
        ).all()
        for bi in bowl_ingredients:
            session.delete(bi)
        session.delete(current_bowl)
        session.commit()
    
    # Return empty bowl template
    return templates.TemplateResponse(
        "empty_bowl.html",
        {"request": request},
    )


@router.post("/bowl/save", response_class=HTMLResponse)
def save_bowl_htmx(
    request: Request,
    bowl_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowl = session.get(Bowl, bowl_id)
    bowl = verify_bowl_access(bowl, current_user)

    # Mark bowl as saved
    bowl.saved = True
    session.add(bowl)
    session.commit()
    session.refresh(bowl)
    
    # Calculate nutrition for the bowl
    bowl_data = calculate_nutrition(bowl.id, current_user.id, session)
    
    # Get updated saved bowls list
    bowls = get_saved_bowls(current_user.id, session)
    
    # Render bowl section template
    bowl_template = templates.env.get_template("bowl_section.html")
    bowl_content = bowl_template.render(
        request=request,
        bowl=bowl,
        bowl_data=bowl_data,
    )
    
    # Render saved bowls template
    saved_bowls_template = templates.env.get_template("saved_bowls.html")
    saved_bowls_content = saved_bowls_template.render(
        request=request,
        bowls=bowls,
    )
    
    # Return bowl section with out-of-band update for saved bowls list
    return HTMLResponse(
        content=bowl_content + f'<div id="saved-bowls" hx-swap-oob="innerHTML">{saved_bowls_content}</div>'
    )


@router.get("/ingredients/edit", response_class=HTMLResponse)
def edit_ingredient_form(
    request: Request,
    ingredient_id: int,
    bowl_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )
    
    # Get user-specific nutrition values or use defaults
    nutrition = get_ingredient_nutrition(ingredient_id, current_user.id, session)
    
    # Create a dict with ingredient data including user-specific nutrition
    ingredient_data = {
        "id": ingredient.id,
        "name": ingredient.name,
        "calories": nutrition["calories"],
        "protein": nutrition["protein"],
        "fiber": nutrition["fiber"],
        "sugar": nutrition["sugar"],
        "icon_filename": ingredient.icon_filename,
        "bowl_image_filename": ingredient.bowl_image_filename,
        "is_drizzle": ingredient.is_drizzle,
    }
    
    return templates.TemplateResponse(
        "ingredient_edit.html",
        {
            "request": request,
            "ingredient": ingredient_data,
            "bowl_id": bowl_id,
        },
    )


@router.post("/ingredients/update", response_class=HTMLResponse)
def update_ingredient_htmx(
    request: Request,
    ingredient_id: int = Form(...),
    bowl_id: Optional[int] = Form(None),
    calories: float = Form(...),
    protein: float = Form(...),
    fiber: float = Form(...),
    sugar: float = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ingredient = session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found",
        )
    
    # Save user-specific nutrition values
    user_nutrition = session.exec(
        select(UserIngredientNutrition).where(
            UserIngredientNutrition.user_id == current_user.id,
            UserIngredientNutrition.ingredient_id == ingredient_id
        )
    ).first()
    
    if user_nutrition:
        # Update existing user-specific values
        user_nutrition.calories = calories
        user_nutrition.protein = protein
        user_nutrition.fiber = fiber
        user_nutrition.sugar = sugar
        session.add(user_nutrition)
    else:
        # Create new user-specific values
        user_nutrition = UserIngredientNutrition(
            user_id=current_user.id,
            ingredient_id=ingredient_id,
            calories=calories,
            protein=protein,
            fiber=fiber,
            sugar=sugar,
        )
        session.add(user_nutrition)
    
    session.commit()
    
    # Get the current bowl - use provided bowl_id or default to unsaved bowl
    if bowl_id:
        bowl = session.get(Bowl, bowl_id)
        bowl = verify_bowl_access(bowl, current_user)
    else:
        bowl = get_or_create_unsaved_bowl(current_user.id, session)
    
    # Calculate updated nutrition for the bowl
    bowl_data = calculate_nutrition(bowl.id, current_user.id, session)
    
    # Render ingredient list with current bowl context
    ingredients = sort_ingredients(session.exec(select(Ingredient)).all())
    ingredient_list_template = templates.env.get_template("ingredient_list.html")
    ingredient_list_content = ingredient_list_template.render(
        request=request,
        ingredients=ingredients,
        current_bowl=bowl,
    )
    
    # Render bowl section with updated nutrition
    bowl_template = templates.env.get_template("bowl_section.html")
    bowl_content = bowl_template.render(
        request=request,
        bowl=bowl,
        bowl_data=bowl_data,
    )
    
    # Return both ingredient list and bowl section updates
    return HTMLResponse(
        content=ingredient_list_content + f'<div id="bowl-section" hx-swap-oob="innerHTML">{bowl_content}</div>'
    )
