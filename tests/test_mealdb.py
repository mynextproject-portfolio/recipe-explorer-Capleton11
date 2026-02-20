"""
Tests for TheMealDB integration.

Sections:
  1. Unit tests  – _transform_meal (no network)
  2. Mock tests  – API endpoints with mocked search_meals / get_meal_by_id
  3. Integration – one real HTTP call to verify the live API adapter works
"""

from unittest.mock import AsyncMock, patch

from tests.conftest import MOCK_MEALDB_MEAL
from app.services.mealdb import _transform_meal
from app.models import Recipe


# ---------------------------------------------------------------------------
# 1. Unit tests: data transformation
# ---------------------------------------------------------------------------


def test_transform_meal_source_is_external():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert recipe.source == "external"


def test_transform_meal_id_prefixed_with_mealdb():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert recipe.id == "mealdb-52772"


def test_transform_meal_title():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert recipe.title == "Teriyaki Chicken Casserole"


def test_transform_meal_cuisine_from_area():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert recipe.cuisine == "Japanese"


def test_transform_meal_combines_measure_and_ingredient():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert "3/4 cup soy sauce" in recipe.ingredients
    assert "1/2 cup water" in recipe.ingredients
    assert "1/4 cup sugar" in recipe.ingredients


def test_transform_meal_skips_empty_ingredients():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    # MOCK_MEALDB_MEAL has exactly 3 non-empty ingredients
    assert len(recipe.ingredients) == 3


def test_transform_meal_splits_instructions_into_steps():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert isinstance(recipe.instructions, list)
    assert len(recipe.instructions) >= 1
    assert all(isinstance(s, str) and s for s in recipe.instructions)


def test_transform_meal_parses_tags():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert "Meat" in recipe.tags
    assert "Casserole" in recipe.tags


def test_transform_meal_empty_ingredients_fallback():
    """When all ingredient slots are empty a fallback string is used."""
    sparse = {
        **MOCK_MEALDB_MEAL,
        **{f"strIngredient{i}": "" for i in range(1, 21)},
    }
    recipe = _transform_meal(sparse)
    assert len(recipe.ingredients) == 1
    assert "original recipe" in recipe.ingredients[0].lower()


def test_transform_meal_empty_instructions_fallback():
    """When instructions are blank a fallback string is used."""
    sparse = {**MOCK_MEALDB_MEAL, "strInstructions": ""}
    recipe = _transform_meal(sparse)
    assert len(recipe.instructions) == 1
    assert "original recipe" in recipe.instructions[0].lower()


def test_transform_meal_missing_area_defaults_to_international():
    no_area = {**MOCK_MEALDB_MEAL, "strArea": ""}
    recipe = _transform_meal(no_area)
    assert recipe.cuisine == "International"


def test_transform_result_is_valid_recipe_instance():
    recipe = _transform_meal(MOCK_MEALDB_MEAL)
    assert isinstance(recipe, Recipe)


# ---------------------------------------------------------------------------
# 2. Mock tests: API endpoints
# ---------------------------------------------------------------------------


def _make_external_recipe() -> Recipe:
    return _transform_meal(MOCK_MEALDB_MEAL)


def test_search_with_query_returns_both_sources(
    client, clean_storage, sample_recipe_data
):
    """GET /api/recipes?search=... should merge internal + external results."""
    client.post("/api/recipes", json=sample_recipe_data)

    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[_make_external_recipe()],
    ):
        response = client.get("/api/recipes?search=test")

    assert response.status_code == 200
    recipes = response.json()["recipes"]
    sources = {r["source"] for r in recipes}
    assert "internal" in sources
    assert "external" in sources


def test_search_without_query_does_not_call_external_api(client, clean_storage):
    """GET /api/recipes (no query) must NOT call TheMealDB."""
    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
    ) as mock_search:
        response = client.get("/api/recipes")

    assert response.status_code == 200
    mock_search.assert_not_called()


