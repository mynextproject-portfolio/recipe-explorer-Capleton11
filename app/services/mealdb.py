"""
TheMealDB API adapter with Redis caching.

Fetches meals from https://www.themealdb.com/api/json/v1/1 and transforms
them into the internal Recipe schema.  All public functions return empty
results (not exceptions) when the external API is unavailable.

Search results are cached in Redis for 24 hours to reduce latency on
repeated queries.  Cache misses fall back to the live API transparently.
"""

import httpx
from typing import List, Optional

from app.models import Recipe
from app.services import cache

MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
_TIMEOUT = 5.0  # seconds


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def search_meals(query: str) -> List[Recipe]:
    """Search TheMealDB by name.

    Checks Redis first (key ``mealdb:search:<query_lowercase>``).  On a
    cache hit the deserialised recipes are returned immediately without
    any HTTP call.  On a miss the live API is queried and the results are
    stored in Redis before returning.

    Returns [] on any network / parse error.
    """
    cache_key = f"mealdb:search:{query.lower()}"

    # --- Cache hit -----------------------------------------------------------
    cached = await cache.get(cache_key)
    if cached is not None:
        return [Recipe(**r) for r in cached]

    # --- Cache miss: fetch from the live API ---------------------------------
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{MEALDB_BASE_URL}/search.php",
                params={"s": query},
            )
            response.raise_for_status()
            meals = response.json().get("meals") or []
            results = [_transform_meal(m) for m in meals]
    except Exception:
        return []

    # Store in cache (failures are silenced inside cache.set)
    await cache.set(cache_key, [r.model_dump(mode="json") for r in results])

    return results


async def get_meal_by_id(meal_id: str) -> Optional[Recipe]:
    """Fetch a single meal from TheMealDB by its numeric ID.

    Checks Redis first (key ``mealdb:meal:<meal_id>``).  Returns None on
    any network / parse error or when the meal is not found.
    """
    cache_key = f"mealdb:meal:{meal_id}"

    # --- Cache hit -----------------------------------------------------------
    cached = await cache.get(cache_key)
    if cached is not None:
        return Recipe(**cached)

    # --- Cache miss: fetch from the live API ---------------------------------
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{MEALDB_BASE_URL}/lookup.php",
                params={"i": meal_id},
            )
            response.raise_for_status()
            meals = response.json().get("meals") or []
            if not meals:
                return None
            result = _transform_meal(meals[0])
    except Exception:
        return None

    await cache.set(cache_key, result.model_dump(mode="json"))

    return result


# ---------------------------------------------------------------------------
# Data transformation
# ---------------------------------------------------------------------------


def _transform_meal(meal: dict) -> Recipe:
    """Convert a raw TheMealDB meal dict into our Recipe schema.

    TheMealDB stores ingredients in 20 parallel strIngredient/strMeasure
    fields and instructions as a single text block.  This function
    normalises both into the List[str] format our schema expects.
    """
    # --- Ingredients ---------------------------------------------------------
    ingredients: List[str] = []
    for i in range(1, 21):
        ingredient = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if ingredient:
            combined = f"{measure} {ingredient}".strip() if measure else ingredient
            ingredients.append(combined)
    if not ingredients:
        ingredients = ["See original recipe for ingredients"]

    # --- Instructions --------------------------------------------------------
    raw = (meal.get("strInstructions") or "").strip()
    # TheMealDB uses \r\n line endings; fall back to \n
    steps = [s.strip() for s in raw.replace("\r\n", "\n").split("\n") if s.strip()]
    if not steps:
        steps = ["See original recipe for instructions"]

    # --- Tags ----------------------------------------------------------------
    raw_tags = (meal.get("strTags") or "").strip()
    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

    # --- Cuisine / description -----------------------------------------------
    cuisine = (meal.get("strArea") or "").strip() or "International"
    category = (meal.get("strCategory") or "").strip()

    if category:
        description = f"{category} dish"
    else:
        description = "A delicious dish"
    if cuisine != "International":
        description += f" from {cuisine}"
    description += "."

    # --- Title ---------------------------------------------------------------
    title = (meal.get("strMeal") or "").strip() or "Unknown Recipe"

    return Recipe(
        id=f"mealdb-{meal['idMeal']}",
        title=title,
        description=description,
        ingredients=ingredients,
        instructions=steps,
        cuisine=cuisine,
        tags=tags,
        source="external",
    )
