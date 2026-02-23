import { ChefHat, Mail } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="mt-auto border-t border-neutral-100 dark:border-neutral-800 bg-white dark:bg-neutral-950">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
          <ChefHat className="h-4 w-4 text-brand-500" />
          <span>Recipe Explorer</span>
          <span className="text-neutral-300 dark:text-neutral-700">·</span>
          <span>Powered by FastAPI + React</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-neutral-400">
          <span>Built by <span className="font-medium text-neutral-600 dark:text-neutral-300">Capleton</span></span>
          <a
            href="mailto:capletonchapfika@gmail.com"
            className="flex items-center gap-1.5 hover:text-brand-500 transition-colors duration-150"
          >
            <Mail className="h-3.5 w-3.5" />
            capletonchapfika@gmail.com
          </a>
        </div>
      </div>
    </footer>
  )
}
