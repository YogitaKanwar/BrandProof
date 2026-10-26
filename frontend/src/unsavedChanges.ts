import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState } from 'react'

type Register = (id: symbol, dirty: boolean) => void
export const UnsavedChangesContext = createContext<Register>(() => {})

export function useUnsavedChanges(dirty: boolean) {
  const register = useContext(UnsavedChangesContext)
  const [id] = useState(() => Symbol('unsaved changes'))
  useLayoutEffect(() => {
    register(id, dirty)
    return () => register(id, false)
  }, [register, id, dirty])
}

export function useDraftGuard() {
  const changes = useRef(new Set<symbol>())
  const register = useCallback<Register>((id, dirty) => {
    if (dirty) changes.current.add(id)
    else changes.current.delete(id)
  }, [])
  const confirmLeave = useCallback(() => changes.current.size === 0 || window.confirm('You have unsaved changes or an upload in progress. Leave without saving?'), [])
  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (changes.current.size === 0) return
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', beforeUnload)
    return () => window.removeEventListener('beforeunload', beforeUnload)
  }, [])
  return { register, confirmLeave }
}
