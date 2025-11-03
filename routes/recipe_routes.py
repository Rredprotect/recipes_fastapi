from typing import List

try:
    from typing import Annotated  # Python 3.9+
except ImportError:
    from typing_extensions import Annotated  # Python < 3.9

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    IngredientDB,
    Recipe,
    RecipeCreate,
    RecipeDB,
    RecipeIngredient,
    RecipeIngredientDB,
    RecipeSearch,
    get_db,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.post("/", response_model=Recipe, status_code=201)
async def create_recipe(
    recipe: RecipeCreate, db: Annotated[Session, Depends(get_db)]
) -> Recipe:
    db_recipe = RecipeDB(
        title=recipe.title,
        description=recipe.description,
        cooking_time=recipe.cooking_time,
    )
    db.add(db_recipe)
    db.flush()

    ingredients_map = {}
    for ingredient in recipe.ingredients:
        if ingredient.name not in ingredients_map:
            db_ingredient = (
                db.query(IngredientDB).filter_by(name=ingredient.name).first()
            )
            if not db_ingredient:
                db_ingredient = IngredientDB(name=ingredient.name)
                db.add(db_ingredient)
                db.flush()
            ingredients_map[ingredient.name] = db_ingredient

    for order, ingredient in enumerate(recipe.ingredients):
        db_recipe_ingredient = RecipeIngredientDB(
            recipe_id=db_recipe.id,
            ingredient_id=ingredients_map[ingredient.name].id,
            order=order,
        )
        db.add(db_recipe_ingredient)

    db.commit()
    db.refresh(db_recipe)

    return Recipe(
        id=int(db_recipe.id),
        title=str(db_recipe.title),
        description=str(db_recipe.description) if db_recipe.description else None,
        cooking_time=int(db_recipe.cooking_time),
        views=int(db_recipe.views),
        ingredients=[
            RecipeIngredient(name=str(ri.ingredient.name))
            for ri in sorted(
                db_recipe.ingredients_association,
                key=lambda x: x.order if x.order is not None else 0,
            )
        ],
    )


@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)) -> Recipe:
    db_recipe = db.query(RecipeDB).filter_by(id=recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    db_recipe.views = db_recipe.views + 1
    db.commit()

    return Recipe(
        id=int(db_recipe.id),
        title=str(db_recipe.title),
        description=str(db_recipe.description) if db_recipe.description else None,
        cooking_time=int(db_recipe.cooking_time),
        views=int(db_recipe.views),
        ingredients=[
            RecipeIngredient(name=str(ri.ingredient.name))
            for ri in sorted(
                db_recipe.ingredients_association,
                key=lambda x: x.order if x.order is not None else 0,
            )
        ],
    )


@router.get("/", response_model=List[RecipeSearch])
async def get_recipes(db: Session = Depends(get_db)) -> List[RecipeSearch]:
    recipes = db.query(RecipeDB).order_by(RecipeDB.views.desc()).limit(10).all()
    return [
        RecipeSearch(
            id=int(recipe.id),
            title=str(recipe.title),
            views=int(recipe.views),
            cooking_time=int(recipe.cooking_time),
        )
        for recipe in recipes
    ]


@router.get("/search/by-title", response_model=List[RecipeSearch])
async def search_recipes_by_title(
    title: str = Query(min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> List[RecipeSearch]:
    recipes = (
        db.query(RecipeDB)
        .filter(RecipeDB.title.contains(title))
        .order_by(RecipeDB.views.desc())
        .all()
    )

    return [
        RecipeSearch(
            id=int(recipe.id),
            title=str(recipe.title),
            views=int(recipe.views),
            cooking_time=int(recipe.cooking_time),
        )
        for recipe in recipes
    ]


@router.get("/search/by-ingredients", response_model=List[RecipeSearch])
async def search_recipes_by_ingredients(
    ingredients: List[str] = Query(min_length=1),
    db: Session = Depends(get_db),
) -> List[RecipeSearch]:
    recipes = (
        db.query(RecipeDB)
        .join(RecipeIngredientDB)
        .join(IngredientDB)
        .filter(IngredientDB.name.in_(ingredients))
        .group_by(RecipeDB.id)
        .having(func.count(IngredientDB.id) == len(set(ingredients)))
        .order_by(RecipeDB.views.desc())
        .all()
    )

    return [
        RecipeSearch(
            id=int(recipe.id),
            title=str(recipe.title),
            views=int(recipe.views),
            cooking_time=int(recipe.cooking_time),
        )
        for recipe in recipes
    ]
