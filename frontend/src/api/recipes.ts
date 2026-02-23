import type {
  Recipe,
  RecipeCreate,
  RecipeUpdate,
  RecipeListResponse,
  ImportResponse,
} from '@/types/recipe'

const BASE = '/api'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(res.status, (body as { detail?: string }).detail ?? 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const recipeKeys = {
  all: ['recipes'] as const,
  list: (search?: string) => ['recipes', 'list', { search }] as const,
  detail: (id: string) => ['recipes', 'detail', id] as const,
}

export function getRecipes(search?: string): Promise<RecipeListResponse> {
  const url = new URL(`${BASE}/recipes`, window.location.origin)
  if (search) url.searchParams.set('search', search)
  return apiFetch<RecipeListResponse>(url.toString())
}

export function getRecipe(
  id: string,
  source: 'internal' | 'external' | 'generic' = 'generic',
): Promise<Recipe> {
  if (source === 'internal') return apiFetch<Recipe>(`${BASE}/recipes/internal/${id}`)
  if (source === 'external') return apiFetch<Recipe>(`${BASE}/recipes/external/${id}`)
  return apiFetch<Recipe>(`${BASE}/recipes/${id}`)
}

export function createRecipe(data: RecipeCreate): Promise<Recipe> {
  return apiFetch<Recipe>(`${BASE}/recipes`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateRecipe(id: string, data: RecipeUpdate): Promise<Recipe> {
  return apiFetch<Recipe>(`${BASE}/recipes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteRecipe(id: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>(`${BASE}/recipes/${id}`, {
    method: 'DELETE',
  })
}

export async function exportRecipes(): Promise<void> {
  const res = await fetch(`${BASE}/recipes/export`)
  if (!res.ok) throw new ApiError(res.status, 'Export failed')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'recipes.json'
  a.click()
  URL.revokeObjectURL(url)
}

export function importRecipes(file: File): Promise<ImportResponse> {
  const form = new FormData()
  form.append('file', file)
  return apiFetch<ImportResponse>(`${BASE}/recipes/import`, {
    method: 'POST',
    headers: {},
    body: form,
  })
}
