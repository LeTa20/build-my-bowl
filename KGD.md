Knowledge Goal Number & Name: [KG1] Endpoint Definition

File Reference: app/main.py:20-24 and app/routers/bowls_api.py:109-110,125-126,243-244
Code Fragment:

```python
# From app/main.py - Router registration with URL prefixes
app.include_router(
    bowls_api.router,
    prefix="/api/bowls",
    tags=["bowls-api"],
)

# From app/routers/bowls_api.py - Specific endpoint paths
@router.get("/{bowl_id}", status_code=status.HTTP_200_OK)
def get_bowl(bowl_id: int, ...):
    ...

@router.post("/create_bowl", status_code=status.HTTP_201_CREATED)
def create_bowl(...):
    ...
```

Justification: This code fragment shows two locations where the server's unique URL paths for handling incoming client requests are defined. The router prefixes in main.py are combined with route decorators in the router files to create complete endpoint URLs, such as /api/bowls/123 for a specific bowl_id and /api/bowls/create_bowl to create a new bowl. These unique URL paths define where resources can be accessed on the server.

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG2] HTTP Methods & Status Codes

File Reference: app/routers/bowls_api.py:164-178

Code Fragment:

```python
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
```

Justification: The route is defined using the @router.post decorator, which enforces the appropriate POST HTTP method. On success, the function returns a 200 OK status code. If the resource is not found or the user is not authorized, an HTTPException is raised, correctly signaling a 404 NOT FOUND or 401 UNAUTHORIZED status code to the client.

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG3] Endpoint Validation

File Reference: app/routers/auth_api.py:12-14

Code Fragment (Pydantic Schema):

```python
from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$", description="Username, 3-30 characters, alphanumeric and underscore only")
    password: str = Field(min_length=6, description="Password, must be at least 6 characters")
```

Justification: This Pydantic RegisterRequest schema is used in a FastAPI route to validate incoming JSON data. By defining min_length, max_length, and pattern constraints within the Field objects, FastAPI automatically performs Endpoint Validation. If a client submits a registration request with a username less than 3 characters, more than 30 characters, or containing invalid characters, or a password less than 6 characters, the server will reject the request and return a 422 Unprocessable Entity status code before the data even reaches the application logic.

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG4] Dependency Injection

File Reference: app/routers/bowls_api.py:109-115 and app/db.py:16-18

Code Fragment:

```python
# From app/routers/bowls_api.py
@router.get("/{bowl_id}", response_model=BowlResponse, status_code=status.HTTP_200_OK)
def get_bowl(
    bowl_id: int = Path(ge=1, description="Bowl ID, must be >= 1"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BowlResponse:
    bowl = get_and_verify_bowl(bowl_id, current_user, session, unauthorized_detail="Not authorized to access this bowl")
    # ... returns BowlResponse ...

# From app/db.py
def get_session():
    with Session(engine) as session:
        yield session
```

Justification: This FastAPI route uses the Depends() function to inject dependencies (session and current_user) into the function arguments.  This demonstrates Dependency Injection because the route handler receives its database session and authenticated user dependencies externally instead of creating them internally, which maintains Separation of Concerns (KG10) and simplifies testing.
___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG5] Data Model

File Reference: app/models.py:12-21

Code Fragment:

```python
from typing import Optional
from sqlmodel import SQLModel, Field

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

```

Justification: This SQLModel class defines the formal structure of the Ingredient data model, specifying how ingredient data is organized and stored in the PostgreSQL database. It defines fields with their types and constraints, including a primary key, optional fields with default values, and various data types (int, str, float, bool, Optional). The `table=True` parameter indicates that this model corresponds to a database table. This defines the formal structure that organizes nutritional information, file references, and ingredient properties.___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG6] CRUD Operations & Persistent Data

File Reference: app/routers/bowls_api.py:125-136

Code Fragment:

```python
@router.post("/create_bowl", response_model=CreateBowlResponse, status_code=status.HTTP_201_CREATED)
def create_bowl(
    request: CreateBowlRequest,
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
) -> CreateBowlResponse:  # Create a new bowl for the current user
    cleaned = request.name.strip()  # Clean bowl name
    bowl = Bowl(name=cleaned, user_id=current_user.id, saved=False) 
    session.add(bowl)
    session.commit()
    session.refresh(bowl)
    return CreateBowlResponse(bowl_id=bowl.id)

```

Justification: The create_bowl function demonstrates the Create operation from CRUD by creating a new Bowl instance, adding it to the database session with session.add(), and then committing it with session.commit(). The session.commit() call persists the data to PostgreSQL, which ensures the data remains available even after the application server restarts. This demonstrates Persistent Data because the bowl is stored in a database that persists beyond the application’s runtime, contrasting with in-memory data structures that would be lost when the server stops.

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG7] API Endpoints & JSON

