import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import LoadingScreen from './components/LoadingScreen'
import BottomNav from './components/BottomNav'
import ProfilePage from './pages/ProfilePage'
import TasksPage from './pages/TasksPage'
import TaskDetailPage from './pages/TaskDetailPage'
import LeaderboardPage from './pages/LeaderboardPage'
import WalletPage from './pages/WalletPage'

export default function App() {
  const { isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
  }

  if (!isAuthenticated) {
    const debug = (window as any).__authDebug || ''
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center px-8 text-center"
        style={{ background: 'var(--bg)' }}>
        <div style={{
          width: 80, height: 80, borderRadius: 24,
          background: 'linear-gradient(135deg, #23233A, #12121C)',
          border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 24, fontSize: 36
        }}>🔒</div>
        <h1 style={{ color: 'var(--text)', fontSize: 22, fontWeight: 700, marginBottom: 10 }}>
          Откройте через Telegram
        </h1>
        <p style={{ color: 'var(--text-sub)', fontSize: 14, lineHeight: 1.6 }}>
          Это Telegram Mini App. Откройте его через бота{' '}
          <span style={{ color: 'var(--accent)' }}>@Tasker8_bot</span>
        </p>
        {debug && (
          <p style={{ color: '#FF6B6B', fontSize: 11, marginTop: 16, wordBreak: 'break-all', maxWidth: 300 }}>
            {debug}
          </p>
        )}
      </div>
    )
  }

  return (
    <div id="app-shell" style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>
      <main className="scroll-area" style={{ paddingBottom: 80 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/profile" replace />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/tasks/:id" element={<TaskDetailPage />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/wallet" element={<WalletPage />} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  )
}
