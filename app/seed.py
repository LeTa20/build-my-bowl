from sqlmodel import Session, select
from app.db import engine
from app.models import Ingredient

INGREDIENTS = [
    {
        "name": "Greek Yogurt",
        "calories": 140.0,
        "protein": 22.0,
        "fiber": 0.5,
        "sugar": 7.5,
        "icon_filename": None,
        "bowl_image_filename": None,
        "is_drizzle": False,
    },
    {
        "name": "Plain Yogurt",
        "calories": 140.0,
        "protein": 23.0,
        "fiber": 0.0,
        "sugar": 7.0,
        "icon_filename": None,
        "bowl_image_filename": None,
        "is_drizzle": False,
    },
    {
        "name": "Strawberry Yogurt",
        "calories": 160.0,
        "protein": 7.0,
        "fiber": 0.5,
        "sugar": 23.0,
        "icon_filename": None,
        "bowl_image_filename": None,
        "is_drizzle": False,
    },
    {
        "name": "Banana",
        "calories": 107.5,
        "protein": 1.3,
        "fiber": 3.0,
        "sugar": 14.5,
        "icon_filename": "banana_icon.PNG",
        "bowl_image_filename": "banana_slices.PNG",
        "is_drizzle": False,
    },
    {
        "name": "Blueberries",
        "calories": 87.5,
        "protein": 1.0,
        "fiber": 3.5,
        "sugar": 15.0,
        "icon_filename": "blueberry_icon.PNG",
        "bowl_image_filename": "blueberry_clump.PNG",
        "is_drizzle": False,
    },
    {
        "name": "Strawberry",
        "calories": 5.0,
        "protein": 0.1,
        "fiber": 1.0,
        "sugar": 0.7,
        "icon_filename": "strawberry_icon.png",
        "bowl_image_filename": "strawberry_slices.PNG",
        "is_drizzle": False,
    },
    {
        "name": "Honey",
        "calories": 64.0,
        "protein": 0.0,
        "fiber": 0.0,
        "sugar": 17.0,
        "icon_filename": "honey_bottle.PNG",
        "bowl_image_filename": "honey_drizzle.PNG",
        "is_drizzle": True,
    },
    {
        "name": "Nuts",
        "calories": 575.0,
        "protein": 17.5,
        "fiber": 7.0,
        "sugar": 5.0,
        "icon_filename": "nuts_icon.png",
        "bowl_image_filename": "nuts_slices.png",
        "is_drizzle": False,
    },
    {
        "name": "Peanut Butter",
        "calories": 95.0,
        "protein": 3.5,
        "fiber": 1.5,
        "sugar": 1.5,
        "icon_filename": "peanut_icon.png",
        "bowl_image_filename": "peanut_drizzle.png",
        "is_drizzle": True,
    },
]


def seed_ingredients():
    with Session(engine) as session:
        for ing_data in INGREDIENTS:
            existing = session.exec(
                select(Ingredient).where(Ingredient.name == ing_data["name"])
            ).first()
            if existing:
                # Update existing ingredient
                existing.calories = ing_data["calories"]
                existing.protein = ing_data["protein"]
                existing.fiber = ing_data["fiber"]
                existing.sugar = ing_data["sugar"]
                existing.icon_filename = ing_data.get("icon_filename")
                existing.bowl_image_filename = ing_data.get("bowl_image_filename")
                existing.is_drizzle = ing_data.get("is_drizzle", False)
                session.add(existing)
            else:
                ingredient = Ingredient(**ing_data)
                session.add(ingredient)
        session.commit()
        print("Ingredients seeded successfully!")


if __name__ == "__main__":
    seed_ingredients()

