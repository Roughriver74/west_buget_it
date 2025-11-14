import { create } from 'zustand'

interface LoadingState {
  count: number
  startLoading: () => void
  stopLoading: () => void
}

export const useLoadingStore = create<LoadingState>(set => ({
  count: 0,
  startLoading: () =>
    set(state => ({
      count: state.count + 1,
    })),
  stopLoading: () =>
    set(state => ({
      count: Math.max(state.count - 1, 0),
    })),
}))

export const useIsGlobalLoading = () => useLoadingStore(state => state.count > 0)

