from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import bowls_api, bowls_ui, auth_api, ingredients_api

app = FastAPI()

init_db()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

app.include_router(
    auth_api.router,
    prefix="/api",
    tags=["auth-api"],
)

app.include_router(
    bowls_api.router,
    prefix="/api/bowls",
    tags=["bowls-api"],
)

app.include_router(
    ingredients_api.router,
    prefix="/api/ingredients",
    tags=["ingredients-api"],
)

app.include_router(
    bowls_ui.router,
    tags=["bowls-ui"],
)
