import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check } from 'lucide-react'
import { cn } from '@/lib/cn'

interface IngredientChecklistProps {
  ingredients: string[]
}

export function IngredientChecklist({ ingredients }: IngredientChecklistProps) {
  const [checked, setChecked] = useState<Set<number>>(new Set())

  const toggle = (index: number) => {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  const checkedCount = checked.size

  return (
    <div>
      {checkedCount > 0 && (
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-3">
          {checkedCount} of {ingredients.length} checked
        </p>
      )}

      <ul className="space-y-2">
        {ingredients.map((ingredient, i) => {
          const isChecked = checked.has(i)
          return (
            <li key={i}>
              <button
                onClick={() => toggle(i)}
                className={cn(
                  'flex items-start gap-3 w-full text-left rounded-lg px-3 py-2.5',
                  'transition-colors duration-150',
                  'hover:bg-neutral-50 dark:hover:bg-neutral-800/50',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                  isChecked && 'opacity-60',
                )}
              >
                {/* Checkbox */}
                <span
                  className={cn(
                    'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition-colors duration-150',
                    isChecked
                      ? 'border-brand-500 bg-brand-500'
                      : 'border-neutral-300 dark:border-neutral-600',
                  )}
                >
                  <AnimatePresence>
                    {isChecked && (
                      <motion.span
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ duration: 0.15 }}
                      >
                        <Check className="h-3 w-3 text-white" strokeWidth={3} />
                      </motion.span>
                    )}
                  </AnimatePresence>
                </span>

                <span
                  className={cn(
                    'text-sm text-neutral-700 dark:text-neutral-300 transition-all duration-150',
                    isChecked && 'line-through text-neutral-400 dark:text-neutral-600',
                  )}
                >
                  {ingredient}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
