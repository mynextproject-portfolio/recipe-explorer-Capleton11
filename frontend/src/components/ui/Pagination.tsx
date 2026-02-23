import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/cn'

interface PaginationProps {
  page: number
  totalPages: number
  onChange: (page: number) => void
}

export function Pagination({ page, totalPages, onChange }: PaginationProps) {
  // Build visible page numbers: always show first, last, current ±1, with ellipsis
  const pages: (number | 'ellipsis')[] = []
  const range = (from: number, to: number) =>
    Array.from({ length: to - from + 1 }, (_, i) => from + i)

  if (totalPages <= 7) {
    pages.push(...range(1, totalPages))
  } else {
    pages.push(1)
    if (page > 3) pages.push('ellipsis')
    pages.push(...range(Math.max(2, page - 1), Math.min(totalPages - 1, page + 1)))
    if (page < totalPages - 2) pages.push('ellipsis')
    pages.push(totalPages)
  }

  const btnBase = cn(
    'h-9 w-9 inline-flex items-center justify-center rounded-lg text-sm font-medium transition-colors duration-150',
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
  )

  return (
    <div className="flex items-center justify-center gap-1 mt-10">
      <button
        onClick={() => onChange(page - 1)}
        disabled={page === 1}
        className={cn(btnBase, 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-30 disabled:pointer-events-none')}
        aria-label="Previous page"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {pages.map((p, i) =>
        p === 'ellipsis' ? (
          <span key={`ellipsis-${i}`} className="h-9 w-9 inline-flex items-center justify-center text-sm text-neutral-400">
            …
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            className={cn(
              btnBase,
              p === page
                ? 'bg-brand-500 text-white shadow-sm'
                : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-neutral-100 dark:hover:bg-neutral-800',
            )}
            aria-current={p === page ? 'page' : undefined}
          >
            {p}
          </button>
        ),
      )}

      <button
        onClick={() => onChange(page + 1)}
        disabled={page === totalPages}
        className={cn(btnBase, 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 dark:hover:bg-neutral-800 disabled:opacity-30 disabled:pointer-events-none')}
        aria-label="Next page"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}
