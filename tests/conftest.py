"""
Test fixtures for Recipe Explorer tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_storage
from app.services.storage import RecipeStorage


# Raw TheMealDB API response used by mealdb unit and mock tests
MOCK_MEALDB_MEAL = {
    "idMeal": "52772",
    "strMeal": "Teriyaki Chicken Casserole",
    "strCategory": "Chicken",
    "strArea": "Japanese",
    "strInstructions": (
        "Preheat oven to 350\u00b0 F.\r\n"
        "Spray a 9x13-inch baking pan with non-stick spray.\r\n"
        "Mix soy sauce, water and sugar together."
    ),
    "strIngredient1": "soy sauce",
    "strMeasure1": "3/4 cup",
    "strIngredient2": "water",
    "strMeasure2": "1/2 cup",
    "strIngredient3": "sugar",
    "strMeasure3": "1/4 cup",
    # remaining ingredient slots are empty
    **{f"strIngredient{i}": "" for i in range(4, 21)},
    **{f"strMeasure{i}": "" for i in range(4, 21)},
    "strTags": "Meat,Casserole",
    "strMealThumb": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg",
}


@pytest.fixture
def client():
    """Test client for making requests to the API"""
    return TestClient(app)


@pytest.fixture
def clean_storage():
    """Provide a fresh, empty RecipeStorage for the duration of the test.

    Uses FastAPI's dependency override system so every route that declares
    ``storage: RecipeStorage = Depends(get_storage)`` receives the isolated
    instance — no global state is touched.
    """
    fresh = RecipeStorage()
    app.dependency_overrides[get_storage] = lambda: fresh
    yield fresh
    app.dependency_overrides.pop(get_storage, None)


@pytest.fixture
def sample_recipe_data():
    """Sample recipe for testing"""
    return {
        "title": "Test Recipe",
        "description": "A test recipe",
        "ingredients": ["ingredient 1", "ingredient 2"],
        "instructions": ["First, do step 1.", "Then, do step 2."],
        "cuisine": "Italian",
        "tags": ["test"],
    }
