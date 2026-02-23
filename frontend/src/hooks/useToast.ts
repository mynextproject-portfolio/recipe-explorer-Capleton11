import { useState, useEffect } from 'react'

export type ToastVariant = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  variant: ToastVariant
}

type Listener = (toasts: Toast[]) => void
let listeners: Listener[] = []
let toastState: Toast[] = []

function notify() {
  listeners.forEach((l) => l([...toastState]))
}

export function addToast(message: string, variant: ToastVariant = 'info', duration = 4000) {
  const id = crypto.randomUUID()
  toastState = [...toastState, { id, message, variant }]
  notify()
  setTimeout(() => removeToast(id), duration)
}

export function removeToast(id: string) {
  toastState = toastState.filter((t) => t.id !== id)
  notify()
}

export function useToastState(): Toast[] {
  const [toasts, setToasts] = useState<Toast[]>([...toastState])

  useEffect(() => {
    listeners.push(setToasts)
    return () => {
      listeners = listeners.filter((l) => l !== setToasts)
    }
  }, [])

  return toasts
}
