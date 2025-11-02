from typing import List

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.ext.orderinglist import ordering_list

SQLALCHEMY_DATABASE_URL = "sqlite:///./recipes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class IngredientDB(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class RecipeIngredientDB(Base):
    __tablename__ = "recipe_ingredients"
    recipe_id = Column(Integer, ForeignKey('recipes.id'), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), primary_key=True)
    order = Column(Integer)

    recipe = relationship("RecipeDB", back_populates="ingredients_association")
    ingredient = relationship("IngredientDB")


class RecipeDB(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    cooking_time = Column(Integer, nullable=False)
    views = Column(Integer, default=0)

    ingredients_association = relationship(
        "RecipeIngredientDB",
        order_by="RecipeIngredientDB.order",
        collection_class=ordering_list('order'),
        back_populates="recipe"
    )


Base.metadata.create_all(bind=engine)


class IngredientResponse(BaseModel):
    name: str
    order: int

    class Config:
        orm_mode = True


class RecipeBase(BaseModel):
    title: str
    cooking_time: int

    class Config:
        orm_mode = True


class RecipeCreate(RecipeBase):
    description: str
    ingredients: List[IngredientResponse]


class RecipeResponse(RecipeBase):
    id: int
    views: int
    description: str
    ingredients: List[IngredientResponse]

    class Config:
        orm_mode = True


app = FastAPI(
    title="CookBook API",
    description="API для управления рецептами кулинарной книги",
    version="1.0.0",
    openapi_tags=[{
        'name': 'Рецепты',
        'description': 'Операции с рецептами'
    }]
)


@app.get(
    "/recipes",
    response_model=List[RecipeBase],
    tags=["Рецепты"],
    summary="Получить список рецептов",
    description="Возвращает отсортированный список рецептов по популярности и времени приготовления"
)
def get_recipes():
    with SessionLocal() as session:
        recipes = session.query(RecipeDB).order_by(
            RecipeDB.views.desc(),
            RecipeDB.cooking_time.asc()
        ).all()
        return recipes


@app.get(
    "/recipes/{recipe_id}",
    response_model=RecipeResponse,
    tags=["Рецепты"],
    summary="Получить детали рецепта",
    responses={404: {"description": "Рецепт не найден"}}
)
def get_recipe_details(recipe_id: int):
    with SessionLocal() as session:
        recipe = session.query(RecipeDB).filter(RecipeDB.id == recipe_id).first()
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рецепт не найден"
            )

        recipe.views += 1
        session.commit()
        session.refresh(recipe)

        ingredients = [
            IngredientResponse(
                name=assoc.ingredient.name,
                order=assoc.order
            ) for assoc in recipe.ingredients_association
        ]

        return RecipeResponse(
            id=recipe.id,
            title=recipe.title,
            cooking_time=recipe.cooking_time,
            views=recipe.views,
            description=recipe.description,
            ingredients=ingredients
        )


@app.post(
    "/recipes",
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Рецепты"],
    summary="Создать новый рецепт",
    responses={400: {"description": "Некорректные данные"}}
)
def create_recipe(recipe_data: RecipeCreate):
    with SessionLocal() as session:
        try:
            ingredients_association = []
            for ing in recipe_data.ingredients:
                db_ing = session.query(IngredientDB).filter_by(name=ing.name).first()
                if not db_ing:
                    db_ing = IngredientDB(name=ing.name)
                    session.add(db_ing)
                    session.flush()

                ingredients_association.append(
                    RecipeIngredientDB(
                        ingredient=db_ing,
                        order=ing.order
                    )
                )

            new_recipe = RecipeDB(
                title=recipe_data.title,
                description=recipe_data.description,
                cooking_time=recipe_data.cooking_time,
                ingredients_association=ingredients_association
            )

            session.add(new_recipe)
            session.commit()
            session.refresh(new_recipe)

            ingredients_response = [
                IngredientResponse(
                    name=assoc.ingredient.name,
                    order=assoc.order
                ) for assoc in new_recipe.ingredients_association
            ]

            return RecipeResponse(
                id=new_recipe.id,
                title=new_recipe.title,
                cooking_time=new_recipe.cooking_time,
                views=new_recipe.views,
                description=new_recipe.description,
                ingredients=ingredients_response
            )

        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)