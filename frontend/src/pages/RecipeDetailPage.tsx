import { useParams, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Edit2, Trash2, ChefHat } from 'lucide-react'
import { getRecipe, deleteRecipe, recipeKeys } from '@/api/recipes'
import { addToast } from '@/hooks/useToast'
import { IngredientChecklist } from '@/components/recipe/IngredientChecklist'
import { SourceBadge } from '@/components/recipe/SourceBadge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

export default function RecipeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: recipe, isLoading, isError } = useQuery({
    queryKey: recipeKeys.detail(id!),
    queryFn: () => getRecipe(id!),
    enabled: !!id,
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteRecipe(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: recipeKeys.all })
      addToast('Recipe deleted', 'success')
      navigate('/')
    },
    onError: () => addToast('Failed to delete recipe', 'error'),
  })

  const handleDelete = () => {
    if (window.confirm('Delete this recipe? This cannot be undone.')) {
      deleteMutation.mutate()
    }
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-24 text-center">
        <ChefHat className="h-12 w-12 text-neutral-300 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          Recipe not found
        </h2>
        <Link to="/" className="text-sm text-brand-500 hover:text-brand-600">
          ← Back to recipes
        </Link>
      </div>
    )
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
      className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10"
    >
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100 mb-8 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        All recipes
      </Link>

      {isLoading ? (
        <DetailSkeleton />
      ) : recipe ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Main content — 2/3 */}
          <div className="lg:col-span-2 space-y-8">
            <div>
              <div className="flex items-start justify-between gap-4 mb-3">
                <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900 dark:text-neutral-100 leading-tight">
                  {recipe.title}
                </h1>
                <SourceBadge source={recipe.source ?? ''} />
              </div>

              {recipe.description && (
                <p className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed mb-3">
                  {recipe.description}
                </p>
              )}

              <div className="flex flex-wrap gap-3 text-sm text-neutral-500 dark:text-neutral-400">
                {recipe.cuisine && (
                  <span className="capitalize">🌍 {recipe.cuisine}</span>
                )}
                {recipe.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded-full bg-neutral-100 dark:bg-neutral-800 text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Thumbnail */}
            {recipe.thumbnail_url && (
              <div className="rounded-xl overflow-hidden aspect-video bg-neutral-100 dark:bg-neutral-800">
                <img
                  src={recipe.thumbnail_url}
                  alt={recipe.title}
                  className="w-full h-full object-cover"
                />
              </div>
            )}

            {recipe.instructions && recipe.instructions.length > 0 && (
              <section>
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
                  Instructions
                </h2>
                <ol className="space-y-4">
                  {recipe.instructions.map((step: string, i: number) => (
                    <li key={i} className="flex gap-4">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-500 text-white text-xs font-bold mt-0.5">
                        {i + 1}
                      </span>
                      <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed pt-1">
                        {step}
                      </p>
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {recipe.source !== 'external' && (
              <div className="flex gap-3 pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigate(`/recipes/${id}/edit`)}
                >
                  <Edit2 className="h-3.5 w-3.5" />
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleDelete}
                  loading={deleteMutation.isPending}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete
                </Button>
              </div>
            )}
          </div>

          {/* Sidebar — 1/3 */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 rounded-xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-5">
              <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
                Ingredients
              </h2>
              {recipe.ingredients && recipe.ingredients.length > 0 ? (
                <IngredientChecklist ingredients={recipe.ingredients} />
              ) : (
                <p className="text-sm text-neutral-400">No ingredients listed.</p>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </motion.div>
  )
}

function DetailSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
      <div className="lg:col-span-2 space-y-6">
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-5 w-1/3" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      </div>
      <div className="lg:col-span-1">
        <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 space-y-3">
          <Skeleton className="h-5 w-1/2" />
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      </div>
    </div>
  )
}
