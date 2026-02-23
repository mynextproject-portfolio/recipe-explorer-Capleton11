import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, ArrowLeft } from 'lucide-react'
import { getRecipe, createRecipe, updateRecipe, recipeKeys } from '@/api/recipes'
import { RecipeCreate } from '@/types/recipe'
import { addToast } from '@/hooks/useToast'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/cn'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

const listItemVariants = {
  initial: { opacity: 0, height: 0 },
  enter: { opacity: 1, height: 'auto', transition: { duration: 0.2 } },
  exit: { opacity: 0, height: 0, transition: { duration: 0.15 } },
}

interface FormErrors {
  title?: string
  description?: string
  cuisine?: string
  ingredients?: string
  instructions?: string
}

export default function RecipeFormPage() {
  const { id } = useParams<{ id: string }>()
  const isEdit = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [cuisine, setCuisine] = useState('')
  const [ingredients, setIngredients] = useState<string[]>([''])
  const [instructions, setInstructions] = useState<string[]>([''])
  const [errors, setErrors] = useState<FormErrors>({})

  const { data: existing } = useQuery({
    queryKey: recipeKeys.detail(id!),
    queryFn: () => getRecipe(id!),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      setTitle(existing.title ?? '')
      setDescription(existing.description ?? '')
      setCuisine(existing.cuisine ?? '')
      setIngredients(existing.ingredients?.length ? existing.ingredients : [''])
      setInstructions(existing.instructions?.length ? existing.instructions : [''])
    }
  }, [existing])

  const mutation = useMutation({
    mutationFn: (data: RecipeCreate) =>
      isEdit ? updateRecipe(id!, data) : createRecipe(data),
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: recipeKeys.all })
      addToast(isEdit ? 'Recipe updated' : 'Recipe created', 'success')
      navigate(`/recipes/${saved.id}`)
    },
    onError: () => addToast('Something went wrong. Please try again.', 'error'),
  })

  const updateIngredient = (i: number, val: string) =>
    setIngredients((prev) => prev.map((x, idx) => (idx === i ? val : x)))
  const addIngredient = () => setIngredients((prev) => [...prev, ''])
  const removeIngredient = (i: number) =>
    setIngredients((prev) => prev.filter((_, idx) => idx !== i))

  const updateInstruction = (i: number, val: string) =>
    setInstructions((prev) => prev.map((x, idx) => (idx === i ? val : x)))
  const addInstruction = () => setInstructions((prev) => [...prev, ''])
  const removeInstruction = (i: number) =>
    setInstructions((prev) => prev.filter((_, idx) => idx !== i))

  const validate = (): boolean => {
    const errs: FormErrors = {}
    if (!title.trim()) errs.title = 'Title is required'
    if (!description.trim()) errs.description = 'Description is required'
    if (!cuisine.trim()) errs.cuisine = 'Cuisine is required'
    if (!ingredients.some((s) => s.trim())) errs.ingredients = 'Add at least one ingredient'
    if (!instructions.some((s) => s.trim())) errs.instructions = 'Add at least one step'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    const payload: RecipeCreate = {
      title: title.trim(),
      description: description.trim(),
      cuisine: cuisine.trim(),
      ingredients: ingredients.filter((s) => s.trim()),
      instructions: instructions.filter((s) => s.trim()),
    }
    mutation.mutate(payload)
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
      className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-10"
    >
      <Link
        to={isEdit ? `/recipes/${id}` : '/'}
        className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100 mb-8 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {isEdit ? 'Back to recipe' : 'All recipes'}
      </Link>

      <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-8">
        {isEdit ? 'Edit Recipe' : 'New Recipe'}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-8">
        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide mb-4">
            Basic Info
          </legend>

          <Input
            label="Title *"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            error={errors.title}
            placeholder="e.g. Spaghetti Carbonara"
          />

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              Description *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="A brief description of the dish..."
              rows={3}
              className={cn(
                'block w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-neutral-900',
                'placeholder:text-neutral-400 transition-colors duration-150 resize-none',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                'dark:bg-neutral-900 dark:text-neutral-100 dark:placeholder:text-neutral-600',
                errors.description
                  ? 'border-red-400'
                  : 'border-neutral-200 dark:border-neutral-700',
              )}
            />
            {errors.description && (
              <p className="text-xs text-red-500">{errors.description}</p>
            )}
          </div>

          <Input
            label="Cuisine *"
            value={cuisine}
            onChange={(e) => setCuisine(e.target.value)}
            error={errors.cuisine}
            placeholder="e.g. Italian"
          />
        </fieldset>

        {/* Ingredients */}
        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide">
            Ingredients
          </legend>
          {errors.ingredients && (
            <p className="text-xs text-red-500">{errors.ingredients}</p>
          )}

          <AnimatePresence initial={false}>
            {ingredients.map((ingredient, i) => (
              <motion.div
                key={i}
                variants={listItemVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="flex gap-2 overflow-hidden"
              >
                <input
                  value={ingredient}
                  onChange={(e) => updateIngredient(i, e.target.value)}
                  placeholder={`Ingredient ${i + 1}`}
                  className={cn(
                    'flex-1 rounded-lg border border-neutral-200 dark:border-neutral-700',
                    'bg-white dark:bg-neutral-900 px-3.5 py-2.5 text-sm',
                    'text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400',
                    'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                  )}
                />
                {ingredients.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeIngredient(i)}
                    className="h-10 w-10 flex items-center justify-center rounded-lg text-neutral-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors"
                    aria-label="Remove ingredient"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          <button
            type="button"
            onClick={addIngredient}
            className="inline-flex items-center gap-1.5 text-sm text-brand-500 hover:text-brand-600 font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add ingredient
          </button>
        </fieldset>

        {/* Instructions */}
        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 uppercase tracking-wide">
            Instructions
          </legend>
          {errors.instructions && (
            <p className="text-xs text-red-500">{errors.instructions}</p>
          )}

          <AnimatePresence initial={false}>
            {instructions.map((step, i) => (
              <motion.div
                key={i}
                variants={listItemVariants}
                initial="initial"
                animate="enter"
                exit="exit"
                className="flex gap-2 overflow-hidden"
              >
                <div className="flex items-start gap-2 flex-1">
                  <span className="flex h-7 w-7 shrink-0 mt-2 items-center justify-center rounded-full bg-brand-500 text-white text-xs font-bold">
                    {i + 1}
                  </span>
                  <textarea
                    value={step}
                    onChange={(e) => updateInstruction(i, e.target.value)}
                    placeholder={`Step ${i + 1}`}
                    rows={2}
                    className={cn(
                      'flex-1 rounded-lg border border-neutral-200 dark:border-neutral-700',
                      'bg-white dark:bg-neutral-900 px-3.5 py-2.5 text-sm resize-none',
                      'text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400',
                      'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
                    )}
                  />
                </div>
                {instructions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeInstruction(i)}
                    className="h-10 w-10 flex items-center justify-center rounded-lg text-neutral-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 transition-colors mt-1"
                    aria-label="Remove step"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          <button
            type="button"
            onClick={addInstruction}
            className="inline-flex items-center gap-1.5 text-sm text-brand-500 hover:text-brand-600 font-medium transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add step
          </button>
        </fieldset>

        <div className="flex gap-3 pt-2">
          <Button type="submit" loading={mutation.isPending}>
            {isEdit ? 'Save Changes' : 'Create Recipe'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => navigate(isEdit ? `/recipes/${id}` : '/')}
          >
            Cancel
          </Button>
        </div>
      </form>
    </motion.div>
  )
}
