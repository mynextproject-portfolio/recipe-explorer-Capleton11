import { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileJson, CheckCircle2, AlertCircle } from 'lucide-react'
import { importRecipes, recipeKeys } from '@/api/recipes'
import { addToast } from '@/hooks/useToast'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/cn'

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  enter: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

export default function ImportPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [parseError, setParseError] = useState<string | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  const mutation = useMutation({
    mutationFn: (f: File) => importRecipes(f),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: recipeKeys.all })
      addToast(`Imported ${result.count} recipe${result.count !== 1 ? 's' : ''}`, 'success')
      navigate('/')
    },
    onError: () => addToast('Import failed. Check your file format.', 'error'),
  })

  const handleFileSelect = (selected: File | null) => {
    setParseError(null)
    setFile(null)
    if (!selected) return
    if (!selected.name.endsWith('.json')) {
      setParseError('Only JSON files are supported.')
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        JSON.parse(e.target?.result as string)
        setFile(selected)
      } catch {
        setParseError('Invalid JSON — could not parse the file.')
      }
    }
    reader.readAsText(selected)
  }

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileSelect(e.dataTransfer.files[0] ?? null)
  }

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const onDragLeave = () => setIsDragOver(false)

  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files?.[0] ?? null)
  }

  const handleImport = () => {
    if (!file || !confirmed) return
    mutation.mutate(file)
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
      className="mx-auto max-w-xl px-4 sm:px-6 lg:px-8 py-10"
    >
      <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
        Import Recipes
      </h1>
      <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-8">
        Upload a JSON file containing an array of recipe objects to bulk-import
        into your collection.
      </p>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed',
          'py-14 cursor-pointer transition-colors duration-200',
          isDragOver
            ? 'border-brand-400 bg-brand-50 dark:bg-brand-950/30'
            : file
            ? 'border-green-400 bg-green-50 dark:bg-green-950/20'
            : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600 bg-neutral-50 dark:bg-neutral-900',
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,application/json"
          className="sr-only"
          onChange={onInputChange}
        />

        {file ? (
          <>
            <CheckCircle2 className="h-10 w-10 text-green-500 mb-3" />
            <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {file.name}
            </p>
            <p className="text-xs text-neutral-500 mt-1">
              {(file.size / 1024).toFixed(1)} KB — click to change
            </p>
          </>
        ) : (
          <>
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-neutral-100 dark:bg-neutral-800">
              {isDragOver ? (
                <Upload className="h-6 w-6 text-brand-500" />
              ) : (
                <FileJson className="h-6 w-6 text-neutral-400" />
              )}
            </div>
            <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              {isDragOver ? 'Drop it here' : 'Drag & drop a JSON file'}
            </p>
            <p className="text-xs text-neutral-400">or click to browse</p>
          </>
        )}
      </div>

      {/* Parse error */}
      {parseError && (
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 px-3 py-2.5">
          <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
          <p className="text-xs text-red-600 dark:text-red-400">{parseError}</p>
        </div>
      )}

      {/* Confirmation */}
      {file && !parseError && (
        <label className="mt-5 flex items-start gap-3 cursor-pointer group">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-neutral-300 text-brand-500 focus:ring-brand-500 cursor-pointer"
          />
          <span className="text-sm text-neutral-600 dark:text-neutral-400 group-hover:text-neutral-900 dark:group-hover:text-neutral-200 transition-colors">
            I confirm I want to import recipes from{' '}
            <span className="font-medium text-neutral-900 dark:text-neutral-100">
              {file.name}
            </span>
            . Duplicate entries will be merged by the API.
          </span>
        </label>
      )}

      {/* Actions */}
      <div className="mt-6 flex gap-3">
        <Button
          onClick={handleImport}
          disabled={!file || !confirmed || !!parseError}
          loading={mutation.isPending}
        >
          <Upload className="h-4 w-4" />
          Import Recipes
        </Button>
        <Button variant="secondary" onClick={() => navigate('/')}>
          Cancel
        </Button>
      </div>

      {/* Format hint */}
      <details className="mt-8 text-xs text-neutral-400">
        <summary className="cursor-pointer hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors select-none">
          Expected JSON format
        </summary>
        <pre className="mt-3 rounded-lg bg-neutral-100 dark:bg-neutral-800 p-4 overflow-x-auto text-neutral-600 dark:text-neutral-300 leading-relaxed">
{`[
  {
    "title": "Pasta Primavera",
    "cuisine": "Italian",
    "prep_time_minutes": 30,
    "servings": 4,
    "ingredients": ["200g pasta", "..."],
    "steps": ["Boil water", "..."]
  }
]`}
        </pre>
      </details>
    </motion.div>
  )
}
