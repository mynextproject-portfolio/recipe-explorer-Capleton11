export type RecipeSource = 'internal' | 'external'

export interface Recipe {
  id: string
  title: string
  description: string
  ingredients: string[]
  instructions: string[]
  cuisine: string
  tags: string[]
  source: string
  thumbnail_url?: string | null
  created_at: string
  updated_at: string
}

export interface RecipeCreate {
  title: string
  description: string
  ingredients: string[]
  instructions: string[]
  cuisine: string
  tags?: string[]
}

export type RecipeUpdate = RecipeCreate

export interface RecipeListMeta {
  internal: { count: number; duration_ms: number }
  external: { count: number; duration_ms: number }
  total_duration_ms: number
}

export interface RecipeListResponse {
  recipes: Recipe[]
  meta: RecipeListMeta
}

export interface ImportResponse {
  message: string
  count: number
}
