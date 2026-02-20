"""
Smoke and contract tests for Recipe Explorer API.
"""


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_health_check(client):
    """Smoke test: API is running and responding"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_home_page_loads(client):
    """Smoke test: Home page renders without error"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Recipe Explorer" in response.text


# ---------------------------------------------------------------------------
# GET /api/recipes
# ---------------------------------------------------------------------------


def test_get_all_recipes(client, clean_storage):
    """Contract test: GET /api/recipes returns correct structure"""
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert isinstance(data["recipes"], list)


# ---------------------------------------------------------------------------
# POST /api/recipes — success path
# ---------------------------------------------------------------------------


def test_create_recipe_returns_201(client, clean_storage, sample_recipe_data):
    """Contract test: creating a recipe returns 201 Created"""
    response = client.post("/api/recipes", json=sample_recipe_data)
    assert response.status_code == 201


def test_create_recipe_response_shape(client, clean_storage, sample_recipe_data):
    """Contract test: created recipe response contains expected fields"""
    response = client.post("/api/recipes", json=sample_recipe_data)
    assert response.status_code == 201
    recipe = response.json()
    assert "id" in recipe
    assert "title" in recipe
    assert "created_at" in recipe
    assert "updated_at" in recipe
    assert recipe["title"] == sample_recipe_data["title"]
    assert recipe["cuisine"] == sample_recipe_data["cuisine"]
    assert recipe["instructions"] == sample_recipe_data["instructions"]


# ---------------------------------------------------------------------------
# POST /api/recipes — validation errors (expect 422)
# ---------------------------------------------------------------------------


def test_create_recipe_missing_title(client, clean_storage, sample_recipe_data):
    """Validation: missing title field returns 422"""
    data = {k: v for k, v in sample_recipe_data.items() if k != "title"}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_empty_title(client, clean_storage, sample_recipe_data):
    """Validation: blank title returns 422"""
    data = {**sample_recipe_data, "title": "   "}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_title_too_long(client, clean_storage, sample_recipe_data):
    """Validation: title over 200 chars returns 422"""
    data = {**sample_recipe_data, "title": "x" * 201}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_empty_ingredients_list(
    client, clean_storage, sample_recipe_data
):
    """Validation: empty ingredients list returns 422"""
    data = {**sample_recipe_data, "ingredients": []}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_too_many_ingredients(client, clean_storage, sample_recipe_data):
    """Validation: more than 50 ingredients returns 422"""
    data = {**sample_recipe_data, "ingredients": [f"ingredient {i}" for i in range(51)]}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_empty_instructions_list(
    client, clean_storage, sample_recipe_data
):
    """Validation: empty instructions list returns 422"""
    data = {**sample_recipe_data, "instructions": []}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_empty_cuisine(client, clean_storage, sample_recipe_data):
    """Validation: blank cuisine returns 422"""
    data = {**sample_recipe_data, "cuisine": "   "}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


def test_create_recipe_missing_cuisine(client, clean_storage, sample_recipe_data):
    """Validation: missing cuisine field returns 422"""
    data = {k: v for k, v in sample_recipe_data.items() if k != "cuisine"}
    response = client.post("/api/recipes", json=data)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/recipes/{id}
# ---------------------------------------------------------------------------


def test_get_recipe_success(client, clean_storage, sample_recipe_data):
    """Contract test: fetching an existing recipe returns 200"""
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create_response.json()["id"]

    response = client.get(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["id"] == recipe_id


def test_get_recipe_not_found(client, clean_storage):
    """Contract test: fetching a non-existent recipe returns 404"""
    response = client.get("/api/recipes/non-existent-id")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/recipes/{id}
# ---------------------------------------------------------------------------


def test_update_recipe_success(client, clean_storage, sample_recipe_data):
    """Contract test: updating an existing recipe returns 200 with new data"""
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create_response.json()["id"]

    updated = {**sample_recipe_data, "title": "Updated Title", "cuisine": "French"}
    response = client.put(f"/api/recipes/{recipe_id}", json=updated)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["cuisine"] == "French"


def test_update_recipe_not_found(client, clean_storage, sample_recipe_data):
    """Contract test: updating a non-existent recipe returns 404"""
    response = client.put("/api/recipes/non-existent-id", json=sample_recipe_data)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/recipes/{id}
# ---------------------------------------------------------------------------


def test_delete_recipe_success(client, clean_storage, sample_recipe_data):
    """Contract test: deleting an existing recipe returns 200"""
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create_response.json()["id"]

    response = client.delete(f"/api/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Recipe deleted successfully"


def test_delete_recipe_not_found(client, clean_storage):
    """Contract test: deleting a non-existent recipe returns 404"""
    response = client.delete("/api/recipes/non-existent-id")
    assert response.status_code == 404


def test_delete_recipe_actually_removes_it(client, clean_storage, sample_recipe_data):
    """Contract test: deleted recipe is no longer accessible"""
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create_response.json()["id"]

    client.delete(f"/api/recipes/{recipe_id}")

    get_response = client.get(f"/api/recipes/{recipe_id}")
    assert get_response.status_code == 404


# ---------------------------------------------------------------------------
# HTML pages smoke tests
# ---------------------------------------------------------------------------


def test_recipe_pages_load(client, clean_storage, sample_recipe_data):
    """Smoke test: recipe HTML pages load without error"""
    create_response = client.post("/api/recipes", json=sample_recipe_data)
    recipe_id = create_response.json()["id"]

    assert client.get(f"/recipes/{recipe_id}").status_code == 200
    assert client.get("/recipes/new").status_code == 200
    assert client.get("/import").status_code == 200
