from typing import Generator

from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import Session, relationship, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./recipes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class IngredientDB(Base):  # type: ignore
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)


class RecipeIngredientDB(Base):  # type: ignore
    __tablename__ = "recipe_ingredients"
    recipe_id = Column(Integer, ForeignKey("recipes.id"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), primary_key=True)
    order = Column(Integer)

    recipe = relationship("RecipeDB", back_populates="ingredients_association")
    ingredient = relationship("IngredientDB")


class RecipeDB(Base):  # type: ignore
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    cooking_time = Column(Integer, nullable=False)
    views = Column(Integer, default=0)

    ingredients_association = relationship(
        "RecipeIngredientDB",
        order_by="RecipeIngredientDB.order",
        collection_class=ordering_list("order"),
        back_populates="recipe",
    )


Base.metadata.create_all(bind=engine)
