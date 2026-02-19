from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
from app.models import Recipe, RecipeCreate, RecipeUpdate
from app.services.storage import recipe_storage

router = APIRouter(prefix="/api")


@router.get("/recipes")
def get_recipes(search: Optional[str] = None):
    """Get all recipes or search by title"""
    if search:
        recipes = recipe_storage.search_recipes(search)
    else:
        recipes = recipe_storage.get_all_recipes()
    return {"recipes": recipes}


@router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str):
    """Get a specific recipe by ID"""
    recipe = recipe_storage.get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("/recipes", status_code=201)
def create_recipe(recipe: RecipeCreate):
    """Create a new recipe"""
    new_recipe = recipe_storage.create_recipe(recipe)
    return new_recipe


@router.put("/recipes/{recipe_id}")
def update_recipe(recipe_id: str, recipe: RecipeUpdate):
    """Update an existing recipe"""
    updated_recipe = recipe_storage.update_recipe(recipe_id, recipe)
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return updated_recipe


@router.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: str):
    """Delete a recipe"""
    success = recipe_storage.delete_recipe(recipe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"}


@router.post("/recipes/import")
async def import_recipes(file: UploadFile = File(...)):
    """Import recipes from JSON file"""
    try:
        content = await file.read()

        if len(content) > 1_000_000:
            raise HTTPException(status_code=413, detail="File too large (max 1MB)")

        recipes_data = json.loads(content)

        if not isinstance(recipes_data, list):
            raise HTTPException(status_code=400, detail="JSON must be an array of recipes")

        count = recipe_storage.import_recipes(recipes_data)
        return {"message": f"Successfully imported {count} recipes", "count": count}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/recipes/export")
def export_recipes():
    """Export all recipes as JSON"""
    recipes = recipe_storage.get_all_recipes()
    recipes_dict = [recipe.model_dump() for recipe in recipes]
    return JSONResponse(content=recipes_dict)
