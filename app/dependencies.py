"""
FastAPI dependency providers.

Use these with FastAPI's ``Depends()`` system to inject services into route
handlers::

    from fastapi import Depends
    from app.dependencies import get_storage, get_metrics, get_mealdb

    @router.get("/recipes")
    def list_recipes(storage: RecipeStorage = Depends(get_storage)):
        return storage.get_all_recipes()

Swapping a dependency for tests is done via ``app.dependency_overrides``::

    from app.main import app
    from app.dependencies import get_storage
    from app.services.storage import RecipeStorage

    app.dependency_overrides[get_storage] = lambda: RecipeStorage()
"""

from app.services.mealdb import MealDBService, _mealdb_service
from app.services.metrics import MetricsCollector, collector
from app.services.storage import RecipeStorage, recipe_storage


def get_storage() -> RecipeStorage:
    """Provide the shared recipe storage instance."""
    return recipe_storage


def get_metrics() -> MetricsCollector:
    """Provide the shared metrics collector instance."""
    return collector


def get_mealdb() -> MealDBService:
    """Provide the MealDB service instance."""
    return _mealdb_service
