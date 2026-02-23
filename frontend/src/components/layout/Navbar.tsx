import { useState, useEffect } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ChefHat, Plus, Sun, Moon, Menu, X } from 'lucide-react'
import { useTheme } from '@/context/ThemeContext'
import { cn } from '@/lib/cn'

export default function Navbar() {
  const { theme, toggleTheme } = useTheme()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'text-sm font-medium transition-colors duration-150 px-1 py-0.5 rounded',
      'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
      isActive
        ? 'text-brand-600 dark:text-brand-400'
        : 'text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100',
    )

  const iconBtnClass = cn(
    'h-9 w-9 inline-flex items-center justify-center rounded-lg transition-colors duration-150',
    'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100',
    'dark:text-neutral-400 dark:hover:text-neutral-100 dark:hover:bg-neutral-800',
  )

  return (
    <header
      className={cn(
        'sticky top-0 z-40 w-full bg-white/90 dark:bg-neutral-950/90 backdrop-blur-sm transition-shadow duration-200',
        scrolled ? 'shadow-nav-scrolled' : 'shadow-nav',
      )}
    >
      <nav className="mx-auto flex max-w-6xl items-center gap-6 px-4 sm:px-6 lg:px-8 h-16">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2 font-semibold text-neutral-900 dark:text-neutral-100 shrink-0"
        >
          <ChefHat className="h-5 w-5 text-brand-500" aria-hidden />
          <span>Recipe Explorer</span>
        </Link>

        {/* Desktop nav links */}
        <div className="hidden sm:flex items-center gap-5 flex-1">
          <NavLink to="/" end className={navLinkClass}>
            Recipes
          </NavLink>
          <NavLink to="/import" className={navLinkClass}>
            Import
          </NavLink>
        </div>

        {/* Desktop actions */}
        <div className="hidden sm:flex items-center gap-2 ml-auto">
          <button
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            className={iconBtnClass}
          >
            {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </button>

          <Link
            to="/recipes/new"
            className={cn(
              'inline-flex items-center gap-1.5 h-9 px-4 rounded-lg text-sm font-medium',
              'bg-brand-500 text-white hover:bg-brand-600 transition-colors duration-150 shadow-sm',
            )}
          >
            <Plus className="h-4 w-4" /> New Recipe
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          className="sm:hidden ml-auto h-9 w-9 inline-flex items-center justify-center rounded-lg text-neutral-600"
          onClick={() => setMobileOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="sm:hidden border-t border-neutral-100 dark:border-neutral-800 bg-white dark:bg-neutral-950 px-4 pb-4 pt-2 space-y-2 overflow-hidden"
          >
            <NavLink
              to="/"
              end
              className={navLinkClass}
              onClick={() => setMobileOpen(false)}
            >
              Recipes
            </NavLink>
            <NavLink
              to="/import"
              className={navLinkClass}
              onClick={() => setMobileOpen(false)}
            >
              Import
            </NavLink>
            <Link
              to="/recipes/new"
              className="flex items-center gap-1.5 text-sm font-medium text-brand-600 dark:text-brand-400"
              onClick={() => setMobileOpen(false)}
            >
              <Plus className="h-4 w-4" /> New Recipe
            </Link>
            <button
              onClick={() => { toggleTheme(); setMobileOpen(false) }}
              className="flex items-center gap-1.5 text-sm text-neutral-600 dark:text-neutral-400"
            >
              {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
              {theme === 'light' ? 'Dark mode' : 'Light mode'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