File Reference: app/routers/bowls_api.py:74-80 and 164-178

Code Fragment:

```python
class SaveBowlRequest(BaseModel):
    bowl_id: int = Field(ge=1, description="Bowl ID, must be >= 1")

class SaveBowlResponse(BaseModel):
    bowl_id: int
    saved: bool

@router.post("/save_bowl", response_model=SaveBowlResponse, status_code=status.HTTP_200_OK)
def save_bowl(
    request: SaveBowlRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SaveBowlResponse:
    # ... logic to save bowl ...
    return SaveBowlResponse(bowl_id=bowl.id, saved=True)
```

Justification: This endpoint is designed to be consumed by other applications, as indicated by its location in bowls_api.py and its return type SaveBowlResponse, which is a Pydantic BaseModel. FastAPI automatically serializes the Pydantic models to JSON format, so the endpoint accepts JSON input via SaveBowlRequest and returns JSON output via SaveBowlResponse, demonstrating the standard text-based format used for API communication. For example, when a client sends {"bowl_id": 3} as JSON, the server responds with JSON such as {"bowl_id": 3, "saved": true}, allowing other applications to interact with the server by sending and receiving structured data.

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG8] UI Endpoints & HTMX

File Reference: app/routers/bowls_ui.py:528-536 and app/templates/ingredient_list.html:35-50

Code Fragment:

```python
@router.post("/bowl/add_ingredient", response_class=HTMLResponse)
def add_ingredient_to_bowl(
    request: Request,
    ingredient_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # ... logic to add ingredient ...
    return templates.TemplateResponse("bowl_section.html", {"request": request, "bowl": bowl, "bowl_data": bowl_data})
```

```html
<form hx-post="/bowl/add_ingredient" hx-target="#bowl-section" hx-swap="innerHTML">
  <input type="hidden" name="ingredient_id" value="{{ ingredient.id }}" />
  <button type="submit">Add to Bowl</button>
</form>
```

Justification: This endpoint returns HTML content for web browsers using response_class=HTMLResponse and templates.TemplateResponse(), demonstrating a UI Endpoint designed for human users rather than other applications. The HTMX attributes in the HTML form (hx-post, hx-target, hx-swap) allow the frontend to make AJAX requests directly from HTML without writing JavaScript code, automatically updating the #bowl-section element with the server's HTML response when the form is submitted.

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG9] User Interaction (CRUD)

File Reference: app/routers/bowls_ui.py:37-57, 482-488 and app/templates/saved_bowls.html:13-21

Code Fragment:

```python
@router.post("/bowl/delete", response_class=HTMLResponse)
def delete_bowl(
    request: Request,
    bowl_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    bowl = session.get(Bowl, bowl_id)
    bowl = verify_bowl_access(bowl, current_user)
    session.delete(bowl)
    session.commit()
    # ... returns updated saved bowls list ...
```

```html
<form hx-post="/bowl/delete" hx-target="#saved-bowls" hx-swap="innerHTML">
  <input type="hidden" name="bowl_id" value="{{ bowl.id }}" />
  <button type="submit">Remove</button>
</form>
```

Justification: This code demonstrates User Interaction (CRUD) by showing how a user-facing action (clicking the "Remove" button) corresponds to a backend CRUD operation (Delete). When a user clicks the "Remove" button in the template, it triggers a POST request to the delete_bowl endpoint, which performs the Delete operation by removing the bowl from the database using session.delete() and session.commit().

___________________________________________________________________________________________________

Knowledge Goal Number & Name: [KG10] Separation of Concerns

File Reference: app/models.py:24-28, app/routers/bowls_ui.py:67-77, and app/templates/empty_bowl.html:3-5

Code Fragment:

```python
# Data Access Layer - app/models.py:24-28
class Bowl(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    saved: bool = Field(default=False)

# Business Logic Layer - app/routers/bowls_ui.py:67-77
def get_or_create_unsaved_bowl(user_id: int, session: Session) -> Bowl:
    bowl = session.exec(select(Bowl).where(Bowl.user_id == user_id, Bowl.saved == False)).first()
    if not bowl:
        bowl = Bowl(name="My Bowl", user_id=user_id, saved=False)
        session.add(bowl)
        session.commit()
    return bowl
```

```html
<!-- Presentation Layer - app/templates/empty_bowl.html:3-5 -->
<form hx-get="/bowl" hx-target="#bowl-section" hx-swap="innerHTML">
  <button type="submit">Create New Bowl</button>
</form>
```

Justification: These different sections of code show the separation of concerns by dividing the application into distinct layers. The data access layer in app/models.py defines the Bowl data model structure. The business logic layer in app/routers/bowls_ui.py holds the route handlers that process requests and perform CRUD operations. Finally, the presentation layer in app/templates/ contains HTML templates with HTMX attributes for user interaction.

