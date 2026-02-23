"""
SQLite-backed recipe storage.

Drop-in replacement for the in-memory ``RecipeStorage``.  Provides the
identical public interface so it can be swapped in via the dependency
injection layer without touching any route handlers.

The database path is configurable at construction time.  In production the
default ``"recipes.db"`` file is created next to the working directory;
in Docker that resolves to ``/app/recipes.db``.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional

from app.models import Recipe, RecipeCreate, RecipeUpdate

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS recipes (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL,
    ingredients  TEXT NOT NULL,
    instructions TEXT NOT NULL,
    cuisine      TEXT NOT NULL,
    tags         TEXT NOT NULL DEFAULT '[]',
    source       TEXT NOT NULL DEFAULT 'internal',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
)
"""


class SQLiteRecipeStorage:
    """Persistent recipe storage backed by a SQLite database.

    Public methods mirror ``RecipeStorage`` exactly so callers never need
    to know which implementation is in use.
    """

    def __init__(self, db_path: str = "recipes.db") -> None:
        self.db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def _row_to_recipe(self, row: sqlite3.Row) -> Recipe:
        return Recipe(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            ingredients=json.loads(row["ingredients"]),
            instructions=json.loads(row["instructions"]),
            cuisine=row["cuisine"],
            tags=json.loads(row["tags"]),
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ------------------------------------------------------------------
    # Public interface (mirrors RecipeStorage)
    # ------------------------------------------------------------------

    def get_all_recipes(self) -> List[Recipe]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM recipes ORDER BY created_at").fetchall()
        return [self._row_to_recipe(r) for r in rows]

    def get_recipe(self, recipe_id: str) -> Optional[Recipe]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM recipes WHERE id = ?", (recipe_id,)
            ).fetchone()
        return self._row_to_recipe(row) if row else None

    def search_recipes(self, query: str) -> List[Recipe]:
        if not query:
            return self.get_all_recipes()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM recipes WHERE LOWER(title) LIKE ? ORDER BY created_at",
                (f"%{query.lower()}%",),
            ).fetchall()
        return [self._row_to_recipe(r) for r in rows]

    def create_recipe(self, recipe_data: RecipeCreate) -> Recipe:
        recipe = Recipe(**recipe_data.model_dump())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO recipes
                    (id, title, description, ingredients, instructions,
                     cuisine, tags, source, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recipe.id,
                    recipe.title,
                    recipe.description,
                    json.dumps(recipe.ingredients),
                    json.dumps(recipe.instructions),
                    recipe.cuisine,
                    json.dumps(recipe.tags),
                    recipe.source,
                    recipe.created_at.isoformat(),
                    recipe.updated_at.isoformat(),
                ),
            )
        return recipe

    def update_recipe(
        self, recipe_id: str, recipe_data: RecipeUpdate
    ) -> Optional[Recipe]:
        recipe = self.get_recipe(recipe_id)
        if recipe is None:
            return None

        for key, value in recipe_data.model_dump().items():
            setattr(recipe, key, value)
        recipe.updated_at = datetime.now()

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE recipes SET
                    title = ?, description = ?, ingredients = ?,
                    instructions = ?, cuisine = ?, tags = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    recipe.title,
                    recipe.description,
                    json.dumps(recipe.ingredients),
                    json.dumps(recipe.instructions),
                    recipe.cuisine,
                    json.dumps(recipe.tags),
                    recipe.updated_at.isoformat(),
                    recipe_id,
                ),
            )
        return recipe

    def delete_recipe(self, recipe_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        return cursor.rowcount > 0

    def import_recipes(self, recipes_data: List[dict]) -> int:
        """Replace all recipes with the provided list (used for bulk import)."""
        count = 0
        with self._connect() as conn:
            conn.execute("DELETE FROM recipes")
            for recipe_dict in recipes_data:
                try:
                    if "created_at" in recipe_dict and isinstance(
                        recipe_dict["created_at"], str
                    ):
                        recipe_dict["created_at"] = datetime.fromisoformat(
                            recipe_dict["created_at"]
                        )
                    if "updated_at" in recipe_dict and isinstance(
                        recipe_dict["updated_at"], str
                    ):
                        recipe_dict["updated_at"] = datetime.fromisoformat(
                            recipe_dict["updated_at"]
                        )
                    recipe = Recipe(**recipe_dict)
                    conn.execute(
                        """
                        INSERT INTO recipes
                            (id, title, description, ingredients, instructions,
                             cuisine, tags, source, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            recipe.id,
                            recipe.title,
                            recipe.description,
                            json.dumps(recipe.ingredients),
                            json.dumps(recipe.instructions),
                            recipe.cuisine,
                            json.dumps(recipe.tags),
                            recipe.source,
                            recipe.created_at.isoformat(),
                            recipe.updated_at.isoformat(),
                        ),
                    )
                    count += 1
                except Exception:
                    continue
        return count
