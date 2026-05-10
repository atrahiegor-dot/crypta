import { useEffect } from 'react'
import { authTelegram } from '../api/client'
import { getProfile } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'

// Get Telegram WebApp from global script (telegram-web-app.js in index.html)
const twa = () => window.Telegram?.WebApp

export function useAuth() {
  const { token, setToken, setProfile, setLoading, isLoading, isAuthenticated, profile } =
    useAuthStore()

  useEffect(() => {
    async function init() {
      try {
        const webapp = twa()

        // Tell Telegram the app is ready and expand to full height
        webapp?.ready()
        webapp?.expand()

        const initData = webapp?.initData || ''

        if (initData) {
          // Running inside Telegram — authenticate via initData
          const newToken = await authTelegram(initData)
          setToken(newToken)
          const p = await getProfile()
          setProfile(p)
          return
        }

        // No initData — try existing token (browser refresh / dev mode)
        if (token) {
          try {
            const p = await getProfile()
            setProfile(p)
            return
          } catch {
            // Token expired or invalid — clear it
            useAuthStore.getState().logout()
          }
        }

        // Dev mode fallback: send empty initData (backend will create dev user)
        if (import.meta.env.DEV) {
          try {
            const newToken = await authTelegram(
              'user=%7B%22id%22%3A1%2C%22first_name%22%3A%22DevUser%22%2C%22username%22%3A%22dev%22%7D&auth_date=1&hash=dev'
            )
            setToken(newToken)
            const p = await getProfile()
            setProfile(p)
            return
          } catch {
            // Backend validation rejected dev token — just show unauthenticated state
          }
        }

        setLoading(false)
      } catch (err) {
        console.error('[Auth] Error:', err)
        setLoading(false)
      }
    }

    init()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { isLoading, isAuthenticated, profile }
}
