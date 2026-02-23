import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { Search, Shuffle } from 'lucide-react'
import { getRecipes, recipeKeys } from '@/api/recipes'
import { useDebounce } from '@/hooks/useDebounce'
import { RecipeGrid } from '@/components/recipe/RecipeGrid'
import { Pagination } from '@/components/ui/Pagination'
import { cn } from '@/lib/cn'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

const CUISINES = [
  'All', 'Italian', 'Mexican', 'Chinese', 'Indian',
  'Japanese', 'French', 'American', 'Thai',
]

const FEATURED_TERMS = [
  'chicken', 'pasta', 'beef', 'salmon', 'lamb',
  'prawn', 'potato', 'mushroom', 'pork', 'vegetable',
]

const PAGE_SIZE = 12

function randomTerm() {
  return FEATURED_TERMS[Math.floor(Math.random() * FEATURED_TERMS.length)]
}

export default function HomePage() {
  const [search, setSearch] = useState('')
  const [cuisine, setCuisine] = useState('All')
  const [page, setPage] = useState(1)
  const [featuredTerm, setFeaturedTerm] = useState(() => randomTerm())
  const debouncedSearch = useDebounce(search, 350)

  // Use user's query if provided, otherwise use the featured term so we always
  // get image-rich external results on the default view.
  const activeQuery = debouncedSearch || featuredTerm

  // Reset to page 1 whenever the effective query or cuisine filter changes
  useEffect(() => { setPage(1) }, [debouncedSearch, cuisine, featuredTerm])

  const query = useQuery({
    queryKey: recipeKeys.list(activeQuery),
    queryFn: () => getRecipes(activeQuery),
  })

  // Only show recipes that have an image; apply cuisine filter on top
  const withImages = query.data?.recipes.filter((r) => !!r.thumbnail_url) ?? []
  const filtered = withImages.filter((r) => {
    if (cuisine === 'All') return true
    return r.cuisine?.toLowerCase() === cuisine.toLowerCase()
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const userSearching = !!debouncedSearch
  const searchActive = userSearching || cuisine !== 'All'

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
      className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10"
    >
      {/* Hero */}
      <div className="mb-10 text-center">
        <h1 className="text-3xl sm:text-4xl font-bold text-neutral-900 dark:text-neutral-100 tracking-tight mb-3">
          Your Recipe Collection
        </h1>
        <p className="text-neutral-500 dark:text-neutral-400 max-w-md mx-auto">
          Browse, search, and discover recipes from around the world.
        </p>
      </div>

      {/* Search */}
      <div className="relative max-w-lg mx-auto mb-6">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400 pointer-events-none" />
        <input
          type="search"
          placeholder="Search recipes..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className={cn(
            'block w-full rounded-xl border border-neutral-200 dark:border-neutral-700',
            'bg-white dark:bg-neutral-900 pl-10 pr-4 py-3 text-sm',
            'text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
            'transition-colors duration-150 shadow-sm',
          )}
        />
      </div>

      {/* Cuisine filters */}
      <div className="flex items-center gap-2 flex-wrap justify-center mb-10">
        {CUISINES.map((c) => (
          <button
            key={c}
            onClick={() => setCuisine(c)}
            className={cn(
              'px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors duration-150',
              c === cuisine
                ? 'bg-brand-500 text-white shadow-sm'
                : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-300 hover:bg-neutral-200 dark:hover:bg-neutral-700',
            )}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Result meta row */}
      <div className="flex items-center justify-between mb-5 min-h-[24px]">
        {!query.isLoading && filtered.length > 0 && (
          <p className="text-xs text-neutral-400">
            {userSearching
              ? `${filtered.length} result${filtered.length !== 1 ? 's' : ''} for "${debouncedSearch}"`
              : <span>Featuring: <span className="capitalize font-medium">{featuredTerm}</span> · {filtered.length} recipes</span>
            }
            {totalPages > 1 && ` · page ${page} of ${totalPages}`}
          </p>
        )}
        {/* Shuffle button — only visible on the default (non-search) view */}
        {!userSearching && (
          <button
            onClick={() => setFeaturedTerm(randomTerm())}
            className="ml-auto flex items-center gap-1.5 text-xs text-neutral-400 hover:text-brand-500 transition-colors duration-150"
            title="Show different recipes"
          >
            <Shuffle className="h-3.5 w-3.5" />
            Shuffle
          </button>
        )}
      </div>

      <RecipeGrid
        recipes={paginated}
        isLoading={query.isLoading}
        searchActive={searchActive}
      />

      {!query.isLoading && totalPages > 1 && (
        <Pagination page={page} totalPages={totalPages} onChange={setPage} />
      )}
    </motion.div>
  )
}
