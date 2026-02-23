import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'
import { useToastState, removeToast, type Toast } from '@/hooks/useToast'
import { cn } from '@/lib/cn'

const icons = {
  success: <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />,
  error: <XCircle className="h-4 w-4 text-red-500 shrink-0" />,
  info: <Info className="h-4 w-4 text-brand-500 shrink-0" />,
}

const borderColors = {
  success: 'border-l-green-500',
  error: 'border-l-red-500',
  info: 'border-l-brand-500',
}

function ToastItem({ toast }: { toast: Toast }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={cn(
        'flex items-start gap-3 rounded-xl bg-white dark:bg-neutral-900',
        'border border-neutral-200 dark:border-neutral-700 shadow-lg',
        'p-4 pr-3 min-w-[280px] max-w-sm border-l-4',
        borderColors[toast.variant],
      )}
    >
      {icons[toast.variant]}
      <p className="flex-1 text-sm text-neutral-800 dark:text-neutral-200 leading-snug">
        {toast.message}
      </p>
      <button
        onClick={() => removeToast(toast.id)}
        className="shrink-0 rounded p-0.5 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </motion.div>
  )
}

export default function ToastContainer() {
  const toasts = useToastState()
  return (
    <div aria-live="polite" className="fixed bottom-5 right-5 z-50 flex flex-col-reverse gap-2">
      <AnimatePresence initial={false}>
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} />
        ))}
      </AnimatePresence>
    </div>
  )
}
