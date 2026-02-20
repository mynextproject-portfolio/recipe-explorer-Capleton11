from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional
import json

from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage
from app.services import mealdb

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Recipe list / search  (combined internal + external)
# ---------------------------------------------------------------------------

@router.get("/recipes")
async def get_recipes(search: Optional[str] = None):
    """Get all recipes. When a search query is supplied, results from both
    internal storage and TheMealDB are returned together."""
    internal = (
        recipe_storage.search_recipes(search)
        if search
        else recipe_storage.get_all_recipes()
    )

    external = await mealdb.search_meals(search) if search else []

    return {"recipes": internal + external}


# ---------------------------------------------------------------------------
# Export  — must be registered BEFORE /{recipe_id} to avoid shadowing
# ---------------------------------------------------------------------------

@router.get("/recipes/export")
def export_recipes():
    """Export all internal recipes as JSON."""
    recipes = recipe_storage.get_all_recipes()
    return JSONResponse(content=[r.model_dump() for r in recipes])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("/recipes", status_code=201)
def create_recipe(recipe: RecipeCreate):
    """Create a new internal recipe."""
    return recipe_storage.create_recipe(recipe)


# ---------------------------------------------------------------------------
# Dedicated internal / external endpoints (acceptance criteria)
# ---------------------------------------------------------------------------

@router.get("/recipes/internal/{recipe_id}")
def get_internal_recipe(recipe_id: str):
    """Get a specific internal recipe by ID."""
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get("/recipes/external/{recipe_id}")
async def get_external_recipe(recipe_id: str):
    """Get a specific recipe from TheMealDB by its numeric meal ID."""
    recipe = await mealdb.get_meal_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="External recipe not found")
    return recipe


# ---------------------------------------------------------------------------
# Single internal recipe (generic, backward-compatible)
# ---------------------------------------------------------------------------

@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get a specific internal recipe by ID."""
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe: RecipeUpdate):
    """Update an existing internal recipe."""
    updated = recipe_storage.update_recipe(recipe_id, recipe)
    if not updated:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated


@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str):
    """Delete an internal recipe."""
    if not recipe_storage.delete_recipe(recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"}


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@router.post("/recipes/import")
async def import_recipes(file: UploadFile = File(...)):
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

        count = recipe_storage.import_recipes(recipes_data)
        return {"message": f"Successfully imported {count} recipes", "count": count}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
