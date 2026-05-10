import { create } from 'zustand'
import type { UserProfile } from '../types'

interface AuthState {
  token: string | null
  profile: UserProfile | null
  isLoading: boolean
  isAuthenticated: boolean
  setToken: (token: string) => void
  setProfile: (profile: UserProfile) => void
  setLoading: (v: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('tasker_token'),
  profile: null,
  isLoading: true,
  isAuthenticated: false,

  setToken: (token) => {
    localStorage.setItem('tasker_token', token)
    set({ token, isAuthenticated: true })
  },

  setProfile: (profile) => set({ profile, isAuthenticated: true, isLoading: false }),

  setLoading: (v) => set({ isLoading: v }),

  logout: () => {
    localStorage.removeItem('tasker_token')
    set({ token: null, profile: null, isAuthenticated: false })
  },
}))
