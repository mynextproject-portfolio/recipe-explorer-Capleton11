import json
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.dependencies import get_mealdb, get_metrics, get_storage
from app.models import RecipeCreate, RecipeUpdate
from app.services.mealdb import MealDBService
from app.services.metrics import MetricsCollector, Timer
from app.services.prometheus_metrics import RECIPE_SEARCHES
from app.services.storage import RecipeStorage

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@router.get("/metrics")
def metrics_stats(metrics: MetricsCollector = Depends(get_metrics)):
    """Return accumulated performance stats for internal vs external sources."""
    return metrics.get_stats()


@router.post("/metrics/reset")
def reset_metrics(metrics: MetricsCollector = Depends(get_metrics)):
    """Reset all accumulated metrics (useful for testing)."""
    metrics.reset()
    return {"message": "Metrics reset"}


# ---------------------------------------------------------------------------
# Recipe list / search  (combined internal + external, with timing)
# ---------------------------------------------------------------------------


@router.get("/recipes")
async def get_recipes(
    search: Optional[str] = None,
    storage: RecipeStorage = Depends(get_storage),
    mealdb_svc: MealDBService = Depends(get_mealdb),
    metrics: MetricsCollector = Depends(get_metrics),
):
    """Get all recipes. When a search query is supplied, results from both
    internal storage and TheMealDB are returned together, with per-source
    timing included in the response meta."""
    with Timer("internal", metrics) as t_internal:
        internal = (
            storage.search_recipes(search) if search else storage.get_all_recipes()
        )

    external = []
    t_external_ms = 0.0
    if search:
        RECIPE_SEARCHES.labels(query=search.lower()).inc()
        with Timer("external", metrics) as t_ext:
            external = await mealdb_svc.search_meals(search)
        t_external_ms = t_ext.duration_ms

    return {
        "recipes": internal + external,
        "meta": {
            "internal": {
                "count": len(internal),
                "duration_ms": round(t_internal.duration_ms, 3),
            },
            "external": {
                "count": len(external),
                "duration_ms": round(t_external_ms, 3),
            },
            "total_duration_ms": round(t_internal.duration_ms + t_external_ms, 3),
        },
    }


@router.get("/recipes/search")
async def search_recipes(
    q: Optional[str] = None,
    storage: RecipeStorage = Depends(get_storage),
    mealdb_svc: MealDBService = Depends(get_mealdb),
    metrics: MetricsCollector = Depends(get_metrics),
):
    """Search recipes by keyword (?q=). Combines internal storage and TheMealDB.
    Timing data is included in the response meta."""
    with Timer("internal", metrics) as t_internal:
        internal = storage.search_recipes(q) if q else storage.get_all_recipes()

    external = []
    t_external_ms = 0.0
    if q:
        RECIPE_SEARCHES.labels(query=q.lower()).inc()
        with Timer("external", metrics) as t_ext:
            external = await mealdb_svc.search_meals(q)
        t_external_ms = t_ext.duration_ms

    return {
        "recipes": internal + external,
        "meta": {
            "internal": {
                "count": len(internal),
                "duration_ms": round(t_internal.duration_ms, 3),
            },
            "external": {
                "count": len(external),
                "duration_ms": round(t_external_ms, 3),
            },
            "total_duration_ms": round(t_internal.duration_ms + t_external_ms, 3),
        },
    }


# ---------------------------------------------------------------------------
# Export  — must be registered BEFORE /{recipe_id} to avoid shadowing
# ---------------------------------------------------------------------------


@router.get("/recipes/export")
def export_recipes(storage: RecipeStorage = Depends(get_storage)):
    """Export all internal recipes as JSON."""
    recipes = storage.get_all_recipes()
    return JSONResponse(content=[r.model_dump() for r in recipes])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post("/recipes", status_code=201)
def create_recipe(
    recipe: RecipeCreate,
    storage: RecipeStorage = Depends(get_storage),
):
    """Create a new internal recipe."""
    return storage.create_recipe(recipe)


# ---------------------------------------------------------------------------
# Dedicated internal / external endpoints
# ---------------------------------------------------------------------------


@router.get("/recipes/internal/{recipe_id}")
def get_internal_recipe(
    recipe_id: str,
    storage: RecipeStorage = Depends(get_storage),
):
    """Get a specific internal recipe by ID."""
    recipe = storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get("/recipes/external/{recipe_id}")
async def get_external_recipe(
    recipe_id: str,
    mealdb_svc: MealDBService = Depends(get_mealdb),
):
    """Get a specific recipe from TheMealDB by its numeric meal ID."""
    recipe = await mealdb_svc.get_meal_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="External recipe not found")
    return recipe


# ---------------------------------------------------------------------------
# Single internal recipe (generic, backward-compatible)
# ---------------------------------------------------------------------------


@router.get("/recipes/{recipe_id}")
def get_recipe(
    recipe_id: str,
    storage: RecipeStorage = Depends(get_storage),
):
    """Get a specific internal recipe by ID."""
    recipe = storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.put("/recipes/{recipe_id}")
def update_recipe(
    recipe_id: str,
    recipe: RecipeUpdate,
    storage: RecipeStorage = Depends(get_storage),
):
    """Update an existing internal recipe."""
    updated = storage.update_recipe(recipe_id, recipe)
    if not updated:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated


@router.delete("/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: str,
    storage: RecipeStorage = Depends(get_storage),
):
    """Delete an internal recipe."""
    if not storage.delete_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"}


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------


@router.post("/recipes/import")
async def import_recipes(
    file: UploadFile = File(...),
    storage: RecipeStorage = Depends(get_storage),
):
    """Import recipes from a JSON file (replaces all existing recipes)."""
    try:
        content = await file.read()

        if len(content) > 1_000_000:
            raise HTTPException(status_code=413, detail="File too large (max 1MB)")

        recipes_data = json.loads(content)

        if not isinstance(recipes_data, list):
            raise HTTPException(
                status_code=400, detail="JSON must be an array of recipes"
            )

        count = storage.import_recipes(recipes_data)
        return {"message": f"Successfully imported {count} recipes", "count": count}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
