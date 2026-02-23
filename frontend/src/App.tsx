import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'
import ToastContainer from '@/components/ui/Toast'
import HomePage from '@/pages/HomePage'
import RecipeDetailPage from '@/pages/RecipeDetailPage'
import RecipeFormPage from '@/pages/RecipeFormPage'
import ImportPage from '@/pages/ImportPage'

export default function App() {
  const location = useLocation()

  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-neutral-950">
      <Navbar />
      <main className="flex-1">
        <AnimatePresence mode="wait" initial={false}>
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<HomePage />} />
            <Route path="/recipes/new" element={<RecipeFormPage />} />
            <Route path="/recipes/:id/edit" element={<RecipeFormPage />} />
            <Route path="/recipes/:id" element={<RecipeDetailPage />} />
            <Route path="/import" element={<ImportPage />} />
          </Routes>
        </AnimatePresence>
      </main>
      <Footer />
      <ToastContainer />
    </div>
  )
}
