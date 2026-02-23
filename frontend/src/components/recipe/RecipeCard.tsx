import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Recipe } from '@/types/recipe'
import { SourceBadge } from './SourceBadge'
import { cn } from '@/lib/cn'

interface RecipeCardProps {
  recipe: Recipe
}

export function RecipeCard({ recipe }: RecipeCardProps) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="group relative"
    >
      <Link
        to={`/recipes/${recipe.id}`}
        className={cn(
          'block rounded-xl border border-neutral-200 dark:border-neutral-800',
          'bg-white dark:bg-neutral-900',
          'shadow-card hover:shadow-card-hover',
          'transition-shadow duration-200 overflow-hidden',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
        )}
      >
        {/* Accent bar */}
        <div
          className={cn(
            'absolute inset-x-0 top-0 h-0.5 bg-brand-500',
            'origin-left scale-x-0 group-hover:scale-x-100',
            'transition-transform duration-300 ease-out',
          )}
        />

        {/* Thumbnail */}
        {recipe.thumbnail_url ? (
          <div className="relative aspect-[16/9] overflow-hidden bg-neutral-100 dark:bg-neutral-800">
            <img
              src={recipe.thumbnail_url}
              alt={recipe.title}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
          </div>
        ) : (
          <div className="aspect-[16/9] bg-gradient-to-br from-brand-50 to-orange-100 dark:from-neutral-800 dark:to-neutral-700 flex items-center justify-center">
            <span className="text-4xl opacity-40">🍽️</span>
          </div>
        )}

        <div className="p-4">
          {/* Title + source */}
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 line-clamp-2 leading-snug">
              {recipe.title}
            </h3>
            <SourceBadge source={recipe.source ?? ''} />
          </div>

          {/* Description excerpt */}
          {recipe.description && (
            <p className="text-xs text-neutral-500 dark:text-neutral-400 line-clamp-2 mb-3">
              {recipe.description}
            </p>
          )}

          {/* Meta row */}
          <div className="flex items-center gap-3 text-xs text-neutral-500 dark:text-neutral-400">
            {recipe.cuisine && (
              <span className="capitalize">{recipe.cuisine}</span>
            )}
            {recipe.ingredients?.length > 0 && (
              <span>{recipe.ingredients.length} ingredients</span>
            )}
            {recipe.instructions?.length > 0 && (
              <span>{recipe.instructions.length} steps</span>
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  )
}
