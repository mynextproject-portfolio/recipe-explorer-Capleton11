import { Link } from 'react-router-dom'
import { ChefHat, Plus, Download } from 'lucide-react'

interface EmptyStateProps {
  searchActive?: boolean
}

export function EmptyState({ searchActive }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 dark:bg-brand-950">
        <ChefHat className="h-8 w-8 text-brand-500" />
      </div>

      {searchActive ? (
        <>
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            No recipes found
          </h2>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-xs">
            Try a different search term or browse all recipes.
          </p>
        </>
      ) : (
        <>
          <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            Your recipe book is empty
          </h2>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-xs mb-8">
            Start building your collection by creating a recipe or importing from JSON.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/recipes/new"
              className="inline-flex items-center gap-2 h-10 px-5 rounded-lg text-sm font-medium bg-brand-500 text-white hover:bg-brand-600 transition-colors duration-150 shadow-sm"
            >
              <Plus className="h-4 w-4" />
              New Recipe
            </Link>
            <Link
              to="/import"
              className="inline-flex items-center gap-2 h-10 px-5 rounded-lg text-sm font-medium border border-neutral-200 dark:border-neutral-700 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors duration-150"
            >
              <Download className="h-4 w-4" />
              Import JSON
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
