import { Recipe } from '@/types/recipe'
import { RecipeCard } from './RecipeCard'
import { RecipeCardSkeleton } from '@/components/ui/Skeleton'
import { EmptyState } from './EmptyState'

interface RecipeGridProps {
  recipes?: Recipe[]
  isLoading?: boolean
  searchActive?: boolean
}

export function RecipeGrid({ recipes, isLoading, searchActive }: RecipeGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <RecipeCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!recipes || recipes.length === 0) {
    return <EmptyState searchActive={searchActive} />
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {recipes.map((recipe) => (
        <RecipeCard key={recipe.id} recipe={recipe} />
      ))}
    </div>
  )
}