def test_search_all_recipes_have_source_field(
    client, clean_storage, sample_recipe_data
):
    """Every recipe in a search response must carry a source field."""
    client.post("/api/recipes", json=sample_recipe_data)

    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[_make_external_recipe()],
    ):
        response = client.get("/api/recipes?search=test")

    recipes = response.json()["recipes"]
    assert all("source" in r for r in recipes)


def test_internal_recipes_have_source_internal(
    client, clean_storage, sample_recipe_data
):
    """Internal recipes must have source == 'internal'."""
    client.post("/api/recipes", json=sample_recipe_data)
    response = client.get("/api/recipes")
    recipes = response.json()["recipes"]
    assert all(r["source"] == "internal" for r in recipes)


def test_external_api_failure_still_returns_internal(
    client, clean_storage, sample_recipe_data
):
    """When TheMealDB is down the endpoint should still return internal recipes."""
    client.post("/api/recipes", json=sample_recipe_data)

    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[],  # simulate graceful failure
    ):
        response = client.get("/api/recipes?search=test")

    assert response.status_code == 200
    recipes = response.json()["recipes"]
    assert len(recipes) >= 1
    assert all(r["source"] == "internal" for r in recipes)


def test_get_internal_recipe_endpoint(client, clean_storage, sample_recipe_data):
    """GET /api/recipes/internal/{id} returns the correct internal recipe."""
    create = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create.json()["id"]

    response = client.get(f"/api/recipes/internal/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id
    assert response.json()["source"] == "internal"


def test_get_internal_recipe_not_found(client, clean_storage):
    """GET /api/recipes/internal/{id} returns 404 for unknown IDs."""
    response = client.get("/api/recipes/internal/does-not-exist")
    assert response.status_code == 404


def test_get_external_recipe_endpoint(client):
    """GET /api/recipes/external/{id} returns a transformed external recipe."""
    with patch(
        "app.services.mealdb.get_meal_by_id",
        new_callable=AsyncMock,
        return_value=_make_external_recipe(),
    ):
        response = client.get("/api/recipes/external/52772")

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "external"
    assert data["id"] == "mealdb-52772"
    assert data["title"] == "Teriyaki Chicken Casserole"
    assert data["cuisine"] == "Japanese"


def test_get_external_recipe_not_found(client):
    """GET /api/recipes/external/{id} returns 404 when meal not found."""
    with patch(
        "app.services.mealdb.get_meal_by_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = client.get("/api/recipes/external/99999")

    assert response.status_code == 404


def test_external_recipe_has_all_required_fields(client):
    """External recipe response matches our schema (all fields present)."""
    with patch(
        "app.services.mealdb.get_meal_by_id",
        new_callable=AsyncMock,
        return_value=_make_external_recipe(),
    ):
        response = client.get("/api/recipes/external/52772")

    data = response.json()
    for field in (
        "id",
        "title",
        "description",
        "ingredients",
        "instructions",
        "cuisine",
        "tags",
        "source",
    ):
        assert field in data, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# 3. Integration test — hits the real TheMealDB API
# ---------------------------------------------------------------------------


def test_mealdb_real_api_search(client, clean_storage):
    """Integration: real network call to TheMealDB through /api/recipes search.

    Requires internet access.  Verifies end-to-end: HTTP → transform → schema.
    """
    response = client.get("/api/recipes?search=chicken")
    assert response.status_code == 200

    data = response.json()
    assert "recipes" in data

    external = [r for r in data["recipes"] if r.get("source") == "external"]
    assert len(external) > 0, "Expected at least one external result for 'chicken'"

    # Verify the external result matches our schema
    sample = external[0]
    assert sample["id"].startswith("mealdb-")
    assert sample["title"]
    assert isinstance(sample["ingredients"], list)
    assert len(sample["ingredients"]) > 0
    assert isinstance(sample["instructions"], list)
    assert len(sample["instructions"]) > 0
    assert sample["cuisine"]
    assert sample["source"] == "external"
