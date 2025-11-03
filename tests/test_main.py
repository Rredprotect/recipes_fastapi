from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from main import app
from models.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    Base.metadata.drop_all(bind=engine)


def test_read_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Recipe API is running"}


def test_create_recipe() -> None:
    recipe_data = {
        "title": "Test Recipe",
        "description": "Test Description",
        "cooking_time": 30,
        "ingredients": [{"name": "Tomato"}, {"name": "Cheese"}],
    }
    response = client.post("/recipes/", json=recipe_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Recipe"
    assert data["description"] == "Test Description"
    assert data["cooking_time"] == 30
    assert len(data["ingredients"]) == 2


def test_get_recipe() -> None:
    # Сначала создаем рецепт
    recipe_data = {
        "title": "Test Recipe Get",
        "description": "Test Description",
        "cooking_time": 25,
        "ingredients": [{"name": "Egg"}],
    }
    create_response = client.post("/recipes/", json=recipe_data)
    recipe_id = create_response.json()["id"]

    # Получаем рецепт
    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Recipe Get"
    assert data["views"] == 1  # При просмотре увеличивается счетчик


def test_get_nonexistent_recipe() -> None:
    response = client.get("/recipes/99999")
    assert response.status_code == 404


def test_get_recipes() -> None:
    response = client.get("/recipes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_recipes_by_title() -> None:
    # Создаем рецепт для поиска
    recipe_data = {
        "title": "Pizza Margherita",
        "description": "Classic Italian pizza",
        "cooking_time": 45,
        "ingredients": [{"name": "Flour"}, {"name": "Tomato"}],
    }
    client.post("/recipes/", json=recipe_data)

    response = client.get("/recipes/search/by-title?title=Pizza")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "Pizza" in data[0]["title"]


def test_search_recipes_by_ingredients() -> None:
    # Создаем рецепт с ингредиентами
    recipe_data = {
        "title": "Pasta",
        "description": "Italian pasta",
        "cooking_time": 20,
        "ingredients": [{"name": "Pasta"}, {"name": "Tomato"}],
    }
    client.post("/recipes/", json=recipe_data)

    response = client.get(
        "/recipes/search/by-ingredients?ingredients=Pasta&ingredients=Tomato"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_recipe_invalid_data() -> None:
    invalid_data = {
        "title": "",  # Пустой заголовок
        "cooking_time": -5,  # Отрицательное время
        "ingredients": [],
    }
    response = client.post("/recipes/", json=invalid_data)
    assert response.status_code == 422


def test_create_recipe_too_long_title() -> None:
    invalid_data = {
        "title": "a" * 101,  # Слишком длинный заголовок
        "cooking_time": 30,
        "ingredients": [{"name": "Test"}],
    }
    response = client.post("/recipes/", json=invalid_data)
    assert response.status_code == 422


def test_create_recipe_too_many_ingredients() -> None:
    invalid_data = {
        "title": "Test Recipe",
        "cooking_time": 30,
        "ingredients": [
            {"name": f"Ingredient {i}"} for i in range(21)
        ],  # Слишком много ингредиентов
    }
    response = client.post("/recipes/", json=invalid_data)
    assert response.status_code == 422
