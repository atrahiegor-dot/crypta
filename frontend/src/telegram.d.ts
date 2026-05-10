// Global Telegram WebApp types (from telegram-web-app.js script tag)
interface TelegramWebApp {
  ready(): void
  expand(): void
  close(): void
  initData: string
  initDataUnsafe: {
    user?: {
      id: number
      first_name: string
      last_name?: string
      username?: string
      language_code?: string
    }
    query_id?: string
    auth_date: number
    hash: string
  }
  colorScheme: 'light' | 'dark'
  themeParams: {
    bg_color?: string
    text_color?: string
    hint_color?: string
    link_color?: string
    button_color?: string
    button_text_color?: string
    secondary_bg_color?: string
  }
  MainButton: {
    text: string
    show(): void
    hide(): void
    onClick(fn: () => void): void
  }
  BackButton: {
    show(): void
    hide(): void
    onClick(fn: () => void): void
  }
  isExpanded: boolean
  viewportHeight: number
  platform: string
}

interface Window {
  Telegram?: {
    WebApp: TelegramWebApp
  }
}
